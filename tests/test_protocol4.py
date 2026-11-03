"""Protocol 4.0: equivalence with v3.4, institutional clock, revealed-in-process rule, claim ceiling,
blind packets, concordance and Krippendorff's alpha (hand-computed cases)."""
import itertools
import random

import pandas as pd
import pytest

from clockbind import binding as b3
from clockbind.binding import evaluate_all
from clockbind.binding4 import (blind_packet, concordance, evaluate_all_v4, krippendorff_alpha_nominal,
                                layer_summary)

EP = ["episode", "anchor_earliest", "anchor_latest", "tw_earliest", "tw_latest", "r_step"]
ST = ["episode", "step", "clock", "predecessors", "finish_earliest", "finish_latest", "expected_days",
      "ex_ante_status", "revealed_at", "source_class", "actionable_from", "direct_record"]


def frames(eps, steps):
    if eps and not isinstance(eps[0], list):
        eps = [eps]
    return pd.DataFrame(eps, columns=EP), pd.DataFrame(steps, columns=ST)


def chain(eid, finishes, expected, tw, clocks, status=None, revealed=None, src=None, act=None, direct=None):
    names = [f"s{i}" for i in range(len(finishes))]
    rows = []
    for i, n in enumerate(names):
        rows.append([eid, n, clocks[i], names[i - 1] if i else "", finishes[i], None, expected[i],
                     (status or [None] * len(names))[i], (revealed or [None] * len(names))[i],
                     (src or ["third-party"] * len(names))[i], (act or [None] * len(names))[i],
                     (direct or [None] * len(names))[i]])
    return [eid, "2026-01-01", None, tw, None, names[-1]], rows


def test_identical_to_v34_without_new_features():
    rng = random.Random(7)
    eps, steps = [], []
    clocks = ["finance", "payment", "fulfilment", "logistics", "operational-readiness"]
    for k in range(200):
        n = rng.randint(2, 5)
        day, fin, exp = 1, [], []
        for _ in range(n):
            day += rng.randint(0, 5)
            fin.append(f"2026-02-{day:02d}")
            exp.append(rng.choice([None, 1, 2, 3]))
        e, s = chain(f"R{k}", fin, exp, f"2026-02-{rng.randint(5, 26):02d}", [rng.choice(clocks) for _ in range(n)])
        eps.append(e)
        steps += s
    e, s = frames(eps, steps)
    v3 = evaluate_all(e, s[ST[:7]]).set_index("episode")
    v4 = evaluate_all_v4(e, s).set_index("episode")
    for col in ["verdict", "binding_clocks", "indeterminate_reason", "decisive_slack_earliest_days", "decisive_slack_latest_days",
                "finance_actionable", "sign_stable"]:
        pd.testing.assert_series_equal(v3[col], v4[col], check_names=False)


def test_v3_globals_restored_after_v4():
    before = (dict(b3.CLOCK_LABELS), dict(b3.CLOCK_ALIASES))
    e, s = frames(*chain("X", ["2026-01-02", "2026-01-05"], [1, 1], "2026-01-10", ["finance", "customs"]))
    evaluate_all_v4(e, s)
    assert (b3.CLOCK_LABELS, b3.CLOCK_ALIASES) == before
    assert b3.CLOCK_ALIASES["customs"] == "logistics"  # v3.4 registered alias unchanged


def test_institutional_binding_and_v34_contrast():
    # finance 1 day on time; customs expected 2 days but took 8 -> R at Jan 11, tW Jan 6
    e, s = frames(*chain("I1", ["2026-01-02", "2026-01-10", "2026-01-11"], [1, 2, 1], "2026-01-06",
                         ["finance", "customs", "operational-readiness"]))
    v4 = evaluate_all_v4(e, s).set_index("episode").loc["I1"]
    assert v4["verdict"] == "Institution-binding"
    v3 = evaluate_all(e, s[ST[:7]]).set_index("episode").loc["I1"]
    assert v3["verdict"] == "Logistics-binding"  # same step, v3.4 clock set
    sens = evaluate_all_v4(e, s, merge_institutional=True).set_index("episode").loc["I1"]
    assert sens["verdict"] == "Logistics-binding"


