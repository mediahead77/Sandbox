# Buecherei-Check (eigenstaendiges Skript)

Laeuft komplett ohne Claude/Cowork -- ein Python-Skript, das du selbst auf
deinem Mac startest (manuell oder automatisch per launchd). Das ist der
Grund, warum es Passwoerter eintragen darf, wo der Cowork-Agent es nicht
darf: die Regel betrifft den Agenten, nicht Code, den du selbst ausfuehrst.

**Wichtig, bitte zuerst lesen:** Zwei Bugs wurden nach dem ersten echten
Testlauf gefunden und gefixt (2026-08-09):

1. Stuttgart/aDISWeb schien 5 Laeufe lang "down" (weisse Seite) -- war es
   nicht. Die alte URL in `library_accounts.yaml` fuehrte auf eine Seite mit
   kaputtem Weiterleitungslink. Die URL ist jetzt korrigiert, und das
   Login-Formular (Felder "Ausweisnummer"/"Passwort") ist read-only
   verifiziert. UNVERIFIZIERT bleibt: die Tabelle der Ausleihen nach dem
   Login -- das kann ich nicht sehen, ohne selbst einzuloggen. Rechne beim
   ersten echten Lauf noch mit einer Nachbesserungsrunde hier.
2. Koha/Korntal-Muenchingen warf einen "strict mode violation"-Fehler, weil
   die Seite zwei Felder mit demselben Label hat (ein sichtbares Hauptfeld
   und ein verstecktes Duplikat im Navigations-Menue). Jetzt per eindeutiger
   ID angesprochen, sollte zuverlaessig funktionieren.

Nach dem naechsten Lauf: pruef den Report trotzdem kritisch, bevor du ihm
vertraust -- v.a. ob bei Stuttgart tatsaechlich Ausleihen auftauchen.

## 0. Schnellstart per Doppelklick

`Buecherei-Check.command` im Finder doppelklicken. Beim ersten Start richtet
es venv, Pakete und Chromium selbst ein (einmalig, ein paar Minuten), danach
laeuft der Check und `uebersicht.txt` oeffnet sich. Abschnitt 1 ist damit
nur noch fuer manuelles Einrichten noetig.

Falls macOS den Start blockiert ("kann nicht geoeffnet werden"): einmal
Rechtsklick -> "Oeffnen", oder im Terminal:

```bash
chmod +x Buecherei-Check.command
xattr -d com.apple.quarantine Buecherei-Check.command
```

## 1. Einmalig einrichten

**Achtung Terminal-Falle:** Der Ordnername enthaelt ein "!" (in "!_Claude").
In zsh/bash loest "!" in DOPPELTEN Anfuehrungszeichen eine History-Expansion
aus ("event not found"). Deshalb unten EINFACHE Anfuehrungszeichen ('...')
verwenden, nicht doppelte -- oder `cd /Users/timwittig/Documents/Tim/` tippen
und dann TAB druecken, die Shell vervollstaendigt und escaped korrekt.

**Python-Version:** Das Skript laeuft ab Python 3.9 (auch mit dem
macOS-System-Python). Pruefen mit `python3 --version`.

