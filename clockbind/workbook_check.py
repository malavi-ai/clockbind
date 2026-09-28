"""Workbook integrity check: formulas, dropdowns, cross-sheet consistency, override logs, privacy.

Reports locations (sheet and cell) and controlled codes only. Cell contents that
could hold personal data are never printed.
"""
from __future__ import annotations

import re
from pathlib import Path

import openpyxl
import pandas as pd

from .privacy import scan_dataframe

ERRORS = ("#REF!", "#VALUE!", "#DIV/0!", "#NAME?", "#N/A", "#NUM!", "#NULL!", "Err:")
UNQUOTED = re.compile(r"(?<![\w'])(\d[\w.]*)!")
CODE = re.compile(r"\b(?:E\d{2,3}|PL-M\d{2}[A-Z]?)\b")


class Report:
    def __init__(self):
        self.rows = []

    def add(self, level, check, where="", detail=""):
        self.rows.append({"level": level, "check": check, "where": where, "detail": detail})

    def frame(self):
        return pd.DataFrame(self.rows, columns=["level", "check", "where", "detail"])

    def count(self, level):
        return sum(r["level"] == level for r in self.rows)


def _list_items(dv):
    f = (dv.formula1 or "").strip()
    if dv.type != "list" or not (f.startswith('"') and f.endswith('"')):
        return None
    return [x.strip() for x in f[1:-1].split(",")]


def _header_row(ws, name, max_row=6):
    for r in range(1, max_row + 1):
        vals = [str(c.value).strip() if c.value is not None else "" for c in ws[r]]
        if name in vals:
            return r, {v: i + 1 for i, v in enumerate(vals) if v}
    return None, {}


def _short(where, n=12):
    return ", ".join(where[:n]) + (f" … (+{len(where) - n} more)" if len(where) > n else "")


def _uncalculated(path) -> dict:
    """Formula cells that carry no stored result at all (never calculated), per sheet name.

    An empty-string result is stored as <v></v> or t="str" and is not counted."""
    import zipfile
    out = {}
    with zipfile.ZipFile(path) as z:
        wbx = z.read("xl/workbook.xml").decode("utf-8")
        rels = z.read("xl/_rels/workbook.xml.rels").decode("utf-8")
        target = {m.group(1): m.group(2) for m in re.finditer(r'<Relationship[^>]*Id="([^"]+)"[^>]*Target="([^"]+)"', rels)}
        target.update({m.group(2): m.group(1) for m in re.finditer(r'<Relationship[^>]*Target="([^"]+)"[^>]*Id="([^"]+)"', rels)})
        for m in re.finditer(r'<sheet\b[^>]*?name="([^"]+)"[^>]*?r:id="([^"]+)"', wbx):
            name, rid = m.group(1), m.group(2)
            t = target.get(rid, "")
            t = t.lstrip("/")
            t = t if t.startswith("xl/") else "xl/" + t
            try:
                xml = z.read(t).decode("utf-8")
            except KeyError:
                continue
            cells = [c.group(1) for c in re.finditer(r'<c r="([A-Z]+\d+)"((?:(?!/>)[^>])*)>((?:(?!</c>).)*)</c>', xml, re.S)
                     if "<f" in c.group(3) and 't="' not in c.group(2)
                     and ("<v" not in c.group(3) or "<v></v>" in c.group(3) or "<v/>" in c.group(3))]
            if cells:
                out[name.replace("&amp;", "&")] = cells
    return out


