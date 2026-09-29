"""ClockBind Studio shell: profiles, three languages, home screen and step-by-step research tasks."""
from __future__ import annotations

import datetime as _dt
import io
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from clockbind import __version__, profiles
from clockbind.resources import resource
from clockbind.studio.i18n import LANGS, RTL, digits, fix_text, t, tx

TASK_COLORS = {"check": ("#2D6CDF", "#16307A"), "clock": ("#F5A524", "#B8620B"), "privacy": ("#12B886", "#08664E"), "report": ("#8E44EC", "#4A1E8C")}
ICONS = {
    "check": '<path d="M9 11l3 3 8-8"/><path d="M20 12v7a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h9"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "privacy": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z"/>',
    "report": '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6M9 15h6M9 18h4"/>',
}


# ------------------------------------------------------------------ style
def css(lang: str) -> str:
    rtl = lang in RTL
    font = "'Vazirmatn','IBM Plex Sans',system-ui,sans-serif" if rtl else "'IBM Plex Sans',system-ui,sans-serif"
    s = f"""
<style>
:root{{--cb-navy:#0B1B3A;--cb-blue:#2D6CDF;--cb-gold:#E0A526;--cb-gold2:#F5C04A;--cb-green:#0FA37F;--cb-violet:#8E44EC;--cb-muted:#5A6778;--cb-line:#D5DCE1}}
.stApp{{background:radial-gradient(900px 500px at 90% -10%,#cfdcf0,transparent),radial-gradient(700px 400px at 0% 110%,#e3dcf5,transparent),#E6ECF4}}
header[data-testid="stHeader"]{{background:transparent}}
.block-container,[data-testid="stMainBlockContainer"]{{padding-top:2.2rem!important;max-width:1280px}}
html,body,[class*="css"],.stMarkdown,p,li,label,input,textarea,button{{font-family:{font}}}
.cb-top{{background:linear-gradient(90deg,#0B1B3A 0%,#16307A 55%,#3B1E7A 100%);color:#E9EEF3;border-radius:18px;padding:14px 22px;display:flex;align-items:center;justify-content:space-between;gap:16px;box-shadow:0 18px 36px -20px rgba(11,27,58,.8);margin-bottom:10px}}
.cb-top .b{{display:flex;gap:12px;align-items:center}}.cb-top b{{font:600 24px/1 'Newsreader',Georgia,serif;letter-spacing:-.02em}}.cb-top small{{display:block;opacity:.7;font-size:12.5px;margin-top:3px}}
.cb-top .who{{font-size:13px;opacity:.9;border:1px solid rgba(233,238,243,.3);border-radius:999px;padding:6px 14px}}
.cb-card{{background:linear-gradient(135deg,#fff,#f3f7ff);border-radius:22px;padding:22px 24px;box-shadow:0 2px 4px rgba(11,27,58,.06),0 26px 50px -30px rgba(11,27,58,.55);margin-bottom:12px}}
.cb-card.blue{{border-top:5px solid #2D6CDF}}.cb-card.gold{{border-top:5px solid #E0A526}}.cb-card.green{{border-top:5px solid #0FA37F}}.cb-card.violet{{border-top:5px solid #8E44EC}}
.cb-hello{{font-size:30px;font-weight:700;margin:0 0 4px;color:#0B1B3A}}.cb-sub{{color:#5A6778;margin:0 0 12px;font-size:15px;line-height:1.6}}
.cb-ring{{width:140px;height:140px;border-radius:50%;display:grid;place-items:center;box-shadow:0 18px 30px -18px rgba(11,27,58,.6)}}
.cb-ring>div{{width:104px;height:104px;border-radius:50%;background:linear-gradient(145deg,#fff,#eef2f5);display:grid;place-items:center;text-align:center;box-shadow:inset 0 2px 6px rgba(11,27,58,.12)}}
.cb-ring b{{font-size:28px;display:block;line-height:1.1;color:#0B1B3A}}.cb-ring small{{font-size:11.5px;color:#5A6778}}
.cb-road{{display:flex;gap:6px;flex-wrap:wrap}}.cb-road span{{font-size:12.5px;padding:6px 10px;border-radius:9px;background:#e3e9f3;color:#34425a}}
.cb-road .done{{background:#0FA37F;color:#fff}}.cb-road .now{{background:#F5C04A;color:#0B1B3A;font-weight:700}}
.cb-lg{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}.cb-lg div{{border-radius:12px;padding:10px 12px;border:2px solid}}.cb-lg b{{font-size:24px;display:block}}.cb-lg span{{font-size:12px;color:#5A6778}}
.cb-kpis{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-top:10px}}.cb-kpi{{border-radius:12px;padding:10px 12px;border:2px solid #e6ecf4;background:#fff}}.cb-kpi b{{font-size:20px}}.cb-kpi span{{display:block;font-size:12px;color:#5A6778}}
.cb-task{{position:relative;overflow:hidden;border-radius:22px;padding:22px 20px 16px;color:#fff;min-height:250px;box-shadow:0 30px 50px -30px rgba(10,20,40,.9)}}
.cb-task:after{{content:"";position:absolute;inset:-40% -30% auto auto;width:220px;height:220px;background:radial-gradient(circle,rgba(255,255,255,.28),transparent 65%)}}
.cb-task .ic{{width:50px;height:50px;border-radius:15px;display:grid;place-items:center;background:rgba(255,255,255,.18);box-shadow:0 0 0 1px rgba(255,255,255,.35) inset;margin-bottom:12px}}
.cb-task h3{{margin:0 0 6px;font-size:19px;color:#fff!important;font-family:{font}!important}}.cb-task p{{margin:0;font-size:13.5px;line-height:1.65;opacity:.92;color:#fff}}
.cb-li{{display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-bottom:1px dashed #D5DCE1;font-size:14px}}.cb-li em{{font-style:normal;font-size:12px;color:#5A6778}}
.cb-steps{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:6px 0 16px}}.cb-steps div{{background:#fff;border:1px solid #D5DCE1;border-radius:12px;padding:10px 14px;font-size:14px}}
.cb-steps .done{{border-color:#0FA37F;color:#0FA37F;font-weight:700}}.cb-steps .now{{border:2px solid #E0A526;background:#FFF6DD;font-weight:700}}
.cb-sum{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:8px 0 14px}}.cb-sum div{{border-radius:14px;padding:14px 16px}}.cb-sum b{{font-size:28px;display:block}}
.cb-sum .e{{background:#FCE3E1;color:#B3261E}}.cb-sum .w{{background:#FFF0CC;color:#8C5A00}}.cb-sum .o{{background:#D3F5EA;color:#0A7A5E}}
.cb-fix{{display:grid;grid-template-columns:auto 1fr auto;gap:14px;align-items:center;background:#fff;border:1px solid #D5DCE1;border-radius:12px;padding:12px 16px;margin-bottom:8px}}
.cb-fix .tag{{font-size:12px;font-weight:700;border-radius:7px;padding:4px 10px;white-space:nowrap}}.cb-fix .tag.e{{background:#FCE3E1;color:#B3261E}}.cb-fix .tag.w{{background:#FFF0CC;color:#8C5A00}}
.cb-fix b{{display:block}}.cb-fix span.h{{font-size:13.5px;color:#5A6778}}.cb-fix code{{direction:ltr;font-size:12px;color:#34425a;background:#eef2f7;border-radius:6px;padding:3px 7px;white-space:nowrap}}
.cb-pill{{display:inline-block;background:#0FA37F;color:#fff;border-radius:999px;padding:3px 12px;font-weight:700;font-size:12.5px}}.cb-pill.off{{background:#9aa6b6}}
.cb-sidebrand{{display:flex;gap:10px;align-items:center;padding:6px 4px 14px;color:#E9EEF3}}.cb-sidebrand b{{font:600 22px/1 Newsreader,Georgia,serif}}.cb-sidebrand small{{display:block;font-size:11px;opacity:.68;margin-top:3px}}
.cb-sidecap{{font-size:10px;letter-spacing:.16em;font-weight:700;opacity:.55;margin:4px 0 8px}}
[data-testid="stSidebar"]{{background:linear-gradient(180deg,#0B1B3A 0%,#101C2F 100%)}}[data-testid="stSidebar"] *{{color:#E9EEF3}}
[data-testid="stSidebar"] .stButton>button{{justify-content:flex-start;text-align:left;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.10);color:#E9EEF3}}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{{background:linear-gradient(90deg,rgba(224,165,38,.95),rgba(245,192,74,.95));color:#0B1B3A;border:0}}
.cb-workflow{{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:8px 0 22px}}.cb-workflow div{{display:flex;gap:9px;align-items:center;background:#fff;border:1px solid #D5DCE1;border-radius:12px;padding:10px 12px;color:#68768A;font-size:13px;min-height:46px}}.cb-workflow div b{{display:grid;place-items:center;width:24px;height:24px;border-radius:50%;background:#EDF1F6;color:#5A6778;font-size:11px}}.cb-workflow div.done{{border-color:#A9DCCF;color:#0A7A5E}}.cb-workflow div.done b{{background:#0FA37F;color:#fff}}.cb-workflow div.now{{border:2px solid #E0A526;background:#FFF8E7;color:#0B1B3A;font-weight:700}}.cb-workflow div.now b{{background:#E0A526;color:#0B1B3A}}
.cb-sectionhead{{display:flex;align-items:end;justify-content:space-between;gap:12px;margin:2px 0 8px}}.cb-sectionhead h1{{margin:0!important}}.cb-sectionhead .meta{{font-size:12px;color:#5A6778}}
.cb-module-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:10px 0 18px}}.cb-module{{background:#fff;border:1px solid #D5DCE1;border-radius:16px;padding:16px;min-height:120px}}.cb-module b{{font-size:15px;color:#0B1B3A}}.cb-module p{{font-size:13px;color:#5A6778;line-height:1.55;margin:7px 0 0}}
@media(max-width:900px){{.cb-workflow{{grid-template-columns:1fr}}.cb-module-grid{{grid-template-columns:1fr}}}}
.stButton>button{{border-radius:12px;font-weight:600;transition:transform .15s,box-shadow .15s}}
.stButton>button:hover{{transform:translateY(-1px);box-shadow:0 10px 22px -12px rgba(11,27,58,.5)}}
.stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"]{{background:linear-gradient(180deg,#F5C04A,#E0A526);border:0;color:#0B1B3A}}
[data-testid="stDataFrame"],[data-testid="stTable"],code,pre{{direction:ltr}}
</style>"""
    if rtl:
        s += """<style>
[data-testid="stMain"] .block-container{direction:rtl;text-align:right}
[data-testid="stMain"] .block-container [data-testid="stMarkdownContainer"]{text-align:right}
[data-testid="stSidebar"]{direction:rtl}
</style>"""
    return s


