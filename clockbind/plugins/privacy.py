"""clockbind privacy scan: check a data file for personal data before analysis (GDPR / KVKK aid)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..core.plugin import Plugin
from ..privacy import ADVICE, scan_dataframe


def _read(path: str) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() in (".xlsx", ".xlsm", ".xls"):
        return pd.read_excel(p, dtype=str)
    if p.suffix.lower() == ".sav":
        import pyreadstat
        df, _ = pyreadstat.read_sav(str(p))
        return df
    return pd.read_csv(p, dtype=str, keep_default_na=False)


def cmd_scan(a):
    f = scan_dataframe(_read(a.data))
    if not f:
        print("No personal-data patterns found. (This does not prove the file is anonymous.)")
        return 0
    print(ADVICE)
    for x in f:
        print(f"  - column '{x['column']}': {x['kind']} ({x['count']} cells)")
    return 3 if a.strict else 0


class Privacy(Plugin):
    name = "privacy"
    help = "Check a data file for personal data before analysis (values are never shown)"

    def register(self, sub):
        p = sub.add_parser("scan", help="Scan a CSV/Excel/SPSS file for names, e-mails, phone numbers, IBANs, ID numbers")
        p.add_argument("--data", required=True)
        p.add_argument("--strict", action="store_true", help="exit with code 3 if anything is found")
        p.set_defaults(func=cmd_scan)


PLUGIN = Privacy()
