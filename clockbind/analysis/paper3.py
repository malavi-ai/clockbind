"""Paper 3 — fsQCA, dyadic/panel analysis and survival analysis."""
from __future__ import annotations

import json
import math
from itertools import product

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.duration.hazard_regression import PHReg
from statsmodels.duration.survfunc import SurvfuncRight

from .core import Output, analysis, as_list, numeric


def calibrate_direct(x: pd.Series, full_out: float, crossover: float, full_in: float) -> pd.Series:
    """Piecewise-logit direct calibration hitting .05/.50/.95 at the three anchors."""
    if not (full_out < crossover < full_in):
        raise ValueError("Calibration anchors must satisfy full_out < crossover < full_in")
    z = pd.to_numeric(x, errors="coerce").astype(float)
    logit95 = math.log(.95/.05)
    out = pd.Series(index=z.index, dtype=float)
    lo = z <= crossover
    out.loc[lo] = 1/(1+np.exp(-logit95*(z.loc[lo]-crossover)/(crossover-full_out)))
    out.loc[~lo] = 1/(1+np.exp(-logit95*(z.loc[~lo]-crossover)/(full_in-crossover)))
    return out.clip(0.0001,0.9999)


def _fuzzy_consistency_suff(x: np.ndarray, y: np.ndarray) -> tuple[float,float]:
    mn=np.minimum(x,y); sx=np.sum(x); sy=np.sum(y)
    return (float(mn.sum()/sx) if sx>0 else np.nan, float(mn.sum()/sy) if sy>0 else np.nan)


def _necessity(x: np.ndarray, y: np.ndarray) -> tuple[float,float]:
    mn=np.minimum(x,y); sy=np.sum(y); sx=np.sum(x)
    return (float(mn.sum()/sy) if sy>0 else np.nan, float(mn.sum()/sx) if sx>0 else np.nan)


def _pri(x: np.ndarray,y: np.ndarray) -> float:
    """PRI = [Σmin(X,Y) − Σmin(X,Y,~Y)] / [ΣX − Σmin(X,Y,~Y)] (Ragin 2008)."""
    a=np.minimum(x,y).sum(); b=np.minimum(np.minimum(x,y),1-y).sum(); den=x.sum()-b
    return float((a-b)/den) if den>0 else np.nan


def _config_membership(d: pd.DataFrame, conditions: list[str], bits: tuple[int,...]) -> np.ndarray:
    arr=[]
    for c,b in zip(conditions,bits):
        x=d[c].to_numpy(float); arr.append(x if b else 1-x)
    return np.min(np.column_stack(arr),axis=1)


def _expr_to_terms(expr, symbol_map: dict[str, str]) -> list[list[tuple[str,int]]]:
    import sympy as sp
    if expr is sp.true: return [[]]
    ors=list(expr.args) if isinstance(expr,sp.Or) else [expr]
    out=[]
    for term in ors:
        atoms=list(term.args) if isinstance(term,sp.And) else [term]
        row=[]
        for a in atoms:
            if isinstance(a,sp.Not):
                key=str(a.args[0]); row.append((symbol_map[key],0))
            else:
                key=str(a); row.append((symbol_map[key],1))
        out.append(row)
    return out


def _term_membership(d: pd.DataFrame, term: list[tuple[str,int]]) -> np.ndarray:
    if not term:return np.ones(len(d))
    return np.min(np.column_stack([d[c].to_numpy(float) if s else 1-d[c].to_numpy(float) for c,s in term]),axis=1)


