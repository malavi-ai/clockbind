"""Reliability (alpha, omega, ICC), rater agreement (kappa, weighted kappa, AC1), EFA, CFA (lavaan), power."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from .core import Output, analysis, as_list, numeric
from .style import BRASS, INK, REF, SLATE, TEAL, fig


# EFA, KMO, Bartlett and the omega loadings use ClockBind's own implementation (analysis/factor.py,
# numpy/scipy only); factor_analyzer is no longer required. Agreement with it is checked in the tests.
from .factor import EFA, bartlett as _bartlett, kmo as _kmo


# ----------------------------------------------------------------- reliability
def cronbach_alpha(X: pd.DataFrame) -> float:
    k = X.shape[1]
    return k / (k - 1) * (1 - X.var(ddof=1).sum() / X.sum(axis=1).var(ddof=1))


def one_factor_omega(X: pd.DataFrame):
    fa = EFA(n_factors=1, method="ml").fit(X)
    lam = fa.loadings_[:, 0]
    lam = lam * np.sign(lam.sum()) if lam.sum() != 0 else lam
    uniq = 1 - lam ** 2
    return float(lam.sum() ** 2 / (lam.sum() ** 2 + uniq.sum())), lam


@analysis("reliability", "Scale reliability (α, ω)", "Scale",
          [{"name": "items", "label": "Items", "type": "columns", "multi": True, "numeric": True},
           {"name": "reverse", "label": "Reverse-scored items (optional)", "type": "columns", "multi": True, "optional": True},
           {"name": "scale_min", "label": "Scale minimum (for reversing)", "type": "number", "default": 1},
           {"name": "scale_max", "label": "Scale maximum (for reversing)", "type": "number", "default": 5}])
def reliability(df, items, reverse=None, scale_min=1, scale_max=5):
    its = as_list(items); rev = as_list(reverse)
    X = numeric(df, its).dropna()
    for r in rev:
        X[r] = scale_min + scale_max - X[r]
    out = Output("reliability", "Scale reliability", {}); out.n_used = len(X)
    a = cronbach_alpha(X)
    C = X.corr(); k = len(its); rbar = (C.values.sum() - k) / (k * (k - 1))
    a_std = k * rbar / (1 + (k - 1) * rbar)
    om, lam = one_factor_omega(X)
    out.table(pd.DataFrame([{"N (listwise)": len(X), "Items": k, "Cronbach's α": a, "Standardised α": a_std, "McDonald's ω (total, 1 factor)": om, "Mean inter-item r": rbar}]), "Reliability")
    rows = []
    total = X.sum(axis=1)
    for c in its:
        rest = total - X[c]
        rows.append({"Item": c + (" (reversed)" if c in rev else ""), "Mean": X[c].mean(), "SD": X[c].std(ddof=1), "Corrected item–total r": np.corrcoef(X[c], rest)[0, 1],
                     "α if item deleted": cronbach_alpha(X.drop(columns=c)), "Loading (1-factor ML)": lam[its.index(c)]})
    out.table(pd.DataFrame(rows), "Item statistics", "ω from a one-factor maximum-likelihood solution: ω = (Σλ)² / ((Σλ)² + Σθ).")
    out.methods(f"Internal consistency of the {k}-item scale was α = {a:.2f} and ω = {om:.2f} (N = {len(X)}).")
    out.ref(REF["cronbach"], REF["mcdonald"])
    return out


# ----------------------------------------------------------------- agreement
def gwet_ac1(x, y, cats):
    po = np.mean(np.asarray(x) == np.asarray(y))
    q = len(cats)
    pi = np.array([(np.mean(np.asarray(x) == c) + np.mean(np.asarray(y) == c)) / 2 for c in cats])
    pe = (pi * (1 - pi)).sum() / (q - 1)
    return (po - pe) / (1 - pe)


def cohen_kappa(x, y, cats, weights=None):
    cats = list(cats); k = len(cats); idx = {c: i for i, c in enumerate(cats)}
    O = np.zeros((k, k))
    for a, b in zip(x, y):
        O[idx[a], idx[b]] += 1
    O /= O.sum()
    E = np.outer(O.sum(1), O.sum(0))
    i, j = np.indices((k, k))
    if weights is None:
        Wd = (i != j).astype(float)
    elif weights == "linear":
        Wd = np.abs(i - j) / (k - 1)
    else:
        Wd = ((i - j) / (k - 1)) ** 2
    return 1 - (Wd * O).sum() / (Wd * E).sum()


@analysis("agreement", "Rater agreement (κ, AC1)", "Scale",
          [{"name": "rater1", "label": "Rater 1 (e.g. author)", "type": "column"}, {"name": "rater2", "label": "Rater 2 (e.g. independent coder)", "type": "column"},
           {"name": "ordered", "label": "Categories are ordered (adds weighted κ)", "type": "bool", "default": False},
           {"name": "categories", "label": "Full category scale in order (comma-separated; default: observed)", "type": "text", "optional": True}])
def agreement(df, rater1, rater2, ordered=False, categories=None):
    d = df[[rater1, rater2]].dropna().astype(str)
    cats = as_list(categories) or sorted(set(d[rater1]) | set(d[rater2]))
    x, y = d[rater1].tolist(), d[rater2].tolist()
    out = Output("agreement", f"Agreement: {rater1} vs {rater2}", {}); out.n_used = len(d)
    rows = [{"Statistic": "Percent agreement", "Value": 100 * np.mean(np.array(x) == np.array(y))},
            {"Statistic": "Cohen's κ", "Value": cohen_kappa(x, y, cats)},
            {"Statistic": "Gwet's AC1", "Value": gwet_ac1(x, y, cats)}]
    if ordered:
        rows += [{"Statistic": "Weighted κ (linear)", "Value": cohen_kappa(x, y, cats, "linear")}, {"Statistic": "Weighted κ (quadratic)", "Value": cohen_kappa(x, y, cats, "quadratic")}]
    out.table(pd.DataFrame(rows), "Agreement statistics", f"N = {len(d)} units; category scale: {', '.join(cats)}.")
    out.table(pd.crosstab(pd.Series(x, name=rater1), pd.Series(y, name=rater2)), "Confusion table")
    if len(d) < 30:
        out.warn("With few units, κ and AC1 are unstable. Report the disagreement table and the resolution of each disagreement.")
    out.ref(REF["kappa"], REF["gwet"])
    return out


@analysis("icc", "Intraclass correlation (ICC)", "Scale",
          [{"name": "raters", "label": "Rater columns (one row per target)", "type": "columns", "multi": True, "numeric": True}])
def icc(df, raters):
    X = numeric(df, as_list(raters)).dropna().to_numpy(float)
    n, k = X.shape
    gm = X.mean(); msr = k * ((X.mean(1) - gm) ** 2).sum() / (n - 1); msc = n * ((X.mean(0) - gm) ** 2).sum() / (k - 1)
    sst = ((X - gm) ** 2).sum(); mse = (sst - msr * (n - 1) - msc * (k - 1)) / ((n - 1) * (k - 1)); msw = (sst - msr * (n - 1)) / (n * (k - 1))
    vals = {"ICC1 (one-way, single)": (msr - msw) / (msr + (k - 1) * msw),
            "ICC2 (two-way random, absolute, single)": (msr - mse) / (msr + (k - 1) * mse + k * (msc - mse) / n),
            "ICC3 (two-way mixed, consistency, single)": (msr - mse) / (msr + (k - 1) * mse),
            "ICC1k (one-way, average)": (msr - msw) / msr,
            "ICC2k (two-way random, absolute, average)": (msr - mse) / (msr + (msc - mse) / n),
            "ICC3k (two-way mixed, consistency, average)": (msr - mse) / msr}
    out = Output("icc", "Intraclass correlation", {}); out.n_used = n
    out.table(pd.DataFrame({"ICC": vals}), "Intraclass correlations", f"{n} targets × {k} raters (Shrout & Fleiss, 1979; labels as in R psych::ICC).")
    out.ref(REF["icc"])
    return out


# ----------------------------------------------------------------- EFA
@analysis("efa", "Exploratory factor analysis", "Dimension reduction",
          [{"name": "items", "label": "Items", "type": "columns", "multi": True, "numeric": True},
           {"name": "n_factors", "label": "Number of factors", "type": "int", "default": 2},
           {"name": "method", "label": "Extraction", "type": "choice", "choices": ["ml", "minres", "principal"], "default": "ml"},
           {"name": "rotation", "label": "Rotation", "type": "choice", "choices": ["varimax", "oblimin", "promax", "none"], "default": "oblimin"}])
def efa(df, items, n_factors=2, method="ml", rotation="oblimin"):
    its = as_list(items); X = numeric(df, its).dropna()
    out = Output("efa", "Exploratory factor analysis", {}); out.n_used = len(X)
    chi, p = _bartlett(X); kmo_i, kmo = _kmo(X)
    out.table(pd.DataFrame([{"N": len(X), "KMO": kmo, "Bartlett χ²": chi, "df": len(its) * (len(its) - 1) / 2, "p": p}]), "Sampling adequacy")
    ev = np.sort(np.linalg.eigvalsh(X.corr().values))[::-1]
    out.table(pd.DataFrame({"Eigenvalue": ev, "% variance": 100 * ev / len(its), "Cumulative %": 100 * np.cumsum(ev) / len(its)}, index=[f"Component {i + 1}" for i in range(len(ev))]), "Eigenvalues of the correlation matrix")
    f, ax = fig(5.8, 3.4)
    ax.plot(range(1, len(ev) + 1), ev, "o-", color=INK); ax.axhline(1, color=BRASS, ls="--", lw=1.2); ax.set_title("Scree plot"); ax.set_xlabel("Component"); ax.set_ylabel("Eigenvalue")
    out.figure(f)
    rot = None if rotation == "none" else rotation
    fa = EFA(n_factors=int(n_factors), method=method, rotation=rot).fit(X)
    L = pd.DataFrame(fa.loadings_, index=its, columns=[f"F{i + 1}" for i in range(int(n_factors))])
    L["Communality"] = fa.communalities_
    out.table(L, f"Loadings ({method}, {rotation})", "Loadings above |.40| are usually interpreted.")
    if rot in ("oblimin", "promax") and getattr(fa, "phi_", None) is not None:
        out.table(pd.DataFrame(fa.phi_, index=L.columns[:-1], columns=L.columns[:-1]), "Factor correlations")
    var = fa.factor_variance()
    out.table(pd.DataFrame(np.vstack(var), index=["SS loadings", "Proportion", "Cumulative"], columns=L.columns[:-1]), "Variance explained")
    if not fa.converged_:
        out.note("The extraction optimiser did not report convergence; check the number of factors and the items.")
    out.ref(REF["kmo"], REF["bartlett"])
    return out


# ----------------------------------------------------------------- CFA via lavaan
def _rscript():
    for c in ["Rscript", "/usr/local/bin/Rscript", "/opt/homebrew/bin/Rscript", "/Library/Frameworks/R.framework/Resources/bin/Rscript"]:
        p = shutil.which(c) or (c if Path(c).exists() else None)
        if p:
            return p
    return None


LAVAAN_R = r'''
suppressMessages(library(lavaan)); suppressMessages(library(jsonlite))
a <- commandArgs(TRUE); d <- read.csv(a[1], check.names=FALSE); m <- readLines(a[2]); est <- a[3]
fit <- cfa(paste(m, collapse="\n"), data=d, estimator=est, std.lv=FALSE)
fm <- fitMeasures(fit, c("npar","chisq","df","pvalue","cfi","tli","rmsea","rmsea.ci.lower","rmsea.ci.upper","srmr","aic","bic"))
ss <- standardizedSolution(fit)
pe <- parameterEstimates(fit)
out <- list(fit=as.list(fm), std=ss, est=pe, n=lavInspect(fit,"nobs"), lavaan=as.character(packageVersion("lavaan")), converged=lavInspect(fit,"converged"))
cat(toJSON(out, digits=NA, auto_unbox=TRUE))
'''


@analysis("cfa", "Confirmatory factor analysis (lavaan)", "Dimension reduction",
          [{"name": "model", "label": "Model in lavaan syntax, e.g.  F1 =~ x1 + x2 + x3", "type": "textarea"},
           {"name": "estimator", "label": "Estimator", "type": "choice", "choices": ["ML", "MLR"], "default": "ML"}])
def cfa(df, model, estimator="ML"):
    rs = _rscript()
    if not rs:
        raise RuntimeError("CFA runs in R's lavaan package. Install R (https://cran.r-project.org) and in R run install.packages(c('lavaan','jsonlite')).")
    import re
    vars_ = sorted(set(re.findall(r"[A-Za-z_][A-Za-z0-9_.]*", model)) & set(df.columns))
    with tempfile.TemporaryDirectory() as td:
        numeric(df, vars_).to_csv(Path(td, "d.csv"), index=False)
        Path(td, "m.lav").write_text(model); Path(td, "run.R").write_text(LAVAAN_R)
        r = subprocess.run([rs, str(Path(td, "run.R")), str(Path(td, "d.csv")), str(Path(td, "m.lav")), estimator], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError("lavaan error: " + r.stderr[-800:])
    res = json.loads(r.stdout)
    out = Output("cfa", "Confirmatory factor analysis", {}); out.n_used = int(res["n"])
    fm = res["fit"]
    out.table(pd.DataFrame([{"N": res["n"], "χ²": fm["chisq"], "df": fm["df"], "p": fm["pvalue"], "CFI": fm["cfi"], "TLI": fm["tli"], "RMSEA": fm["rmsea"],
                             "RMSEA 90% CI": f"{fm['rmsea.ci.lower']:.3f}–{fm['rmsea.ci.upper']:.3f}", "SRMR": fm["srmr"], "AIC": fm["aic"], "BIC": fm["bic"]}]),
              "Model fit", f"lavaan {res['lavaan']}, estimator {estimator}; converged: {res['converged']}. Common guides: CFI/TLI ≥ .95, RMSEA ≤ .06, SRMR ≤ .08 (Hu & Bentler, 1999).")
    ss = pd.DataFrame(res["std"])
    load = ss[ss["op"] == "=~"][["lhs", "rhs", "est.std", "se", "pvalue"]].rename(columns={"lhs": "Factor", "rhs": "Item", "est.std": "Std. loading", "se": "SE", "pvalue": "p"})
    out.table(load, "Standardised loadings")
    rows = []
    for fac, g in load.groupby("Factor"):
        lam = g["Std. loading"].to_numpy(float)
        rows.append({"Factor": fac, "Items": len(lam), "ω (from std. loadings)": lam.sum() ** 2 / (lam.sum() ** 2 + (1 - lam ** 2).sum()), "AVE": (lam ** 2).mean(), "CR": lam.sum() ** 2 / (lam.sum() ** 2 + (1 - lam ** 2).sum())})
    out.table(pd.DataFrame(rows), "Construct reliability and convergent validity", "AVE ≥ .50 and CR ≥ .70 are common benchmarks (Fornell & Larcker, 1981).")
    cov = ss[(ss["op"] == "~~") & (ss["lhs"] != ss["rhs"])][["lhs", "rhs", "est.std"]]
    if len(cov):
        out.table(cov.rename(columns={"lhs": "A", "rhs": "B", "est.std": "Std. covariance (r)"}), "Factor correlations")
    out.ref(REF["lavaan"], "Hu, L., & Bentler, P. M. (1999). Cutoff criteria for fit indexes in covariance structure analysis. Structural Equation Modeling, 6(1), 1–55.",
            "Fornell, C., & Larcker, D. F. (1981). Evaluating structural equation models with unobservable variables and measurement error. Journal of Marketing Research, 18(1), 39–50.")
    return out


# ----------------------------------------------------------------- power
def _r_power(r, n, alpha):
    """Power of the two-sided test of rho = 0 (Cohen, 1988; same formula as R pwr::pwr.r.test)."""
    t = stats.t.isf(alpha / 2, n - 2)
    rc = np.sqrt(t ** 2 / (t ** 2 + n - 2))
    zr = np.arctanh(r) + r / (2 * (n - 1))
    zrc = np.arctanh(rc)
    return stats.norm.cdf((zr - zrc) * np.sqrt(n - 3)) + stats.norm.cdf((-zr - zrc) * np.sqrt(n - 3))


@analysis("power", "Power and sample size", "Planning",
          [{"name": "test", "label": "Test", "type": "choice", "choices": ["t_independent", "t_paired", "anova", "correlation", "chisquare"], "default": "t_independent"},
           {"name": "effect", "label": "Effect size (d, f, r or w)", "type": "number", "default": 0.5},
           {"name": "alpha", "label": "α", "type": "number", "default": 0.05},
           {"name": "power", "label": "Target power", "type": "number", "default": 0.8},
           {"name": "k", "label": "Groups (ANOVA) or df+1 (chi-square)", "type": "int", "default": 3}])
def power(df, test="t_independent", effect=0.5, alpha=0.05, power=0.8, k=3):
    from statsmodels.stats import power as P
    out = Output("power", "Power and sample size", {})
    if test == "t_independent":
        n = P.TTestIndPower().solve_power(effect_size=effect, alpha=alpha, power=power); lab = "n per group"
    elif test == "t_paired":
        n = P.TTestPower().solve_power(effect_size=effect, alpha=alpha, power=power); lab = "pairs"
    elif test == "anova":
        n = P.FTestAnovaPower().solve_power(effect_size=effect, alpha=alpha, power=power, k_groups=k); lab = "total N"
    elif test == "correlation":
        from scipy.optimize import brentq
        n = brentq(lambda n: _r_power(effect, n, alpha) - power, 4, 1e6); lab = "N"
    else:
        n = P.GofChisquarePower().solve_power(effect_size=effect, alpha=alpha, power=power, n_bins=k); lab = "total N"
    out.table(pd.DataFrame([{"Test": test, "Effect size": effect, "α": alpha, "Power": power, "Required": np.ceil(n), "Unit": lab, "Exact value": n}]), "Required sample size")
    grid = np.linspace(max(4, n * 0.3), n * 2, 40)
    pw = []
    for g in grid:
        if test == "t_independent": pw.append(P.TTestIndPower().power(effect, g, alpha))
        elif test == "t_paired": pw.append(P.TTestPower().power(effect, g, alpha))
        elif test == "anova": pw.append(P.FTestAnovaPower().power(effect, g, alpha, k_groups=k))
        elif test == "correlation": pw.append(_r_power(effect, g, alpha))
        else: pw.append(P.GofChisquarePower().power(effect, g, alpha, n_bins=k))
    f, ax = fig(6.0, 3.4)
    ax.plot(grid, pw, color=INK, lw=2); ax.axhline(power, color=BRASS, ls="--"); ax.axvline(n, color=TEAL, ls=":")
    ax.set_xlabel(lab); ax.set_ylabel("Power"); ax.set_title("Power curve")
    out.figure(f)
    out.ref("Cohen, J. (1988). Statistical power analysis for the behavioral sciences (2nd ed.). Lawrence Erlbaum.")
    return out
