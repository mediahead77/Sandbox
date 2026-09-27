# Cowork-Aufgabe: Wochenendplan in Apple Kalender und Erinnerungen

Ergänzt die Cloud-Routine „Wochenendplan Stuttgart“ (Donnerstag ca. 18 Uhr, siehe `ROUTINE_PROMPT.md`).
Die Cowork-Aufgabe läuft auf dem Mac und trägt den fertigen Plan in Apple Kalender und Erinnerungen ein.

## Einmalige Einrichtung auf dem Mac

1. **iCloud-Kalender anlegen**: In der Kalender-App einen neuen iCloud-Kalender „Wochenendplan“ erstellen.
   Die Aufgabe schreibt nur in diesen Kalender und kann ihn gefahrlos aufräumen.
2. **Erinnerungsliste anlegen**: In der Erinnerungen-App eine iCloud-Liste „Wochenendplan“ erstellen.
3. **Kalender/Erinnerungen-Zugriff für Cowork**: Einen MCP-Server für Apple Kalender + Erinnerungen in der
   Claude-Desktop-App hinzufügen (Einstellungen → Connectors/Erweiterungen). Das sind Projekte von Dritten,
   z. B. auf GitHub; vor der Installation Quelle prüfen. Beim ersten Lauf fragt macOS nach Zugriff auf
   Kalender und Erinnerungen → erlauben.
4. **Gmail** in Cowork aktivieren (derselbe Gmail-Connector wie in claude.ai).
5. **Mac wach halten**: Donnerstag 18:30 muss der Mac an und die Claude-App offen sein
   (Systemeinstellungen → Energie: Ruhezustand verhindern, oder Mac zu der Zeit ohnehin an).
6. **Aufgabe anlegen**: In Cowork eine geplante Aufgabe erstellen, **jeden Donnerstag 18:30 Uhr**,
   mit dem Auftragstext unten.

## Auftragstext (in Cowork einfügen)

```
Trage den aktuellen Wochenendplan in Apple Kalender und Erinnerungen ein.

1. Suche in Gmail die neueste E-Mail mit Betreff „Wochenendplan“ von heute
   (Suche: subject:Wochenendplan newer_than:1d). Keine gefunden → abbrechen und melden:
   „Kein Wochenendplan gefunden – lief die Cloud-Routine?“
2. Lies aus der E-Mail den Abschnitt „TERMINE (maschinenlesbar)“. Jede Zeile hat das Format
   TT.MM.JJJJ HH:MM-HH:MM | Titel | Ort | Typ
   Typ ist „termin“ oder „aufgabe“. Falls der Abschnitt fehlt: stattdessen den .ics-Anhang auswerten.
3. Kalender „Wochenendplan“: Zuerst alle vorhandenen Einträge dieses Kalenders von Freitag 00:00
   bis Sonntag 23:59 des betreffenden Wochenendes löschen (damit ein erneuter Lauf nichts doppelt einträgt).
   Dann für JEDE Zeile (termin und aufgabe) einen Termin mit Start, Ende, Titel und Ort anlegen.
   Notiz: „Automatisch aus Wochenendplan“ plus Link auf den Plan aus der E-Mail.
   Nur in den Kalender „Wochenendplan“ schreiben, niemals in andere Kalender.
4. Erinnerungsliste „Wochenendplan“: Offene Erinnerungen dieser Liste mit Fälligkeit im selben Wochenende
   löschen. Dann für jede Zeile mit Typ „aufgabe“ (z. B. Einkaufen, Putzen, Hemden) eine Erinnerung mit
   Fälligkeit = Startzeit anlegen, Hinweis 15 Minuten vorher.
5. Kurze Rückmeldung: Anzahl Termine, Anzahl Erinnerungen, Reit-Wochenende ja/nein.

Automatischer Lauf: keine Rückfragen, keine E-Mails senden, nichts außerhalb von Kalender und Liste
„Wochenendplan“ ändern.
