import json
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd

from clockbind.analysis import REGISTRY, run
from clockbind.stats.dce import prepare_choice_data, fit_mnl, swait_louviere, fit_mixed_logit, fit_hb_mnl
from clockbind.analysis.paper2 import htmt_matrix, build_longitudinal_models
from clockbind.publication import build_prereg_bundle, consistency_audit


def conjoint_df(n_resp=12, tasks=6, seed=7):
    rng=np.random.default_rng(seed); rows=[]
    for r in range(n_resp):
        for t in range(tasks):
            f='HIGH' if t%2==0 else 'LOW'
            vals=[]
            for p in ['A','B']:
                x=int(rng.integers(0,2)); z=int(rng.integers(0,2)); u=.7*x-.3*z + rng.normal(scale=.2)
                vals.append((p,x,z,u))
            pick=int(np.argmax([x[3] for x in vals])) if rng.random()>.15 else -1
            for j,(p,x,z,u) in enumerate(vals):
                rows.append({'respondent':r,'task':t,'profile':p,'a':str(x),'b':str(z),'enforceability':f,'chosen':int(j==pick)})
    return pd.DataFrame(rows)


def test_registry_has_all_paper_engines():
    for name in ['p1_mixed_logit','p1_hb_mnl','p2_longitudinal_invariance','p3_fsqca','p3_survival_cox','p4_process_trace']:
        assert name in REGISTRY


def test_p1_mnl_and_swait_louviere():
    d=conjoint_df()
    cd=prepare_choice_data(d,['a','b'],'chosen','respondent','task','profile',factor='enforceability',interact_factor=False)
    m=fit_mnl(cd); s=swait_louviere(cd)
    assert m['success']
    assert np.isfinite(m['loglike'])
    assert s['converged']
    assert s['relative_scale_group2_to_group1']>0


def test_p1_mixed_and_hb_smoke():
    d=conjoint_df(n_resp=8,tasks=4)
    cd=prepare_choice_data(d,['a','b'],'chosen','respondent','task','profile')
    mx=fit_mixed_logit(cd,[cd.terms[0]],n_draws=16,seed=1)
    hb=fit_hb_mnl(cd,iterations=20,burn=6,thin=2,seed=1,step_scale=.1)
    assert mx['success']
    assert len(hb['population'])==len(cd.terms)
    assert len(hb['individual_means'])==8


def test_p2_htmt_and_longitudinal_syntax():
    rng=np.random.default_rng(1)
    d=pd.DataFrame({f'a{i}':rng.normal(size=60) for i in range(3)}|{f'b{i}':rng.normal(size=60) for i in range(3)})
    h=htmt_matrix(d,{'A':['a0','a1','a2'],'B':['b0','b1','b2']})
    assert h.shape==(2,2) and h.loc['A','A']==1
    m=build_longitudinal_models({'F':{'t1':['x1_t1','x2_t1'],'t2':['x1_t2','x2_t2']}},['x2_t1'])
    assert set(m)=={'configural','metric','scalar'}
    assert 'l_F_1*x1_t1' in m['metric']
    assert 'int_F_1*1' in m['scalar']
    assert 'int_F_2_t1*1' in m['scalar']


def test_p2_incremental_validity_runs():
    rng=np.random.default_rng(2); n=100
    d=pd.DataFrame({'base':rng.normal(size=n),'cap':rng.normal(size=n)})
    d['y']=.4*d['base']+.5*d['cap']+rng.normal(size=n)
    o=run('p2_incremental_validity',d,{'outcome':'y','base_predictors':'base','focal_predictors':'cap'})
    assert o.n_used==100
    assert any(b.kind=='table' for b in o.blocks)


def test_p3_fsqca_panel_survival_run():
    rng=np.random.default_rng(3); n=80
    q=pd.DataFrame({'A':rng.uniform(size=n),'B':rng.uniform(size=n),'C':rng.uniform(size=n)})
    q['Y']=np.minimum(q.A,q.B)*.85+rng.uniform(0,.15,size=n); q['Y']=q.Y.clip(0,1)
    o=run('p3_fsqca',q,{'conditions':'A,B,C','outcome':'Y','frequency_cutoff':1,'consistency_cutoff':.75,'pri_cutoff':.3})
    assert o.n_used==n
    p=pd.DataFrame({'x1':rng.normal(size=n),'y1':rng.normal(size=n)}); p['x2']=p.x1+rng.normal(size=n); p['y2']=p.y1+.4*(p.x2-p.x1)+rng.normal(size=n)
    assert run('p3_panel_first_difference',p,{'outcome_t1':'y1','outcome_t2':'y2','predictor_pairs':json.dumps({'x':['x1','x2']})}).n_used==n
    s=pd.DataFrame({'t':rng.exponential(3,size=n)+.1,'status':rng.binomial(1,.7,size=n),'x':rng.normal(size=n)})
    assert run('p3_survival_cox',s,{'duration':'t','status':'status','covariates':'x'}).n_used==n


