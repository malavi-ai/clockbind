"""Unified local statistics CLI over the same analysis registry used by ClockBind Studio.

Examples
--------
clockbind stats list
clockbind stats columns --data study.xlsx
clockbind stats run --data study.xlsx --analysis descriptives --param variables=age,bp
clockbind stats run --data study.xlsx --analysis t_independent --param variables=outcome --param group=arm
clockbind stats batch --data study.xlsx --syntax analysis_plan.json

All computation is local. No dataset contents are sent to an AI or network service.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from ..core.io import load_data
from ..core.plugin import Plugin
from ..core.provenance import RunLog


def _value(text: str):
    """Parse JSON-like scalar/list/object; otherwise keep the original string."""
    s = text.strip()
    try:
        return json.loads(s)
    except Exception:
        low = s.lower()
        if low == "true":
            return True
        if low == "false":
            return False
        if low in {"none", "null"}:
            return None
        return s


def _params(a) -> dict:
    out = {}
    if getattr(a, "params", None):
        raw = a.params
        p = Path(raw)
        if p.exists():
            out.update(json.loads(p.read_text(encoding="utf-8")))
        else:
            obj = json.loads(raw)
            if not isinstance(obj, dict):
                raise ValueError("--params must be a JSON object or the path to a JSON object file")
            out.update(obj)
    for item in getattr(a, "param", []) or []:
        if "=" not in item:
            raise ValueError(f"Invalid --param {item!r}; use key=value")
        k, v = item.split("=", 1)
        k = k.strip()
        if not k:
            raise ValueError("--param key cannot be empty")
        out[k] = _value(v)
    return out


def _safe_sheet(s: str, used: set[str]) -> str:
    s = re.sub(r"[\\/*?:\[\]]", "_", str(s)).strip() or "table"
    base = s[:31]
    candidate = base
    n = 2
    while candidate in used:
        suffix = f"_{n}"
        candidate = base[: 31 - len(suffix)] + suffix
        n += 1
    used.add(candidate)
    return candidate


def _export_blocks(output, runlog) -> None:
    tables = [(b.title or f"table_{i+1}", b.content) for i, b in enumerate(output.blocks) if b.kind == "table"]
    figures = [(b.title or f"figure_{i+1}", b.content) for i, b in enumerate(output.blocks) if b.kind == "figure"]
    if tables:
        xlsx = runlog.path("tables.xlsx")
        used: set[str] = set()
        with pd.ExcelWriter(xlsx, engine="openpyxl") as xw:
            for title, df in tables:
                df.to_excel(xw, sheet_name=_safe_sheet(title, used), index=True)
        runlog.add_output(xlsx)
    for i, (title, png) in enumerate(figures, 1):
        stem = re.sub(r"[^A-Za-z0-9._-]+", "_", title).strip("_")[:60] or f"figure_{i}"
        p = runlog.path(f"{i:02d}_{stem}.png")
        p.write_bytes(png)
        runlog.add_output(p)


def cmd_list(a):
    from ..analysis import REGISTRY
    groups: dict[str, list[tuple[str, str]]] = {}
    for name, spec in REGISTRY.items():
        groups.setdefault(spec["group"], []).append((name, spec["title"]))
    for group in sorted(groups):
        print(f"\n{group}")
        for name, title in sorted(groups[group]):
            print(f"  {name:28s} {title}")


def cmd_show(a):
    from ..analysis import REGISTRY
    if a.analysis not in REGISTRY:
        raise ValueError(f"Unknown analysis {a.analysis!r}. Run 'clockbind stats list'.")
    spec = REGISTRY[a.analysis]
    print(spec["title"])
    print(f"Group: {spec['group']}")
    if spec.get("doc"):
        print(spec["doc"])
    print("Parameters:")
    for p in spec.get("params", []):
        req = "optional" if p.get("optional") or "default" in p else "required"
        default = f"; default={p['default']!r}" if "default" in p else ""
        print(f"  {p['name']}: {p.get('label', p['name'])} [{p.get('type','value')}; {req}{default}]")


def cmd_columns(a):
    df = load_data(a.data)
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    for c in df.columns:
        s = df[c]
        nonmiss = int(s.notna().sum())
        nunique = int(s.nunique(dropna=True))
        print(f"  {c}\t{s.dtype}\tnonmissing={nonmiss}\tunique={nunique}")


def _run_one(data: str, analysis_name: str, params: dict, out_dir: str, title: str | None = None):
    from ..analysis import REGISTRY, outputs_to_docx, run, syntax_file
    if analysis_name not in REGISTRY:
        raise ValueError(f"Unknown analysis {analysis_name!r}. Run 'clockbind stats list'.")
    df = load_data(data)
    with RunLog(out_dir, "stats", analysis_name, {"data": data, "analysis": analysis_name, "params": params, "title": title}, None) as log:
        log.add_input(data)
        o = run(analysis_name, df, params)
        doc = outputs_to_docx([o], log.path("output.docx"), title=title or f"ClockBind statistics — {Path(data).name}")
        log.add_output(doc)
        syntax = log.path("syntax.json")
        syntax.write_text(syntax_file([o]), encoding="utf-8")
        log.add_output(syntax)
        _export_blocks(o, log)
        log.note("analysis", analysis_name)
        log.note("parameters", params)
        log.note("data_rows", len(df))
        log.note("data_columns", len(df.columns))
        print(f"Analysis: {analysis_name}")
        print(f"Word output: {doc}")
        return 0


def cmd_run(a):
    return _run_one(a.data, a.analysis, _params(a), a.out, a.title)


def cmd_batch(a):
    from ..analysis import outputs_to_docx, run, syntax_file
    spec = json.loads(Path(a.syntax).read_text(encoding="utf-8"))
    steps = spec.get("steps", []) if isinstance(spec, dict) else spec
    if not isinstance(steps, list) or not steps:
        raise ValueError("Syntax file must contain a non-empty 'steps' list")
    df = load_data(a.data)
    with RunLog(a.out, "stats", "batch", vars(a), None) as log:
        log.add_input(a.data)
        log.add_input(a.syntax, "syntax")
        outs = []
        for st in steps:
            if not isinstance(st, dict) or "analysis" not in st:
                raise ValueError("Each syntax step needs an 'analysis' field")
            o = run(st["analysis"], df, st.get("params", {}))
            outs.append(o)
            print(f"ran {st['analysis']}")
        doc = outputs_to_docx(outs, log.path("output.docx"), title=a.title or f"ClockBind statistics — {Path(a.data).name}")
        log.add_output(doc)
        frozen = log.path("syntax.json")
        frozen.write_text(syntax_file(outs), encoding="utf-8")
        log.add_output(frozen)
        # Combined table workbook and figure exports.
        used: set[str] = set(); table_rows = []
        xlsx = log.path("tables.xlsx")
        any_table = False
        with pd.ExcelWriter(xlsx, engine="openpyxl") as xw:
            for oi, o in enumerate(outs, 1):
                for bi, b in enumerate(o.blocks, 1):
                    if b.kind == "table":
                        any_table = True
                        nm = _safe_sheet(f"{oi}_{o.analysis}_{b.title or bi}", used)
                        b.content.to_excel(xw, sheet_name=nm, index=True)
                    elif b.kind == "figure":
                        stem = re.sub(r"[^A-Za-z0-9._-]+", "_", b.title or f"{o.analysis}_{bi}").strip("_")[:50]
                        p = log.path(f"fig_{oi:02d}_{bi:02d}_{stem}.png")
                        p.write_bytes(b.content); log.add_output(p)
        if any_table:
            log.add_output(xlsx)
        else:
            xlsx.unlink(missing_ok=True)
        log.note("steps", [o.syntax for o in outs])
        print(f"Word output: {doc}")
        return 0


class Stats(Plugin):
    name = "stats"
    help = "Local reproducible statistics: descriptives, tests, regression, reliability, factor analysis and doctoral modules"

    def register(self, sub):
        p = sub.add_parser("list", help="List all statistical analyses available in the local analysis registry")
        p.set_defaults(func=cmd_list)

        p = sub.add_parser("show", help="Show the parameters required by one analysis")
        p.add_argument("analysis", help="Analysis name from 'clockbind stats list'")
        p.set_defaults(func=cmd_show)

        p = sub.add_parser("columns", help="Inspect column names/types without printing row values")
        p.add_argument("--data", required=True)
        p.set_defaults(func=cmd_columns)

        p = sub.add_parser("run", help="Run one analysis locally and write Word, Excel/figures, syntax and provenance manifest")
        p.add_argument("--data", required=True)
        p.add_argument("--analysis", required=True, help="Analysis name from 'clockbind stats list'")
        p.add_argument("--params", help="JSON object or path to JSON object file")
        p.add_argument("--param", action="append", default=[], help="Repeatable key=value parameter (for example --param variables=age,bp)")
        p.add_argument("--title", help="Optional report title")
        p.add_argument("--out", default="clockbind_runs")
        p.set_defaults(func=cmd_run)

        p = sub.add_parser("batch", help="Run a frozen multi-step syntax file locally")
        p.add_argument("--data", required=True)
        p.add_argument("--syntax", required=True)
        p.add_argument("--title", help="Optional report title")
        p.add_argument("--out", default="clockbind_runs")
        p.set_defaults(func=cmd_batch)


PLUGIN = Stats()
