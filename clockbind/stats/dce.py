"""Discrete-choice engines for Paper 1.

The functions in this module are deliberately data-contract driven.  They expect
profile-row conjoint data (two candidate rows per task by default) with a 0/1
``chosen`` field.  A task where no profile is chosen is converted into an
explicit outside alternative before choice-model estimation.

Implemented here:
* dummy-coded MNL with an explicit outside option;
* Swait--Louviere scale/parameter equality diagnostics;
* simulated maximum-likelihood mixed logit with respondent-level normal random
  coefficients;
* hierarchical-Bayes multinomial logit using Metropolis-within-Gibbs.

The HB and mixed-logit engines are computationally intensive and are marked as
validation-required in the user-facing analyses until an external reference
implementation has been matched on frozen validation cases.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import optimize, stats
from scipy.special import logsumexp
from scipy.stats import qmc, invwishart


@dataclass
class ChoiceData:
    frame: pd.DataFrame
    X: np.ndarray
    y: np.ndarray
    terms: list[str]
    set_slices: list[np.ndarray]
    respondents: np.ndarray
    set_group: np.ndarray | None = None


def _as_list(x) -> list[str]:
    if x is None:
        return []
    if isinstance(x, str):
        return [z.strip() for z in x.split(",") if z.strip()]
    return list(x)


def _safe_unique(x: pd.Series) -> list[str]:
    return sorted(x.dropna().astype(str).unique().tolist(), key=str)


def prepare_choice_data(
    df: pd.DataFrame,
    attributes: Iterable[str],
    chosen: str,
    respondent: str,
    task: str = "task",
    alternative: str = "profile",
    baselines: dict | None = None,
    factor: str | None = None,
    factor_baseline: str | None = None,
    add_outside: bool = True,
    interact_factor: bool = True,
) -> ChoiceData:
    """Convert profile rows to a full long-format discrete-choice design.

    ``add_outside=True`` turns a reject-both task into a third alternative and
    adds an ``outside`` coefficient.  A task with more than one selected profile
    is invalid and rejected.
    """
    attrs = list(attributes)
    need = [respondent, task, alternative, chosen] + attrs + ([factor] if factor else [])
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise ValueError(f"Variables not found: {missing}")
    d = df[need].copy()
    d[chosen] = pd.to_numeric(d[chosen], errors="coerce")
    if d[chosen].isna().any() or not d[chosen].isin([0, 1]).all():
        raise ValueError(f"{chosen} must contain only 0/1 values")
    d["__set"] = d[respondent].astype(str) + "\x1f" + d[task].astype(str)
    counts = d.groupby("__set")[chosen].sum()
    if (counts > 1).any():
        bad = counts[counts > 1].index[:5].tolist()
        raise ValueError(f"Choice sets with multiple selected alternatives: {bad}")
    if not add_outside and (counts == 0).any():
        raise ValueError("Reject/no-choice tasks exist; use add_outside=True")

    baselines = {str(k): str(v) for k, v in (baselines or {}).items()}
    attr_levels: dict[str, list[str]] = {}
    for a in attrs:
        levels = _safe_unique(d[a])
        if not levels:
            raise ValueError(f"Attribute {a!r} has no observed levels")
        base = baselines.get(a, levels[0])
        if base not in levels:
            raise ValueError(f"Baseline {base!r} is not observed for attribute {a!r}")
        attr_levels[a] = levels
        baselines[a] = base

    if add_outside:
        rows = []
        first_cols = [respondent, task]
        if factor:
            first_cols.append(factor)
        first = d.groupby("__set", sort=False)[first_cols].first()
        for sid, row in first.iterrows():
            r = {respondent: row[respondent], task: row[task], alternative: "__OUTSIDE__", chosen: int(counts.loc[sid] == 0), "__set": sid}
            for a in attrs:
                r[a] = "__OUTSIDE__"
            if factor:
                r[factor] = row[factor]
            rows.append(r)
        d = pd.concat([d, pd.DataFrame(rows)], ignore_index=True, sort=False)

    # Make every choice set contiguous.  This is not cosmetic: the likelihood
    # uses vectorised reduce-at operations and is substantially faster than a
    # Python loop over thousands of tasks.
    set_order = list(dict.fromkeys(d["__set"].astype(str).tolist()))
    d["__set_order"] = pd.Categorical(d["__set"].astype(str), categories=set_order, ordered=True)
    d["__outside_order"] = (d[alternative].astype(str) == "__OUTSIDE__").astype(int)
    d = d.sort_values(["__set_order", "__outside_order"], kind="stable").reset_index(drop=True)

    # Build dummy design; outside is the zero point for profile attributes.
    cols = []
    terms = []
    for a in attrs:
        s = d[a].astype(str)
        for lv in attr_levels[a]:
            if lv == baselines[a]:
                continue
            terms.append(f"{a}={lv}")
            cols.append((s == lv).to_numpy(float))
    outside = (d[alternative].astype(str) == "__OUTSIDE__").to_numpy(float)
    terms.append("outside")
    cols.append(outside)

    # Task-level factor cannot enter as an alternative-invariant main effect;
    # it enters via interactions with profile attributes and outside utility.
    if factor and interact_factor:
        flv = _safe_unique(d[factor])
        fb = str(factor_baseline or flv[0])
        if fb not in flv:
            raise ValueError(f"factor_baseline {fb!r} is not observed in {factor!r}")
        base_cols = list(cols[:-1])  # profile attribute dummies only
        base_terms = list(terms[:-1])
        for lv in flv:
            if lv == fb:
                continue
            z = (d[factor].astype(str) == lv).to_numpy(float)
            for bt, bc in zip(base_terms, base_cols):
                terms.append(f"{bt} x {factor}={lv}")
                cols.append(bc * z)
            terms.append(f"outside x {factor}={lv}")
            cols.append(outside * z)

    X = np.column_stack(cols).astype(float) if cols else np.zeros((len(d), 0))
    y = d[chosen].to_numpy(int)
    # Choice sets are now contiguous.
    sets = list(dict.fromkeys(d["__set"].astype(str).tolist()))
    sizes = d.groupby("__set", sort=False).size().to_numpy(int)
    starts = np.r_[0, np.cumsum(sizes)[:-1]]
    set_slices = [np.arange(st, st+n) for st, n in zip(starts, sizes)]
    for idx in set_slices:
        if y[idx].sum() != 1:
            raise ValueError("Every expanded choice set must contain exactly one chosen alternative")
    respondents = d[respondent].astype(str).to_numpy()
    set_group = None
    if factor:
        set_group = np.asarray([str(d.iloc[idx[0]][factor]) for idx in set_slices], dtype=object)
    return ChoiceData(d, X, y, terms, set_slices, respondents, set_group)


def _mnl_ll(beta: np.ndarray, cd: ChoiceData, scale_by_set: np.ndarray | None = None) -> float:
    u = cd.X @ beta
    lengths = np.asarray([len(x) for x in cd.set_slices], dtype=int)
    starts = np.r_[0, np.cumsum(lengths)[:-1]]
    if scale_by_set is not None:
        u = u * np.repeat(np.asarray(scale_by_set, float), lengths)
    mx = np.maximum.reduceat(u, starts)
    den = np.add.reduceat(np.exp(u - np.repeat(mx, lengths)), starts)
    chosen_u = u[cd.y == 1]
    if len(chosen_u) != len(starts):
        raise ValueError("Each choice set must have exactly one chosen alternative")
    return float(np.sum(chosen_u - mx - np.log(den)))


def _mnl_grad(beta: np.ndarray, cd: ChoiceData, scale_by_set: np.ndarray | None = None) -> np.ndarray:
    lengths = np.asarray([len(x) for x in cd.set_slices], dtype=int)
    starts = np.r_[0, np.cumsum(lengths)[:-1]]
    scset = np.ones(len(starts)) if scale_by_set is None else np.asarray(scale_by_set, float)
    scrow = np.repeat(scset, lengths)
    u = (cd.X @ beta) * scrow
    mx = np.maximum.reduceat(u, starts)
    eu = np.exp(u - np.repeat(mx, lengths))
    den = np.add.reduceat(eu, starts)
    p = eu / np.repeat(den, lengths)
    # derivative of utility wrt beta is scale * X
    score_rows = (cd.y - p)[:, None] * (cd.X * scrow[:, None])
    return score_rows.sum(axis=0)


def fit_mnl(cd: ChoiceData, start: np.ndarray | None = None, scale_by_set: np.ndarray | None = None) -> dict:
    k = cd.X.shape[1]
    if k == 0:
        raise ValueError("No estimable choice-design terms")
    x0 = np.zeros(k) if start is None else np.asarray(start, float)
    res = optimize.minimize(lambda b: -_mnl_ll(b, cd, scale_by_set), x0, jac=lambda b: -_mnl_grad(b, cd, scale_by_set), method="BFGS", options={"gtol": 1e-6, "maxiter": 1500})
    beta = np.asarray(res.x, float)
    # Observed information from the analytic gradient (central differences), not the BFGS approximation.
    try:
        h = 1e-5
        H = np.empty((k, k))
        for j in range(k):
            e = np.zeros(k); e[j] = h
            H[:, j] = (_mnl_grad(beta + e, cd, scale_by_set) - _mnl_grad(beta - e, cd, scale_by_set)) / (2 * h)
        H = (H + H.T) / 2
        vcov = np.linalg.inv(-H)
        se = np.sqrt(np.clip(np.diag(vcov), 0, None))
    except Exception:
        vcov = np.full((k, k), np.nan); se = np.full(k, np.nan)
    z = beta / se
    p = 2 * stats.norm.sf(np.abs(z))
    tab = pd.DataFrame({"estimate": beta, "se": se, "z": z, "p": p,
                        "ci_low": beta - 1.96 * se, "ci_high": beta + 1.96 * se}, index=cd.terms)
    return {"coef": beta, "vcov": vcov, "table": tab, "loglike": float(-res.fun), "success": bool(res.success), "message": str(res.message), "n_params": k}


def subset_choice_data(cd: ChoiceData, keep_sets: list[int]) -> ChoiceData:
    rows = np.concatenate([cd.set_slices[i] for i in keep_sets]) if keep_sets else np.array([], dtype=int)
    f = cd.frame.iloc[rows].reset_index(drop=True)
    X = cd.X[rows]
    y = cd.y[rows]
    # remap set slices by original lengths
    slices = []
    pos = 0
    for i in keep_sets:
        n = len(cd.set_slices[i]); slices.append(np.arange(pos, pos+n)); pos += n
    resp = cd.respondents[rows]
    sg = cd.set_group[keep_sets] if cd.set_group is not None else None
    return ChoiceData(f, X, y, cd.terms, slices, resp, sg)


def swait_louviere(cd: ChoiceData) -> dict:
    """Two-sample Swait--Louviere scale and parameter-equality diagnostics.

    The factor supplied to ``prepare_choice_data`` must define exactly two
    choice-set groups.  We estimate separate MNLs, then a constrained pooled
    model with a freely estimated positive relative scale for group 2.
    """
    if cd.set_group is None:
        raise ValueError("A task-level factor is required for the Swait–Louviere diagnostic")
    levels = sorted(pd.unique(cd.set_group).tolist(), key=str)
    if len(levels) != 2:
        raise ValueError("Swait–Louviere diagnostic currently requires exactly two factor levels")
    keep1 = [i for i, g in enumerate(cd.set_group) if g == levels[0]]
    keep2 = [i for i, g in enumerate(cd.set_group) if g == levels[1]]
    a, b = subset_choice_data(cd, keep1), subset_choice_data(cd, keep2)
    fa, fb = fit_mnl(a), fit_mnl(b)
    k = cd.X.shape[1]
    group2 = np.array([g == levels[1] for g in cd.set_group], bool)

    def obj(theta):
        beta = theta[:k]
        mu = math.exp(theta[k])
        scales = np.where(group2, mu, 1.0)
        return -_mnl_ll(beta, cd, scales)

    start = np.r_[0.5 * (fa["coef"] + fb["coef"]), 0.0]
    rscale = optimize.minimize(obj, start, method="L-BFGS-B", options={"maxiter": 3000, "ftol": 1e-12, "gtol": 1e-7})
    ll_scale = float(-rscale.fun); mu = float(math.exp(rscale.x[k]))
    pooled = fit_mnl(cd)
    ll_sep = fa["loglike"] + fb["loglike"]
    # H0 parameter equality allowing a relative scale: 2k separate parameters vs k+1 constrained.
    lr_pref = max(0.0, 2 * (ll_sep - ll_scale)); df_pref = max(k - 1, 1)
    # H0 scale equality given common preferences: common-scale model vs free-scale common-preference model.
    lr_scale = max(0.0, 2 * (ll_scale - pooled["loglike"])); df_scale = 1
    return {
        "levels": levels, "relative_scale_group2_to_group1": mu,
        "loglike_group1": fa["loglike"], "loglike_group2": fb["loglike"],
        "loglike_separate": ll_sep, "loglike_common_with_scale": ll_scale,
        "loglike_common_scale1": pooled["loglike"],
        "preference_equality_lr": lr_pref, "preference_equality_df": df_pref,
        "preference_equality_p": float(stats.chi2.sf(lr_pref, df_pref)),
        "scale_equality_lr": lr_scale, "scale_equality_df": df_scale,
        "scale_equality_p": float(stats.chi2.sf(lr_scale, df_scale)),
        "converged": bool(rscale.success and fa["success"] and fb["success"] and pooled["success"]),
    }


def _respondent_sets(cd: ChoiceData) -> list[tuple[str, list[int]]]:
    # set ownership is constant within set
    owners = [str(cd.respondents[idx[0]]) for idx in cd.set_slices]
    order = list(dict.fromkeys(owners))
    return [(r, [i for i, o in enumerate(owners) if o == r]) for r in order]


def _halton_normal(n_draws: int, dim: int, seed: int) -> np.ndarray:
    if dim == 0:
        return np.zeros((n_draws, 0))
    eng = qmc.Halton(d=dim, scramble=True, seed=int(seed))
    u = np.clip(eng.random(n_draws), 1e-10, 1 - 1e-10)
    z = stats.norm.ppf(u)
    # antithetic centring improves small-draw stability
    z -= z.mean(axis=0, keepdims=True)
    return z


def fit_mixed_logit(cd: ChoiceData, random_terms: Iterable[str], n_draws: int = 128, seed: int = 20260928) -> dict:
    random_terms = _as_list(random_terms)
    idx_random = [cd.terms.index(t) for t in random_terms if t in cd.terms]
    missing = [t for t in random_terms if t not in cd.terms]
    if missing:
        raise ValueError(f"Random-coefficient terms not found: {missing}; available terms: {cd.terms}")
    if not idx_random:
        raise ValueError("Select at least one random-coefficient term")
    if n_draws < 16:
        raise ValueError("Use at least 16 simulation draws")
    base = fit_mnl(cd)
    k, q = len(cd.terms), len(idx_random)
    draws = _halton_normal(int(n_draws), q, int(seed))
    resp_sets = _respondent_sets(cd)
    resp_names = [r for r, _ in resp_sets]
    resp_map = {r:i for i,r in enumerate(resp_names)}
    set_owner = np.asarray([resp_map[str(cd.respondents[idx[0]])] for idx in cd.set_slices], dtype=int)
    lengths = np.asarray([len(x) for x in cd.set_slices], dtype=int)
    equal_m = bool(np.all(lengths == lengths[0]))
    if not equal_m:
        starts = np.r_[0, np.cumsum(lengths)[:-1]]

    Xr = cd.X[:, idx_random]
    H = len(draws)

    def nll(theta):
        mean = theta[:k]
        sd = np.exp(theta[k:])
        # utilities for every row under every simulation draw: rows x H
        U = (cd.X @ mean)[:, None] + Xr @ (sd[:, None] * draws.T)
        if equal_m:
            m = int(lengths[0]); S = len(lengths)
            U3 = U.reshape(S, m, H)
            Y3 = cd.y.reshape(S, m)
            chosen_u = (U3 * Y3[:, :, None]).sum(axis=1)
            set_lp = chosen_u - logsumexp(U3, axis=1)  # S x H
        else:
            set_lp = np.empty((len(lengths), H))
            for si, (st, ln) in enumerate(zip(starts, lengths)):
                z = U[st:st+ln]
                j = int(np.flatnonzero(cd.y[st:st+ln] == 1)[0])
                set_lp[si] = z[j] - logsumexp(z, axis=0)
        resp_ll = np.zeros((len(resp_names), H))
        np.add.at(resp_ll, set_owner, set_lp)
        total = np.sum(logsumexp(resp_ll, axis=1) - math.log(H))
        return -float(total)

    x0 = np.r_[base["coef"], np.log(np.repeat(0.25, q))]
    res = optimize.minimize(nll, x0, method="L-BFGS-B", options={"maxiter": 900, "ftol": 1e-9, "gtol": 1e-5, "maxls": 30})
    mean = res.x[:k]; sd = np.exp(res.x[k:])
    rows = [{"term": t, "mean": mean[i], "random_sd": (sd[idx_random.index(i)] if i in idx_random else 0.0),
             "random": i in idx_random} for i, t in enumerate(cd.terms)]
    return {"table": pd.DataFrame(rows).set_index("term"), "loglike": float(-res.fun), "success": bool(res.success),
            "message": str(res.message), "draws": int(n_draws), "respondents": len(resp_sets), "seed": int(seed)}

def _individual_ll(beta: np.ndarray, cd: ChoiceData, set_indices: list[int]) -> float:
    v = 0.0
    for si in set_indices:
        idx = cd.set_slices[si]; u = cd.X[idx] @ beta
        j = int(np.flatnonzero(cd.y[idx] == 1)[0]); v += float(u[j] - logsumexp(u))
    return v


def fit_hb_mnl(cd: ChoiceData, iterations: int = 1000, burn: int = 400, thin: int = 5,
               seed: int = 20260928, step_scale: float = 0.18) -> dict:
    """Hierarchical-Bayes MNL using Metropolis-within-Gibbs.

    Prior: beta_i ~ N(mu,Sigma), mu ~ N(0, 10 I),
    Sigma ~ InvWishart(K+3, I).  This is a transparent reference engine intended
    for validation against an established HB implementation before confirmatory
    use in the dissertation.
    """
    if iterations <= burn or thin < 1:
        raise ValueError("iterations must exceed burn and thin must be >= 1")
    resp_sets = _respondent_sets(cd); n = len(resp_sets); k = len(cd.terms)
    if n < 3:
        raise ValueError("HB requires at least 3 respondents")
    if k > 40:
        raise ValueError("HB guardrail: more than 40 coefficients; simplify coding or validate a dedicated backend")
    rng = np.random.default_rng(int(seed))
    base = fit_mnl(cd)
    B = np.tile(base["coef"], (n, 1)) + rng.normal(0, 0.05, size=(n, k))
    mu = base["coef"].copy(); Sigma = np.eye(k)
    V0 = np.eye(k) * 10.0; V0inv = np.linalg.inv(V0)
    df0 = k + 3; S0 = np.eye(k)
    acc = np.zeros(n); kept_mu = []; kept_B = []; kept_S = []
    prop = float(step_scale)
    for it in range(int(iterations)):
        invS = np.linalg.inv(Sigma)
        # respondent beta updates
        chol = np.linalg.cholesky(Sigma + np.eye(k) * 1e-9)
        for i, (_, sets) in enumerate(resp_sets):
            cur = B[i]
            cand = cur + prop * (chol @ rng.normal(size=k))
            def lp(b):
                z = b - mu
                return _individual_ll(b, cd, sets) - 0.5 * float(z @ invS @ z)
            lr = lp(cand) - lp(cur)
            if math.log(rng.random()) < min(0.0, lr):
                B[i] = cand; acc[i] += 1
        # mu | B,Sigma
        Vn = np.linalg.inv(V0inv + n * invS)
        mn = Vn @ (invS @ B.sum(axis=0))
        mu = rng.multivariate_normal(mn, Vn)
        # Sigma | B,mu
        D = B - mu
        Sn = S0 + D.T @ D
        Sigma = invwishart.rvs(df=df0 + n, scale=Sn, random_state=rng)
        Sigma = np.atleast_2d(Sigma)
        if it >= burn and ((it - burn) % thin == 0):
            kept_mu.append(mu.copy()); kept_B.append(B.copy()); kept_S.append(Sigma.copy())
    if not kept_mu:
        raise RuntimeError("No HB posterior draws were retained")
    MU = np.asarray(kept_mu); BB = np.asarray(kept_B); SS = np.asarray(kept_S)
    pop_mean = MU.mean(axis=0)
    pop_sd = np.sqrt(np.clip(np.diagonal(SS.mean(axis=0)), 0, None))
    ci_lo = np.quantile(MU, 0.025, axis=0); ci_hi = np.quantile(MU, 0.975, axis=0)
    tab = pd.DataFrame({"posterior_mean": pop_mean, "population_sd": pop_sd,
                        "mean_95ci_low": ci_lo, "mean_95ci_high": ci_hi}, index=cd.terms)
    indiv = pd.DataFrame(BB.mean(axis=0), columns=cd.terms, index=[r for r, _ in resp_sets])
    indiv.index.name = "respondent"
    return {"population": tab, "individual_means": indiv, "acceptance": pd.Series(acc / iterations, index=indiv.index),
            "retained_draws": len(MU), "iterations": int(iterations), "burn": int(burn), "thin": int(thin), "seed": int(seed)}
