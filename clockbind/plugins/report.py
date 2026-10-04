"""clockbind report: one command that produces every output (PDF, Excel, Word, CSV, charts, bundle)."""
from __future__ import annotations

from pathlib import Path

from ..core.plugin import Plugin
from ..core.provenance import RunLog

DEFAULT_GATES = Path(__file__).resolve().parents[1] / "data" / "gates_v3.4_DRAFT.json"


def cmd_full(a):
    from ..fullreport import build
    gates = a.gates or str(DEFAULT_GATES)
    with RunLog(a.out, "report", "full", vars(a), None) as run:
        run.add_input(a.data)
        run.add_input(gates, "gates")
        r = build(a.data, gates, str(run.path("")), sheet=a.sheet, header_row=a.header_row, chat_safe=a.chat_safe, title=a.title, run=run, relative_time=getattr(a, "relative_time", False))
        print(r["summary"])
        print("\nFiles:")
        for k in ("pdf", "xlsx", "docx", "md", "bundle"):
            print(f"  {k:6} {r[k]}")
    return 0


class Report(Plugin):
    name = "report"
    help = "Full report: PDF + Excel + Word + CSV + charts + zip bundle, in one command"

    def register(self, sub):
        f = sub.add_parser("full", help="Everything from a Bridge master workbook: integrity, pipeline, gates, claim ladder, binding, agreement")
        f.add_argument("--data", required=True, help="Bridge master workbook (.xlsx)")
        f.add_argument("--gates", default="", help="Gates JSON (default: the bundled v3.4 gates)")
        f.add_argument("--sheet", default="05_Level_Assessment")
        f.add_argument("--header-row", type=int, default=2, help="0-based header row of the assessment sheet (default 2 = Excel row 3)")
        f.add_argument("--chat-safe", action="store_true", help="Aggregate only: no episode codes, no per-episode rows (use for anything shared or shown in chat)")
        f.add_argument("--relative-time", action="store_true", help="Timelines in days from the anchor instead of calendar dates (for publication)")
        f.add_argument("--title", default="Bridge — full report")
        f.add_argument("--out", default="clockbind_runs")
        f.set_defaults(func=cmd_full)


PLUGIN = Report()
