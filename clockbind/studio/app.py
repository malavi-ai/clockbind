"""ClockBind Studio — local point-and-click statistics app (run with:  clockbind studio)."""
from __future__ import annotations

import datetime as _dt
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from clockbind import __version__
from clockbind.analysis import REGISTRY, outputs_to_docx, run, syntax_file
from clockbind.analysis.core import data_hash

ASSETS = Path(__file__).resolve().parents[1] / "assets"
ROOT = Path(__file__).resolve().parents[2]
from clockbind.resources import resource

st.set_page_config(page_title="ClockBind Studio", page_icon=str(ASSETS / "clockbind-icon-512.png") if (ASSETS / "clockbind-icon-512.png").exists() else None, layout="wide")

from clockbind.analysis.style import BRAND
_C = {"ink": "#14233A", "accent": "#A4772B", "second": "#2A7A6D", "error": "#B3452A", "muted": "#5C6978", "line": "#D3DADB", "background": "#EEF1F0", **BRAND.get("colors", {})}
_F = {"display": "Newsreader", "body": "IBM Plex Sans", "mono": "IBM Plex Mono", **BRAND.get("fonts", {})}
st.markdown(f"<style>:root{{--cb-ink:{_C['ink']};--cb-accent:{_C['accent']};--cb-second:{_C['second']};--cb-bg:{_C['background']};}}</style>", unsafe_allow_html=True)
from clockbind.fontcss import font_css as _font_css
st.markdown("<style>" + _font_css("inline") + "</style>", unsafe_allow_html=True)  # fonts bundled: no request to Google
st.markdown("""
<style>
html, body, [class*="css"], .stMarkdown, .stText, p, li, label, input, textarea { font-family: "IBM Plex Sans", system-ui, sans-serif; }
h1, h2, h3 { font-family: "Newsreader", Georgia, serif !important; font-weight: 600 !important; letter-spacing: -0.015em; color: var(--cb-ink); }
code, pre, .stCode { font-family: "IBM Plex Mono", ui-monospace, monospace !important; }
[data-testid="stSidebar"] { background: var(--cb-ink); }
[data-testid="stSidebar"] * { color: #E9EEF3 !important; }
[data-testid="stSidebar"] .stButton button, [data-testid="stSidebar"] [data-testid="stFileUploader"] section, [data-testid="stSidebar"] [data-testid="stFileUploader"] button { background: #1D3150 !important; border-color: #34507A !important; }
.cb-card { background: #fff; border: 1px solid #D3DADB; border-radius: 14px; padding: 16px 20px; margin-bottom: 14px; }
.cb-eyebrow { font: 600 11px/1 "IBM Plex Sans", sans-serif; letter-spacing: .12em; text-transform: uppercase; color: #5C6978; }
.cb-pill { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; background: #F3E7D0; color: var(--cb-accent); }
.cb-pill.ok { background: #DCEEEA; color: #2A7A6D; }
.cb-pill.warn { background: #F7E1DA; color: #B3452A; }
div[data-testid="stMetricValue"] { font-family: "Newsreader", Georgia, serif; font-weight: 600; }
.block-container { padding-top: 2.2rem; max-width: 1240px; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #14233A 0%, #101C2F 100%); }
.stButton > button, .stDownloadButton > button { border-radius: 10px; font-weight: 500; transition: transform .15s, box-shadow .15s; }
.stButton > button:hover, .stDownloadButton > button:hover { transform: translateY(-1px); box-shadow: 0 10px 22px -12px rgba(20,35,58,.45); }
.stButton > button[kind="primary"] { background: linear-gradient(180deg, #C99A45, #A4772B); border: 0; color: #14233A; font-weight: 600; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 16px !important; box-shadow: 0 1px 1px rgba(20,35,58,.04), 0 18px 40px -22px rgba(20,35,58,.22); background: #fff; }
.cb-hero { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; flex-wrap: wrap; margin-bottom: 8px; }
.cb-hero h1 { margin: 4px 0 0 !important; }
.cb-stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 10px 0 18px; }
@media (max-width: 900px) { .cb-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.cb-stat { position: relative; background: #fff; border: 1px solid #D5DCE1; border-radius: 12px; padding: 12px 14px 12px 18px; overflow: hidden; }
.cb-stat::before { content: ""; position: absolute; inset: 0 auto 0 0; width: 4px; background: #8A96A3; }
.cb-stat.ok::before { background: #2A7A6D; } .cb-stat.warn::before { background: #8C6410; } .cb-stat.bad::before { background: #B3452A; } .cb-stat.gold::before { background: linear-gradient(#C99A45, #A4772B); }
.cb-stat .k { font: 500 11px/1.2 "IBM Plex Sans", sans-serif; letter-spacing: .12em; text-transform: uppercase; color: #5A6778; }
.cb-stat .v { font: 600 22px/1.2 "Newsreader", Georgia, serif; color: #14233A; }
.cb-note { font-size: 13px; color: #5A6778; }
</style>""", unsafe_allow_html=True)

