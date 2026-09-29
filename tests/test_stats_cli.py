import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "clockbind", *args], cwd=ROOT, capture_output=True, text=True)


def test_stats_plugin_auto_discovered():
    r = run_cli("--help")
    assert r.returncode == 0, r.stderr
    assert "stats" in r.stdout


def test_stats_list_and_show():
    r = run_cli("stats", "list")
    assert r.returncode == 0, r.stderr
    assert "descriptives" in r.stdout
    assert "regression_linear" in r.stdout
    assert "reliability" in r.stdout
    r = run_cli("stats", "show", "t_independent")
    assert r.returncode == 0, r.stderr
    assert "Independent-samples t-test" in r.stdout
    assert "variables" in r.stdout and "group" in r.stdout


def test_stats_columns_does_not_print_values(tmp_path):
    data = tmp_path / "d.csv"
    pd.DataFrame({"secret_name": ["Alice Secret", "Bob Secret"], "x": [1, 2]}).to_csv(data, index=False)
    r = run_cli("stats", "columns", "--data", str(data))
    assert r.returncode == 0, r.stderr
    assert "secret_name" in r.stdout
    assert "Alice Secret" not in r.stdout and "Bob Secret" not in r.stdout


def test_stats_run_writes_reproducible_outputs(tmp_path):
    data = ROOT / "validation" / "validation_data.csv"
    out = tmp_path / "runs"
    r = run_cli("stats", "run", "--data", str(data), "--analysis", "t_independent",
                "--param", "variables=y", "--param", "group=g2", "--out", str(out))
    assert r.returncode == 0, r.stdout + r.stderr
    run_dir = next(out.glob("stats_t_independent_*"))
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "output.docx").exists()
    assert (run_dir / "tables.xlsx").exists()
    assert (run_dir / "syntax.json").exists()
    man = json.loads((run_dir / "manifest.json").read_text())
    assert man["status"] == "completed"
    assert man["inputs"]["data"]["sha256"]
    assert man["outputs"]["output.docx"]


def test_stats_json_params(tmp_path):
    data = ROOT / "validation" / "validation_data.csv"
    out = tmp_path / "runs"
    params = json.dumps({"variables": "x1,y", "method": "spearman", "chart": False})
    r = run_cli("stats", "run", "--data", str(data), "--analysis", "correlation",
                "--params", params, "--out", str(out))
    assert r.returncode == 0, r.stdout + r.stderr
    assert next(out.glob("stats_correlation_*/output.docx")).exists()


def test_stats_batch(tmp_path):
    data = ROOT / "validation" / "validation_data.csv"
    syntax = tmp_path / "plan.json"
    syntax.write_text(json.dumps({"steps": [
        {"analysis": "descriptives", "params": {"variables": "y", "chart": False}},
        {"analysis": "correlation", "params": {"variables": "x1,y", "chart": False}},
    ]}), encoding="utf-8")
    out = tmp_path / "runs"
    r = run_cli("stats", "batch", "--data", str(data), "--syntax", str(syntax), "--out", str(out))
    assert r.returncode == 0, r.stdout + r.stderr
    run_dir = next(out.glob("stats_batch_*"))
    assert (run_dir / "output.docx").exists()
    assert (run_dir / "tables.xlsx").exists()
    assert (run_dir / "syntax.json").exists()