def lang() -> str:
    return st.session_state.get("cb_lang", "en")


# ------------------------------------------------------------------ profiles
def gate() -> dict | None:
    """Profile chooser. Returns the active profile, or renders the chooser and returns None."""
    ss = st.session_state
    if ss.get("cb_profile"):
        return ss.cb_profile
    data = profiles.load()
    L = ss.get("cb_lang", "en")
    auto = __import__("os").environ.get("CLOCKBIND_AUTO_PROFILE", "").strip()
    if auto:
        p = next((x for x in data.get("profiles", []) if x.get("name") == auto), None)
        if p:
            ss.cb_profile = p
            ss.cb_lang = p.get("lang", "en")
            profiles.set_last(p["name"])
            return p
    st.markdown(f"<div class='cb-top'><div class='b'>{_logo()}<div><b>ClockBind</b><small>{t('brand_sub', L)}</small></div></div></div>", unsafe_allow_html=True)
    lc = st.columns([3, 1])
    with lc[1]:
        L = st.selectbox(t("language", L), list(LANGS), format_func=LANGS.get, index=list(LANGS).index(L), key="cb_lang_pick")
        ss.cb_lang = L
    st.markdown(f"<div class='cb-card blue'><div class='cb-hello'>{t('who', L)}</div><p class='cb-sub'>{t('who_sub', L)}</p></div>", unsafe_allow_html=True)
    if data["profiles"]:
        cols = st.columns(min(4, len(data["profiles"])) or 1)
        for i, p in enumerate(data["profiles"]):
            if cols[i % len(cols)].button(p["name"], key=f"prof_{i}", type="primary" if p["name"] == data.get("last") else "secondary", use_container_width=True):
                ss.cb_profile = p
                ss.cb_lang = p.get("lang", "en")
                profiles.set_last(p["name"])
                st.rerun()
    with st.form("new_profile"):
        st.markdown(f"**{t('new_profile', L)}**")
        name = st.text_input(t("name", L), key="np_name")
        plang = st.selectbox(t("language", L), list(LANGS), format_func=LANGS.get, index=list(LANGS).index(L), key="np_lang")
        if st.form_submit_button(t("continue", L), type="primary") and name.strip():
            p = profiles.upsert({"name": name.strip(), "lang": plang, "workbook": "", "gates": "", "manifest": ""})
            ss.cb_profile, ss.cb_lang = p, plang
            st.rerun()
    return None


def _logo(size=40):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 128 128"><rect width="128" height="128" rx="30" fill="#1d3150"/>'
            '<path d="M 64 20 A 44 44 0 1 1 25.9 42" fill="none" stroke="#E9EEF3" stroke-width="7" stroke-linecap="round"/>'
            '<line x1="64" y1="64" x2="64" y2="34" stroke="#E9EEF3" stroke-width="6" stroke-linecap="round"/>'
            '<line x1="64" y1="64" x2="38" y2="44" stroke="#F5C04A" stroke-width="6" stroke-linecap="round"/><circle cx="64" cy="64" r="6.5" fill="#F5C04A"/></svg>')


def topbar(profile: dict) -> str:
    """Render the product header and persistent left navigation; return page key.

    The navigation intentionally separates scientific tasks from data-governance tasks:
    Home / Doctoral Programme / Bridge / Statistics / Document Audit / Privacy / Reproducibility / Publication.
    Legacy page keys are mapped so profiles created by 1.2.1 keep working.
    """
    ss, L = st.session_state, lang()
    legacy = {"reports": "reproducibility", "check": "bridge", "clock": "bridge"}
    ss["cb_page"] = legacy.get(ss.get("cb_page", "home"), ss.get("cb_page", "home"))

    # Main-page product bar. Navigation itself lives in the left rail.
    st.markdown(
        f"<div class='cb-top'><div class='b'>{_logo()}<div><b>ClockBind</b>"
        f"<small>{t('brand_sub', L)} · v{__version__}</small></div></div>"
        f"<span class='who'>{profile['name']} · {LANGS[L]}</span></div>",
        unsafe_allow_html=True,
    )

    nav = [
        ("home", "⌂", "nav_home"),
        ("doctoral", "◎", "nav_doctoral"),
        ("bridge", "◈", "nav_bridge"),
        ("stats", "∑", "nav_stats"),
        ("document_audit", "⌕", "nav_document_audit"),
        ("privacy", "◇", "nav_privacy"),
        ("reproducibility", "↻", "nav_reproducibility"),
        ("publication", "▤", "nav_publication"),
    ]
    with st.sidebar:
        st.markdown(
            f"<div class='cb-sidebrand'>{_logo(34)}<div><b>ClockBind</b><small>{t('workspace', L)}</small></div></div>",
            unsafe_allow_html=True,
        )
        st.markdown(f"<div class='cb-sidecap'>{tx('WORKSPACE', L)}</div>", unsafe_allow_html=True)
        for key, icon, label_key in nav:
            if st.button(
                f"{icon}  {t(label_key, L)}",
                key=f"nav_{key}",
                type="primary" if ss.cb_page == key else "secondary",
                use_container_width=True,
            ):
                ss.cb_page = key
                st.rerun()
        st.markdown("---")
        if st.button(f"⚙  {t('nav_settings', L)}", key="nav_settings", type="primary" if ss.cb_page == "settings" else "secondary", use_container_width=True):
            ss.cb_page = "settings"
            st.rerun()
        if st.button(t("switch_user", L), key="nav_switch", use_container_width=True):
            ss.cb_profile = None
            st.rerun()
        st.caption(f"ClockBind {__version__} · local-first")
    return ss.cb_page


