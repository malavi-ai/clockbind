"""Run provenance: every run writes a manifest so any number can be traced to
its code version, inputs, seed and software versions."""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import platform
import sys
from pathlib import Path

from .. import __version__

TRACKED_PACKAGES = ["numpy", "pandas", "scipy", "statsmodels", "sklearn", "openpyxl"]


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def package_versions() -> dict:
    out = {"python": sys.version.split()[0], "clockbind": __version__, "platform": platform.platform()}
    for name in TRACKED_PACKAGES:
        try:
            mod = __import__(name)
            out[name] = getattr(mod, "__version__", "unknown")
        except Exception:
            out[name] = "not installed"
    return out


def code_sha256() -> str:
    """Hash of all clockbind source files, so results can be tied to exact code even without a version bump."""
    root = Path(__file__).resolve().parents[1]
    h = hashlib.sha256()
    for f in sorted(root.rglob("*.py")):
        h.update(str(f.relative_to(root)).encode())
        h.update(f.read_bytes())
    return h.hexdigest()


class RunLog:
    """Creates <out>/<plugin>_<command>_<timestamp>/ and a manifest.json.

    Use as a context manager. Outputs registered with `add_output` are hashed
    at close so later edits to a result file can be detected.
    """

    def __init__(self, out_dir: str | Path, plugin: str, command: str, args: dict, seed: int | None):
        stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.dir = Path(out_dir) / f"{plugin}_{command}_{stamp}"
        suffix = 1
        while self.dir.exists():
            self.dir = Path(out_dir) / f"{plugin}_{command}_{stamp}_{suffix}"
            suffix += 1
        self.dir.mkdir(parents=True)
        self.manifest = {
            "tool": "clockbind",
            "plugin": plugin,
            "command": command,
            "command_line": " ".join(sys.argv),
            "arguments": {k: (str(v) if isinstance(v, Path) else v) for k, v in args.items()},
            "seed": seed,
            "started": _dt.datetime.now().isoformat(timespec="seconds"),
            "software": package_versions(),
            "code_sha256": code_sha256(),
            "inputs": {},
            "outputs": {},
            "warnings": [],
            "status": "running",
        }

    def add_input(self, path: str | Path, label: str = "data") -> None:
        p = Path(path)
        self.manifest["inputs"][label] = {"path": str(p.resolve()), "sha256": sha256_file(p), "bytes": p.stat().st_size}

    def path(self, name: str) -> Path:
        return self.dir / name

    def add_output(self, path: str | Path) -> None:
        self.manifest["outputs"][Path(path).name] = None  # hashed at close

    def warn(self, msg: str) -> None:
        self.manifest["warnings"].append(msg)
        print(f"WARNING: {msg}", file=sys.stderr)

    def note(self, key: str, value) -> None:
        self.manifest[key] = value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.manifest["finished"] = _dt.datetime.now().isoformat(timespec="seconds")
        self.manifest["status"] = "failed: " + repr(exc) if exc else "completed"
        for name in list(self.manifest["outputs"]):
            p = self.dir / name
            if p.exists():
                self.manifest["outputs"][name] = sha256_file(p)
        with open(self.dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, indent=2, default=str)
        print(f"Run folder: {self.dir}")
        return False


def env_seed(seed: int | None) -> int:
    if seed is None:
        seed = int.from_bytes(os.urandom(4), "little")
    return int(seed)
