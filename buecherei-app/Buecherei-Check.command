#!/bin/bash
# Doppelklick-Starter fuer den Buecherei-Check (macOS Finder).
#
# Beim ersten Start wird automatisch eingerichtet: virtuelle Umgebung (venv),
# Python-Pakete und der Chromium-Browser fuer Playwright. Das dauert einmalig
# ein paar Minuten. Danach: Check laufen lassen, uebersicht.txt oeffnen.
#
# Zusaetzliche Argumente werden durchgereicht, z.B. im Terminal:
#   ./Buecherei-Check.command --debug --dry-run

set -uo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR" || exit 1

pause_and_exit() {
  echo
  read -r -n 1 -s -p "Taste druecken zum Schliessen ..."
  echo
  exit "$1"
}

echo "=== Buecherei-Check ($(date '+%d.%m.%Y %H:%M')) ==="
echo

# --- Python pruefen (>= 3.9) ------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  echo "FEHLER: python3 nicht gefunden."
  echo "macOS fragt evtl. nach den 'Command Line Developer Tools' -- installieren und erneut starten."
  pause_and_exit 1
fi
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
  echo "FEHLER: Python 3.9 oder neuer noetig, gefunden: $(python3 --version 2>&1)"
  pause_and_exit 1
fi

# --- Zugangsdaten pruefen ---------------------------------------------------
if [ ! -f "../library_accounts.yaml" ]; then
  echo "FEHLER: ../library_accounts.yaml fehlt."
  echo "Erwartet in: $(cd .. && pwd)/library_accounts.yaml"
  pause_and_exit 1
fi

# --- Einmalige Einrichtung --------------------------------------------------
# Marker enthaelt den Inhalt von requirements.txt: aendert sich die Datei,
# wird neu installiert.
MARKER="venv/.installed"
if [ ! -x "venv/bin/python" ] || ! cmp -s requirements.txt "$MARKER"; then
  echo "Ersteinrichtung (einmalig, dauert ein paar Minuten) ..."
  python3 -m venv venv || { echo "FEHLER: venv konnte nicht angelegt werden."; pause_and_exit 1; }
  venv/bin/python -m pip install --quiet --upgrade pip
  venv/bin/python -m pip install --quiet -r requirements.txt \
    || { echo "FEHLER: pip install fehlgeschlagen."; pause_and_exit 1; }
  venv/bin/python -m playwright install chromium \
    || { echo "FEHLER: Chromium-Installation fehlgeschlagen."; pause_and_exit 1; }
  cp requirements.txt "$MARKER"
  echo "Einrichtung fertig."
  echo
fi

# --- Check ausfuehren -------------------------------------------------------
mkdir -p logs
LOG="logs/$(date +%Y-%m).log"
echo "=== Lauf gestartet (manuell): $(date) ===" >> "$LOG"
venv/bin/python buecherei_check.py "$@" 2>&1 | tee -a "$LOG"
STATUS=${PIPESTATUS[0]}
echo "=== Lauf beendet: $(date), Exit-Code $STATUS ===" >> "$LOG"

if [ "$STATUS" -ne 0 ]; then
  echo
  echo "FEHLER: Skript mit Exit-Code $STATUS beendet. Details in $DIR/$LOG"
  pause_and_exit "$STATUS"
fi

if [ -f uebersicht.txt ] && command -v open >/dev/null 2>&1; then
  open uebersicht.txt
fi

pause_and_exit 0