def workflow(current: int, labels: tuple[str, ...] = ("Upload", "Configure", "Run", "Review", "Export")) -> None:
    """Five-step analysis workflow used across the Studio.

    `current` is 0-based. It is presentation-only; scientific state is held by the
    underlying engine/session objects, so the UI cannot manufacture a result.
    """
    current = max(0, min(int(current), len(labels) - 1))
    items = []
    for i, label in enumerate(labels):
        cls = "done" if i < current else "now" if i == current else ""
        mark = "✓" if i < current else str(i + 1)
        items.append(f"<div class='{cls}'><b>{mark}</b><span>{tx(label, lang())}</span></div>")
    st.markdown("<div class='cb-workflow'>" + "".join(items) + "</div>", unsafe_allow_html=True)


# ------------------------------------------------------------------ helpers
def _gates(profile) -> str:
    g = (profile.get("gates") or "").strip()
    return g if g and Path(g).expanduser().exists() else str(resource("gates_v3.4_DRAFT.json"))


def _workbook(profile) -> str | None:
    w = (profile.get("workbook") or "").strip()
    return str(Path(w).expanduser()) if w and Path(w).expanduser().exists() else None


def _manifest(profile) -> dict:
    m = (profile.get("manifest") or "").strip()
    if not m:
        return {}
    p = Path(m).expanduser()
    if not p.exists():
        return {}
    try:
        import json
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


@st.cache_data(show_spinner=False)
def _status(path: str, mtime: float, gates: str):
    from clockbind.project import project_status
    return project_status(path, gates)


def _greeting(name: str, L: str) -> str:
    h = _dt.datetime.now().hour
    key = "hello_m" if h < 12 else "hello_a" if h < 18 else "hello_e"
    return t(key, L, n=name)


def _chat_connected() -> bool:
    try:
        import json
        from clockbind.plugins.connect import claude_desktop_config_path
        p = claude_desktop_config_path()
        return p.exists() and "clockbind" in json.loads(p.read_text(encoding="utf-8") or "{}").get("mcpServers", {})
    except Exception:
        return False


def _tmp(up) -> str:
    f = tempfile.NamedTemporaryFile(delete=False, suffix=Path(up.name).suffix)
    f.write(up.getvalue())
    f.close()
    return f.name


# ------------------------------------------------------------------ pages
def page_home(profile):
    ss, L = st.session_state, lang()
    wb = _workbook(profile)
    stt = None
    if wb:
        with st.spinner("…"):
            stt = _status(wb, Path(wb).stat().st_mtime, _gates(profile))
    c1, c2 = st.columns([1.25, 1])
    with c1:
        if stt:
            s = stt["sources"]
            done = s["complete"] + s["held"]
            pct_c = 100 * s["complete"] / max(s["total"], 1)
            pct_h = 100 * done / max(s["total"], 1)
            ring = f"conic-gradient(#0FA37F 0 {pct_c:.1f}%,#F5C04A {pct_c:.1f}% {pct_h:.1f}%,#d6deea {pct_h:.1f}% 100%)"
            steps = "ABCDE"
            road = "".join(f"<span class='{'done' if steps.index(x) < steps.index(stt['step']) else 'now' if x == stt['step'] else ''}'>{x} · {t('r_' + x.lower(), L)}</span>" for x in steps)
            sub = t("home_sub", L, s=stt["step"], left=digits(s["pending"], L))
            ring_html = f"<div class='cb-ring' style='background:{ring}'><div><b>{digits(s['complete'], L)}/{digits(s['total'], L)}</b><small>{t('sources_done', L)}</small></div></div>"
        else:
            road, sub = "", t("home_sub_nofile", L)
            ring_html = "<div class='cb-ring' style='background:#d6deea'><div><b>–</b></div></div>"
        st.markdown(f"<div class='cb-card blue' style='display:grid;grid-template-columns:auto 1fr;gap:22px;align-items:center'>{ring_html}"
                    f"<div><div class='cb-hello'>{_greeting(profile['name'], L)}</div><p class='cb-sub'>{sub}</p><div class='cb-road'>{road}</div></div></div>",
                    unsafe_allow_html=True)
        if not stt and st.button(t("set_workbook", L), type="primary", key="home_set"):
            ss.cb_page = "settings"
            st.rerun()
    with c2:
        lv = (stt or {}).get("levels", {})
        n3, n2, n1 = (digits(lv.get(k, 0), L) for k in ("Level 3", "Level 2", "Level 1"))
        held = digits((stt or {}).get("held", 0), L)
        fail = (stt or {}).get("fail")
        st.markdown(f"<div class='cb-card gold'><b style='font-size:16px'>{t('levels_t', L)}</b>"
                    f"<div class='cb-lg' style='margin-top:10px'><div style='border-color:#F5C04A;background:#FFF6DD'><b style='color:#B8860B'>{n3}</b><span>{t('l3', L)}</span></div>"
                    f"<div style='border-color:#0FA37F;background:#E3F8F1'><b style='color:#0A7A5E'>{n2}</b><span>{t('l2', L)}</span></div>"
                    f"<div style='border-color:#2D6CDF;background:#E6EEFD'><b style='color:#1D4FB0'>{n1}</b><span>{t('l1', L)}</span></div></div>"
                    f"<div class='cb-kpis'><div class='cb-kpi'><b>{held}</b><span>{t('held', L)}</span></div>"
                    f"<div class='cb-kpi'><b style='color:{'#B3261E' if fail else '#0A7A5E'}'>{digits(fail if fail is not None else '–', L)}</b><span>{t('wb_errors', L)}</span></div></div></div>",
                    unsafe_allow_html=True)
    manifest = _manifest(profile)
    if manifest:
        gov = manifest.get("governance", {})
        assets = manifest.get("data_assets", [])
        st.markdown(
            "<div class='cb-card violet'><b style='font-size:16px'>Project governance</b>"
            f"<p class='cb-sub' style='margin-top:8px'><b>{manifest.get('title','Bridge Study')}</b><br>"
            f"{gov.get('design','')} · Protocol {gov.get('protocol_version','')} · "
            f"{'FROZEN' if gov.get('frozen') else 'PRE-FREEZE'}</p>"
            f"<div class='cb-kpis'><div class='cb-kpi'><b>{gov.get('analytic_sources','–')}</b><span>controlled sources</span></div>"
            f"<div class='cb-kpi'><b>{gov.get('historical_candidates','–')}</b><span>historical candidates only</span></div></div>"
            f"<p class='cb-sub' style='margin-top:10px'><b>Current boundary:</b> {gov.get('research_support_boundary','')}</p>"
            f"<p class='cb-sub'><b>Next action:</b> {gov.get('next_action','')}</p></div>",
            unsafe_allow_html=True,
        )
        if assets:
            with st.expander("Project data registry", expanded=False):
                st.dataframe(pd.DataFrame(assets), width="stretch", hide_index=True)
        # Optional privacy-minimised row registries. These are deliberately separate
        # from the workbook and contain only status/coding metadata approved for the
        # local project dashboard; they never replace controlled-source evidence.
        mp = (profile.get("manifest") or "").strip()
        base = Path(mp).expanduser().parent if mp else None
        for key, label in (("source_registry_file", "Controlled-source registry"),
                           ("episode_registry_file", "Episode registry")):
            rel = manifest.get(key)
            rp = (base / rel) if base and rel else None
            if rp and rp.exists():
                try:
                    import json
                    rows = json.loads(rp.read_text(encoding="utf-8"))
                    if isinstance(rows, list):
                        with st.expander(f"{label} · {len(rows)}", expanded=False):
                            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
                except Exception as e:
                    st.warning(f"{label} could not be loaded: {type(e).__name__}")

    tasks = [("check", "k1"), ("clock", "k2"), ("privacy", "k3"), ("report", "k4")]
    cols = st.columns(4)
    for c, (key, tk) in zip(cols, tasks):
        a, b = TASK_COLORS[key]
        c.markdown(f"<div class='cb-task' style='background:linear-gradient(150deg,{a} 0%,{b} 80%)'><div class='ic'><svg width='26' height='26' viewBox='0 0 24 24' fill='none' stroke='#fff' "
                   f"stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>{ICONS[key]}</svg></div><h3>{t(tk, L)}</h3><p>{t(tk + 'd', L)}</p></div>", unsafe_allow_html=True)
        if c.button(f"{t('start', L)}  →" if L not in RTL else f"←  {t('start', L)}", key=f"go_{key}", type="primary", use_container_width=True):
            ss.cb_page = "reports" if key == "report" else key
            st.rerun()
    d1, d2 = st.columns([1.2, 1])
    with d1:
        s = (stt or {}).get("sources", {"pending": 0})
        items = [(t("n1", L), t("done", L) if stt and stt.get("fail") == 0 else ""), (t("n2", L), f"{digits(s.get('pending', 0), L)} {t('left', L)}" if stt else ""),
                 (t("n3", L), ""), (t("n4", L), ""), (t("n5", L), "26.10.2026")]
        st.markdown(f"<div class='cb-card green'><b style='font-size:16px'>{t('next_t', L)}</b>" + "".join(f"<div class='cb-li'><span>{a}</span><em>{b}</em></div>" for a, b in items) + "</div>",
                    unsafe_allow_html=True)
    with d2:
        on = _chat_connected()
        st.markdown(f"<div class='cb-card violet'><b style='font-size:16px'>{t('chat_t', L)}</b><p style='margin:10px 0'><span class='cb-pill {'' if on else 'off'}'>{t('chat_on' if on else 'chat_off', L)}</span></p>"
                    f"<code>/clockbind:validate</code> <code>/clockbind:binding</code><p class='cb-sub' style='margin-top:10px'>{t('chat_note', L)}</p></div>", unsafe_allow_html=True)
    st.caption(f"ClockBind {__version__} · {t('local', L)} · GDPR / KVKK")