@analysis("p3_fsqca_calibrate", "P3 · fsQCA direct calibration (exploratory)", "Paper 3 · QCA & Panel", [
    {"name":"variable","label":"Raw variable","type":"column","numeric":True},
    {"name":"full_out","label":"Full non-membership anchor","type":"number","default":0.0},
    {"name":"crossover","label":"Crossover anchor","type":"number","default":0.5},
    {"name":"full_in","label":"Full membership anchor","type":"number","default":1.0},
])
def p3_fsqca_calibrate(df, variable, full_out=0.0, crossover=0.5, full_in=1.0):
    m=calibrate_direct(df[variable],float(full_out),float(crossover),float(full_in))
    out=Output("p3_fsqca_calibrate","P3 · fsQCA direct calibration (exploratory)",{}); out.n_used=int(m.notna().sum())
    q=pd.DataFrame({"raw":pd.to_numeric(df[variable],errors="coerce"),"membership":m}).dropna()
    out.table(q.describe(percentiles=[.05,.25,.5,.75,.95]).T,"Calibration summary")
    out.table(pd.DataFrame([{"full out":full_out,"crossover":crossover,"full in":full_in,"membership at anchors":"0.05 / 0.50 / 0.95"}]),"Anchors")
    out.note("ClockBind uses a transparent piecewise-logit direct calibration that exactly maps the three declared anchors to .05/.50/.95. Calibration anchors remain substantive researcher decisions and must be justified before outcome inspection where feasible.")
    return out


@analysis("p3_fsqca", "P3 · fsQCA necessity, truth table and conservative solution (exploratory)", "Paper 3 · QCA & Panel", [
    {"name":"conditions","label":"Fuzzy-set conditions (0–1)","type":"columns","multi":True,"numeric":True},
    {"name":"outcome","label":"Fuzzy-set outcome (0–1)","type":"column","numeric":True},
    {"name":"frequency_cutoff","label":"Truth-table frequency cutoff","type":"int","default":1},
    {"name":"consistency_cutoff","label":"Sufficiency consistency cutoff","type":"number","default":0.80},
    {"name":"pri_cutoff","label":"PRI cutoff","type":"number","default":0.50},
])
def p3_fsqca(df, conditions, outcome, frequency_cutoff=1, consistency_cutoff=.80, pri_cutoff=.50):
    cond=as_list(conditions)
    if len(cond)<2: raise ValueError("Select at least two conditions")
    d=numeric(df,cond+[outcome]).dropna()
    if ((d<0)|(d>1)).any().any(): raise ValueError("fsQCA inputs must be calibrated membership scores in [0,1]")
    y=d[outcome].to_numpy(float)
    out=Output("p3_fsqca","P3 · fsQCA necessity, truth table and conservative solution (exploratory)",{}); out.n_used=len(d)
    nr=[]
    for c in cond:
        for neg,label in [(False,c),(True,"~"+c)]:
            x=(1-d[c] if neg else d[c]).to_numpy(float); co,cv=_necessity(x,y)
            nr.append({"condition":label,"necessity consistency":co,"necessity coverage":cv})
    out.table(pd.DataFrame(nr).set_index("condition"),"Necessity analysis")
    tt=[]; sufficient=[]
    for bits in product([0,1],repeat=len(cond)):
        crisp=np.ones(len(d),dtype=bool)
        for c,b in zip(cond,bits): crisp &= ((d[c].to_numpy()>=.5)==bool(b))
        n=int(crisp.sum()); x=_config_membership(d,cond,bits); cons,cov=_fuzzy_consistency_suff(x,y); pri=_pri(x,y)
        row={**{c:b for c,b in zip(cond,bits)},"cases":n,"consistency":cons,"PRI":pri,"raw coverage":cov}
        row["sufficient"] = bool(n>=int(frequency_cutoff) and cons>=float(consistency_cutoff) and pri>=float(pri_cutoff))
        tt.append(row)
        if row["sufficient"]: sufficient.append(bits)
    tdf=pd.DataFrame(tt).sort_values(["sufficient","consistency","cases"],ascending=[False,False,False])
    out.table(tdf,"Truth table")
    if not sufficient:
        out.warn("No observed truth-table configuration passed the declared frequency/consistency/PRI thresholds; no sufficiency solution was generated.")
        return out
    import sympy as sp
    symbols=tuple(sp.symbols(f"q0:{len(cond)}"))
    symbol_map={str(sym):name for sym,name in zip(symbols,cond)}
    mins=[list(bits) for bits in sufficient]
    expr=sp.SOPform(symbols,mins,[])  # conservative: no logical remainders as don't-cares
    terms=_expr_to_terms(expr,symbol_map)
    term_rows=[]; mems=[]
    for term in terms:
        x=_term_membership(d,term); mems.append(x); cons,cov=_fuzzy_consistency_suff(x,y)
        label="*".join([c if s else "~"+c for c,s in term]) or "1"
        term_rows.append({"solution term":label,"consistency":cons,"raw coverage":cov})
    sol=np.max(np.column_stack(mems),axis=1); scons,scov=_fuzzy_consistency_suff(sol,y)
    # unique coverage
    for i,row in enumerate(term_rows):
        other=np.max(np.column_stack([m for j,m in enumerate(mems) if j!=i]),axis=1) if len(mems)>1 else np.zeros(len(d))
        unique=np.maximum(mems[i]-other,0).sum()/max(y.sum(),1e-12); row["unique coverage"] = float(unique)
    out.table(pd.DataFrame(term_rows).set_index("solution term"),"Conservative solution terms")
    human_expr=str(expr)
    for sym,name in symbol_map.items(): human_expr=human_expr.replace(sym,name)
    out.table(pd.DataFrame([{"solution":human_expr,"consistency":scons,"coverage":scov,"logical remainders used":False}]),"Solution summary")
    out.note("This is the conservative solution: unobserved configurations are not used as simplifying remainders. Intermediate/parsimonious solutions require explicit directional expectations and are intentionally not auto-generated.")
    return out


