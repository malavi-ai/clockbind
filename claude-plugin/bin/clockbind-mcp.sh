#!/bin/sh
# Starts the local ClockBind MCP server with the first Python that has ClockBind installed.
for PY in "$HOME/.clockbind-env/bin/python" "$(command -v python3)" "$(command -v python)"; do
  if [ -n "$PY" ] && [ -x "$PY" ] && "$PY" -c "import clockbind.mcp_server, mcp" >/dev/null 2>&1; then
    exec "$PY" -m clockbind.mcp_server
  fi
done
echo "ClockBind with MCP support was not found. Install it with:  pip install 'clockbind[mcp] @ git+https://github.com/malavi-ai/clockbind'  (or run the Mac installer)." >&2
exit 1
