"""Known-answer tests for the counterfactual binding rule (hand-computed cases)."""
import pandas as pd
import pytest

from clockbind.binding import evaluate_all

EP_COLS = ["episode", "anchor_earliest", "anchor_latest", "tw_earliest", "tw_latest", "r_step"]


def run(episodes, steps):
    e = pd.DataFrame(episodes, columns=EP_COLS)
    s = pd.DataFrame(steps, columns=["episode", "step", "clock", "predecessors", "finish_earliest", "finish_latest", "expected_days"])
    return evaluate_all(e, s).set_index("episode")


def chain(eid, finishes, expected, tw, tw_hi=None, clocks=("finance", "supplier", "logistics", "installation")):
    names = ["funds", "dispatch", "delivered", "operational"]
    steps = []
    for i, n in enumerate(names):
        lo, hi = finishes[i] if isinstance(finishes[i], tuple) else (finishes[i], None)
        steps.append([eid, n, clocks[i], names[i - 1] if i else "", lo, hi, expected[i]])
    return [eid, "2026-01-01", None, tw, tw_hi, "operational"], steps


def test_design_note_illustration_transit_binds():
    # Anchor Jan 1, tW Jan 10; transit expected 3 days, took 6; everything else on time.
    e, s = chain("T1", ["2026-01-02", "2026-01-04", "2026-01-10", "2026-01-11"], [2, 2, 3, 1], "2026-01-11")
    e[3] = "2026-01-10"
    r = run([e], s).loc["T1"]
    assert r["verdict"] == "Non-finance: logistics"
    assert r["sign_stable"] == "Yes"
    assert r["finance_actionable"] == "Yes"
    assert r["decisive_slack_earliest_days"] == pytest.approx(2.0)  # corrected: delivered Jan 7, R Jan 8; tW Jan 10
    assert r["baseline_slack_earliest_days"] == pytest.approx(-1.0)


def test_non_binding_when_r_met():
    e, s = chain("T2", ["2026-01-02", "2026-01-04", "2026-01-07", "2026-01-08"], [2, 2, 3, 1], "2026-01-10")
    r = run([e], s).loc["T2"]
    assert r["verdict"] == "Non-binding" and r["decisive_slack_earliest_days"] == pytest.approx(2.0)


def test_finance_binding():
    # finance took 6 days (expected 1); everything else on time; tW missed by 3 days
    e, s = chain("T3", ["2026-01-07", "2026-01-09", "2026-01-12", "2026-01-13"], [1, 2, 3, 1], "2026-01-10")
    r = run([e], s).loc["T3"]
    assert r["verdict"] == "Finance-binding"
    assert r["finance_actionable"] == "No"


def test_jointly_binding_needs_both():
    # finance 3 days late and transit 3 days late; tW missed by 5: no single correction suffices, both do
    e, s = chain("T4", ["2026-01-05", "2026-01-07", "2026-01-13", "2026-01-14"], [1, 2, 3, 1], "2026-01-09")
    r = run([e], s).loc["T4"]
    assert r["verdict"] == "Jointly binding"
    assert r["binding_clocks"] == "finance + logistics"


def test_indeterminate_when_expected_duration_missing():
    e, s = chain("T5", ["2026-01-02", "2026-01-04", "2026-01-10", "2026-01-11"], [2, 2, None, 1], "2026-01-10")
    r = run([e], s).loc["T5"]
    assert r["verdict"] == "Indeterminate"
    assert "logistics" in r["reason"]


def test_indeterminate_when_date_not_documented():
    e, s = chain("T6", ["2026-01-02", None, "2026-01-10", "2026-01-11"], [2, 2, 3, 1], "2026-01-10")
    r = run([e], s).loc["T6"]
    assert r["verdict"] == "Indeterminate" and "dispatch" in r["reason"]


def test_sign_stability_rule():
    # R finishes Jan 10 or Jan 11 (interval); tW Jan 10 -> non-binding at earliest, logistics-binding at latest
    e, s = chain("T7", ["2026-01-02", "2026-01-04", "2026-01-09", ("2026-01-10", "2026-01-11")], [2, 2, 3, 1], "2026-01-10")
    r = run([e], s).loc["T7"]
    assert r["sign_stable"] == "No" and r["verdict"] == "Indeterminate"
    assert "sign-stability" in r["reason"]


def test_window_infeasible_is_flagged_for_author():
    # even at expected durations (1+2+3+1 = 7 days) R cannot be met by day 5
    e, s = chain("T8", ["2026-01-02", "2026-01-04", "2026-01-07", "2026-01-08"], [1, 2, 3, 1], "2026-01-05")
    r = run([e], s).loc["T8"]
    assert r["verdict"] == "Window infeasible at ex-ante durations"
    assert r["workbook_verdict"] == "" and "AUTHOR DECISION" in r["flags"]


def test_parallel_network_only_critical_branch_binds():
    # finance and supplier run in parallel from the anchor; delivery needs both.
    steps = [["P1", "funds", "finance", "", "2026-01-03", None, 1],       # 2 days late, but off the critical path
             ["P1", "made", "supplier", "", "2026-01-08", None, 3],       # 4 days late
             ["P1", "delivered", "logistics", "funds;made", "2026-01-10", None, 2],
             ["P1", "operational", "installation", "delivered", "2026-01-11", None, 1]]
    r = run([["P1", "2026-01-01", None, "2026-01-08", None, "operational"]], steps).loc["P1"]
    assert r["verdict"] == "Non-finance: supplier"
    assert r["finance_actionable"] == "Yes"


def test_cycle_and_unknown_predecessor_are_reported():
    steps = [["C1", "a", "finance", "b", "2026-01-02", None, 1], ["C1", "b", "supplier", "a", "2026-01-03", None, 1]]
    r = run([["C1", "2026-01-01", None, "2026-01-05", None, "b"]], steps).loc["C1"]
    assert r["verdict"] == "Indeterminate" and "cycle" in r["reason"]


def test_input_safeguards_dates_duplicates_orphans_timezones():
    import pandas as pd
    from clockbind.binding import _days, evaluate_all
    import pytest as _pt
    # European day-first dates, Hungarian year-first dates and Excel serials are read correctly
    assert _days("03.02.2026") == _days("2026-02-03") == _days("2026. 02. 03.") == _days(46056)
    with _pt.raises(ValueError, match="ambiguous"):
        _days("02/03/2026")
    with _pt.raises(ValueError):
        _days(5)
    ep = pd.DataFrame([{"episode": "A", "anchor_earliest": "2026-01-01", "tw_earliest": "2026-01-10", "r_step": "x"},
                       {"episode": "A", "anchor_earliest": "2026-01-01", "tw_earliest": "2026-01-10", "r_step": "x"},
                       {"episode": "B", "anchor_earliest": "2026-01-01 08:00+01:00", "tw_earliest": "2026-01-10 08:00", "r_step": "x"}])
    st = pd.DataFrame([{"episode": e, "step": "x", "clock": "finance", "predecessors": "", "finish_earliest": "2026-01-05", "expected_days": 1}
                       for e in ("A", "B", "C")])
    r = evaluate_all(ep, st).set_index("episode")
    assert "more than once" in r.loc["A"].iloc[0]["flags"]
    assert "time-zone" in r.loc["B", "flags"] and r.loc["B", "verdict"] == "Indeterminate"
    assert r.loc["C", "reason"] == "listed in Steps but has no row in Episodes"
    with _pt.raises(ValueError, match="missing column"):
        evaluate_all(ep.drop(columns=["tw_earliest"]), st)