# ----------------------------------------------------------------- shell: profile, language, home and research tasks
from clockbind.studio import shell as _shell
from clockbind.fontcss import persian_font_css as _fa_css
st.markdown("<style>" + _fa_css() + "</style>", unsafe_allow_html=True)
st.markdown(_shell.css(_shell.lang()), unsafe_allow_html=True)
_profile = _shell.gate()
if _profile is None:
    st.stop()
st.markdown(_shell.css(_shell.lang()), unsafe_allow_html=True)  # language may have changed with the profile
_pg = _shell.topbar(_profile)
_PAGES = {
    "home": _shell.page_home,
    "doctoral": _shell.page_doctoral,
    "bridge": _shell.page_bridge,
    "document_audit": _shell.page_document_audit,
    "privacy": _shell.page_privacy,
    "reproducibility": _shell.page_reproducibility,
    "publication": _shell.page_publication,
    "settings": _shell.page_settings,
}
if _pg in _PAGES:
    _PAGES[_pg](_profile)
    st.stop()

ss = st.session_state
ss.setdefault("outputs", [])
ss.setdefault("df", None)
ss.setdefault("data_name", None)
ss.setdefault("labels", {})
ss.setdefault("pii", [])


# ----------------------------------------------------------------- data loading
def load_file(up) -> tuple[pd.DataFrame, dict]:
    name = up.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(up), {}
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(up), {}
    if name.endswith(".sav"):
        import pyreadstat
        tmp = Path("/tmp") / f"cb_{_dt.datetime.now():%H%M%S}.sav"
        tmp.write_bytes(up.getvalue())
        df, meta = pyreadstat.read_sav(str(tmp))
        return df, {"variable_labels": dict(zip(meta.column_names, meta.column_labels)), "value_labels": meta.variable_value_labels}
    raise ValueError("Use .xlsx, .csv or .sav")


with st.sidebar:
    st.markdown("---")
    st.markdown("<div class='cb-sidecap'>STATISTICS WORKFLOW</div>", unsafe_allow_html=True)
    ss.setdefault("stat_step", "Upload")
    _stat_steps = ["Upload", "Configure", "Run", "Review", "Export"]
    for _i, _step in enumerate(_stat_steps, 1):
        if st.button(f"{_i}. {_step}", key=f"stat_nav_{_step.lower()}", type="primary" if ss.stat_step == _step else "secondary", use_container_width=True):
            ss.stat_step = _step
            st.rerun()
    st.markdown("---")
    if ss.df is not None:
        st.caption(f"**{ss.data_name}**  \n{len(ss.df):,} rows · {ss.df.shape[1]} variables  \nsha256 {data_hash(ss.df)[:12]}")
    else:
        st.caption("No statistics dataset loaded.")
    st.caption(f"Results in this session: {len(ss.outputs)}")
    st.caption("Data stay on this computer. Use pseudonymised codes.")


