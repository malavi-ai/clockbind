<img src="clockbind/assets/clockbind-logo-horizontal.svg" width="360" alt="ClockBind — Which clock binds?">

# ClockBind
**A reproducible statistics studio for doctoral research.** Point-and-click app, command line and syntax files; every procedure validated against R.


| | |
|---|---|
| **Studio** | Local app in your browser (like SPSS): open Excel/CSV/SPSS files, choose an analysis from the menu, get tables, charts and a *methods text*, export everything to Word. Data never leave your computer. |
| **Reproducible** | Every result carries its *syntax* (JSON). `clockbind syntax run` re-creates the whole output from the data file, with a manifest (data hash, software versions, code hash). |
| **Validated** | `clockbind validate all` compares 50 statistics with established R functions (stats, psych, lavaan, irr, irrCAC, nnet, MASS, sandwich, clubSandwich, pwr) and writes [VALIDATION.md](VALIDATION.md). Current result: **50 of 50 pass**. |
| **Citable** | MIT licence, `CITATION.cff`, Zenodo DOI per release (see [RELEASE_GUIDE.md](RELEASE_GUIDE.md)). |

## Analyses
- **Data:** missing-data overview.
- **Descriptive statistics:** frequencies, descriptives (SPSS-style skewness/kurtosis), normality (Shapiro–Wilk, Q–Q), crosstabs (χ², likelihood ratio, Yates, Fisher, Cramér's V).
- **Compare means:** independent t-test (Student and Welch, Levene, Cohen's d); paired and one-sample t-tests; one-way ANOVA (Welch ANOVA, η², ω², Tukey HSD).
- **Non-parametric tests:** Mann–Whitney U, Wilcoxon signed-rank, Kruskal–Wallis.
- **Correlate:** Pearson, Spearman, Kendall, with CIs and a heat map.
- **Regression:**
  - linear: classical, HC3, cluster-robust CR1/CR2, weights, standardised β, VIF;
  - logistic: odds ratios, pseudo-R², classification table;
  - multinomial and ordinal.
- **Scale:** Cronbach's α and standardised α, McDonald's ω, item statistics; Cohen's κ, weighted κ, Gwet's AC1; ICC (6 types).
- **Dimension reduction:** EFA (KMO, Bartlett, scree, ML/minres/principal, varimax/oblimin/promax); CFA via **lavaan**, with fit indices, standardised loadings, AVE and CR.
- **Planning:** power and sample size (t, paired t, ANOVA, correlation, χ²).
- **Doctoral modules:**
  - Bridge screening with evidence levels;
  - P3 multi-arm overlap weights (diagnostics, estimability gates, CR2 contrasts, cluster bootstrap);
  - P1 conjoint AMCEs with CR2 by respondent.

## Install (Mac)
1. Double-click `Install_ClockBind_on_Mac.command`.
2. Double-click `Start_ClockBind_Studio.command`.

R is optional: it is needed only for CFA (lavaan) and for re-running the validation.

Command line:
```
clockbind studio open                                   # the app
clockbind syntax list                                   # all analyses
clockbind syntax run --data data.xlsx --syntax my_syntax.json
clockbind screen run --data screening.xlsx --gates gates.json
clockbind validate all                                  # regenerate VALIDATION.md
```
`phdstat` remains as an alias of `clockbind`.

## Citing
> Alavi, S. M. (2026). *ClockBind: a reproducible statistics studio for doctoral research* (Version 1.0.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.XXXXXXX

Source code: https://github.com/malavi-ai/clockbind (the DOI is added after the first Zenodo release).

Please also cite the underlying libraries named in each result (statsmodels, SciPy, lavaan, …).

## Principles and limits
- Computations come from established libraries. ClockBind adds the interface, provenance and validation; no AI runs inside the software.
- Missing data: listwise deletion by default. Pre-specify your rule (e.g. multiple imputation) before analysing outcomes; multiple imputation is planned.
- Cluster-robust tests use G − 1 degrees of freedom. clubSandwich uses Satterthwaite df, so p-values can differ slightly with few clusters even when SEs agree.
- The P3 simulation assumptions (`clockbind/dgp`) are placeholders, not findings.
- Qualitative coding belongs in dedicated software (MAXQDA, NVivo). ClockBind computes the agreement statistics.

Developed with the assistance of Claude (Anthropic); see [AI_ASSISTANCE.md](AI_ASSISTANCE.md). MIT licence.
