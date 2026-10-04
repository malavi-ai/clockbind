"""Stress test: 30 random synthetic Bridge workbooks through the full report (FULL, chat-safe, relative time).

Each scenario checks that every output is written, the counts are internally consistent, claim tiers follow the
frozen engine where 05 has no verdict, the ladders match hand counts, and chat-safe outputs carry no episode code."""
import json
import random
import subprocess
from pathlib import Path

import pandas as pd
import pytest

openpyxl = pytest.importorskip("openpyxl")

GATES = Path(__file__).resolve().parents[1] / "clockbind" / "data" / "gates_v3.4_DRAFT.json"
CLOCKS = ["finance", "payment", "fulfilment", "logistics", "operational-readiness"]


def _gates(tmp):
    from clockbind.descriptive import DEFAULT_FIELDS, DEFAULT_LADDER
    g = json.loads(GATES.read_text(encoding="utf-8"))
    g["descriptive_fields"] = DEFAULT_FIELDS
    g["temporal_ladder"] = [{"id": i, "label": l} for i, l in DEFAULT_LADDER]
    p = tmp / "gates.json"
    p.write_text(json.dumps(g, ensure_ascii=False), encoding="utf-8")
    return g, p


def _value(rng, c, yes=0.75):
    if c["id"] == "S0p1":
        return rng.choice(["COMPLETE"] * 9 + ["PENDING"])
    if c["id"] == "S0p2":
        return rng.choice(["Yes"] * 9 + ["PENDING"])
    if c.get("allowed") and c["id"] in ("L1f", "L1g"):
        return rng.choice(c["allowed"])
    if c["id"].startswith("S0"):
        return rng.choice(["Yes"] * 12 + ["No"])
    u = rng.random()
    return "Yes" if u < yes else ("No" if u < yes + (1 - yes) * 0.7 else "PENDING")


def _scenario(seed, tmp):
    from clockbind.descriptive import DEFAULT_FIELDS
    from clockbind.plugins.screen import apply_gates
    rng = random.Random(seed)
    g, gp = _gates(tmp)
    crit = [c for s in g["stages"] for c in s["criteria"]]
    n = rng.randint(6, 30)
    yes = rng.uniform(0.80, 0.985)
    codes = [f"E{i:02d}" + (rng.choice(["", "", "a"])) for i in range(1, n + 1)]
    desc = [f["column"] for f in DEFAULT_FIELDS]
    cols = ["Episode ID", "Source code"] + [c["column"] for c in crit] + ["Verdict", "Sign-stable?", "Supplier-delay rival", "Window tier (A/B/C)", "Window setter"] + desc
    rows = []
    for e in codes:
        r = [e, f"S{rng.randint(1, 9):02d}"] + [_value(rng, c, yes) for c in crit] + ["", "", rng.choice(["Rejected", "Not rejected", ""]), rng.choice("AB"), rng.choice(["Buyer", "Seller", "Third party"])]
        for f in DEFAULT_FIELDS:
            r.append(rng.choice(f["allowed"] + ["", "nonsense"] if rng.random() < .15 else f["allowed"] + [""]))
        rows.append(r)
    df = pd.DataFrame(rows, columns=cols)
    _, eps, _ = apply_gates(df.copy(), g)
    l3 = [str(x) for x in eps.loc[eps["level"] == "Level 3", "Episode ID"]]
    E, S = [], []
    for e in l3:
        k = rng.randint(2, 5)
        t = pd.Timestamp("2025-03-01") + pd.Timedelta(days=rng.randint(0, 200))
        prev, names = "", []
        for j in range(k):
            t = t + pd.Timedelta(days=rng.choice([0.5, 1, 2, 3, 5, 8]))
            hi = (t + pd.Timedelta(days=rng.choice([1, 2]))) if rng.random() < .3 else None
            exp = rng.choice([0, 1, 2, 3, 5, None]) if rng.random() < .9 else None
            nm = f"s{j}"
            S.append({"episode": e, "step": nm, "clock": rng.choice(CLOCKS), "predecessors": prev, "finish_earliest": t.date().isoformat(),
                      "finish_latest": hi.date().isoformat() if hi is not None else "", "expected_days": exp,
                      "zero_documented": rng.choice(["Yes", "", "No"]) if exp == 0 else "", "source": "D", "note": ""})
            prev, names = nm, names + [nm]
        tw = t + pd.Timedelta(days=rng.choice([-6, -3, -1, 0, 1, 4]))
        E.append({"episode": e, "anchor_earliest": "2025-03-01", "anchor_latest": "", "tw_earliest": tw.date().isoformat(), "tw_latest": "", "r_step": names[-1], "note": ""})
    wb = tmp / "w.xlsx"
    with pd.ExcelWriter(wb, engine="openpyxl") as xw:
        pd.DataFrame([["title"], ["sub"]]).to_excel(xw, sheet_name="05_Level_Assessment", header=False, index=False)
        df.to_excel(xw, sheet_name="05_Level_Assessment", startrow=2, index=False)
        pd.DataFrame(E, columns=["episode", "anchor_earliest", "anchor_latest", "tw_earliest", "tw_latest", "r_step", "note"]).to_excel(xw, sheet_name="Episodes", index=False)
        pd.DataFrame(S, columns=["episode", "step", "clock", "predecessors", "finish_earliest", "finish_latest", "expected_days", "zero_documented", "source", "note"]).to_excel(xw, sheet_name="Steps", index=False)
    return wb, gp, codes, eps


