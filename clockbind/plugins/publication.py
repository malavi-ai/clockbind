"""Publication/preregistration CLI."""
from __future__ import annotations
import json
from pathlib import Path
from ..core.plugin import Plugin
from ..publication import build_prereg_bundle, consistency_audit, build_submission_bundle


def cmd_prereg(a):
    if a.status.upper()=="FROZEN" and not a.confirm:
        raise ValueError("A FROZEN snapshot requires --confirm. This still does not register anything externally.")
    p=build_prereg_bundle(a.manifest or None,a.file or [],a.output,a.status,a.frozen_by or "",a.note or "")
    print(f"Preregistration snapshot: {p}")
    print("External registry status: NOT REGISTERED BY CLOCKBIND")


def cmd_audit(a):
    rows,s=consistency_audit(a.manuscript,a.registry)
    print(json.dumps(s,indent=2))
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True); p=out/"manuscript_consistency_audit.json"
    p.write_text(json.dumps({"summary":s,"checks":rows},indent=2),encoding="utf-8"); print(f"Local report: {p}")
    return 1 if s["fail"] else 0


def cmd_bundle(a):
    p=build_submission_bundle(a.manuscript,a.artifact or [],a.output); print(f"Submission bundle: {p}")


class Publication(Plugin):
    name="publication"; help="Preregistration snapshots, manuscript-output consistency checks and submission bundles"
    def register(self,sub):
        p=sub.add_parser("prereg",help="Create a draft/frozen local preregistration snapshot with hashes")
        p.add_argument("--manifest"); p.add_argument("--file",action="append",default=[]); p.add_argument("--output",required=True)
        p.add_argument("--status",choices=["DRAFT","FROZEN"],default="DRAFT"); p.add_argument("--frozen-by"); p.add_argument("--note"); p.add_argument("--confirm",action="store_true"); p.set_defaults(func=cmd_prereg)
        p=sub.add_parser("audit",help="Check manuscript text against an explicit result/claim registry")
        p.add_argument("--manuscript",required=True); p.add_argument("--registry",required=True); p.add_argument("--out",default="clockbind_runs"); p.set_defaults(func=cmd_audit)
        p=sub.add_parser("bundle",help="Create a hashed submission bundle")
        p.add_argument("--manuscript",required=True); p.add_argument("--artifact",action="append",default=[]); p.add_argument("--output",required=True); p.set_defaults(func=cmd_bundle)

PLUGIN=Publication()