def check_generic(wb_f, wb_v, rep: Report, path=None):
    uncalc = _uncalculated(path) if path else {}
    for ws in wb_f.worksheets:
        wv = wb_v[ws.title]
        archived = ws.title.lower().startswith("archive")
        err, stale, unq = [], [], []
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith("="):
                    cached = wv[c.coordinate].value
                    if isinstance(cached, str) and cached.startswith(ERRORS):
                        err.append(c.coordinate)
                    if UNQUOTED.search(c.value):
                        unq.append(c.coordinate)
        if err:
            rep.add("FAIL", "Formula errors", ws.title, _short(err))
        stale = uncalc.get(ws.title, [])
        if stale:
            rep.add("WARN", "Formulas without a calculated value (open and recalculate, e.g. Ctrl+Alt+F9)", ws.title, f"{len(stale)} cells, e.g. {_short(stale, 5)}")
        if unq:
            rep.add("WARN", "Sheet name starting with a digit is not quoted in a formula (may fail in Excel)", ws.title, _short(unq, 5))
        for dv in ws.data_validations.dataValidation:
            items = _list_items(dv)
            if items is None:
                continue
            bad = []
            for rng in str(dv.sqref).split():
                cells = ws[rng]
                cells = cells if isinstance(cells, tuple) else ((cells,),)
                for row in cells:
                    for c in (row if isinstance(row, tuple) else (row,)):
                        v = c.value
                        if v not in (None, "") and not (isinstance(v, str) and v.startswith("=")) and str(v).strip() not in items:
                            bad.append(c.coordinate)
            if bad:
                rep.add("INFO" if archived else "FAIL", "Entries outside the dropdown list" + (" (archived sheet)" if archived else ""),
                        f"{ws.title} {dv.sqref}", _short(bad))
            if not dv.showErrorMessage and not archived:
                rep.add("INFO", "Dropdown does not block invalid entries", f"{ws.title} {dv.sqref}")


def _codes(text):
    return set(CODE.findall(str(text or "")))


