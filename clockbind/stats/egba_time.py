"""EGBA-Time: evidence-graded bounds for activation times of financing routes.

For each route, the activation latency (first auditable action to usable funds) is bounded from incomplete evidence:
  1. Stage sums: total latency = sum of stage durations; each stage's interval comes from the evidence grades admitted
     in ladder order (A-E documentary/public, S survey, I interview), intersected as in EGBA; total bounds = sum of
     stage lower bounds and sum of stage upper bounds. A directly reported total interval, if given, is intersected too.
  2. Censoring: a route still pending after `elapsed` days has latency >= elapsed (lower bound raised); if an upper
     bound falls below the elapsed time the conflict is reported and the upper bound becomes open (max_latency).
  3. Interval answers: survey answers such as "2-4 weeks" enter directly as intervals (converted to the chosen unit).
  4. Deadline classification against the documented action window W (a value or an interval [W_lo, W_hi]):
     surely on time if L_hi <= W_lo; surely late if L_lo > W_hi; otherwise undetermined. Refused, withdrawn or
     abandoned routes are not usable in the episode. Routes with no evidence are not identified.
     The temporal margin interval is [W_lo - L_hi, W_hi - L_lo]; the window needed to be surely on time is L_hi.
  5. Share bounds (Manski, 1989/2003 worst-case logic): among all routes, the share usable in time lies between
     (surely on time) / K and (surely on time + undetermined + not identified) / K. Each endpoint also gets a 95%
     Wilson interval for sampling uncertainty, reported separately from the identification bounds.
"""
from __future__ import annotations
import math

DEFAULT_LADDER = ["A", "B", "C", "D", "E", "S", "I"]
UNIT = {"days": 1.0, "weeks": 7.0, "months": 30.4375}
NOT_USABLE = {"refused", "withdrawn", "abandoned", "conditions_unmet"}


def _iv(ev, unit_factor):
    if isinstance(ev, dict):
        f = UNIT[ev["unit"]] / unit_factor if ev.get("unit") else 1.0
        lo, hi = float(ev["low"]), float(ev["high"])
    else:
        f = 1.0
        lo, hi = float(ev[0]), float(ev[1])
    lo, hi = min(lo, hi), max(lo, hi)
    return [lo * f, hi * f]


def _admit(grades: dict, ladder, unit_factor, where, conflicts):
    cur = None
    for g in ladder:
        if g not in grades:
            continue
        new = _iv(grades[g], unit_factor)
        if cur is None:
            cur = new
        else:
            lo, hi = max(cur[0], new[0]), min(cur[1], new[1])
            if lo > hi:
                conflicts.append({"where": where, "grade": g, "kept": cur, "rejected": new})
            else:
                cur = [lo, hi]
    return cur


def wilson(k: int, n: int, z: float = 1.959964):
    if n == 0:
        return [None, None]
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0.0, c - h), min(1.0, c + h)]


def run(spec: dict) -> dict:
    ladder = spec.get("ladder") or DEFAULT_LADDER
    unit = spec.get("unit", "days")
    uf = UNIT[unit]  # outputs in `unit`; an input with its own unit is converted
    cap = float(spec.get("max_latency", 365))
    out_routes, conflicts = [], []
    counts = {"surely on time": 0, "surely late": 0, "undetermined": 0, "not usable": 0, "not identified": 0}
    for r in spec["routes"]:
        rid = r.get("id", f"route{len(out_routes) + 1}")
        status = r.get("status", "completed")
        stages = r.get("stages") or {}
        st_iv, missing = {}, []
        for s, grades in stages.items():
            iv = _admit(grades, ladder, uf, f"{rid}/{s}", conflicts)
            if iv is None:
                missing.append(s)
            st_iv[s] = iv
        L = None
        if stages and not missing:
            L = [sum(v[0] for v in st_iv.values()), sum(v[1] for v in st_iv.values())]
        if r.get("total"):
            T = _admit(r["total"], ladder, uf, f"{rid}/total", conflicts)
            if T is not None:
                if L is None:
                    L = T
                else:
                    lo, hi = max(L[0], T[0]), min(L[1], T[1])
                    if lo > hi:
                        conflicts.append({"where": f"{rid}/total", "grade": "total", "kept": L, "rejected": T})
                    else:
                        L = [lo, hi]
        if status == "pending" and r.get("elapsed") is not None:
            e = float(r["elapsed"])
            if L is None:
                L = [e, cap]
            else:
                if L[1] < e:
                    conflicts.append({"where": f"{rid}/censoring", "grade": "elapsed", "kept": [e, cap], "rejected": L})
                    L = [e, cap]
                else:
                    L = [max(L[0], e), L[1]]
        w = r.get("window")
        W = None if w is None else ([float(w), float(w)] if not isinstance(w, (list, tuple)) else sorted([float(w[0]), float(w[1])]))
        rec = {"id": rid, "status": status, "stages": st_iv, "missing_stages": missing, "latency": L, "window": W}
        if status in NOT_USABLE:
            label = "not usable"
        elif L is None or W is None:
            label = "not identified"
        elif L[1] <= W[0]:
            label = "surely on time"
        elif L[0] > W[1]:
            label = "surely late"
        else:
            label = "undetermined"
        rec["label"] = label
        if L is not None and W is not None:
            rec["margin"] = [W[0] - L[1], W[1] - L[0]]
            rec["window_needed_surely_on_time"] = L[1]
        rec["ex_ante"] = status in ("screened_out", "not_attempted")
        counts[label] += 1
        out_routes.append(rec)
    K = len(out_routes)
    lo_k = counts["surely on time"]
    hi_k = counts["surely on time"] + counts["undetermined"] + counts["not identified"]
    share = {"routes": K, "lower": lo_k / K if K else None, "upper": hi_k / K if K else None,
             "lower_wilson95": wilson(lo_k, K), "upper_wilson95": wilson(hi_k, K),
             "rule": "Manski worst-case: undetermined and not-identified routes counted as late for the lower bound and on time for the upper bound"}
    return {"unit": unit, "ladder": ladder, "routes": out_routes, "counts": counts, "share_usable_in_time": share, "conflicts": conflicts}
