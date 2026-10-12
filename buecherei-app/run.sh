#!/bin/bash
# Wrapper, aufgerufen von launchd (siehe com.tim.buechereicheck.plist).
# Sorgt dafuer, dass das Skript im richtigen Ordner mit der richtigen
# virtuellen Umgebung laeuft und alles geloggt wird.

set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

mkdir -p logs

if [ -d "venv" ]; then
  source venv/bin/activate
fi

{
  echo "=== Lauf gestartet: $(date) ==="
  python3 buecherei_check.py
  echo "=== Lauf beendet: $(date) ==="
} >> "logs/$(date +%Y-%m).log" 2>&1
