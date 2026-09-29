"""Cross-check of the binding engine against an independent reference implementation on random networks."""
import random
import sys
from pathlib import Path

import pandas as pd

from clockbind.binding import evaluate_all

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "validation" / "binding"))
import reference as ref  # noqa: E402

CLOCKS = ["finance", "payment", "fulfilment", "logistics", "operational-readiness"]
T0 = pd.Timestamp("2026-01-01")


def _date(d):
    return (T0 + pd.Timedelta(days=d)).isoformat()


def random_case(rng, i):
    n = rng.randint(1, 7)
    names = [f"s{k}" for k in range(n)]
    steps, rows = {}, []
    finish_lo, finish_hi = {}, {}
    anchor = (0.0, 0.0) if rng.random() < .7 else (0.0, round(rng.uniform(0, 1), 2))
    for k, nm in enumerate(names):
        preds = sorted(rng.sample(names[:k], rng.randint(0, min(2, k)))) if k else []
        clock = rng.choice(CLOCKS[:rng.randint(2, 5)])
        base = max([finish_hi[p] for p in preds], default=anchor[1])
        lo = round(base + rng.choice([0, 0.25, 0.5, 1, 2, 3, 5]) + rng.random() * 2, 2)
        hi = lo if rng.random() < .6 else round(lo + rng.choice([0.25, 0.5, 1, 2]), 2)
        exp = None if rng.random() < .1 else rng.choice([0.25, 0.5, 1, 2, 3])
        steps[nm] = {"preds": preds, "clock": clock, "exp": exp}
        finish_lo[nm], finish_hi[nm] = lo, hi
        rows.append({"episode": f"R{i}", "step": nm, "clock": clock, "predecessors": ";".join(preds),
                     "finish_earliest": _date(lo), "finish_latest": _date(hi), "expected_days": exp, "source": "DOC-000"})
    r = names[-1]
    tw_lo = round(finish_hi[r] - rng.uniform(-2, 8), 2)
    tw = (tw_lo, tw_lo if rng.random() < .6 else round(tw_lo + rng.choice([0.5, 1, 2]), 2))
    ep = {"episode": f"R{i}", "anchor_earliest": _date(anchor[0]), "anchor_latest": _date(anchor[1]),
          "tw_earliest": _date(tw[0]), "tw_latest": _date(tw[1]), "r_step": r}
    expected = ref.final(steps, {n: (finish_lo[n], finish_hi[n]) for n in names}, anchor, tw, r)
    return ep, rows, expected


def test_engine_matches_independent_reference_on_2000_random_networks():
    rng = random.Random(20260927)
    eps, rows, exp = [], [], {}
    for i in range(2000):
        e, s, x = random_case(rng, i)
        eps.append(e); rows += s; exp[e["episode"]] = x
    res = evaluate_all(pd.DataFrame(eps), pd.DataFrame(rows)).set_index("episode")
    bad = []
    for eid, (label, clocks) in exp.items():
        got = res.loc[eid]
        got_clocks = tuple(sorted(c for c in str(got["binding_clocks"]).split("; ") if c))
        if got["verdict"] != label or (label not in ("Indeterminate", "Non-binding") and got_clocks != tuple(sorted(clocks))):
            bad.append((eid, label, clocks, got["verdict"], got_clocks, got["reason"]))
    assert not bad, f"{len(bad)} mismatches, first: {bad[:3]}"
    # the random design must actually exercise every outcome
    seen = set(res["verdict"])
    for v in ("Non-binding", "Finance-binding", "Jointly binding", "Indeterminate"):
        assert v in seen, v
