"""ClockBind chart style and standard references."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import json as _json
import os as _os
from pathlib import Path as _Path


def load_brand() -> dict:
    """Brand theme: $CLOCKBIND_BRAND (path) or clockbind/assets/brand.json."""
    p = _Path(_os.environ.get("CLOCKBIND_BRAND", _Path(__file__).resolve().parents[1] / "assets" / "brand.json"))
    try:
        return _json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"colors": {}, "fonts": {}}


BRAND = load_brand()
_c = BRAND.get("colors", {})
INK = _c.get("ink", "#14233A")
BRASS = _c.get("accent", "#A4772B")
TEAL = _c.get("second", "#2A7A6D")
SLATE = _c.get("third", "#5F7A98")
ERR = _c.get("error", "#B3452A")
MUTED = _c.get("muted", "#5C6978")
LINE = _c.get("line", "#D3DADB")
PALETTE = [INK, BRASS, TEAL, SLATE, "#8C6410", "#7A4E7E", "#3F8FBF", "#9AA8B8"]

plt.rcParams.update({
    "figure.figsize": (7.2, 4.2), "figure.dpi": 110, "savefig.dpi": 200,
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.edgecolor": LINE, "axes.labelcolor": INK, "axes.titlecolor": INK, "axes.titleweight": "bold",
    "axes.titlesize": 11, "axes.titlelocation": "left", "axes.grid": True, "grid.color": "#E7ECEC", "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "axes.prop_cycle": matplotlib.cycler(color=PALETTE),
    "xtick.color": MUTED, "ytick.color": MUTED, "legend.frameon": False,
})


def fig(w=7.2, h=4.2):
    return plt.subplots(figsize=(w, h))


def _v(mod):
    try:
        return __import__(mod).__version__
    except Exception:
        return "?"


REF = {
    "numpy": "Harris, C. R., et al. (2020). Array programming with NumPy. Nature, 585, 357–362. https://doi.org/10.1038/s41586-020-2649-2",
    "scipy": "Virtanen, P., et al. (2020). SciPy 1.0: Fundamental algorithms for scientific computing in Python. Nature Methods, 17, 261–272. https://doi.org/10.1038/s41592-019-0686-2",
    "statsmodels": "Seabold, S., & Perktold, J. (2010). statsmodels: Econometric and statistical modeling with Python. Proceedings of the 9th Python in Science Conference, 92–96.",
    "pandas": "McKinney, W. (2010). Data structures for statistical computing in Python. Proceedings of the 9th Python in Science Conference, 56–61.",
    "lavaan": "Rosseel, Y. (2012). lavaan: An R package for structural equation modeling. Journal of Statistical Software, 48(2), 1–36. https://doi.org/10.18637/jss.v048.i02",
    "welch": "Welch, B. L. (1947). The generalization of 'Student's' problem when several different population variances are involved. Biometrika, 34(1–2), 28–35.",
    "levene": "Levene, H. (1960). Robust tests for equality of variances. In I. Olkin (Ed.), Contributions to probability and statistics (pp. 278–292). Stanford University Press.",
    "tukey": "Tukey, J. W. (1949). Comparing individual means in the analysis of variance. Biometrics, 5(2), 99–114.",
    "cohen_d": "Cohen, J. (1988). Statistical power analysis for the behavioral sciences (2nd ed.). Lawrence Erlbaum.",
    "cramer": "Cramér, H. (1946). Mathematical methods of statistics. Princeton University Press.",
    "mann_whitney": "Mann, H. B., & Whitney, D. R. (1947). On a test of whether one of two random variables is stochastically larger than the other. Annals of Mathematical Statistics, 18(1), 50–60.",
    "kruskal": "Kruskal, W. H., & Wallis, W. A. (1952). Use of ranks in one-criterion variance analysis. Journal of the American Statistical Association, 47(260), 583–621.",
    "wilcoxon": "Wilcoxon, F. (1945). Individual comparisons by ranking methods. Biometrics Bulletin, 1(6), 80–83.",
    "shapiro": "Shapiro, S. S., & Wilk, M. B. (1965). An analysis of variance test for normality. Biometrika, 52(3–4), 591–611.",
    "cronbach": "Cronbach, L. J. (1951). Coefficient alpha and the internal structure of tests. Psychometrika, 16(3), 297–334.",
    "mcdonald": "McDonald, R. P. (1999). Test theory: A unified treatment. Lawrence Erlbaum.",
    "kappa": "Cohen, J. (1960). A coefficient of agreement for nominal scales. Educational and Psychological Measurement, 20(1), 37–46.",
    "gwet": "Gwet, K. L. (2008). Computing inter-rater reliability and its variance in the presence of high agreement. British Journal of Mathematical and Statistical Psychology, 61(1), 29–48.",
    "icc": "Shrout, P. E., & Fleiss, J. L. (1979). Intraclass correlations: Uses in assessing rater reliability. Psychological Bulletin, 86(2), 420–428.",
    "cr2": "Pustejovsky, J. E., & Tipton, E. (2018). Small-sample methods for cluster-robust variance estimation and hypothesis testing in fixed effects models. Journal of Business & Economic Statistics, 36(4), 672–683.",
    "bell_mccaffrey": "Bell, R. M., & McCaffrey, D. F. (2002). Bias reduction in standard errors for linear regression with multi-stage samples. Survey Methodology, 28(2), 169–181.",
    "hc3": "MacKinnon, J. G., & White, H. (1985). Some heteroskedasticity-consistent covariance matrix estimators with improved finite sample properties. Journal of Econometrics, 29(3), 305–325.",
    "kmo": "Kaiser, H. F. (1974). An index of factorial simplicity. Psychometrika, 39(1), 31–36.",
    "bartlett": "Bartlett, M. S. (1950). Tests of significance in factor analysis. British Journal of Statistical Psychology, 3(2), 77–85.",
    "overlap": "Li, F., & Li, F. (2019). Propensity score weighting for causal inference with multiple treatments. Annals of Applied Statistics, 13(4), 2389–2415.",
    "amce": "Hainmueller, J., Hopkins, D. J., & Yamamoto, T. (2014). Causal inference in conjoint analysis. Political Analysis, 22(1), 1–30.",
    "fleiss_ci": "Agresti, A. (2013). Categorical data analysis (3rd ed.). Wiley.",
}
