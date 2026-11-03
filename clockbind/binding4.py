"""Protocol 4.0 engine for "which clock binds?" (Bridge Study 2a).

Protocol 4.0 extends the registered v3.4 rule (``clockbind.binding``) without changing it:

* Six clocks: the five v3.4 clocks plus ``institutional`` (tariff classification, movement
  certificates, proof of origin, product control, duty assessment, release). In v3.4 customs was
  an alias of logistics; under 4.0 it is a clock of its own.
* Ex-ante status per step: documented (expected duration from a pre-outcome document, v3.4 rule
  incl. the zero-duration rule), revealed (requirement first documented after the process began;
  ``revealed_at`` from a dated document) or undocumented.
* Revealed-in-process rule (knowledge, feasibility and execution kept separate): a revealed step has
  no ex-ante duration. The worst case treats it as untestable. A best case exists only if the earliest
  date at which the action could have started (``actionable_from``) is supported by a dated document;
  the step is then corrected to start at max(ready, actionable_from) and to take its post-revelation
  execution time (finish - max(ready, revealed_at)). Without ``actionable_from`` the best case is not
  computed and the worst-case verdict stands (usually Indeterminate). Different best/worst verdicts ->
  Indeterminate, reason ``revelation-sensitive`` (a sub-type of Indeterminate, not a causal verdict).
* Claim ceiling (claim-specific evidence): a positive binding verdict is capped at "consistent with"
  unless every binding clock has at least one step whose timing is recorded directly
  (``direct_record`` = Yes) by a non-internal source. The verdict is not changed.

The counterfactual machinery (critical path, sign stability, jointly binding, multiple-sufficient,
window-infeasible, fragile flag, finance actionability) is the v3.4 engine itself: this module only
supplies the 4.0 clock set and inputs and combines the two revelation bounds. With no institutional
or revealed steps, results are identical to ``clockbind.binding.evaluate_all``.
"""
from __future__ import annotations

import contextlib
import copy

import pandas as pd

from . import binding as b3

PROTOCOL = "4.0"
LABELS_V4 = {**b3.CLOCK_LABELS, "institutional": "Institution-binding"}
ALIASES_V4 = {k: v for k, v in b3.CLOCK_ALIASES.items() if k != "customs"}
ALIASES_V4.update({
    "customs": "institutional", "customs clearance": "institutional", "clearance": "institutional",
    "origin": "institutional", "proof of origin": "institutional", "classification": "institutional",
    "tariff": "institutional", "duty": "institutional", "release": "institutional", "regulatory": "institutional",
    "product control": "institutional", "conformity": "institutional", "institution": "institutional",
})
VERDICTS_V4 = set(LABELS_V4.values()) | {"Jointly binding", "Non-binding", "Indeterminate"}
STATUS = {"documented": "documented", "d": "documented", "s-d": "documented",
          "revealed": "revealed", "r": "revealed", "s-r": "revealed", "revealed in process": "revealed",
          "undocumented": "undocumented", "u": "undocumented", "s-u": "undocumented"}
SOURCE_CLASSES = {"internal", "counterparty", "third-party", "public-authority"}
NON_INTERNAL = SOURCE_CLASSES - {"internal"}
STEP_COLUMNS_V4 = b3.STEP_COLUMNS[:8] + ["ex_ante_status", "revealed_at", "actionable_from", "source_class", "direct_record", "contemporaneity"] + b3.STEP_COLUMNS[8:]
EPISODE_COLUMNS_V4 = b3.EPISODE_COLUMNS[:-1] + ["related_party"] + b3.EPISODE_COLUMNS[-1:]
LAYERS = ["focal-firm", "counterparty", "intermediary", "institutional", "environmental"]
LAYER_STATES = {"activated": "Activated", "a": "Activated", "exposed": "Exposed", "e": "Exposed",
                "not present": "Not present", "n": "Not present", "unknown": "Unknown", "u": "Unknown"}


