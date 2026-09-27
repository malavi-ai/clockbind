"""Locate files that ship with ClockBind, both in a source checkout and in an installed copy.

Installed copies only contain the clockbind/ package, so data and documents the software needs at run
time are also kept in clockbind/data/ (tests check that these copies match the repository originals).
"""
from __future__ import annotations

from pathlib import Path

PKG = Path(__file__).resolve().parent
ROOT = PKG.parent
BUNDLED = {  # name -> original location in the repository
    "validation_data.csv": "validation/validation_data.csv",
    "conjoint_synthetic.csv": "examples/conjoint_synthetic.csv",
    "gates_v3_DRAFT.json": "examples/screening/gates_v3_DRAFT.json",
    "VALIDATION.md": "VALIDATION.md",
    "AI_ASSISTANCE.md": "AI_ASSISTANCE.md",
    "PRIVACY.md": "PRIVACY.md",
}


def resource(name: str) -> Path:
    """Path of a bundled file (source checkout first, then the installed copy)."""
    for p in (ROOT / BUNDLED.get(name, name), PKG / "data" / name):
        if p.exists():
            return p
    raise FileNotFoundError(f"Bundled file not found: {name}")


def sync_bundled() -> list[str]:
    """Copy repository originals into clockbind/data (run before building a release)."""
    import shutil
    (PKG / "data").mkdir(exist_ok=True)
    done = []
    for name, rel in BUNDLED.items():
        src = ROOT / rel
        if src.exists():
            shutil.copy2(src, PKG / "data" / name); done.append(name)
    return done


if __name__ == "__main__":
    print("synced:", ", ".join(sync_bundled()))
