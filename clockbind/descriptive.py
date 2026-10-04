"""Descriptive (non-gate) fields, the temporal-evidence ladder and chat-safe sharing safeguards.

Descriptive fields never change a gate, level, verdict or claim tier. They are declared in the
gates JSON under "descriptive_fields"; when absent, the Bridge defaults below are used, but only
for columns that actually exist in the data sheet.

Each field: {"column", "label", "allowed": [...], "aliases": [...],
             "required_when": {"criterion": "L3b", "equals": "No"} | {"level": "Below Level 1"} | {"analysable": true}}
"""
from __future__ import annotations

import re

import pandas as pd

GAP_VALUES = ["Not created", "Informal channel (WhatsApp/phone)", "Exists – not accessible", "Legal restriction", "Unknown", "PENDING", "N/A"]
STOP_VALUES = ["Stopped after price quote", "Liquidity constraint stated", "Financing inquired – not pursued", "Chose other supplier",
               "Deferred", "Other", "Unknown", "PENDING", "N/A"]
BUYER_VALUES = ["Existing business", "New venture (pre-opening / <1 year)", "Unknown", "PENDING"]

DEFAULT_FIELDS = [
    {"column": f"{g} gap reason", "label": f"Why the record for {g} is missing", "allowed": GAP_VALUES,
     "required_when": {"criterion": g, "equals": "No"}} for g in ("L3b", "L3c", "L3e")
] + [
    {"column": "Stop point", "label": "Where an episode below Level 1 stopped (main reason)", "allowed": STOP_VALUES,
     "required_when": {"level": "Below Level 1"}},
    {"column": "Stop point 2", "label": "Second reason (optional)", "allowed": STOP_VALUES},
    {"column": "Buyer stage", "label": "Buyer stage", "allowed": BUYER_VALUES, "required_when": {"analysable": True}},
]

DEFAULT_LADDER = [("L1d", "Realised chronology reconstructable"),
                  ("L3b", "Ex-ante expected durations documented"),
                  ("L3c", "Window set independently of the outcome")]

NOT_ANALYSABLE = ("Outside analytic archive", "Held at S0")
SMALL_CELL = 3
# tables whose count columns are suppressed (<3) in chat-safe mode; core funnel/level tables are exempt
SUPPRESS_PREFIXES = ("03_Source_classes", "08_", "13_")


