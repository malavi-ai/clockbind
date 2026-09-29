"""clockbind export: privacy-preserving research handoff packages."""
from __future__ import annotations

from pathlib import Path

from ..core.plugin import Plugin
from ..safe_export import safe_payload, write_safe_zip


def cmd_ai_safe(a):
    out = write_safe_zip(a.workbook, a.gates, a.output)
    p = safe_payload(a.workbook, a.gates)
    b = p["bridge"]
    s = b["sources"]
    print(
        f"AI-safe export written: {out}\n"
        f"{s.get('total', 0)} sources · {b.get('episodes', 0)} episodes · "
        f"{b.get('workbook_checks', {}).get('fail', 0)} workbook FAIL · protocol frozen={p['protocol']['frozen']}\n"
        "No workbook cell values, document text, personal-data values or input paths are included."
    )
    return 0


class Export(Plugin):
    name = "export"
    help = "Create privacy-preserving research exports for AI review or controlled handoff"

    def register(self, sub):
        p = sub.add_parser("ai-safe", help="Create an aggregate Bridge export with hashes but no raw study data")
        p.add_argument("--workbook", required=True, help="Bridge workbook (.xlsx/.xlsm)")
        p.add_argument("--gates", required=True, help="Protocol/gates JSON")
        p.add_argument("--output", default="Bridge_AI_Safe_Export.zip", help="Output zip")
        p.set_defaults(func=cmd_ai_safe)


PLUGIN = Export()
