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

st.set_page_config(page_title="ClockBind Studio", page_icon=str(ASSETS / "clockbind-icon-512.png") if (ASSETS / "clockbind-icon-512.png").exists() else None, layout="wide")

from clockbind.analysis.style import BRAND
_C = {"ink": "#14233A", "accent": "#A4772B", "second": "#2A7A6D", "error": "#B3452A", "muted": "#5C6978", "line": "#D3DADB", "background": "#EEF1F0", **BRAND.get("colors", {})}
_F = {"display": "Newsreader", "body": "IBM Plex Sans", "mono": "IBM Plex Mono", **BRAND.get("fonts", {})}
st.markdown(f"<style>:root{{--cb-ink:{_C['ink']};--cb-accent:{_C['accent']};--cb-second:{_C['second']};--cb-bg:{_C['background']};}}</style>", unsafe_allow_html=True)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono&display=swap');
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
</style>""", unsafe_allow_html=True)

ss = st.session_state
ss.setdefault("outputs", [])
ss.setdefault("df", None)
ss.setdefault("data_name", None)
ss.setdefault("labels", {})


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
    icon = ASSETS / "clockbind-icon.svg"
    c1, c2 = st.columns([1, 3])
    if icon.exists():
        c1.image(str(icon), width=52)
    c2.markdown(f"<div style='font:600 27px/1.1 Newsreader,Georgia,serif;letter-spacing:-.02em;padding-top:6px'>ClockBind</div><div style='font-size:12px;opacity:.75'>Studio {__version__}</div>", unsafe_allow_html=True)
    st.markdown("---")
    up = st.file_uploader("Open data (.xlsx, .csv, .sav)", type=["xlsx", "xls", "csv", "sav"])
    if up is not None and up.name != ss.data_name:
        try:
            ss.df, meta = load_file(up); ss.data_name = up.name; ss.labels = meta
        except Exception as e:
            st.error(f"Could not read the file: {e}")
    if st.button("Load example data (synthetic)"):
        ss.df = pd.read_csv(ROOT / "validation" / "validation_data.csv") if (ROOT / "validation" / "validation_data.csv").exists() else None
        ss.data_name = "validation_data.csv (synthetic example)"; ss.labels = {}
    if st.button("Run demo analyses"):
        ss.df = pd.read_csv(ROOT / "validation" / "validation_data.csv"); ss.data_name = "validation_data.csv (synthetic example)"; ss.labels = {}
        for n_, p_ in [("descriptives", {"variables": "y,x1", "by": "g2"}), ("t_independent", {"variables": "y", "group": "g2"}),
                       ("regression_linear", {"y": "y", "x": "x1,x2,x3", "categorical": "g2", "se": "CR2", "cluster": "firm"}), ("reliability", {"items": "q1,q2,q3"})]:
            ss.outputs.append(run(n_, ss.df, p_))
        ss.nav = "Output"
    page = st.radio("Go to", ["Data", "Analyze", "Output", "Cite & validation"], label_visibility="collapsed", key="nav")
    st.markdown("---")
    if ss.df is not None:
        st.caption(f"**{ss.data_name}**  \n{len(ss.df):,} rows · {ss.df.shape[1]} variables  \nsha256 {data_hash(ss.df)[:12]}")
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


# ----------------------------------------------------------------- pages
if page == "Data":
    st.markdown("<span class='cb-eyebrow'>Data</span>", unsafe_allow_html=True)
    st.title("Data view")
    if ss.df is None:
        st.markdown("<div class='cb-card'>Open a data file from the sidebar, or load the synthetic example. Excel, CSV and SPSS (.sav) files are supported. Nothing leaves this computer.</div>", unsafe_allow_html=True)
    else:
        df = ss.df
        m = st.columns(4)
        m[0].metric("Rows", f"{len(df):,}"); m[1].metric("Variables", df.shape[1]); m[2].metric("Missing cells", f"{int(df.isna().sum().sum()):,}"); m[3].metric("Complete rows", f"{int(df.dropna().shape[0]):,}")
        t1, t2 = st.tabs(["Data", "Variables"])
        with t1:
            st.dataframe(df, width="stretch", height=460)
        with t2:
            vl = ss.labels.get("variable_labels", {})
            info = pd.DataFrame({"Variable": df.columns, "Label": [vl.get(c, "") or "" for c in df.columns],
                                 "Type": ["numeric" if is_numeric(df[c]) else "categorical" for c in df.columns],
                                 "Valid": [int(df[c].notna().sum()) for c in df.columns], "Missing": [int(df[c].isna().sum()) for c in df.columns],
                                 "Distinct": [int(df[c].nunique()) for c in df.columns], "Example": [str(df[c].dropna().iloc[0]) if df[c].notna().any() else "" for c in df.columns]})
            st.dataframe(info, width="stretch", hide_index=True, height=460)

elif page == "Analyze":
    st.markdown("<span class='cb-eyebrow'>Analyze</span>", unsafe_allow_html=True)
    st.title("Run an analysis")
    groups = {}
    for k, v in REGISTRY.items():
        groups.setdefault(v["group"], []).append(k)
    order = ["Data", "Descriptive statistics", "Compare means", "Non-parametric tests", "Correlate", "Regression", "Scale", "Dimension reduction", "Planning", "Doctoral modules"]
    gnames = [g for g in order if g in groups] + [g for g in groups if g not in order]
    c = st.columns([1, 1.4])
    grp = c[0].selectbox("Menu", gnames)
    name = c[1].selectbox("Analysis", groups[grp], format_func=lambda k: REGISTRY[k]["title"])
    spec = REGISTRY[name]
    needs_data = name != "power"
    if needs_data and ss.df is None:
        st.warning("Open a data file first (sidebar).")
    else:
        df = ss.df if ss.df is not None else pd.DataFrame()
        cols = list(df.columns)
        numcols = [x for x in cols if is_numeric(df[x])]
        with st.form(f"form_{name}"):
            params = {}
            for p in spec["params"]:
                t, lab, key = p["type"], p["label"], f"{name}_{p['name']}"
                pool = numcols if p.get("numeric") else cols
                if t == "columns":
                    v = st.multiselect(lab, pool, key=key)
                    params[p["name"]] = ",".join(v) if v else None
                elif t == "column":
                    opts = ([""] if p.get("optional") else []) + pool
                    v = st.selectbox(lab, opts, key=key)
                    params[p["name"]] = v or None
                elif t == "bool":
                    params[p["name"]] = st.checkbox(lab, value=p.get("default", False), key=key)
                elif t == "choice":
                    params[p["name"]] = st.selectbox(lab, p["choices"], index=p["choices"].index(p.get("default", p["choices"][0])), key=key)
                elif t == "int":
                    params[p["name"]] = int(st.number_input(lab, value=int(p.get("default", 0)), step=1, key=key))
                elif t == "number":
                    params[p["name"]] = float(st.number_input(lab, value=float(p.get("default", 0.0)), key=key, format="%.4f"))
                elif t == "textarea":
                    params[p["name"]] = st.text_area(lab, key=key) or None
                else:
                    params[p["name"]] = st.text_input(lab, key=key) or None
            go = st.form_submit_button("Run", type="primary")
        with st.expander("About this analysis"):
            st.write(spec["doc"] or spec["title"])
        if go:
            params = {k: v for k, v in params.items() if v is not None}
            try:
                with st.spinner("Running…"):
                    o = run(name, df, params)
                ss.outputs.append(o)
                st.success("Done. The result is also saved in Output.")
                show_output(o)
            except Exception as e:
                st.error(f"{type(e).__name__}: {e}")

elif page == "Output":
    st.markdown("<span class='cb-eyebrow'>Output</span>", unsafe_allow_html=True)
    st.title("Output viewer")
    if not ss.outputs:
        st.markdown("<div class='cb-card'>Results appear here as you run analyses. Export them as a Word document, or save the syntax file to re-run everything later with <code>clockbind syntax run</code>.</div>", unsafe_allow_html=True)
    else:
        b = st.columns([1, 1, 1, 3])
        buf = io.BytesIO()
        tmp = Path("/tmp") / "clockbind_output.docx"
        outputs_to_docx(ss.outputs, tmp, title=f"ClockBind output — {ss.data_name or ''}")
        b[0].download_button("Word (.docx)", tmp.read_bytes(), file_name=f"ClockBind_output_{_dt.date.today()}.docx")
        b[1].download_button("Syntax (.json)", syntax_file(ss.outputs), file_name=f"ClockBind_syntax_{_dt.date.today()}.json")
        if b[2].button("Clear all"):
            ss.outputs = []; st.rerun()
        for i, o in list(enumerate(ss.outputs))[::-1]:
            show_output(o, i)

else:
    st.markdown("<span class='cb-eyebrow'>Cite &amp; validation</span>", unsafe_allow_html=True)
    st.title("How to cite ClockBind")
    st.markdown(f"<div class='cb-card'>Alavi, S. M. (2026). <i>ClockBind: a reproducible statistics studio for doctoral research</i> (Version {__version__}) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.<b>XXXXXXX</b><br><span class='cb-eyebrow'>Add the DOI after the first Zenodo release. Also cite the libraries listed under each result.</span></div>", unsafe_allow_html=True)
    v = ROOT / "VALIDATION.md"
    if v.exists():
        txt = v.read_text(encoding="utf-8")
        ok = "pass" in txt
        st.markdown(txt)
    a = ROOT / "AI_ASSISTANCE.md"
    if a.exists():
        with st.expander("Disclosure of AI assistance"):
            st.markdown(a.read_text(encoding="utf-8"))
