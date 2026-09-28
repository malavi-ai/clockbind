"""Studio shell: profiles, three languages and the project status."""
import json
from pathlib import Path

import pytest

from clockbind import profiles
from clockbind.studio.i18n import FIX, LANGS, T, digits, fix_text, t

ROOT = Path(__file__).resolve().parents[1]


def test_every_ui_string_in_three_languages():
    for key, row in T.items():
        for L in LANGS:
            assert row.get(L), f"{key} missing {L}"
    for key, row in FIX.items():
        for L in LANGS:
            assert row.get(L) and len(row[L]) == 2, f"fix {key} missing {L}"


def test_placeholders_match_across_languages():
    import re
    for key, row in T.items():
        ph = {L: set(re.findall(r"\{(\w+)\}", row[L])) for L in LANGS}
        assert ph["en"] == ph["hu"] == ph["fa"], key
        if ph["en"]:
            t(key, "fa", **{k: "x" for k in ph["en"]})


def test_persian_digits_and_fallback():
    assert digits("45/19", "fa") == "۴۵/۱۹"
    assert digits("45", "en") == "45"
    assert fix_text("no-such-check", "hu")[0]


def test_profiles_local_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("CLOCKBIND_HOME", str(tmp_path))
    assert profiles.load() == {"profiles": [], "last": None}
    profiles.upsert({"name": "Mr Alavi", "lang": "fa", "workbook": "", "gates": ""})
    profiles.upsert({"name": "Guest", "lang": "hu", "workbook": "", "gates": ""})
    profiles.upsert({"name": "Mr Alavi", "lang": "en", "workbook": "x.xlsx", "gates": ""})
    d = json.loads((tmp_path / "profiles.json").read_text(encoding="utf-8"))
    assert [p["name"] for p in d["profiles"]] == ["Guest", "Mr Alavi"] and d["last"] == "Mr Alavi"
    assert profiles.get("Mr Alavi")["lang"] == "en"
    assert "password" not in (tmp_path / "profiles.json").read_text()
    (tmp_path / "profiles.json").write_text("{broken", encoding="utf-8")
    assert profiles.load()["profiles"] == []


def test_project_status_on_synthetic_workbook():
    from clockbind.project import project_status
    wb = ROOT / "examples" / "screening"
    cands = sorted(wb.glob("*.xlsx"))
    if not cands:
        pytest.skip("no synthetic screening workbook")
    st = project_status(str(cands[0]), str(ROOT / "examples/screening/gates_v3.3_DRAFT.json"))
    assert st["step"] in "ABCDE" and "sources" in st and "levels" in st


def test_studio_opens_and_navigates(tmp_path, monkeypatch):
    AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
    monkeypatch.setenv("CLOCKBIND_HOME", str(tmp_path))
    for L in LANGS:
        at = AppTest.from_file(str(ROOT / "clockbind/studio/app.py"), default_timeout=120).run()
        assert not at.exception
        at.text_input(key="np_name").input("Tester " + L)
        at.selectbox(key="np_lang").select(L)
        at.button[-1].click().run()
        assert not at.exception
        for k in ("nav_bridge", "nav_reports", "nav_settings", "nav_stats", "nav_home"):
            at.button(key=k).click().run()
            assert not at.exception, (L, k)
