"""Weighted least squares with cluster-robust variance estimators.

CR0  : plain cluster sandwich.
CR1  : CR0 * G/(G-1) * (N-1)/(N-p)   (same small-sample factor as Stata/statsmodels)
CR2  : Bell & McCaffrey (2002) bias-reduced linearization, as generalised by
       Pustejovsky & Tipton (2018), with working model Phi = I (weights treated
       as sampling/balancing weights, not inverse-variance weights). This matches
       clubSandwich::vcovCR(type = "CR2") defaults for lm with weights.
       With B = (X'WX)^{-1}, U = W X B, residuals e = y - Xb:
       M_g = I - X_g U_g' - U_g X_g' + X_g (U'U) X_g',   A_g = M_g^{-1/2},
       meat = sum_g X_g' W_g A_g e_g e_g' A_g W_g X_g.

Degrees of freedom for tests default to G - 1 (conservative relative to the
Satterthwaite approximation used by clubSandwich; see the README).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass
class WLSResult:
    coef: np.ndarray
    vcov: np.ndarray
    names: list
    n: int
    n_clusters: int
    vcov_type: str
    df: int

    def contrast(self, c, alpha: float = 0.05) -> dict:
        c = np.asarray(c, dtype=float)
        est = float(c @ self.coef)
        se = float(np.sqrt(max(c @ self.vcov @ c, 0.0)))
        tcrit = stats.t.ppf(1 - alpha / 2, self.df)
        tval = est / se if se > 0 else np.nan
        p = 2 * stats.t.sf(abs(tval), self.df) if se > 0 else np.nan
        return {"estimate": est, "se": se, "t": tval, "df": self.df, "p": p,
                "ci_low": est - tcrit * se, "ci_high": est + tcrit * se}


def _inv_sqrt_psd(m: np.ndarray, tol: float = 1e-12) -> np.ndarray:
    vals, vecs = np.linalg.eigh((m + m.T) / 2)
    inv = np.where(vals > tol, 1.0 / np.sqrt(np.clip(vals, tol, None)), 0.0)
    return (vecs * inv) @ vecs.T


def wls_cluster(y, X, w=None, cluster=None, vcov_type: str = "CR2", names=None) -> WLSResult:
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    n, p = X.shape
    w = np.ones(n) if w is None else np.asarray(w, dtype=float)
    if np.any(w < 0):
        raise ValueError("weights must be non-negative")
    keep = w > 0
    y, X, w = y[keep], X[keep], w[keep]
    cl = np.arange(n)[keep] if cluster is None else np.asarray(cluster)[keep]
    n = len(y)
    WX = X * w[:, None]
    bread = np.linalg.pinv(X.T @ WX)
    coef = bread @ (WX.T @ y)
    e = y - X @ coef
    U = WX @ bread
    UU = U.T @ U

    groups = {}
    for i, g in enumerate(cl):
        groups.setdefault(g, []).append(i)
    G = len(groups)
    meat = np.zeros((p, p))
    vt = vcov_type.upper()
    if vt not in ("CR0", "CR1", "CR2"):
        raise ValueError("vcov_type must be CR0, CR1 or CR2")
    for idx in groups.values():
        idx = np.asarray(idx)
        Xg, eg, wg = X[idx], e[idx], w[idx]
        if vt == "CR2":
            Ug = U[idx]
            M = np.eye(len(idx)) - Xg @ Ug.T - Ug @ Xg.T + Xg @ UU @ Xg.T
            eg = _inv_sqrt_psd(M) @ eg
        u = Xg.T @ (wg * eg)
        meat += np.outer(u, u)
    vcov = bread @ meat @ bread
    if vt == "CR1":
        vcov *= (G / (G - 1)) * ((n - 1) / (n - p))
    names = list(names) if names is not None else [f"x{j}" for j in range(p)]
    return WLSResult(coef=coef, vcov=vcov, names=names, n=n, n_clusters=G, vcov_type=vt, df=max(G - 1, 1))