@pytest.mark.parametrize("seed", range(30))
def test_report_stress(seed, tmp_path):
    from clockbind.fullreport import build
    wb, gp, codes, eps = _scenario(seed, tmp_path)
    full = build(str(wb), str(gp), str(tmp_path / "full"), relative_time=bool(seed % 2))
    safe = build(str(wb), str(gp), str(tmp_path / "safe"), chat_safe=True)
    for r in (full, safe):
        for k in ("pdf", "xlsx", "docx", "md", "bundle"):
            assert Path(r[k]).exists() and Path(r[k]).stat().st_size > 0
    t = full["tables"]
    # levels add up to the screened episodes
    assert int(t["04_Levels"]["episodes"].sum()) == len(eps)
    # temporal ladder equals hand counts among analysable episodes
    an = eps[~eps["level"].astype(str).str.startswith(("Outside", "Held"))]
    g = json.loads(Path(gp).read_text())
    col = {c["id"]: c["column"] for s in g["stages"] for c in s["criteria"]}
    lad = t["05_Temporal_ladder"].set_index("step")["Yes"]
    for cid in ("L1d", "L3b", "L3c"):
        hand = int(an[col[cid]].astype(str).isin(["Yes", "COMPLETE"]).sum())
        assert lad[[i for i in lad.index if i.startswith(cid)][0]] == hand
    # claim tiers follow the engine where 05 has no verdict
    res = t.get("07_Binding_per_episode")
    cl = t["06_Claims_per_episode"]
    if res is not None and len(res):
        eng = res.set_index("episode")
        for _, r in cl[cl["level"] == "Level 3"].iterrows():
            assert r["verdict source"] == "engine" and r["verdict"] == eng.loc[r["episode"], "verdict"]
            if r["verdict"] == "Indeterminate":
                assert r["claim tier"] == "X"
            if r["verdict"] == "Non-binding":
                assert r["claim tier"] in ("A¬", "B¬", "C¬", "PENDING")      # never a positive tier
            if r["claim tier"] in ("A", "B", "C"):
                assert r["verdict"] not in ("Non-binding", "Indeterminate")
        fb = int((res["verdict"] == "Finance-binding").sum())
        assert int(t["07_Finance_ladder"].set_index("level of the financing claim").filter(like="Counterfactually", axis=0)["episodes"].iloc[0]) == fb
        assert set(res["indeterminate_reason"].fillna("")) <= {"", "window-infeasible", "multiple-sufficient", "sign-unstable", "missing-inputs"}
    # chat-safe: manifest present and no episode code anywhere (tables, markdown, PDF text)
    out = tmp_path / "safe"
    assert (out / "SAFE_TO_SHARE.txt").exists()
    text = "".join(p.read_text(errors="ignore") for p in (out / "tables").glob("*.csv")) + safe["summary"]
    try:
        text += subprocess.run(["pdftotext", str(safe["pdf"]), "-"], capture_output=True, text=True, timeout=60).stdout
    except FileNotFoundError:
        pass
    import re
    for c in codes:
        assert not re.search(rf"(?<![A-Za-z0-9]){re.escape(c)}(?![A-Za-z0-9])", text), f"{c} leaked in chat-safe output"
