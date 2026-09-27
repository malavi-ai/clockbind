"""Cross-check clockbind against independent R implementations (PSweight, clubSandwich).
Agreement within tolerance is necessary, not sufficient: it shows the code implements
the same method as established software; it does not validate the design choices."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from ..core.io import load_data, require_columns, write_tables
from ..core.plugin import Plugin
from ..core.provenance import RunLog
from ..stats import weights as W
from ..stats.robust import wls_cluster
from ._common import add_common, split_list

def _within_arm_diff(w1, w2, z):
    d = 0.0
    for k in np.unique(z):
        m = z == k
        d = max(d, float(np.abs(w1[m] / w1[m].sum() - w2[m] / w2[m].sum()).max()))
    return d


R_SCRIPT = Path(__file__).resolve().parent.parent / "r" / "validate_weights.R"


def cmd_weights(a):
    if not shutil.which("Rscript"):
        raise SystemExit("Rscript not found. Install R and the packages PSweight, clubSandwich, jsonlite.")
    df = load_data(a.data)
    covs = split_list(a.covariates)
    require_columns(df, [a.treatment, a.outcome, a.cluster] + covs)
    with RunLog(a.out, "validate", "weights", vars(a), None) as run:
        run.add_input(a.data)
        d = df[[a.treatment, a.outcome, a.cluster] + covs].dropna().reset_index(drop=True)
        levels = sorted(d[a.treatment].astype(str).unique())
        d[a.treatment] = d[a.treatment].astype(str)
        fit = W.fit_ps(d, a.treatment, covs, levels)
        w = W.gow_weights(fit)
        y = d[a.outcome].to_numpy(float)
        mu_py = np.array([np.average(y[fit.z == k], weights=w[fit.z == k]) for k in range(len(levels))])
        res = wls_cluster(y, W.arm_design(fit), w, d[a.cluster].to_numpy(), "CR2")

        dpath, wpath, jpath = run.path("validation_data.csv"), run.path("python_weights.csv"), run.path("r_output.json")
        d.to_csv(dpath, index=False)
        pd.DataFrame({"weight": w}).to_csv(wpath, index=False)
        cmd = ["Rscript", str(R_SCRIPT), str(dpath), a.treatment, ",".join(covs), a.outcome, a.cluster, str(wpath), str(jpath)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("R validation failed:\n" + r.stderr)
        R = json.loads(jpath.read_text())
        run.note("r_versions", R["versions"])

        tol_est, tol_se = a.tol_estimate, a.tol_se
        ps_r = np.asarray(R["psweight_ps"], float)
        checks = [
            ("arm levels identical", R["levels"] == levels, "", ""),
            ("max |PS python - PS PSweight|", None, float(np.abs(fit.ps - ps_r).max()), tol_est),
            ("max |weight python - weight PSweight| (each normalised to sum 1 within arm)", None,
             _within_arm_diff(w, np.asarray(R["psweight_weights"], float), fit.z), tol_est),
            ("max |arm mean python - PSweight muhat|", None, float(np.abs(mu_py - np.asarray(R["psweight_muhat"])).max()), tol_est),
            ("max |coef python - lm coef|", None, float(np.abs(res.coef - np.asarray(R["club_coef"])).max()), tol_est),
            ("max |CR2 SE python - clubSandwich CR2 SE|", None,
             float(np.abs(np.sqrt(np.diag(res.vcov)) - np.sqrt(np.diag(np.asarray(R["club_vcov_cr2"])))).max()), tol_se),
        ]
        rows = []
        for name, ok, diff, tol in checks:
            if ok is None:
                ok = diff <= tol
            rows.append({"check": name, "difference": diff, "tolerance": tol, "pass": bool(ok)})
        tab = pd.DataFrame(rows).set_index("check")
        verdict = "AGREES" if tab["pass"].all() else "DISAGREES"
        run.note("verdict", verdict)
        write_tables(run, {"verdict": pd.DataFrame({"verdict": [verdict]}), "checks": tab}, "validation")
        print(tab.to_string())
        print(f"Verdict: {verdict}")
        return 0 if verdict == "AGREES" else 3


class Validate(Plugin):
    name = "validate"
    help = "Cross-check results against independent R packages (PSweight, clubSandwich)"

    def register(self, sub):
        p = add_common(sub.add_parser("weights", help="Compare PS, overlap weights, arm means and CR2 SEs with R"))
        p.add_argument("--treatment", required=True)
        p.add_argument("--covariates", required=True)
        p.add_argument("--outcome", required=True)
        p.add_argument("--cluster", required=True)
        p.add_argument("--tol-estimate", dest="tol_estimate", type=float, default=1e-4)
        p.add_argument("--tol-se", dest="tol_se", type=float, default=1e-8)
        p.set_defaults(func=cmd_weights)

        p = sub.add_parser("all", help="Validate every statistical procedure against R and write VALIDATION.md")
        p.add_argument("--data", default=None, help="Validation data (default: bundled synthetic data)")
        p.add_argument("--conjoint", default=None, help="Conjoint data (default: bundled synthetic data)")
        p.add_argument("--report", default="VALIDATION.md")
        p.add_argument("--out", default="clockbind_runs")
        p.set_defaults(func=cmd_all)


def cmd_all(a):
    from ..validation_suite import ROOT, compute, write_report
    data = Path(a.data) if a.data else ROOT / "validation" / "validation_data.csv"
    cj = Path(a.conjoint) if a.conjoint else ROOT / "examples" / "conjoint_synthetic.csv"
    with RunLog(a.out, "validate", "all", vars(a), None) as run:
        run.add_input(data, "validation_data"); run.add_input(cj, "conjoint_data")
        rows, versions = compute(data, cj)
        n_pass, n = write_report(rows, versions, Path(a.report))
        run.note("r_versions", versions); run.note("result", f"{n_pass}/{n} pass")
        print(f"{n_pass} of {n} checks pass. Report: {a.report}")
        if n_pass < n:
            return 1


PLUGIN = Validate()
