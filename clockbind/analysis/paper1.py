"""Paper 1 — choice-based conjoint / DCE analyses."""
from __future__ import annotations

import json
import numpy as np
import pandas as pd

from .core import Output, analysis, as_list
from .style import fig, INK, BRASS, SLATE
from ..stats import dce

COMMON = [
    {"name":"attributes","label":"Conjoint attributes","type":"columns","multi":True},
    {"name":"chosen","label":"Chosen (0/1 on profile rows)","type":"column"},
    {"name":"respondent","label":"Respondent ID","type":"column"},
    {"name":"task","label":"Task ID","type":"column"},
    {"name":"alternative","label":"Profile / alternative label","type":"column"},
    {"name":"baselines","label":"Attribute baselines JSON (optional)","type":"textarea","optional":True},
    {"name":"factor","label":"Task-level enforceability factor (optional)","type":"column","optional":True},
    {"name":"factor_baseline","label":"Factor baseline level (optional)","type":"text","optional":True},
]


def _prep(df, attributes, chosen, respondent, task, alternative, baselines=None, factor=None, factor_baseline=None):
    return dce.prepare_choice_data(
        df, as_list(attributes), chosen, respondent, task=task, alternative=alternative,
        baselines=json.loads(baselines) if baselines else None,
        factor=factor or None, factor_baseline=factor_baseline or None, add_outside=True,
    )


@analysis("p1_choice_diagnostics", "P1 · DCE choice/design diagnostics", "Paper 1 · DCE", COMMON)
def p1_choice_diagnostics(df, attributes, chosen, respondent, task, alternative, baselines=None, factor=None, factor_baseline=None):
    cd = _prep(df, attributes, chosen, respondent, task, alternative, baselines, factor, factor_baseline)
    raw = df.copy(); raw[chosen] = pd.to_numeric(raw[chosen], errors="coerce")
    g = raw.groupby([respondent, task], dropna=False)[chosen].sum()
    out = Output("p1_choice_diagnostics", "P1 · DCE choice/design diagnostics", {})
    out.n_used = int(raw[respondent].nunique())
    summ = pd.DataFrame([{
        "respondents": raw[respondent].nunique(), "tasks": len(g), "profile_rows": len(raw),
        "reject/no-choice tasks": int((g == 0).sum()), "reject rate": float((g == 0).mean()),
        "invalid multiple-choice tasks": int((g > 1).sum()), "estimable terms": len(cd.terms),
    }])
    out.table(summ, "Choice-set integrity")
    rows = []
    for a in as_list(attributes):
        vc = raw[a].astype(str).value_counts(dropna=False)
        for lv, n in vc.items(): rows.append({"attribute":a,"level":lv,"n":int(n),"share":float(n/len(raw))})
    out.table(pd.DataFrame(rows), "Observed attribute-level balance")
    if factor:
        task_factor = raw.groupby([respondent, task])[factor].first()
        out.table(task_factor.value_counts().rename("tasks").to_frame(), "Task-level factor balance")
    out.note("Reject/no-choice tasks are represented as an explicit outside alternative for the choice models; task-level factors enter through interactions, not as alternative-invariant main effects.")
    return out


@analysis("p1_mnl", "P1 · Conditional MNL with outside option", "Paper 1 · DCE", COMMON)
def p1_mnl(df, attributes, chosen, respondent, task, alternative, baselines=None, factor=None, factor_baseline=None):
    cd = _prep(df, attributes, chosen, respondent, task, alternative, baselines, factor, factor_baseline)
    fit = dce.fit_mnl(cd)
    out = Output("p1_mnl", "P1 · Conditional MNL with outside option", {}); out.n_used = int(pd.Series(cd.respondents).nunique())
    out.table(fit["table"], "Utility coefficients (dummy-coded)")
    out.table(pd.DataFrame([{"log likelihood":fit["loglike"],"choice sets":len(cd.set_slices),"respondents":out.n_used,"converged":fit["success"],"message":fit["message"]}]), "Model information")
    if not fit["success"]: out.warn("Optimizer did not report convergence. Do not interpret coefficients until the model is re-specified or convergence is achieved.")
    return out


