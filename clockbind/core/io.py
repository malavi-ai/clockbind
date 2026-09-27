"""Data input and table output."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_data(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".csv":
        return pd.read_csv(p)
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(p)
    if ext == ".sav":
        try:
            import pyreadstat  # noqa: F401
        except ImportError as e:  # pragma: no cover
            raise SystemExit("Reading .sav needs pyreadstat: pip install pyreadstat") from e
        return pd.read_spss(p)
    if ext == ".dta":
        return pd.read_stata(p)
    if ext == ".parquet":
        return pd.read_parquet(p)
    raise SystemExit(f"Unsupported file type: {ext} (use csv, xlsx, sav, dta or parquet)")


def require_columns(df: pd.DataFrame, cols) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing columns in data: {missing}. Available: {list(df.columns)}")


def write_tables(run, tables: dict[str, pd.DataFrame], stem: str = "results") -> None:
    """Write several tables to one Excel workbook and one Markdown file."""
    xlsx = run.path(f"{stem}.xlsx")
    with pd.ExcelWriter(xlsx, engine="openpyxl") as xw:
        for name, df in tables.items():
            df.to_excel(xw, sheet_name=name[:31], index=True)
    run.add_output(xlsx)
    md = run.path(f"{stem}.md")
    with open(md, "w", encoding="utf-8") as f:
        for name, df in tables.items():
            f.write(f"## {name}\n\n")
            f.write(_to_markdown(df))
            f.write("\n\n")
    run.add_output(md)


def _to_markdown(df: pd.DataFrame) -> str:
    d = df.copy()
    d.index = d.index.map(str)
    cols = [str(d.index.name or "")] + [str(c) for c in d.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for idx, row in d.iterrows():
        vals = []
        for v in row.values:
            if isinstance(v, float):
                vals.append(f"{v:.4g}")
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join([str(idx)] + vals) + " |")
    return "\n".join(lines)