@contextlib.contextmanager
def _protocol4(merge_institutional: bool = False):
    """Run the v3.4 machinery with the 4.0 clock set (restored afterwards)."""
    saved = (b3.CLOCK_LABELS, b3.CLOCK_ALIASES, b3.WORKBOOK_VERDICTS)
    if merge_institutional:  # sensitivity 10.2(c): reproduce the v3.4 clock set
        labels, aliases = dict(b3.CLOCK_LABELS), dict(ALIASES_V4)
        aliases.update({k: "logistics" for k, v in ALIASES_V4.items() if v == "institutional"})
        aliases["institutional"] = "logistics"
        verdicts = set(b3.WORKBOOK_VERDICTS)
    else:
        labels, aliases, verdicts = LABELS_V4, ALIASES_V4, VERDICTS_V4
    b3.CLOCK_LABELS, b3.CLOCK_ALIASES, b3.WORKBOOK_VERDICTS = labels, aliases, verdicts
    try:
        yield
    finally:
        b3.CLOCK_LABELS, b3.CLOCK_ALIASES, b3.WORKBOOK_VERDICTS = saved


def _low(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns=lambda c: str(c).strip().lower())


def _txt(v) -> str:
    return "" if b3._blank(v) else str(v).strip()


def _step_meta(steps: pd.DataFrame) -> dict:
    """(episode, step) -> ex-ante status, revealed_at (days), source class, contemporaneity, problems."""
    meta = {}
    for _, s in _low(steps).iterrows():
        eid, name = _txt(s.get("episode")), _txt(s.get("step"))
        if not eid or not name:
            continue
        probs = []
        raw = _txt(s.get("ex_ante_status")).lower()
        status = STATUS.get(raw) if raw else None
        if raw and status is None:
            probs.append(f"step {name}: ex_ante_status '{raw}' is not documented, revealed or undocumented")
        has_exp = not b3._blank(s.get("expected_days"))
        if status is None:
            status = "documented" if has_exp else "undocumented"
        if status == "revealed" and has_exp:
            probs.append(f"step {name}: ex-ante duration present, so status 'documented' prevails over 'revealed' (rule 4.2)")
            status = "documented"
        rev = act = None
        if status == "revealed":
            try:
                rev = b3._days(s.get("revealed_at"))
            except ValueError as err:
                probs.append(f"step {name}: revealed_at {err}")
            if rev is None:
                probs.append(f"step {name}: status 'revealed' needs a revealed_at date from a dated document (rule 4.1); treated as undocumented")
                status = "undocumented"
            try:
                act = b3._days(s.get("actionable_from"))
            except ValueError as err:
                probs.append(f"step {name}: actionable_from {err}")
            if act is None and status == "revealed":
                probs.append(f"step {name}: no documented actionable_from, so the best case is not computed (rule 5.2)")
        sc = _txt(s.get("source_class")).lower().replace("_", "-").replace(" ", "-")
        if sc and sc not in SOURCE_CLASSES:
            probs.append(f"step {name}: source_class '{sc}' is not internal, counterparty, third-party or public-authority")
            sc = ""
        dr = _txt(s.get("direct_record")).lower()
        meta[(eid, name)] = {"status": status, "revealed_at": rev, "actionable_from": act, "source_class": sc,
                             "direct_record": None if not dr else dr in b3.YES,
                             "contemporaneity": _txt(s.get("contemporaneity")).lower(), "problems": probs}
    return meta


def _best_case(ep: b3.Episode, revealed: dict, actionable: dict):
    """Copy of ep in which each revealed step starts at max(ready, actionable_from) and takes its post-revelation
    execution time (most favourable documented bound). Returns None if any revealed step on the path to R lacks
    a documented actionable_from (best case not computable)."""
    best = copy.deepcopy(ep)
    order, anc = b3._topo(ep), b3._ancestors(ep, ep.r_step)
    scen = {b: b3._Scenario(ep, order, anc, b) for b in ("earliest", "latest")}
    for name, rev in revealed.items():
        if name not in anc:
            continue
        act = actionable.get(name)
        if act is None:
            return None
        cands = []
        for sc in scen.values():
            fin = sc.finish[name]
            ready = fin - sc.realised[name]
            execution = max(fin - max(ready, rev), 0.0)
            cands.append(max(act - ready, 0.0) + execution)
        best.steps[name].expected = min(cands)
    return best


