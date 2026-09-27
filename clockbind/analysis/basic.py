"""Descriptive statistics, crosstabs, mean comparisons, non-parametric tests, correlation, normality."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .core import Output, analysis, as_list, fmt_p, numeric
from .style import BRASS, INK, LINE, MUTED, PALETTE, REF, SLATE, TEAL, fig

V = {"name": "variables", "label": "Variables", "type": "columns", "multi": True}


# ----------------------------------------------------------------- frequencies
@analysis("frequencies", "Frequencies", "Descriptive statistics",
          [{"name": "variables", "label": "Categorical variables", "type": "columns", "multi": True},
           {"name": "chart", "label": "Bar chart", "type": "bool", "default": True}])
def frequencies(df, variables, chart=True):
    out = Output("frequencies", "Frequencies", {})
    for v in as_list(variables):
        s = df[v]
        vc = s.value_counts(dropna=False)
        n_valid = int(s.notna().sum())
        t = pd.DataFrame({"Frequency": vc.values}, index=[("Missing" if pd.isna(k) else str(k)) for k in vc.index])
        t["Percent"] = 100 * t["Frequency"] / len(s)
        t["Valid percent"] = [100 * f / n_valid if lab != "Missing" and n_valid else np.nan for lab, f in zip(t.index, t["Frequency"])]
        t.loc["Total"] = [len(s), 100.0, 100.0 if n_valid else np.nan]
        t.index.name = v
        out.table(t, f"{v}")
        if chart and len(vc) <= 30:
            f, ax = fig(6.6, 0.35 * min(len(vc), 20) + 1.4)
            vv = vc[vc.index.notna()] if vc.index.notna().any() else vc
            ax.barh([str(k) for k in vv.index][::-1], vv.values[::-1], color=INK)
            ax.set_xlabel("Frequency"); ax.set_title(v); ax.grid(axis="y", visible=False)
            out.figure(f)
    out.ref(REF["pandas"])
    return out


# ----------------------------------------------------------------- descriptives
@analysis("descriptives", "Descriptive statistics", "Descriptive statistics",
          [{"name": "variables", "label": "Numeric variables", "type": "columns", "multi": True, "numeric": True},
           {"name": "by", "label": "Split by (optional)", "type": "column", "optional": True},
           {"name": "chart", "label": "Histogram and box plot", "type": "bool", "default": True}])
def descriptives(df, variables, by=None, chart=True):
    vs = as_list(variables)
    out = Output("descriptives", "Descriptive statistics", {})
    groups = [("All", df)] if not by else [(str(k), g) for k, g in df.groupby(by, dropna=True)]
    rows = []
    for gname, g in groups:
        X = numeric(g, vs)
        for v in vs:
            x = X[v].dropna()
            n = len(x)
            rows.append({**({"Group": gname} if by else {}), "Variable": v, "N": n, "Missing": int(X[v].isna().sum()),
                         "Mean": x.mean() if n else np.nan, "SD": x.std(ddof=1) if n > 1 else np.nan,
                         "SE mean": x.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan,
                         "Min": x.min() if n else np.nan, "Q1": x.quantile(.25) if n else np.nan, "Median": x.median() if n else np.nan,
                         "Q3": x.quantile(.75) if n else np.nan, "Max": x.max() if n else np.nan,
                         "Skewness": stats.skew(x, bias=False) if n > 2 else np.nan,
                         "Kurtosis": stats.kurtosis(x, bias=False) if n > 3 else np.nan})
    out.table(pd.DataFrame(rows), "Descriptive statistics",
              "SD with n − 1. Skewness and kurtosis are the bias-corrected sample statistics (G1, G2; excess kurtosis), as reported by SPSS. Quartiles use linear interpolation (type 7).")
    if chart:
        X = numeric(df, vs)
        for v in vs:
            x = X[v].dropna()
            if len(x) < 3:
                continue
            f, (a1, a2) = __import__("matplotlib.pyplot", fromlist=["subplots"]).subplots(1, 2, figsize=(8.4, 3.4), gridspec_kw={"width_ratios": [2.2, 1]})
            a1.hist(x, bins="auto", color=INK, edgecolor="white"); a1.set_title(f"{v}: distribution"); a1.set_ylabel("Frequency")
            a1.axvline(x.mean(), color=BRASS, lw=2, label="mean"); a1.legend()
            if by:
                data = [pd.to_numeric(g[v], errors="coerce").dropna() for _, g in df.groupby(by)]
                a2.boxplot(data, tick_labels=[str(k) for k in df.groupby(by).groups], patch_artist=True, boxprops={"facecolor": "#E2E9F1", "color": INK}, medianprops={"color": BRASS, "lw": 2})
            else:
                a2.boxplot(x, patch_artist=True, boxprops={"facecolor": "#E2E9F1", "color": INK}, medianprops={"color": BRASS, "lw": 2})
            a2.set_title("Box plot")
            out.figure(f)
    out.methods(f"Descriptive statistics were computed for {', '.join(vs)}" + (f", separately by {by}" if by else "") + ".")
    out.ref(REF["pandas"], REF["scipy"])
    return out


# ----------------------------------------------------------------- normality
@analysis("normality", "Normality tests", "Descriptive statistics",
          [{"name": "variables", "label": "Numeric variables", "type": "columns", "multi": True, "numeric": True}])
def normality(df, variables):
    vs = as_list(variables)
    X = numeric(df, vs)
    out = Output("normality", "Normality tests", {})
    rows = []
    for v in vs:
        x = X[v].dropna()
        w, p = stats.shapiro(x) if 3 <= len(x) <= 5000 else (np.nan, np.nan)
        rows.append({"Variable": v, "N": len(x), "Shapiro–Wilk W": w, "p": p})
    out.table(pd.DataFrame(rows), "Shapiro–Wilk test")
    for v in vs[:6]:
        x = X[v].dropna()
        if len(x) < 3:
            continue
        f, ax = fig(4.6, 4.0)
        (osm, osr), (sl, ic, _) = stats.probplot(x, dist="norm")
        ax.scatter(osm, osr, s=14, color=INK); ax.plot(osm, sl * np.asarray(osm) + ic, color=BRASS, lw=2)
        ax.set_title(f"Q–Q plot: {v}"); ax.set_xlabel("Theoretical quantiles"); ax.set_ylabel("Sample quantiles")
        out.figure(f)
    out.ref(REF["shapiro"], REF["scipy"])
    return out


# ----------------------------------------------------------------- crosstabs
@analysis("crosstabs", "Crosstabs and chi-square", "Descriptive statistics",
          [{"name": "row", "label": "Row variable", "type": "column"}, {"name": "col", "label": "Column variable", "type": "column"},
           {"name": "chart", "label": "Stacked bar chart", "type": "bool", "default": True}])
def crosstabs(df, row, col, chart=True):
    d = df[[row, col]].dropna()
    tab = pd.crosstab(d[row].astype(str), d[col].astype(str))
    out = Output("crosstabs", f"Crosstabs: {row} × {col}", {})
    out.n_used = len(d)
    t = tab.copy(); t["Total"] = t.sum(1); t.loc["Total"] = t.sum(0)
    out.table(t, "Counts")
    out.table((100 * tab.div(tab.sum(1), axis=0)).round(1), "Row percentages")
    chi2, p, dof, exp = stats.chi2_contingency(tab, correction=False)
    g2, pg, _, _ = stats.chi2_contingency(tab, correction=False, lambda_="log-likelihood")
    rows = [{"Test": "Pearson chi-square", "Value": chi2, "df": dof, "p": p},
            {"Test": "Likelihood ratio", "Value": g2, "df": dof, "p": pg}]
    if tab.shape == (2, 2):
        cy, py_, _, _ = stats.chi2_contingency(tab, correction=True)
        rows.append({"Test": "Continuity correction (Yates)", "Value": cy, "df": 1, "p": py_})
        _, pf = stats.fisher_exact(tab.values)
        rows.append({"Test": "Fisher's exact (two-sided)", "Value": np.nan, "df": np.nan, "p": pf})
    n = tab.values.sum()
    v = np.sqrt(chi2 / (n * (min(tab.shape) - 1))) if min(tab.shape) > 1 else np.nan
    rows.append({"Test": "Cramér's V", "Value": v, "df": np.nan, "p": p})
    out.table(pd.DataFrame(rows), "Tests of association")
    low = (exp < 5).mean()
    if low > 0.2:
        out.warn(f"{100 * low:.0f}% of cells have expected counts below 5; prefer Fisher's exact test or merge categories.")
    if chart:
        f, ax = fig(7.0, 3.8)
        pct = 100 * tab.div(tab.sum(1), axis=0)
        left = np.zeros(len(pct))
        for i, c in enumerate(pct.columns):
            ax.barh(pct.index, pct[c], left=left, color=PALETTE[i % len(PALETTE)], label=str(c)); left += pct[c].values
        ax.set_xlabel("Row %"); ax.set_title(f"{col} within {row}"); ax.legend(ncol=min(4, len(pct.columns)), loc="upper center", bbox_to_anchor=(.5, -0.18)); ax.grid(axis="y", visible=False)
        out.figure(f)
    out.methods(f"Association between {row} and {col} was tested with Pearson's chi-square test (χ²({dof}, N = {n}) = {chi2:.2f}, p {fmt_p(p) if fmt_p(p).startswith('<') else '= ' + fmt_p(p)}); effect size Cramér's V = {v:.2f}.")
    out.ref(REF["cramer"], REF["fleiss_ci"], REF["scipy"])
    return out


# ----------------------------------------------------------------- t-tests
def _cohen_d(a, b):
    na, nb = len(a), len(b)
    sp = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    return (a.mean() - b.mean()) / sp


@analysis("t_independent", "Independent-samples t-test", "Compare means",
          [{"name": "variables", "label": "Test variables", "type": "columns", "multi": True, "numeric": True},
           {"name": "group", "label": "Grouping variable (2 groups)", "type": "column"}])
def t_independent(df, variables, group):
    out = Output("t_independent", "Independent-samples t-test", {})
    levels = [x for x in pd.unique(df[group].dropna())]
    if len(levels) != 2:
        raise ValueError(f"'{group}' must have exactly 2 groups; found {len(levels)}: {levels}")
    levels = sorted(levels, key=str)
    rows, desc = [], []
    for v in as_list(variables):
        x = pd.to_numeric(df[v], errors="coerce")
        a, b = x[df[group] == levels[0]].dropna(), x[df[group] == levels[1]].dropna()
        for lab, s in ((levels[0], a), (levels[1], b)):
            desc.append({"Variable": v, "Group": str(lab), "N": len(s), "Mean": s.mean(), "SD": s.std(ddof=1), "SE mean": s.std(ddof=1) / np.sqrt(len(s))})
        lev = stats.levene(a, b, center="mean")
        st = stats.ttest_ind(a, b, equal_var=True); we = stats.ttest_ind(a, b, equal_var=False)
        va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
        df_w = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
        diff = a.mean() - b.mean()
        se_s = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2) * (1 / len(a) + 1 / len(b)))
        se_w = np.sqrt(va + vb)
        for lab, t, dfv, p, se in (("Equal variances assumed (Student)", st.statistic, len(a) + len(b) - 2, st.pvalue, se_s),
                                   ("Equal variances not assumed (Welch)", we.statistic, df_w, we.pvalue, se_w)):
            tc = stats.t.ppf(.975, dfv)
            rows.append({"Variable": v, "Assumption": lab, "Levene F": lev.statistic, "Levene p": lev.pvalue, "t": t, "df": dfv, "p (two-sided)": p,
                         "Mean difference": diff, "SE difference": se, "95% CI low": diff - tc * se, "95% CI high": diff + tc * se})
        d = _cohen_d(a, b)
        rows[-1]["Cohen's d"] = d; rows[-2]["Cohen's d"] = d
        out.methods(f"{v}: Welch's t({df_w:.1f}) = {we.statistic:.2f}, p {('= ' + fmt_p(we.pvalue)) if not fmt_p(we.pvalue).startswith('<') else fmt_p(we.pvalue)}, d = {d:.2f} ({levels[0]} vs {levels[1]}). Welch's test is reported by default because it does not assume equal variances.")
    out.table(pd.DataFrame(desc), "Group statistics")
    out.table(pd.DataFrame(rows), "Independent-samples test", "Levene's test uses deviations from the mean (as in SPSS). Cohen's d uses the pooled SD.")
    f, ax = fig(6.4, 0.9 * len(as_list(variables)) + 1.6)
    ds = pd.DataFrame(desc)
    for i, (lab, g) in enumerate(ds.groupby("Group", sort=False)):
        y = np.arange(len(g)) + (i - 0.5) * 0.25
        ax.errorbar(g["Mean"], y, xerr=1.96 * g["SE mean"], fmt="o", color=[INK, BRASS][i % 2], capsize=4, label=str(lab))
    ax.set_yticks(np.arange(len(as_list(variables)))); ax.set_yticklabels(as_list(variables)); ax.set_title("Means with 95% CI"); ax.legend(); ax.grid(axis="y", visible=False)
    out.figure(f)
    out.ref(REF["welch"], REF["levene"], REF["cohen_d"], REF["scipy"])
    return out


@analysis("t_paired", "Paired-samples t-test", "Compare means",
          [{"name": "first", "label": "First measurement", "type": "column", "numeric": True}, {"name": "second", "label": "Second measurement", "type": "column", "numeric": True}])
def t_paired(df, first, second):
    d = numeric(df, [first, second]).dropna()
    r = stats.ttest_rel(d[first], d[second])
    diff = d[first] - d[second]
    se = diff.std(ddof=1) / np.sqrt(len(d)); tc = stats.t.ppf(.975, len(d) - 1)
    out = Output("t_paired", "Paired-samples t-test", {}); out.n_used = len(d)
    out.table(pd.DataFrame([{"Pair": f"{first} − {second}", "N": len(d), "Mean difference": diff.mean(), "SD": diff.std(ddof=1), "SE": se,
                             "95% CI low": diff.mean() - tc * se, "95% CI high": diff.mean() + tc * se, "t": r.statistic, "df": len(d) - 1, "p (two-sided)": r.pvalue,
                             "Cohen's dz": diff.mean() / diff.std(ddof=1)}]), "Paired-samples test")
    out.ref(REF["scipy"], REF["cohen_d"])
    return out


@analysis("t_one_sample", "One-sample t-test", "Compare means",
          [{"name": "variables", "label": "Variables", "type": "columns", "multi": True, "numeric": True}, {"name": "mu", "label": "Test value", "type": "number", "default": 0.0}])
def t_one_sample(df, variables, mu=0.0):
    out = Output("t_one_sample", "One-sample t-test", {})
    rows = []
    for v in as_list(variables):
        x = pd.to_numeric(df[v], errors="coerce").dropna()
        r = stats.ttest_1samp(x, mu); se = x.std(ddof=1) / np.sqrt(len(x)); tc = stats.t.ppf(.975, len(x) - 1); dm = x.mean() - mu
        rows.append({"Variable": v, "N": len(x), "Mean": x.mean(), "Test value": mu, "t": r.statistic, "df": len(x) - 1, "p (two-sided)": r.pvalue,
                     "Mean difference": dm, "95% CI low": dm - tc * se, "95% CI high": dm + tc * se})
    out.table(pd.DataFrame(rows), "One-sample test")
    out.ref(REF["scipy"])
    return out


# ----------------------------------------------------------------- ANOVA
@analysis("anova_oneway", "One-way ANOVA", "Compare means",
          [{"name": "variable", "label": "Dependent variable", "type": "column", "numeric": True}, {"name": "group", "label": "Factor", "type": "column"},
           {"name": "posthoc", "label": "Tukey HSD post hoc", "type": "bool", "default": True}])
def anova_oneway(df, variable, group, posthoc=True):
    d = df[[variable, group]].copy(); d[variable] = pd.to_numeric(d[variable], errors="coerce"); d = d.dropna()
    d[group] = d[group].astype(str)
    gs = [g[variable].values for _, g in d.groupby(group)]
    out = Output("anova_oneway", f"One-way ANOVA: {variable} by {group}", {}); out.n_used = len(d)
    desc = d.groupby(group)[variable].agg(N="count", Mean="mean", SD="std")
    desc["SE"] = desc["SD"] / np.sqrt(desc["N"])
    out.table(desc, "Descriptives")
    grand = d[variable].mean()
    ssb = sum(len(g) * (g.mean() - grand) ** 2 for g in gs); ssw = sum(((g - g.mean()) ** 2).sum() for g in gs)
    k, n = len(gs), len(d)
    F, p = stats.f_oneway(*gs)
    out.table(pd.DataFrame([{"Source": "Between groups", "Sum of squares": ssb, "df": k - 1, "Mean square": ssb / (k - 1), "F": F, "p": p},
                            {"Source": "Within groups", "Sum of squares": ssw, "df": n - k, "Mean square": ssw / (n - k), "F": np.nan, "p": np.nan},
                            {"Source": "Total", "Sum of squares": ssb + ssw, "df": n - 1, "Mean square": np.nan, "F": np.nan, "p": np.nan}]), "ANOVA",
              f"η² = {ssb / (ssb + ssw):.3f}; ω² = {(ssb - (k - 1) * ssw / (n - k)) / (ssb + ssw + ssw / (n - k)):.3f}.")
    lev = stats.levene(*gs, center="mean")
    # Welch ANOVA
    w_ = np.array([len(g) / g.var(ddof=1) for g in gs]); m_ = np.array([g.mean() for g in gs]); nn = np.array([len(g) for g in gs])
    mw = (w_ * m_).sum() / w_.sum(); A = (w_ * (m_ - mw) ** 2).sum() / (k - 1)
    lam = ((1 - w_ / w_.sum()) ** 2 / (nn - 1)).sum(); Bw = 1 + 2 * (k - 2) / (k ** 2 - 1) * lam
    Fw = A / Bw; df2 = (k ** 2 - 1) / (3 * lam); pw = stats.f.sf(Fw, k - 1, df2)
    out.table(pd.DataFrame([{"Test": "Levene (mean)", "Statistic": lev.statistic, "df1": k - 1, "df2": n - k, "p": lev.pvalue},
                            {"Test": "Welch ANOVA", "Statistic": Fw, "df1": k - 1, "df2": df2, "p": pw}]), "Assumption check and robust test")
    if posthoc and k > 2:
        from statsmodels.stats.multicomp import pairwise_tukeyhsd
        th = pairwise_tukeyhsd(d[variable], d[group])
        from itertools import combinations
        pairs = list(combinations(th.groupsunique, 2))
        ci = np.asarray(th.confint)
        res = pd.DataFrame({"group1": [str(a) for a, _ in pairs], "group2": [str(b) for _, b in pairs], "meandiff": th.meandiffs,
                            "p-adj": th.pvalues, "lower": ci[:, 0], "upper": ci[:, 1], "reject": th.reject})
        out.table(res, "Tukey HSD multiple comparisons")
        out.ref(REF["tukey"], REF["statsmodels"])
    f, ax = fig(6.4, 3.6)
    ax.errorbar(desc.index, desc["Mean"], yerr=stats.t.ppf(.975, desc["N"] - 1) * desc["SE"], fmt="o-", color=INK, ecolor=BRASS, capsize=5, lw=1.5)
    ax.set_title(f"Mean {variable} by {group} (95% CI)"); ax.set_ylabel(variable)
    out.figure(f)
    out.methods(f"A one-way ANOVA showed F({k - 1}, {n - k}) = {F:.2f}, p {('= ' + fmt_p(p)) if not fmt_p(p).startswith('<') else fmt_p(p)}, η² = {ssb / (ssb + ssw):.2f}; Welch's F({k - 1}, {df2:.1f}) = {Fw:.2f}.")
    out.ref(REF["levene"], REF["welch"], REF["scipy"])
    return out


# ----------------------------------------------------------------- non-parametric
@analysis("mann_whitney", "Mann–Whitney U test", "Non-parametric tests",
          [{"name": "variables", "label": "Test variables", "type": "columns", "multi": True, "numeric": True}, {"name": "group", "label": "Grouping variable (2 groups)", "type": "column"}])
def mann_whitney(df, variables, group):
    levels = sorted(pd.unique(df[group].dropna()), key=str)
    if len(levels) != 2:
        raise ValueError("Grouping variable must have exactly 2 groups.")
    out = Output("mann_whitney", "Mann–Whitney U test", {}); rows = []
    for v in as_list(variables):
        x = pd.to_numeric(df[v], errors="coerce")
        a, b = x[df[group] == levels[0]].dropna(), x[df[group] == levels[1]].dropna()
        r = stats.mannwhitneyu(a, b, alternative="two-sided", method="asymptotic", use_continuity=True)
        z = stats.norm.isf(r.pvalue / 2) * np.sign(r.statistic - len(a) * len(b) / 2)
        rows.append({"Variable": v, f"N {levels[0]}": len(a), f"N {levels[1]}": len(b), f"Median {levels[0]}": a.median(), f"Median {levels[1]}": b.median(),
                     "U": r.statistic, "z": z, "p (asymptotic, two-sided)": r.pvalue, "r = |z|/√N": abs(z) / np.sqrt(len(a) + len(b))})
    out.table(pd.DataFrame(rows), "Mann–Whitney U", "Normal approximation with continuity and tie correction (as R wilcox.test with exact = FALSE).")
    out.ref(REF["mann_whitney"], REF["scipy"])
    return out


@analysis("wilcoxon", "Wilcoxon signed-rank test", "Non-parametric tests",
          [{"name": "first", "label": "First measurement", "type": "column", "numeric": True}, {"name": "second", "label": "Second measurement", "type": "column", "numeric": True}])
def wilcoxon(df, first, second):
    d = numeric(df, [first, second]).dropna()
    r = stats.wilcoxon(d[first], d[second], zero_method="wilcox", correction=True, method="approx")
    out = Output("wilcoxon", "Wilcoxon signed-rank test", {}); out.n_used = len(d)
    dd = (d[first] - d[second]); dd = dd[dd != 0]; V = dd.abs().rank()[dd > 0].sum()
    out.table(pd.DataFrame([{"Pair": f"{first} − {second}", "N": len(d), "N non-zero": len(dd), "V (sum of positive ranks)": V,
                             "p (approx., two-sided)": r.pvalue}]), "Wilcoxon signed-rank", "Zero differences dropped; normal approximation with continuity correction (as R wilcox.test(paired=TRUE, exact=FALSE)).")
    out.ref(REF["wilcoxon"], REF["scipy"])
    return out


@analysis("kruskal", "Kruskal–Wallis test", "Non-parametric tests",
          [{"name": "variable", "label": "Test variable", "type": "column", "numeric": True}, {"name": "group", "label": "Grouping variable", "type": "column"}])
def kruskal(df, variable, group):
    d = df[[variable, group]].copy(); d[variable] = pd.to_numeric(d[variable], errors="coerce"); d = d.dropna()
    gs = [g[variable].values for _, g in d.groupby(group)]
    H, p = stats.kruskal(*gs)
    out = Output("kruskal", f"Kruskal–Wallis: {variable} by {group}", {}); out.n_used = len(d)
    out.table(d.groupby(group)[variable].agg(N="count", Median="median", **{"Mean rank": lambda s: d[variable].rank()[s.index].mean()}), "Ranks")
    out.table(pd.DataFrame([{"H": H, "df": len(gs) - 1, "p": p, "ε²": H / ((len(d) ** 2 - 1) / (len(d) + 1))}]), "Test statistic", "Tie-corrected H.")
    out.ref(REF["kruskal"], REF["scipy"])
    return out


# ----------------------------------------------------------------- correlation
@analysis("correlation", "Correlations", "Correlate",
          [{"name": "variables", "label": "Variables", "type": "columns", "multi": True, "numeric": True},
           {"name": "method", "label": "Coefficient", "type": "choice", "choices": ["pearson", "spearman", "kendall"], "default": "pearson"},
           {"name": "chart", "label": "Heat map", "type": "bool", "default": True}])
def correlation(df, variables, method="pearson", chart=True):
    vs = as_list(variables); X = numeric(df, vs)
    fn = {"pearson": stats.pearsonr, "spearman": stats.spearmanr, "kendall": stats.kendalltau}[method]
    R = pd.DataFrame(np.eye(len(vs)), index=vs, columns=vs); P = R * np.nan; N = R.copy()
    rows = []
    for i, a in enumerate(vs):
        for j, b in enumerate(vs):
            if j <= i:
                continue
            d = X[[a, b]].dropna()
            r, p = fn(d[a], d[b])[:2]
            R.loc[a, b] = R.loc[b, a] = r; P.loc[a, b] = P.loc[b, a] = p; N.loc[a, b] = N.loc[b, a] = len(d)
            row = {"Pair": f"{a} – {b}", "r": r, "p": p, "N": len(d)}
            if method == "pearson" and len(d) > 3:
                z = np.arctanh(r); se = 1 / np.sqrt(len(d) - 3)
                row["95% CI low"], row["95% CI high"] = np.tanh(z - 1.96 * se), np.tanh(z + 1.96 * se)
            rows.append(row)
    out = Output("correlation", f"{method.capitalize()} correlations", {})
    out.table(R.round(3), "Correlation matrix", "Pairwise deletion.")
    out.table(pd.DataFrame(rows), "Pairwise tests", "Two-sided p-values; Fisher z confidence intervals for Pearson r.")
    if chart and len(vs) > 1:
        f, ax = fig(0.6 * len(vs) + 3, 0.55 * len(vs) + 2.4)
        from matplotlib.colors import LinearSegmentedColormap
        cm = LinearSegmentedColormap.from_list("cb", [TEAL, "#F4F6F6", BRASS])
        im = ax.imshow(R.values.astype(float), cmap=cm, vmin=-1, vmax=1)
        ax.set_xticks(range(len(vs))); ax.set_xticklabels(vs, rotation=45, ha="right"); ax.set_yticks(range(len(vs))); ax.set_yticklabels(vs); ax.grid(False)
        for i in range(len(vs)):
            for j in range(len(vs)):
                ax.text(j, i, f"{R.values[i, j]:.2f}", ha="center", va="center", fontsize=8, color=INK)
        f.colorbar(im, ax=ax, shrink=.8); ax.set_title(f"{method.capitalize()} correlations")
        out.figure(f)
    out.ref(REF["scipy"])
    return out