# ----------------------------------------------------------------- rendering
def show_output(o, idx=None):
    with st.container(border=True):
        top = st.columns([6, 1])
        top[0].markdown(f"### {o.title}")
        top[0].markdown(f"<span class='cb-eyebrow'>{o.created.replace('T', ' ')} · data sha256 {o.data_sha256[:12]}{' · n = ' + str(o.n_used) if o.n_used is not None else ''}</span>", unsafe_allow_html=True)
        if idx is not None and top[1].button("Remove", key=f"rm{idx}"):
            ss.outputs.pop(idx); st.rerun()
        for b in o.blocks:
            if b.kind == "table":
                if b.title:
                    st.markdown(f"**{b.title}**")
                df = b.content
                num = [c for c in df.select_dtypes("float").columns if not (df[c].dropna() % 1 == 0).all()]
                ints = [c for c in df.select_dtypes("number").columns if c not in num]
                fmt = {**{c: "{:.3f}" for c in num}, **{c: "{:,.0f}" for c in ints}}
                st.dataframe(df.style.format(fmt, na_rep=""), width="stretch", hide_index=isinstance(df.index, pd.RangeIndex))
                if b.note:
                    st.caption(b.note)
            elif b.kind == "figure":
                if b.title:
                    st.markdown(f"**{b.title}**")
                st.image(b.content, width=720)
            elif b.kind == "methods":
                st.info("Methods text · " + str(b.content))
            elif b.kind == "warning":
                st.warning(str(b.content))
            elif b.kind == "note":
                st.caption(str(b.content))
            else:
                st.markdown(str(b.content))
        with st.expander("Syntax and references"):
            st.code(json.dumps(o.syntax, indent=2, ensure_ascii=False), language="json")
            for r in o.references:
                st.caption(r)


def is_numeric(s: pd.Series) -> bool:
    return pd.to_numeric(s, errors="coerce").notna().mean() > 0.9 if len(s.dropna()) else False


# ----------------------------------------------------------------- Statistics: five-stage workflow
_shell._section_header("Statistics", "Point-and-click analysis with an explicit plan → run → review → export separation.")
_stat_steps = ["Upload", "Configure", "Run", "Review", "Export"]
try:
    _current = _stat_steps.index(ss.stat_step)
except ValueError:
    ss.stat_step, _current = "Upload", 0
_shell.workflow(_current)


def _goto(step: str):
    ss.stat_step = step
    st.rerun()


if ss.stat_step == "Upload":
    st.markdown("### Upload data")
    st.caption("Excel, CSV and SPSS (.sav) are supported. The file is read locally in this Studio session.")
    up = st.file_uploader("Research dataset", type=["xlsx", "xls", "csv", "sav"], key="stats_upload_main")
    c1, c2 = st.columns([1, 1])
    if up is not None and up.name != ss.data_name:
        try:
            ss.df, meta = load_file(up)
            ss.data_name, ss.labels = up.name, meta
            from clockbind.privacy import scan_dataframe
            ss.pii = scan_dataframe(ss.df)
        except Exception as e:
            st.error(f"Could not read the file: {e}")
    if c1.button("Load synthetic example", key="stats_example", use_container_width=True):
        ss.df = pd.read_csv(resource("validation_data.csv"))
        ss.data_name = "validation_data.csv (synthetic example)"
        ss.labels, ss.pii = {}, []
        st.rerun()
    if c2.button("Continue to Configure →", key="stats_upload_next", type="primary", use_container_width=True, disabled=ss.df is None):
        _goto("Configure")
    if ss.df is not None:
        df = ss.df
        if ss.get("pii"):
            st.warning("Possible personal-data patterns were found. Review them in Privacy before sharing this dataset.")
            st.dataframe(pd.DataFrame(ss.pii).rename(columns={"column": "Column", "kind": "Looks like", "count": "Cells"}), hide_index=True, width="stretch")
        m = st.columns(4)
        m[0].metric("Rows", f"{len(df):,}")
        m[1].metric("Variables", df.shape[1])
        m[2].metric("Missing cells", f"{int(df.isna().sum().sum()):,}")
        m[3].metric("Complete rows", f"{int(df.dropna().shape[0]):,}")
        with st.expander("Preview and variable structure", expanded=False):
            t1, t2 = st.tabs(["Data preview", "Variables"])
            with t1:
                st.dataframe(df.head(200), width="stretch", height=390)
            with t2:
                vl = ss.labels.get("variable_labels", {})
                info = pd.DataFrame({
                    "Variable": df.columns,
                    "Label": [vl.get(c, "") or "" for c in df.columns],
                    "Type": ["numeric" if is_numeric(df[c]) else "categorical" for c in df.columns],
                    "Valid": [int(df[c].notna().sum()) for c in df.columns],
                    "Missing": [int(df[c].isna().sum()) for c in df.columns],
                    "Distinct": [int(df[c].nunique()) for c in df.columns],
                })
                st.dataframe(info, width="stretch", hide_index=True, height=390)

