"""Choice-based conjoint with a task-level factor (e.g. HIGH/LOW enforceability applied
to both profiles in a task) and a Reject Both outside option.

Estimation: linear probability model on profile rows (chosen = 1/0; Reject Both means both
rows are 0), respondent-clustered CR2 standard errors. AMCEs are on the probability scale.
The task-level factor cannot have a candidate-level AMCE; its role is estimated through
attribute x factor interactions (e.g. delta_C = standards_compliance x enforceability).
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from .robust import wls_cluster


# ---------------------------------------------------------------- design
def _allowed(profile: dict, restrictions: list[dict]) -> bool:
    return not any(all(profile.get(k) == v for k, v in r.items()) for r in restrictions or [])


def generate_design(cfg: dict, rng: np.random.Generator) -> pd.DataFrame:
    attrs: dict = cfg["attributes"]
    tf = cfg.get("task_factor")
    n_blocks, n_tasks = int(cfg["n_blocks"]), int(cfg["n_tasks"])
    restr = cfg.get("restrictions", [])
    rows = []
    for b in range(1, n_blocks + 1):
        if tf:
            lv = list(tf["levels"])
            seq = (lv * (n_tasks // len(lv) + 1))[:n_tasks]
            rng.shuffle(seq)
        for t in range(1, n_tasks + 1):
            for _ in range(10_000):
                prof = [{a: rng.choice(levels) for a, levels in attrs.items()} for _ in range(2)]
                if all(_allowed(p, restr) for p in prof) and prof[0] != prof[1]:
                    break
            else:
                raise RuntimeError("Could not draw allowed profiles; restrictions too tight")
            for label, p in zip(["A", "B"], prof):
                row = {"block": b, "task": t, "profile": label, **{k: str(v) for k, v in p.items()}}
                if tf:
                    row[tf["name"]] = seq[t - 1]
                rows.append(row)
    return pd.DataFrame(rows)


def design_diagnostics(design: pd.DataFrame, cfg: dict) -> dict[str, pd.DataFrame]:
    attrs = list(cfg["attributes"])
    freq = []
    for a in attrs:
        vc = design[a].value_counts(normalize=True)
        for lv, sh in vc.items():
            freq.append({"attribute": a, "level": lv, "share": sh, "expected": 1 / len(cfg["attributes"][a])})
    out = {"level_balance": pd.DataFrame(freq).set_index(["attribute", "level"])}
    cv = []
    for a, b in itertools.combinations(attrs, 2):
        ct = pd.crosstab(design[a], design[b]).to_numpy(float)
        n = ct.sum()
        e = ct.sum(1, keepdims=True) @ ct.sum(0, keepdims=True) / n
        chi2 = ((ct - e) ** 2 / np.where(e > 0, e, 1)).sum()
        k = min(ct.shape) - 1
        cv.append({"pair": f"{a} x {b}", "cramers_v": float(np.sqrt(chi2 / (n * k))) if k > 0 else 0.0})
    out["attribute_association"] = pd.DataFrame(cv).set_index("pair")
    tf = cfg.get("task_factor")
    if tf:
        out["task_factor_by_block"] = pd.crosstab(design["block"], design[tf["name"]]) / 2
    return out


# ---------------------------------------------------------------- analysis
def _dummies(df: pd.DataFrame, attrs: list[str], baselines: dict) -> pd.DataFrame:
    parts = []
    for a in attrs:
        cats = sorted(df[a].astype(str).unique())
        base = str(baselines.get(a, cats[0]))
        for lv in cats:
            if lv != base:
                parts.append(pd.Series((df[a].astype(str) == lv).astype(float), name=f"{a}={lv}"))
    return pd.concat(parts, axis=1)


def analyze(df: pd.DataFrame, attrs: list[str], chosen: str, respondent: str,
            factor: str | None = None, interact: list[str] | None = None,
            baselines: dict | None = None, factor_baseline: str | None = None, vcov: str = "CR2") -> dict:
    baselines = baselines or {}
    D = _dummies(df, attrs, baselines)
    y = df[chosen].to_numpy(float)
    cl = df[respondent].to_numpy()
    out = {}
    # 1. pooled AMCEs
    X = np.column_stack([np.ones(len(df)), D.to_numpy()])
    names = ["const"] + list(D.columns)
    r = wls_cluster(y, X, cluster=cl, vcov_type=vcov, names=names)
    out["amce"] = _coef_table(r)
    # 2. interactions with the task-level factor
    if factor:
        levels = sorted(df[factor].astype(str).unique())
        fb = str(factor_baseline or levels[0])
        F = pd.concat([pd.Series((df[factor].astype(str) == lv).astype(float), name=f"{factor}={lv}")
                       for lv in levels if lv != fb], axis=1)
        inter_cols = [c for c in D.columns if interact is None or c.split("=")[0] in interact]
        I = pd.concat([(D[c] * F[f]).rename(f"{c} x {f}") for c in inter_cols for f in F.columns], axis=1)
        Xi = np.column_stack([np.ones(len(df)), D.to_numpy(), F.to_numpy(), I.to_numpy()])
        names_i = ["const"] + list(D.columns) + list(F.columns) + list(I.columns)
        ri = wls_cluster(y, Xi, cluster=cl, vcov_type=vcov, names=names_i)
        tab = _coef_table(ri)
        out["interaction_model"] = tab
        out["interactions"] = tab.loc[[n for n in names_i if " x " in n]]
        # reject-both rate by factor level (task level)
        task = df.groupby([respondent, "task"]).agg(any_chosen=(chosen, "max"), f=(factor, "first"))
        out["reject_both_rate"] = (1 - task.groupby("f")["any_chosen"].mean()).to_frame("reject_both_rate")
    out["model_info"] = pd.DataFrame({"value": [len(df), int(pd.Series(cl).nunique()), vcov]},
                                     index=["profile_rows", "respondents", "vcov"])
    return out


def _coef_table(r) -> pd.DataFrame:
    rows = []
    for j, nm in enumerate(r.names):
        c = np.zeros(len(r.names)); c[j] = 1
        rows.append({"term": nm, **{k: v for k, v in r.contrast(c).items() if k in ("estimate", "se", "t", "p", "ci_low", "ci_high")}})
    return pd.DataFrame(rows).set_index("term")


# ---------------------------------------------------------------- simulation of respondents
def simulate_choices(design: pd.DataFrame, cfg: dict, sim: dict, n_resp: int, rng: np.random.Generator) -> pd.DataFrame:
    """Logit choice among A, B and Reject Both. sim holds ASSUMED utilities:
       utilities: {"attr=level": beta}, interaction: {"attr=level x factor=LEVEL": beta},
       outside: alpha0, outside_by_factor: {"LEVEL": shift}, heterogeneity_sd, fatigue (0-1).
    Respondents are assigned to blocks in rotation."""
    tf = cfg.get("task_factor")
    fname = tf["name"] if tf else None
    des = design.sort_values(["block", "task", "profile"]).reset_index(drop=True)
    util = sim.get("utilities", {})
    keys = list(util)
    beta = np.array([util[k] for k in keys], float)
    ind = np.column_stack([(des[k.split("=", 1)[0]].astype(str) == k.split("=", 1)[1]).to_numpy(float) for k in keys]) if keys else np.zeros((len(des), 0))
    inter = np.zeros(len(des))
    for k, b in sim.get("interaction", {}).items():
        left, right = k.split(" x ")
        a, lv = left.split("=", 1)
        f, flv = right.split("=", 1)
        inter += b * ((des[a].astype(str) == lv) & (des[f].astype(str) == flv)).to_numpy(float)
    het = float(sim.get("heterogeneity_sd", 0.0))
    fat = float(sim.get("fatigue", 0.0))
    n_tasks = int(des["task"].max())
    blocks = list(des["block"].unique())
    by_block = {b: np.where(des["block"].to_numpy() == b)[0] for b in blocks}
    ob = sim.get("outside_by_factor", {})
    frames = []
    for r in range(n_resp):
        idx = by_block[blocks[r % len(blocks)]]
        noise = rng.normal(0, het, size=len(beta)) if het > 0 else 0.0
        u = ind[idx] @ (beta + noise) + inter[idx]
        u = u.reshape(-1, 2)                       # tasks x (A, B)
        tasks = des["task"].to_numpy()[idx][::2]
        u0 = float(sim.get("outside", 0.0)) + (np.array([float(ob.get(str(v), 0.0)) for v in des[fname].to_numpy()[idx][::2]]) if fname else 0.0)
        scale = 1.0 - fat * (tasks - 1) / max(n_tasks - 1, 1)
        U = np.column_stack([u, np.broadcast_to(u0, len(tasks))]) * scale[:, None]
        U -= U.max(axis=1, keepdims=True)
        P = np.exp(U); P /= P.sum(axis=1, keepdims=True)
        pick = (rng.random(len(tasks))[:, None] > np.cumsum(P, axis=1)).sum(axis=1)
        chosen = np.column_stack([pick == 0, pick == 1]).astype(int).ravel()
        f = des.iloc[idx].copy()
        f.insert(0, "respondent", r)
        f["chosen"] = chosen
        frames.append(f)
    return pd.concat(frames, ignore_index=True)
