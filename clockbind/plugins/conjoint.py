"""Paper 1: conjoint design, analysis and design-recovery (power) simulation."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from ..core.io import load_data, require_columns, write_tables
from ..core.plugin import Plugin
from ..core.provenance import RunLog, env_seed
from ..stats import conjoint as C
from ..stats.simulation import performance
from ._common import add_common, load_json, split_list


def cmd_design(a):
    cfg = load_json(a.config)
    seed = env_seed(a.seed)
    with RunLog(a.out, "conjoint", "design", vars(a), seed) as run:
        run.add_input(a.config, "config")
        des = C.generate_design(cfg, np.random.default_rng(seed))
        des.to_csv(run.path("design.csv"), index=False); run.add_output(run.path("design.csv"))
        write_tables(run, C.design_diagnostics(des, cfg), "design_diagnostics")
        print(f"{len(des)//2} tasks across {cfg['n_blocks']} blocks written.")


def cmd_analyze(a):
    df = load_data(a.data)
    attrs = split_list(a.attributes)
    need = attrs + [a.chosen, a.respondent, "task"] + ([a.factor] if a.factor else [])
    require_columns(df, need)
    with RunLog(a.out, "conjoint", "analyze", vars(a), None) as run:
        run.add_input(a.data)
        res = C.analyze(df, attrs, a.chosen, a.respondent, a.factor, split_list(a.interact) or None,
                        load_json(a.baselines) if a.baselines else None, a.factor_baseline, a.vcov)
        write_tables(run, res, "conjoint_results")
        if "interactions" in res:
            print(res["interactions"].to_string())


def cmd_power(a):
    cfg = load_json(a.config)
    sim = load_json(a.sim)
    seed = env_seed(a.seed)
    target = a.target
    grid_n = [int(x) for x in split_list(a.n_grid)]
    with RunLog(a.out, "conjoint", "power", vars(a), seed) as run:
        run.add_input(a.config, "config"); run.add_input(a.sim, "assumptions")
        run.warn("All utilities in the assumptions file are ASSUMED values, not estimates.")
        rng = np.random.default_rng(seed)
        des = C.generate_design(cfg, rng)
        attrs = list(cfg["attributes"])
        fname = cfg["task_factor"]["name"]
        interact = [target.split("=")[0]]
        # population value of the target coefficient (probability scale) from one large sample
        big = C.simulate_choices(des, cfg, sim, a.truth_n, np.random.default_rng(seed + 1))
        bl = cfg.get("baselines")
        fb = cfg["task_factor"].get("baseline", cfg["task_factor"]["levels"][0])
        tb = C.analyze(big, attrs, "chosen", "respondent", fname, interact, bl, fb, vcov="CR1")["interactions"]
        if target not in tb.index:
            raise SystemExit(f"Target '{target}' not found. Available: {list(tb.index)}")
        truth = float(tb.loc[target, "estimate"])
        run.note("true_value_probability_scale", truth)
        rows = []
        for n in grid_n:
            est, se, lo, hi, p = [], [], [], [], []
            for r in range(a.reps):
                d = C.simulate_choices(des, cfg, sim, n, rng)
                t = C.analyze(d, attrs, "chosen", "respondent", fname, interact, bl, fb, vcov=a.vcov)["interactions"].loc[target]
                est.append(t["estimate"]); se.append(t["se"]); lo.append(t["ci_low"]); hi.append(t["ci_high"]); p.append(t["p"])
            perf = performance(np.array(est), np.array(se), np.array(lo), np.array(hi), np.array(p), truth)
            rows.append({"n_respondents": n, "tasks_per_respondent": cfg["n_tasks"], **perf})
            print(f"N={n}: power={perf['rejection_rate']:.3f}  coverage={perf['coverage']:.3f}")
        write_tables(run, {"performance": pd.DataFrame(rows).set_index("n_respondents"),
                           "truth": pd.DataFrame({"value": [truth]}, index=[target])}, "power")


class Conjoint(Plugin):
    name = "conjoint"
    help = "Paper 1: blocked conjoint design, AMCE/interaction analysis, design-recovery simulation"

    def register(self, sub):
        p = add_common(sub.add_parser("design", help="Generate a blocked design from a JSON config"), data=False, seed=True)
        p.add_argument("--config", required=True)
        p.set_defaults(func=cmd_design)

        p = add_common(sub.add_parser("analyze", help="AMCEs and attribute x task-factor interactions"))
        p.add_argument("--attributes", required=True)
        p.add_argument("--chosen", default="chosen")
        p.add_argument("--respondent", default="respondent")
        p.add_argument("--factor", help="Task-level factor column (e.g. enforceability)")
        p.add_argument("--factor-baseline", dest="factor_baseline")
        p.add_argument("--interact", help="Attributes to interact with the factor (default: all)")
        p.add_argument("--baselines", help="JSON {attribute: baseline level}")
        p.add_argument("--vcov", default="CR2", choices=["CR0", "CR1", "CR2"])
        p.set_defaults(func=cmd_analyze)

        p = add_common(sub.add_parser("power", help="Monte Carlo design recovery for one target coefficient"), data=False, seed=True)
        p.add_argument("--config", required=True)
        p.add_argument("--sim", required=True, help="JSON with assumed utilities")
        p.add_argument("--target", required=True, help="e.g. 'standards_compliance=high x enforceability=LOW'")
        p.add_argument("--n-grid", dest="n_grid", default="90,120,150,180,200")
        p.add_argument("--reps", type=int, default=500)
        p.add_argument("--truth-n", dest="truth_n", type=int, default=20000)
        p.add_argument("--vcov", default="CR1", choices=["CR0", "CR1", "CR2"])
        p.set_defaults(func=cmd_power)


PLUGIN = Conjoint()
