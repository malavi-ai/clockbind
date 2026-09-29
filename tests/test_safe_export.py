import json
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

from clockbind.safe_export import build_safe_zip

ROOT = Path(__file__).resolve().parents[1]


def test_safe_export_has_no_paths_or_cells():
    cands = sorted((ROOT / "examples" / "screening").glob("*.xlsx"))
    gates = ROOT / "examples" / "screening" / "gates_v3.4_DRAFT.json"
    if not cands or not gates.exists():
        pytest.skip("synthetic Bridge example unavailable")
    raw = build_safe_zip(str(cands[0]), str(gates))
    with zipfile.ZipFile(BytesIO(raw)) as z:
        p = json.loads(z.read("ai_safe_summary.json"))
    assert p["privacy_contract"]["contains_cell_values"] is False
    assert p["privacy_contract"]["contains_input_paths"] is False
    text = json.dumps(p)
    assert str(cands[0].resolve()) not in text
    assert "workbook_sha256" in p["inputs"] and len(p["inputs"]["workbook_sha256"]) == 64
