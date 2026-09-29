"""Independent reference implementation of the registered binding rule, written separately from
clockbind/binding.py (no shared code) to cross-check it. Plain dictionaries, explicit recursion."""
from itertools import combinations

EPS = 1e-9


def realised(steps, finish, anchor):
    """Realised duration of each step = finish - ready, ready = latest predecessor finish (or anchor)."""
    out = {}
    for n, s in steps.items():
        ready = max([finish[p] for p in s["preds"]]) if s["preds"] else anchor
        out[n] = max(finish[n] - ready, 0.0)
    return out


def finish_time(steps, dur, anchor, target, memo=None):
    memo = {} if memo is None else memo
    if target in memo:
        return memo[target]
    s = steps[target]
    ready = max([finish_time(steps, dur, anchor, p, memo) for p in s["preds"]]) if s["preds"] else anchor
    memo[target] = ready + dur[target]
    return memo[target]


def ancestors(steps, target):
    seen = {target}
    stack = [target]
    while stack:
        for p in steps[stack.pop()]["preds"]:
            if p not in seen:
                seen.add(p)
                stack.append(p)
    return seen


def slack_with(steps, finish, anchor, tw, r, correct):
    anc = ancestors(steps, r)
    sub = {n: steps[n] for n in anc}
    dur = realised(sub, finish, anchor)
    for n in anc:
        if sub[n]["clock"] in correct and sub[n]["exp"] is not None:
            dur[n] = min(dur[n], sub[n]["exp"])
    return tw - finish_time(sub, dur, anchor, r)


def verdict(steps, finish, anchor, tw, r):
    anc = ancestors(steps, r)
    clocks = sorted({steps[n]["clock"] for n in anc})
    if slack_with(steps, finish, anchor, tw, r, set()) >= -EPS:
        return ("Non-binding", ())
    testable = [c for c in clocks if all(steps[n]["exp"] is not None for n in anc if steps[n]["clock"] == c)]
    singles = tuple(sorted(c for c in testable if slack_with(steps, finish, anchor, tw, r, {c}) >= -EPS))
    if len(singles) == 1:
        return ("single", singles)
    if len(singles) > 1:
        return ("Multiple sufficient corrections", singles)
    if len(testable) < len(clocks):
        return ("Indeterminate", ())
    pairs = tuple(sorted(" + ".join(p) for p in combinations(testable, 2) if slack_with(steps, finish, anchor, tw, r, set(p)) >= -EPS))
    if pairs:
        return ("Jointly binding", pairs)
    if len(testable) > 2 and slack_with(steps, finish, anchor, tw, r, set(testable)) >= -EPS:
        return ("Jointly binding", (" + ".join(testable),))
    return ("Window infeasible at ex-ante durations", ())


LABEL = {"finance": "Finance-binding", "payment": "Payment-binding", "fulfilment": "Fulfilment-binding",
         "logistics": "Logistics-binding", "operational-readiness": "Operational-readiness-binding"}


def final(steps, bounds, anchor, tw, r):
    """bounds: {step: (lo, hi)}; anchor, tw: (lo, hi). Returns (verdict label, clocks) under the sign-stability rule."""
    res = []
    for i in (0, 1):
        v = verdict(steps, {n: b[i] for n, b in bounds.items()}, anchor[i], tw[i], r)
        if v[0] == "single":
            v = (LABEL[v[1][0]], v[1])
        res.append(v)
    return res[0] if res[0] == res[1] else ("Indeterminate", ())