elif ss.stat_step == "Configure":
    st.markdown("### Configure analysis")
    if ss.df is None:
        st.warning("Upload a dataset first.")
        if st.button("← Go to Upload", key="cfg_back"):
            _goto("Upload")
    else:
        groups = {}
        for k, v in REGISTRY.items():
            groups.setdefault(v["group"], []).append(k)
        order = ["Data", "Descriptive statistics", "Compare means", "Non-parametric tests", "Correlate", "Regression", "Scale", "Dimension reduction", "Planning", "Paper 1 · DCE", "Paper 2 · Measurement", "Paper 3 · QCA & Panel", "Paper 4 · Qualitative", "Doctoral modules"]
        gnames = [g for g in order if g in groups] + [g for g in groups if g not in order]
        c = st.columns([1, 1.4])
        grp = c[0].selectbox("Analysis family", gnames, key="stats_group")
        name = c[1].selectbox("Analysis", groups[grp], format_func=lambda k: REGISTRY[k]["title"], key="stats_analysis")
        spec = REGISTRY[name]
        df = ss.df
        cols = list(df.columns)
        numcols = [x for x in cols if is_numeric(df[x])]
        with st.form(f"configure_{name}"):
            params = {}
            for p in spec["params"]:
                typ, lab, key = p["type"], p["label"], f"cfg_{name}_{p['name']}"
                pool = numcols if p.get("numeric") else cols
                if typ == "columns":
                    v = st.multiselect(lab, pool, key=key)
                    params[p["name"]] = ",".join(v) if v else None
                elif typ == "column":
                    opts = ([""] if p.get("optional") else []) + pool
                    v = st.selectbox(lab, opts, key=key)
                    params[p["name"]] = v or None
                elif typ == "bool":
                    params[p["name"]] = st.checkbox(lab, value=p.get("default", False), key=key)
                elif typ == "choice":
                    choices = p["choices"]
                    params[p["name"]] = st.selectbox(lab, choices, index=choices.index(p.get("default", choices[0])), key=key)
                elif typ == "int":
                    params[p["name"]] = int(st.number_input(lab, value=int(p.get("default", 0)), step=1, key=key))
                elif typ == "number":
                    params[p["name"]] = float(st.number_input(lab, value=float(p.get("default", 0.0)), key=key, format="%.4f"))
                elif typ == "textarea":
                    params[p["name"]] = st.text_area(lab, key=key) or None
                else:
                    params[p["name"]] = st.text_input(lab, key=key) or None
            save_plan = st.form_submit_button("Save analysis plan →", type="primary")
        with st.expander("Method note"):
            st.write(spec["doc"] or spec["title"])
        if save_plan:
            ss.stat_plan = {"analysis": name, "title": spec["title"], "params": {k: v for k, v in params.items() if v is not None}}
            _goto("Run")

