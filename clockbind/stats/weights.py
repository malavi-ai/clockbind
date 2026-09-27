"""Multi-arm propensity scores and generalized overlap weights (Li & Li, 2019).

Design-stage functions (fit_ps, gow_weights, balance_table, ess_table,
estimability_gates) never touch the outcome. The outcome enters only in
estimate_contrast, so diagnostics can be frozen before outcomes are seen.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .robust import wls_cluster


@dataclass
class PSFit:
    ps: np.ndarray          # n x K matrix of estimated probabilities
    levels: list            # arm labels in column order
    z: np.ndarray           # integer arm index per row
    converged: bool
    loglik: float
    notes: list = field(default_factory=list)


def design_matrix(df: pd.DataFrame, covariates: list[str]) -> tuple[np.ndarray, list[str]]:
    X = pd.get_dummies(df[covariates], drop_first=True, dtype=float)
    names = ["const"] + list(X.columns)
    return np.column_stack([np.ones(len(df)), X.to_numpy(dtype=float)]), names


def fit_ps(df: pd.DataFrame, treatment: str, covariates: list[str], levels=None) -> PSFit:
    """Unpenalised multinomial logistic regression by maximum likelihood."""
    import statsmodels.api as sm

    levels = list(levels) if levels is not None else sorted(df[treatment].dropna().unique().tolist())
    lookup = {lv: i for i, lv in enumerate(levels)}
    z = df[treatment].map(lookup).to_numpy()
    if np.any(pd.isna(z)):
        raise ValueError("treatment has values outside the declared levels")
    z = z.astype(int)
    X, _ = design_matrix(df, covariates)
    notes = []
    import warnings
    model = sm.MNLogit(z, X)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = model.fit(method="newton", maxiter=200, disp=False)
        converged = bool(res.mle_retvals.get("converged", False))
    except Exception as e:  # separation etc.
        notes.append(f"Newton failed ({e}); retrying with BFGS")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = model.fit(method="bfgs", maxiter=2000, disp=False)
        converged = bool(res.mle_retvals.get("converged", False))
    ps = np.asarray(res.predict(X))
    if not converged:
        notes.append("Propensity model did not fully converge; check for separation or sparse arms.")
    return PSFit(ps=ps, levels=levels, z=z, converged=converged, loglik=float(res.llf), notes=notes)


def gow_weights(fit: PSFit) -> np.ndarray:
    """w_i = h(x_i) / e_{z_i}(x_i), with h(x) = 1 / sum_k 1/e_k(x)."""
    ps = np.clip(fit.ps, 1e-12, 1.0)
    h = 1.0 / np.sum(1.0 / ps, axis=1)
    return h / ps[np.arange(len(fit.z)), fit.z]


def ess(w) -> float:
    w = np.asarray(w, float)
    return float(w.sum() ** 2 / np.sum(w ** 2)) if w.sum() > 0 else 0.0


def ess_table(fit: PSFit, w, cluster=None) -> pd.DataFrame:
    rows = []
    for k, lv in enumerate(fit.levels):
        m = fit.z == k
        row = {"arm": lv, "n": int(m.sum()), "ess": ess(w[m]),
               "min_ps_own_arm": float(fit.ps[m, k].min()) if m.any() else np.nan}
        if cluster is not None:
            row["firms"] = int(pd.Series(np.asarray(cluster)[m]).nunique())
        rows.append(row)
    t = pd.DataFrame(rows).set_index("arm")
    t.loc["TOTAL", "n"] = int(len(fit.z))
    t.loc["TOTAL", "ess"] = float(t["ess"].iloc[:-1].sum())
    if cluster is not None:
        t.loc["TOTAL", "firms"] = int(pd.Series(np.asarray(cluster)).nunique())
    return t


def balance_table(df: pd.DataFrame, fit: PSFit, w, covariates: list[str]) -> pd.DataFrame:
    """Max pairwise standardized mean difference across arms, before and after weighting.
    SD in the denominator: pooled unweighted SD across arms (fixed across comparisons)."""
    X, names = design_matrix(df, covariates)
    X, names = X[:, 1:], names[1:]
    out = []
    for j, nm in enumerate(names):
        x = X[:, j]
        sds = [x[fit.z == k].std(ddof=1) for k in range(len(fit.levels)) if (fit.z == k).sum() > 1]
        sd = np.sqrt(np.mean(np.square(sds))) if sds else np.nan
        raw, wtd = [], []
        for k in range(len(fit.levels)):
            m = fit.z == k
            raw.append(x[m].mean())
            wtd.append(np.average(x[m], weights=w[m]) if w[m].sum() > 0 else np.nan)
        def maxdiff(v):
            v = np.asarray(v)
            return float((np.nanmax(v) - np.nanmin(v)) / sd) if sd and sd > 0 else 0.0
        out.append({"covariate": nm, "max_smd_unweighted": maxdiff(raw), "max_smd_weighted": maxdiff(wtd)})
    return pd.DataFrame(out).set_index("covariate")


DEFAULT_GATES = {
    "min_n_per_arm": 20,
    "min_firms_per_arm": 12,
    "min_ess_per_arm": 12,
    "min_ess_total": 60,
    "max_abs_smd": 0.10,
    "min_ps_own_arm": 0.01,
}


def estimability_gates(ess_tab: pd.DataFrame, bal: pd.DataFrame, gates: dict, arms_needed=None) -> pd.DataFrame:
    """Outcome-blind gates. arms_needed: arms that enter the contrast (default: all)."""
    g = {**DEFAULT_GATES, **(gates or {})}
    arms = [a for a in ess_tab.index if a != "TOTAL"]
    arms = [a for a in arms if arms_needed is None or str(a) in {str(x) for x in arms_needed}]
    rows = []
    for a in arms:
        r = ess_tab.loc[a]
        rows.append((f"n[{a}] >= {g['min_n_per_arm']}", r["n"] >= g["min_n_per_arm"], r["n"]))
        if "firms" in ess_tab.columns:
            rows.append((f"firms[{a}] >= {g['min_firms_per_arm']}", r["firms"] >= g["min_firms_per_arm"], r["firms"]))
        rows.append((f"ESS[{a}] >= {g['min_ess_per_arm']}", r["ess"] >= g["min_ess_per_arm"], r["ess"]))
        rows.append((f"min own-arm PS[{a}] >= {g['min_ps_own_arm']}", r["min_ps_own_arm"] >= g["min_ps_own_arm"], r["min_ps_own_arm"]))
    tot = float(ess_tab.loc[arms, "ess"].sum())
    rows.append((f"ESS(total of arms used) >= {g['min_ess_total']}", tot >= g["min_ess_total"], tot))
    mx = float(bal["max_smd_weighted"].abs().max()) if len(bal) else 0.0
    rows.append((f"max |weighted SMD| <= {g['max_abs_smd']}", mx <= g["max_abs_smd"], mx))
    return pd.DataFrame(rows, columns=["gate", "pass", "value"]).set_index("gate")


def parse_contrast(spec: str, levels: list) -> np.ndarray:
    """'A-B'  or  'A:0.5,B:0.5,C:-0.5,D:-0.5'. Coefficients must sum to zero."""
    c = np.zeros(len(levels))
    names = [str(x) for x in levels]
    if ":" in spec:
        for part in spec.split(","):
            lv, val = part.rsplit(":", 1)
            c[names.index(lv.strip())] = float(val)
    else:
        a, b = [s.strip() for s in spec.split("-", 1)]
        c[names.index(a)] = 1.0
        c[names.index(b)] = -1.0
    if abs(c.sum()) > 1e-9:
        raise ValueError(f"contrast coefficients must sum to 0 (got {c.sum()})")
    return c


def arm_design(fit: PSFit) -> np.ndarray:
    D = np.zeros((len(fit.z), len(fit.levels)))
    D[np.arange(len(fit.z)), fit.z] = 1.0
    return D


def estimate_contrast(y, fit: PSFit, w, cluster, contrast: np.ndarray, vcov_type="CR2") -> tuple[dict, pd.DataFrame]:
    """Weighted arm means (overlap population) and a linear contrast with cluster-robust SE.
    SE treats weights as fixed; use cluster_bootstrap to include PS-estimation uncertainty."""
    res = wls_cluster(y, arm_design(fit), w=w, cluster=cluster, vcov_type=vcov_type, names=fit.levels)
    means = pd.DataFrame({"weighted_mean": res.coef, "se": np.sqrt(np.diag(res.vcov))}, index=pd.Index(fit.levels, name="arm"))
    out = res.contrast(contrast)
    out.update({"vcov_type": vcov_type, "clusters": res.n_clusters, "n": res.n})
    return out, means


def cluster_bootstrap(df: pd.DataFrame, treatment, covariates, outcome, cluster, contrast_spec, levels,
                      B: int = 999, seed: int = 1) -> dict:
    """Resample clusters (firms) with replacement; re-fit the PS model and weights in every
    resample. Failed resamples (arm missing, non-convergence) are counted, never dropped silently."""
    rng = np.random.default_rng(seed)
    ids = df[cluster].unique()
    by = {g: d for g, d in df.groupby(cluster)}
    c = parse_contrast(contrast_spec, levels)
    ests, fails = [], {"arm_missing": 0, "not_converged": 0, "error": 0}
    for _ in range(B):
        draw = rng.choice(ids, size=len(ids), replace=True)
        parts = []
        for j, g in enumerate(draw):
            d = by[g].copy()
            d[cluster] = f"b{j}"
            parts.append(d)
        bd = pd.concat(parts, ignore_index=True)
        if bd[treatment].nunique() < len(levels):
            fails["arm_missing"] += 1
            continue
        try:
            f = fit_ps(bd, treatment, covariates, levels)
            if not f.converged:
                fails["not_converged"] += 1
                continue
            w = gow_weights(f)
            mu = np.array([np.average(bd[outcome].to_numpy(float)[f.z == k], weights=w[f.z == k]) for k in range(len(levels))])
            ests.append(float(c @ mu))
        except Exception:
            fails["error"] += 1
    ests = np.asarray(ests)
    out = {"B_requested": B, "B_successful": int(len(ests)), "failures": fails}
    if len(ests) > 1:
        out.update({"boot_se": float(ests.std(ddof=1)),
                    "ci_low_percentile": float(np.quantile(ests, 0.025)),
                    "ci_high_percentile": float(np.quantile(ests, 0.975))})
    return out
