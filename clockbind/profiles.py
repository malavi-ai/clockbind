"""Local user profiles: name, language and project settings, stored only on this computer.

File: ~/.clockbind/profiles.json (override with CLOCKBIND_HOME). No passwords and no online accounts.
"""
from __future__ import annotations

import json
import os
from pathlib import Path


def _file() -> Path:
    base = Path(os.environ.get("CLOCKBIND_HOME", Path.home() / ".clockbind")).expanduser()
    base.mkdir(parents=True, exist_ok=True)
    return base / "profiles.json"


def load() -> dict:
    f = _file()
    if f.exists():
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("profiles"), list):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {"profiles": [], "last": None}


def save(data: dict) -> None:
    f = _file()
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(f)


def get(name: str) -> dict | None:
    return next((p for p in load()["profiles"] if p.get("name") == name), None)


def upsert(profile: dict) -> dict:
    data = load()
    data["profiles"] = [p for p in data["profiles"] if p.get("name") != profile["name"]] + [profile]
    data["last"] = profile["name"]
    save(data)
    return profile


def set_last(name: str) -> None:
    data = load()
    data["last"] = name
    save(data)
