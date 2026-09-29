"""Privacy-preserving export for AI-assisted research review.

The export contains aggregate project state, hashes and reproducibility metadata only.
It deliberately excludes workbook cell values, document text, customer identifiers,
file paths and detected personal-data values.
"""
from __future__ import annotations

import datetime as dt
import io
import json
import zipfile
from pathlib import Path

from . import __version__
from .core.provenance import code_sha256, package_versions, sha256_file
from .project import project_status

SCHEMA_VERSION = "clockbind-ai-safe-1"


def safe_payload(workbook: str, gates: str) -> dict:
    wb = Path(workbook).expanduser()
    gp = Path(gates).expanduser()
    if not wb.exists():
        raise FileNotFoundError(wb)
    if not gp.exists():
        raise FileNotFoundError(gp)
    status = project_status(str(wb), str(gp))
    return {
        "schema": SCHEMA_VERSION,
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "clockbind_version": __version__,
        "code_sha256": code_sha256(),
        "software": package_versions(),
        "inputs": {
            "workbook_sha256": sha256_file(wb),
            "protocol_sha256": sha256_file(gp),
        },
        "protocol": {
            "version": status.get("protocol", ""),
            "frozen": bool(status.get("frozen", False)),
        },
        "bridge": {
            "roadmap_step": status.get("step"),
            "sources": status.get("sources", {}),
            "episodes": status.get("episodes", 0),
            "levels": status.get("levels", {}),
            "held_at_s0": status.get("held", 0),
            "workbook_checks": {"fail": status.get("fail"), "warn": status.get("warn")},
            "status_complete": not bool(status.get("error")),
        },
        "privacy_contract": {
            "contains_cell_values": False,
            "contains_document_text": False,
            "contains_personal_data_values": False,
            "contains_input_paths": False,
            "purpose": "Share aggregate research state with an AI assistant without sharing raw study records.",
        },
    }


def build_safe_zip(workbook: str, gates: str) -> bytes:
    payload = safe_payload(workbook, gates)
    readme = (
        "ClockBind AI-safe research export\n"
        "=================================\n\n"
        "This package contains aggregate Bridge-study status and reproducibility metadata only.\n"
        "It does not contain workbook cell values, raw documents, customer names, detected values, or input paths.\n"
        "The SHA-256 hashes let a reviewer link the summary to the exact local inputs without receiving those inputs.\n"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("ai_safe_summary.json", json.dumps(payload, indent=2, ensure_ascii=False))
        z.writestr("README.txt", readme)
    return buf.getvalue()


def write_safe_zip(workbook: str, gates: str, output: str) -> Path:
    out = Path(output).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(build_safe_zip(workbook, gates))
    return out
