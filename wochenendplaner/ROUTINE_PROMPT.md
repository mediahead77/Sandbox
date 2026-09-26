Erstelle den Familien-Wochenendplan für das kommende Wochenende (Freitagabend, Samstag, Sonntag). Nutze zuerst ToolSearch, um WebSearch, WebFetch und die Gmail-Tools zu laden.

## Familie
- Wohnort: Stuttgart. Radius für Aktivitäten: max. 50 km.
- 2 Erwachsene (Tim und seine Frau), 2 Kinder: Konrad und Greta (Alter 9 und 12; die 9-jährige Tochter reitet).

## Feste Termine (zuerst einplanen, Freizeit drumherum)
- **Freitag**: Planung erst ab 18:00 Uhr. Seine Frau ist freitags 18–20 Uhr beim Sport (inkl. Weg).
  Freitag 18–20 Uhr also nur Tim + Kinder; Aktivitäten für die ganze Familie frühestens ab 20 Uhr.
- **Reiten (Tochter, 9 Jahre)**: jeden 2. Samstag 13–15 Uhr auf dem Martinshof in Schöckingen (Ditzingen).
  Im Zeitraster 12:30–15:30 inkl. Hin- und Rückfahrt blocken (Fahrzeit ab Stuttgart vorab per Suche prüfen).
  Referenztermin: Samstag, 03.10.2026. Reit-Samstag, wenn (Datum − 03.10.2026) in Tagen durch 14 teilbar ist
  (also 03.10., 17.10., 31.10., 14.11., …). Im Plan ausdrücklich angeben, ob dieses Wochenende Reit-Wochenende ist.
  An Reit-Samstagen: Samstagvormittag bis ca. 12 Uhr frei für Familie/Haushalt. Für die anderen drei (2 Erwachsene + Kind 12)
  während 13–15 Uhr eine Aktivität in der Nähe von Schöckingen/Ditzingen/Leonberg vorschlagen (max. 15 Min. vom Hof),
  damit niemand zweimal fahren muss. Feiertag (z. B. 03.10.): Hinweis, dass Reitstunde evtl. entfällt.
- **Schulthemen**: Sonntag 9:30–12:00 Uhr (2,5 h) für beide Kinder. Nur verschieben, wenn Sonntagvormittag ein
  besonders passendes Ereignis liegt; dann gleich lange auf Samstag legen und begründen.
- **Abendübungen**: Freitag, Samstag und Sonntag nach dem Abendessen je ca. 15 Min. (Reflexintegration, Konrad und Greta).
  Link im Plan: https://claude.ai/artifact/CbYsJEn5em7dceWVBTzhH3 — Abendaktivitäten so legen, dass die Übungen nicht ausfallen.

## Haushalt (flexibel einplanen)
- **Einkaufen**: ca. 1,5 h. Bevorzugt Freitag 18–19:30 (Tim + Kinder, Öffnungszeiten prüfen) oder Samstagvormittag. Sonntags zu.
- **Putzen**: ca. 2 h. Bevorzugt in ein Zeitfenster mit schlechtem Wetter, sonst Samstagvormittag.
- **Hemden waschen/bügeln (Tim)**: 1,5–2 h, nur an Reit-Wochenenden (gleiche 14-Tage-Regel wie Reiten).
  Bevorzugt Sonntag 19:30–21:30 nach den Abendübungen. Hinweis im Plan: Waschmaschine schon tagsüber anstellen
  (z. B. während des Schul-Slots), damit abends nur noch gebügelt wird.
- **Feiertage**: Prüfen, ob Fr, Sa oder So ein gesetzlicher Feiertag in Baden-Württemberg ist (z. B. 03.10.).
  Dann haben Geschäfte zu: Einkauf auf einen offenen Termin davor legen und im Plan darauf hinweisen.
- Tagesplan als Zeitraster darstellen (Fr ab 18 Uhr, Sa und So ganztägig), damit Überschneidungen sichtbar sind.

## Recherche (WebSearch/WebFetch, nur aktuelle Quellen)
1. **Wetter** für Stuttgart, Fr–So: Temperatur, Regenwahrscheinlichkeit, Wind.
   Quelle bevorzugt Open-Meteo:
   https://api.open-meteo.com/v1/forecast?latitude=48.78&longitude=9.18&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max&timezone=Europe%2FBerlin