def _worst_case(ep: b3.Episode, revealed: dict) -> b3.Episode:
    worst = copy.deepcopy(ep)
    for name in revealed:
        if name in worst.steps:
            worst.steps[name].expected = None
    return worst


def _clocks_of(row) -> list:
    out = []
    for part in str(row.get("binding_clocks") or "").replace(";", "+").split("+"):
        p = part.strip()
        if p:
            out.append(p)
    return sorted(set(out))


def _claim_cap(ep: b3.Episode, row: dict, meta: dict) -> str:
    v = row.get("verdict", "")
    if v not in set(LABELS_V4.values()) | {"Jointly binding"}:
        return ""
    try:
        anc = b3._ancestors(ep, ep.r_step)
    except Exception:
        return ""
    lacking = []
    for clock in _clocks_of(row):
        ok = False
        for n in anc:
            if ep.steps[n].clock != clock:
                continue
            m = meta.get((ep.id, n), {})
            if m.get("source_class") in NON_INTERNAL and m.get("direct_record") is not False:
                if m.get("direct_record") is None:
                    row.setdefault("_claim_notes", []).append(f"{n}: direct_record not coded; external source assumed to record the step")
                ok = True
        if not ok:
            lacking.append(clock)
    return ("consistent with (internal evidence only for: " + ", ".join(lacking) + ")") if lacking else "not capped"


def evaluate_all_v4(episodes: pd.DataFrame, steps: pd.DataFrame, zero_as_documented: bool = False,
                    merge_institutional: bool = False) -> pd.DataFrame:
    """Protocol 4.0 verdicts. merge_institutional=True is SENSITIVITY 10.2(c) (v3.4 clock set)."""
    meta = _step_meta(steps)
    rel = {}
    e_low = _low(episodes)
    if "related_party" in e_low.columns:
        for _, e in e_low.iterrows():
            rel[_txt(e.get("episode"))] = "Yes" if _txt(e.get("related_party")).lower() in b3.YES else ("No" if _txt(e.get("related_party")) else "")
    rows = []
    with _protocol4(merge_institutional):
        eps = b3.build_episodes(episodes, steps, zero_as_documented=zero_as_documented)
        for ep in eps:
            extra = [p for (eid, _), m in meta.items() if eid == ep.id for p in m["problems"]]
            revealed = {n: meta[(ep.id, n)]["revealed_at"] for n in ep.steps
                        if meta.get((ep.id, n), {}).get("status") == "revealed"}
            actionable = {n: meta[(ep.id, n)]["actionable_from"] for n in revealed}
            if not revealed:
                row = b3.evaluate(ep)
                row["revelation_bounds"] = "Not applicable"
            else:
                try:
                    best, worst = _best_case(ep, revealed, actionable), _worst_case(ep, revealed)
                    rw = b3.evaluate(worst)
                    rb = b3.evaluate(best) if best is not None else None
                except ValueError as err:
                    row = b3.evaluate(ep)
                    row["revelation_bounds"] = f"Not computed ({err})"
                    rb = rw = None
                if rw is not None and rb is None:
                    row = rw
                    row["revelation_bounds"] = "Best case not computable (no documented actionable_from); worst-case verdict reported"
                elif rw is not None:
                    same = (rb["verdict"], rb["binding_clocks"]) == (rw["verdict"], rw["binding_clocks"])
                    if same:
                        row = rw
                        row["revelation_bounds"] = "Same verdict under best and worst case"
                        if rb.get("indeterminate_reason") != rw.get("indeterminate_reason"):
                            row["revelation_bounds"] += (f" (Indeterminate reason: best case {rb.get('indeterminate_reason')}, "
                                                         f"worst case {rw.get('indeterminate_reason')})")
                    else:
                        row = dict(rw)
                        row["engine_outcome"] = f"best: {rb['verdict']} [{rb['binding_clocks']}]; worst: {rw['verdict']} [{rw['binding_clocks']}]"
                        row["verdict"] = row["workbook_verdict"] = "Indeterminate"
                        row["binding_clocks"] = ""
                        row["indeterminate_reason"] = "revelation-sensitive"
                        row["reason"] = ("revelation-sensitive: verdict differs between the best case (revealed requirement known from the start) "
                                         f"= {rb['verdict']} {rb['binding_clocks'] or ''} and the worst case (no ex-ante duration) = {rw['verdict']} {rw['binding_clocks'] or ''}").strip()
                        row["revelation_bounds"] = "Different (revelation-sensitive)"
            row["protocol"] = PROTOCOL + (" SENSITIVITY: institutional merged into logistics" if merge_institutional else "")
            row["revealed_steps"] = "; ".join(sorted(revealed))
            row["claim_cap"] = _claim_cap(ep, row, meta)
            notes = row.pop("_claim_notes", [])
            if notes:
                extra = extra + ["claim ceiling: " + n for n in notes]
            row["related_party"] = rel.get(ep.id, "")
            if extra:
                row["flags"] = "; ".join(dict.fromkeys([f for f in [row.get("flags", "")] + extra if f]))
            rows.append(row)
    known = {r["episode"] for r in rows}
    st_ids = _low(steps)["episode"]
    for orphan in sorted({str(x).strip() for x in st_ids if not b3._blank(x)} - known):
        rows.append({"episode": orphan, "verdict": "Indeterminate", "workbook_verdict": "Indeterminate", "protocol": PROTOCOL,
                     "reason": "listed in Steps but has no row in Episodes", "flags": "input problems"})
    return pd.DataFrame(rows)


