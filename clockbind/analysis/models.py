"""Regression family: linear (classical / HC3 / CR1 / CR2), logistic, multinomial, ordinal."""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from ..stats.robust import wls_cluster
from .core import Output, analysis, as_list, fmt_p
from .style import BRASS, INK, MUTED, REF, SLATE, fig

PRED = [{"name": "y", "label": "Dependent variable", "type": "column"},
        {"name": "x", "label": "Numeric predictors", "type": "columns", "multi": True, "numeric": True, "optional": True},
        {"name": "categorical", "label": "Categorical predictors (first level = reference)", "type": "columns", "multi": True, "optional": True}]


def _design(df, y, x, categorical, extra=(), y_numeric=False):
    x, cat = as_list(x), as_list(categorical)
    cols = [y] + x + cat + [e for e in extra if e]
    d = df[cols].copy()
    for c in ([y] if y_numeric else []) + x:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna()
    parts = [d[x]] if x else []
    for c in cat:
        lv = sorted(d[c].astype(str).unique())
        parts.append(pd.get_dummies(d[c].astype(str), prefix=c, prefix_sep="=", dtype=float).drop(columns=f"{c}={lv[0]}"))
    X = pd.concat(parts, axis=1) if parts else pd.DataFrame(index=d.index)
    X.insert(0, "(Intercept)", 1.0)
    return d, X


def _coef_plot(tab, est="B", lo="95% CI low", hi="95% CI high", title="Coefficients (95% CI)", ref=0.0):
    t = tab[tab.index != "(Intercept)"] if "(Intercept)" in tab.index else tab
    f, ax = fig(6.8, 0.42 * len(t) + 1.4)
    y = np.arange(len(t))[::-1]
    ax.hlines(y, t[lo], t[hi], color=SLATE, lw=2)
    ax.plot(t[est], y, "o", color=INK, ms=7)
    ax.axvline(ref, color=BRASS, lw=1.2, ls="--")
    ax.set_yticks(y); ax.set_yticklabels(t.index); ax.set_title(title); ax.grid(axis="y", visible=False)
    return f


@analysis("regression_linear", "Linear regression", "Regression",
          PRED + [{"name": "se", "label": "Standard errors", "type": "choice", "choices": ["classical", "HC3", "CR1", "CR2"], "default": "classical"},
                  {"name": "cluster", "label": "Cluster variable (for CR1/CR2)", "type": "column", "optional": True},
                  {"name": "weight", "label": "Weight variable (optional)", "type": "column", "optional": True}])
