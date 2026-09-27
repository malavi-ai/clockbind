"""Known-answer tests. Run: pytest -q"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from clockbind.dgp import paper3
from clockbind.stats import conjoint as C
from clockbind.stats import weights as W
from clockbind.stats.robust import wls_cluster
from clockbind.stats.simulation import performance

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def p3():
    df, _ = paper3.simulate({"n_firms": 120}, np.random.default_rng(1))
    fit = W.fit_ps(df, "arm", ["x1", "x2", "x3"])
    return df, fit, W.gow_weights(fit)


def test_cr1_matches_statsmodels(p3):
    df, fit, w = p3
    X, y = W.arm_design(fit), df["y"].to_numpy(float)
    r = wls_cluster(y, X, w, df["firm"].to_numpy(), "CR1")
    ref = sm.WLS(y, X, weights=w).fit(cov_type="cluster", cov_kwds={"groups": df["firm"].to_numpy()})
    assert np.allclose(r.coef, ref.params, atol=1e-12)
    assert np.allclose(r.vcov, ref.cov_params(), atol=1e-12)


def test_cr2_singletons_equal_hc2():
    rng = np.random.default_rng(2)
    X = np.column_stack([np.ones(200), rng.normal(size=(200, 2))])
    y = X @ [1, 0.5, -0.2] + rng.normal(size=200) * (1 + np.abs(X[:, 1]))
    r = wls_cluster(y, X, None, None, "CR2")
    assert np.allclose(r.vcov, sm.OLS(y, X).fit(cov_type="HC2").cov_params(), atol=1e-12)


def test_overlap_weights_exact_balance_two_arms():
    rng = np.random.default_rng(0)
    x1, x2 = rng.normal(size=800), rng.normal(size=800)
    p = 1 / (1 + np.exp(-(0.8 * x1 - 0.5 * x2)))
    df = pd.DataFrame({"t": np.where(rng.random(800) < p, "b", "a"), "x1": x1, "x2": x2})
    fit = W.fit_ps(df, "t", ["x1", "x2"])
    bal = W.balance_table(df, fit, W.gow_weights(fit), ["x1", "x2"])
    assert bal["max_smd_weighted"].abs().max() < 1e-10


def test_gow_formula(p3):
    _, fit, w = p3
    h = 1 / (1 / fit.ps).sum(axis=1)
    assert np.allclose(w, h / fit.ps[np.arange(len(fit.z)), fit.z])


def test_weighted_means_equal_wls_coefficients(p3):
    df, fit, w = p3
    y = df["y"].to_numpy(float)
    r = wls_cluster(y, W.arm_design(fit), w, df["firm"].to_numpy())
    mu = [np.average(y[fit.z == k], weights=w[fit.z == k]) for k in range(4)]
    assert np.allclose(r.coef, mu)


def test_contrast_must_sum_to_zero():
    with pytest.raises(ValueError):
        W.parse_contrast("a:1,b:1", ["a", "b"])
    assert list(W.parse_contrast("b-a", ["a", "b"])) == [-1, 1]


def test_conjoint_design_rules():
    cfg = json.loads((ROOT / "examples" / "conjoint_config.json").read_text())
    d = C.generate_design(cfg, np.random.default_rng(3))
    attrs = list(cfg["attributes"])
    for _, g in d.groupby(["block", "task"]):
        assert len(g) == 2
        assert not (g.iloc[0][attrs] == g.iloc[1][attrs]).all()
        assert g["enforceability"].nunique() == 1
    per_block = d.drop_duplicates(["block", "task"]).groupby("block")["enforceability"].value_counts().unstack()
    assert (per_block["HIGH"] == per_block["LOW"]).all()


def test_performance_known_values():
    est = np.array([0.0, 2.0]); se = np.array([1.0, 1.0])
    out = performance(est, se, est - 2, est + 2, np.array([0.5, 0.01]), truth=1.0)
    assert out["bias"] == 0.0 and out["coverage"] == 1.0 and out["rejection_rate"] == 0.5


def test_cli_writes_manifest(tmp_path, p3):
    df, _, _ = p3
    data = tmp_path / "d.csv"; df.to_csv(data, index=False)
    r = subprocess.run([sys.executable, "-m", "clockbind", "weights", "diagnose", "--data", str(data), "--treatment", "arm",
                        "--covariates", "x1,x2,x3", "--cluster", "firm", "--out", str(tmp_path / "runs")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    man = json.loads(next((tmp_path / "runs").glob("*/manifest.json")).read_text())
    assert man["status"] == "completed" and man["outcome_used"] is False
    assert all(v for v in man["outputs"].values())
    assert man["inputs"]["data"]["sha256"]


@pytest.mark.skipif(shutil.which("Rscript") is None, reason="R not installed")
def test_agrees_with_R(tmp_path, p3):
    df, _, _ = p3
    data = tmp_path / "d.csv"; df.to_csv(data, index=False)
    r = subprocess.run([sys.executable, "-m", "clockbind", "validate", "weights", "--data", str(data), "--treatment", "arm",
                        "--covariates", "x1,x2,x3", "--outcome", "y", "--cluster", "firm", "--out", str(tmp_path / "runs")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_screen_gates_and_freeze(tmp_path):
    import json, shutil
    import pandas as pd
    from clockbind.plugins.screen import apply_gates, load_gates, gates_hash
    ex = Path(__file__).resolve().parents[1] / "examples" / "screening"
    g = load_gates(ex / "gates_v2_DRAFT.json")
    df = pd.read_excel(ex / "SYNTHETIC_screening_demo.xlsx", dtype=str)
    entries, eps, probs = apply_gates(df, g)
    assert len(entries) == 30
    # the planted conflict inside episode X02 must be caught and must not pass
    assert ((probs["where"] == "X02") & probs["problem"].str.contains("Conflicting")).any()
    assert eps.set_index("episode_id").loc["X02", "final_status"].startswith("Held")
    # a Tier C episode fails v2 but can pass the explicit mechanism path in v2b
    g2 = load_gates(ex / "gates_v2b_mechanism_DRAFT.json")
    _, eps2, _ = apply_gates(df, g2)
    assert (eps2.final_status.str.contains("Mechanism core")).sum() >= 1
    # hash covers everything, including freeze metadata (so dates cannot be backdated)
    h = gates_hash(g)
    g["frozen_on"] = "2026-08-01"
    assert gates_hash(g) != h


def test_screen_integrity(tmp_path):
    import json, shutil
    import pandas as pd
    import pytest
    from clockbind.plugins.screen import apply_gates, load_gates, _agreement_stats
    ex = Path(__file__).resolve().parents[1] / "examples" / "screening"
    g = load_gates(ex / "gates_v3_nested_DRAFT.json")
    df = pd.read_excel(ex / "SYNTHETIC_screening_demo.xlsx", dtype=str, keep_default_na=False)
    # invalid values are flagged, never silently failed
    d = df.copy(); d.loc[0, "S0_organisational"] = "Yes"; d.loc[1, "S0_organisational"] = "y"
    _, _, probs = apply_gates(d, g)
    assert probs["problem"].str.contains("'Yes' is not an allowed value").any()
    assert not probs["problem"].str.contains("'y' is not").any()   # case variant canonicalised
    # episode IDs differing in case/space are merged and flagged
    d = df.copy(); d.loc[1, "episode_id"] = "x01 "
    _, eps, probs = apply_gates(d, g)
    assert probs["problem"].str.contains("different forms").any()
    assert eps["episode_id"].str.casefold().is_unique
    # duplicate entry IDs stop the run
    d = pd.concat([df, df.iloc[[0]]])
    with pytest.raises(SystemExit):
        apply_gates(d, g)
    # levels: every analysable episode gets exactly one level
    _, eps, _ = apply_gates(df, g)
    assert eps["level"].notna().all()
    # AC1 on the full scale; perfect agreement on one category gives 1
    assert abs(_agreement_stats(list("YYYNN"), list("YYNNY"), ["Y", "N"])[1] - 1 / 6) < 1e-9
    assert _agreement_stats(list("YYYYY"), list("YYYYY"), ["Y", "N", "Unknown"])[2] == 1.0


def test_screen_freeze_register(tmp_path):
    import json, shutil, subprocess, sys
    ex = Path(__file__).resolve().parents[1] / "examples" / "screening"
    gp = tmp_path / "g.json"
    g = json.load(open(ex / "gates_v3_nested_DRAFT.json"))
    g["protocol_version"] = "v3-test"
    json.dump(g, open(gp, "w"))
    run = lambda *a: subprocess.run([sys.executable, "-m", "clockbind", "screen", *a], capture_output=True, text=True)
    assert run("freeze", "--gates", str(gp), "--by", "T").returncode == 0
    assert (tmp_path / "FREEZE_REGISTER.jsonl").exists()
    # tamper + rehash must be caught against the register
    from clockbind.plugins.screen import gates_hash
    g2 = json.load(open(gp)); g2["stages"][2]["criteria"][2]["allowed"] = ["A", "B", "C"]; g2["sha256"] = gates_hash(g2)
    json.dump(g2, open(gp, "w"))
    r = run("run", "--data", str(ex / "SYNTHETIC_screening_demo.xlsx"), "--gates", str(gp), "--out", str(tmp_path / "o"))
    assert r.returncode != 0 and "Re-freezing" in (r.stdout + r.stderr)
    # unfreezing and re-freezing the same version is refused
    g2["frozen"] = False; json.dump(g2, open(gp, "w"))
    r = run("freeze", "--gates", str(gp), "--by", "T")
    assert r.returncode != 0


def test_all_analyses_run_and_export(tmp_path):
    import pandas as pd
    import clockbind.analysis as A
    root = Path(__file__).resolve().parents[1]
    df = pd.read_csv(root / "validation" / "validation_data.csv")
    specs = [("frequencies", dict(variables="g3")), ("descriptives", dict(variables="y", by="g2")), ("normality", dict(variables="y")),
             ("crosstabs", dict(row="g2", col="ycat")), ("t_independent", dict(variables="y", group="g2")), ("t_paired", dict(first="pre", second="post")),
             ("t_one_sample", dict(variables="x1")), ("anova_oneway", dict(variable="y", group="g3")), ("mann_whitney", dict(variables="y", group="g2")),
             ("wilcoxon", dict(first="pre", second="post")), ("kruskal", dict(variable="y", group="g3")), ("correlation", dict(variables="x1,y")),
             ("regression_linear", dict(y="y", x="x1", se="CR2", cluster="firm")), ("regression_logistic", dict(y="ybin", x="x1")),
             ("regression_multinomial", dict(y="ycat", x="x1")), ("regression_ordinal", dict(y="yord", x="x1")), ("reliability", dict(items="q1,q2,q3")),
             ("agreement", dict(rater1="rater1", rater2="rater2")), ("icc", dict(raters="icc1,icc2")), ("efa", dict(items="q1,q2,q3,q4,q5,q6", n_factors=2)),
             ("power", dict()), ("missing", dict())]
    outs = [A.run(n, df, p) for n, p in specs]
    assert all(o.blocks for o in outs)
    doc = A.outputs_to_docx(outs, tmp_path / "o.docx")
    assert doc.stat().st_size > 10000
    assert '"steps"' in A.syntax_file(outs)


# ---------------------------------------------------------------- privacy scan (GDPR / KVKK aid)
def test_privacy_scan_detects_and_ignores():
    import pandas as pd
    from clockbind.privacy import classify, scan_dataframe, _hu_tax_ok
    assert classify("mehdi@example.com") == ["e-mail address"]
    assert "phone number" in classify("+36 30 123 4567")
    assert "phone number" in classify("0532 123 45 67")
    assert "bank account (IBAN)" in classify("HU42 1177 3016 1111 1018 0000 0000")
    assert "bank account (IBAN)" in classify("DE89370400440532013000")
    assert "Turkish ID number (TCKN)" in classify("10000000146")
    assert "payment card number" in classify("4111 1111 1111 1111")
    # a valid Hungarian tax ID constructed from the checksum rule
    base = "812345678"; cd = sum(int(c) * (i + 1) for i, c in enumerate(base)) % 11
    if cd < 10:
        assert _hu_tax_ok(base + str(cd))
    for clean in ["-0.1234567890123456", "3.1415926535897932", "Company A", "Firm 3", "EP-D01", "12500", "0.123456789", "2026-09-27", "01.02.2026", "Level 3", "A", "", None, "R003", "DE89370400440532013001"]:
        assert classify(clean) == [], clean
    df = pd.DataFrame({"episode_id": ["EP-D01", "EP-D02"], "Müşteri adı": ["Anna Kovács", "Ali Yılmaz"], "contact": ["a@b.co", ""], "amount": ["100", "0.25"]})
    f = scan_dataframe(df)
    cols = {(x["column"], x["kind"]) for x in f}
    assert ("contact", "e-mail address") in cols
    assert any(c == "Müşteri adı" for c, _ in cols)
    assert not any(c in ("episode_id", "amount") for c, _ in cols)
    coded = pd.DataFrame({"company": ["Company A", "Company B", "Company C", "Company D", "Company E"]})
    assert scan_dataframe(coded) == []  # pseudonymous codes are not flagged
    assert all(set(x) == {"column", "kind", "count"} for x in f)  # never returns values


# ---------------------------------------------------------------- command-line smoke tests (clean-install regressions)
def test_cli_screen_and_privacy(tmp_path):
    import json, subprocess, sys
    import pandas as pd
    root = Path(__file__).resolve().parents[1]
    rows = json.loads((root / "webapp" / "demo_rows.json").read_text(encoding="utf-8"))
    sheet = tmp_path / "demo.xlsx"; pd.DataFrame(rows).to_excel(sheet, index=False)
    r = subprocess.run([sys.executable, "-m", "clockbind", "screen", "run", "--data", str(sheet),
                        "--gates", str(root / "examples" / "screening" / "gates_v3_DRAFT.json"), "--out", str(tmp_path / "runs")],
                       capture_output=True, text=True, cwd=root)
    assert r.returncode == 2, r.stderr[-800:]          # the demo contains one deliberate conflict (EP-D04)
    assert "Level 3 – binding clock  3" in r.stdout and "Citable: False" in r.stdout
    r2 = subprocess.run([sys.executable, "-m", "clockbind", "privacy", "scan", "--data", str(sheet), "--strict"], capture_output=True, text=True, cwd=root)
    assert r2.returncode == 0 and "No personal-data patterns" in r2.stdout
    pd.DataFrame({"contact": ["a@b.com"]}).to_csv(tmp_path / "p.csv", index=False)
    r3 = subprocess.run([sys.executable, "-m", "clockbind", "privacy", "scan", "--data", str(tmp_path / "p.csv"), "--strict"], capture_output=True, text=True, cwd=root)
    assert r3.returncode == 3 and "a@b.com" not in r3.stdout


def test_bundled_copies_match_originals():
    from clockbind.resources import BUNDLED, PKG, ROOT
    for name, rel in BUNDLED.items():
        assert (PKG / "data" / name).read_bytes() == (ROOT / rel).read_bytes(), f"clockbind/data/{name} is stale: run python webapp/build.py"