def _steps(n, L):
    # Backward-compatible adapter: old three-stage pages now render the common
    # five-stage product workflow. n=0 -> Upload, n>=1 -> Run/Review, n>=2 -> Export.
    mapped = 0 if n <= 0 else 3 if n == 1 else 4
    workflow(mapped)


def page_check(profile):
    from clockbind.workbook_check import check_workbook
    ss, L = st.session_state, lang()
    st.markdown(f"<div class='cb-hello'>{t('k1', L)}</div>", unsafe_allow_html=True)
    res = ss.get("cb_check")
    _steps(2 if res else 0, L)
    wb = _workbook(profile)
    c1, c2 = st.columns([1, 1])
    src = None
    if wb and c1.button(f"{t('use_project', L)}: {Path(wb).name}", type="primary", key="chk_proj", use_container_width=True):
        src = (wb, Path(wb).name)
    up = c2.file_uploader(t("or_upload", L), type=["xlsx"], key="chk_up")
    if up is not None and st.button(t("check_now", L), type="primary", key="chk_up_go"):
        src = (_tmp(up), up.name)
    if src:
        with st.spinner(t("checking", L)):
            try:
                rep = check_workbook(src[0])
                ss.cb_check = {"name": src[1], "df": rep.frame(), "path": src[0]}
            except Exception as e:
                ss.cb_check = {"name": src[1], "error": f"{type(e).__name__}: {e}"}
        st.rerun()
    if not res:
        return
    if "error" in res:
        st.error(res["error"])
        return
    df = res["df"]
    fails, warns = df[df["level"] == "FAIL"], df[df["level"] == "WARN"]
    npass = int((df["level"] == "PASS").sum())
    title = t("n_fix", L, n=digits(len(fails), L)) if len(fails) else t("all_good", L)
    st.markdown(f"<div class='cb-card {'gold' if len(fails) else 'green'}'><div class='cb-hello' style='font-size:24px'>{title}</div><p class='cb-sub'>{res['name']} · {t('locations_only', L)}</p>"
                f"<div class='cb-sum'><div class='e'><b>{digits(len(fails), L)}</b>{t('must_fix', L)}</div><div class='w'><b>{digits(len(warns), L)}</b>{t('should_check', L)}</div>"
                f"<div class='o'><b>{digits(npass, L)}</b>{t('ok', L)}</div></div></div>", unsafe_allow_html=True)
    for _, r in pd.concat([fails, warns]).iterrows():
        head, how = fix_text(str(r["check"]), L)
        where = f"{r['where']} · {r['detail']}" if str(r.get("detail", "")).strip() else str(r["where"])
        tag = ("e", t("must_fix", L)) if r["level"] == "FAIL" else ("w", t("should_check", L))
        st.markdown(f"<div class='cb-fix'><span class='tag {tag[0]}'>{tag[1]}</span><div><b>{head}</b><span class='h'>{how}</span></div><code>{where[:90]}</code></div>", unsafe_allow_html=True)
    from clockbind.pdfreport import build_pdf
    pdf = io.BytesIO()
    build_pdf(pdf, "Workbook integrity check", [("kv", [("FAIL", len(fails)), ("WARN", len(warns)), ("PASS", npass)]),
              ("h", "Problems to fix"), ("table", pd.concat([fails, warns]) if len(fails) + len(warns) else None, "Locations only; cell contents are never shown."),
              ("h", "All checks"), ("table", df)], subtitle=res["name"])
    b1, b2, b3 = st.columns(3)
    b1.download_button(t("pdf", L), pdf.getvalue(), file_name="workbook_check.pdf", mime="application/pdf", key="chk_pdf", type="primary", use_container_width=True)
    if b2.button(t("again", L), key="chk_again", use_container_width=True):
        ss.cb_check = None
        st.rerun()
    if b3.button(t("back_home", L), key="chk_home", use_container_width=True):
        ss.cb_page = "home"
        st.rerun()
    with st.expander(t("all_checks", L)):
        st.dataframe(df, width="stretch", hide_index=True)