def regression_linear(df, y, x=None, categorical=None, se="classical", cluster=None, weight=None):
    d, X = _design(df, y, x, categorical, extra=(cluster, weight), y_numeric=True)
    yy = pd.to_numeric(d[y], errors="coerce").to_numpy(float)
    w = pd.to_numeric(d[weight], errors="coerce").to_numpy(float) if weight else None
    out = Output("regression_linear", f"Linear regression: {y}", {}); out.n_used = len(d)
    ols = (sm.WLS(yy, X, weights=w) if w is not None else sm.OLS(yy, X)).fit()
    if se in ("CR1", "CR2"):
        if not cluster:
            raise ValueError("CR1/CR2 need a cluster variable.")
        r = wls_cluster(yy, X.to_numpy(float), w=w, cluster=d[cluster].to_numpy(), vcov_type=se, names=list(X.columns))
        rows = []
        for j, nm in enumerate(r.names):
            c = np.zeros(len(r.names)); c[j] = 1; ct = r.contrast(c)
            rows.append({"term": nm, "B": ct["estimate"], "SE": ct["se"], "t": ct["t"], "df": ct["df"], "p": ct["p"], "95% CI low": ct["ci_low"], "95% CI high": ct["ci_high"]})
        tab = pd.DataFrame(rows).set_index("term")
        note = f"{se} cluster-robust standard errors ({r.n_clusters} clusters), t-tests with G − 1 = {r.df} df."
        out.ref(REF["cr2"], REF["bell_mccaffrey"])
    else:
        res = ols if se == "classical" else ols.get_robustcov_results(cov_type="HC3")
        ci = np.asarray(res.conf_int())
        tab = pd.DataFrame({"B": res.params, "SE": res.bse, "t": res.tvalues, "df": res.df_resid, "p": res.pvalues, "95% CI low": ci[:, 0], "95% CI high": ci[:, 1]}, index=X.columns)
        note = "Classical OLS standard errors." if se == "classical" else "HC3 heteroskedasticity-consistent standard errors."
        if se == "HC3":
            out.ref(REF["hc3"])
    if w is None:
        sd_y = np.std(yy, ddof=1)
        tab["Beta"] = [np.nan if c == "(Intercept)" else tab.loc[c, "B"] * X[c].std(ddof=1) / sd_y for c in tab.index]
    out.table(pd.DataFrame([{"N": len(d), "R²": ols.rsquared, "Adjusted R²": ols.rsquared_adj, "F": ols.fvalue, "df1": ols.df_model, "df2": ols.df_resid, "p (F)": ols.f_pvalue,
                             "RMSE": np.sqrt(ols.mse_resid)}]), "Model summary", "R² and F from the (weighted) least-squares fit; the F-test uses classical errors.")
    out.table(tab, "Coefficients", note)
    if X.shape[1] > 2:
        from statsmodels.stats.outliers_influence import variance_inflation_factor
        vif = pd.DataFrame({"VIF": [variance_inflation_factor(X.to_numpy(float), j) for j in range(1, X.shape[1])]}, index=X.columns[1:])
        out.table(vif, "Collinearity (VIF)", "Values above 5–10 indicate problematic collinearity.")
    out.figure(_coef_plot(tab))
    f, ax = fig(5.8, 3.6)
    ax.scatter(ols.fittedvalues, ols.resid, s=12, color=INK, alpha=.7); ax.axhline(0, color=BRASS, lw=1.2)
    ax.set_xlabel("Fitted"); ax.set_ylabel("Residual"); ax.set_title("Residuals vs fitted")
    out.figure(f)
    out.methods(f"{y} was regressed on {', '.join(X.columns[1:])} by {'weighted ' if w is not None else ''}least squares (N = {len(d)}, R² = {ols.rsquared:.3f}); {note}")
    out.ref(REF["statsmodels"])
    return out


@analysis("regression_logistic", "Binary logistic regression", "Regression",
          PRED + [{"name": "event", "label": "Event value of the dependent variable (default: higher / 1)", "type": "text", "optional": True},
                  {"name": "cluster", "label": "Cluster variable (optional, CR1)", "type": "column", "optional": True}])
def regression_logistic(df, y, x=None, categorical=None, event=None, cluster=None):
    d, X = _design(df, y, x, categorical, extra=(cluster,))
    vals = sorted(d[y].astype(str).unique())
    if len(vals) != 2:
        raise ValueError(f"{y} must have exactly two values; found {vals}")
    ev = str(event) if event not in (None, "") else vals[-1]
    yy = (d[y].astype(str) == ev).astype(float).to_numpy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = sm.Logit(yy, X)
        res = m.fit(disp=False, maxiter=200, cov_type="cluster", cov_kwds={"groups": pd.factorize(d[cluster])[0]}) if cluster else m.fit(disp=False, maxiter=200)
    ci = np.asarray(res.conf_int())
    tab = pd.DataFrame({"B": res.params, "SE": res.bse, "z": res.tvalues, "p": res.pvalues, "Odds ratio": np.exp(res.params),
                        "OR 95% CI low": np.exp(ci[:, 0]), "OR 95% CI high": np.exp(ci[:, 1])}, index=X.columns)
    n = len(d); ll0, ll1 = res.llnull, res.llf
    cs = 1 - np.exp(2 * (ll0 - ll1) / n); nag = cs / (1 - np.exp(2 * ll0 / n))
    out = Output("regression_logistic", f"Logistic regression: P({y} = {ev})", {}); out.n_used = n
    out.table(pd.DataFrame([{"N": n, "Events": int(yy.sum()), "−2LL": -2 * ll1, "LR χ²": 2 * (ll1 - ll0), "df": res.df_model, "p": stats.chi2.sf(2 * (ll1 - ll0), res.df_model),
                             "McFadden R²": 1 - ll1 / ll0, "Cox & Snell R²": cs, "Nagelkerke R²": nag, "AIC": res.aic}]), "Model summary")
    out.table(tab, "Coefficients", ("Cluster-robust (CR1) standard errors. " if cluster else "") + "Wald tests; odds-ratio intervals exponentiate the coefficient intervals.")
    pred = (res.predict(X) >= .5).astype(int)
    ct = pd.crosstab(pd.Series(yy.astype(int), name="Observed"), pd.Series(np.asarray(pred), name="Predicted"))
    out.table(ct, "Classification table (cut-off 0.5)", f"Overall correct: {100 * (np.asarray(pred) == yy).mean():.1f}%.")
    tp = tab.rename(columns={"Odds ratio": "OR"})
    f = _coef_plot(tp.assign(**{"95% CI low": tab["OR 95% CI low"], "95% CI high": tab["OR 95% CI high"]}), est="OR", title="Odds ratios (95% CI)", ref=1.0)
    f.axes[0].set_xscale("log")
    out.figure(f)
    out.ref(REF["statsmodels"])
    return out


