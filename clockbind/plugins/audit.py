"""clockbind audit docs: check documents for personal data and outdated wording, on this computer only."""
from __future__ import annotations

from ..core.plugin import Plugin
from ..core.provenance import RunLog


def cmd_docs(a):
    from pathlib import Path

    import pandas as pd

    from ..docaudit import audit, load_names, load_terms
    from ..resources import resource

    src = Path(a.data).expanduser()
    if not src.exists():
        print(f"Not found: {src}")
        return 1
    terms_path = None if a.no_terms else (a.terms or str(resource("bridge_terms_2026-09-28.json")))
    terms = load_terms(terms_path)
    names = load_names(a.names)
    findings, summary, skipped = audit(str(src), terms, names)
    fdf = pd.DataFrame(findings, columns=["file", "location", "check", "finding", "count", "severity", "current wording / action", "matched"])
    sdf = pd.DataFrame(summary, columns=["file", "text units read", "personal-data findings", "outdated-wording findings", "status"])
    kdf = pd.DataFrame(skipped, columns=["file", "reason"])
    with RunLog(a.out, "audit", "docs", {k: v for k, v in vars(a).items() if k != "names"}, None) as run:
        if src.is_file():
            run.add_input(str(src))
        x = run.path("document_audit.xlsx")
        with pd.ExcelWriter(x) as w:
            sdf.to_excel(w, sheet_name="Files", index=False)
            fdf.to_excel(w, sheet_name="Findings", index=False)
            kdf.to_excel(w, sheet_name="Not read", index=False)
        run.add_output(x)
        from ..pdfreport import add_pdf
        add_pdf(run, "document_audit.pdf", "Document audit", [
            ("h", "Summary"),
            ("kv", [("Files read", len(sdf)), ("Files with personal or confidential data", int((sdf["personal-data findings"] > 0).sum())),
                    ("Files with outdated wording", int((sdf["outdated-wording findings"] > 0).sum())), ("Files not read", len(kdf)),
                    ("Wording rules", terms.get("name", "(none)")), ("Name list used", "yes" if names else "no")]),
            ("note", "Personal-data findings show the kind and location only; values are never shown. A clean result does not prove a document is anonymous."),
            ("h", "Files"), ("table", sdf if len(sdf) else None),
            ("h", "Findings"), ("table", fdf.drop(columns=["matched"]) if len(fdf) else None),
            ("h", "Not read"), ("table", kdf if len(kdf) else None)], subtitle=src.name, landscape_pages=True)
        run.note("files", len(sdf))
        run.note("personal_data_files", int((sdf["personal-data findings"] > 0).sum()) if len(sdf) else 0)
    n_pd = int((sdf["personal-data findings"] > 0).sum()) if len(sdf) else 0
    n_tw = int((sdf["outdated-wording findings"] > 0).sum()) if len(sdf) else 0
    safe_summary = {
        "files_read": len(sdf),
        "files_with_personal_or_confidential_data": n_pd,
        "files_with_outdated_wording": n_tw,
        "files_not_read": len(kdf),
    }
    if a.summary_json:
        import json
        Path(a.summary_json).expanduser().write_text(json.dumps(safe_summary, indent=2), encoding="utf-8")
    # Safe-by-default console output: do not print file names/paths unless explicitly requested.
    if a.list_files:
        print(sdf.to_string(index=False) if len(sdf) else "No readable files found.")
        if len(kdf):
            print("\nNot read:")
            print(kdf.to_string(index=False))
        print()
    print(f"{len(sdf)} files read · {n_pd} with personal or confidential data · {n_tw} with outdated wording · {len(kdf)} not read")
    print("Values are never shown. Local details: document_audit.xlsx / .pdf in the run folder.")
    return 3 if a.strict and (n_pd or n_tw) else 0


class Audit(Plugin):
    name = "audit"
    help = "Check documents (Word, PDF, Excel, CSV, text, zip, folders) for personal data and outdated wording, locally"

    def register(self, sub):
        p = sub.add_parser("docs", help="Audit a file, a folder or a zip (e.g. a Google Drive download)")
        p.add_argument("--data", required=True, help="File, folder or .zip")
        p.add_argument("--names", help="Optional local text file with one name per line (customers, people) to look for; never copied into the report")
        p.add_argument("--terms", help="Wording rules (JSON). Default: the Bridge current-position rules of 28 Sep 2026")
        p.add_argument("--no-terms", action="store_true", help="check personal data only")
        p.add_argument("--out", default="clockbind_runs")
        p.add_argument("--summary-json", help="write a safe aggregate JSON summary (no file names or detected values)")
        p.add_argument("--list-files", action="store_true", help="also print per-file names/statuses to the terminal (local use only)")
        p.add_argument("--strict", action="store_true", help="exit with code 3 if anything is found")
        p.set_defaults(func=cmd_docs)


PLUGIN = Audit()
