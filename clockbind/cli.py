"""Command-line entry point:  clockbind <plugin> <command> [options]"""
from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .core.plugin import discover


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clockbind",
        description="Reproducible statistics toolkit with plugins. Every run writes a manifest "
        "(inputs, seed, software versions, output hashes).",
    )
    parser.add_argument("--version", action="version", version=f"clockbind {__version__}")
    sub = parser.add_subparsers(dest="plugin", metavar="<plugin>")
    for plugin in discover():
        p = sub.add_parser(plugin.name, help=plugin.help, description=plugin.help)
        psub = p.add_subparsers(dest="command", metavar="<command>")
        plugin.register(psub)
        p.set_defaults(_plugin_parser=p)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "plugin", None):
        parser.print_help()
        return 1
    if not hasattr(args, "func"):
        args._plugin_parser.print_help()
        return 1
    if os.environ.get("CLOCKBIND_DEBUG"):
        return int(args.func(args) or 0)
    try:
        return int(args.func(args) or 0)
    except KeyboardInterrupt:
        print("Stopped.")
        return 130
    except Exception as e:  # clear message instead of a traceback; CLOCKBIND_DEBUG=1 shows the traceback
        print(friendly_error(e), file=sys.stderr)
        return 1


def friendly_error(e: Exception) -> str:
    import json
    import zipfile
    msg = str(e)
    if isinstance(e, FileNotFoundError):
        return f"File not found: {getattr(e, 'filename', None) or msg}"
    if isinstance(e, PermissionError):
        return f"No permission to read or write: {getattr(e, 'filename', None) or msg}. Close the file in Excel and retry."
    if isinstance(e, zipfile.BadZipFile) or "Excel file format cannot be determined" in msg or "does not support" in msg:
        return "The file could not be opened as an Excel workbook. Open it in Excel, save it as .xlsx, and retry."
    if isinstance(e, json.JSONDecodeError):
        return f"The protocol (gates) file is not valid JSON (line {e.lineno}, column {e.colno}). Use the .json protocol file, not the workbook."
    if isinstance(e, ValueError) and "Worksheet named" in msg:
        return f"{msg}. Check the sheet name (for the Bridge workbook: 05_Level_Assessment)."
    return f"{type(e).__name__}: {msg}  (set CLOCKBIND_DEBUG=1 for details)"


if __name__ == "__main__":
    sys.exit(main())
