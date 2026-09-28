"""Branded PDF reports for ClockBind results (checks, verdicts, screening, Studio outputs).

    build_pdf(path, title, blocks, subtitle="", meta={})

blocks is a list of tuples:
    ("h", "Heading")                       section heading
    ("p", "Paragraph text")                paragraph
    ("table", DataFrame[, caption])        table (long tables continue on the next page)
    ("image", path_or_matplotlib_figure)   figure
    ("kv", [(label, value), ...])          label/value list
    ("note", "Small print")                muted note
Fonts are bundled (IBM Plex, Newsreader; SIL Open Font Licence); nothing is downloaded.
"""
from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import pandas as pd

from . import __version__

FONTS = Path(__file__).resolve().parent / "assets" / "fonts"
INK, BRASS, MUTED, LINE, SUNK = "#14233A", "#A4772B", "#5A6778", "#D5DCE1", "#F2F5F7"
_REGISTERED = False


def _fonts():
    global _REGISTERED
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    if _REGISTERED:
        return
    for name in ("IBMPlexSans-Regular", "IBMPlexSans-SemiBold", "IBMPlexMono-Regular", "Newsreader-SemiBold"):
        pdfmetrics.registerFont(TTFont(name, str(FONTS / f"{name}.ttf")))
    from reportlab.lib.fonts import addMapping

    addMapping("IBMPlexSans-Regular", 0, 0, "IBMPlexSans-Regular")
    addMapping("IBMPlexSans-Regular", 1, 0, "IBMPlexSans-SemiBold")
    _REGISTERED = True


def _styles():
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import ParagraphStyle

    base = dict(fontName="IBMPlexSans-Regular", fontSize=9.5, leading=13.5, textColor=HexColor(INK))
    return {
        "title": ParagraphStyle("title", fontName="Newsreader-SemiBold", fontSize=24, leading=28, textColor=HexColor(INK), spaceAfter=4),
        "sub": ParagraphStyle("sub", fontName="IBMPlexSans-Regular", fontSize=10, leading=14, textColor=HexColor(MUTED), spaceAfter=10),
        "h": ParagraphStyle("h", fontName="Newsreader-SemiBold", fontSize=14.5, leading=18, textColor=HexColor(INK), spaceBefore=14, spaceAfter=6),
        "p": ParagraphStyle("p", spaceAfter=6, **base),
        "note": ParagraphStyle("note", fontName="IBMPlexSans-Regular", fontSize=8, leading=11, textColor=HexColor(MUTED), spaceAfter=4),
        "cell": ParagraphStyle("cell", fontName="IBMPlexSans-Regular", fontSize=7.6, leading=9.6, textColor=HexColor(INK)),
        "head": ParagraphStyle("headcell", fontName="IBMPlexSans-SemiBold", fontSize=7.2, leading=9, textColor=HexColor("#FFFFFF")),
        "kvk": ParagraphStyle("kvk", fontName="IBMPlexSans-Regular", fontSize=9, leading=12, textColor=HexColor(MUTED)),
        "kvv": ParagraphStyle("kvv", fontName="IBMPlexMono-Regular", fontSize=8.6, leading=12, textColor=HexColor(INK)),
    }


