"""Paper 2 — measurement, longitudinal invariance and incremental validity."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

from .core import Output, analysis, as_list, numeric


def _constructs(spec: str | dict) -> dict[str, list[str]]:
    obj = json.loads(spec) if isinstance(spec, str) else spec
    if not isinstance(obj, dict) or not obj:
        raise ValueError("Constructs must be a JSON object mapping construct names to item lists")
    out = {}
    for k, v in obj.items():
        if not isinstance(v, list) or len(v) < 2:
            raise ValueError(f"Construct {k!r} needs at least two item variables")
        out[str(k)] = [str(x) for x in v]
    return out


def _alpha(X: pd.DataFrame) -> float:
    X = X.dropna()
    k = X.shape[1]
    if k < 2 or len(X) < 3: return np.nan
    v = X.var(ddof=1)
    tv = X.sum(axis=1).var(ddof=1)
    return float(k/(k-1) * (1 - v.sum()/tv)) if tv > 0 else np.nan


def htmt_matrix(df: pd.DataFrame, constructs: dict[str, list[str]]) -> pd.DataFrame:
    all_items = [i for items in constructs.values() for i in items]
    X = numeric(df, all_items)
    C = X.corr().abs()
    names = list(constructs)
    H = pd.DataFrame(np.eye(len(names)), index=names, columns=names, dtype=float)
    for i, a in enumerate(names):
        for j, b in enumerate(names[:i]):
            het = [C.loc[x,y] for x in constructs[a] for y in constructs[b] if x != y]
            mono_a = [C.loc[x,y] for ii,x in enumerate(constructs[a]) for y in constructs[a][ii+1:]]
            mono_b = [C.loc[x,y] for ii,x in enumerate(constructs[b]) for y in constructs[b][ii+1:]]
            den = np.sqrt(np.nanmean(mono_a) * np.nanmean(mono_b))
            val = float(np.nanmean(het) / den) if den and np.isfinite(den) else np.nan
            H.loc[a,b] = H.loc[b,a] = val
    return H


def _parse_loadings(spec: str | None) -> dict[str, list[float]]:
    if not spec: return {}
    obj = json.loads(spec)
    if not isinstance(obj, dict): raise ValueError("loadings must be a JSON object")
    return {str(k): [float(x) for x in v] for k,v in obj.items()}


@analysis("p2_construct_validity", "P2 · Construct reliability and discriminant validity", "Paper 2 · Measurement", [
    {"name":"constructs","label":"Constructs JSON, e.g. {\"Runway\":[\"r1\",\"r2\",\"r3\"]}","type":"textarea"},
    {"name":"loadings","label":"Standardised CFA loadings JSON (optional, for CR/AVE)","type":"textarea","optional":True},
    {"name":"htmt_cutoff","label":"HTMT review threshold","type":"number","default":0.85},
])
def p2_construct_validity(df, constructs, loadings=None, htmt_cutoff=0.85):
    con = _constructs(constructs); all_items = [x for v in con.values() for x in v]
    X = numeric(df, all_items)
    out = Output("p2_construct_validity", "P2 · Construct reliability and discriminant validity", {}); out.n_used = int(X.dropna().shape[0])
    rel=[]
    lds=_parse_loadings(loadings)
    for k, items in con.items():
        row={"construct":k,"items":len(items),"Cronbach alpha":_alpha(X[items])}
        if k in lds:
            lam=np.asarray(lds[k],float)
            if len(lam)!=len(items): raise ValueError(f"Loadings for {k} must match its {len(items)} items")
            err=1-lam**2
            row["CR"] = float(lam.sum()**2/(lam.sum()**2+err.sum()))
            row["AVE"] = float(np.mean(lam**2))
        rel.append(row)
    out.table(pd.DataFrame(rel).set_index("construct"), "Reliability / convergent validity")
    H=htmt_matrix(df,con); out.table(H,"HTMT matrix")
    bad=[]
    for i,a in enumerate(H.index):
        for b in H.columns[:i]:
            if H.loc[a,b] > float(htmt_cutoff): bad.append(f"{a}–{b}: {H.loc[a,b]:.3f}")
    if bad: out.warn("HTMT pairs above the review threshold: " + "; ".join(bad))
    out.note("CR and AVE are reported only when standardised CFA loadings are supplied; they are not approximated from PCA loadings.")
    return out


@analysis("p2_incremental_validity", "P2 · Incremental validity (ΔR²)", "Paper 2 · Measurement", [
    {"name":"outcome","label":"Outcome","type":"column","numeric":True},
    {"name":"base_predictors","label":"Baseline/control predictors","type":"columns","multi":True,"numeric":True},
    {"name":"focal_predictors","label":"Financial-flexibility capability predictors","type":"columns","multi":True,"numeric":True},
    {"name":"cluster","label":"Cluster ID (optional)","type":"column","optional":True},
])
def p2_incremental_validity(df, outcome, base_predictors, focal_predictors, cluster=None):
    base=as_list(base_predictors); focal=as_list(focal_predictors)
    if not focal: raise ValueError("Select at least one focal capability predictor")
    cols=[outcome]+base+focal+([cluster] if cluster else [])
    d=df[cols].copy(); d[[outcome]+base+focal]=d[[outcome]+base+focal].apply(pd.to_numeric,errors="coerce"); d=d.dropna()
    y=d[outcome].astype(float)
    X0=sm.add_constant(d[base].astype(float),has_constant="add") if base else pd.DataFrame({"const":np.ones(len(d))},index=d.index)
    X1=sm.add_constant(d[base+focal].astype(float),has_constant="add")
    m0=sm.OLS(y,X0).fit(); m1=sm.OLS(y,X1).fit()
    if cluster:
        m1r=m1.get_robustcov_results(cov_type="cluster", groups=d[cluster])
        coef=pd.DataFrame({"B":m1r.params,"SE":m1r.bse,"t/z":m1r.tvalues,"p":m1r.pvalues},index=X1.columns)
    else:
        m1r=m1.get_robustcov_results(cov_type="HC3")
        coef=pd.DataFrame({"B":m1r.params,"SE":m1r.bse,"t/z":m1r.tvalues,"p":m1r.pvalues},index=X1.columns)
    df_num=len(focal); df_den=int(m1.df_resid)
    dr2=float(m1.rsquared-m0.rsquared)
    fchg=((m1.rsquared-m0.rsquared)/df_num)/((1-m1.rsquared)/df_den) if df_den>0 else np.nan
    pchg=float(stats.f.sf(fchg,df_num,df_den)) if np.isfinite(fchg) else np.nan
    out=Output("p2_incremental_validity","P2 · Incremental validity (ΔR²)",{}); out.n_used=len(d)
    out.table(pd.DataFrame([{"N":len(d),"Base R²":m0.rsquared,"Full R²":m1.rsquared,"ΔR²":dr2,"F change":fchg,"df1":df_num,"df2":df_den,"p change":pchg}]),"Hierarchical model comparison")
    out.table(coef,"Full-model coefficients",f"Inference: {'cluster-robust' if cluster else 'HC3 robust'} standard errors.")
    return out


def _rscript() -> str | None:
    for c in ["Rscript","/opt/homebrew/bin/Rscript","/usr/local/bin/Rscript","/Library/Frameworks/R.framework/Resources/bin/Rscript"]:
        p=shutil.which(c) or (c if Path(c).exists() else None)
        if p:return str(p)
    return None


INVARIANCE_R = r'''
suppressMessages(library(lavaan)); suppressMessages(library(jsonlite))
a <- commandArgs(TRUE); d <- read.csv(a[1], check.names=FALSE); m <- paste(readLines(a[2]),collapse="\n"); g <- a[3]; est <- a[4]
gp <- if(length(a)>=5 && nzchar(a[5])) strsplit(a[5],"\\|")[[1]] else character(0)
fitone <- function(equal=NULL, partial=NULL){
  cfa(m, data=d, group=g, estimator=est, missing="fiml", std.lv=TRUE, meanstructure=TRUE,
      group.equal=if(is.null(equal)) character(0) else equal,
      group.partial=if(is.null(partial)) character(0) else partial)
}
f0 <- fitone(); f1 <- fitone(c("loadings")); f2 <- fitone(c("loadings","intercepts"))
fits <- list(configural=f0, metric=f1, scalar=f2)
if(length(gp)>0) fits$partial_scalar <- fitone(c("loadings","intercepts"), gp)
fm <- lapply(fits,function(f){ as.list(fitMeasures(f,c("chisq","df","pvalue","cfi","tli","rmsea","srmr","aic","bic"))) })
out <- list(fit=fm, converged=lapply(fits,lavInspect,"converged"), n=lavInspect(f0,"nobs"), lavaan=as.character(packageVersion("lavaan")))
cat(toJSON(out,digits=NA,auto_unbox=TRUE))
'''


def _run_group_invariance(df, model, group, estimator="MLR", partial=None):
    rs=_rscript()
    if not rs: raise RuntimeError("Measurement invariance requires R + lavaan. Install R, then in R run install.packages(c('lavaan','jsonlite')).")
    vars_=sorted(set(re.findall(r"[A-Za-z_][A-Za-z0-9_.]*",model)) & set(df.columns))
    if group not in df.columns: raise ValueError(f"Group variable {group!r} not found")
    with tempfile.TemporaryDirectory() as td:
        path=Path(td); df[vars_+[group]].to_csv(path/"d.csv",index=False); (path/"m.lav").write_text(model,encoding="utf-8"); (path/"run.R").write_text(INVARIANCE_R,encoding="utf-8")
        gp="|".join(as_list(partial))
        r=subprocess.run([rs,str(path/"run.R"),str(path/"d.csv"),str(path/"m.lav"),group,estimator,gp],capture_output=True,text=True,timeout=600)
    if r.returncode!=0: raise RuntimeError("lavaan invariance error: "+r.stderr[-1200:])
    return json.loads(r.stdout)


def _fit_table(res: dict) -> pd.DataFrame:
    rows=[]; prev=None
    for name,f in res["fit"].items():
        row={"model":name,**f}
        if prev is not None:
            row["ΔCFI"] = float(f.get("cfi",np.nan)-prev.get("cfi",np.nan)); row["ΔRMSEA"] = float(f.get("rmsea",np.nan)-prev.get("rmsea",np.nan))
        rows.append(row); prev=f
    return pd.DataFrame(rows).set_index("model")


@analysis("p2_group_invariance", "P2 · Measurement invariance (configural → metric → scalar)", "Paper 2 · Measurement", [
    {"name":"model","label":"lavaan measurement model","type":"textarea"},
    {"name":"group","label":"Group/time variable","type":"column"},
    {"name":"estimator","label":"Estimator","type":"choice","choices":["MLR","ML"],"default":"MLR"},
    {"name":"partial","label":"Partial-scalar parameters to free, separated by commas (e.g. item1~1,item4~1)","type":"text","optional":True},
])
def p2_group_invariance(df, model, group, estimator="MLR", partial=None):
    r=_run_group_invariance(df,model,group,estimator,partial)
    out=Output("p2_group_invariance","P2 · Measurement invariance",{}); out.n_used=int(sum(r["n"])) if isinstance(r["n"],list) else int(r["n"])
    out.table(_fit_table(r),"Sequential invariance models")
    out.note("Interpret invariance from the pre-specified combination of absolute fit and change-in-fit criteria; do not use a single cutoff mechanically. Partial scalar constraints must be theory/evidence justified and pre-declared where possible.")
    return out


def build_longitudinal_models(spec: dict, partial_items: list[str] | None = None) -> dict[str,str]:
    """Generate configural/metric/scalar longitudinal CFA syntax with correlated uniquenesses."""
    partial=set(partial_items or [])
    lines0=[]; lines1=[]; lines2=[]; residual=[]; latents=[]
    for fac,waves in spec.items():
        if not isinstance(waves,dict) or set(waves)<{"t1","t2"}: raise ValueError(f"{fac}: expected {{'t1':[...], 't2':[...]}}")
        a=[str(x) for x in waves["t1"]]; b=[str(x) for x in waves["t2"]]
        if len(a)!=len(b) or len(a)<2: raise ValueError(f"{fac}: t1/t2 item lists must have equal length >=2")
        f1,f2=f"{fac}_T1",f"{fac}_T2"
        lines0 += [f"{f1} =~ " + " + ".join(a), f"{f2} =~ " + " + ".join(b)]
        l1=[]; l2=[]
        for i,(x,y) in enumerate(zip(a,b),1):
            lab=f"l_{fac}_{i}"; l1.append(f"{lab}*{x}"); l2.append(f"{lab}*{y}")
            residual.append(f"{x} ~~ {y}")
            if x in partial or y in partial:
                lines2 += [f"{x} ~ int_{fac}_{i}_t1*1",f"{y} ~ int_{fac}_{i}_t2*1"]
            else:
                lines2 += [f"{x} ~ int_{fac}_{i}*1",f"{y} ~ int_{fac}_{i}*1"]
        lines1 += [f"{f1} =~ "+" + ".join(l1),f"{f2} =~ "+" + ".join(l2)]
        latents.append(f"{f1} ~~ {f2}")
    base_extra=residual+latents
    metric=lines1+base_extra
    return {"configural":"\n".join(lines0+base_extra),"metric":"\n".join(metric),"scalar":"\n".join(metric+lines2)}


LONG_R = r'''
suppressMessages(library(lavaan)); suppressMessages(library(jsonlite))
a <- commandArgs(TRUE); d <- read.csv(a[1],check.names=FALSE); est <- a[5]
fitone <- function(f){ sem(paste(readLines(f),collapse="\n"),data=d,estimator=est,missing="fiml",std.lv=TRUE,meanstructure=TRUE) }
f0<-fitone(a[2]); f1<-fitone(a[3]); f2<-fitone(a[4]); fits<-list(configural=f0,metric=f1,scalar=f2)
fm<-lapply(fits,function(f) as.list(fitMeasures(f,c("chisq","df","pvalue","cfi","tli","rmsea","srmr","aic","bic"))))
out<-list(fit=fm,converged=lapply(fits,lavInspect,"converged"),n=lavInspect(f0,"nobs"),lavaan=as.character(packageVersion("lavaan")))
cat(toJSON(out,digits=NA,auto_unbox=TRUE))
'''


@analysis("p2_longitudinal_invariance", "P2 · Longitudinal measurement invariance (T1/T2)", "Paper 2 · Measurement", [
    {"name":"waves","label":"JSON: construct -> {t1:[items], t2:[items]}","type":"textarea"},
    {"name":"partial_items","label":"Items allowed non-invariant intercepts (comma-separated, optional)","type":"text","optional":True},
    {"name":"estimator","label":"Estimator","type":"choice","choices":["MLR","ML"],"default":"MLR"},
])
def p2_longitudinal_invariance(df, waves, partial_items=None, estimator="MLR"):
    spec=json.loads(waves); models=build_longitudinal_models(spec,as_list(partial_items))
    rs=_rscript()
    if not rs: raise RuntimeError("Longitudinal invariance requires R + lavaan. Install R, then install.packages(c('lavaan','jsonlite')).")
    vars_=sorted({x for w in spec.values() for k in ("t1","t2") for x in w[k]})
    miss=[x for x in vars_ if x not in df.columns]
    if miss: raise ValueError(f"Variables not found: {miss}")
    with tempfile.TemporaryDirectory() as td:
        p=Path(td); df[vars_].to_csv(p/"d.csv",index=False); (p/"run.R").write_text(LONG_R,encoding="utf-8")
        files=[]
        for key in ("configural","metric","scalar"):
            q=p/f"{key}.lav"; q.write_text(models[key],encoding="utf-8"); files.append(str(q))
        r=subprocess.run([rs,str(p/"run.R"),str(p/"d.csv"),*files,estimator],capture_output=True,text=True,timeout=600)
    if r.returncode!=0: raise RuntimeError("lavaan longitudinal invariance error: "+r.stderr[-1200:])
    res=json.loads(r.stdout)
    out=Output("p2_longitudinal_invariance","P2 · Longitudinal measurement invariance (T1/T2)",{}); out.n_used=int(res["n"])
    out.table(_fit_table(res),"Longitudinal invariance sequence")
    with_models=pd.DataFrame({"model":list(models),"lavaan syntax":[models[k] for k in models]}).set_index("model")
    out.table(with_models,"Generated frozen model syntax")
    out.note("Same-item residuals are correlated across waves. Metric models constrain corresponding loadings equal; scalar models additionally constrain corresponding intercepts equal except pre-specified partial-invariance items.")
    return out


@analysis("p2_followup_attrition", "P2 · 12-month follow-up attrition diagnostics", "Paper 2 · Measurement", [
    {"name":"followup_variables","label":"Variables expected at follow-up","type":"columns","multi":True},
    {"name":"baseline_predictors","label":"Baseline predictors of retention (optional)","type":"columns","multi":True,"optional":True,"numeric":True},
])
def p2_followup_attrition(df, followup_variables, baseline_predictors=None):
    fu=as_list(followup_variables); base=as_list(baseline_predictors)
    if not fu: raise ValueError("Select follow-up variables")
    complete=df[fu].notna().all(axis=1).astype(int)
    out=Output("p2_followup_attrition","P2 · 12-month follow-up attrition diagnostics",{}); out.n_used=len(df)
    out.table(pd.DataFrame([{"baseline N":len(df),"complete follow-up":int(complete.sum()),"incomplete/lost":int((1-complete).sum()),"retention rate":float(complete.mean())}]),"Follow-up status")
    if base:
        X=numeric(df,base); d=pd.concat([complete.rename("retained"),X],axis=1).dropna()
        Xd=sm.add_constant(d[base],has_constant="add")
        m=sm.Logit(d["retained"],Xd).fit(disp=False)
        tab=pd.DataFrame({"B":m.params,"SE":m.bse,"OR":np.exp(m.params),"p":m.pvalues})
        out.table(tab,"Baseline predictors of complete follow-up")
    return out
