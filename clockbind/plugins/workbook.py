"""clockbind workbook check: integrity of a screening workbook before analysis or freeze."""
from __future__ import annotations

from ..core.plugin import Plugin
from ..core.provenance import RunLog
from ..workbook_check import check_workbook


def cmd_check(a):
    from pathlib import Path
    p = Path(a.data)
    if not p.exists():
        print(f"File not found: {p}")
        return 1
    if p.suffix.lower() not in (".xlsx", ".xlsm"):
        print(f"The workbook check reads Excel workbooks (.xlsx). This file is {p.suffix or 'without an extension'}. "
              "For a CSV file use:  clockbind privacy scan --data <file>")
        return 1
    try:
        rep = check_workbook(a.data)
    except Exception as e:  # damaged or password-protected files
        print(f"The file could not be opened as an Excel workbook ({type(e).__name__}: {e}). "
              "Open it in Excel, save it again as .xlsx, and retry.")
        return 1
    df = rep.frame()
    with RunLog(a.out, "workbook", "check", vars(a), None) as run:
        run.add_input(a.data)
        out = run.path("workbook_check.xlsx")
        df.to_excel(out, index=False)
        run.add_output(out)
        from ..pdfreport import add_pdf
        from pathlib import Path as _P
        issues = df[df["level"].isin(["FAIL", "WARN"])]
        add_pdf(run, "workbook_check.pdf", "Workbook integrity check", [
            ("h", "Summary"),
            ("kv", [("FAIL", rep.count("FAIL")), ("WARN", rep.count("WARN")), ("PASS", rep.count("PASS"))]),
            ("h", "Problems to fix"), ("table", issues if len(issues) else None, "Locations only; cell contents are never shown."),
            ("h", "All checks"), ("table", df)], subtitle=_P(a.data).name)
        run.note("fail", rep.count("FAIL"))
        run.note("warn", rep.count("WARN"))
    show = df if a.verbose else df[(df["level"] != "INFO") | df["check"].str.contains("skipped", na=False)]
    print(show.to_string(index=False) if len(show) else "Nothing to report.")
    print(f"\n{rep.count('FAIL')} FAIL, {rep.count('WARN')} WARN, {rep.count('PASS')} PASS")
    return 2 if rep.count("FAIL") and a.strict else 0


class Workbook(Plugin):
    name = "workbook"
    help = "Integrity check of a screening workbook: formulas, dropdowns, cross-sheet links, overrides, privacy"

    def register(self, sub):
        p = sub.add_parser("check", help="Check formulas, dropdown entries, episode/source links, override logs and personal data")
        p.add_argument("--data", required=True, help="Workbook (.xlsx)")
        p.add_argument("--out", default="clockbind_runs")
        p.add_argument("--verbose", action="store_true", help="also list INFO lines")
        p.add_argument("--strict", action="store_true", help="exit with code 2 if any check fails")
        p.set_defaults(func=cmd_check)


PLUGIN = Workbook()
