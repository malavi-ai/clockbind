"""clockbind binding: counterfactual "which clock binds?" verdicts from episode timelines."""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pandas as pd

from ..binding import EPISODE_COLUMNS, STEP_COLUMNS, evaluate_all
from ..core.plugin import Plugin
from ..core.provenance import RunLog

GUIDE = [
    ("What this file is", "Timeline input for `clockbind binding run`. One row per episode in Episodes; one row per process step in Steps."),
    ("Episodes: anchor", "Time the process starts for steps without predecessors (usually the route decision tD). Earliest/latest bounds; latest may be blank if exact."),
    ("Episodes: tW", "End of the action window. Earliest/latest bounds."),
    ("Episodes: r_step", "Name of the step whose finish is the required event R (e.g. 'operational')."),
    ("Steps: clock", "finance, supplier, logistics, installation, or other."),
    ("Steps: predecessors", "Step names separated by ';'. Parallel steps are allowed (dependency network, not a chain)."),
    ("Steps: finish", "Documented finish time as an interval. Dates or date-times (YYYY-MM-DD or YYYY-MM-DD HH:MM). Blank = not documented."),
    ("Steps: expected_days", "Ex-ante expected duration in days (decimals allowed: 0.5 = 12 hours), from a document dated before the outcome. Blank = not documented."),
    ("Steps: source", "Document code (DOC-nnn). No names, amounts or file links."),
    ("Rule", "A clock binds if R would have occurred by tW had that clock met its ex-ante duration, other clocks as documented. "
             "Verdicts are computed at the earliest and at the latest bounds; if they differ the episode is Indeterminate."),
]


def _read(a):
    if a.data:
        x = pd.read_excel(a.data, sheet_name=None, dtype=object)
        low = {k.strip().lower(): v for k, v in x.items()}
        if "episodes" not in low or "steps" not in low:
            raise SystemExit("The workbook needs two sheets named 'Episodes' and 'Steps' (see `clockbind binding template`).")
        return low["episodes"], low["steps"]
    if a.episodes and a.steps:
        return pd.read_csv(a.episodes, dtype=object), pd.read_csv(a.steps, dtype=object)
    raise SystemExit("Give --data timeline.xlsx, or both --episodes and --steps CSV files.")


def cmd_run(a):
    ep, st = _read(a)
    res = evaluate_all(ep, st)
    with RunLog(a.out, "binding", "run", vars(a), None) as run:
        for p, lab in ((a.data, "timeline"), (a.episodes, "episodes"), (a.steps, "steps")):
            if p:
                run.add_input(p, lab)
        out = run.path("binding_verdicts.xlsx")
        summary = res["verdict"].value_counts().rename_axis("verdict").reset_index(name="episodes") if len(res) else pd.DataFrame(columns=["verdict", "episodes"])
        with pd.ExcelWriter(out, engine="openpyxl") as xw:
            res.to_excel(xw, sheet_name="Verdicts", index=False)
            summary.to_excel(xw, sheet_name="Summary", index=False)
            pd.DataFrame(GUIDE, columns=["item", "meaning"]).to_excel(xw, sheet_name="Rule", index=False)
        run.add_output(out)
        md = run.path("binding_summary.md")
        md.write_text(summary.to_markdown(index=False) + "\n", encoding="utf-8")
        run.add_output(md)
        from ..pdfreport import add_pdf
        cols = [c for c in ["episode", "verdict", "binding_clocks", "sign_stable", "finance_actionable", "reactive_sensitivity", "reason"] if c in res.columns]
        add_pdf(run, "binding_report.pdf", "Which clock binds?", [
            ("h", "Verdicts"), ("table", summary),
            ("h", "Per episode"), ("table", res[cols] if len(res) else None),
            ("h", "Registered rule"), ("table", pd.DataFrame(GUIDE, columns=["item", "meaning"]).iloc[-1:]),
            ("note", "Verdicts apply the registered rule. The researcher records them; any override needs a reason and a date.")],
            subtitle=Path(a.data).name if a.data else "", landscape_pages=True)
        run.note("episodes", int(len(res)))
        run.note("decision_required", int(res["flags"].str.contains("AUTHOR DECISION", na=False).sum()) if len(res) else 0)
        cols = ["episode", "verdict", "binding_clocks", "sign_stable", "finance_actionable"]
        print(res[cols].to_string(index=False) if len(res) else "No episodes found.")
    return 0


def cmd_template(a):
    ep = pd.DataFrame([{"episode": "EX-01", "anchor_earliest": "2026-01-05", "anchor_latest": "", "tw_earliest": "2026-01-14", "tw_latest": "",
                        "r_step": "operational", "note": "Synthetic example: delete before use"}], columns=EPISODE_COLUMNS)
    st = pd.DataFrame([
        {"episode": "EX-01", "step": "funds_usable", "clock": "finance", "predecessors": "", "finish_earliest": "2026-01-06", "finish_latest": "", "expected_days": 2, "source": "DOC-000"},
        {"episode": "EX-01", "step": "dispatch", "clock": "supplier", "predecessors": "funds_usable", "finish_earliest": "2026-01-08", "finish_latest": "", "expected_days": 2, "source": "DOC-000"},
        {"episode": "EX-01", "step": "delivered", "clock": "logistics", "predecessors": "dispatch", "finish_earliest": "2026-01-14", "finish_latest": "", "expected_days": 3, "source": "DOC-000"},
        {"episode": "EX-01", "step": "operational", "clock": "installation", "predecessors": "delivered", "finish_earliest": "2026-01-15", "finish_latest": "", "expected_days": 1, "source": "DOC-000"},
    ], columns=STEP_COLUMNS)
    with pd.ExcelWriter(a.output, engine="openpyxl") as xw:
        ep.to_excel(xw, sheet_name="Episodes", index=False)
        st.to_excel(xw, sheet_name="Steps", index=False)
        pd.DataFrame(GUIDE, columns=["item", "meaning"]).to_excel(xw, sheet_name="Guide", index=False)
    print(f"Template written: {a.output} ({_dt.date.today().isoformat()})")
    return 0


class Binding(Plugin):
    name = "binding"
    help = "Which clock binds? Counterfactual critical-path verdicts with the sign-stability rule"

    def register(self, sub):
        p = sub.add_parser("run", help="Verdict per episode: finance-binding, non-finance, jointly binding, non-binding or indeterminate")
        p.add_argument("--data", help="Timeline workbook with sheets Episodes and Steps")
        p.add_argument("--episodes", help="Episodes CSV (instead of --data)")
        p.add_argument("--steps", help="Steps CSV (instead of --data)")
        p.add_argument("--out", default="clockbind_runs")
        p.set_defaults(func=cmd_run)
        p = sub.add_parser("template", help="Write a timeline input template with a synthetic example")
        p.add_argument("--output", default="timeline_template.xlsx")
        p.set_defaults(func=cmd_template)


PLUGIN = Binding()
