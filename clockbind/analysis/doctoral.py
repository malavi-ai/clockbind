"""Project modules: Bridge screening, Paper 3 overlap weights, Paper 1 conjoint, missing-data overview."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from ..stats import conjoint as CJ
from ..stats import weights as W
from .core import Output, analysis, as_list
from .style import BRASS, ERR, INK, LINE, MUTED, REF, SLATE, TEAL, fig


@analysis("missing", "Missing-data overview", "Data",
          [{"name": "variables", "label": "Variables (default: all)", "type": "columns", "multi": True, "optional": True}])
def missing(df, variables=None):
    vs = as_list(variables) or list(df.columns)
    d = df[vs]
    miss = d.isna() | d.astype(str).apply(lambda s: s.str.strip().eq(""))
    out = Output("missing", "Missing-data overview", {})
    t = pd.DataFrame({"Missing": miss.sum(), "% missing": 100 * miss.mean()}).sort_values("% missing", ascending=False)
    out.table(t, "Missing values per variable")
    pat = miss.astype(int).astype(str).agg("".join, axis=1).value_counts().head(15)
    out.table(pd.DataFrame({"Rows": pat.values, "% rows": 100 * pat.values / len(d)}, index=[p.replace("1", "■").replace("0", "·") for p in pat.index]), "Most frequent patterns (■ = missing, columns in the order above)")
    f, ax = fig(7.0, 0.3 * len(vs) + 1.4)
    ax.barh(t.index[::-1], t["% missing"][::-1], color=[ERR if v > 20 else SLATE for v in t["% missing"][::-1]])
    ax.set_xlabel("% missing"); ax.set_title("Missing data by variable"); ax.grid(axis="y", visible=False)
    out.figure(f)
    out.note("Listwise deletion is the default in every analysis. For the final papers, pre-specify the missing-data rule (e.g. multiple imputation) before outcomes are analysed.")
    return out


@analysis("bridge_screening", "Bridge screening (levels)", "Doctoral modules",
          [{"name": "gates_json", "label": "Protocol (gates) JSON text or file path", "type": "textarea"}])
def bridge_screening(df, gates_json):
    from ..plugins.screen import apply_gates, funnel, gates_hash
    try:
        g = json.loads(gates_json)
    except Exception:
        with open(gates_json, encoding="utf-8") as fh:
            g = json.load(fh)
    d = df.astype(str).replace({"nan": ""})
    entries, eps, probs = apply_gates(d, g)
    fun = funnel(entries, eps, g)
    out = Output("bridge_screening", f"Bridge screening — protocol {g['protocol_version']}", {})
    out.text(f"Protocol sha256 {gates_hash(g)[:16]} · {'frozen ' + str(g.get('frozen_on', '')) if g.get('frozen') else 'DRAFT — not citable'}")
    out.table(fun[["stage", "kind", "count", "n"]], "Screening flow")
    if "level" in eps:
        lv = eps["level"].str.replace(r" \(pending.*\)$", "", regex=True).value_counts().sort_index()
        f, ax = fig(6.6, 0.45 * len(lv) + 1.4)
        cols = [BRASS if "Level 3" in k else TEAL if "Level 2" in k else SLATE if "Level 1" in k else LINE for k in lv.index]
        ax.barh(lv.index[::-1], lv.values[::-1], color=cols[::-1]); ax.set_title("Episodes by evidence level"); ax.grid(axis="y", visible=False)
        out.figure(f)
    keep = [c for c in [g["episode_column"], "level", "final_status"] if c in eps]
    out.table(eps[keep], "Episodes")
    if len(probs):
        out.table(probs, "Checks")
        if (probs["level"] == "ERROR").any():
            out.warn("The sheet contains errors: counts are not citable until they are fixed.")
    return out


def _love_plot(bal):
    cols = [c for c in bal.columns if "smd" in c.lower()]
    f, ax = fig(6.6, 0.4 * len(bal) + 1.6)
    y = np.arange(len(bal))[::-1]
    if len(cols) >= 2:
        ax.plot(bal[cols[0]].abs(), y, "o", mfc="white", color=MUTED, label=cols[0])
        ax.plot(bal[cols[1]].abs(), y, "o", color=INK, label=cols[1])
    elif cols:
        ax.plot(bal[cols[0]].abs(), y, "o", color=INK, label=cols[0])
    ax.axvline(0.1, color=BRASS, ls="--", lw=1); ax.set_yticks(y); ax.set_yticklabels(bal.index); ax.set_title("Covariate balance (|max pairwise SMD|)"); ax.legend(); ax.grid(axis="y", visible=False)
    return f


P3 = [{"name": "treatment", "label": "Architecture (arm)", "type": "column"},
      {"name": "covariates", "label": "Baseline covariates", "type": "columns", "multi": True},
      {"name": "cluster", "label": "Firm (cluster)", "type": "column"},
      {"name": "gates", "label": "Estimability gates JSON (optional)", "type": "textarea", "optional": True}]


def _p3_prepare(df, treatment, covariates, cluster, extra=()):
    covs = as_list(covariates)
    d = df[[treatment, cluster] + covs + [e for e in extra if e]].dropna()
    levels = sorted(d[treatment].unique().tolist(), key=str)
    fit = W.fit_ps(d, treatment, covs, levels)
    return d, covs, levels, fit, W.gow_weights(fit)


@analysis("p3_diagnose", "P3 · overlap weights: design diagnostics", "Doctoral modules", P3)
def p3_diagnose(df, treatment, covariates, cluster, gates=None):
    d, covs, levels, fit, w = _p3_prepare(df, treatment, covariates, cluster)
    ess_t = W.ess_table(fit, w, d[cluster].to_numpy()); bal = W.balance_table(d, fit, w, covs)
    g = json.loads(gates) if gates else {}
    gt = W.estimability_gates(ess_t, bal, g)
    out = Output("p3_diagnose", "P3 · design-stage diagnostics (outcome not read)", {}); out.n_used = len(d)
    out.text(f"Verdict: {'ESTIMABLE' if bool(gt['pass'].all()) else 'NON-ESTIMABLE'} under the stated gates.")
    for n in fit.notes:
        out.warn(n)
    out.table(gt, "Estimability gates"); out.table(ess_t, "Effective sample size by arm"); out.table(bal, "Balance")
    out.figure(_love_plot(bal))
    out.ref(REF["overlap"], REF["statsmodels"])
    return out


@analysis("p3_estimate", "P3 · overlap weights: contrast estimate", "Doctoral modules",
          P3 + [{"name": "outcome", "label": "Outcome", "type": "column"}, {"name": "contrast", "label": "Contrast, e.g.  A:0.5,B:0.5,C:-0.5,D:-0.5", "type": "text"},
                {"name": "bootstrap", "label": "Cluster bootstrap replicates (0 = none)", "type": "int", "default": 0}, {"name": "seed", "label": "Seed", "type": "int", "default": 20260926}])
def p3_estimate(df, treatment, covariates, cluster, outcome, contrast, gates=None, bootstrap=0, seed=20260926):
    d, covs, levels, fit, w = _p3_prepare(df, treatment, covariates, cluster, extra=(outcome,))
    ess_t = W.ess_table(fit, w, d[cluster].to_numpy()); bal = W.balance_table(d, fit, w, covs)
    gt = W.estimability_gates(ess_t, bal, json.loads(gates) if gates else {})
    out = Output("p3_estimate", "P3 · weighted contrast", {}); out.n_used = len(d)
    if not bool(gt["pass"].all()):
        out.warn("Estimability gates failed: this estimate is EXPLORATORY and must not be reported as confirmatory.")
    c = W.parse_contrast(contrast, levels)
    est, means = W.estimate_contrast(d[outcome].to_numpy(float), fit, w, d[cluster].to_numpy(), c, "CR2")
    out.table(means, "Weighted arm means"); out.table(pd.DataFrame([{"contrast": contrast, **est}]), "Contrast (CR2, G − 1 df)")
    if bootstrap:
        bs = W.cluster_bootstrap(d, treatment, covs, outcome, cluster, contrast, levels, B=int(bootstrap), seed=int(seed))
        out.table(pd.DataFrame([{k: (json.dumps(v) if isinstance(v, dict) else v) for k, v in bs.items()}]), "Cluster bootstrap (PS re-fitted per replicate)")
    out.ref(REF["overlap"], REF["cr2"], REF["bell_mccaffrey"])
    return out


@analysis("p1_conjoint", "P1 · conjoint AMCEs", "Doctoral modules",
          [{"name": "attributes", "label": "Attributes", "type": "columns", "multi": True}, {"name": "chosen", "label": "Chosen (0/1)", "type": "column"},
           {"name": "respondent", "label": "Respondent ID", "type": "column"}, {"name": "factor", "label": "Task-level factor (optional, e.g. enforceability)", "type": "column", "optional": True},
           {"name": "factor_baseline", "label": "Factor baseline level", "type": "text", "optional": True},
           {"name": "baselines", "label": "Attribute baselines JSON, e.g. {\"track_record\": \"none\"}", "type": "textarea", "optional": True}])
def p1_conjoint(df, attributes, chosen, respondent, factor=None, factor_baseline=None, baselines=None):
    res = CJ.analyze(df, as_list(attributes), chosen, respondent, factor=factor or None, baselines=json.loads(baselines) if baselines else None, factor_baseline=factor_baseline or None)
    out = Output("p1_conjoint", "P1 · conjoint analysis (AMCE)", {})
    am = res["amce"]; out.table(am, "AMCEs (CR2 by respondent)")
    t = am.drop(index="const", errors="ignore")
    f, ax = fig(6.8, 0.42 * len(t) + 1.4)
    y = np.arange(len(t))[::-1]
    ax.hlines(y, t["ci_low"], t["ci_high"], color=SLATE, lw=2); ax.plot(t["estimate"], y, "o", color=INK); ax.axvline(0, color=BRASS, ls="--")
    ax.set_yticks(y); ax.set_yticklabels(t.index); ax.set_title("AMCEs (95% CI)"); ax.grid(axis="y", visible=False)
    out.figure(f)
    for k in ("interactions", "reject_both_rate", "model_info"):
        if k in res:
            out.table(res[k], k.replace("_", " ").capitalize())
    out.ref(REF["amce"], REF["cr2"])
    return out
