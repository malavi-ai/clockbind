"""Simulated data for Paper 3 design checks. ALL PARAMETERS ARE ASSUMPTIONS,
not empirical estimates. Every value used is written to the run manifest.

Structure: firms -> relationships. Firm-level random effects enter both
architecture choice and outcome (clustering + confounding). Four arms,
with adjustable shares so one arm can be rare. Binary outcome with
potential outcomes Y(k) generated for every unit, so the true
overlap-population contrast is known.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULTS = {
    "n_firms": 150,
    "mean_rel_per_firm": 2.0,       # relationships per firm = 1 + Poisson(mean-1)
    "arm_labels": ["focal", "partner", "bilateral", "third_party"],
    "arm_intercepts": [0.0, -0.3, 0.0, -1.2],   # logit scale; last arm rare
    "cov_effects_on_arm": 0.5,      # strength of confounding in treatment model
    "firm_sd_arm": 0.5,             # firm random effect in treatment model
    "base_logit": -0.4,             # outcome baseline
    "cov_effects_on_y": 0.4,
    "firm_sd_y": 0.6,               # firm random effect in outcome (ICC)
    "arm_effects": [0.0, 0.0, 0.0, 0.0],        # logit-scale effects; all zero = null
}


def _softmax(u):
    u = u - u.max(axis=1, keepdims=True)
    e = np.exp(u)
    return e / e.sum(axis=1, keepdims=True)


def simulate(params: dict, rng: np.random.Generator):
    p = {**DEFAULTS, **(params or {})}
    K = len(p["arm_labels"])
    sizes = 1 + rng.poisson(max(p["mean_rel_per_firm"] - 1, 0), size=p["n_firms"])
    firm = np.repeat(np.arange(p["n_firms"]), sizes)
    n = len(firm)
    fx = rng.normal(size=(p["n_firms"], 2))  # firm-level covariate components
    x1 = fx[firm, 0] + rng.normal(scale=0.7, size=n)
    x2 = fx[firm, 1] + rng.normal(scale=0.7, size=n)
    x3 = rng.binomial(1, 0.4, size=n).astype(float)
    X = np.column_stack([x1, x2, x3])
    # treatment model: arm-specific slopes create confounding
    rs = np.random.default_rng(12345)  # fixed slope pattern (part of the DGP, not a random draw)
    slopes = rs.normal(scale=1.0, size=(3, K)) * p["cov_effects_on_arm"]
    slopes[:, 0] = 0.0
    re_arm = rng.normal(scale=p["firm_sd_arm"], size=(p["n_firms"], K))
    re_arm[:, 0] = 0.0
    util = np.asarray(p["arm_intercepts"])[None, :] + X @ slopes + re_arm[firm]
    true_ps = _softmax(util)
    z = np.array([rng.choice(K, p=pr) for pr in true_ps])
    # outcome
    re_y = rng.normal(scale=p["firm_sd_y"], size=p["n_firms"])[firm]
    lin = p["base_logit"] + X @ np.array([p["cov_effects_on_y"], -p["cov_effects_on_y"], p["cov_effects_on_y"] / 2]) + re_y
    eff = np.asarray(p["arm_effects"], float)
    probs = 1 / (1 + np.exp(-(lin[:, None] + eff[None, :])))
    y_pot = (rng.random(size=(n, 1)) < probs).astype(float)  # common uniform: coupled potential outcomes
    y = y_pot[np.arange(n), z]
    df = pd.DataFrame({"firm": firm, "arm": np.array(p["arm_labels"])[z], "x1": x1, "x2": x2, "x3": x3, "y": y})
    truth = {"probs": probs, "true_ps": true_ps}
    return df, truth


def true_overlap_contrast(params: dict, contrast, n_big: int = 200_000, seed: int = 99) -> float:
    """Population value of sum_k c_k E_h[mu_k(X)] where h(x) = 1/sum_k 1/e_k(x) uses TRUE
    propensities (the overlap target population). Computed on one large simulated sample."""
    p = {**DEFAULTS, **(params or {})}
    big = {**p, "n_firms": int(n_big / max(p["mean_rel_per_firm"], 1))}
    _, truth = simulate(big, np.random.default_rng(seed))
    h = 1.0 / np.sum(1.0 / truth["true_ps"], axis=1)
    mu = (truth["probs"] * h[:, None]).sum(axis=0) / h.sum()
    return float(np.asarray(contrast, float) @ mu)
