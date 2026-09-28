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
from clockbind.studio.i18n import LANGS, RTL, digits, fix_text, t

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
            p = profiles.upsert({"name": name.strip(), "lang": plang, "workbook": "", "gates": ""})
            ss.cb_profile, ss.cb_lang = p, plang
            st.rerun()
    return None


def _logo(size=40):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 128 128"><rect width="128" height="128" rx="30" fill="#1d3150"/>'
            '<path d="M 64 20 A 44 44 0 1 1 25.9 42" fill="none" stroke="#E9EEF3" stroke-width="7" stroke-linecap="round"/>'
            '<line x1="64" y1="64" x2="64" y2="34" stroke="#E9EEF3" stroke-width="6" stroke-linecap="round"/>'
            '<line x1="64" y1="64" x2="38" y2="44" stroke="#F5C04A" stroke-width="6" stroke-linecap="round"/><circle cx="64" cy="64" r="6.5" fill="#F5C04A"/></svg>')


def topbar(profile: dict) -> str:
    """Header and navigation; returns the selected page key."""
    ss, L = st.session_state, lang()
    st.markdown(f"<div class='cb-top'><div class='b'>{_logo()}<div><b>ClockBind</b><small>{t('brand_sub', L)}</small></div></div>"
                f"<span class='who'>{profile['name']} · {LANGS[L]}</span></div>", unsafe_allow_html=True)
    ss.setdefault("cb_page", "home")
    keys = ["home", "bridge", "reports", "stats", "settings"]
    cols = st.columns(len(keys) + 1)
    for c, k in zip(cols, keys):
        if c.button(t(f"nav_{k}", L), key=f"nav_{k}", type="primary" if ss.cb_page == k or (k == "bridge" and ss.cb_page in ("check", "clock", "privacy")) else "secondary", use_container_width=True):
            ss.cb_page = "check" if k == "bridge" else k
            st.rerun()
    if cols[-1].button(t("switch_user", L), key="nav_switch", use_container_width=True):
        ss.cb_profile = None
        st.rerun()
    return ss.cb_page


# ------------------------------------------------------------------ helpers
def _gates(profile) -> str:
    g = (profile.get("gates") or "").strip()
    return g if g and Path(g).expanduser().exists() else str(resource("gates_v3.3_DRAFT.json"))


def _workbook(profile) -> str | None:
    w = (profile.get("workbook") or "").strip()
    return str(Path(w).expanduser()) if w and Path(w).expanduser().exists() else None


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
    labels = [t("step1", L), t("step2", L), t("step3", L)]
    st.markdown("<div class='cb-steps'>" + "".join(f"<div class='{'done' if i < n else 'now' if i == n else ''}'>{'✓ ' if i < n else ''}{x}</div>" for i, x in enumerate(labels)) + "</div>",
                unsafe_allow_html=True)


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
    from clockbind.plugins.privacy import _read
    from clockbind.privacy import scan_dataframe
    ss, L = st.session_state, lang()
    st.markdown(f"<div class='cb-hello'>{t('k3', L)}</div><p class='cb-sub'>{t('k3d', L)}</p>", unsafe_allow_html=True)
    wb = _workbook(profile)
    c1, c2 = st.columns(2)
    src = None
    if wb and c1.button(f"{t('use_project', L)}: {Path(wb).name}", type="primary", key="pii_proj", use_container_width=True):
        src = (wb, Path(wb).name)
    up = c2.file_uploader(t("pii_file", L), type=["xlsx", "csv"], key="pii_up")
    if up is not None and st.button(t("scan", L), type="primary", key="pii_go"):
        src = (_tmp(up), up.name)
    if src:
        try:
            found = [{"sheet": n, **f} for n, d in _read(src[0]).items() for f in scan_dataframe(d)]
            ss.cb_pii = {"name": src[1], "found": found}
        except Exception as e:
            ss.cb_pii = {"error": f"{type(e).__name__}: {e}"}
    r = ss.get("cb_pii")
    if not r:
        return
    if "error" in r:
        st.error(r["error"])
    elif r["found"]:
        st.warning(t("pii_found", L))
        st.dataframe(pd.DataFrame(r["found"]), width="stretch", hide_index=True)
    else:
        st.success(t("pii_none", L))


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
    if st.button(t("save", L), type="primary", key="set_save"):
        wbp_c = wbp.strip().strip("'\"")
        if wbp_c and not Path(wbp_c).expanduser().exists():
            st.error(t("not_found", L) + f" ({wbp_c})")
        else:
            old = profile["name"]
            p = {**profile, "name": name.strip() or old, "lang": plang, "workbook": wbp_c, "gates": gp.strip().strip("'\"")}
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
