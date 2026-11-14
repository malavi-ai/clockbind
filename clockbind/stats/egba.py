"""Evidence-Graded Bounds Analysis (EGBA) with survey and interview evidence grades.

A target quantity is written as an expression of parameters (for example the paired cost difference
E1 = o_I - rho*p_S + (F_I - F_S)/Q). Each parameter receives intervals from evidence grades that are admitted
in ladder order (default A-E for documentary/public evidence, then S for survey answers and I for interview
statements). At every rung a parameter's interval is the intersection of the intervals admitted so far; a
parameter with no interval yet is NOT IDENTIFIED. If a newly admitted interval does not overlap the current
one, the conflict is recorded and the earlier interval is kept, so weaker or self-reported evidence can narrow
the bounds but never overrule them. Survey evidence can be given as an interval or as raw answers, from which
the interval is the 95% confidence interval of the mean or the 10th-90th percentile range.

Bounds are found by evaluating the expression at every corner of the parameter box (exact for expressions that
are linear in each parameter, such as E1). The breakdown value of a chosen parameter is the value at which the
least favourable bound reaches the threshold.
"""
from __future__ import annotations
import ast, itertools, math
from statistics import mean, stdev

_ALLOWED = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow,
            ast.USub, ast.UAdd, ast.Name, ast.Load, ast.Constant, ast.Call)
_FUNCS = {"min": min, "max": max, "abs": abs, "log": math.log, "exp": math.exp, "sqrt": math.sqrt}
DEFAULT_LADDER = ["A", "B", "C", "D", "E", "S", "I"]


def _compile(expr: str):
    tree = ast.parse(expr, mode="eval")
    names = set()
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED):
            raise ValueError(f"expression element not allowed: {type(node).__name__}")
        if isinstance(node, ast.Call) and not (isinstance(node.func, ast.Name) and node.func.id in _FUNCS):
            raise ValueError("only min, max, abs, log, exp and sqrt may be called")
        if isinstance(node, ast.Name) and node.id not in _FUNCS:
            names.add(node.id)
    code = compile(tree, "<egba>", "eval")
    return code, names


def survey_interval(values, method: str = "ci95"):
    v = sorted(float(x) for x in values if x is not None)
    if len(v) < 2:
        raise ValueError("survey evidence needs at least two answers")
    if method == "p10p90":
        q = lambda p: v[min(len(v) - 1, max(0, int(math.floor(p * (len(v) - 1) + 0.5))))]
        return [q(0.10), q(0.90)]
    m, s = mean(v), stdev(v)
    h = 1.959964 * s / math.sqrt(len(v))
    return [m - h, m + h]


def _interval(ev):
    if isinstance(ev, dict):
        if "values" in ev:
            return survey_interval(ev["values"], ev.get("method", "ci95"))
        return [float(ev["low"]), float(ev["high"])]
    lo, hi = float(ev[0]), float(ev[1])
    return [min(lo, hi), max(lo, hi)]


def run(spec: dict) -> dict:
    code, names = _compile(spec["expression"])
    fixed = {k: float(v) for k, v in (spec.get("fixed") or {}).items()}
    params = spec.get("parameters") or {}
    ladder = spec.get("ladder") or DEFAULT_LADDER
    thr = float(spec.get("threshold", 0))
    lab_below = spec.get("label_below", "below threshold favoured")
    lab_above = spec.get("label_above", "above threshold favoured")
    unknown = names - set(fixed) - set(params)
    if unknown:
        raise ValueError("no value or evidence for: " + ", ".join(sorted(unknown)))
    if len(params) > 14:
        raise ValueError("at most 14 uncertain parameters")
    f = lambda env: eval(code, {"__builtins__": {}}, {**_FUNCS, **env})

    current = {p: None for p in params}
    rungs, conflicts = [], []
    for g in ladder:
        for p, grades in params.items():
            if g not in grades:
                continue
            new = _interval(grades[g])
            cur = current[p]
            if cur is None:
                current[p] = new
            else:
                lo, hi = max(cur[0], new[0]), min(cur[1], new[1])
                if lo > hi:
                    conflicts.append({"rung": g, "parameter": p, "kept": cur, "rejected": new})
                else:
                    current[p] = [lo, hi]
        missing = [p for p, iv in current.items() if iv is None]
        if missing:
            rungs.append({"rung": g, "status": "NOT IDENTIFIED", "missing": missing})
            continue
        keys = list(current)
        vals = [f({**fixed, **dict(zip(keys, c))}) for c in itertools.product(*[current[k] for k in keys])]
        lo, hi = min(vals), max(vals)
        label = lab_below if hi < thr else lab_above if lo > thr else "assumption-sensitive"
        rungs.append({"rung": g, "status": label, "low": lo, "high": hi,
                      "intervals": {k: list(v) for k, v in current.items()}})

    out = {"expression": spec["expression"], "fixed": fixed, "ladder": ladder, "threshold": thr,
           "rungs": rungs, "conflicts": conflicts,
           "final": rungs[-1] if rungs else None,
           "method": "corner enumeration (exact for expressions linear in each parameter)"}

    bp = spec.get("breakdown_parameter")
    last = rungs[-1] if rungs else None
    if bp and last and "intervals" in last:
        iv = dict(last["intervals"]); a, b = iv[bp]
        others = [k for k in iv if k != bp]
        side = spec.get("breakdown_side", "high")  # 'high': the upper bound must stay below threshold
        def worst(x):
            vs = [f({**fixed, bp: x, **dict(zip(others, c))}) for c in itertools.product(*[iv[k] for k in others])] or [f({**fixed, bp: x})]
            return (max(vs) if side == "high" else min(vs)) - thr
        if spec.get("breakdown_range"):
            a, b = [float(x) for x in spec["breakdown_range"]]
        ga, gb = worst(a), worst(b)
        step = max(abs(b - a), 1.0)
        for _ in range(40):  # widen the search beyond the admitted range until the bound crosses the threshold
            if ga * gb <= 0:
                break
            a, b = a - step, b + step; step *= 2; ga, gb = worst(a), worst(b)
        if ga * gb > 0:
            out["breakdown"] = {"parameter": bp, "value": None, "note": "the bound does not cross the threshold within the admitted range"}
        else:
            for _ in range(200):
                m = (a + b) / 2
                if worst(m) * ga <= 0:
                    b = m
                else:
                    a, ga = m, worst(m)
            out["breakdown"] = {"parameter": bp, "value": (a + b) / 2, "side": side, "admitted_range": iv[bp], "inside_admitted_range": iv[bp][0] <= (a + b) / 2 <= iv[bp][1]}
    return out