def check_bridge(wb_v, rep: Report):
    names = {ws.title for ws in wb_v.worksheets}
    a_name = next((n for n in names if n.startswith("05") and "Level_Assessment" in n and not n.startswith("Archive")), None)
    s_name = next((n for n in names if n.startswith("03") and "Source_Extraction" in n), None)
    m_name = next((n for n in names if n.startswith("04") and "Source_Metadata" in n), None)
    if not a_name:
        rep.add("INFO", "Bridge-specific checks skipped (no level assessment sheet found)")
        return
    a = wb_v[a_name]
    hr, h = _header_row(a, "Episode ID")
    if not hr:
        rep.add("FAIL", "Header 'Episode ID' not found", a_name)
        return
    col = lambda *keys: next((i for k, i in h.items() if all(x.lower() in k.lower() for x in keys)), None)
    rows = [r for r in range(hr + 1, a.max_row + 1) if a.cell(r, 1).value not in (None, "")]
    ids = [str(a.cell(r, 1).value).strip() for r in rows]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    rep.add("FAIL" if dup else "PASS", "Episode IDs unique", a_name, ", ".join(dup))
    # overrides
    for label, lv, rs, dt in (("Level override", col("Override level"), col("Override reason"), col("Override date")),
                              ("Ceiling override", col("Ceiling override (only"), col("Ceiling override reason"), col("Ceiling override date"))):
        if lv:
            bad = [ids[k] for k, r in enumerate(rows) if a.cell(r, lv).value not in (None, "") and (a.cell(r, rs).value in (None, "") or a.cell(r, dt).value in (None, ""))]
            rep.add("FAIL" if bad else "PASS", f"{label}s have reason and date", a_name, ", ".join(bad))
    ba = col("Verdict consistency")
    if ba:
        bad = [f"{ids[k]} ({a.cell(r, ba).value})" for k, r in enumerate(rows) if str(a.cell(r, ba).value or "").startswith("ERROR")]
        rep.add("FAIL" if bad else "PASS", "Binding verdicts consistent with level and sign stability", a_name, "; ".join(bad))
    fin = col("Final level")
    if fin:
        bad = [ids[k] for k, r in enumerate(rows) if str(a.cell(r, fin).value or "").startswith("INVALID")]
        rep.add("FAIL" if bad else "PASS", "No invalid final levels", a_name, ", ".join(bad))
    # cross-sheet
    if s_name:
        s = wb_v[s_name]
        shr, sh = _header_row(s, "Source code")
        if shr:
            c_status = next((i for k, i in sh.items() if "extraction status" in k.lower()), None)
            c_ids = next((i for k, i in sh.items() if "episode id" in k.lower()), None)
            c_n = next((i for k, i in sh.items() if "number of distinct" in k.lower()), None)
            srows = [r for r in range(shr + 1, s.max_row + 1) if s.cell(r, 1).value not in (None, "")]
            src = [str(s.cell(r, 1).value).strip() for r in srows]
            d = sorted({x for x in src if src.count(x) > 1})
            rep.add("FAIL" if d else "PASS", "Source codes unique", s_name, ", ".join(d))
            status = {src[k]: str(s.cell(r, c_status).value or "").strip().upper() for k, r in enumerate(srows)} if c_status else {}
            pend = [x for x, v in status.items() if v == "PENDING"]
            rep.add("INFO", "Sources still PENDING extraction", s_name, f"{len(pend)} of {len(src)}")
            listed = set()
            if c_ids:
                for k, r in enumerate(srows):
                    listed |= _codes(s.cell(r, c_ids).value)
                    if status.get(src[k]) == "COMPLETE":
                        if c_n and s.cell(r, c_n).value in (None, ""):
                            rep.add("FAIL", "COMPLETE source without a number of episodes", s_name, src[k])
                        n = s.cell(r, c_n).value if c_n else None
                        if n not in (None, "", 0, "0") and not _codes(s.cell(r, c_ids).value):
                            rep.add("FAIL", "COMPLETE source without episode codes", s_name, src[k])
            missing = sorted(listed - set(ids))
            rep.add("FAIL" if missing else "PASS", "Every episode code in the extraction sheet has a row in the assessment sheet", a_name, ", ".join(missing))
            c_src = col("Source code")
            c_d = col("Episode extraction complete")
            if c_src and c_d:
                bad = [ids[k] for k, r in enumerate(rows) if str(a.cell(r, c_d).value or "").upper() == "COMPLETE"
                       and status.get(str(a.cell(r, c_src).value or "").strip()) != "COMPLETE"]
                rep.add("FAIL" if bad else "PASS", "Episode marked COMPLETE only when its source is COMPLETE", a_name, ", ".join(bad))
                unknown = sorted({str(a.cell(r, c_src).value).strip() for r in rows if a.cell(r, c_src).value not in (None, "")} - set(src))
                rep.add("FAIL" if unknown else "PASS", "Episode source codes exist in the extraction sheet", a_name, ", ".join(unknown))
    if m_name:
        m = wb_v[m_name]
        mhr, _ = _header_row(m, "Evidence ID")
        if mhr:
            ev = {str(m.cell(r, 1).value).strip() for r in range(mhr + 1, m.max_row + 1) if m.cell(r, 1).value}
            refs = set()
            for ws in (wb_v[x] for x in (s_name, a_name) if x):
                for row in ws.iter_rows():
                    for c in row:
                        refs |= set(re.findall(r"\bEV-[A-Z0-9-]+\b", str(c.value or "")))
            miss = sorted(r for r in refs - ev if not r.endswith("-MAP"))
            rep.add("WARN" if miss else "PASS", "Evidence references exist in the source metadata sheet", m_name, ", ".join(miss))


def check_privacy(path, rep: Report):
    found = 0
    for sheet, df in pd.read_excel(path, sheet_name=None, dtype=str).items():
        for x in scan_dataframe(df):
            found += 1
            rep.add("FAIL", "Possible personal data (values not shown)", f"{sheet} › {x['column']}", f"{x['kind']} ({x['count']} cells)")
    if not found:
        rep.add("PASS", "Personal-data scan", "all sheets", "no patterns found (does not prove anonymity)")


def check_workbook(path) -> Report:
    rep = Report()
    p = Path(path)
    wb_f = openpyxl.load_workbook(p)
    wb_v = openpyxl.load_workbook(p, data_only=True)
    check_generic(wb_f, wb_v, rep, p)
    check_bridge(wb_v, rep)
    check_privacy(p, rep)
    return rep
