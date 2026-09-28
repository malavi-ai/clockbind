"""Project status for the Studio home screen and reports: where the Bridge workbook stands.

Everything is read locally. Only counts and check results are computed; cell contents are not kept.
"""
from __future__ import annotations

import json
from pathlib import Path


def find_assessment_sheet(data: str, gates: str):
    """(sheet, 0-based header row) of the sheet whose header row holds the protocol's ID column and the most
    criterion columns of the protocol; None if no sheet matches."""
    try:
        g = json.loads(Path(gates).read_text(encoding="utf-8"))
    except Exception:
        return None
    idc = g.get("id_column")
    wanted = {c.get("column") for st in g.get("stages", []) for c in st.get("criteria", []) if c.get("column")}
    if not idc or not str(data).lower().endswith((".xlsx", ".xlsm")):
        return None
    import openpyxl

    best = None
    wb = openpyxl.load_workbook(data, read_only=True, data_only=True)
    try:
        for ws in wb.worksheets:
            for i, row in enumerate(ws.iter_rows(min_row=1, max_row=8, values_only=True)):
                cells = {str(v).strip() for v in row if v is not None}
                if idc in cells:
                    score = len(cells & wanted)
                    if best is None or score > best[0]:
                        best = (score, ws.title, i)
    finally:
        wb.close()
    return None if best is None or best[0] == 0 else (best[1], best[2])


def _source_status(path: str) -> dict:
    """Counts of source extraction status (COMPLETE / Held / PENDING) from the extraction sheet."""
    import openpyxl

    out = {"total": 0, "complete": 0, "held": 0, "pending": 0}
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        for ws in wb.worksheets:
            if "source_extraction" not in ws.title.lower():
                continue
            rows = list(ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True))
            hdr_i = next((i for i, r in enumerate(rows[:8]) if r and "Source code" in [str(v).strip() for v in r if v is not None]), None)
            if hdr_i is None:
                continue
            hdr = [str(v).strip() if v is not None else "" for v in rows[hdr_i]]
            col = next((j for j, h in enumerate(hdr) if "extraction status" in h.lower()), None)
            if col is None:
                continue
            for r in rows[hdr_i + 1:]:
                if not r or r[0] in (None, ""):
                    continue
                v = str(r[col] or "").strip().upper()
                out["total"] += 1
                if v == "COMPLETE":
                    out["complete"] += 1
                elif v == "HELD":
                    out["held"] += 1
                else:
                    out["pending"] += 1
            break
    finally:
        wb.close()
    return out


def project_status(workbook: str, gates: str) -> dict:
    """Sources, episode levels, workbook check counts and the current roadmap step."""
    from .plugins.screen import apply_gates, load_data_sheet
    from .workbook_check import check_workbook

    st = {"workbook": Path(workbook).name, "sources": _source_status(workbook), "levels": {}, "episodes": 0,
          "held": 0, "fail": None, "warn": None, "frozen": False, "protocol": "", "problems": [], "error": ""}
    try:
        g = json.loads(Path(gates).read_text(encoding="utf-8"))
        st["frozen"], st["protocol"] = bool(g.get("frozen")), g.get("protocol_version", "")
        found = find_assessment_sheet(workbook, gates)
        if found:
            df = load_data_sheet(workbook, found[0], found[1])
            _, eps, _ = apply_gates(df, g)
            st["episodes"] = int(len(eps))
            lv = eps["level"].astype(str) if len(eps) else []
            for k in ("Level 3", "Level 2", "Level 1"):
                st["levels"][k] = int(sum(x.startswith(k) for x in lv))
            st["held"] = int(sum(x.startswith("Held") for x in lv))
    except SystemExit as e:
        st["error"] = str(e)
    except Exception as e:  # status must never break the home screen
        st["error"] = f"{type(e).__name__}: {e}"
    try:
        rep = check_workbook(workbook)
        st["fail"], st["warn"] = rep.count("FAIL"), rep.count("WARN")
        df = rep.frame()
        st["problems"] = df[df["level"].isin(["FAIL", "WARN"])].to_dict("records")
    except Exception as e:
        st["error"] = st["error"] or f"{type(e).__name__}: {e}"
    s = st["sources"]
    if s["total"] and s["pending"]:
        st["step"] = "A"
    elif not st["frozen"]:
        st["step"] = "B" if s["total"] else "A"
    else:
        st["step"] = "D"
    return st
