# ClockBind 1.4.0 — validation against R

Generated 2026-10-04 08:11 by `clockbind validate all`. Each row compares a statistic computed by ClockBind with the same statistic from an established R function on the same data (`validation/validation_data.csv`, synthetic, n = 300; `examples/conjoint_synthetic.csv`).

**Result: 50 of 50 checks pass.**

Python engines: SciPy 1.17.1, statsmodels 0.15.0. R 4.3.3: psych 2.6.5, lavaan 0.7.2, irr 0.85, irrCAC 1.4, nnet 7.3.19, MASS 7.3.60.0.1, sandwich 3.1.3, clubSandwich 0.7.0, pwr 1.3.0.

| Procedure | Statistic | R reference | Max abs. difference | Tolerance | Result |
|---|---|---|---|---|---|
| Descriptives | mean, SD, median, Q1 | `base::mean/sd/quantile` | 5.11e-15 | 1e-10 | PASS |
| Descriptives | skewness, kurtosis (G1, G2) | `psych::describe(type = 2)` | 1.72e-15 | 1e-10 | PASS |
| Independent t-test | Student t, p | `stats::t.test(var.equal = TRUE)` | 4.44e-16 | 1e-10 | PASS |
| Independent t-test | Welch t, df, p | `stats::t.test()` | 2.84e-13 | 1e-08 | PASS |
| Independent t-test | Levene F (mean-centred), p | `anova(lm(|y − group mean| ~ g))` | 8.88e-16 | 1e-10 | PASS |
| Paired t-test | t, p | `stats::t.test(paired = TRUE)` | 5.04e-25 | 1e-10 | PASS |
| One-sample t-test | t, p | `stats::t.test(mu = 0)` | 6.66e-16 | 1e-10 | PASS |
| One-way ANOVA | F, p | `stats::aov` | 7.77e-16 | 1e-10 | PASS |
| One-way ANOVA | Welch F, df2, p | `stats::oneway.test` | 3.13e-13 | 1e-08 | PASS |
| One-way ANOVA | Levene F | `anova(lm(|y − group mean| ~ g))` | 1.78e-15 | 1e-10 | PASS |
| Tukey HSD | mean differences | `stats::TukeyHSD` | 9.71e-16 | 1e-10 | PASS |
| Tukey HSD | adjusted p | `stats::TukeyHSD` | 3.86e-13 | 2e-03 | PASS |
| Chi-square | Pearson χ², p | `stats::chisq.test(correct = FALSE)` | 2.22e-16 | 1e-10 | PASS |
| Chi-square 2×2 | Yates χ², p | `stats::chisq.test(correct = TRUE)` | 0.00e+00 | 1e-10 | PASS |
| Fisher's exact | p (two-sided) | `stats::fisher.test` | 0.00e+00 | 1e-08 | PASS |
| Mann–Whitney | U (= R's W), p | `stats::wilcox.test(exact = FALSE)` | 0.00e+00 | 1e-10 | PASS |
| Wilcoxon signed-rank | V, p | `stats::wilcox.test(paired = TRUE, exact = FALSE)` | 2.27e-24 | 1e-10 | PASS |
| Kruskal–Wallis | H, p | `stats::kruskal.test` | 4.44e-16 | 1e-10 | PASS |
| Correlation | pearson coefficient, p | `stats::cor.test(method = 'pearson')` | 2.22e-16 | 1e-10 | PASS |
| Correlation | spearman coefficient, p | `stats::cor.test(method = 'spearman')` | 1.11e-16 | 1e-10 | PASS |
| Correlation | kendall coefficient | `stats::cor.test(method = 'kendall')` | 4.44e-16 | 1e-10 | PASS |
| Linear regression | coefficients | `stats::lm` | 2.44e-15 | 1e-10 | PASS |
| Linear regression | classical SE | `stats::lm` | 7.49e-16 | 1e-10 | PASS |
| Linear regression | R², F | `summary.lm` | 6.39e-14 | 1e-10 | PASS |
| Linear regression | HC3 SE | `sandwich::vcovHC(type = 'HC3')` | 1.33e-15 | 1e-10 | PASS |
| Linear regression | CR2 cluster-robust SE | `clubSandwich::vcovCR(type = 'CR2')` | 1.28e-15 | 1e-08 | PASS |
| Linear regression | CR1 cluster-robust SE | `clubSandwich::vcovCR(type = 'CR1S')` | 3.58e-15 | 1e-08 | PASS |
| Logistic regression | coefficients, SE | `stats::glm(binomial)` | 1.99e-08 | 1e-06 | PASS |
| Logistic regression | deviance (−2LL) | `stats::glm(binomial)` | 1.71e-13 | 1e-06 | PASS |
| Multinomial logistic | coefficients | `nnet::multinom` | 3.01e-08 | 1e-04 | PASS |
| Multinomial logistic | standard errors | `nnet::multinom (Hessian)` | 9.49e-10 | 1e-04 | PASS |
| Ordinal logistic | coefficients | `MASS::polr` | 1.06e-05 | 1e-04 | PASS |
| Ordinal logistic | thresholds | `MASS::polr` | 2.91e-05 | 1e-04 | PASS |
| Ordinal logistic | SE | `MASS::polr (Hessian)` | 3.02e-07 | 1e-03 | PASS |
| Reliability | Cronbach's α, standardised α | `psych::alpha` | 3.33e-16 | 1e-10 | PASS |
| Reliability | corrected item–total r, α if deleted | `psych::alpha` | 6.66e-16 | 1e-10 | PASS |
| Reliability | McDonald's ω (1 factor) | `lavaan one-factor CFA, ω from standardised loadings` | 3.27e-08 | 1e-03 | PASS |
| Agreement | Cohen's κ, weighted κ (linear, quadratic) | `irr::kappa2` | 3.33e-16 | 1e-10 | PASS |
| Agreement | Gwet's AC1 | `irrCAC::gwet.ac1.raw (reports 5 decimals)` | 1.16e-06 | 5e-06 | PASS |
| ICC | ICC1, ICC2, ICC3, ICC1k, ICC2k, ICC3k | `psych::ICC(lmer = FALSE)` | 1.22e-15 | 1e-10 | PASS |
| Exploratory FA | ML varimax loadings (|λ|, factor order aligned) | `psych::fa(fm = 'ml', rotate = 'varimax')` | 3.97e-06 | 2e-03 | PASS |
| Exploratory FA | communalities | `psych::fa` | 5.85e-06 | 2e-03 | PASS |
| Exploratory FA | KMO, Bartlett χ² | `psych::KMO, psych::cortest.bartlett` | 1.02e-12 | 1e-06 | PASS |
| Confirmatory FA | χ², df, CFI, TLI, RMSEA, SRMR | `lavaan::cfa (same engine)` | 0.00e+00 | 1e-08 | PASS |
| Power | required n (t_independent) | `pwr::pwr.t.test` | 1.45e-07 | 1e-03 | PASS |
| Power | required n (anova) | `pwr::pwr.anova.test` | 1.24e-05 | 1e-03 | PASS |
| Power | required n (correlation) | `pwr::pwr.r.test` | 2.04e-06 | 1e-03 | PASS |
| Power | required n (chisquare) | `pwr::pwr.chisq.test` | 9.64e-09 | 1e-03 | PASS |
| Conjoint AMCE | estimates | `stats::lm on dummies` | 6.44e-15 | 1e-10 | PASS |
| Conjoint AMCE | CR2 SE (respondent clusters) | `clubSandwich::vcovCR(type = 'CR2')` | 4.54e-16 | 1e-08 | PASS |

## Also validated elsewhere
- **P3 overlap weights**: propensity scores, weights, weighted arm means and CR2 SEs against R `PSweight` and `clubSandwich` (`clockbind validate weights`; see tests).
- **Bridge screening**: the browser app's JavaScript engine gives identical levels, counts, checks and protocol hash to the Python engine on 14 reference cases.

## Tolerances
Closed-form statistics must agree to 1e-8–1e-10. Iterative estimators (multinomial and ordinal logit, factor analysis) are compared at 1e-3–1e-4 because optimisers stop at slightly different points. Tukey-adjusted p-values use different numerical integration of the studentized range distribution (2e-3). irrCAC rounds its AC1 estimate to 5 decimals (5e-6). Power analysis compares the exact (non-integer) required n from root-finding (1e-3).
