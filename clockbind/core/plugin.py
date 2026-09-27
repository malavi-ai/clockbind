"""Plugin system.

A plugin is a Python module that defines a subclass of `Plugin` named
`PLUGIN` (an instance) at module level. Plugins are discovered from:

1. built-in modules in clockbind/plugins/
2. every *.py file in folders listed in the CLOCKBIND_PLUGINS environment
   variable (separated by os.pathsep) and in ~/.clockbind/plugins/
3. installed packages exposing the entry-point group "clockbind.plugins"

Each plugin registers one or more commands:  clockbind <plugin> <command> ...
"""
from __future__ import annotations

import importlib
import importlib.util
import os
import pkgutil
import sys
from pathlib import Path


class Plugin:
    name: str = "unnamed"
    help: str = ""

    def register(self, subparsers) -> None:
        """Add this plugin's commands. Each command must set func=callable(args)."""
        raise NotImplementedError


def _load_file(path: Path):
    spec = importlib.util.spec_from_file_location(f"clockbind_ext_{path.stem}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def discover() -> list[Plugin]:
    found: dict[str, Plugin] = {}
    from .. import plugins as builtin

    for info in pkgutil.iter_modules(builtin.__path__):
        mod = importlib.import_module(f"clockbind.plugins.{info.name}")
        p = getattr(mod, "PLUGIN", None)
        if isinstance(p, Plugin):
            found[p.name] = p

    folders = [Path.home() / ".clockbind" / "plugins"]
    folders += [Path(x) for x in os.environ.get("CLOCKBIND_PLUGINS", "").split(os.pathsep) if x]
    for folder in folders:
        if folder.is_dir():
            for f in sorted(folder.glob("*.py")):
                try:
                    p = getattr(_load_file(f), "PLUGIN", None)
                    if isinstance(p, Plugin):
                        found[p.name] = p
                except Exception as e:  # keep the tool usable if one plugin is broken
                    print(f"Could not load plugin {f}: {e}", file=sys.stderr)

    try:
        from importlib.metadata import entry_points

        for ep in entry_points(group="clockbind.plugins"):
            try:
                p = ep.load()
                p = p() if isinstance(p, type) else p
                if isinstance(p, Plugin):
                    found[p.name] = p
            except Exception as e:
                print(f"Could not load entry-point plugin {ep.name}: {e}", file=sys.stderr)
    except Exception:
        pass
    return [found[k] for k in sorted(found)]