def page_clock(profile):
    import contextlib
    from clockbind.binding import evaluate_all
    from clockbind.plugins.binding import cmd_template
    ss, L = st.session_state, lang()
    st.markdown(f"<div class='cb-hello'>{t('k2', L)}</div><p class='cb-sub'>{t('clock_rule', L)}</p>", unsafe_allow_html=True)
    buf = io.BytesIO()

    class _A:
        output = buf
    with contextlib.redirect_stdout(io.StringIO()):
        cmd_template(_A())
    c1, c2 = st.columns([2, 1])
    up = c1.file_uploader(t("tl_file", L), type=["xlsx"], key="tl_up")
    c2.download_button(t("tpl", L), buf.getvalue(), file_name="timeline_template.xlsx", key="tl_tpl", use_container_width=True)
    if up is not None and st.button(t("compute", L), type="primary", key="tl_go"):
        try:
            x = pd.read_excel(up, sheet_name=None, dtype=object)
            low = {k.strip().lower(): v for k, v in x.items()}
            if "episodes" not in low or "steps" not in low:
                raise ValueError("Episodes / Steps sheets missing — download the template")
            ss.cb_clock = {"name": up.name, "res": evaluate_all(low["episodes"], low["steps"])}
        except Exception as e:
            ss.cb_clock = {"error": str(e)}
    r = ss.get("cb_clock")
    if not r:
        return
    if "error" in r:
        st.error(r["error"])
        return
    res = r["res"]
    vc = res["verdict"].value_counts()
    st.markdown("<div class='cb-sum'>" + "".join(f"<div class='{c}'><b>{digits(int(vc.get(k, 0)), L)}</b>{k}</div>" for c, k in
                (("w", "Finance-binding"), ("o", "Non-binding"), ("e", "Indeterminate"))) + "</div>", unsafe_allow_html=True)
    st.dataframe(res, width="stretch", hide_index=True)
    from clockbind.pdfreport import build_pdf
    pdf = io.BytesIO()
    cols = [c for c in ["episode", "verdict", "binding_clocks", "sign_stable", "finance_actionable", "reactive_sensitivity", "reason"] if c in res.columns]
    build_pdf(pdf, "Which clock binds?", [("h", "Verdicts"), ("table", vc.rename_axis("verdict").reset_index(name="episodes")),
              ("h", "Per episode"), ("table", res[cols])], subtitle=r["name"], landscape_pages=True)
    x = io.BytesIO()
    res.to_excel(x, index=False)
    b1, b2 = st.columns(2)
    b1.download_button(t("pdf", L), pdf.getvalue(), file_name="binding_verdicts.pdf", mime="application/pdf", key="tl_pdf", type="primary", use_container_width=True)
    b2.download_button("Excel", x.getvalue(), file_name="binding_verdicts.xlsx", key="tl_xlsx", use_container_width=True)


def page_privacy(profile):
    from clockbind.docaudit import audit, load_names, load_terms
    from clockbind.plugins.privacy import _read
    from clockbind.privacy import scan_dataframe
    ss, L = st.session_state, lang()
    st.markdown(f"<div class='cb-hello'>{t('k3', L)}</div><p class='cb-sub'>{t('k3d', L)}</p>", unsafe_allow_html=True)
    wb = _workbook(profile)
    c1, c2 = st.columns(2)
    srcs = []
    if wb and c1.button(f"{t('use_project', L)}: {Path(wb).name}", type="primary", key="pii_proj", use_container_width=True):
        srcs = [(wb, Path(wb).name)]
    ups = c2.file_uploader(t("pii_file", L), type=["xlsx", "xlsm", "csv", "docx", "pdf", "txt", "md", "zip"], key="pii_up", accept_multiple_files=True)
    terms_on = st.checkbox(t("aud_terms", L), value=True, key="aud_terms_on")
    nm = st.file_uploader(t("aud_names", L), type=["txt"], key="aud_names_up")
    if ups and st.button(t("scan", L), type="primary", key="pii_go"):
        srcs = [(_tmp(u), u.name) for u in ups]
    if srcs:
        from clockbind.resources import resource
        terms = load_terms(str(resource("bridge_terms_2026-09-28.json")) if terms_on else None)
        names = load_names(_tmp(nm)) if nm is not None else []
        cols, files, finds, skipped = [], [], [], []
        for path, label in srcs:
            try:
                if Path(label).suffix.lower() in (".xlsx", ".xlsm", ".csv"):
                    cols += [{"file": label, "sheet": n, **f} for n, d in _read(path).items() for f in scan_dataframe(d)]
                fs, sm, sk = audit(path, terms, names)
                for rows, dst in ((fs, finds), (sm, files), (sk, skipped)):
                    for r in rows:
                        r["file"] = label if r["file"] == Path(path).name else r["file"].replace(Path(path).name, label)
                        dst.append(r)
            except Exception as e:
                skipped.append({"file": label, "reason": f"{type(e).__name__}: {e}"})
        ss.cb_pii = {"cols": cols, "files": files, "finds": finds, "skipped": skipped}
    r = ss.get("cb_pii")
    if not r:
        return
    if "error" in r:
        st.error(r["error"])
        return
    n_pd = sum(1 for f in r.get("files", []) if f["personal-data findings"]) + len({c["file"] for c in r.get("cols", [])})
    n_tw = sum(1 for f in r.get("files", []) if f["outdated-wording findings"])
    if not r.get("cols") and not r.get("finds"):
        st.success(t("pii_none", L))
    elif n_pd:
        st.warning(t("pii_found", L))
    if r.get("files"):
        st.markdown(f"**{t('aud_files', L)}**")
        st.dataframe(pd.DataFrame(r["files"]), width="stretch", hide_index=True)
    if r.get("cols"):
        st.dataframe(pd.DataFrame(r["cols"]), width="stretch", hide_index=True)
    if r.get("finds"):
        st.markdown(f"**{t('aud_find', L)}**")
        st.dataframe(pd.DataFrame(r["finds"]), width="stretch", hide_index=True)
    if r.get("skipped"):
        st.caption(t("aud_skip", L))
        st.dataframe(pd.DataFrame(r["skipped"]), width="stretch", hide_index=True)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf) as w:
        for sheet, key in (("Files", "files"), ("Findings", "finds"), ("Columns", "cols"), ("Not read", "skipped")):
            pd.DataFrame(r.get(key, [])).to_excel(w, sheet_name=sheet, index=False)
    st.download_button(t("aud_dl", L), buf.getvalue(), file_name=f"document_audit_{_dt.date.today()}.xlsx", key="aud_dl_btn")


def page_reports(profile):
    ss, L = st.session_state, lang()
    st.markdown(f"<div class='cb-hello'>{t('rep_t', L)}</div><p class='cb-sub'>{t('rep_desc', L)}</p>", unsafe_allow_html=True)
    wb = _workbook(profile)
    if not wb:
        st.info(t("need_workbook", L))
        return
    if st.button(t("rep_make", L), type="primary", key="rep_go"):
        with st.spinner("…"):
            ss.cb_report = make_status_pdf(wb, _gates(profile), profile["name"])
    if ss.get("cb_report"):
        st.download_button(t("pdf", L), ss.cb_report, file_name=f"Bridge_status_{_dt.date.today()}.pdf", mime="application/pdf", type="primary", key="rep_dl")


def make_status_pdf(workbook: str, gates: str, who: str) -> bytes:
    from clockbind.pdfreport import build_pdf
    from clockbind.project import project_status
    s = project_status(workbook, gates)
    src = s["sources"]
    lv = s["levels"]
    probs = pd.DataFrame(s["problems"]) if s["problems"] else None
    blocks = [("kv", [("Workbook", s["workbook"]), ("Protocol", f"{s['protocol']} ({'frozen' if s['frozen'] else 'draft, not citable'})"),
                      ("Prepared for", who), ("Roadmap step", s["step"])]),
              ("h", "Sources"), ("table", pd.DataFrame([{"total": src["total"], "complete": src["complete"], "held (access)": src["held"], "pending": src["pending"]}])),
              ("h", "Episodes by evidence level"),
              ("table", pd.DataFrame([{"episodes": s["episodes"], "Level 3": lv.get("Level 3", 0), "Level 2": lv.get("Level 2", 0), "Level 1": lv.get("Level 1", 0), "held at S0": s["held"]}])),
              ("h", "Workbook checks"), ("kv", [("Must be fixed", s["fail"]), ("Worth checking", s["warn"])]),
              ("table", probs, "Locations only; cell contents are never shown."),
              ("note", "Counts are computed by the registered rule from the workbook. Results from draft (unfrozen) protocols are not citable.")]
    buf = io.BytesIO()
    build_pdf(buf, "Bridge status report", blocks, subtitle=_dt.date.today().isoformat())
    return buf.getvalue()



