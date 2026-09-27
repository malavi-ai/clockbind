"""ADEMP simulation runner (Aims, Data-generating mechanisms, Estimands, Methods,
Performance measures). The protocol JSON is hashed into the manifest, so the
protocol can be frozen and cited before any run.

Built-in data-generating mechanism: "paper3" (clustered 4-arm architecture,
binary outcome, overlap-weighted contrast with estimability gates).

Protocol example: see examples/ademp_paper3_null.json
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..core.io import write_tables
from ..core.plugin import Plugin
from ..core.provenance import RunLog, env_seed
from ..dgp import paper3
from ..stats import weights as W
from ..stats.simulation import performance
from ._common import add_common, load_json

REQUIRED = ["aims", "dgm", "estimand", "methods", "performance", "n_reps"]


def _one_rep_paper3(params, method, contrast_spec, gates, rng, apply_gates=True):
    df, _ = paper3.simulate(params, rng)
    levels = list(params.get("arm_labels", paper3.DEFAULTS["arm_labels"]))
    if df["arm"].nunique() < len(levels):
        return None, "arm_missing"
    try:
        fit = W.fit_ps(df, "arm", ["x1", "x2", "x3"], levels)
    except Exception:
        return None, "ps_error"
    w = W.gow_weights(fit)
    c = W.parse_contrast(contrast_spec, levels)
    ess_t = W.ess_table(fit, w, df["firm"].to_numpy())
    bal = W.balance_table(df, fit, w, ["x1", "x2", "x3"])
    arms_needed = [lv for lv, ci in zip(levels, c) if ci != 0]
    g = W.estimability_gates(ess_t, bal, gates, arms_needed)
    if apply_gates and not bool(g["pass"].all()):
        failed = [i for i, ok in zip(g.index, g["pass"]) if not ok]
        return None, "gate_fail:" + failed[0].split("[")[0].split(" ")[0]
    est, _ = W.estimate_contrast(df["y"].to_numpy(float), fit, w, df["firm"].to_numpy(), c, method)
    return est, "ok"


def cmd_run(a):
    proto = load_json(a.protocol)
    missing = [k for k in REQUIRED if k not in proto]
    if missing:
        raise SystemExit(f"Protocol is missing ADEMP fields: {missing}")
    seed = env_seed(a.seed if a.seed is not None else proto.get("seed"))
    with RunLog(a.out, "simulate", "run", vars(a), seed) as run:
        run.add_input(a.protocol, "protocol")
        run.note("protocol", proto)
        run.warn("Data-generating parameters are ASSUMPTIONS. Results describe the design under these assumptions, not the world.")
        if proto["dgm"]["name"] != "paper3":
            raise SystemExit("Only the built-in 'paper3' DGM is available; add others as plugins.")
        rng = np.random.default_rng(seed)
        rows, scenarios = [], proto["dgm"]["scenarios"]
        for sc in scenarios:
            params = {**proto["dgm"].get("common", {}), **sc["params"]}
            levels = params.get("arm_labels", paper3.DEFAULTS["arm_labels"])
            c = W.parse_contrast(proto["estimand"]["contrast"], levels)
            truth = paper3.true_overlap_contrast(params, c, n_big=proto["estimand"].get("truth_n", 200_000), seed=seed + 7)
            for method in proto["methods"]:
                est_l, se_l, lo_l, hi_l, p_l = [], [], [], [], []
                reasons = {}
                for r in range(int(proto["n_reps"])):
                    est, why = _one_rep_paper3(params, method, proto["estimand"]["contrast"], proto.get("gates", {}), rng, proto.get("apply_gates", True))
                    reasons[why] = reasons.get(why, 0) + 1
                    if est is not None:
                        est_l.append(est["estimate"]); se_l.append(est["se"]); lo_l.append(est["ci_low"])
                        hi_l.append(est["ci_high"]); p_l.append(est["p"])
                perf = performance(est_l, se_l, lo_l, hi_l, p_l, truth, n_attempted=int(proto["n_reps"]))
                row = {"scenario": sc["name"], "method": method, **perf,
                       **{f"reason_{k}": v for k, v in reasons.items()}}
                rows.append(row)
                print(f"[{sc['name']} | {method}] estimable={perf.get('estimable_rate', 0):.3f} "
                      f"rejection={perf.get('rejection_rate', float('nan')):.3f} coverage={perf.get('coverage', float('nan')):.3f}")
        res = pd.DataFrame(rows).set_index(["scenario", "method"])
        write_tables(run, {"performance": res, "protocol": pd.DataFrame({"field": list(proto), "value": [str(v) for v in proto.values()]}).set_index("field")}, "simulation")


class Simulate(Plugin):
    name = "simulate"
    help = "ADEMP simulation studies: null calibration, bias, coverage, power, estimability"

    def register(self, sub):
        p = add_common(sub.add_parser("run", help="Run a frozen ADEMP protocol (JSON)"), data=False, seed=True)
        p.add_argument("--protocol", required=True)
        p.set_defaults(func=cmd_run)


PLUGIN = Simulate()
