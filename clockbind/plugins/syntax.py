"""Run analyses from a syntax file (the same JSON the Studio exports), and list analyses."""
from __future__ import annotations

import json
from pathlib import Path

from ..core.io import load_data
from ..core.plugin import Plugin
from ..core.provenance import RunLog


def cmd_list(a):
    from ..analysis import REGISTRY
    groups = {}
    for k, v in REGISTRY.items():
        groups.setdefault(v["group"], []).append((k, v["title"]))
    for gname, items in groups.items():
        print(f"\n{gname}")
        for k, t in items:
            print(f"  {k:26s} {t}")


def cmd_run(a):
    from ..analysis import outputs_to_docx, run
    spec = json.loads(Path(a.syntax).read_text(encoding="utf-8"))
    steps = spec["steps"] if isinstance(spec, dict) else spec
    df = load_data(a.data)
    with RunLog(a.out, "syntax", "run", vars(a), None) as log:
        log.add_input(a.data); log.add_input(a.syntax, "syntax")
        outs = []
        for st in steps:
            o = run(st["analysis"], df, st.get("params", {}))
            outs.append(o)
            print(f"ran {st['analysis']}")
        doc = outputs_to_docx(outs, log.path("output.docx"), title=f"ClockBind output — {Path(a.data).name}")
        log.add_output(doc)
        log.note("steps", [o.syntax for o in outs])
        print(f"Word output: {doc}")


class Syntax(Plugin):
    name = "syntax"
    help = "Run analyses from a syntax file exported by ClockBind Studio; list available analyses"

    def register(self, sub):
        p = sub.add_parser("list", help="List all analyses"); p.set_defaults(func=cmd_list)
        p = sub.add_parser("run", help="Re-run a syntax file on a data file; writes Word output + manifest")
        p.add_argument("--data", required=True); p.add_argument("--syntax", required=True); p.add_argument("--out", default="clockbind_runs")
        p.set_defaults(func=cmd_run)


PLUGIN = Syntax()
