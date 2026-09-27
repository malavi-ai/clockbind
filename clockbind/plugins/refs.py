"""Reference verification against Crossref/OpenAlex (wraps verify_references.py)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from ..core.plugin import Plugin
from ..core.provenance import RunLog
from ._common import add_common


def cmd_verify(a):
    script = Path(__file__).resolve().parent.parent / "verify_references.py"
    with RunLog(a.out, "refs", "verify", vars(a), None) as run:
        run.add_input(a.data, "references_csv")
        stem = run.path("reference_report")
        cmd = [sys.executable, str(script), a.data, "--mailto", a.mailto, "--out", str(stem)] + (["--strict"] if a.strict else [])
        r = subprocess.run(cmd)
        for f in run.dir.glob("reference_report*"):
            run.add_output(f)
        return r.returncode


class Refs(Plugin):
    name = "refs"
    help = "Verify a reference list (CSV) against Crossref and OpenAlex"

    def register(self, sub):
        p = add_common(sub.add_parser("verify", help="Check each reference exists and its metadata matches"))
        p.add_argument("--mailto", required=True, help="Your email (polite-pool requirement of Crossref/OpenAlex)")
        p.add_argument("--strict", action="store_true")
        p.set_defaults(func=cmd_verify)


PLUGIN = Refs()
