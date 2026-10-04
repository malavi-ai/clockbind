"""Exploratory factor analysis implemented from the published algorithms (numpy/scipy only, MIT).

Extraction
* minres (unweighted least squares): uniquenesses psi minimise the squared residuals of the
  correlation matrix with 1 - psi on the diagonal (Harman & Jones, 1966; Revelle's psych::fa).
* ml: R stats::factanal likelihood (Lawley & Maxwell, 1971; Jöreskog, 1967).
* principal: principal-component loadings of the correlation matrix.
Both iterative methods start from 1 - SMC and use L-BFGS-B with bounds [0.005, 1].

Rotation
* varimax with Kaiser normalisation (Kaiser, 1958; R stats::varimax).
* promax, power 4, on Kaiser-normalised varimax loadings (Hendrickson & White, 1964).
* oblimin (gamma = 0, quartimin) by the gradient projection algorithm
  (Jennrich, 2002; Bernaards & Jennrich, 2005).

Conventions: column signs are set so that each column sum is positive; factors are ordered by
explained variance (not for principal). Results agree with the factor_analyzer package to optimiser
tolerance (see tests); this module does not use or contain that package's code.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from scipy.stats import chi2

EPS = np.finfo(float).eps


def corr(X) -> np.ndarray:
    return np.corrcoef(np.asarray(X, dtype=float), rowvar=False)


def smc(R) -> np.ndarray:
    return 1 - 1 / np.diag(np.linalg.inv(R))


def kmo(X):
    R = corr(X)
    Ri = np.linalg.inv(R)
    d = np.sqrt(np.outer(np.diag(Ri), np.diag(Ri)))
    P = -Ri / d                                   # partial (anti-image) correlations
    np.fill_diagonal(P, 0)
    R0 = R.copy()
    np.fill_diagonal(R0, 0)
    r2, p2 = R0 ** 2, P ** 2
    per = r2.sum(0) / (r2.sum(0) + p2.sum(0))
    return per, float(r2.sum() / (r2.sum() + p2.sum()))


def bartlett(X):
    n, p = np.asarray(X).shape
    stat = -np.log(np.linalg.det(corr(X))) * (n - 1 - (2 * p + 5) / 6)
    df = p * (p - 1) / 2
    return float(stat), float(chi2.sf(stat, df))


def _top_eig(M, k):
    w, v = np.linalg.eigh(M)
    return w[::-1][:k], v[:, ::-1][:, :k]


def _uls_loadings(psi, R, k, floor=False):
    M = R.copy()
    np.fill_diagonal(M, 1 - psi)
    w, v = _top_eig(M, k)
    w = np.maximum(w, EPS * 100) if floor else np.maximum(w, 0)
    return v * np.sqrt(w)


def _uls_obj(psi, R, k):
    M = R.copy()
    np.fill_diagonal(M, 1 - psi)
    L = _uls_loadings(psi, R, k, floor=True)
    return float(((M - L @ L.T) ** 2).sum())


def _ml_obj(psi, R, k):
    s = 1 / np.sqrt(psi)
    w = np.linalg.eigvalsh(R * np.outer(s, s))[::-1][k:]
    return float(-(np.sum(np.log(w) - w) - k + R.shape[0]))


def _ml_loadings(psi, R, k):
    s = 1 / np.sqrt(psi)
    w, v = _top_eig(R * np.outer(s, s), k)
    return np.sqrt(psi)[:, None] * (v * np.sqrt(np.maximum(w - 1, 0)))


def varimax(A, normalize=True, max_iter=500, tol=1e-5):
    A = np.asarray(A, float)
    p, k = A.shape
    if k < 2:
        return A.copy(), np.eye(k)
    h = np.sqrt((A ** 2).sum(1)) if normalize else np.ones(p)
    X = A / h[:, None]
    T, d = np.eye(k), 0.0
    for _ in range(max_iter):
        Z = X @ T
        B = X.T @ (Z ** 3 - Z @ np.diag((Z ** 2).sum(0)) / p)
        u, sv, vt = np.linalg.svd(B)
        T = u @ vt
        d_old, d = d, sv.sum()
        if d < d_old * (1 + tol):
            break
    return (X @ T) * h[:, None], T


def promax(A, power=4, normalize=True):
    A = np.asarray(A, float)
    k = A.shape[1]
    if k < 2:
        return A.copy(), np.eye(k), None
    h = np.sqrt((A ** 2).sum(1)) if normalize else np.ones(A.shape[0])
    X, T = varimax(A / h[:, None], normalize=normalize)
    Y = X * np.abs(X) ** (power - 1)
    U = np.linalg.lstsq(X, Y, rcond=None)[0]
    try:
        dinv = np.diag(np.linalg.inv(U.T @ U))
    except np.linalg.LinAlgError:
        dinv = np.diag(np.linalg.pinv(U.T @ U))
    U = U * np.sqrt(dinv)
    Z = (X @ U) * h[:, None]
    Ui = np.linalg.inv(U)
    return Z, T @ U, Ui @ Ui.T


def _quartimin(L):
    L2 = L ** 2
    N = np.ones((L.shape[1],) * 2) - np.eye(L.shape[1])
    X = L2 @ N
    return float((L2 * X).sum() / 4), L * X


def oblimin(A, max_iter=500, tol=1e-5):
    """Quartimin (oblimin, gamma = 0) by gradient projection; returns pattern, T, Phi."""
    A = np.asarray(A, float)
    k = A.shape[1]
    if k < 2:
        return A.copy(), np.eye(k), None
    T = np.eye(k)
    L = A @ np.linalg.inv(T).T
    f, Gq = _quartimin(L)
    G = -(L.T @ Gq @ np.linalg.inv(T)).T
    al = 1.0
    for _ in range(max_iter + 1):
        Gp = G - T @ np.diag((T * G).sum(0))
        s = np.sqrt((Gp ** 2).sum())
        if s < tol:
            break
        al *= 2
        for _ in range(11):
            X = T - al * Gp
            Tt = X / np.sqrt((X ** 2).sum(0))
            Lt = A @ np.linalg.inv(Tt).T
            ft, Gqt = _quartimin(Lt)
            if ft < f - 0.5 * s ** 2 * al:
                break
            al /= 2
        T, L, f, Gq = Tt, Lt, ft, Gqt
        G = -(L.T @ Gq @ np.linalg.inv(T)).T
    return L, T, T.T @ T


class EFA:
    """Fit with EFA(n_factors, method, rotation).fit(X); attributes loadings_, phi_, uniquenesses_, communalities_."""

    def __init__(self, n_factors=1, method="minres", rotation=None, bounds=(0.005, 1.0)):
        if method not in ("minres", "uls", "ml", "mle", "principal"):
            raise ValueError("method must be minres, ml or principal")
        if rotation not in (None, "none", "varimax", "promax", "oblimin"):
            raise ValueError("rotation must be varimax, promax, oblimin or none")
        self.k, self.method, self.rotation, self.bounds = int(n_factors), method, (None if rotation == "none" else rotation), bounds

    def fit(self, X):
        X = np.asarray(X, float)
        R = corr(X)
        self.corr_ = R
        k, p = self.k, R.shape[0]
        self.converged_ = True
        if self.method == "principal":
            w, v = _top_eig(R, k)
            L = v * np.sqrt(np.maximum(w, 0))
        else:
            ml = self.method in ("ml", "mle")
            start = 1 - smc(R)
            res = minimize(_ml_obj if ml else _uls_obj, start, args=(R, k), method="L-BFGS-B",
                           bounds=[self.bounds] * p, options={"maxiter": 1000})
            self.converged_ = bool(res.success)
            L = (_ml_loadings if ml else _uls_loadings)(res.x, R, k)
        phi = None
        if self.rotation and k > 1:
            if self.rotation == "varimax":
                L, _ = varimax(L)
            elif self.rotation == "promax":
                L, _, phi = promax(L)
            else:
                L, _, phi = oblimin(L)
        if k > 1:
            sg = np.sign(L.sum(0))
            sg[sg == 0] = 1
            L = L * sg
            if phi is not None:
                phi = phi * np.outer(sg, sg)
        elif L.sum() < 0:
            L = -L
        if self.method != "principal":
            order = np.argsort((L ** 2).sum(0))[::-1]
            L = L[:, order]
            if phi is not None:
                phi = phi[np.ix_(order, order)]
        self.loadings_, self.phi_ = L, phi
        self.communalities_ = (L ** 2).sum(1)
        self.uniquenesses_ = 1 - self.communalities_
        return self

    def factor_variance(self):
        v = (self.loadings_ ** 2).sum(0)
        prop = v / self.loadings_.shape[0]
        return v, prop, np.cumsum(prop)
