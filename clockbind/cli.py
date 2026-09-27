"""Command-line entry point:  clockbind <plugin> <command> [options]"""
from __future__ import annotations

import argparse
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
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
