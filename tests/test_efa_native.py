"""Native EFA (numpy/scipy): recovers a known structure, and matches factor_analyzer when that package is installed."""
import itertools

import numpy as np
import pandas as pd
import pytest

from clockbind.analysis.factor import EFA, bartlett, kmo, oblimin, varimax


def _data(seed=7, n=400):
    rng = np.random.default_rng(seed)
    f = rng.normal(size=(n, 2))
    L = np.array([[.8, 0], [.7, .1], [.75, 0], [0, .8], [.1, .7], [0, .75]])
    return pd.DataFrame(f @ L.T + rng.normal(scale=.5, size=(n, 6)), columns=[f"i{k}" for k in range(6)]), L


@pytest.mark.parametrize("method", ["minres", "ml"])
@pytest.mark.parametrize("rotation", ["varimax", "promax", "oblimin"])
def test_recovers_simple_structure(method, rotation):
    X, _ = _data()
    L = EFA(2, method, rotation).fit(X).loadings_
    big = np.abs(L) > .5
    assert big[:3].sum(1).tolist() == [1, 1, 1] and big[3:].sum(1).tolist() == [1, 1, 1]
    assert big[:3, :].argmax(1).tolist().count(big[0].argmax()) == 3      # first three items share one factor


def test_rotations_are_rotations():
    A = np.random.default_rng(1).normal(size=(8, 3))
    V, T = varimax(A)
    assert np.allclose(T.T @ T, np.eye(3), atol=1e-10)                      # orthogonal
    assert np.allclose((V ** 2).sum(1), (A ** 2).sum(1))                     # communalities preserved
    P, T2, Phi = oblimin(A)
    assert np.allclose(np.diag(Phi), 1) and np.allclose(P @ Phi @ P.T, A @ A.T, atol=1e-8)   # same common variance


def test_kmo_bartlett_basic():
    X, _ = _data()
    per, tot = kmo(X)
    assert 0.5 < tot < 1 and len(per) == 6
    stat, p = bartlett(X)
    assert stat > 0 and p < 1e-10


def test_matches_factor_analyzer_when_installed():
    fa_pkg = pytest.importorskip("factor_analyzer")
    import warnings
    import factor_analyzer.factor_analyzer as fa_mod
    warnings.filterwarnings("ignore")
    try:                                    # scikit-learn >= 1.6 renamed force_all_finite
        import sklearn.utils.validation as skv
        orig = skv.check_array
        fa_mod.check_array = lambda *a, force_all_finite=None, **k: orig(*a, **({**k, "ensure_all_finite": force_all_finite} if force_all_finite is not None else k))
    except ImportError:
        pass
    worst = {}
    for seed in range(3):
        rng = np.random.default_rng(seed)
        f = rng.normal(size=(300, 3))
        Lt = rng.uniform(-.2, .9, size=(9, 3)) * (rng.random((9, 3)) > .5)
        X = pd.DataFrame(f @ Lt.T + rng.normal(scale=.6, size=(300, 9)))
        for k in (1, 2, 3):
            for m in ("minres", "ml", "principal"):
                for r in (None, "varimax", "promax", "oblimin"):
                    if k == 1 and r:
                        continue
                    a = fa_mod.FactorAnalyzer(n_factors=k, method=m, rotation=r).fit(X).loadings_[:, :k]
                    b = EFA(k, m, r).fit(X).loadings_
                    d = min(np.abs(np.abs(a) - np.abs(b[:, list(p)])).max() for p in itertools.permutations(range(k)))
                    worst[m] = max(worst.get(m, 0), d)
        pa, ta = fa_mod.calculate_kmo(X)
        assert np.isclose(ta, kmo(X)[1]) and np.allclose(pa, kmo(X)[0])
        assert np.allclose(fa_mod.calculate_bartlett_sphericity(X), bartlett(X))
    assert worst["minres"] < 1e-5 and worst["principal"] < 1e-8 and worst["ml"] < 5e-4
