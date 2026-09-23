Erstelle den Familien-Wochenendplan für das kommende Wochenende (Freitagabend, Samstag, Sonntag).

## Familie
- Wohnort: Stuttgart. Radius für Aktivitäten: max. 50 km.
- 2 Erwachsene, 2 Kinder (9 und 12 Jahre).

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
1. **Webseite aktualisieren**: Lade den Skill `artifact-design` und veröffentliche den Plan per Artifact-Tool
   mit `url: https://claude.ai/artifact/H8Uh9FJ3x6K6ik2JEqAE2J` (erst mit `action: read` lesen, dann auf derselben URL neu veröffentlichen, Titel „Wochenendplan Stuttgart“ beibehalten).
   Aufbau: Wetter-Übersicht, Tagesplan Fr/Sa/So mit Plan B, Veranstaltungsliste, Wanderung, Kosten-Übersicht, Einkehr, Quellen.
2. **E-Mail** per Gmail an die eigene Adresse des verbundenen Gmail-Kontos, Betreff „Wochenendplan <Datum Sa>–<Datum So>“:
   Kurzfassung (Wetter in einem Satz, je Tag 2–3 Stichpunkte, Top-Veranstaltung, Wanderung) plus Link auf die Webseite.