2. **Veranstaltungen** an genau diesem Wochenende: Konzerte, Museen (inkl. Sonderausstellungen, Familienführungen), Theater.
   Getrennt markieren: für Kinder 9+12 / für die ganze Familie / nur für Erwachsene.
3. **Wanderung**: eine Hauptempfehlung und eine Alternative, jeweils 3–7 km, kindertauglich, mit Startpunkt, Höhenmetern und Anfahrt (Auto und, falls möglich, VVS).
4. **Plan B bei Regen**: pro Tag eine Indoor-Alternative.
5. **Preise**: Eintritt für 2 Erwachsene + 2 Kinder; kostenlose Angebote markieren.
6. **Einkehr**: familienfreundliche Einkehr nahe der Wanderung bzw. Veranstaltung.

## Regeln
- Nur Veranstaltungen, deren Datum für dieses Wochenende auf einer Quelle bestätigt ist. Jede Angabe mit Quell-Link.
- Nichts erfinden. Unbekannte Preise oder Zeiten als „nicht gefunden“ kennzeichnen.
- Jede Empfehlung mit Label „sicher“, „wahrscheinlich“ oder „Vermutung“ (Verlässlichkeit der Angabe).
- Den Plan so bauen, dass er zum Wetter passt (Wanderung an den trockensten Tag).

## Ausgabe
1. **Webseite aktualisieren**: Lade den Skill `artifact-design` und veröffentliche den Plan per Artifact-Tool mit
   `url: https://claude.ai/artifact/H8Uh9FJ3x6K6ik2JEqAE2J` (erst mit `action: read` lesen, dann auf derselben URL neu veröffentlichen,
   Titel „Wochenendplan Stuttgart“ beibehalten, keine neue Artifact-URL anlegen).
   Aufbau: Wetter-Übersicht, Tagesplan Fr/Sa/So als Zeitraster (inkl. Sport, Reiten, Schule, Abendübungen, Einkaufen, Putzen, Hemden) mit Plan B,
   Veranstaltungsliste, Wanderung, Kosten-Übersicht, Einkehr, Quellen.
2. **Kalenderdatei (Apple Kalender)**: Erzeuge eine iCalendar-Datei `wochenendplan-<JJJJ-MM-TT Sa>.ics` (RFC 5545) mit allen
   geplanten Terminen des Wochenendes (feste Termine, Haushalt, Hauptaktivitäten; Plan-B-Alternativen nicht).
   - `VCALENDAR` mit `VERSION:2.0`, `PRODID:-//Wochenendplan Stuttgart//DE`, `METHOD:PUBLISH`, `X-WR-TIMEZONE:Europe/Berlin`
     und einem `VTIMEZONE`-Block für Europe/Berlin; Zeiten als `DTSTART;TZID=Europe/Berlin:...`.
   - Pro Termin: `UID:wp-<JJJJMMTT>-<HHMM>-<kurzname>@wochenendplan` (stabil, damit ein erneuter Import aktualisiert statt dupliziert),
     `DTSTAMP` in UTC, `SUMMARY`, `LOCATION` (Adresse, falls bekannt), `DESCRIPTION` (Kurzinfo + Quell-Link).
   - Zeilenenden CRLF, Sonderzeichen (Komma, Semikolon) escapen, lange Zeilen falten.
3. **E-Mail** per Gmail (send_message) an {{EMAIL}}, Betreff „Wochenendplan <Datum Sa>–<Datum So>“:
   Kurzfassung (Wetter in einem Satz, Reit-Wochenende ja/nein, je Tag 2–3 Stichpunkte inkl. Einkauf/Putzen/Schule/Hemden, Top-Veranstaltung, Wanderung)
   plus Link https://claude.ai/artifact/H8Uh9FJ3x6K6ik2JEqAE2J.
   Die .ics-Datei als Anhang (base64, mimeType `text/calendar`) mitschicken und im Text erklären:
   „Auf dem iPhone in Apple Mail den Anhang antippen → Alle hinzufügen.“
   Falls Gmail nicht verfügbar ist: nur die Webseite aktualisieren und das im Abschlusstext sagen.

Das ist ein automatischer, unbeaufsichtigter Lauf: keine Rückfragen stellen, mit sinnvollen Annahmen direkt liefern. Keine Commits, keine Pull Requests.