@analysis("p3_panel_first_difference", "P3 · T1/T2 first-difference panel model", "Paper 3 · QCA & Panel", [
    {"name":"outcome_t1","label":"Outcome at T1","type":"column","numeric":True},
    {"name":"outcome_t2","label":"Outcome at T2","type":"column","numeric":True},
    {"name":"predictor_pairs","label":"Predictor pairs JSON: name -> [T1,T2]","type":"textarea"},
    {"name":"cluster","label":"Cluster/dyad ID (optional)","type":"column","optional":True},
])
def p3_panel_first_difference(df, outcome_t1, outcome_t2, predictor_pairs, cluster=None):
    pairs=json.loads(predictor_pairs)
    if not isinstance(pairs,dict) or not pairs: raise ValueError("predictor_pairs must be a non-empty JSON object")
    raw=[outcome_t1,outcome_t2]+[x for p in pairs.values() for x in p]+([cluster] if cluster else [])
    d=df[raw].copy(); num=[outcome_t1,outcome_t2]+[x for p in pairs.values() for x in p]; d[num]=d[num].apply(pd.to_numeric,errors="coerce"); d=d.dropna()
    Y=d[outcome_t2]-d[outcome_t1]; X=pd.DataFrame(index=d.index)
    for name,p in pairs.items():
        if not isinstance(p,list) or len(p)!=2: raise ValueError(f"{name}: pair must be [T1,T2]")
        X[f"Δ{name}"]=d[p[1]]-d[p[0]]
    X=sm.add_constant(X,has_constant="add"); m=sm.OLS(Y,X).fit()
    if cluster and d[cluster].nunique()<len(d): r=m.get_robustcov_results(cov_type="cluster",groups=d[cluster]); infer="cluster-robust"
    else: r=m.get_robustcov_results(cov_type="HC3"); infer="HC3"
    tab=pd.DataFrame({"B":r.params,"SE":r.bse,"t":r.tvalues,"p":r.pvalues},index=X.columns)
    out=Output("p3_panel_first_difference","P3 · T1/T2 first-difference panel model",{}); out.n_used=len(d)
    out.table(tab,"Change-on-change model",f"{infer} inference. First differencing removes time-invariant unit effects under the two-wave specification.")
    out.table(pd.DataFrame([{"N":len(d),"R²":m.rsquared,"adjusted R²":m.rsquared_adj,"mean Δ outcome":float(Y.mean()),"SD Δ outcome":float(Y.std(ddof=1))}]),"Model summary")
    return out