def test_p4_process_and_case_matrix():
    d=pd.DataFrame([
        {'case':'C1','code':'control','source':'S1','direction':'support','form':'franchise'},
        {'case':'C1','code':'control','source':'S2','direction':'oppose','form':'franchise'},
        {'case':'C2','code':'risk','source':'S3','direction':'support','form':'licence'},
    ])
    o=run('p4_case_matrix',d,{'case':'case','code':'code','source':'source','direction':'direction','governance_form':'form'})
    assert o.n_used==2
    pt=pd.DataFrame([{'case':'C1','prop':'P1','test':'hoop','result':'pass','source':'S1'}, {'case':'C1','prop':'P1','test':'smoking-gun','result':'pass','source':'S2'}])
    po=run('p4_process_trace',pt,{'case':'case','proposition':'prop','test_type':'test','result':'result','source':'source'})
    assert po.n_used==1


def test_prereg_bundle_refuses_data_and_marks_no_external_registration(tmp_path):
    protocol=tmp_path/'plan.json'; protocol.write_text('{"study":"x"}')
    out=tmp_path/'pre.zip'; build_prereg_bundle(None,[protocol],out,'DRAFT')
    with zipfile.ZipFile(out) as z:
        manifest=json.loads(z.read('ClockBind_preregistration_package/PREREG_MANIFEST.json'))
    assert manifest['external_registration'] is False
    data=tmp_path/'data.csv'; data.write_text('x\n1\n')
    try:
        build_prereg_bundle(None,[data],tmp_path/'bad.zip','DRAFT')
    except ValueError:
        pass
    else:
        raise AssertionError('row-level data should be refused')


def test_manuscript_consistency_registry(tmp_path):
    m=tmp_path/'m.txt'; m.write_text('Sample N = 150. The result suggests a mechanism.')
    r=tmp_path/'r.json'; r.write_text(json.dumps({'checks':[{'id':'N','expected':'N = 150','required':True,'forbidden':['N = 90']}]}))
    rows,s=consistency_audit(m,r)
    assert s['fail']==0 and rows[0]['status']=='PASS'


def test_pri_matches_ragin_formula():
    import numpy as np
    from clockbind.analysis.paper3 import _pri
    x = np.array([.8, .9, .3, .6]); y = np.array([.2, .9, .9, .7])
    a = np.minimum(x, y).sum(); b = np.minimum(np.minimum(x, y), 1 - y).sum()
    assert abs(_pri(x, y) - (a - b) / (x.sum() - b)) < 1e-12


def test_mnl_matches_statsmodels_conditional_logit():
    import numpy as np, pandas as pd
    from statsmodels.discrete.conditional_models import ConditionalLogit
    from clockbind.stats import dce
    rng = np.random.default_rng(7); rows = []
    B = {"price": {"low": 0, "high": -1.0}, "brand": {"A": 0, "B": 0.8}}
    for r in range(150):
        for t in range(6):
            alts = [({k: rng.choice(list(v)) for k, v in B.items()}) for _ in range(2)]
            u = [sum(B[k][lv[k]] for k in B) + rng.gumbel() for lv in alts] + [-0.3 + rng.gumbel()]
            best = int(np.argmax(u))
            for a, lv in enumerate(alts):
                rows.append({"resp": r, "task": t, "alt": a, **lv, "chosen": int(best == a)})
    cd = dce.prepare_choice_data(pd.DataFrame(rows), ["price", "brand"], "chosen", "resp", task="task", alternative="alt",
                                 baselines={"price": "low", "brand": "A"})
    fit = dce.fit_mnl(cd)
    g = np.empty(len(cd.y), int)
    for i, s in enumerate(cd.set_slices):
        g[s] = i
    ref = ConditionalLogit(cd.y, cd.X, groups=g).fit(disp=0)
    assert np.allclose(fit["coef"], ref.params, atol=1e-3)
    assert np.allclose(fit["table"]["se"].values, ref.bse, rtol=1e-3)
