"""clockbind lock: data dictionary, lock-readiness check and the gated data lock."""
from __future__ import annotations

from pathlib import Path

from ..core.plugin import Plugin


def cmd_dictionary(a):
    from ..lock import data_dictionary
    dd = data_dictionary(a.data, a.gates or None)
    out = Path(a.output)
    if out.suffix.lower() == ".csv":
        dd.to_csv(out, index=False)
    else:
        import pandas as pd
        with pd.ExcelWriter(out, engine="openpyxl") as xw:
            dd.to_excel(xw, sheet_name="Data_Dictionary", index=False)
    print(f"{len(dd)} fields in {dd['sheet'].nunique()} sheets → {out}")
    return 0


def _run(a, dry):
    from ..lock import run_lock
    r = run_lock(a.data, a.gates, a.by, a.out, sheet=a.sheet, header_row=a.header_row, notes_path=a.warnings_note or None,
                 amendment=a.amendment, dry_run=dry, extra_files=a.include or [])
    if r["locked"]:
        print(f"LOCKED: {r['lock_id']}\nLock hash: {r['lock_hash']}\nPackage (read-only): {r['package']}")
        print("Register the lock hash externally today (OSF hash-only note or email to the supervisor).")
        return 0
    print(Path(r["readiness"]).read_text(encoding="utf-8"))
    print(("NOT LOCKED — fix the blockers above." if r["blockers"] else "Ready: no blockers. Run `clockbind lock run` to lock.")
          + f"\nReadiness report: {r['readiness']}")
    return 2 if r["blockers"] else 0


def cmd_verify(a):
    from ..lock import verify
    ok, probs = verify(a.package)
    print("VERIFIED: every file matches the lock manifest." if ok else "NOT VERIFIED:\n" + "\n".join(f"  - {p}" for p in probs))
    return 0 if ok else 2


class Lock(Plugin):
    name = "lock"
    help = "Data dictionary, lock-readiness check and gated data lock with SHA-256 manifest"

    def register(self, sub):
        p = sub.add_parser("dictionary", help="Data dictionary of every sheet and column (input/calculated, allowed values, meaning)")
        p.add_argument("--data", required=True)
        p.add_argument("--gates", default="")
        p.add_argument("--output", default="Data_Dictionary.xlsx")
        p.set_defaults(func=cmd_dictionary)
        v = sub.add_parser("verify", help="Re-hash a lock package and compare with its manifest")
        v.add_argument("package", help="Path to a LOCK_<timestamp> folder")
        v.set_defaults(func=cmd_verify)
        for name, dry, h in (("check", True, "Lock-readiness check only (nothing is locked)"),
                             ("run", False, "Lock the data if, and only if, there are no blockers")):
            q = sub.add_parser(name, help=h)
            q.add_argument("--data", required=True, help="Bridge master workbook")
            q.add_argument("--gates", required=True, help="FROZEN gates JSON (FREEZE_REGISTER.jsonl next to it)")
            q.add_argument("--by", required=True, help="Initials of the person locking")
            q.add_argument("--out", default="Bridge_Lock", help="Lock folder (holds LOCK_REGISTER.csv and lock packages)")
            q.add_argument("--sheet", default="05_Level_Assessment")
            q.add_argument("--header-row", type=int, default=2)
            q.add_argument("--warnings-note", default="", help="CSV with columns check,justification for every remaining warning")
            q.add_argument("--amendment", default="", help="Required for any lock after the first: the reason")
            q.add_argument("--include", nargs="*", help="Extra files to seal in the package (e.g. Codebook, OSF plan)")
            q.set_defaults(func=(lambda a, d=dry: _run(a, d)))


PLUGIN = Lock()
