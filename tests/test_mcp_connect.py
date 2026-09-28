"""Chat integration: the connect command and the MCP server (skipped if the MCP package is absent)."""
import asyncio
import json
import sys

import pytest

from clockbind.cli import main


def test_connect_writes_config_and_keeps_other_servers(tmp_path):
    cfg = tmp_path / "claude_desktop_config.json"
    cfg.write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}, "keep": 1}))
    pytest.importorskip("mcp")
    assert main(["connect", "claude-desktop", "--config", str(cfg), "--out", str(tmp_path / "runs")]) == 0
    data = json.loads(cfg.read_text())
    assert data["keep"] == 1 and "other" in data["mcpServers"]
    block = data["mcpServers"]["clockbind"]
    assert block["command"] == sys.executable and block["args"] == ["-m", "clockbind.mcp_server"]
    assert list(tmp_path.glob("claude_desktop_config.backup-*.json"))


def test_connect_refuses_invalid_json(tmp_path):
    pytest.importorskip("mcp")
    cfg = tmp_path / "c.json"
    cfg.write_text("{not json")
    assert main(["connect", "claude-desktop", "--config", str(cfg)]) == 1
    assert cfg.read_text() == "{not json"


def test_mcp_server_tools_return_summaries(tmp_path):
    pytest.importorskip("mcp")
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    import os

    async def go():
        p = StdioServerParameters(command=sys.executable, args=["-m", "clockbind.mcp_server"],
                                  env={**os.environ, "CLOCKBIND_OUT": str(tmp_path / "runs")})
        async with stdio_client(p) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                names = {t.name for t in (await s.list_tools()).tools}
                assert {"validate_workbook", "privacy_scan", "screen_workbook", "binding_verdicts", "coder_agreement", "freeze_gates"} <= names
                tpl = tmp_path / "t.xlsx"
                out = (await s.call_tool("binding_template", {"output_path": str(tpl)})).content[0].text
                assert "Template written" in out
                out = (await s.call_tool("binding_verdicts", {"path": str(tpl)})).content[0].text
                assert "EX-01" in out and "Non-finance: logistics" in out
                out = (await s.call_tool("freeze_gates", {"gates": str(tpl), "frozen_by": "x"})).content[0].text
                assert out.startswith("Not frozen")
                out = (await s.call_tool("privacy_scan", {"path": str(tmp_path / "missing.xlsx")})).content[0].text
                assert "not found" in out.lower()

    asyncio.run(go())