def _s(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def _norm(t: str) -> str:
    return re.sub(r"[\s\-–—_/()]+", " ", t.lower()).strip()


def find_column(columns, name, aliases=()) -> str | None:
    want = {_norm(x) for x in (name, *aliases)}
    for c in columns:
        if _norm(str(c)) in want:
            return c
    return None


def canonical(value, allowed) -> str | None:
    """'' for blank; canonical allowed value (case/spacing-insensitive); None if not allowed."""
    v = _s(value)
    if not v:
        return ""
    for a in allowed:
        if _norm(v) == _norm(a):
            return a
    return None


def fields_for(g: dict) -> list:
    return g.get("descriptive_fields") or DEFAULT_FIELDS


def _criterion_columns(g):
    return {c["id"]: c["column"] for s in g["stages"] for c in s["criteria"]}


def _required(rule, ep_row, crit_cols) -> bool:
    if not rule:
        return False
    lvl = _s(ep_row.get("level"))
    if "criterion" in rule:
        col = crit_cols.get(rule["criterion"])
        return bool(col) and _s(ep_row.get(col)) == rule.get("equals", "No")
    if "level" in rule:
        return lvl == rule["level"]
    if rule.get("analysable"):
        return bool(lvl) and not lvl.startswith(NOT_ANALYSABLE)
    return False


def evaluate(eps: pd.DataFrame, first_rows: pd.DataFrame, eid: str, g: dict):
    """Returns (tables, checks). checks = list of (level, check, episodes, note)."""
    tables, checks = {}, []
    crit_cols = _criterion_columns(g)
    src = first_rows if first_rows is not None and len(first_rows) else None
    present = []
    for f in fields_for(g):
        col = find_column(src.columns if src is not None else [], f["column"], f.get("aliases", ()))
        if col is None:
            continue
        present.append(f["column"])
        rows, blank_req, invalid = [], [], []
        for _, r in eps.iterrows():
            e = _s(r[eid])
            raw = src.loc[e].get(col) if e in src.index else None
            val = canonical(raw, f["allowed"])
            req = _required(f.get("required_when"), {**r.to_dict(), **({crit_cols[k]: src.loc[e].get(crit_cols[k]) for k in crit_cols
                                                                         if e in src.index and crit_cols[k] in src.columns})}, crit_cols)
            if val is None:
                invalid.append(e)
                val = "invalid value"
            if req and val in ("", "PENDING"):
                blank_req.append(e)
            if req or (val and val != "N/A"):
                rows.append({"required": "required" if req else "optional", "value": val or "blank"})
        key = "13_" + re.sub(r"[^A-Za-z0-9]+", "_", f["column"]).strip("_")
        if rows:
            t = pd.DataFrame(rows).groupby(["value"]).size().reset_index(name="episodes")
            order = {v: i for i, v in enumerate(f["allowed"] + ["blank", "invalid value"])}
            tables[key] = t.sort_values("value", key=lambda s: s.map(lambda v: order.get(v, 99))).reset_index(drop=True)
        checks.append(("FAIL", f"Descriptive field '{f['column']}': value not in the allowed list", invalid,
                       "Use one of: " + " | ".join(f["allowed"])))
        checks.append(("WARN", f"Descriptive field '{f['column']}': required but blank/PENDING", blank_req,
                       f"Code it before the lock ({f.get('label', '')}). Descriptive only: never changes a gate or level."))
    return tables, checks, present


def temporal_ladder(eps: pd.DataFrame, g: dict) -> pd.DataFrame | None:
    """Yes/No/PENDING counts for the realised → ex-ante → independent-window ladder among analysable episodes."""
    crit = _criterion_columns(g)
    spec = g.get("temporal_ladder") or DEFAULT_LADDER
    spec = [(i, lab) if isinstance(i, str) else (i["id"], i["label"]) for i, lab in
            ([(x["id"], x["label"]) for x in spec] if spec and isinstance(spec[0], dict) else spec)]
    an = eps[~eps["level"].map(_s).str.startswith(NOT_ANALYSABLE)]
    rows = []
    for cid, lab in spec:
        col = crit.get(cid)
        if not col or col not in an.columns:
            continue
        v = an[col].map(_s)
        rows.append({"step": f"{cid} · {lab}", "Yes": int(v.isin(["Yes", "COMPLETE"]).sum()), "No": int((v == "No").sum()),
                     "PENDING / other": int((~v.isin(["Yes", "COMPLETE", "No"])).sum()), "of analysable": len(an)})
    return pd.DataFrame(rows) if rows else None


def finance_ladder(eps: pd.DataFrame, g: dict, res: pd.DataFrame | None) -> pd.DataFrame | None:
    """Observed → temporally actionable → counterfactually binding financing."""
    crit = _criterion_columns(g)
    col = crit.get("L3a")
    if not col or col not in eps.columns:
        return None
    an = eps[~eps["level"].map(_s).str.startswith(NOT_ANALYSABLE)]
    rows = [("Financing observed: financing route evaluated (L3a = Yes)", int((an[col].map(_s) == "Yes").sum()))]
    if res is not None and len(res):
        rows.append(("Temporally actionable: finance usable in time (engine = Yes)", int((res["finance_actionable"].map(_s) == "Yes").sum())))
        rows.append(("Actionability not computable (engine)", int(res["finance_actionable"].map(_s).str.lower().str.contains("not computable").sum())))
        rows.append(("Counterfactually binding: Finance-binding (engine)", int((res["verdict"].map(_s) == "Finance-binding").sum())))
        if "fragile" in res.columns:
            rows.append(("   of which fragile (|slack| ≤ 1 day)", int(((res["verdict"].map(_s) == "Finance-binding") & (res["fragile"].map(_s) == "Yes")).sum())))
    return pd.DataFrame(rows, columns=["level of the financing claim", "episodes"])


def suppress_small_cells(tables: dict) -> list:
    """Chat-safe: replace counts 1–2 by '<3' in tables listed in SUPPRESS_PREFIXES. Returns a manifest of suppressed cells."""
    manifest = []
    for k, t in list(tables.items()):
        if not k.startswith(SUPPRESS_PREFIXES):
            continue
        t = t.copy()
        for c in t.columns:
            if c in ("episodes", "records", "documents", "entries", "count") and pd.api.types.is_numeric_dtype(t[c]):
                small = t[c].between(1, SMALL_CELL - 1)
                if small.any():
                    manifest += [(k, c, _s(t.iloc[i, 0])) for i in range(len(t)) if small.iloc[i]]
                    t[c] = t[c].astype(object).where(~small, f"<{SMALL_CELL}")
        tables[k] = t
    return manifest


def leaked_codes(tables: dict, codes) -> list:
    """Episode codes that still appear in any table (chat-safe must have none)."""
    codes = {c for c in (_s(x) for x in codes) if len(c) >= 2}
    if not codes:
        return []
    pat = re.compile(r"(?<![A-Za-z0-9])(" + "|".join(re.escape(c) for c in sorted(codes, key=len, reverse=True)) + r")(?![A-Za-z0-9])")
    found = set()
    for t in tables.values():
        for v in [_s(x) for x in t.to_numpy().ravel().tolist()] + [str(c) for c in t.columns]:
            found.update(pat.findall(v))
    return sorted(found)
