"""Survey planner: sample size per planned analysis, completes per group, invitations, survey length and an
anonymity check. Same formulas as the Quartile survey_plan tool (R), so both give identical numbers:
conjoint Johnson-Orme rule N >= 500c/(t a) (Orme, 2010); two-sample t test (Cohen, 1988); CFA RMSEA close-fit
power (MacCallum, Browne & Sugawara, 1996); noncentral F for added predictors (Cohen's f2); logistic regression
events per variable (Peduzzi et al., 1996) with outcome-rate precision (Riley et al., 2020); Fisher z for r;
finite population correction; invitations = completes / (response rate x (1 - loss) x eligibility);
k-anonymity of background questions (Sweeney, 2002).
"""
from __future__ import annotations
import math
from scipy import stats


def _solve(fun, target, lo=2, hi=10**6):
    _f = fun
    fun = lambda n: (lambda v: 1.0 if v != v else v)(_f(n))
    if fun(hi) < target:
        return None
    while hi - lo > 1:
        m = (lo + hi) // 2
        if fun(m) >= target:
            hi = m
        else:
            lo = m
    return hi


def _ttest_power(n, d, alpha):
    df = 2 * n - 2
    ncp = d * math.sqrt(n / 2)
    tc = stats.t.ppf(1 - alpha / 2, df)
    pw = stats.nct.sf(tc, df, ncp) + stats.nct.cdf(-tc, df, ncp)
    return 1.0 if math.isnan(pw) else pw  # nct can return nan far in the tail, where power is 1


def component(c: dict, alpha: float, power: float) -> dict:
    t = c["type"]
    if t == "conjoint":
        lev, tasks, alt = c.get("levels_max", 4), c.get("tasks", 8), c.get("alternatives", 2)
        return {"type": t, "per_group": bool(c.get("per_group", False)), "n": math.ceil(500 * lev / (tasks * alt)),
                "formula": "Johnson-Orme: N >= 500 c / (t a)", "source": "Orme (2010)"}
    if t == "two_group":
        d = c.get("d", 0.3)
        ng = _solve(lambda n: _ttest_power(n, d, alpha), power)
        return {"type": t, "per_group": bool(c.get("per_group", False)), "n": 2 * ng, "n_per_arm": ng, "source": "Cohen (1988)"}
    if t == "cfa":
        p, k, e0, ea = c.get("items", 12), c.get("factors", 3), c.get("rmsea0", 0.05), c.get("rmsea_a", 0.08)
        df = p * (p + 1) / 2 - (2 * p + k * (k - 1) / 2)
        if df < 1:
            raise ValueError("CFA model has no degrees of freedom")
        def pw(N):
            c0 = stats.ncx2.ppf(1 - alpha, df, (N - 1) * df * e0 ** 2)
            return stats.ncx2.sf(c0, df, (N - 1) * df * ea ** 2)
        n = max(_solve(pw, power, lo=10), c.get("min_n", 0))
        return {"type": t, "per_group": bool(c.get("per_group", True)), "n": n, "df": df, "source": "MacCallum, Browne & Sugawara (1996)"}
    if t == "regression":
        f2, u, tot = c.get("f2", 0.02), c.get("predictors", 1), c.get("total_predictors", c.get("predictors", 1))
        def pw(N):
            v = N - tot - 1
            if v < 1:
                return 0.0
            return stats.ncf.sf(stats.f.ppf(1 - alpha, u, v), u, v, f2 * N)
        return {"type": t, "per_group": bool(c.get("per_group", False)), "n": _solve(pw, power, lo=tot + 2), "source": "Cohen (1988)"}
    if t == "logistic":
        k, phi, epv, delta = c.get("predictors", 8), c.get("event_rate", 0.3), c.get("epv", 10), c.get("precision", 0.05)
        n_epv = math.ceil(epv * k / min(phi, 1 - phi))
        n_prec = math.ceil((stats.norm.ppf(1 - alpha / 2) / delta) ** 2 * phi * (1 - phi))
        return {"type": t, "per_group": bool(c.get("per_group", False)), "n": max(n_epv, n_prec), "n_epv": n_epv,
                "n_precision": n_prec, "source": "Peduzzi et al. (1996); Riley et al. (2020)"}
    if t == "correlation":
        r = c.get("r", 0.2)
        def pw(n):
            z = math.atanh(r) * math.sqrt(max(n, 4) - 3); zc = stats.norm.ppf(1 - alpha / 2)
            return stats.norm.cdf(z - zc) + stats.norm.cdf(-z - zc)
        return {"type": t, "per_group": bool(c.get("per_group", False)), "n": _solve(pw, power, lo=4), "source": "Cohen (1988)"}
    raise ValueError(f"unknown component type {t!r}")


def plan(s: dict) -> dict:
    alpha, power, loss = s.get("alpha", 0.05), s.get("power", 0.8), s.get("completion_loss", 0.15)
    groups = s["groups"]; G = len(groups); k = s.get("k", 5); el = s.get("eligibility", 1)
    papers = []
    for p in s["papers"]:
        comps = [component(c, alpha, power) for c in p["components"]]
        pg = max([0] + [x["n"] for x in comps if x["per_group"]]); ov = max([0] + [x["n"] for x in comps if not x["per_group"]])
        papers.append({"name": p["name"], "components": comps, "items": p.get("items", 0), "per_group_needed": pg,
                       "overall_needed": ov, "total_needed": max(ov, pg * G)})
    per_group = max(x["per_group_needed"] for x in papers); overall = max(x["overall_needed"] for x in papers)
    base = max(per_group, math.ceil(overall / G), math.ceil(s.get("target_total", 0) / G))
    share = 1.0
    for q in s.get("quasi_identifiers", []):
        share *= q.get("smallest_share", 1 / q.get("categories", 2))
    out_groups = []
    for g in groups:
        n = base; Np = g.get("population"); n_use = math.ceil(n / (1 + (n - 1) / Np)) if Np else n
        rr = g.get("response_rate", s.get("response_rate", 0.10))
        inv = math.ceil(n_use / (rr * (1 - loss) * el))
        out_groups.append({"group": g["name"], "completes_needed": n_use, "invitations_needed": inv,
                           "smallest_expected_cell": n_use * share, "k_anonymity_ok": n_use * share >= k})
    conj = sum(c.get("tasks", 8) * c.get("seconds_per_task", 30) for p in s["papers"] for c in p["components"] if c["type"] == "conjoint")
    items = s.get("shared_items", 0) + sum(p["items"] for p in papers)
    minutes = (items * s.get("seconds_per_item", 8) + conj) / 60
    total = sum(g["completes_needed"] for g in out_groups)
    checks = [{"check": "each paper's requirement met", "pass": all(p["total_needed"] <= total and p["per_group_needed"] <= base for p in papers)},
              {"check": "survey length", "pass": minutes <= s.get("max_minutes", 20), "value": round(minutes, 1)},
              {"check": "k-anonymity", "pass": all(g["k_anonymity_ok"] for g in out_groups)}]
    return {"papers": papers, "completes_per_group": base, "total_completes": total,
            "total_invitations": sum(g["invitations_needed"] for g in out_groups), "groups": out_groups,
            "survey_minutes": round(minutes, 1), "pattern_checks": checks, "pattern_ok": all(c["pass"] for c in checks)}
