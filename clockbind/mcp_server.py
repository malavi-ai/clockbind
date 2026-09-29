"""ClockBind as a local MCP server.

Any chat application that supports the Model Context Protocol (MCP) can call
ClockBind's research tools through this server. The server runs on the
researcher's own computer over stdio: files are read locally, and only
summaries (counts, check results, verdicts per pseudonymised code, locations of
problems) are returned to the chat. Cell values that could contain personal
data are never returned.

Start:  clockbind-mcp          (or: python -m clockbind.mcp_server)
"""
from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
from pathlib import Path

from . import __version__

PRIVACY_NOTE = ("Processed locally by ClockBind; only summaries are returned. "
                "Run folders with full results and manifests stay on this computer.")


def _out_dir() -> str:
    d = Path(os.environ.get("CLOCKBIND_OUT", Path.home() / "ClockBind_runs")).expanduser()
    d.mkdir(parents=True, exist_ok=True)
    return str(d)


def _path(p: str) -> str:
    q = Path(p).expanduser()
    if not q.exists():
        raise FileNotFoundError(f"File not found on this computer: {q}")
    return str(q.resolve())


def _cli(argv: list[str]) -> str:
    """Run a ClockBind command in-process and return what it printed."""
    from .cli import main

    buf = io.StringIO()
    code = 0
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            code = main(argv) or 0
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
            if e.code not in (None, 0) and not isinstance(e.code, int):
                print(e.code)
        except Exception as e:  # report, never crash the server
            from .cli import friendly_error
            code = 1
            print(friendly_error(e))
    text = buf.getvalue().strip()
    return f"{text}\n\n(exit code {code}) {PRIVACY_NOTE}"


from .project import find_assessment_sheet as _find_sheet  # noqa: E402