@analysis("regression_multinomial", "Multinomial logistic regression", "Regression",
          PRED + [{"name": "base", "label": "Reference category (default: first)", "type": "text", "optional": True}])
def regression_multinomial(df, y, x=None, categorical=None, base=None):
    d, X = _design(df, y, x, categorical)
    cats = sorted(d[y].astype(str).unique())
    b = str(base) if base not in (None, "") else cats[0]
    order = [b] + [c for c in cats if c != b]
    z = d[y].astype(str).map({c: i for i, c in enumerate(order)}).to_numpy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = sm.MNLogit(z, X).fit(method="newton", disp=False, maxiter=300)
    out = Output("regression_multinomial", f"Multinomial logistic regression: {y} (reference = {b})", {}); out.n_used = len(d)
    rows = []
    for k, cat in enumerate(order[1:]):
        for j, nm in enumerate(X.columns):
            B, SE = res.params.iloc[j, k], res.bse.iloc[j, k]
            rows.append({"Outcome": cat, "term": nm, "B": B, "SE": SE, "z": B / SE, "p": 2 * stats.norm.sf(abs(B / SE)), "RRR": np.exp(B),
                         "RRR 95% CI low": np.exp(B - 1.959964 * SE), "RRR 95% CI high": np.exp(B + 1.959964 * SE)})
    out.table(pd.DataFrame([{"N": len(d), "Log-likelihood": res.llf, "LR χ²": res.llr, "df": res.df_model, "p": res.llr_pvalue, "McFadden R²": res.prsquared, "AIC": res.aic}]), "Model summary")
    out.table(pd.DataFrame(rows), "Coefficients (vs reference category)", "RRR = relative-risk ratio.")
    out.ref(REF["statsmodels"])
    return out


@analysis("regression_ordinal", "Ordinal logistic regression", "Regression",
          PRED + [{"name": "order", "label": "Category order, low to high (comma-separated; default: sorted)", "type": "text", "optional": True}])
def regression_ordinal(df, y, x=None, categorical=None, order=None):
    from statsmodels.miscmodels.ordinal_model import OrderedModel
    d, X = _design(df, y, x, categorical)
    cats = as_list(order) or sorted(d[y].astype(str).unique(), key=lambda s: (float(s) if s.replace('.', '', 1).lstrip('-').isdigit() else np.inf, s))
    yy = pd.Categorical(d[y].astype(str), categories=cats, ordered=True)
    Xn = X.drop(columns="(Intercept)")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = OrderedModel(pd.Series(yy), Xn, distr="logit")
        res = m.fit(method="bfgs", disp=False, maxiter=2000)
    k = Xn.shape[1]
    beta, se = res.params.iloc[:k], res.bse.iloc[:k]
    thr = m.transform_threshold_params(res.params)[1:-1]
    out = Output("regression_ordinal", f"Ordinal (proportional-odds) logistic regression: {y}", {}); out.n_used = len(d)
    tab = pd.DataFrame({"B": beta, "SE": se, "z": beta / se, "p": 2 * stats.norm.sf(np.abs(beta / se)), "Odds ratio": np.exp(beta)})
    out.table(tab, "Coefficients", "Model: logit P(Y ≤ k) = τ_k − xβ (same parametrisation as R MASS::polr).")
    out.table(pd.DataFrame({"Threshold": [f"{cats[i]} | {cats[i + 1]}" for i in range(len(cats) - 1)], "τ": thr}), "Thresholds")
    out.table(pd.DataFrame([{"N": len(d), "Log-likelihood": res.llf, "AIC": res.aic}]), "Model summary")
    out.ref(REF["statsmodels"])
    return out
