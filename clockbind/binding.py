"""Counterfactual critical-path engine for "which clock binds?".

Registered rule (Bridge protocol, decisions of 27 September 2026):

* A clock binds if the required event R would have occurred by the end of the
  action window tW had that clock met its ex-ante expected duration, other
  clocks as documented. Only ex-ante expected durations are used.
* Jointly binding: no single correction is sufficient; the specified combined
  correction is sufficient for R to occur by tW.
* Sign stability: the verdict is computed at the earliest and at the latest
  admissible date bounds. If the two verdicts differ (for example because the
  decisive slack changes sign), the episode is Indeterminate.
* Finance actionability (finance usable in time, slack >= 0) is reported
  separately from binding.

Model. Each episode is a dependency network of steps. Each step belongs to a
clock (finance, supplier, logistics, installation/set-up, other), has zero or
more predecessor steps, a documented finish time given as an interval
[earliest, latest], and optionally an ex-ante expected duration. A step becomes
ready when all its predecessors have finished (or at the episode anchor if it
has none). Its realised duration is finish - ready, so waiting before a step is
attributed to that step's clock. "As documented" keeps the realised duration;
"corrected" uses min(realised, expected).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from itertools import combinations, product

import pandas as pd

EPS = 1e-9
CLOCK_LABELS = {
    "finance": "Finance-binding",
    "supplier": "Non-finance: supplier",
    "logistics": "Non-finance: logistics",
    "installation": "Non-finance: installation/set-up",
    "installation/set-up": "Non-finance: installation/set-up",
    "set-up": "Non-finance: installation/set-up",
    "other": "Non-finance: other",
}
STEP_COLUMNS = ["episode", "step", "clock", "predecessors", "finish_earliest", "finish_latest", "expected_days", "source", "note"]
EPISODE_COLUMNS = ["episode", "anchor_earliest", "anchor_latest", "tw_earliest", "tw_latest", "r_step", "note"]


_DMY = re.compile(r"^\s*(\d{1,2})\.(\d{1,2})\.(\d{4})\.?(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?)?\s*$")   # 03.02.2026 (day first)
_YMD_DOT = re.compile(r"^\s*(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.?(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?)?\s*$")  # 2026. 02. 03. (Hungarian)
EXCEL_EPOCH = pd.Timestamp("1899-12-30")


def _days(v):
    """Date/time -> float days since 1970-01-01; blank -> None.

    Accepted: ISO text (2026-02-03, 2026-02-03 14:30, with or without a time-zone offset), Excel date cells,
    Excel serial numbers, day-first dotted dates (03.02.2026 = 3 February) and Hungarian year-first dates
    (2026. 02. 03.). Slashed dates (02/03/2026) are rejected because day and month order is ambiguous."""
    if v is None or (isinstance(v, float) and pd.isna(v)) or (isinstance(v, str) and not v.strip()):
        return None
    if isinstance(v, bool):
        raise ValueError(f"not a date/time: {v!r}")
    if isinstance(v, (int, float)) or (hasattr(v, "dtype") and pd.api.types.is_number(v)):
        x = float(v)
        if not 20000 <= x <= 80000:
            raise ValueError(f"not a date/time: {v!r} (numbers are read as Excel date serials, 1954–2119)")
        v = EXCEL_EPOCH + pd.Timedelta(days=x)
    elif isinstance(v, str):
        s = v.strip()
        m = _DMY.match(s) or _YMD_DOT.match(s)
        if m:
            a, b, c, hh, mm, ss = m.groups()
            y, mo, d = (int(c), int(b), int(a)) if m.re is _DMY else (int(a), int(b), int(c))
            try:
                v = pd.Timestamp(year=y, month=mo, day=d, hour=int(hh or 0), minute=int(mm or 0), second=int(ss or 0))
            except ValueError:
                raise ValueError(f"not a valid date: {s!r}")
        elif re.search(r"\d{1,2}/\d{1,2}/\d{2,4}", s):
            raise ValueError(f"ambiguous date {s!r}: write it as YYYY-MM-DD (day/month order differs between countries)")
        elif re.fullmatch(r"\d+(\.\d+)?", s):
            return _days(float(s))
    try:
        ts = pd.Timestamp(v)
    except Exception:
        raise ValueError(f"not a date/time: {v!r}")
    if pd.isna(ts):
        return None
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return (ts - pd.Timestamp("1970-01-01")) / pd.Timedelta(days=1)


def _num(v):
    if v is None or (isinstance(v, float) and pd.isna(v)) or (isinstance(v, str) and not v.strip()):
        return None
    return float(v)


@dataclass
class Step:
    name: str
    clock: str
    preds: list
    f_lo: float | None
    f_hi: float | None
    expected: float | None


@dataclass
class Episode:
    id: str
    anchor: tuple
    tw: tuple
    r_step: str
    steps: dict = field(default_factory=dict)
    problems: list = field(default_factory=list)


_TZ = re.compile(r"(Z|[+-]\d{2}:?\d{2})\s*$")


def _has_tz(v):
    if isinstance(v, pd.Timestamp) or hasattr(v, "tzinfo"):
        return getattr(v, "tzinfo", None) is not None
    return isinstance(v, str) and bool(re.search(r"\d{1,2}:\d{2}", v)) and bool(_TZ.search(v.strip()))


def _blank(v):
    return v is None or (isinstance(v, float) and pd.isna(v)) or (isinstance(v, str) and not v.strip())


def build_episodes(episodes: pd.DataFrame, steps: pd.DataFrame) -> list[Episode]:
    episodes = episodes.rename(columns=lambda c: str(c).strip().lower())
    steps = steps.rename(columns=lambda c: str(c).strip().lower())
    for need, frame, cols in (("Episodes", episodes, ["episode", "anchor_earliest", "tw_earliest", "r_step"]),
                              ("Steps", steps, ["episode", "step", "clock", "finish_earliest"])):
        miss = [c for c in cols if c not in frame.columns]
        if miss:
            raise ValueError(f"sheet {need} is missing column(s): {', '.join(miss)} (see `clockbind binding template`)")
    out = []
    ids = [str(x).strip() for x in episodes["episode"] if not _blank(x)]
    dup = sorted({x for x in ids if ids.count(x) > 1})
    for _, e in episodes.iterrows():
        eid = str(e.get("episode", "")).strip()
        if not eid or eid.lower() == "nan":
            continue
        ep = Episode(eid, (None, None), (None, None), str(e.get("r_step", "") or "").strip())
        if eid in dup:
            ep.problems.append(f"episode code {eid} appears more than once in Episodes")
        raw = [e.get("anchor_earliest"), e.get("anchor_latest"), e.get("tw_earliest"), e.get("tw_latest")]
        sub = steps[steps["episode"].astype(str).str.strip() == eid]
        raw += list(sub.get("finish_earliest", [])) + list(sub.get("finish_latest", []))
        raw = [x for x in raw if not _blank(x)]
        if raw and any(_has_tz(x) for x in raw) and not all(_has_tz(x) for x in raw):
            ep.problems.append("some times have a time-zone offset and others do not; use one convention for the whole episode")
        try:
            a_lo = _days(e.get("anchor_earliest"))
            a_hi = _days(e.get("anchor_latest")) if _days(e.get("anchor_latest")) is not None else a_lo
            t_lo = _days(e.get("tw_earliest"))
            t_hi = _days(e.get("tw_latest")) if _days(e.get("tw_latest")) is not None else t_lo
            ep.anchor, ep.tw = (a_lo, a_hi), (t_lo, t_hi)
        except ValueError as err:
            ep.problems.append(str(err))
        for _, s in steps[steps["episode"].astype(str).str.strip() == eid].iterrows():
            name = str(s.get("step", "")).strip()
            if not name or name.lower() == "nan":
                continue
            preds = [p.strip() for p in str(s.get("predecessors", "") or "").replace(",", ";").split(";") if p.strip() and p.strip().lower() != "nan"]
            try:
                lo = _days(s.get("finish_earliest"))
                hi = _days(s.get("finish_latest"))
                hi = lo if hi is None else hi
                exp = _num(s.get("expected_days"))
            except ValueError as err:
                ep.problems.append(f"step {name}: {err}")
                lo = hi = exp = None
            if lo is not None and hi is not None and hi < lo:
                ep.problems.append(f"step {name}: latest finish is before earliest finish")
            if exp is not None and exp < 0:
                ep.problems.append(f"step {name}: negative expected duration")
            clock = str(s.get("clock", "other") or "other").strip().lower()
            if name in ep.steps:
                ep.problems.append(f"duplicate step name {name}")
            ep.steps[name] = Step(name, clock, preds, lo, hi, exp)
        out.append(ep)
    return out


def _topo(ep: Episode) -> list[str]:
    order, state = [], {}

    def visit(n, stack=()):
        if state.get(n) == 2:
            return
        if state.get(n) == 1:
            raise ValueError(f"dependency cycle through {' -> '.join(stack + (n,))}")
        state[n] = 1
        for p in ep.steps[n].preds:
            if p not in ep.steps:
                raise ValueError(f"step {n}: unknown predecessor {p}")
            visit(p, stack + (n,))
        state[n] = 2
        order.append(n)

    for n in ep.steps:
        visit(n)
    return order


def _ancestors(ep: Episode, target: str) -> set:
    seen, todo = set(), [target]
    while todo:
        n = todo.pop()
        if n in seen:
            continue
        seen.add(n)
        todo += ep.steps[n].preds
    return seen


class _Scenario:
    """One consistent set of dates (all earliest or all latest bounds)."""

    def __init__(self, ep: Episode, order, anc, bound: str):
        self.ep, self.order, self.anc = ep, [n for n in order if n in anc], anc
        pick = (lambda lo, hi: lo) if bound == "earliest" else (lambda lo, hi: hi)
        self.anchor = pick(*ep.anchor)
        self.tw = pick(*ep.tw)
        self.finish = {n: pick(ep.steps[n].f_lo, ep.steps[n].f_hi) for n in self.order}
        self.realised, self.warn = {}, []
        for n in self.order:
            ready = max([self.finish[p] for p in ep.steps[n].preds], default=self.anchor)
            r = self.finish[n] - ready
            if r < -EPS:
                self.warn.append(f"step {n} finishes before it is ready at the {bound} bound; realised duration set to 0")
                r = 0.0
            self.realised[n] = max(r, 0.0)

    def simulate(self, dur: dict) -> float:
        fin = {}
        for n in self.order:
            ready = max([fin[p] for p in self.ep.steps[n].preds], default=self.anchor)
            fin[n] = ready + dur[n]
        return fin[self.ep.r_step]

    def durations(self, correct: set, reactive: bool = False) -> dict:
        dur = dict(self.realised)
        corrected = {n for n in self.order if self.ep.steps[n].clock in correct}
        if reactive and corrected:
            down = set()
            for n in self.order:
                if any(p in corrected or p in down for p in self.ep.steps[n].preds):
                    down.add(n)
            corrected |= {n for n in down if self.ep.steps[n].expected is not None}
        for n in corrected:
            e = self.ep.steps[n].expected
            if e is not None:
                dur[n] = min(dur[n], e)
        return dur

    def slack(self, correct: set = frozenset(), reactive=False) -> float:
        return self.tw - self.simulate(self.durations(set(correct), reactive))

    def finance_slack(self):
        fin_steps = [n for n in self.order if self.ep.steps[n].clock == "finance"]
        if not fin_steps:
            return None, "no finance step"
        succ = {n: [m for m in self.order if n in self.ep.steps[m].preds] for n in self.order}
        lf = {self.ep.r_step: self.tw}
        for n in reversed(self.order):
            if n == self.ep.r_step:
                continue
            vals = []
            for m in succ[n]:
                e = self.ep.steps[m].expected
                if m not in lf or e is None:
                    return None, f"ex-ante duration missing for {m}"
                vals.append(lf[m] - e)
            if vals:
                lf[n] = min(vals)
        return min(lf[n] - self.finish[n] for n in fin_steps if n in lf), ""


def _verdict(sc: _Scenario, clocks: list, reactive=False) -> dict:
    base = sc.slack()
    if base >= -EPS:
        return {"verdict": "Non-binding", "clocks": [], "decisive_slack": base, "untestable": []}
    testable = [c for c in clocks if all(sc.ep.steps[n].expected is not None for n in sc.order if sc.ep.steps[n].clock == c)]
    untestable = [c for c in clocks if c not in testable]
    singles = [c for c in testable if sc.slack({c}, reactive) >= -EPS]
    if singles:
        slack = max(sc.slack({c}, reactive) for c in singles)
        if len(singles) == 1:
            label = CLOCK_LABELS.get(singles[0], "Non-finance: other")
        else:
            label = "Multiple sufficient corrections"
        return {"verdict": label, "clocks": singles, "decisive_slack": slack, "untestable": untestable}
    if untestable:
        return {"verdict": "Indeterminate", "clocks": [], "decisive_slack": base, "untestable": untestable,
                "reason": "ex-ante duration not documented for: " + ", ".join(untestable)}
    pairs = [p for p in combinations(testable, 2) if sc.slack(set(p), reactive) >= -EPS]
    if pairs:
        slack = max(sc.slack(set(p), reactive) for p in pairs)
        return {"verdict": "Jointly binding", "clocks": [" + ".join(p) for p in pairs], "decisive_slack": slack, "untestable": []}
    if len(testable) > 2 and sc.slack(set(testable), reactive) >= -EPS:
        return {"verdict": "Jointly binding", "clocks": [" + ".join(testable)], "decisive_slack": sc.slack(set(testable), reactive), "untestable": []}
    return {"verdict": "Window infeasible at ex-ante durations", "clocks": [], "decisive_slack": sc.slack(set(testable), reactive), "untestable": []}


def _key(v):
    return (v["verdict"], tuple(sorted(v["clocks"])))


WORKBOOK_VERDICTS = {"Finance-binding", "Non-finance: supplier", "Non-finance: logistics", "Non-finance: installation/set-up",
                     "Non-finance: other", "Jointly binding", "Non-binding", "Indeterminate"}


def evaluate(ep: Episode, corner_limit: int = 10) -> dict:
    row = {"episode": ep.id, "verdict": "Indeterminate", "workbook_verdict": "Indeterminate", "binding_clocks": "",
           "sign_stable": "", "decisive_slack_earliest_days": None, "decisive_slack_latest_days": None,
           "baseline_slack_earliest_days": None, "baseline_slack_latest_days": None,
           "finance_slack_earliest_days": None, "finance_slack_latest_days": None, "finance_actionable": "",
           "reactive_sensitivity": "", "corner_check": "", "flags": "", "reason": ""}
    flags = list(ep.problems)
    try:
        if not ep.steps:
            raise ValueError("no steps recorded")
        if ep.r_step not in ep.steps:
            raise ValueError(f"required event step '{ep.r_step}' is not among the steps")
        order = _topo(ep)
        anc = _ancestors(ep, ep.r_step)
    except ValueError as err:
        row["reason"] = str(err)
        row["flags"] = "; ".join(flags)
        return row
    missing = [n for n in anc if ep.steps[n].f_lo is None]
    if ep.tw[0] is None:
        missing.append("tW")
    if ep.anchor[0] is None:
        missing.append("anchor")
    if missing or ep.problems:
        row["reason"] = ("not documented: " + ", ".join(sorted(missing))) if missing else "input problems"
        row["flags"] = "; ".join(flags)
        return row
    clocks = sorted({ep.steps[n].clock for n in anc})
    scen = {b: _Scenario(ep, order, anc, b) for b in ("earliest", "latest")}
    for sc in scen.values():
        flags += sc.warn
    v = {b: _verdict(sc, clocks) for b, sc in scen.items()}
    for b in ("earliest", "latest"):
        row[f"decisive_slack_{b}_days"] = round(v[b]["decisive_slack"], 4)
        row[f"baseline_slack_{b}_days"] = round(scen[b].slack(), 4)
        fs, why = scen[b].finance_slack()
        row[f"finance_slack_{b}_days"] = None if fs is None else round(fs, 4)
        if fs is None and why and why != "no finance step":
            flags.append(f"finance slack not computable ({why})")
    fe, fl = row["finance_slack_earliest_days"], row["finance_slack_latest_days"]
    if fe is None or fl is None:
        row["finance_actionable"] = "N/A" if all(ep.steps[n].clock != "finance" for n in anc) else "Not computable"
    elif fe >= -EPS and fl >= -EPS:
        row["finance_actionable"] = "Yes"
    elif fe < -EPS and fl < -EPS:
        row["finance_actionable"] = "No"
    else:
        row["finance_actionable"] = "Unstable across bounds"
    stable = _key(v["earliest"]) == _key(v["latest"])
    row["sign_stable"] = "Yes" if stable else "No"
    if stable:
        row["verdict"] = v["earliest"]["verdict"]
        row["binding_clocks"] = "; ".join(v["earliest"]["clocks"])
        row["reason"] = v["earliest"].get("reason", "")
        if v["earliest"]["untestable"] and row["verdict"] != "Indeterminate":
            flags.append("clocks without an ex-ante duration could not be tested: " + ", ".join(v["earliest"]["untestable"]))
    else:
        row["verdict"] = "Indeterminate"
        row["reason"] = (f"sign-stability rule: verdict at earliest bounds = {v['earliest']['verdict']} "
                         f"{v['earliest']['clocks'] or ''}; at latest bounds = {v['latest']['verdict']} {v['latest']['clocks'] or ''}")
    if row["verdict"] in WORKBOOK_VERDICTS:
        row["workbook_verdict"] = row["verdict"]
    else:
        row["workbook_verdict"] = ""
        flags.append(f"AUTHOR DECISION REQUIRED: '{row['verdict']}' has no category in the workbook list")
    # reactive-downstream sensitivity (does not change the verdict)
    if stable and row["verdict"] not in ("Non-binding", "Indeterminate"):
        rv = {b: _verdict(sc, clocks, reactive=True) for b, sc in scen.items()}
        same = all(_key(rv[b]) == _key(v[b]) for b in rv)
        row["reactive_sensitivity"] = "Unchanged" if same else f"Changes to {rv['earliest']['verdict']} {rv['earliest']['clocks'] or ''}".strip()
    else:
        row["reactive_sensitivity"] = "Not applicable"
    # diagnostic: every combination of interval bounds (does not change the verdict)
    fields = [("anchor", ep.anchor), ("tw", ep.tw)] + [(n, (ep.steps[n].f_lo, ep.steps[n].f_hi)) for n in anc]
    varying = [f for f in fields if abs(f[1][1] - f[1][0]) > EPS]
    if not varying:
        row["corner_check"] = "No intervals (exact dates)"
    elif len(varying) > corner_limit:
        row["corner_check"] = f"Not run ({len(varying)} interval dates > {corner_limit})"
    else:
        keys = set()
        for combo in product((0, 1), repeat=len(varying)):
            choice = {name: bounds[i] for (name, bounds), i in zip(varying, combo)}
            sc = _Scenario(ep, order, anc, "earliest")
            sc.anchor = choice.get("anchor", ep.anchor[0])
            sc.tw = choice.get("tw", ep.tw[0])
            sc.finish = {n: choice.get(n, ep.steps[n].f_lo) for n in sc.order}
            sc.realised = {}
            for n in sc.order:
                ready = max([sc.finish[p] for p in ep.steps[n].preds], default=sc.anchor)
                sc.realised[n] = max(sc.finish[n] - ready, 0.0)
            keys.add(_key(_verdict(sc, clocks)))
        row["corner_check"] = "Stable at every bound combination" if len(keys) == 1 else f"Varies across {len(keys)} outcomes (diagnostic only)"
    row["flags"] = "; ".join(dict.fromkeys(flags))
    return row


def evaluate_all(episodes: pd.DataFrame, steps: pd.DataFrame) -> pd.DataFrame:
    eps = build_episodes(episodes, steps)
    rows = [evaluate(ep) for ep in eps]
    known = {ep.id for ep in eps}
    st_ids = steps.rename(columns=lambda c: str(c).strip().lower())["episode"]
    for orphan in sorted({str(x).strip() for x in st_ids if not _blank(x)} - known):
        rows.append({"episode": orphan, "verdict": "Indeterminate", "workbook_verdict": "Indeterminate",
                     "reason": "listed in Steps but has no row in Episodes", "flags": "input problems"})
    return pd.DataFrame(rows)
