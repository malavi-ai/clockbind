"""Procedure-level validation of ClockBind against R reference implementations.

Run:  clockbind validate all      (needs R with: psych lavaan irr irrCAC nnet MASS sandwich clubSandwich pwr jsonlite)
Writes VALIDATION.md and validation_results.csv. Every row compares one statistic computed by
ClockBind with the same statistic from an established R function on the same data.
"""
from __future__ import annotations

import datetime as _dt
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from . import __version__
from .analysis import run as run_analysis
from .analysis.scales import _rscript

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def _tab(out, title):
    for b in out.blocks:
        if b.kind == "table" and b.title == title:
            return b.content
    raise KeyError(f"table '{title}' not in {out.title}")


def compute(data_csv: Path, conjoint_csv: Path) -> tuple[list[dict], dict]:
    rs = _rscript()
    if not rs:
        raise SystemExit("R is required for validation.")
    r = subprocess.run([rs, str(HERE / "r" / "reference_all.R"), str(data_csv), str(conjoint_csv)], capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        raise SystemExit("R reference script failed:\n" + r.stderr[-1500:])
    R = json.loads(r.stdout)
    df = pd.read_csv(data_csv)
    rows: list[dict] = []

    def chk(proc, stat, ours, ref, tol, rfun):
        ours = np.atleast_1d(np.asarray(ours, dtype=float)); ref = np.atleast_1d(np.asarray(ref, dtype=float))
        diff = float(np.max(np.abs(ours - ref))) if ours.shape == ref.shape else np.inf
        rows.append({"Procedure": proc, "Statistic": stat, "R reference": rfun, "Max |difference|": diff, "Tolerance": tol, "Result": "PASS" if diff <= tol else "FAIL"})

    o = run_analysis("descriptives", df, {"variables": "y", "chart": False}); t = _tab(o, "Descriptive statistics").iloc[0]
    chk("Descriptives", "mean, SD, median, Q1", [t["Mean"], t["SD"], t["Median"], t["Q1"]], [R["desc"][k] for k in ("mean", "sd", "median", "q1")], 1e-10, "base::mean/sd/quantile")
    chk("Descriptives", "skewness, kurtosis (G1, G2)", [t["Skewness"], t["Kurtosis"]], [R["desc"]["skew"], R["desc"]["kurt"]], 1e-10, "psych::describe(type = 2)")

    o = run_analysis("t_independent", df, {"variables": "y", "group": "g2"}); t = _tab(o, "Independent-samples test")
    chk("Independent t-test", "Student t, p", [t.iloc[0]["t"], t.iloc[0]["p (two-sided)"]], [R["t_ind"]["t"], R["t_ind"]["p"]], 1e-10, "stats::t.test(var.equal = TRUE)")
    chk("Independent t-test", "Welch t, df, p", [t.iloc[1]["t"], t.iloc[1]["df"], t.iloc[1]["p (two-sided)"]], [R["t_ind"]["wt"], R["t_ind"]["wdf"], R["t_ind"]["wp"]], 1e-8, "stats::t.test()")
    chk("Independent t-test", "Levene F (mean-centred), p", [t.iloc[0]["Levene F"], t.iloc[0]["Levene p"]], [R["t_ind"]["levF"], R["t_ind"]["levp"]], 1e-10, "anova(lm(|y − group mean| ~ g))")
    o = run_analysis("t_paired", df, {"first": "pre", "second": "post"}); t = _tab(o, "Paired-samples test").iloc[0]
    chk("Paired t-test", "t, p", [t["t"], t["p (two-sided)"]], [R["t_paired"]["t"], R["t_paired"]["p"]], 1e-10, "stats::t.test(paired = TRUE)")
    o = run_analysis("t_one_sample", df, {"variables": "x1", "mu": 0}); t = _tab(o, "One-sample test").iloc[0]
    chk("One-sample t-test", "t, p", [t["t"], t["p (two-sided)"]], [R["t_one"]["t"], R["t_one"]["p"]], 1e-10, "stats::t.test(mu = 0)")

    o = run_analysis("anova_oneway", df, {"variable": "y", "group": "g3"}); a = _tab(o, "ANOVA").iloc[0]; rb = _tab(o, "Assumption check and robust test")
    chk("One-way ANOVA", "F, p", [a["F"], a["p"]], [R["anova"]["F"], R["anova"]["p"]], 1e-10, "stats::aov")
    chk("One-way ANOVA", "Welch F, df2, p", [rb.iloc[1]["Statistic"], rb.iloc[1]["df2"], rb.iloc[1]["p"]], [R["anova"]["wF"], R["anova"]["wdf2"], R["anova"]["wp"]], 1e-8, "stats::oneway.test")
    chk("One-way ANOVA", "Levene F", [rb.iloc[0]["Statistic"]], [R["anova"]["levF"]], 1e-10, "anova(lm(|y − group mean| ~ g))")
    tk = _tab(o, "Tukey HSD multiple comparisons")
    ours = {f"{r_['group2']}-{r_['group1']}": (float(r_["meandiff"]), float(r_["p-adj"])) for _, r_ in tk.iterrows()}
    ref_d = dict(zip(R["anova"]["tukey"]["names"], zip(R["anova"]["tukey"]["diff"], R["anova"]["tukey"]["p"])))
    keys = [k for k in ref_d if k in ours]
    chk("Tukey HSD", "mean differences", [ours[k][0] for k in keys], [ref_d[k][0] for k in keys], 1e-10, "stats::TukeyHSD")
    chk("Tukey HSD", "adjusted p", [ours[k][1] for k in keys], [ref_d[k][1] for k in keys], 2e-3, "stats::TukeyHSD")

    o = run_analysis("crosstabs", df, {"row": "g2", "col": "ycat", "chart": False}); t = _tab(o, "Tests of association")
    chk("Chi-square", "Pearson χ², p", [t.iloc[0]["Value"], t.iloc[0]["p"]], [R["chisq"]["x2"], R["chisq"]["p"]], 1e-10, "stats::chisq.test(correct = FALSE)")
    o = run_analysis("crosstabs", df, {"row": "g2", "col": "x3", "chart": False}); t = _tab(o, "Tests of association").set_index("Test")
    chk("Chi-square 2×2", "Yates χ², p", [t.loc["Continuity correction (Yates)", "Value"], t.loc["Continuity correction (Yates)", "p"]], [R["chisq"]["yates"], R["chisq"]["yp"]], 1e-10, "stats::chisq.test(correct = TRUE)")
    chk("Fisher's exact", "p (two-sided)", [t.loc["Fisher's exact (two-sided)", "p"]], [R["chisq"]["fisher_p"]], 1e-8, "stats::fisher.test")

    o = run_analysis("mann_whitney", df, {"variables": "y", "group": "g2"}); t = _tab(o, "Mann–Whitney U").iloc[0]
    chk("Mann–Whitney", "U (= R's W), p", [t["U"], t["p (asymptotic, two-sided)"]], [R["mw"]["W"], R["mw"]["p"]], 1e-10, "stats::wilcox.test(exact = FALSE)")
    o = run_analysis("wilcoxon", df, {"first": "pre", "second": "post"}); t = _tab(o, "Wilcoxon signed-rank").iloc[0]
    chk("Wilcoxon signed-rank", "V, p", [t["V (sum of positive ranks)"], t["p (approx., two-sided)"]], [R["wilcox"]["V"], R["wilcox"]["p"]], 1e-10, "stats::wilcox.test(paired = TRUE, exact = FALSE)")
    o = run_analysis("kruskal", df, {"variable": "y", "group": "g3"}); t = _tab(o, "Test statistic").iloc[0]
    chk("Kruskal–Wallis", "H, p", [t["H"], t["p"]], [R["kw"]["H"], R["kw"]["p"]], 1e-10, "stats::kruskal.test")

    for m, key in (("pearson", "pearson"), ("spearman", "spearman"), ("kendall", "kendall")):
        o = run_analysis("correlation", df, {"variables": "x1,y", "method": m, "chart": False}); t = _tab(o, "Pairwise tests").iloc[0]
        vals, refs = [t["r"]], [R["cor"][key]]
        if m != "kendall":
            vals.append(t["p"]); refs.append(R["cor"][f"{key}_p"])
        chk("Correlation", f"{m} coefficient" + (", p" if m != "kendall" else ""), vals, refs, 1e-10, f"stats::cor.test(method = '{m}')")

    o = run_analysis("regression_linear", df, {"y": "y", "x": "x1,x2,x3", "categorical": "g2"}); c = _tab(o, "Coefficients"); s = _tab(o, "Model summary").iloc[0]
    chk("Linear regression", "coefficients", c["B"], R["lm"]["b"], 1e-10, "stats::lm")
    chk("Linear regression", "classical SE", c["SE"], R["lm"]["se"], 1e-10, "stats::lm")
    chk("Linear regression", "R², F", [s["R²"], s["F"]], [R["lm"]["r2"], R["lm"]["F"]], 1e-10, "summary.lm")
    o = run_analysis("regression_linear", df, {"y": "y", "x": "x1,x2,x3", "categorical": "g2", "se": "HC3"})
    chk("Linear regression", "HC3 SE", _tab(o, "Coefficients")["SE"], R["lm"]["hc3"], 1e-10, "sandwich::vcovHC(type = 'HC3')")
    o = run_analysis("regression_linear", df, {"y": "y", "x": "x1,x2,x3", "categorical": "g2", "se": "CR2", "cluster": "firm"})
    chk("Linear regression", "CR2 cluster-robust SE", _tab(o, "Coefficients")["SE"], R["lm"]["cr2"], 1e-8, "clubSandwich::vcovCR(type = 'CR2')")
    o = run_analysis("regression_linear", df, {"y": "y", "x": "x1,x2,x3", "categorical": "g2", "se": "CR1", "cluster": "firm"})
    chk("Linear regression", "CR1 cluster-robust SE", _tab(o, "Coefficients")["SE"], R["lm"]["cr1"], 1e-8, "clubSandwich::vcovCR(type = 'CR1S')")
    o = run_analysis("regression_logistic", df, {"y": "ybin", "x": "x1,x3"}); c = _tab(o, "Coefficients"); s = _tab(o, "Model summary").iloc[0]
    chk("Logistic regression", "coefficients, SE", list(c["B"]) + list(c["SE"]), R["logit"]["b"] + R["logit"]["se"], 1e-6, "stats::glm(binomial)")
    chk("Logistic regression", "deviance (−2LL)", [s["−2LL"]], [R["logit"]["dev"]], 1e-6, "stats::glm(binomial)")
    o = run_analysis("regression_multinomial", df, {"y": "ycat", "x": "x1,x3", "base": "stay"}); c = _tab(o, "Coefficients (vs reference category)")
    ours = [c[(c["Outcome"] == row)]["B"].tolist() for row in R["multinom"]["rows"]]
    chk("Multinomial logistic", "coefficients", np.ravel(ours), np.ravel(R["multinom"]["b"]), 1e-4, "nnet::multinom")
    ours_se = [c[(c["Outcome"] == row)]["SE"].tolist() for row in R["multinom"]["rows"]]
    chk("Multinomial logistic", "standard errors", np.ravel(ours_se), np.ravel(R["multinom"]["se"]), 1e-4, "nnet::multinom (Hessian)")
    o = run_analysis("regression_ordinal", df, {"y": "yord", "x": "x1,x3"})
    chk("Ordinal logistic", "coefficients", _tab(o, "Coefficients")["B"], R["polr"]["b"], 1e-4, "MASS::polr")
    chk("Ordinal logistic", "thresholds", _tab(o, "Thresholds")["τ"], R["polr"]["zeta"], 1e-4, "MASS::polr")
    chk("Ordinal logistic", "SE", _tab(o, "Coefficients")["SE"], R["polr"]["se"], 1e-3, "MASS::polr (Hessian)")

    o = run_analysis("reliability", df, {"items": "q1,q2,q3"}); t = _tab(o, "Reliability").iloc[0]; it = _tab(o, "Item statistics")
    chk("Reliability", "Cronbach's α, standardised α", [t["Cronbach's α"], t["Standardised α"]], [R["alpha"]["raw"], R["alpha"]["std"]], 1e-10, "psych::alpha")
    chk("Reliability", "corrected item–total r, α if deleted", list(it["Corrected item–total r"]) + list(it["α if item deleted"]), R["alpha"]["r_drop"] + R["alpha"]["alpha_drop"], 1e-10, "psych::alpha")
    chk("Reliability", "McDonald's ω (1 factor)", [t["McDonald's ω (total, 1 factor)"]], [R["omega"]], 1e-3, "lavaan one-factor CFA, ω from standardised loadings")
    o = run_analysis("agreement", df, {"rater1": "rater1", "rater2": "rater2", "ordered": True, "categories": "1,2,3,4"}); t = _tab(o, "Agreement statistics").set_index("Statistic")["Value"]
    chk("Agreement", "Cohen's κ, weighted κ (linear, quadratic)", [t["Cohen's κ"], t["Weighted κ (linear)"], t["Weighted κ (quadratic)"]], [R["kappa"]["unweighted"], R["kappa"]["linear"], R["kappa"]["quadratic"]], 1e-10, "irr::kappa2")
    chk("Agreement", "Gwet's AC1", [t["Gwet's AC1"]], [R["kappa"]["ac1"]], 5e-6, "irrCAC::gwet.ac1.raw (reports 5 decimals)")
    o = run_analysis("icc", df, {"raters": "icc1,icc2,icc3"})
    chk("ICC", "ICC1, ICC2, ICC3, ICC1k, ICC2k, ICC3k", _tab(o, "Intraclass correlations")["ICC"], R["icc"]["icc"], 1e-10, "psych::ICC(lmer = FALSE)")
    o = run_analysis("efa", df, {"items": ",".join(f"q{i}" for i in range(1, 7)), "n_factors": 2, "method": "ml", "rotation": "varimax"})
    L = _tab(o, "Loadings (ml, varimax)"); Lr = np.array(R["efa"]["loadings"])
    ours = L[["F1", "F2"]].to_numpy()
    best = min(((np.abs(np.abs(ours[:, p]) - np.abs(Lr))).max(), p) for p in ([0, 1], [1, 0]))
    chk("Exploratory FA", "ML varimax loadings (|λ|, factor order aligned)", [best[0]], [0.0], 2e-3, "psych::fa(fm = 'ml', rotate = 'varimax')")
    chk("Exploratory FA", "communalities", L["Communality"], R["efa"]["communality"], 2e-3, "psych::fa")
    sa = _tab(o, "Sampling adequacy").iloc[0]
    chk("Exploratory FA", "KMO, Bartlett χ²", [sa["KMO"], sa["Bartlett χ²"]], [R["kmo"], R["bartlett"]], 1e-6, "psych::KMO, psych::cortest.bartlett")
    o = run_analysis("cfa", df, {"model": "F1 =~ q1 + q2 + q3\nF2 =~ q4 + q5 + q6"}); t = _tab(o, "Model fit").iloc[0]
    chk("Confirmatory FA", "χ², df, CFI, TLI, RMSEA, SRMR", [t["χ²"], t["df"], t["CFI"], t["TLI"], t["RMSEA"], t["SRMR"]], [R["cfa"][k] for k in ("chisq", "df", "cfi", "tli", "rmsea", "srmr")], 1e-8, "lavaan::cfa (same engine)")
    for test, key, eff, kw, tol in (("t_independent", "t", .5, {}, 1e-3), ("anova", "anova", .25, {"k": 3}, 1e-3), ("correlation", "r", .3, {}, 1e-3), ("chisquare", "chisq", .3, {"k": 3}, 1e-3)):
        o = run_analysis("power", df, {"test": test, "effect": eff, **kw}); v = _tab(o, "Required sample size").iloc[0]["Exact value"]
        chk("Power", f"required n ({test})", [v], [R["power"][key]], tol, f"pwr::pwr.{ {'t_independent':'t.test','anova':'anova.test','correlation':'r.test','chisquare':'chisq.test'}[test] }")

    cj = pd.read_csv(conjoint_csv)
    o = run_analysis("p1_conjoint", cj, {"attributes": "standards_compliance,track_record,capital_commitment,local_network", "chosen": "chosen", "respondent": "respondent"})
    am = _tab(o, "AMCEs (CR2 by respondent)")
    chk("Conjoint AMCE", "estimates", am["estimate"], R["amce"]["b"], 1e-10, "stats::lm on dummies")
    chk("Conjoint AMCE", "CR2 SE (respondent clusters)", am["se"], R["amce"]["cr2"], 1e-8, "clubSandwich::vcovCR(type = 'CR2')")
    return rows, R["versions"]


def write_report(rows, versions, path: Path):
    import scipy
    import statsmodels
    df = pd.DataFrame(rows)
    n_pass = int((df["Result"] == "PASS").sum())
    lines = [f"# ClockBind {__version__} — validation against R", "",
             f"Generated {_dt.datetime.now():%Y-%m-%d %H:%M} by `clockbind validate all`. Each row compares a statistic computed by ClockBind with the same statistic from an established R function on the same data (`validation/validation_data.csv`, synthetic, n = 300; `examples/conjoint_synthetic.csv`).", "",
             f"**Result: {n_pass} of {len(df)} checks pass.**", "",
             f"Python engines: SciPy {scipy.__version__}, statsmodels {statsmodels.__version__}. R {versions['R']}: " + ", ".join(f"{k} {v}" for k, v in versions.items() if k != "R") + ".", "",
             "| Procedure | Statistic | R reference | Max abs. difference | Tolerance | Result |", "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['Procedure']} | {r['Statistic']} | `{r['R reference']}` | {r['Max |difference|']:.2e} | {r['Tolerance']:.0e} | {r['Result']} |")
    lines += ["", "## Also validated elsewhere",
              "- **P3 overlap weights**: propensity scores, weights, weighted arm means and CR2 SEs against R `PSweight` and `clubSandwich` (`clockbind validate weights`; see tests).",
              "- **Bridge screening**: the browser app's JavaScript engine gives identical levels, counts, checks and protocol hash to the Python engine on 14 reference cases.",
              "", "## Tolerances",
              "Closed-form statistics must agree to 1e-8–1e-10. Iterative estimators (multinomial and ordinal logit, factor analysis) are compared at 1e-3–1e-4 because optimisers stop at slightly different points. Tukey-adjusted p-values use different numerical integration of the studentized range distribution (2e-3). irrCAC rounds its AC1 estimate to 5 decimals (5e-6). Power analysis compares the exact (non-integer) required n from root-finding (1e-3)."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    df.to_csv(path.with_name("validation_results.csv"), index=False)
    return n_pass, len(df)