@analysis("p3_survival_cox", "P3 · Survival analysis, Cox PH (exploratory)", "Paper 3 · QCA & Panel", [
    {"name":"duration","label":"Time to event/censoring","type":"column","numeric":True},
    {"name":"status","label":"Event indicator (1=event, 0=censored)","type":"column","numeric":True},
    {"name":"covariates","label":"Numeric covariates","type":"columns","multi":True,"numeric":True},
    {"name":"cluster","label":"Cluster/dyad ID (optional robust covariance)","type":"column","optional":True},
])
def p3_survival_cox(df, duration, status, covariates, cluster=None):
    covs=as_list(covariates); cols=[duration,status]+covs+([cluster] if cluster else [])
    d=df[cols].copy(); d[[duration,status]+covs]=d[[duration,status]+covs].apply(pd.to_numeric,errors="coerce"); d=d.dropna()
    if (d[duration]<=0).any(): raise ValueError("Survival durations must be > 0")
    if not d[status].isin([0,1]).all(): raise ValueError("status must be 0/1")
    X=d[covs].to_numpy(float)
    fit=PHReg(d[duration].to_numpy(float),X,status=d[status].to_numpy(int),ties="efron").fit(groups=d[cluster].to_numpy() if cluster else None)
    ci=fit.conf_int(); tab=pd.DataFrame({"B":fit.params,"SE":fit.bse,"HR":np.exp(fit.params),"HR 95% low":np.exp(ci[:,0]),"HR 95% high":np.exp(ci[:,1]),"p":fit.pvalues},index=covs)
    km=SurvfuncRight(d[duration].to_numpy(float),d[status].to_numpy(int))
    # survival quantiles from step function where possible
    med=np.nan
    if np.any(km.surv_prob<=.5): med=float(km.surv_times[np.flatnonzero(km.surv_prob<=.5)[0]])
    out=Output("p3_survival_cox","P3 · Survival analysis, Cox proportional hazards (exploratory)",{}); out.n_used=len(d)
    out.table(tab,"Cox proportional-hazards model",f"Ties: Efron; {'cluster-robust covariance' if cluster else 'model-based covariance'}.")
    out.table(pd.DataFrame([{"N":len(d),"events":int(d[status].sum()),"censored":int((1-d[status]).sum()),"median survival":med,"log likelihood":fit.llf}]),"Survival summary")
    out.note("The proportional-hazards assumption must be checked before substantive interpretation. ClockBind does not silently certify PH from model convergence alone.")
    out.warn("Exploratory: not part of a preregistered primary analysis unless survival modelling was separately preregistered.")
    return out


@analysis("p3_dyad_gap", "P3 · Dyadic agreement / discrepancy summary", "Paper 3 · QCA & Panel", [
    {"name":"dyad","label":"Dyad ID","type":"column"},
    {"name":"side","label":"Side/partner label","type":"column"},
    {"name":"variables","label":"Dyad-rated variables","type":"columns","multi":True,"numeric":True},
])
def p3_dyad_gap(df, dyad, side, variables):
    vars_=as_list(variables); d=df[[dyad,side]+vars_].copy(); d[vars_]=d[vars_].apply(pd.to_numeric,errors="coerce")
    counts=d.groupby(dyad)[side].nunique(); eligible=counts[counts==2].index; d=d[d[dyad].isin(eligible)]
    rows=[]
    for v in vars_:
        p=d.pivot_table(index=dyad,columns=side,values=v,aggfunc="first").dropna()
        if p.shape[1]!=2: continue
        diff=(p.iloc[:,0]-p.iloc[:,1]).abs()
        r=float(p.iloc[:,0].corr(p.iloc[:,1])) if len(p)>2 else np.nan
        rows.append({"variable":v,"complete dyads":len(p),"mean absolute gap":float(diff.mean()),"median absolute gap":float(diff.median()),"Pearson r":r})
    out=Output("p3_dyad_gap","P3 · Dyadic agreement / discrepancy summary",{}); out.n_used=len(eligible)
    out.table(pd.DataFrame(rows).set_index("variable"),"Dyad-level agreement diagnostics")
    out.note("Partner agreement and partner discrepancy are descriptive constructs, not interchangeable. Decide ex ante whether a dyad-level variable uses aggregation, discrepancy, or one-side measurement.")
    return out
