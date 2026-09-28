"""Regenerate the Python expectations for the JavaScript parity cases (webapp/parity/cases.json).

Rows and protocols of the stored cases are kept; the expected output is recomputed with the Python engine.
Optionally add a case from a workbook:  python make_cases.py --add NAME workbook.xlsx gates.json SHEET HEADER_ROW
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from clockbind.plugins.screen import apply_gates, funnel, gates_hash, load_data_sheet  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--add", nargs=5, metavar=("NAME", "WORKBOOK", "GATES", "SHEET", "HEADER_ROW"), action="append", default=[])
    a = ap.parse_args()
    cases = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
    for name, wb, gates, sheet, hr in a.add:
        g = json.loads(Path(gates).read_text(encoding="utf-8"))
        df = load_data_sheet(wb, sheet, int(hr))
        rows = df.fillna("").astype(str).to_dict("records")
        cases = [c for c in cases if c["name"] != name] + [{"name": name, "gates": g, "rows": rows}]
    for c in cases:
        g = c["gates"]
        c["hash"] = gates_hash(g)
        df = pd.DataFrame(c["rows"]).fillna("").astype(str)
        try:
            entries, eps, probs = apply_gates(df, g)
        except SystemExit as e:
            c["expect"] = {"stop": str(e)}
            continue
        f = funnel(entries, eps, g)
        epc = g["episode_column"]
        c["expect"] = {"episodes": {str(r[epc]): [r["final_status"], r.get("level", "") or ""] for _, r in eps.iterrows()},
                       "problems": sorted(f"{p['level']}|{p['where']}|{p['problem']}" for _, p in probs.iterrows()),
                       "funnel": sorted(f"{r['kind']}|{r['count']}|{r['n']}" for _, r in f.iterrows())}
    (HERE / "cases.json").write_text(json.dumps(cases, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"{len(cases)} cases written")


if __name__ == "__main__":
    main()
