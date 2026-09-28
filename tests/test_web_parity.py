"""The browser engine (webapp/engine.js) must give the same levels, counts and checks as the Python engine."""
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
def test_javascript_engine_matches_python():
    d = Path(__file__).resolve().parents[1] / "webapp" / "parity"
    r = subprocess.run(["node", "parity.js"], cwd=d, capture_output=True, text=True, timeout=120)
    assert "ALL CASES IDENTICAL" in r.stdout, r.stdout[-2000:]