elif ss.stat_step == "Run":
    st.markdown("### Run")
    plan = ss.get("stat_plan")
    if ss.df is None or not plan:
        st.warning("A dataset and saved analysis plan are required.")
        if st.button("← Configure analysis", key="run_back"):
            _goto("Configure")
    else:
        st.markdown("<div class='cb-card'><span class='cb-eyebrow'>Frozen for this run</span>", unsafe_allow_html=True)
        st.markdown(f"**{plan['title']}**")
        st.code(json.dumps(plan["params"], indent=2, ensure_ascii=False), language="json")
        st.caption(f"Dataset sha256: {data_hash(ss.df)}")
        st.markdown("</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1])
        if c1.button("← Change configuration", key="run_change", use_container_width=True):
            _goto("Configure")
        if c2.button("Run analysis", type="primary", key="run_now", use_container_width=True):
            try:
                with st.spinner("Running analysis…"):
                    o = run(plan["analysis"], ss.df, plan["params"])
                ss.outputs.append(o)
                ss.stat_last_idx = len(ss.outputs) - 1
                _goto("Review")
            except Exception as e:
                st.error(f"{type(e).__name__}: {e}")

elif ss.stat_step == "Review":
    st.markdown("### Review")
    if not ss.outputs:
        st.info("No statistical results yet.")
        if st.button("← Configure an analysis", key="review_back"):
            _goto("Configure")
    else:
        idx = min(int(ss.get("stat_last_idx", len(ss.outputs) - 1)), len(ss.outputs) - 1)
        st.caption("Scientific review comes before export. Inspect diagnostics, warnings, assumptions and syntax here.")
        show_output(ss.outputs[idx])
        with st.expander("Other results in this session"):
            for i, o in enumerate(ss.outputs):
                st.write(f"{i + 1}. {o.title} · {o.created}")
        c1, c2 = st.columns(2)
        if c1.button("Configure another analysis", key="review_more", use_container_width=True):
            _goto("Configure")
        if c2.button("Continue to Export →", key="review_export", type="primary", use_container_width=True):
            _goto("Export")

elif ss.stat_step == "Export":
    st.markdown("### Export")
    if not ss.outputs:
        st.info("No results to export.")
    else:
        tmp = Path("/tmp") / "clockbind_output.docx"
        outputs_to_docx(ss.outputs, tmp, title=f"ClockBind output — {ss.data_name or ''}")
        from clockbind.pdfreport import outputs_to_pdf
        pdf = io.BytesIO()
        outputs_to_pdf(ss.outputs, pdf, title=f"ClockBind output: {ss.data_name or ''}")
        c1, c2, c3 = st.columns(3)
        c1.download_button("Word report", tmp.read_bytes(), file_name=f"ClockBind_output_{_dt.date.today()}.docx", use_container_width=True)
        c2.download_button("PDF report", pdf.getvalue(), file_name=f"ClockBind_output_{_dt.date.today()}.pdf", mime="application/pdf", use_container_width=True)
        c3.download_button("Analysis syntax", syntax_file(ss.outputs), file_name=f"ClockBind_syntax_{_dt.date.today()}.json", use_container_width=True)
        st.markdown("<div class='cb-card'><b>Reproducibility note</b><p class='cb-sub'>Each result carries the dataset hash and exact syntax. Use the Reproducibility module for project hashes, run manifests and the AI-safe Bridge export.</p></div>", unsafe_allow_html=True)
        a, b = st.columns(2)
        if a.button("Run another analysis", key="export_more", use_container_width=True):
            _goto("Configure")
        if b.button("Clear session results", key="export_clear", use_container_width=True):
            ss.outputs = []
            ss.stat_plan = None
            ss.stat_last_idx = None
            _goto("Upload")

