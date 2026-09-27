"""Shared helpers for plugins."""
from __future__ import annotations

import json
from pathlib import Path


def add_common(p, data: bool = True, seed: bool = False):
    if data:
        p.add_argument("--data", required=True, help="Input file (csv, xlsx, sav, dta, parquet)")
    p.add_argument("--out", default="clockbind_runs", help="Folder for run outputs (default: clockbind_runs)")
    if seed:
        p.add_argument("--seed", type=int, default=None, help="Random seed (recorded in the manifest). Required for reproducible runs.")
    return p


def split_list(s: str | None) -> list[str]:
    return [x.strip() for x in s.split(",") if x.strip()] if s else []


def load_json(path: str | None) -> dict:
    if not path:
        return {}
    with open(Path(path), encoding="utf-8") as f:
        return json.load(f)
