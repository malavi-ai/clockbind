#!/bin/bash
# Double-click on a Mac to install ClockBind (command line + Studio app). Takes a few minutes the first time.
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is needed. A window will offer Apple's developer tools; accept, then double-click this file again."
  xcode-select --install; exit 1
fi
python3 -m venv "$HOME/.clockbind-env" && "$HOME/.clockbind-env/bin/pip" install --upgrade pip >/dev/null && "$HOME/.clockbind-env/bin/pip" install -e ".[all]" || { echo "Installation failed. Send a screenshot of this window."; read -n 1; exit 1; }
mkdir -p "$HOME/bin" && ln -sf "$HOME/.clockbind-env/bin/clockbind" "$HOME/bin/clockbind"
grep -q 'HOME/bin' "$HOME/.zshrc" 2>/dev/null || echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.zshrc"
echo ""
echo "Done. Double-click Start_ClockBind_Studio.command to open the Studio."
echo "Optional, for CFA and validation: install R from https://cran.r-project.org, then in R run:"
echo "  install.packages(c('lavaan','jsonlite','psych','irr','irrCAC','nnet','sandwich','clubSandwich','pwr','PSweight'))"
read -n 1
