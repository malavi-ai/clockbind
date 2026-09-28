"""clockbind connect: plug ClockBind into chat applications as an MCP server.

    clockbind connect claude-desktop     writes/updates the Claude Desktop config
    clockbind connect show               prints the JSON block for any MCP client
    clockbind connect status             shows whether Claude Desktop is configured

The server runs locally over stdio with the same Python that runs this command,
so it works inside the ClockBind installer's environment without PATH changes.
Only summaries leave ClockBind (see PRIVACY.md).
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from datetime import datetime
from pathlib import Path

from ..core.plugin import Plugin

SERVER_NAME = "clockbind"


def server_block(out_dir: str | None = None) -> dict:
    block = {"command": sys.executable, "args": ["-m", "clockbind.mcp_server"]}
    if out_dir:
        block["env"] = {"CLOCKBIND_OUT": str(Path(out_dir).expanduser())}
    return block


def claude_desktop_config_path() -> Path:
    system = platform.system()
    home = Path.home()
    if system == "Darwin":
        return home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if system == "Windows":
        return Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "Claude" / "claude_desktop_config.json"
    return home / ".config" / "Claude" / "claude_desktop_config.json"


def _check_mcp() -> str | None:
    if sys.version_info < (3, 10):
        return (f"The chat tools need Python 3.10 or later; ClockBind is running on Python {sys.version_info[0]}.{sys.version_info[1]}. "
                "Install Python from https://www.python.org/downloads/ and run the ClockBind installer again.")
    try:
        import mcp  # noqa: F401
    except ImportError:
        return ("The MCP package is missing in this Python. Install it first:\n"
                f"  {sys.executable} -m pip install 'clockbind[mcp]'")
    return None


def cmd_claude_desktop(a):
    problem = _check_mcp()
    if problem:
        print(problem)
        return 1
    cfg_path = Path(a.config).expanduser() if a.config else claude_desktop_config_path()
    cfg = {}
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            print(f"The existing config is not valid JSON and was left untouched: {cfg_path}")
            return 1
        backup = cfg_path.with_suffix(f".backup-{datetime.now():%Y%m%d_%H%M%S}.json")
        shutil.copy2(cfg_path, backup)
        print(f"Backup of the previous config: {backup}")
    cfg.setdefault("mcpServers", {})[SERVER_NAME] = server_block(a.out)
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"ClockBind added to Claude Desktop: {cfg_path}")
    print("Quit and reopen Claude Desktop. The ClockBind tools then appear in the tools menu of a new chat.")
    return 0


def cmd_show(a):
    print(json.dumps({"mcpServers": {SERVER_NAME: server_block(a.out)}}, indent=2))
    problem = _check_mcp()
    if problem:
        print("\n" + problem)
    return 0


def cmd_status(a):
    p = claude_desktop_config_path()
    if not p.exists():
        print(f"Claude Desktop config not found ({p}). Run: clockbind connect claude-desktop")
        return 0
    try:
        cfg = json.loads(p.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        print(f"Claude Desktop config is not valid JSON: {p}")
        return 1
    block = cfg.get("mcpServers", {}).get(SERVER_NAME)
    print(f"Claude Desktop: {'configured' if block else 'not configured'} ({p})")
    if block:
        print(json.dumps(block, indent=2))
    print("MCP package: " + ("installed" if not _check_mcp() else "missing"))
    return 0


class Connect(Plugin):
    name = "connect"
    help = "Plug ClockBind into chat apps (Claude Desktop and other MCP clients) as a local tool server"

    def register(self, sub):
        p = sub.add_parser("claude-desktop", help="Add ClockBind to the Claude Desktop config (a backup is kept)")
        p.add_argument("--out", default="~/ClockBind_runs", help="folder for run outputs (default ~/ClockBind_runs)")
        p.add_argument("--config", default="", help="config file path (default: the standard location)")
        p.set_defaults(func=cmd_claude_desktop)
        p = sub.add_parser("show", help="Print the MCP JSON block for any MCP-capable chat app")
        p.add_argument("--out", default="~/ClockBind_runs")
        p.set_defaults(func=cmd_show)
        p = sub.add_parser("status", help="Is ClockBind configured in Claude Desktop?")
        p.set_defaults(func=cmd_status)


PLUGIN = Connect()
