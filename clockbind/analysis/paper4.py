"""Paper 4 — qualitative case, evidence-matrix and process-tracing support.

ClockBind never treats coded text as self-validating evidence.  These routines
organise researcher-coded evidence, provenance and process-tracing tests; they
do not auto-infer motives, causal mechanisms or case conclusions from free text.
"""
from __future__ import annotations

import pandas as pd
import numpy as np

from .core import Output, analysis, as_list


@analysis("p4_case_matrix", "P4 · Case-code evidence matrix", "Paper 4 · Qualitative", [
    {"name":"case","label":"Case ID","type":"column"},
    {"name":"code","label":"Researcher code","type":"column"},
    {"name":"source","label":"Source/document ID","type":"column"},
    {"name":"date","label":"Event/document date (optional)","type":"column","optional":True},
    {"name":"governance_form","label":"Governance form (optional)","type":"column","optional":True},
    {"name":"direction","label":"Evidence direction: support/oppose/neutral (optional)","type":"column","optional":True},
])
def p4_case_matrix(df, case, code, source, date=None, governance_form=None, direction=None):
    cols=[case,code,source]+([date] if date else [])+([governance_form] if governance_form else [])+([direction] if direction else [])
    d=df[cols].copy().dropna(subset=[case,code,source])
    out=Output("p4_case_matrix","P4 · Case-code evidence matrix",{}); out.n_used=int(d[case].nunique())
    mat=pd.crosstab(d[case].astype(str),d[code].astype(str))
    out.table(mat,"Case × code evidence counts","Counts represent coded evidence units, not effect sizes or inferential weights.")
    prov=d.groupby(case).agg(coded_units=(code,"size"),distinct_sources=(source,"nunique"),distinct_codes=(code,"nunique")).sort_index()
    if governance_form:
        gf=d.groupby(case)[governance_form].agg(lambda s: s.dropna().astype(str).mode().iloc[0] if len(s.dropna()) else "")
        prov["governance_form"]=gf
    out.table(prov,"Case provenance coverage")
    if direction:
        dr=pd.crosstab([d[case].astype(str),d[code].astype(str)],d[direction].astype(str))
        out.table(dr,"Support / opposition / neutral evidence by case and code")
        dirs=set(d[direction].dropna().astype(str).str.lower())
        if {"support","oppose"}.issubset(dirs):
            conflict=[]
            for (ca,co),g in d.groupby([case,code]):
                z=set(g[direction].dropna().astype(str).str.lower())
                if "support" in z and "oppose" in z: conflict.append({"case":ca,"code":co,"sources":g[source].nunique()})
            if conflict: out.table(pd.DataFrame(conflict),"Codes with internally conflicting evidence")
    if date:
        dt=pd.to_datetime(d[date],errors="coerce")
        cov=d.assign(__date=dt).groupby(case)["__date"].agg(["min","max","count"])
        out.table(cov,"Chronology coverage")
    out.note("Use this matrix for structured comparison and negative-evidence retention. It does not substitute for reading the source material or process-tracing adjudication.")
    return out


PT_IMPLICATION={
    ("straw-in-the-wind","pass"):"weakly supports the proposition; not necessary or sufficient",
    ("straw-in-the-wind","fail"):"weakly undermines the proposition; not decisive",
    ("hoop","pass"):"passes a necessary test but does not by itself strongly confirm",
    ("hoop","fail"):"strongly undermines the proposition because a necessary implication failed",
    ("smoking-gun","pass"):"strongly supports the proposition; the evidence is highly probative if valid",
    ("smoking-gun","fail"):"absence/failure is not strongly disconfirming because the test is not necessary",
    ("doubly-decisive","pass"):"strongly supports the proposition while discriminating against specified rivals",
    ("doubly-decisive","fail"):"does not satisfy the declared doubly-decisive test; revisit proposition/rivals/evidence",
}


def _norm_test(s:str)->str:
    x=str(s).strip().lower().replace("_","-").replace(" ","-")
    aliases={"straw":"straw-in-the-wind","straw-in-wind":"straw-in-the-wind","smokinggun":"smoking-gun","double":"doubly-decisive","doublydecisive":"doubly-decisive"}
    return aliases.get(x,x)