def layer_summary(layers: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    """Validate a Layers sheet (episode, layer, state, evidence) and return descriptive counts by layer and state.
    Descriptive only: exposure is never treated as cause."""
    df, probs = _low(layers), []
    for c in ("episode", "layer", "state"):
        if c not in df.columns:
            raise ValueError(f"sheet Layers is missing column {c}")
    rows = []
    for i, r in df.iterrows():
        eid, lay, st = _txt(r.get("episode")), _txt(r.get("layer")).lower().replace(" ", "-"), _txt(r.get("state")).lower()
        if not eid:
            continue
        if lay not in LAYERS:
            probs.append(f"row {i + 2}: layer '{lay}' is not one of {', '.join(LAYERS)}")
            continue
        state = LAYER_STATES.get(st)
        if state is None:
            probs.append(f"row {i + 2}: state '{st}' is not Activated, Exposed, Not present or Unknown")
            continue
        if state == "Activated" and not _txt(r.get("evidence")):
            probs.append(f"row {i + 2}: Activated needs a dated, episode-linked evidence reference")
        rows.append((eid, lay, state))
    t = pd.DataFrame(rows, columns=["episode", "layer", "state"])
    dup = t[t.duplicated(["episode", "layer"], keep=False)]
    if len(dup):
        probs.append("episode/layer coded more than once: " + ", ".join(sorted({f"{a}/{b}" for a, b in dup[["episode", "layer"]].values})))
    if not len(t):
        return pd.DataFrame(columns=["layer"] + list(dict.fromkeys(LAYER_STATES.values()))), probs
    tab = pd.crosstab(t["layer"], t["state"]).reindex(index=LAYERS, columns=list(dict.fromkeys(LAYER_STATES.values())), fill_value=0)
    return tab.reset_index(), probs


def concordance(study1: pd.DataFrame, study2: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Episode-by-episode comparison of Study 1 (v3.4) and Study 2a (4.0) verdicts.
    Returns (cross-tabulation, per-episode table with a provisional change attribution)."""
    a = _low(study1)[["episode", "verdict"] + [c for c in ["binding_clocks", "indeterminate_reason"] if c in _low(study1).columns]]
    b = _low(study2)
    keep = ["episode", "verdict"] + [c for c in ["binding_clocks", "indeterminate_reason", "revealed_steps", "claim_cap"] if c in b.columns]
    m = a.merge(b[keep], on="episode", how="outer", suffixes=(" (Study 1, v3.4)", " (Study 2a, 4.0)"))
    v1, v2 = "verdict (Study 1, v3.4)", "verdict (Study 2a, 4.0)"
    m["changed"] = m[v1].fillna("(absent)") != m[v2].fillna("(absent)")

    def why(r):
        if not r["changed"]:
            return ""
        if pd.isna(r[v1]) or pd.isna(r[v2]):
            return "episode present in one study only (re-coded gates or levels)"
        if str(r.get("indeterminate_reason (Study 2a, 4.0)", "")) == "revelation-sensitive":
            return "revealed-in-process rule (5.2)"
        if "institutional" in str(r.get("binding_clocks (Study 2a, 4.0)", "")) or r[v2] == "Institution-binding":
            return "institutional clock separated from logistics (3, C5)"
        return "re-coded inputs (dates, ex-ante status, sources or gates) - check the coder log"
    m["provisional attribution of the change"] = m.apply(why, axis=1)
    tab = pd.crosstab(m[v1].fillna("(absent)"), m[v2].fillna("(absent)"))
    return tab, m


def krippendorff_alpha_nominal(data) -> float:
    """Krippendorff's alpha for nominal data. ``data``: units x coders (DataFrame or list of rows); blanks/None = missing.
    Units with fewer than two values are ignored."""
    df = pd.DataFrame(data)
    units = []
    for _, r in df.iterrows():
        vals = [str(v).strip() for v in r if not b3._blank(v)]
        if len(vals) >= 2:
            units.append(vals)
    if not units:
        return float("nan")
    cats = sorted({v for u in units for v in u})
    idx = {c: i for i, c in enumerate(cats)}
    k = len(cats)
    o = [[0.0] * k for _ in range(k)]
    for u in units:
        m = len(u)
        for i, x in enumerate(u):
            for j, y in enumerate(u):
                if i != j:
                    o[idx[x]][idx[y]] += 1.0 / (m - 1)
    n_c = [sum(o[c]) for c in range(k)]
    n = sum(n_c)
    if n <= 1:
        return float("nan")
    d_o = sum(o[c][d] for c in range(k) for d in range(k) if c != d) / n
    d_e = sum(n_c[c] * n_c[d] for c in range(k) for d in range(k) if c != d) / (n * (n - 1))
    if d_e == 0:
        return 1.0 if d_o == 0 else float("nan")
    return 1.0 - d_o / d_e


BLIND_DROP = ("verdict", "level", "gate", "claim", "tier", "reason", "flag", "outcome", "binding", "slack",
              "actionable", "sensitivity", "note", "interpret", "author", "fragile", "stable", "override", "pass", "result")
BLIND_SHEETS = ("episodes", "steps", "layers", "sources", "events", "event_extraction", "03_event_extraction")


def blind_packet(sheets: dict, seed: int = 0) -> tuple[dict, pd.DataFrame, list]:
    """Coder packet for blind coding (Protocol 4.0, 7.3).

    Keeps only input sheets, removes every column whose name refers to a verdict, level, gate, claim, reason,
    flag, note or other researcher interpretation, and replaces episode codes by random packet codes.
    Returns (packet sheets, key table, list of removed columns). The key must stay with the principal investigator."""
    import random
    low = {str(k).strip().lower(): v for k, v in sheets.items()}
    keep = {k: v for k, v in low.items() if k in BLIND_SHEETS}
    if "episodes" not in keep or "steps" not in keep:
        raise ValueError("the workbook needs sheets Episodes and Steps")
    ids = sorted({_txt(x) for df in keep.values() if "episode" in _low(df).columns for x in _low(df)["episode"] if _txt(x)})
    codes = [f"P{i + 1:03d}" for i in range(len(ids))]
    rng = random.Random(seed)
    rng.shuffle(codes)
    key = dict(zip(ids, codes))
    removed, out = [], {}
    for name, df in keep.items():
        d = _low(df).copy()
        drop = [c for c in d.columns if c != "episode" and any(w in c for w in BLIND_DROP)]
        removed += [f"{name}.{c}" for c in drop]
        d = d.drop(columns=drop)
        if "episode" in d.columns:
            d["episode"] = d["episode"].map(lambda x: key.get(_txt(x), _txt(x)))
        out[name.title()] = d
    return out, pd.DataFrame({"episode": list(key), "packet_code": list(key.values())}), removed
