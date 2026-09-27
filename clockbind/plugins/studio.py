"""Launch ClockBind Studio (local app in the browser; data never leave this computer)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from ..core.plugin import Plugin


def cmd_studio(a):
    app_dir = Path(__file__).resolve().parents[1] / "studio"
    try:
        import streamlit  # noqa: F401
    except ImportError:
        raise SystemExit("ClockBind Studio needs Streamlit:  pip install streamlit")
    env = dict(os.environ, STREAMLIT_BROWSER_GATHER_USAGE_STATS="false")
    from ..analysis.style import BRAND
    c = {"ink": "#14233A", "accent": "#A4772B", "background": "#EEF1F0", **BRAND.get("colors", {})}
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_dir / "app.py"), "--server.address", "localhost", "--server.port", str(a.port),
           "--browser.gatherUsageStats", "false", "--theme.base", "light", "--theme.primaryColor", c["accent"], "--theme.backgroundColor", c["background"],
           "--theme.secondaryBackgroundColor", "#FFFFFF", "--theme.textColor", c["ink"], "--client.toolbarMode", "minimal"]
    if a.headless:
        cmd += ["--server.headless", "true"]
    return subprocess.call(cmd, cwd=str(app_dir))


class Studio(Plugin):
    name = "studio"
    help = "Open ClockBind Studio, the point-and-click app (runs locally)"

    def register(self, sub):
        p = sub.add_parser("open", help="Start the Studio in your browser")
        p.add_argument("--port", type=int, default=8501)
        p.add_argument("--headless", action="store_true")
        p.set_defaults(func=cmd_studio)


PLUGIN = Studio()