@analysis("p4_process_trace", "P4 · Process-tracing evidence tests", "Paper 4 · Qualitative", [
    {"name":"case","label":"Case ID","type":"column"},
    {"name":"proposition","label":"Mechanism/proposition ID","type":"column"},
    {"name":"test_type","label":"Test type (straw / hoop / smoking-gun / doubly-decisive)","type":"column"},
    {"name":"result","label":"Test result (pass / fail / unknown)","type":"column"},
    {"name":"source","label":"Source ID","type":"column"},
    {"name":"rival","label":"Rival explanation ID (optional)","type":"column","optional":True},
])
def p4_process_trace(df, case, proposition, test_type, result, source, rival=None):
    cols=[case,proposition,test_type,result,source]+([rival] if rival else [])
    d=df[cols].copy().dropna(subset=[case,proposition,test_type,result,source])
    d["test_normalized"]=d[test_type].map(_norm_test); d["result_normalized"]=d[result].astype(str).str.strip().str.lower()
    allowed={"straw-in-the-wind","hoop","smoking-gun","doubly-decisive"}; bad=sorted(set(d["test_normalized"])-allowed)
    if bad: raise ValueError(f"Unknown process-tracing test types: {bad}")
    badr=sorted(set(d["result_normalized"])-{"pass","fail","unknown","pending"})
    if badr: raise ValueError(f"Unknown test results: {badr}")
    d["diagnostic implication"]=[PT_IMPLICATION.get((t,r),"unresolved; retain as unknown/pending") for t,r in zip(d["test_normalized"],d["result_normalized"])]
    out=Output("p4_process_trace","P4 · Process-tracing evidence tests",{}); out.n_used=int(d[case].nunique())
    show=[case,proposition,"test_normalized","result_normalized",source,"diagnostic implication"]+([rival] if rival else [])
    out.table(d[show],"Evidence-test register")
    summ=pd.crosstab([d[case].astype(str),d[proposition].astype(str)], [d["test_normalized"],d["result_normalized"]])
    out.table(summ,"Process-tracing test pattern by case/proposition")
    unresolved=d[d["result_normalized"].isin(["unknown","pending"])]
    if len(unresolved): out.warn(f"{len(unresolved)} process-tracing tests remain unresolved; no automated conclusion is assigned to them.")
    out.note("ClockBind reports the diagnostic meaning of researcher-declared evidence tests but does not aggregate them into an automatic causal verdict. Source validity, uniqueness, independence and rival explanations remain researcher judgments.")
    return out


@analysis("p4_governance_comparison", "P4 · Governance-form cross-case comparison", "Paper 4 · Qualitative", [
    {"name":"case","label":"Case ID","type":"column"},
    {"name":"governance_form","label":"Governance form (e.g. franchise / know-how licence)","type":"column"},
    {"name":"dimensions","label":"Coded comparison dimensions","type":"columns","multi":True},
])
def p4_governance_comparison(df, case, governance_form, dimensions):
    dims=as_list(dimensions); d=df[[case,governance_form]+dims].copy().dropna(subset=[case,governance_form])
    # one row per case is ideal; if repeated, use first nonmissing per dimension and flag conflicts
    rows=[]; conflicts=[]
    for ca,g in d.groupby(case,sort=False):
        gf=g[governance_form].dropna().astype(str).unique().tolist()
        row={"case":ca,"governance_form":gf[0] if gf else ""}
        if len(gf)>1: conflicts.append({"case":ca,"field":governance_form,"values":" | ".join(gf)})
        for x in dims:
            vals=g[x].dropna().astype(str).unique().tolist(); row[x]=vals[0] if vals else ""
            if len(vals)>1: conflicts.append({"case":ca,"field":x,"values":" | ".join(vals)})
        rows.append(row)
    cases=pd.DataFrame(rows).set_index("case")
    out=Output("p4_governance_comparison","P4 · Governance-form cross-case comparison",{}); out.n_used=len(cases)
    out.table(cases,"Case comparison matrix")
    for x in dims:
        ct=pd.crosstab(cases["governance_form"],cases[x]); out.table(ct,f"Governance form × {x}")
    if conflicts: out.warn("Repeated-case coding conflicts detected; adjudicate before synthesis."); out.table(pd.DataFrame(conflicts),"Coding conflicts")
    out.note("Cross-case matrices describe documented configurations. ClockBind does not rank governance forms or infer that one form is superior from small-N case counts.")
    return out