def test_revelation_sensitive():
    # origin proof revealed on Jan 8, finished Jan 10 (2 days after revelation); ready since Jan 3.
    # best case: corrected to 2 days -> R Jan 6 <= tW Jan 7 -> Institution-binding
    # worst case: untestable -> Indeterminate (missing ex-ante) -> different -> revelation-sensitive
    e, s = frames(*chain("V1", ["2026-01-02", "2026-01-03", "2026-01-10", "2026-01-11"], [1, 1, None, 1], "2026-01-07",
                         ["finance", "logistics", "institutional", "operational-readiness"],
                         status=[None, None, "revealed", None], revealed=[None, None, "2026-01-08", None],
                         act=[None, None, "2026-01-03", None]))
    r = evaluate_all_v4(e, s).set_index("episode").loc["V1"]
    assert r["verdict"] == "Indeterminate" and r["indeterminate_reason"] == "revelation-sensitive"
    assert "Institution-binding" in r["reason"] and r["revealed_steps"] == "s2"


def test_revealed_same_verdict_both_bounds():
    # finance late beyond any rescue by the revealed step: finance expected 1, took 9 -> finance binds in both cases
    e, s = frames(*chain("V2", ["2026-01-10", "2026-01-12", "2026-01-13"], [1, None, 1], "2026-01-05",
                         ["finance", "institutional", "operational-readiness"],
                         status=[None, "revealed", None], revealed=[None, "2026-01-11", None], act=[None, "2026-01-10", None]))
    r = evaluate_all_v4(e, s).set_index("episode").loc["V2"]
    assert r["revelation_bounds"].startswith("Same verdict")
    assert r["verdict"] == "Finance-binding"


def test_revealed_without_date_is_undocumented():
    e, s = frames(*chain("V3", ["2026-01-02", "2026-01-09"], [1, None], "2026-01-05", ["finance", "institutional"],
                         status=[None, "revealed"]))
    r = evaluate_all_v4(e, s).set_index("episode").loc["V3"]
    assert "rule 4.1" in r["flags"] and r["revealed_steps"] == ""


def test_claim_cap_internal_only():
    e, s = frames(*chain("C1", ["2026-01-09", "2026-01-10"], [1, 1], "2026-01-04", ["finance", "operational-readiness"],
                         src=["internal", "internal"]))
    r = evaluate_all_v4(e, s).set_index("episode").loc["C1"]
    assert r["verdict"] == "Finance-binding" and r["claim_cap"].startswith("consistent with")
    s.loc[0, "source_class"] = "third-party"
    r2 = evaluate_all_v4(e, s).set_index("episode").loc["C1"]
    assert r2["claim_cap"] == "not capped"


def test_alpha_perfect_and_reference():
    assert krippendorff_alpha_nominal([["a", "a"], ["b", "b"], ["c", "c"]]) == pytest.approx(1.0)
    # brute-force reference: alpha = 1 - (n-1) * sum_u D_u / sum_pairs-over-all-values D
    data = [["a", "a"], ["a", "b"], ["b", "b"], ["c", "b"], ["c", "c"], ["a", None]]
    units = [[v for v in u if v is not None] for u in data if sum(v is not None for v in u) >= 2]
    vals = [v for u in units for v in u]
    n = len(vals)
    within = sum(sum(x != y for x, y in itertools.permutations(u, 2)) / (len(u) - 1) for u in units)
    between = sum(x != y for x, y in itertools.permutations(vals, 2))
    ref = 1 - (n - 1) * within / between
    assert krippendorff_alpha_nominal(data) == pytest.approx(ref)


