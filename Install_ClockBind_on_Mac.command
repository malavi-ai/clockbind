#!/bin/bash
# Installs ClockBind on this Mac (command line + Studio + ClockBind app in Applications).
# First time: a few minutes. Safe to run again to update.
cd "$(dirname "$0")" || exit 1
PKG="$(pwd)"
echo "ClockBind installer — package folder: $PKG"
if ! xcode-select -p >/dev/null 2>&1 || ! python3 -c 1 >/dev/null 2>&1; then
  echo "Python 3 is needed. A window will offer Apple's Command Line Tools: click Install."
  echo "When that has finished, open this installer again."
  xcode-select --install >/dev/null 2>&1
  read -n 1 -p "Press any key to close."; exit 1
fi
if [ ! -f "$PKG/pyproject.toml" ] || [ ! -d "$PKG/clockbind" ]; then
  echo "This installer must stay inside the unzipped ClockBind folder."; read -n 1; exit 1
fi
# Use the newest Python 3 on this Mac (3.10 or later is needed for the chat tools; Apple's built-in 3.9 still runs the rest).
PY=python3
for cand in /opt/homebrew/bin/python3 /usr/local/bin/python3 /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
            /opt/homebrew/bin/python3.13 /opt/homebrew/bin/python3.12 /usr/local/bin/python3.13 /usr/local/bin/python3.12 /usr/local/bin/python3.11 /usr/local/bin/python3.10; do
  if [ -x "$cand" ] && "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then PY="$cand"; break; fi
done
PYV=$("$PY" -c 'import sys; print("%d.%d" % sys.version_info[:2])')
echo "Using Python $PYV ($PY)"
if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
  echo "Note: the chat tools (Claude Desktop) need Python 3.10 or later. Everything else works with $PYV."
  echo "      For the chat tools, install Python from https://www.python.org/downloads/ and run this installer again."
fi
# a previous environment made with another Python version is replaced
if [ -x "$HOME/.clockbind-env/bin/python" ] && [ "$("$HOME/.clockbind-env/bin/python" -c 'import sys; print("%d.%d" % sys.version_info[:2])')" != "$PYV" ]; then
  rm -rf "$HOME/.clockbind-env"
fi
echo "Installing (this can take a few minutes)…"
"$PY" -m venv "$HOME/.clockbind-env" \
  && "$HOME/.clockbind-env/bin/python" -m pip install --upgrade pip >/dev/null \
  && "$HOME/.clockbind-env/bin/python" -m pip install --upgrade "${PKG}[all]" \
  || { echo ""; echo "Installation failed. Send a screenshot of this window."; read -n 1; exit 1; }
mkdir -p "$HOME/bin" && ln -sf "$HOME/.clockbind-env/bin/clockbind" "$HOME/bin/clockbind"
grep -q 'HOME/bin' "$HOME/.zshrc" 2>/dev/null || echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.zshrc"
# Put the ClockBind app in the user's Applications folder (no admin rights needed).
if [ -d "$PKG/ClockBind.app" ]; then
  mkdir -p "$HOME/Applications"
  rm -rf "$HOME/Applications/ClockBind.app"
  ditto "$PKG/ClockBind.app" "$HOME/Applications/ClockBind.app"
  xattr -dr com.apple.quarantine "$HOME/Applications/ClockBind.app" 2>/dev/null
  chmod +x "$HOME/Applications/ClockBind.app/Contents/MacOS/ClockBind"
  APP_MSG="ClockBind is now in your Applications folder (Finder → Go → Home → Applications). Drag it to the Dock for a one-click button."
fi
# Optional: connect ClockBind to Claude Desktop as a local tool server (a backup of the config is kept).
if "$HOME/.clockbind-env/bin/python" -c "import mcp" 2>/dev/null && { [ -d "/Applications/Claude.app" ] || [ -d "$HOME/Applications/Claude.app" ] || [ -d "$HOME/Library/Application Support/Claude" ]; }; then
  echo ""
  read -r -p "Connect ClockBind to Claude Desktop, so its tools appear in your chats? [y/N] " ANSWER
  case "$ANSWER" in
    [yY]*) "$HOME/.clockbind-env/bin/clockbind" connect claude-desktop ;;
    *) echo "Skipped. You can do it later with:  clockbind connect claude-desktop" ;;
  esac
fi
echo ""
echo "Done. $("$HOME/.clockbind-env/bin/clockbind" --version 2>/dev/null) is installed."
[ -n "$APP_MSG" ] && echo "$APP_MSG"
echo "Optional, for CFA and validation: install R from https://cran.r-project.org, then in R run:"
echo "  install.packages(c('lavaan','jsonlite','psych','irr','irrCAC','nnet','sandwich','clubSandwich','pwr','PSweight'))"
[ -d "$HOME/Applications/ClockBind.app" ] && open "$HOME/Applications/ClockBind.app"
read -n 1 -p "Press any key to close."
