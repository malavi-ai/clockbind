"""Self-hosted @font-face rules (no requests to Google or any other font service)."""
from __future__ import annotations

import base64
from pathlib import Path

FONT_DIR = Path(__file__).resolve().parent / "assets" / "fonts"
_LATIN = "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"
_LATIN_EXT = "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF"
FACES = [  # family, file, weight, unicode-range
    ("Newsreader", "Newsreader-latin.woff2", "200 800", _LATIN),
    ("Newsreader", "Newsreader-latin-ext.woff2", "200 800", _LATIN_EXT),
    ("IBM Plex Sans", "IBMPlexSans-Regular.woff2", "400", None),
    ("IBM Plex Sans", "IBMPlexSans-Medium.woff2", "500", None),
    ("IBM Plex Sans", "IBMPlexSans-SemiBold.woff2", "600", None),
    ("IBM Plex Mono", "IBMPlexMono-Regular.woff2", "400", None),
    ("IBM Plex Mono", "IBMPlexMono-Medium.woff2", "500", None),
]


def font_css(mode: str = "inline", prefix: str = "fonts/") -> str:
    """mode='inline' embeds the fonts as data URIs (single-file pages, Studio); mode='files' links to prefix+file."""
    out = []
    for fam, fn, w, rng in FACES:
        if mode == "inline":
            src = "data:font/woff2;base64," + base64.b64encode((FONT_DIR / fn).read_bytes()).decode()
        else:
            src = prefix + fn
        r = f"unicode-range:{rng};" if rng else ""
        out.append(f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{w};font-display:swap;src:url({src}) format('woff2');{r}}}")
    return "\n".join(out)