@analysis("p1_swait_louviere", "P1 · Swait–Louviere scale diagnostic", "Paper 1 · DCE", COMMON)
def p1_swait_louviere(df, attributes, chosen, respondent, task, alternative, baselines=None, factor=None, factor_baseline=None):
    if not factor: raise ValueError("Select the task-level factor defining the two samples/conditions")
    cd = dce.prepare_choice_data(df, as_list(attributes), chosen, respondent, task=task, alternative=alternative,
                                 baselines=json.loads(baselines) if baselines else None, factor=factor,
                                 factor_baseline=factor_baseline or None, add_outside=True, interact_factor=False)
    r = dce.swait_louviere(cd)
    out = Output("p1_swait_louviere", "P1 · Swait–Louviere scale diagnostic", {}); out.n_used = int(pd.Series(cd.respondents).nunique())
    out.table(pd.DataFrame([r]), "Scale and preference-equality tests")
    out.note("The relative-scale parameter is estimated jointly with common preference coefficients. The preference-equality LR test compares separate models with a common-preference model allowing relative scale; the scale-equality LR test then tests μ=1 under common preferences.")
    if not r["converged"]: out.warn("At least one optimizer did not report convergence; withhold inferential interpretation.")
    return out


@analysis("p1_mixed_logit", "P1 · Mixed logit (simulated ML)", "Paper 1 · DCE", COMMON + [
    {"name":"random_terms","label":"Random coefficient terms (comma-separated; inspect P1 MNL term names first)","type":"text"},
    {"name":"draws","label":"Halton simulation draws","type":"int","default":128},
    {"name":"seed","label":"Seed","type":"int","default":20260928},
])
def p1_mixed_logit(df, attributes, chosen, respondent, task, alternative, random_terms, draws=128, seed=20260928, baselines=None, factor=None, factor_baseline=None):
    cd = _prep(df, attributes, chosen, respondent, task, alternative, baselines, factor, factor_baseline)
    r = dce.fit_mixed_logit(cd, as_list(random_terms), int(draws), int(seed))
    out = Output("p1_mixed_logit", "P1 · Mixed logit (simulated maximum likelihood)", {}); out.n_used = r["respondents"]
    out.table(r["table"], "Population utility distribution")
    out.table(pd.DataFrame([{"log likelihood":r["loglike"],"draws":r["draws"],"seed":r["seed"],"converged":r["success"],"message":r["message"]}]), "Model information")
    out.warn("Validation-required engine: confirmatory use requires frozen-case agreement with an established mixed-logit implementation before manuscript reporting.")
    return out


@analysis("p1_hb_mnl", "P1 · Hierarchical-Bayes MNL part-worths", "Paper 1 · DCE", COMMON + [
    {"name":"iterations","label":"MCMC iterations","type":"int","default":1000},
    {"name":"burn","label":"Burn-in","type":"int","default":400},
    {"name":"thin","label":"Thinning","type":"int","default":5},
    {"name":"seed","label":"Seed","type":"int","default":20260928},
    {"name":"step_scale","label":"Metropolis proposal scale","type":"number","default":0.18},
])
def p1_hb_mnl(df, attributes, chosen, respondent, task, alternative, iterations=1000, burn=400, thin=5, seed=20260928, step_scale=0.18, baselines=None, factor=None, factor_baseline=None):
    cd = _prep(df, attributes, chosen, respondent, task, alternative, baselines, factor, factor_baseline)
    r = dce.fit_hb_mnl(cd, int(iterations), int(burn), int(thin), int(seed), float(step_scale))
    out = Output("p1_hb_mnl", "P1 · Hierarchical-Bayes MNL part-worths", {}); out.n_used = len(r["individual_means"])
    out.table(r["population"], "Population posterior")
    acc = r["acceptance"]
    out.table(pd.DataFrame([{"retained posterior draws":r["retained_draws"],"median acceptance":float(acc.median()),"min acceptance":float(acc.min()),"max acceptance":float(acc.max()),"seed":r["seed"]}]), "MCMC diagnostics")
    if (acc < .10).any() or (acc > .70).any(): out.warn("Some respondent-level Metropolis acceptance rates are outside 0.10–0.70. Tune proposal scale and inspect convergence before use.")
    out.table(r["individual_means"].head(50), "Respondent posterior mean part-worths (first 50)", "Full respondent table remains available from programmatic/CLI use; do not publish identifiable respondent IDs.")
    out.warn("Validation-required engine: inspect trace/convergence with longer chains and benchmark against an established HB conjoint package before confirmatory reporting.")
    return out