def build_server():
    try:  # MCP SDK 1.x
        from mcp.server.fastmcp import FastMCP as _Server
    except ImportError:
        try:  # MCP SDK 2.x
            from mcp.server.mcpserver import MCPServer as _Server
        except ImportError as e:  # pragma: no cover
            raise SystemExit("The MCP package is not installed. Install with:  pip install 'clockbind[mcp]'") from e

    mcp = _Server("clockbind", instructions=(
        "ClockBind research tools for reproducible screening and 'which clock binds?' analysis. "
        "All processing is local; results are summaries. Never ask the user to paste raw research data into the chat: "
        "pass file paths instead. Levels, verdicts and claim ceilings come from the registered rules; the researcher "
        "decides and codes criteria, the tools only apply and check the rules."))

    @mcp.tool()
    def clockbind_about() -> str:
        """Version, available tools and the privacy model of this ClockBind server."""
        return (f"ClockBind {__version__}. Tools: bridge_validate, audit_documents, privacy_scan, statistics_run, "
                f"binding_verdicts, export_ai_safe, doctoral_capabilities, preregistration_snapshot, publication_consistency_audit, verify_package, coder_agreement, freeze_gates, verify_references. "
                f"Output folder: {_out_dir()}. {PRIVACY_NOTE}")

    @mcp.tool()
    def bridge_validate(path: str, gates: str = "") -> str:
        """Validate a Bridge workbook locally. Checks workbook integrity; when a gates/protocol JSON is supplied,
        also applies the current evidence-level rules. Returns only safe summaries/locations, never cell values."""
        data = _path(path)
        first = _cli(["workbook", "check", "--data", data, "--out", _out_dir()])
        if not gates:
            return first
        g = _path(gates)
        found = _find_sheet(data, g)
        if found is None:
            return first + "\n\nCould not auto-detect the assessment sheet for gate application."
        second = _cli(["screen", "run", "--data", data, "--gates", g, "--sheet", found[0], "--header-row", str(found[1]), "--out", _out_dir()])
        return first + "\n\n" + second

    @mcp.tool()
    def audit_documents(path: str, names_file: str = "", check_bridge_wording: bool = True) -> str:
        """Audit Word/PDF/Excel/CSV/text/zip/folders locally for personal/confidential data and, optionally,
        outdated Bridge wording. Console response is aggregate-only by default; full local reports stay on the computer."""
        argv = ["audit", "docs", "--data", _path(path), "--out", _out_dir()]
        if names_file:
            argv += ["--names", _path(names_file)]
        if not check_bridge_wording:
            argv += ["--no-terms"]
        return _cli(argv)

    @mcp.tool()
    def statistics_run(path: str, analysis: str, params_json: str = "{}") -> str:
        """Run one ClockBind statistical analysis locally. `params_json` is a JSON object string.
        Returns the run summary; detailed Word/Excel/figure outputs and the manifest remain in the local run folder."""
        import json as _json
        obj = _json.loads(params_json or "{}")
        if not isinstance(obj, dict):
            raise ValueError("params_json must be a JSON object")
        return _cli(["stats", "run", "--data", _path(path), "--analysis", analysis, "--params", _json.dumps(obj), "--out", _out_dir()])

    @mcp.tool()
    def doctoral_capabilities() -> str:
        """List the installed Paper 1--4 and Bridge analysis engines. This exposes capability metadata only; no research data are read."""
        from .analysis import REGISTRY
        groups = {}
        for name, spec in REGISTRY.items():
            if spec.get("group", "").startswith("Paper ") or spec.get("group") == "Doctoral modules":
                groups.setdefault(spec["group"], []).append(name)
        lines = [f"{g}: " + ", ".join(sorted(v)) for g, v in sorted(groups.items())]
        return "ClockBind doctoral engines\n" + "\n".join(lines) + f"\n\n{PRIVACY_NOTE}"

    @mcp.tool()
    def preregistration_snapshot(files_json: str, output_path: str, status: str = "DRAFT", frozen_by: str = "", confirm: bool = False) -> str:
        """Create a local hash-locked preregistration snapshot from protocol/plan files. It never registers externally.
        `files_json` is a JSON list of local paths. FROZEN requires explicit confirm=true and frozen_by."""
        import json as _json
        from .publication import build_prereg_bundle
        files = _json.loads(files_json)
        if not isinstance(files, list) or not files:
            raise ValueError("files_json must be a non-empty JSON list of local protocol/plan paths")
        if status.upper() == "FROZEN" and (not confirm or not frozen_by.strip()):
            return "Not frozen. FROZEN requires explicit confirm=true and frozen_by. No external registration occurred."
        local = [_path(x) for x in files]
        out = Path(output_path).expanduser(); out.parent.mkdir(parents=True, exist_ok=True)
        build_prereg_bundle(None, local, out, status.upper(), frozen_by.strip(), "Created through ClockBind MCP")
        return f"Snapshot created: {out}\nExternal registry status: NOT REGISTERED BY CLOCKBIND\n{PRIVACY_NOTE}"

    @mcp.tool()
    def publication_consistency_audit(manuscript: str, registry: str) -> str:
        """Check a local manuscript against an explicit result/claim registry. Returns pass/fail counts only; detailed local report remains on the computer."""
        import json as _json
        from .publication import consistency_audit
        rows, summ = consistency_audit(_path(manuscript), _path(registry))
        out = Path(_out_dir()) / "manuscript_consistency_audit.json"
        out.write_text(_json.dumps({"summary": summ, "checks": rows}, indent=2), encoding="utf-8")
        return f"Checks: {summ['checks']} · PASS {summ['pass']} · FAIL {summ['fail']}\nLocal report: {out}\n{PRIVACY_NOTE}"

    @mcp.tool()
    def export_ai_safe(workbook: str, gates: str, output_path: str = "") -> str:
        """Create a local AI-safe Bridge export containing aggregate counts, hashes and protocol state only.
        No workbook cell values, raw text, personal-data values or local input paths are included in the package."""
        out = Path(output_path).expanduser() if output_path else Path(_out_dir()) / "Bridge_AI_Safe_Export.zip"
        out.parent.mkdir(parents=True, exist_ok=True)
        return _cli(["export", "ai-safe", "--workbook", _path(workbook), "--gates", _path(gates), "--output", str(out)])

    @mcp.tool()
    def verify_package() -> str:
        """Return ClockBind version and exact local code hash for reproducibility verification."""
        from .core.provenance import code_sha256, package_versions
        v = package_versions()
        return f"ClockBind {__version__} · code sha256 {code_sha256()} · Python {v.get('python')} · {PRIVACY_NOTE}"

    @mcp.tool()
    def validate_workbook(path: str) -> str:
        """Integrity check of a screening workbook: formula errors, uncalculated formulas, entries outside dropdown
        lists, episode/source links between sheets, override logs (reason + date), verdict consistency and a
        personal-data scan. Returns locations only, never cell contents."""
        return _cli(["workbook", "check", "--data", _path(path), "--out", _out_dir()])

    @mcp.tool()
    def privacy_scan(path: str) -> str:
        """GDPR/KVKK aid: scan every sheet of a CSV/Excel/SPSS file for e-mails, phone numbers, IBANs, card numbers,
        Turkish ID numbers, Hungarian tax IDs and name-like columns. Reports column, kind and count; values are never shown."""
        return _cli(["privacy", "scan", "--data", _path(path)])

    @mcp.tool()
    def screen_workbook(path: str, gates: str, sheet: str = "", header_row: int = -1) -> str:
        """Apply the registered screening gates: levels per episode, funnel counts, flow diagram (SVG) and integrity
        checks. Leave sheet and header_row empty to find the sheet and header row automatically (the sheet whose
        header contains the protocol's ID column). Results are 'not citable' until the gates are frozen."""
        data, g = _path(path), _path(gates)
        if not sheet or header_row < 0:
            found = _find_sheet(data, g)
            if found is None:
                return ("Could not find a sheet whose header contains the protocol's ID column. "
                        "Give the sheet name and the 0-based header row (Bridge workbook: 05_Level_Assessment, 2).")
            sheet = sheet or found[0]
            header_row = found[1] if header_row < 0 else header_row
        argv = ["screen", "run", "--data", data, "--gates", g, "--header-row", str(header_row), "--out", _out_dir()]
        if sheet:
            argv += ["--sheet", sheet]
        return _cli(argv)

    @mcp.tool()
    def binding_verdicts(path: str) -> str:
        """Which clock binds? Counterfactual critical-path verdict per episode from a timeline workbook (sheets
        Episodes and Steps): finance-binding, non-finance (named clock), jointly binding, non-binding or indeterminate,
        with the sign-stability rule, finance actionability and a reactive-downstream sensitivity check."""
        return _cli(["binding", "run", "--data", _path(path), "--out", _out_dir()])

    @mcp.tool()
    def binding_template(output_path: str) -> str:
        """Write a blank timeline workbook (Episodes, Steps, Guide) with one synthetic example to fill in."""
        out = Path(output_path).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        return _cli(["binding", "template", "--output", str(out)])

    @mcp.tool()
    def coder_agreement(author_path: str, coder_path: str, gates: str, sheet: str = "", header_row: int = -1) -> str:
        """Author versus independent coder on the same frozen gates: percent agreement, Cohen's kappa and Gwet's AC1
        per criterion, plus a disagreement list saved locally for resolution."""
        a_path, g = _path(author_path), _path(gates)
        if not sheet or header_row < 0:
            found = _find_sheet(a_path, g)
            if found is None:
                return "Could not find the assessment sheet. Give the sheet name and the 0-based header row."
            sheet = sheet or found[0]
            header_row = found[1] if header_row < 0 else header_row
        argv = ["screen", "agreement", "--data", a_path, "--coder", _path(coder_path), "--gates", g,
                "--header-row", str(header_row), "--out", _out_dir()]
        if sheet:
            argv += ["--sheet", sheet]
        return _cli(argv)

    @mcp.tool()
    def freeze_gates(gates: str, frozen_by: str, confirm: bool = False) -> str:
        """Freeze the screening gates once per protocol version (append-only register). This cannot be undone:
        it only runs when confirm is true, which the researcher must explicitly approve."""
        if not confirm:
            return ("Not frozen. Freezing is permanent for this protocol version. Ask the researcher to confirm, "
                    "then call again with confirm=true.")
        return _cli(["screen", "freeze", "--gates", _path(gates), "--by", frozen_by, "--out", _out_dir()])

    @mcp.tool()
    def verify_references(path: str, mailto: str) -> str:
        """Check each reference in a CSV/text list against Crossref and OpenAlex (sends reference metadata only, never
        research data). Returns the status counts; the full report is saved locally."""
        script = Path(__file__).resolve().parent / "verify_references.py"
        stem = Path(_out_dir()) / "reference_report"
        r = subprocess.run([sys.executable, str(script), _path(path), "--mailto", mailto, "--out", str(stem)],
                           capture_output=True, text=True, timeout=1800)
        tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-15:])
        return f"{tail}\n\nFull report: {stem}.csv / .md\n{PRIVACY_NOTE}"

    return mcp


def main():
    build_server().run()


if __name__ == "__main__":
    main()
