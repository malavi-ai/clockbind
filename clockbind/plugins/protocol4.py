"""clockbind p4: Protocol 4.0 (Bridge Study 2a) — six clocks, revealed-in-process rule, claim ceiling,
blind coder packets, concordance with Study 1 and Krippendorff's alpha."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..binding import evaluate_all as evaluate_v3
from ..binding4 import (EPISODE_COLUMNS_V4, LAYERS, STEP_COLUMNS_V4, blind_packet, concordance, evaluate_all_v4,
                        krippendorff_alpha_nominal, layer_summary)
from ..core.plugin import Plugin
from ..core.provenance import RunLog

GUIDE = [
    ("Protocol", "Bridge Protocol 4.0 (Study 2a). The registered v3.4 rule is unchanged and still available as `clockbind binding run`."),
    ("Steps: clock", "finance, payment, fulfilment, logistics, institutional or operational-readiness. customs, origin, classification, clearance, duty and release map to institutional."),
    ("Steps: ex_ante_status", "documented | revealed | undocumented. Blank = documented if expected_days is filled, otherwise undocumented. An expected duration always prevails (rule 4.2)."),
    ("Steps: revealed_at", "Date of the first dated document that shows the requirement (rule 4.1). Required when ex_ante_status = revealed."),
    ("Steps: actionable_from", "Earliest date at which the action could have started, supported by a dated document (e.g. the shipment or invoice existed). Without it the best case is not computed (rule 5.2)."),
    ("Steps: direct_record", "Yes if the cited source directly records the timing of this step (e.g. a customs declaration for release, a bank confirmation for payment). Used for the claim ceiling (rule 6.3)."),
    ("Steps: source_class", "internal | counterparty | third-party | public-authority (used for the claim ceiling, rule 6.3)."),
    ("Steps: contemporaneity", "contemporaneous | retrospective."),
    ("Episodes: related_party", "Yes if the researcher controls both buyer and seller (rule 6.4)."),
    ("Layers sheet", "episode, layer (focal-firm, counterparty, intermediary, institutional, environmental), state (Activated, Exposed, Not present, Unknown), evidence. Descriptive only."),
    ("Rule 5.2", "Revealed steps: worst case = no ex-ante duration; best case (only with a documented actionable_from) = start at max(ready, actionable_from) and take the post-revelation execution time. Different verdicts -> Indeterminate, revelation-sensitive."),
    ("Rule 6.3", "A positive binding verdict is capped at 'consistent with' unless every binding clock has a step whose timing is recorded directly by a non-internal source. The verdict is not changed."),
    ("Tests sheet", "Pre-specified process-tracing tests (rule 5.6): episode, rival, hypothesis, observation expected if true, observation expected if false, test type, inference permitted. Filled before coding."),
]


def _sheets(path):
    x = pd.read_excel(path, sheet_name=None, dtype=object)
    return {k.strip().lower(): v for k, v in x.items()}


def _need(sh, *names):
    for n in names:
        if n not in sh:
            raise SystemExit(f"The workbook needs a sheet named '{n.title()}' (see `clockbind p4 template`).")


def cmd_run(a):
    sh = _sheets(a.data)
    _need(sh, "episodes", "steps")
    res = evaluate_all_v4(sh["episodes"], sh["steps"], zero_as_documented=a.zero_as_documented,
                          merge_institutional=a.merge_institutional)
    sens = a.zero_as_documented or a.merge_institutional
    with RunLog(a.out, "p4", "run", vars(a), None) as run:
        run.add_input(a.data, "timeline")
        if sens:
            run.warn("SENSITIVITY RUN: not the primary Protocol 4.0 verdicts.")
        out = run.path("p4_verdicts_SENSITIVITY.xlsx" if sens else "p4_verdicts.xlsx")
        summary = res["verdict"].value_counts().rename_axis("verdict").reset_index(name="episodes") if len(res) else pd.DataFrame(columns=["verdict", "episodes"])
        with pd.ExcelWriter(out, engine="openpyxl") as xw:
            res.to_excel(xw, sheet_name="Verdicts", index=False)
            summary.to_excel(xw, sheet_name="Summary", index=False)
            if "layers" in sh:
                tab, probs = layer_summary(sh["layers"])
                tab.to_excel(xw, sheet_name="Layers (descriptive)", index=False)
                pd.DataFrame({"layer check": probs or ["no problems"]}).to_excel(xw, sheet_name="Layer checks", index=False)
            if a.excluding_related_party and "related_party" in res.columns:
                sub = res[res["related_party"] != "Yes"]
                sub["verdict"].value_counts().rename_axis("verdict").reset_index(name="episodes").to_excel(
                    xw, sheet_name="Excl. related party", index=False)
            pd.DataFrame(GUIDE, columns=["item", "meaning"]).to_excel(xw, sheet_name="Rule", index=False)
        run.add_output(out)
        run.note("episodes", int(len(res)))
        cols = [c for c in ["episode", "verdict", "indeterminate_reason", "binding_clocks", "revealed_steps", "claim_cap"] if c in res.columns]
        print(res[cols].to_string(index=False) if len(res) else "No episodes found.")
    return 0


def cmd_template(a):
    ep = pd.DataFrame([{"episode": "EX-01", "anchor_earliest": "2026-01-05", "anchor_latest": "", "tw_earliest": "2026-01-14",
                        "tw_latest": "", "r_step": "operational", "related_party": "No", "note": "Synthetic example: delete before use"}],
                      columns=EPISODE_COLUMNS_V4)
    rows = [
        ("funds_usable", "finance", "", "2026-01-06", 2, "documented", "", "", "third-party"),
        ("dispatch", "fulfilment", "funds_usable", "2026-01-08", 2, "documented", "", "", "counterparty"),
        ("border_transit", "logistics", "dispatch", "2026-01-10", 2, "documented", "", "", "third-party"),
        ("origin_proof", "institutional", "border_transit", "2026-01-15", "", "revealed", "2026-01-12", "2026-01-10", "public-authority"),
        ("operational", "operational-readiness", "origin_proof", "2026-01-16", 1, "documented", "", "", "internal"),
    ]
    st = pd.DataFrame([{"episode": "EX-01", "step": s, "clock": c, "predecessors": p, "finish_earliest": f, "finish_latest": "",
                        "expected_days": e, "zero_documented": "", "ex_ante_status": x, "revealed_at": r, "actionable_from": af,
                        "source_class": sc, "direct_record": "Yes", "contemporaneity": "contemporaneous", "source": "DOC-000"}
                       for s, c, p, f, e, x, r, af, sc in rows], columns=STEP_COLUMNS_V4)
    tests = pd.DataFrame([{"episode": "EX-01", "rival": "institutional", "hypothesis": "Release was delayed by the origin-proof requirement",
                           "expected_if_true": "Dated broker request for origin proof precedes release; release follows its receipt",
                           "expected_if_false": "Release documented before or independently of the origin document",
                           "test_type": "hoop", "inference_permitted": "Pass: rival remains plausible; fail: rival eliminated"}])
    lay = pd.DataFrame([{"episode": "EX-01", "layer": L, "state": "Unknown", "evidence": ""} for L in LAYERS])
    with pd.ExcelWriter(a.output, engine="openpyxl") as xw:
        ep.to_excel(xw, sheet_name="Episodes", index=False)
        st.to_excel(xw, sheet_name="Steps", index=False)
        lay.to_excel(xw, sheet_name="Layers", index=False)
        tests.to_excel(xw, sheet_name="Tests", index=False)
        pd.DataFrame(GUIDE, columns=["item", "meaning"]).to_excel(xw, sheet_name="Guide", index=False)
    print(f"Protocol 4.0 template written: {a.output}")
    return 0


def cmd_blind(a):
    sh = pd.read_excel(a.data, sheet_name=None, dtype=object)
    packet, key, removed = blind_packet(sh, seed=a.seed)
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(a.output, engine="openpyxl") as xw:
        for n, d in packet.items():
            d.to_excel(xw, sheet_name=n[:31], index=False)
        pd.DataFrame(GUIDE, columns=["item", "meaning"]).to_excel(xw, sheet_name="Guide", index=False)
    with pd.ExcelWriter(a.key, engine="openpyxl") as xw:
        key.to_excel(xw, sheet_name="Key", index=False)
        pd.DataFrame({"removed column": removed or ["(none)"]}).to_excel(xw, sheet_name="Removed columns", index=False)
    print(f"Coder packet: {a.output} ({len(key)} episodes, {len(removed)} columns removed). KEY (keep private): {a.key}")
    return 0


def cmd_concordance(a):
    sh = _sheets(a.data)
    _need(sh, "episodes", "steps")
    s1 = pd.read_excel(a.study1, sheet_name=0, dtype=object) if a.study1 else evaluate_v3(sh["episodes"], sh["steps"])
    s2 = evaluate_all_v4(sh["episodes"], sh["steps"])
    tab, per = concordance(s1, s2)
    with RunLog(a.out, "p4", "concordance", vars(a), None) as run:
        run.add_input(a.data, "timeline (Study 2a)")
        if a.study1:
            run.add_input(a.study1, "Study 1 verdicts")
        out = run.path("p4_concordance.xlsx")
        with pd.ExcelWriter(out, engine="openpyxl") as xw:
            tab.to_excel(xw, sheet_name="Cross-tabulation")
            per.to_excel(xw, sheet_name="Per episode", index=False)
        run.add_output(out)
        print(tab.to_string())
        print(f"Changed verdicts: {int(per['changed'].sum())} of {len(per)}")
    return 0


def cmd_alpha(a):
    df = pd.read_excel(a.data, sheet_name=a.sheet or 0, dtype=object) if str(a.data).lower().endswith((".xlsx", ".xls")) else pd.read_csv(a.data, dtype=object)
    cols = [c.strip() for c in a.coders.split(",")]
    miss = [c for c in cols if c not in df.columns]
    if miss:
        raise SystemExit(f"coder column(s) not found: {', '.join(miss)}")
    rows = []
    groups = [("all items", df)] if not a.by else list(df.groupby(a.by))
    for g, d in groups:
        sub = d[cols]
        both = sub.dropna(how="any")
        raw = float((both.astype(str).nunique(axis=1) == 1).mean()) if len(both) else float("nan")
        rows.append({"item family": g, "units": int(len(sub)), "Krippendorff alpha (nominal)": round(krippendorff_alpha_nominal(sub), 4),
                     "raw agreement (complete units)": round(raw, 4)})
    res = pd.DataFrame(rows)
    print(res.to_string(index=False))
    if a.output:
        with pd.ExcelWriter(a.output, engine="openpyxl") as xw:
            res.to_excel(xw, sheet_name="Agreement", index=False)
            for g, d in groups:  # disagreement tables (rule 7.5); rare categories to be interpreted separately
                tab = pd.crosstab(d[cols[0]].fillna("(missing)"), d[cols[1]].fillna("(missing)"))
                tab.to_excel(xw, sheet_name=f"Disagreement {str(g)[:18]}")
            dis = pd.concat([d[d[cols].astype(str).nunique(axis=1) > 1] for _, d in groups]) if groups else pd.DataFrame()
            dis.to_excel(xw, sheet_name="Units with disagreement", index=False)
    return 0


class Protocol4(Plugin):
    name = "p4"
    help = "Bridge Protocol 4.0 (Study 2a): six clocks, revealed-in-process rule, claim ceiling, blind packets, concordance, Krippendorff's alpha"

    def register(self, sub):
        p = sub.add_parser("run", help="Protocol 4.0 verdicts per episode")
        p.add_argument("--data", required=True, help="Workbook with sheets Episodes, Steps (and optionally Layers)")
        p.add_argument("--out", default="clockbind_runs")
        p.add_argument("--zero-as-documented", action="store_true", help="SENSITIVITY: accept every ex-ante 0")
        p.add_argument("--merge-institutional", action="store_true", help="SENSITIVITY 10.2(c): institutional merged into logistics (v3.4 clock set)")
        p.add_argument("--excluding-related-party", action="store_true", help="add a summary excluding related-party episodes (10.2a)")
        p.set_defaults(func=cmd_run)
        p = sub.add_parser("template", help="Protocol 4.0 input template with a synthetic example")
        p.add_argument("--output", default="timeline_p4_template.xlsx")
        p.set_defaults(func=cmd_template)
        p = sub.add_parser("blind-packet", help="Coder packet without verdicts, levels, notes or interpretations; episode codes randomised")
        p.add_argument("--data", required=True)
        p.add_argument("--output", default="coder_packet.xlsx")
        p.add_argument("--key", default="coder_packet_KEY_private.xlsx")
        p.add_argument("--seed", type=int, default=0)
        p.set_defaults(func=cmd_blind)
        p = sub.add_parser("concordance", help="Study 1 (v3.4) versus Study 2a (4.0) verdicts, episode by episode")
        p.add_argument("--data", required=True, help="Study 2a timeline workbook (Protocol 4.0 inputs)")
        p.add_argument("--study1", help="Locked Study 1 verdict file (first sheet). If omitted, v3.4 is run on --data.")
        p.add_argument("--out", default="clockbind_runs")
        p.set_defaults(func=cmd_concordance)
        p = sub.add_parser("alpha", help="Krippendorff's alpha (nominal) and raw agreement between coders")
        p.add_argument("--data", required=True, help="CSV or Excel: one row per unit, one column per coder")
        p.add_argument("--coders", required=True, help="coder columns, comma-separated")
        p.add_argument("--by", help="optional column with the item family (alpha per family)")
        p.add_argument("--sheet")
        p.add_argument("--output")
        p.set_defaults(func=cmd_alpha)


PLUGIN = Protocol4()