def _esc(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    s = f"{v:.4g}" if isinstance(v, float) else str(v)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _table(df: pd.DataFrame, width: float, st):
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import LongTable, Paragraph, TableStyle

    df = df.copy()
    if df.index.name is not None or not pd.api.types.is_integer_dtype(df.index):
        df = df.reset_index()
    else:
        df = df.reset_index(drop=True)
    cols = [str(c) for c in df.columns]
    # column widths proportional to content length, within limits
    lens = [max([min(len(c), 14)] + [len(_esc(v)) for v in df.iloc[:200, i]]) for i, c in enumerate(cols)]
    lens = [min(max(n, 6), 60) for n in lens]
    total = sum(lens)
    widths = [width * n / total for n in lens]
    data = [[Paragraph(_esc(c), st["head"]) for c in cols]]
    for _, row in df.iterrows():
        data.append([Paragraph(_esc(v), st["cell"]) for v in row.tolist()])
    t = LongTable(data, colWidths=widths, repeatRows=1)
    style = [("BACKGROUND", (0, 0), (-1, 0), HexColor(INK)),
             ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LINEBELOW", (0, 0), (-1, -1), 0.4, HexColor(LINE)),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
             ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    for r in range(2, len(data), 2):
        style.append(("BACKGROUND", (0, r), (-1, r), HexColor(SUNK)))
    t.setStyle(TableStyle(style))
    return t


def _image(obj, width: float):
    from reportlab.platypus import Image

    if isinstance(obj, (bytes, bytearray)):
        src = io.BytesIO(obj)
    elif hasattr(obj, "savefig"):
        buf = io.BytesIO()
        obj.savefig(buf, format="png", dpi=200, bbox_inches="tight")
        buf.seek(0)
        src = buf
    else:
        src = str(obj)
    img = Image(src)
    ratio = img.imageHeight / img.imageWidth
    img.drawWidth = min(width, img.imageWidth)
    img.drawHeight = img.drawWidth * ratio
    return img


def build_pdf(path, title: str, blocks: list, subtitle: str = "", meta: dict | None = None, landscape_pages: bool = False) -> Path:
    """Write a branded PDF report and return its path. `path` may also be a writable binary buffer."""
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    _fonts()
    st = _styles()
    size = landscape(A4) if landscape_pages else A4
    margin = 16 * mm
    width = size[0] - 2 * margin
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    def frame(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(HexColor(INK))
        canvas.rect(0, size[1] - 11 * mm, size[0], 11 * mm, stroke=0, fill=1)
        canvas.setFillColor(HexColor(BRASS))
        canvas.rect(0, size[1] - 11.8 * mm, size[0], 0.8 * mm, stroke=0, fill=1)
        canvas.setFillColor(HexColor("#E9EEF3"))
        canvas.setFont("Newsreader-SemiBold", 12)
        canvas.drawString(margin, size[1] - 7.4 * mm, "ClockBind")
        canvas.setFont("IBMPlexSans-Regular", 8)
        canvas.drawRightString(size[0] - margin, size[1] - 7.2 * mm, title[:90])
        canvas.setFillColor(HexColor(MUTED))
        canvas.setFont("IBMPlexSans-Regular", 7.5)
        canvas.drawString(margin, 9 * mm, f"ClockBind {__version__} · generated {stamp} · processed locally")
        canvas.drawRightString(size[0] - margin, 9 * mm, f"Page {doc.page}")
        canvas.restoreState()

    story = [Spacer(1, 6 * mm), Paragraph(_esc(title), st["title"])]
    if subtitle:
        story.append(Paragraph(_esc(subtitle), st["sub"]))
    if meta:
        blocks = [("kv", list(meta.items()))] + list(blocks)
    for b in blocks:
        kind = b[0]
        if kind == "h":
            story.append(Paragraph(_esc(b[1]), st["h"]))
        elif kind == "p":
            story.append(Paragraph(_esc(b[1]), st["p"]))
        elif kind == "note":
            story.append(Paragraph(_esc(b[1]), st["note"]))
        elif kind == "kv":
            rows = [[Paragraph(_esc(k), st["kvk"]), Paragraph(_esc(v), st["kvv"])] for k, v in b[1]]
            t = Table(rows, colWidths=[width * .28, width * .72])
            t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), HexColor(SUNK)), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                   ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 6)]))
            story += [t, Spacer(1, 4 * mm)]
        elif kind == "table":
            df = b[1]
            if df is None or len(df) == 0:
                story.append(Paragraph("No rows.", st["note"]))
            else:
                story.append(_table(df, width, st))
            if len(b) > 2 and b[2]:
                story.append(Paragraph(_esc(b[2]), st["note"]))
            story.append(Spacer(1, 3 * mm))
        elif kind == "image":
            story += [KeepTogether([_image(b[1], width)]), Spacer(1, 3 * mm)]
    target = path if hasattr(path, "write") else str(path)
    doc = SimpleDocTemplate(target, pagesize=size, leftMargin=margin, rightMargin=margin, topMargin=18 * mm, bottomMargin=16 * mm,
                            title=title, author="ClockBind", subject=subtitle or title, creator=f"ClockBind {__version__}")
    doc.build(story, onFirstPage=frame, onLaterPages=frame)
    return path if hasattr(path, "write") else Path(path)


def add_pdf(run, name: str, title: str, blocks: list, subtitle: str = "", meta: dict | None = None, **kw):
    """Write a PDF into a run folder and register it; returns the path, or None if the PDF could not be made."""
    try:
        out = run.path(name)
        build_pdf(out, title, blocks, subtitle=subtitle, meta=meta, **kw)
        run.add_output(out)
        return out
    except Exception as e:  # a report must never break the analysis run
        print(f"(PDF report not written: {type(e).__name__}: {e})")
        return None


def outputs_to_pdf(outputs, path, title: str = "ClockBind output"):
    """Studio results (tables, figures, methods text, notes, syntax and references) as one PDF."""
    import json

    blocks, refs = [], []
    for o in outputs:
        blocks.append(("h", o.title))
        blocks.append(("note", f"Data sha256 {o.data_sha256[:16]} · {o.created}" + (f" · n = {o.n_used}" if o.n_used is not None else "")))
        for b in o.blocks:
            if b.kind == "table":
                if b.title:
                    blocks.append(("p", b.title))
                blocks.append(("table", b.content, ("Note. " + b.note) if b.note else ""))
            elif b.kind == "figure":
                if b.title:
                    blocks.append(("p", b.title))
                blocks.append(("image", b.content))
                if b.note:
                    blocks.append(("note", "Note. " + b.note))
            elif b.kind == "methods":
                blocks.append(("p", "Methods text: " + str(b.content)))
            elif b.kind == "warning":
                blocks.append(("p", "Caution: " + str(b.content)))
            else:
                blocks.append(("p", str(b.content)))
        blocks.append(("note", "Syntax: " + json.dumps(o.syntax, ensure_ascii=False)))
        refs += [x for x in o.references if x not in refs]
    if refs:
        blocks.append(("h", "References"))
        blocks += [("p", r) for r in refs]
    return build_pdf(path, title, blocks, subtitle=f"{len(outputs)} result(s)")
