"""Build the ClockBind screening web app from webapp/ sources.

Outputs (run from the package root:  python webapp/build.py):
  clockbind/assets/ClockBind.html  single file, fully offline (library and fonts inlined)
  docs/                            installable offline web app for GitHub Pages (PWA)
  webapp/dist/artifact.html        fragment for the claude.ai artifact (library from cdnjs)
No output loads anything from Google or any font service.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
W = ROOT / "webapp"
sys.path.insert(0, str(ROOT))
from clockbind import __version__  # noqa: E402
from clockbind.fontcss import FONT_DIR, font_css  # noqa: E402

GATES = ROOT / "examples" / "screening" / "gates_v3_DRAFT.json"
ICON = ROOT / "clockbind" / "assets" / "clockbind-icon-64.png"
APPICON = ROOT / "clockbind" / "assets" / "clockbind-appicon-1024.png"
CDN = '<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>'


def body() -> str:
    t = (W / "template.html").read_text(encoding="utf-8")
    gates = json.dumps(json.loads(GATES.read_text(encoding="utf-8")), ensure_ascii=False, separators=(",", ":"))
    demo = json.dumps(json.loads((W / "demo_rows.json").read_text(encoding="utf-8")), ensure_ascii=False, separators=(",", ":"))
    t = t.replace("/*__ENGINE__*/", (W / "engine.js").read_text(encoding="utf-8"))
    t = t.replace("/*__GATES__*/", gates).replace("/*__DEMO__*/", demo)
    assert "/*__" not in t, "unfilled placeholder"
    return t


def favicon() -> str:
    return "data:image/png;base64," + base64.b64encode(ICON.read_bytes()).decode()


PWA_HEAD = """<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="ClockBind">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="theme-color" content="#14233A">"""


def page(head_extra: str, xlsx_tag: str, body_prefix: str = "", body_suffix: str = "", fonts_mode="inline") -> str:
    head = (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            f'<title>ClockBind</title><link rel="icon" href="{favicon()}">\n{head_extra}\n'
            f'<style>{font_css(fonts_mode)}</style>\n'
            f'<meta name="generator" content="ClockBind {__version__}">\n</head><body>\n')
    return head + body_prefix + body().replace("<!--__HEAD__-->", xlsx_tag) + body_suffix + "\n</body></html>\n"


def build():
    from clockbind.resources import sync_bundled
    sync_bundled()  # keep clockbind/data in step with the repository originals
    xlsx = (W / "vendor" / "xlsx.full.min.js").read_text(encoding="utf-8")
    # 1) single offline file
    single = page("", "<script>" + xlsx + "</script>")
    (ROOT / "clockbind" / "assets" / "ClockBind.html").write_text(single, encoding="utf-8")
    # 2) artifact fragment (claude.ai wraps it; cdnjs is allowed there)
    (W / "dist").mkdir(exist_ok=True)
    frag = "<title>ClockBind</title>\n<style>" + font_css("inline") + "</style>\n" + body().replace("<!--__HEAD__-->", CDN)
    (W / "dist" / "artifact.html").write_text(frag, encoding="utf-8")
    # 3) PWA in docs/
    D = ROOT / "docs"
    if D.exists():
        shutil.rmtree(D)
    (D / "fonts").mkdir(parents=True)
    for f in FONT_DIR.glob("*.woff2"):
        shutil.copy2(f, D / "fonts" / f.name)
    for f in FONT_DIR.glob("LICENSE*"):
        shutil.copy2(f, D / "fonts" / f.name)
    (D / "xlsx.full.min.js").write_text(xlsx, encoding="utf-8")
    from PIL import Image
    im = Image.open(APPICON).convert("RGB")
    for s in (180, 192, 512):
        im.resize((s, s), Image.LANCZOS).save(D / f"icon-{s}.png", optimize=True)
    bar = (W / "pwa_bar.html").read_text(encoding="utf-8")
    pwa = page(PWA_HEAD + "\n" + (W / "pwa_bar.css").read_text(encoding="utf-8"), '<script src="xlsx.full.min.js"></script>',
               body_prefix=bar, body_suffix=(W / "pwa_bar.js").read_text(encoding="utf-8"), fonts_mode="files")
    (D / "index.html").write_text(pwa, encoding="utf-8")
    json.dump({"name": "ClockBind", "short_name": "ClockBind",
               "description": "ClockBind case screening. Works offline; files never leave the device.",
               "start_url": "./", "scope": "./", "display": "standalone", "background_color": "#EEF1F0", "theme_color": "#14233A",
               "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                         {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}]},
              open(D / "manifest.webmanifest", "w"), indent=2)
    files = sorted(p.relative_to(D).as_posix() for p in D.rglob("*") if p.is_file() and p.name != "sw.js")
    digest = hashlib.sha256(b"".join((D / f).read_bytes() for f in files)).hexdigest()[:10]
    sw = (W / "sw.template.js").read_text(encoding="utf-8")
    sw = sw.replace("__VERSION__", f"clockbind-{__version__}-{digest}").replace("__FILES__", json.dumps(["./"] + files))
    (D / "sw.js").write_text(sw, encoding="utf-8")
    (D / ".nojekyll").write_text("")
    for name, text in [("single", single), ("pwa", pwa)]:
        assert "fonts.googleapis" not in text and "fonts.gstatic" not in text, name
    print(f"built ClockBind {__version__}: single {len(single)//1024} KB, docs {len(files)} files, sw {digest}")


if __name__ == "__main__":
    build()