def _doctoral_program_config() -> dict:
    """Load private programme metadata when present; otherwise use generic module metadata."""
    import json
    root = Path(__file__).resolve().parents[2]
    p = root / "private_project" / "doctoral_program.json"
    if p.exists():
        try:
            x = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(x, dict):
                return x
        except Exception:
            pass
    return {
        "title": "Doctoral research programme",
        "studies": [
            {"key":"bridge","title":"Supplementary Bridge Study","engine":"Bridge evidence + ClockBind","status":"operational"},
            {"key":"paper1","title":"Paper 1 · Choice-based conjoint / DCE","engine":"AMCE + MNL + mixed logit + HB + scale diagnostics","status":"validation-required"},
            {"key":"paper2","title":"Paper 2 · Financial-flexibility capability","engine":"Reliability + CFA + invariance + HTMT + incremental validity","status":"validation-required"},
            {"key":"paper3","title":"Paper 3 · Partnership architecture","engine":"Overlap weights + binary option exercise (primary) + first differences + dyadic diagnostics; fsQCA and Cox survival only as exploratory tools","status":"validation-required"},
            {"key":"paper4","title":"Paper 4 · Internationalisation governance form","engine":"Case matrix + process tracing + cross-case comparison","status":"operational-support"},
        ],
    }


def page_doctoral(profile):
    ss, L = st.session_state, lang()
    cfg = _doctoral_program_config()
    st.markdown("<div class='cb-sectionhead'><div><div class='cb-eyebrow'>DOCTORAL PROGRAMME</div><h1>Research programme control</h1></div><div class='meta'>Protocol → Data → Analysis → Robustness → Publication</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='cb-card blue'><b style='font-size:18px'>" + str(cfg.get("title","Doctoral research programme")) + "</b><p class='cb-sub'>One research operating system, separate study protocols. No result may cross from one paper into another without an explicit data/protocol mapping.</p></div>", unsafe_allow_html=True)
    studies = cfg.get("studies", [])
    cols = st.columns(2)
    for i, study in enumerate(studies):
        status = study.get("status","configured")
        cls = "green" if status in {"operational","operational-support"} else "gold"
        with cols[i % 2]:
            st.markdown(f"<div class='cb-card {cls}'><span class='cb-eyebrow'>{study.get('key','').upper()}</span><b style='display:block;font-size:17px;margin-top:6px'>{study.get('title','')}</b><p class='cb-sub'>{study.get('engine','')}</p><span class='cb-pill {'ok' if status=='operational' else ''}'>{status}</span></div>", unsafe_allow_html=True)
    st.markdown("### Installed doctoral engines")
    engines = pd.DataFrame([
        ["Paper 1", "DCE / conjoint", "AMCE, outside-option MNL, Swait–Louviere diagnostic, simulated-ML mixed logit, HB MNL"],
        ["Paper 2", "Measurement / longitudinal", "Reliability, HTMT, CR/AVE from CFA loadings, group and longitudinal invariance, ΔR², attrition"],
        ["Paper 3", "Configuration / panel", "Overlap weights, first differences, dyad gaps; exploratory only: fsQCA (calibration, necessity, truth table), Cox survival"],
        ["Paper 4", "Qualitative cases", "Case-code matrix, provenance, conflicting evidence, process-tracing tests, governance-form matrices"],
        ["All papers", "Publication", "Preregistration snapshots, hashes, manuscript-result consistency registry, submission bundles"],
    ], columns=["Study","Engine","Capabilities"])
    st.dataframe(engines, hide_index=True, width="stretch")
    st.warning("Mixed logit, HB and invariance engines are marked validation-required until they match frozen reference cases against established external implementations. ClockBind will not label them confirmatory merely because a model converges.")
    a,b=st.columns(2)
    if a.button("Open Statistics / Methods →", type="primary", use_container_width=True, key="doc_stats"):
        ss.cb_page="stats"; st.rerun()
    if b.button("Open Publication / Preregistration →", use_container_width=True, key="doc_pub"):
        ss.cb_page="publication"; st.rerun()


def page_publication(profile):
    from clockbind.publication import build_prereg_bundle, consistency_audit, build_submission_bundle
    ss, L = st.session_state, lang()
    st.markdown("<div class='cb-sectionhead'><div><div class='cb-eyebrow'>PUBLICATION CONTROL</div><h1>Preregistration & submission</h1></div><div class='meta'>Local snapshots only · no external registration is claimed</div></div>", unsafe_allow_html=True)
    tabs = st.tabs(["Preregistration snapshot", "Manuscript consistency", "Submission bundle"])
    with tabs[0]:
        st.caption("Create a hash-locked local snapshot of protocol, analysis plan and syntax. Row-level datasets are refused.")
        files = st.file_uploader("Protocol / analysis-plan files", type=["json","md","txt","docx","pdf"], accept_multiple_files=True, key="pub_prereg_files")
        status = st.selectbox("Snapshot status", ["DRAFT","FROZEN"], key="pub_status")
        frozen_by = st.text_input("Frozen by (required for FROZEN)", key="pub_by")
        confirm = st.checkbox("I confirm this should be a FROZEN local snapshot", key="pub_confirm") if status=="FROZEN" else False
        if st.button("Build preregistration snapshot", type="primary", key="pub_build", disabled=not files):
            if status=="FROZEN" and (not confirm or not frozen_by.strip()):
                st.error("FROZEN requires explicit confirmation and a 'Frozen by' value.")
            else:
                tmp=[]
                for u in files: tmp.append(_tmp(u))
                out=Path(tempfile.gettempdir())/"ClockBind_preregistration_snapshot.zip"
                try:
                    build_prereg_bundle(None,tmp,out,status,frozen_by.strip(),"Created in ClockBind Studio")
                    ss.pub_prereg_bytes=out.read_bytes(); st.success("Local snapshot created. This does not register the study on OSF or any external registry.")
                except Exception as e: st.error(f"{type(e).__name__}: {e}")
        if ss.get("pub_prereg_bytes"):
            st.download_button("Download preregistration snapshot", ss.pub_prereg_bytes, "ClockBind_preregistration_snapshot.zip", mime="application/zip", use_container_width=True)
    with tabs[1]:
        st.caption("Use an explicit JSON registry of expected/forbidden manuscript values. ClockBind does not guess which result should appear.")
        man=st.file_uploader("Manuscript (.docx/.txt/.md)", type=["docx","txt","md"], key="pub_man")
        reg=st.file_uploader("Result/claim registry (.json)", type=["json"], key="pub_reg")
        if st.button("Audit manuscript consistency", key="pub_audit", disabled=man is None or reg is None):
            try:
                rows,summ=consistency_audit(_tmp(man),_tmp(reg)); ss.pub_audit=(rows,summ)
            except Exception as e: st.error(f"{type(e).__name__}: {e}")
        if ss.get("pub_audit"):
            rows,summ=ss.pub_audit; st.metric("Failed checks",summ["fail"]); st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch")
    with tabs[2]:
        man2=st.file_uploader("Final manuscript", type=["docx","pdf"], key="pub_bundle_man")
        arts=st.file_uploader("Analysis artifacts / supplements", accept_multiple_files=True, key="pub_bundle_art")
        if st.button("Build hashed submission bundle", key="pub_bundle", disabled=man2 is None):
            try:
                mp=_tmp(man2); aa=[_tmp(u) for u in (arts or [])]; out=Path(tempfile.gettempdir())/"ClockBind_submission_bundle.zip"
                build_submission_bundle(mp,aa,out); ss.pub_bundle_bytes=out.read_bytes(); st.success("Submission bundle created with SHA-256 manifest.")
            except Exception as e: st.error(f"{type(e).__name__}: {e}")
        if ss.get("pub_bundle_bytes"):
            st.download_button("Download submission bundle",ss.pub_bundle_bytes,"ClockBind_submission_bundle.zip",mime="application/zip",use_container_width=True)

