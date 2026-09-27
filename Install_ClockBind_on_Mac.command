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
echo "Installing (this can take a few minutes)…"
python3 -m venv "$HOME/.clockbind-env" \
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
echo ""
echo "Done. $("$HOME/.clockbind-env/bin/clockbind" --version 2>/dev/null) is installed."
[ -n "$APP_MSG" ] && echo "$APP_MSG"
echo "Optional, for CFA and validation: install R from https://cran.r-project.org, then in R run:"
echo "  install.packages(c('lavaan','jsonlite','psych','irr','irrCAC','nnet','sandwich','clubSandwich','pwr','PSweight'))"
[ -d "$HOME/Applications/ClockBind.app" ] && open "$HOME/Applications/ClockBind.app"
read -n 1 -p "Press any key to close."
