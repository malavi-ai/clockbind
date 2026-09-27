"""Performance measures with Monte Carlo standard errors (Morris, White & Crowther, 2019)."""
from __future__ import annotations

import numpy as np


def performance(est, se, lo, hi, p, truth: float, alpha: float = 0.05, n_attempted: int | None = None) -> dict:
    est, se, lo, hi, p = (np.asarray(v, float) for v in (est, se, lo, hi, p))
    ok = np.isfinite(est) & np.isfinite(se)
    est, se, lo, hi, p = est[ok], se[ok], lo[ok], hi[ok], p[ok]
    n = len(est)
    out = {"n_valid": int(n)}
    if n_attempted is not None:
        out["n_attempted"] = int(n_attempted)
        out["estimable_rate"] = n / n_attempted if n_attempted else np.nan
        out["estimable_rate_mcse"] = float(np.sqrt(out["estimable_rate"] * (1 - out["estimable_rate"]) / n_attempted)) if n_attempted else np.nan
    if n < 2:
        return out
    bias = est.mean() - truth
    emp_se = est.std(ddof=1)
    cover = np.mean((lo <= truth) & (truth <= hi))
    rej = np.mean(p < alpha)
    mod_se = np.sqrt(np.mean(se ** 2))
    out.update({
        "true_value": truth,
        "mean_estimate": float(est.mean()),
        "bias": float(bias), "bias_mcse": float(emp_se / np.sqrt(n)),
        "empirical_se": float(emp_se), "empirical_se_mcse": float(emp_se / np.sqrt(2 * (n - 1))),
        "model_se": float(mod_se),
        "model_se_relative_error_pct": float(100 * (mod_se / emp_se - 1)) if emp_se > 0 else np.nan,
        "rmse": float(np.sqrt(np.mean((est - truth) ** 2))),
        "coverage": float(cover), "coverage_mcse": float(np.sqrt(cover * (1 - cover) / n)),
        "rejection_rate": float(rej), "rejection_rate_mcse": float(np.sqrt(rej * (1 - rej) / n)),
    })
    return out