def page_settings(profile):
    ss, L = st.session_state, lang()
    st.markdown(f"<div class='cb-hello'>{t('nav_settings', L)}</div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(f"**{t('s_profile', L)}**")
        name = st.text_input(t("name", L), value=profile["name"], key="set_name")
        plang = st.selectbox(t("language", L), list(LANGS), format_func=LANGS.get, index=list(LANGS).index(profile.get("lang", "en")), key="set_lang")
        st.caption(t("online_later", L))
    with st.container(border=True):
        st.markdown(f"**{t('s_project', L)}**")
        wbp = st.text_input(t("s_wb_path", L), value=profile.get("workbook", ""), help=t("s_wb_help", L), key="set_wb")
        st.caption(t("s_wb_help", L))
        gp = st.text_input(t("s_gates", L), value=profile.get("gates", ""), key="set_gates")
        mp = st.text_input("Project manifest (optional JSON)", value=profile.get("manifest", ""), key="set_manifest")
    if st.button(t("save", L), type="primary", key="set_save"):
        wbp_c = wbp.strip().strip("'\"")
        if wbp_c and not Path(wbp_c).expanduser().exists():
            st.error(t("not_found", L) + f" ({wbp_c})")
        else:
            old = profile["name"]
            mp_c = mp.strip().strip("'\"")
            if mp_c and not Path(mp_c).expanduser().exists():
                st.error("Project manifest not found" + f" ({mp_c})")
                st.stop()
            p = {**profile, "name": name.strip() or old, "lang": plang, "workbook": wbp_c, "gates": gp.strip().strip("'\""), "manifest": mp_c}
            if p["name"] != old:
                data = profiles.load()
                data["profiles"] = [x for x in data["profiles"] if x.get("name") != old]
                profiles.save(data)
            profiles.upsert(p)
            ss.cb_profile, ss.cb_lang = p, plang
            st.success(t("saved", L))
            st.rerun()
    with st.container(border=True):
        st.markdown(f"**{t('s_chat', L)}**")
        on = _chat_connected()
        st.markdown(f"<span class='cb-pill {'' if on else 'off'}'>{t('chat_on' if on else 'chat_off', L)}</span>", unsafe_allow_html=True)
        if not on and st.button(t("connect", L), key="set_connect"):
            import contextlib
            from clockbind.cli import main as cli
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                cli(["connect", "claude-desktop"])
            st.info(out.getvalue())

# ==================================================================
# Research Studio navigation pages (UI architecture refresh, 28 Sep 2026)
# These later definitions intentionally supersede the earlier privacy page.

def _section_header(title: str, subtitle: str, badge: str | None = None) -> None:
    badge = badge or tx("LOCAL-FIRST", lang())
    st.markdown(
        f"<div class='cb-sectionhead'><div><div class='cb-sidecap' style='color:#5A6778;opacity:1'>{badge}</div>"
        f"<h1>{title}</h1><p class='cb-sub'>{subtitle}</p></div>"
        f"<span class='cb-pill'>{tx('Files stay on this computer', lang())}</span></div>",
        unsafe_allow_html=True,
    )


def page_bridge(profile):
    """Bridge workspace: evidence integrity, binding engine and status reporting."""
    ss, L = st.session_state, lang()
    _section_header(tx("Bridge", lang()), tx("Evidence → rule engine → defensible claim language.", lang()))
    _mods = [("Workbook integrity", "Check formulas, dropdowns, source/episode links, overrides, verdict consistency and privacy flags."),
             ("Which clock binds?", "Apply the counterfactual rule, sign-stability test and finance-only temporal actionability."),
             ("Supervisor status", "Generate a bounded report from the current workbook state; no target episode count is imposed.")]
    st.markdown("<div class='cb-module-grid'>" + "".join(
        f"<div class='cb-module'><b>{tx(h, L)}</b><p>{tx(d, L)}</p></div>" for h, d in _mods) + "</div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs([tx("Workbook integrity", lang()), tx("Binding analysis", lang()), tx("Status report", lang())])
    with tab1:
        page_check(profile, embedded=True)
    with tab2:
        page_clock(profile, embedded=True)
    with tab3:
        page_reports(profile, embedded=True)


def page_document_audit(profile):
    """Document-rule audit: outdated Bridge wording + share-readiness, values never displayed."""
    from clockbind.docaudit import audit, load_names, load_terms
    from clockbind.pdfreport import build_pdf

    ss, L = st.session_state, lang()
    _section_header(tx("Document Audit", lang()), tx("Check documents against the current Bridge language and sharing rules.", lang()))
    r = ss.get("cb_doc_audit")
    workflow(4 if r else 0)
    ups = st.file_uploader(
        tx("Drop Word, PDF, Excel, CSV, text or ZIP files", lang()),
        type=["docx", "docm", "pdf", "xlsx", "xlsm", "csv", "txt", "md", "zip"],
        accept_multiple_files=True,
        key="docaudit_files",
    )
    with st.expander(tx("Configure", lang()), expanded=bool(ups)):
        st.write(tx("Current wording rules: Bridge decisions through 28 September 2026.", lang()))
        nm = st.file_uploader(tx("Optional local customer-name list (.txt, one per line)", lang()), type=["txt"], key="docaudit_names")
        st.caption(tx("The name list is used locally and is not copied into the findings.", lang()))
    if ups and st.button(tx("Run document audit", lang()), type="primary", key="docaudit_run"):
        terms = load_terms(str(resource("bridge_terms_2026-09-28.json")))
        names = load_names(_tmp(nm)) if nm is not None else []
        files, finds, skipped = [], [], []
        with st.spinner(tx("Reading documents locally…", lang())):
            for up in ups:
                path = _tmp(up)
                fs, sm, sk = audit(path, terms, names)
                for rows, dst in ((fs, finds), (sm, files), (sk, skipped)):
                    for row in rows:
                        row = dict(row)
                        if "file" in row:
                            row["file"] = up.name if row["file"] == Path(path).name else row["file"].replace(Path(path).name, up.name)
                        dst.append(row)
        ss.cb_doc_audit = {"files": files, "finds": finds, "skipped": skipped}
        st.rerun()
    if not r:
        st.info(tx("Upload one or more files. The audit reports types and locations; detected personal values are never shown.", lang()))
        return
    fdf, sdf, kdf = pd.DataFrame(r["finds"]), pd.DataFrame(r["files"]), pd.DataFrame(r["skipped"])
    n_words = int(sum(1 for x in r["finds"] if x.get("check") == "outdated wording"))
    n_pd = int(sum(1 for x in r["finds"] if x.get("check") != "outdated wording"))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(tx("Files read", lang()), len(sdf)); c2.metric(tx("Outdated wording", lang()), n_words); c3.metric(tx("Privacy findings", lang()), n_pd); c4.metric(tx("Not read", lang()), len(kdf))
    if len(fdf):
        safe = fdf.drop(columns=[c for c in ["matched"] if c in fdf.columns])
        st.dataframe(safe, width="stretch", hide_index=True)
    else:
        st.success(tx("No findings in readable text. This does not prove that a scanned/image-only document is safe.", lang()))
    if len(kdf):
        with st.expander(tx("Files not read", lang())):
            st.dataframe(kdf, width="stretch", hide_index=True)
    x = io.BytesIO()
    with pd.ExcelWriter(x) as w:
        sdf.to_excel(w, sheet_name="Files", index=False)
        (fdf.drop(columns=[c for c in ["matched"] if c in fdf.columns])).to_excel(w, sheet_name="Findings", index=False)
        kdf.to_excel(w, sheet_name="Not read", index=False)
    pdf = io.BytesIO()
    build_pdf(pdf, "ClockBind document audit", [
        ("kv", [(tx("Files read", lang()), len(sdf)), (tx("Outdated wording", lang()), n_words), (tx("Privacy findings", lang()), n_pd), (tx("Not read", lang()), len(kdf))]),
        ("note", "Personal-data values are never displayed in this report."),
        ("h", tx("Findings", lang())), ("table", fdf.drop(columns=[c for c in ["matched"] if c in fdf.columns]) if len(fdf) else None),
        ("h", tx("Not read", lang())), ("table", kdf if len(kdf) else None),
    ], landscape_pages=True)
    a, b = st.columns(2)
    a.download_button(tx("Export Excel", lang()), x.getvalue(), file_name="ClockBind_document_audit.xlsx", use_container_width=True)
    b.download_button(tx("Export PDF", lang()), pdf.getvalue(), file_name="ClockBind_document_audit.pdf", mime="application/pdf", use_container_width=True)


def page_privacy(profile):
    """Privacy-only scan, separated from methodological wording audit."""
    from clockbind.docaudit import audit, load_names, load_terms

    ss, L = st.session_state, lang()
    _section_header(tx("Privacy", lang()), tx("Identify personal or confidential data before analysis, coding or sharing.", lang()))
    r = ss.get("cb_privacy_only")
    workflow(4 if r else 0)
    ups = st.file_uploader(
        tx("Files to scan", lang()),
        type=["docx", "docm", "pdf", "xlsx", "xlsm", "csv", "txt", "md", "zip"],
        accept_multiple_files=True,
        key="privacy_files",
    )
    names_up = st.file_uploader(tx("Optional local name dictionary (.txt)", lang()), type=["txt"], key="privacy_names")
    if ups and st.button(tx("Run privacy scan", lang()), type="primary", key="privacy_run"):
        names = load_names(_tmp(names_up)) if names_up is not None else []
        privacy_terms = load_terms(str(resource("bridge_terms_2026-09-28.json")))
        privacy_terms["rules"] = []  # retain study-specific allowed amounts, disable wording checks
        files, finds, skipped = [], [], []
        with st.spinner(tx("Scanning locally…", lang())):
            for up in ups:
                path = _tmp(up)
                fs, sm, sk = audit(path, privacy_terms, names)
                for rows, dst in ((fs, finds), (sm, files), (sk, skipped)):
                    for row in rows:
                        row = dict(row)
                        if "file" in row:
                            row["file"] = up.name if row["file"] == Path(path).name else row["file"].replace(Path(path).name, up.name)
                        dst.append(row)
        ss.cb_privacy_only = {"files": files, "finds": finds, "skipped": skipped}
        st.rerun()
    if not r:
        st.info(tx("ClockBind reports the category and location only. It never puts the detected value into the findings table.", lang()))
        return
    fdf, sdf, kdf = pd.DataFrame(r["finds"]), pd.DataFrame(r["files"]), pd.DataFrame(r["skipped"])
    c1, c2, c3 = st.columns(3)
    c1.metric(tx("Files read", lang()), len(sdf)); c2.metric(tx("Findings", lang()), len(fdf)); c3.metric(tx("Not read", lang()), len(kdf))
    if len(fdf):
        safe = fdf.drop(columns=[c for c in ["matched", "current wording / action"] if c in fdf.columns])
        st.warning(tx("Review these locations before sharing the files.", lang()))
        st.dataframe(safe, width="stretch", hide_index=True)
    else:
        st.success(tx("No configured personal-data patterns were found in readable text. This is a screening aid, not proof of anonymity.", lang()))
    x = io.BytesIO()
    with pd.ExcelWriter(x) as w:
        sdf.to_excel(w, sheet_name="Files", index=False)
        (fdf.drop(columns=[c for c in ["matched"] if c in fdf.columns])).to_excel(w, sheet_name="Findings", index=False)
        kdf.to_excel(w, sheet_name="Not read", index=False)
    st.download_button(tx("Export privacy findings", lang()), x.getvalue(), file_name="ClockBind_privacy_scan.xlsx", use_container_width=True)


def page_reproducibility(profile):
    """Reproducibility, hashes, protocol state, run history and AI-safe handoff."""
    from clockbind.core.provenance import code_sha256, package_versions, sha256_file
    from clockbind.safe_export import build_safe_zip, safe_payload

    ss, L = st.session_state, lang()
    _section_header(tx("Reproducibility", lang()), tx("Tie every result to the exact data, protocol, software and code used.", lang()))
    wb, gates = _workbook(profile), _gates(profile)
    tab1, tab2, tab3, tab4 = st.tabs([tx("Project manifest", lang()), tx("AI-safe export", lang()), tx("Run history", lang()), tx("Citation", lang())])
    with tab1:
        versions = package_versions()
        c1, c2, c3 = st.columns(3)
        c1.metric("ClockBind", versions.get("clockbind", __version__))
        c2.metric("Python", versions.get("python", ""))
        c3.metric(tx("Code hash", lang()), code_sha256()[:12])
        if wb:
            p = safe_payload(wb, gates)
            st.json({
                "protocol": p["protocol"],
                "bridge": p["bridge"],
                "workbook_sha256": p["inputs"]["workbook_sha256"],
                "protocol_sha256": p["inputs"]["protocol_sha256"],
                "code_sha256": p["code_sha256"],
            }, expanded=True)
        else:
            st.info(tx("Choose the Bridge workbook in Settings to build a project manifest.", lang()))
    with tab2:
        st.markdown("**Controlled handoff to an AI assistant**")
        st.write(tx("The export contains aggregate project state and hashes only—no workbook cell values, raw document text, personal-data values or local input paths.", lang()))
        if wb:
            raw = build_safe_zip(wb, gates)
            st.download_button(tx("Create AI-safe research export", lang()), raw, file_name="Bridge_AI_Safe_Export.zip", type="primary", use_container_width=True)
        else:
            st.info(tx("Set a Bridge workbook first.", lang()))
    with tab3:
        base = Path.home() / "ClockBind_runs"
        alt = Path.cwd() / "clockbind_runs"
        roots = [x for x in (base, alt) if x.exists()]
        rows = []
        import json as _json
        for root in roots:
            for m in sorted(root.glob("*/manifest.json"), reverse=True)[:100]:
                try:
                    d = _json.loads(m.read_text(encoding="utf-8"))
                    rows.append({"started": d.get("started"), "plugin": d.get("plugin"), "command": d.get("command"), "status": d.get("status"), "warnings": len(d.get("warnings", [])), "code": str(d.get("code_sha256", ""))[:12]})
                except Exception:
                    pass
        if rows:
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        else:
            st.caption(tx("No local run manifests were found yet.", lang()))
    with tab4:
        st.markdown(f"**ClockBind {__version__}**")
        st.code(f"Alavi, S. M. (2026). ClockBind: a reproducible statistics studio for doctoral research (Version {__version__}) [Computer software].")
        st.caption(tx("Use the release/version DOI actually assigned to the version used in the study; do not cite a draft DOI as if released.", lang()))


# Wrap existing pages so Bridge can embed them without duplicate page headings.
_old_page_check = page_check
_old_page_clock = page_clock
_old_page_reports = page_reports


def page_check(profile, embedded: bool = False):
    return _old_page_check(profile)


def page_clock(profile, embedded: bool = False):
    return _old_page_clock(profile)


def page_reports(profile, embedded: bool = False):
    return _old_page_reports(profile)
