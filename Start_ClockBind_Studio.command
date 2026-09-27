#!/bin/bash
# Double-click on a Mac: opens ClockBind Studio in your browser (runs locally; data never leave the computer).
if [ -x "$HOME/.clockbind-env/bin/clockbind" ]; then
  "$HOME/.clockbind-env/bin/clockbind" studio open
else
  echo "ClockBind is not installed yet. Double-click Install_ClockBind_on_Mac.command first."; read -n 1
fi