def test_blind_packet_removes_interpretations():
    sheets = {"Episodes": pd.DataFrame({"episode": ["E1", "E2"], "tw_earliest": ["2026-01-02"] * 2, "verdict": ["x", "y"], "note": ["a", "b"]}),
              "Steps": pd.DataFrame({"episode": ["E1", "E2"], "step": ["s", "s"], "clock": ["finance"] * 2, "Final level": [3, 2]}),
              "05_Level_Assessment": pd.DataFrame({"Episode ID": ["E1"], "Verdict": ["x"]})}
    packet, key, removed = blind_packet(sheets, seed=1)
    assert set(packet) == {"Episodes", "Steps"}
    assert "verdict" not in packet["Episodes"].columns and "note" not in packet["Episodes"].columns
    assert "final level" not in packet["Steps"].columns
    assert set(packet["Episodes"]["episode"]) <= {"P001", "P002"} and len(key) == 2
    assert packet["Episodes"]["episode"].tolist() != ["E1", "E2"]


def test_concordance_attribution():
    s1 = pd.DataFrame({"episode": ["A", "B"], "verdict": ["Logistics-binding", "Non-binding"], "binding_clocks": ["logistics", ""]})
    s2 = pd.DataFrame({"episode": ["A", "B"], "verdict": ["Institution-binding", "Non-binding"], "binding_clocks": ["institutional", ""]})
    tab, per = concordance(s1, s2)
    assert int(per["changed"].sum()) == 1
    assert per.set_index("episode").loc["A", "provisional attribution of the change"].startswith("institutional clock")


def test_layer_summary_validation():
    lay = pd.DataFrame({"episode": ["E1", "E1", "E1"], "layer": ["institutional", "environmental", "carrier"],
                        "state": ["Activated", "Exposed", "Activated"], "evidence": ["", "GSCPI p93", "x"]})
    tab, probs = layer_summary(lay)
    assert any("carrier" in p for p in probs) and any("Activated needs" in p for p in probs)
    assert int(tab.set_index("layer").loc["institutional", "Activated"]) == 1


def test_no_actionable_from_reports_worst_case():
    e, s = frames(*chain("V4", ["2026-01-02", "2026-01-03", "2026-01-10", "2026-01-11"], [1, 1, None, 1], "2026-01-07",
                         ["finance", "logistics", "institutional", "operational-readiness"],
                         status=[None, None, "revealed", None], revealed=[None, None, "2026-01-08", None]))
    r = evaluate_all_v4(e, s).set_index("episode").loc["V4"]
    assert r["revelation_bounds"].startswith("Best case not computable")
    assert r["verdict"] == "Indeterminate" and r["indeterminate_reason"] == "missing-inputs"
    assert "rule 5.2" in r["flags"]


def test_late_actionable_from_removes_rescue():
    # same as V1, but the action could only start on Jan 8 (e.g. the shipment had to exist first):
    # best case: start Jan 8 + 2 days -> Jan 10 -> R Jan 11 > tW Jan 7 -> no rescue -> both bounds non-attributable
    e, s = frames(*chain("V5", ["2026-01-02", "2026-01-03", "2026-01-10", "2026-01-11"], [1, 1, None, 1], "2026-01-07",
                         ["finance", "logistics", "institutional", "operational-readiness"],
                         status=[None, None, "revealed", None], revealed=[None, None, "2026-01-08", None],
                         act=[None, None, "2026-01-08", None]))
    r = evaluate_all_v4(e, s).set_index("episode").loc["V5"]
    assert r["verdict"] == "Indeterminate" and r["indeterminate_reason"] != "revelation-sensitive"
    assert r["revelation_bounds"].startswith("Same verdict")


def test_claim_cap_requires_direct_record():
    e, s = frames(*chain("C2", ["2026-01-09", "2026-01-10"], [1, 1], "2026-01-04", ["finance", "operational-readiness"],
                         src=["third-party", "internal"], direct=["No", None]))
    r = evaluate_all_v4(e, s).set_index("episode").loc["C2"]
    assert r["claim_cap"].startswith("consistent with")
    s.loc[0, "direct_record"] = "Yes"
    assert evaluate_all_v4(e, s).set_index("episode").loc["C2", "claim_cap"] == "not capped"