```bash
cd '/Users/timwittig/Documents/Tim/!_Claude/Scheduled/regular-check/buecherei-app'

# Virtuelle Umgebung (empfohlen, haelt Abhaengigkeiten sauber getrennt)
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

## 2. Testen

Erst sichtbar testen, ohne die echte Uebersicht zu ueberschreiben:

```bash
source venv/bin/activate
python3 buecherei_check.py --debug --dry-run
```

`--debug` zeigt den Browser sichtbar und speichert Screenshots in
`debug_screenshots/` -- besonders wichtig fuer Stuttgart, um zu sehen, ob
die generischen Login-Selektoren tatsaechlich das richtige Feld treffen.
`--dry-run` schreibt nichts, druckt den Report nur in die Konsole.

Wenn das gut aussieht, einmal ohne `--dry-run` laufen lassen:

```bash
python3 buecherei_check.py --debug
```

## 3. Wo finde ich das Ergebnis?

Standardmaessig (kein Flag noetig): `uebersicht.txt` in diesem Ordner wird
bei jedem Lauf ueberschrieben und zeigt immer nur den aktuellsten Stand --
kein E-Mail-Postfach, keine Verwaltung, einfach die Datei aufmachen, wenn
du wissen willst, wo ihr steht.

Falls du es dir doch per E-Mail schicken lassen willst: `--email` Flag
anhaengen. Dafuer braucht es einmalig ein Gmail-App-Passwort:

1. Auf https://myaccount.google.com/security die 2-Faktor-Authentifizierung
   aktivieren (falls noch nicht aktiv).
2. Dort zu "App-Passwoerter" (oder direkt https://myaccount.google.com/apppasswords).
3. Neues App-Passwort erstellen (Name z.B. "Buecherei-Check"), den
   16-stelligen Code kopieren.
4. `email_config.example.yaml` zu `email_config.yaml` kopieren, ausfuellen.

`email_config.yaml` bitte NICHT teilen oder irgendwo hochladen -- gleiche
Sensibilitaet wie `library_accounts.yaml`. Komplett optional -- ohne diese
Datei funktioniert alles andere trotzdem.

## 4. Automatisch laufen lassen (macOS launchd)

```bash
cp com.tim.buechereicheck.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.tim.buechereicheck.plist
```

Laeuft danach jeden Sonntag um 09:00 Uhr. Verpasste Termine:

- Mac war im **Ruhezustand** (Deckel zu): launchd holt den Lauf beim
  naechsten Aufwachen nach. Mehrere verpasste Termine werden zu einem Lauf
  zusammengefasst.
- Mac war **ausgeschaltet**: Der Lauf entfaellt ersatzlos, auch nach dem
  Hochfahren wird nichts nachgeholt. Falls das oft vorkommt, die Uhrzeit auf
  einen Moment legen, an dem der Mac sicher an ist, oder per
  `sudo pmset repeat wakeorpoweron U 08:55:00` einen Start/Aufwecken kurz
  vorher planen.

Logs liegen in `buecherei-app/logs/` -- ein Log pro Monat plus die
launchd-eigenen Out-/Error-Logs.

Zum Deaktivieren:

```bash
launchctl unload ~/Library/LaunchAgents/com.tim.buechereicheck.plist
```

## 5. Wenn sich eine Portal-Seite aendert und das Skript bricht

Das Skript ist bewusst so gebaut, dass es bei einem Strukturbruch eine
FEHLER-Zeile im Report meldet statt stillschweigend "alles ok" zu sagen
(siehe `AccountResult.error` in `buecherei_check.py`). Wenn das passiert:
mit `--debug` laufen lassen, den Screenshot in `debug_screenshots/`
anschauen, und mir (Claude) Bescheid geben -- ich kann die betroffene
Funktion (`check_koha` oder `check_stuttgart`) reparieren, sobald ich weiss,
wie die neue Seite aussieht.

## Dateien in diesem Ordner

- `Buecherei-Check.command` -- Doppelklick-Starter (richtet beim 1. Mal alles ein)
- `buecherei_check.py` -- das eigentliche Skript
- `uebersicht.txt` -- wird beim ersten Lauf erzeugt, danach jedes Mal
  ueberschrieben; das ist die eigentliche "Ansicht"
- `requirements.txt` -- Python-Abhaengigkeiten
- `email_config.example.yaml` -- optional, nur falls du `--email` nutzen willst
- `run.sh` -- Wrapper, den launchd aufruft (aktiviert venv, loggt)
- `com.tim.buechereicheck.plist` -- launchd-Zeitplan (Sonntag 09:00)
- `../library_accounts.yaml` -- deine bestehende Zugangsdaten-Datei (liegt
  eine Ebene hoeher, wird wiederverwendet, nichts Neues anzulegen)
