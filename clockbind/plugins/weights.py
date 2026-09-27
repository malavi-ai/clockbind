"""Paper 3: generalized overlap weighting for multi-arm architecture, with outcome-blind
estimability gates and cluster-robust / cluster-bootstrap inference.

Two-stage use (keeps the design stage outcome-blind):
  clockbind weights diagnose  --data ... --treatment ... --covariates ... --cluster ... [--gates gates.json]
  clockbind weights estimate  --data ... (same) --outcome ... --contrast "A:0.5,B:0.5,C:-0.5,D:-0.5"
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from ..core.io import load_data, require_columns, write_tables
from ..core.plugin import Plugin
from ..core.provenance import RunLog, env_seed
from ..stats import weights as W
from ._common import add_common, load_json, split_list


def _prepare(a, run, need_outcome: bool):
    df = load_data(a.data)
    covs = split_list(a.covariates)
    cols = [a.treatment, a.cluster] + covs + ([a.outcome] if need_outcome else [])
    require_columns(df, cols)
    d = df[cols].dropna()
    if len(d) < len(df):
        run.warn(f"{len(df) - len(d)} rows dropped for missing values. Pre-specify a missing-data rule; do not rely on this default.")
    levels = split_list(a.levels) or sorted(d[a.treatment].unique().tolist(), key=str)
    fit = W.fit_ps(d, a.treatment, covs, levels)
    for n in fit.notes:
        run.warn(n)
    w = W.gow_weights(fit)
    return d, covs, levels, fit, w


def _diagnostics(a, run, d, covs, fit, w):
    ess_t = W.ess_table(fit, w, d[a.cluster].to_numpy())
    bal = W.balance_table(d, fit, w, covs)
    arms_needed = None
    if getattr(a, "contrast", None):
        c = W.parse_contrast(a.contrast, fit.levels)
        arms_needed = [lv for lv, ci in zip(fit.levels, c) if ci != 0]
    gates = W.estimability_gates(ess_t, bal, load_json(a.gates), arms_needed)
    return ess_t, bal, gates


def cmd_diagnose(a):
    with RunLog(a.out, "weights", "diagnose", vars(a), None) as run:
        run.add_input(a.data)
        if a.gates:
            run.add_input(a.gates, "gates")
        d, covs, levels, fit, w = _prepare(a, run, need_outcome=False)
        ess_t, bal, gates = _diagnostics(a, run, d, covs, fit, w)
        verdict = "ESTIMABLE" if bool(gates["pass"].all()) else "NON-ESTIMABLE"
        run.note("verdict", verdict)
        run.note("outcome_used", False)
        wt = pd.DataFrame({"row": d.index, "arm": [levels[k] for k in fit.z], "weight": w,
                           **{f"ps_{lv}": fit.ps[:, k] for k, lv in enumerate(levels)}}).set_index("row")
        write_tables(run, {"verdict": pd.DataFrame({"verdict": [verdict]}), "gates": gates, "ess": ess_t,
                           "balance": bal}, "diagnostics")
        wt.to_csv(run.path("weights.csv")); run.add_output(run.path("weights.csv"))
        print(f"Design-stage verdict: {verdict} (outcome not read)")


def cmd_estimate(a):
    seed = env_seed(a.seed) if a.bootstrap else a.seed
    with RunLog(a.out, "weights", "estimate", vars(a), seed) as run:
        run.add_input(a.data)
        d, covs, levels, fit, w = _prepare(a, run, need_outcome=True)
        ess_t, bal, gates = _diagnostics(a, run, d, covs, fit, w)
        ok = bool(gates["pass"].all())
        verdict = "ESTIMABLE" if ok else "NON-ESTIMABLE"
        run.note("verdict", verdict)
        tables = {"verdict": pd.DataFrame({"verdict": [verdict]}), "gates": gates, "ess": ess_t, "balance": bal}
        if not ok and not a.force:
            print("Gates failed: outcome analysis NOT run (use --force only for exploratory, clearly labelled work).")
            write_tables(run, tables, "estimate")
            return 2
        if not ok:
            run.warn("Gates failed but --force used: results are EXPLORATORY and must not be reported as confirmatory.")
        c = W.parse_contrast(a.contrast, levels)
        y = d[a.outcome].to_numpy(float)
        est, means = W.estimate_contrast(y, fit, w, d[a.cluster].to_numpy(), c, a.vcov)
        tables["arm_means"] = means
        tables["contrast"] = pd.DataFrame([{"contrast": a.contrast, **est}]).set_index("contrast")
        if a.bootstrap:
            bs = W.cluster_bootstrap(d, a.treatment, covs, a.outcome, a.cluster, a.contrast, levels, B=a.bootstrap, seed=seed)
            tables["cluster_bootstrap"] = pd.DataFrame([{k: (json.dumps(v) if isinstance(v, dict) else v) for k, v in bs.items()}])
        write_tables(run, tables, "estimate")
        print(tables["contrast"].to_string())


class Weights(Plugin):
    name = "weights"
    help = "Paper 3: multi-arm generalized overlap weights, estimability gates, cluster-robust contrasts"

    def register(self, sub):
        def base(p):
            add_common(p)
            p.add_argument("--treatment", required=True, help="Architecture (arm) column")
            p.add_argument("--covariates", required=True, help="Comma-separated baseline covariates (pre-architecture only)")
            p.add_argument("--cluster", required=True, help="Firm identifier")
            p.add_argument("--levels", help="Comma-separated arm order (default: sorted)")
            p.add_argument("--gates", help="JSON file with gate thresholds (frozen before outcomes)")
            return p

        p = base(sub.add_parser("diagnose", help="Design stage: PS, weights, balance, ESS, gates. Does NOT read the outcome."))
        p.add_argument("--contrast", help="Optional: restrict gates to arms used by this contrast")
        p.set_defaults(func=cmd_diagnose)

        p = base(sub.add_parser("estimate", help="Outcome stage: weighted arm means and a contrast"))
        p.add_argument("--outcome", required=True)
        p.add_argument("--contrast", required=True, help="'A-B' or 'A:0.5,B:0.5,C:-0.5,D:-0.5' (sums to 0)")
        p.add_argument("--vcov", default="CR2", choices=["CR0", "CR1", "CR2"])
        p.add_argument("--bootstrap", type=int, default=0, help="Cluster-bootstrap replications (re-fits PS each time)")
        p.add_argument("--seed", type=int, default=None)
        p.add_argument("--force", action="store_true", help="Run even if gates fail (exploratory only)")
        p.set_defaults(func=cmd_estimate)


PLUGIN = Weights()
