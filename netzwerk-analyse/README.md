# Netzwerk-Stabilitäts-Analyzer

Ein Kommandozeilen-Werkzeug (reine Python-Standardbibliothek, keine
Installation nötig) für genau dein Setup:

```
Internet -- Kabelrouter -- WLAN/Ethernet-Router -- Powerline -- Endgeräte
```

Die Idee: Wenn du gleichzeitig zum **Kabelrouter**, zum **WLAN-Router** und zu
**externen Servern** pingst, kannst du anhand des Musters erkennen, in
welchem Segment die Störung sitzt:

| Beobachtung | Wahrscheinliche Ursache |
|---|---|
| Kabelrouter selbst schwankt schon | Anschlussleitung, Kabel/Stecker, Kabelmodem, Provider |
| Kabelrouter stabil, WLAN-Router schwankt | WLAN-Interferenz, Powerline-Störung, Kabel zwischen den Routern |
| Beide Router stabil, nur externe Ziele schwanken | Provider/DNS/Route außerhalb deines Netzes |
| Alles schwankt gleichzeitig | Gemeinsame Ursache, z.B. Stromschwankungen oder die Leitung selbst |

## Voraussetzungen

- Python 3
- Die Systembefehle `ping` und `traceroute` (Linux/Mac) bzw. `ping`/`tracert`
  (Windows) - i.d.R. vorinstalliert.
- Optional `matplotlib` (`pip install matplotlib`) für ein Latenz-Diagramm.

## 1. IP-Adressen herausfinden

- Kabelrouter: meist die Adresse, die der WLAN-Router als "Internet-Gateway"
  bzw. WAN-Adresse anzeigt (in dessen Weboberfläche unter Status/Internet).
- WLAN-Router: die eigene Gateway-Adresse deines Rechners, z.B. per
  `ip route` (Linux/Mac) oder `ipconfig` (Windows, Feld "Standardgateway").

## 2. Messung starten

Mehrere Stunden bis Tage laufen lassen, am besten auf einem Gerät, das
durchgehend läuft (z.B. Raspberry Pi, NAS, oder ein Laptop, der nicht in
den Standby geht):

```bash
python3 analyzer.py monitor \
    --target kabelrouter=192.168.0.1 \
    --target wlan_router=192.168.2.1 \
    --interval 5
```

Wichtig: Die Namen `kabelrouter` und `wlan_router` **so beibehalten** - die
automatische Diagnose erkennt diese Ziele namentlich. Externe Ziele
(`cloudflare_dns`, `google_dns`) werden automatisch mitgemessen, wenn du
`--target` nicht angibst; willst du eigene zusätzliche Ziele haben, einfach
weitere `--target name=host` anhängen.

Optional die WLAN-Signalstärke mitloggen (Linux, falls `iw` vorhanden):

```bash
--wifi-iface wlan0
```

Mit `--duration-min 60` läuft die Messung z.B. genau eine Stunde, ohne die
Option läuft sie bis `Strg+C`.

## 3. Auffälligkeiten während der Messung notieren

In einem zweiten Terminal, sobald dir eine Störung auffällt oder du testen
willst, ob ein bestimmtes Gerät die Ursache ist (Mikrowelle, Ladegerät,
zweiter Powerline-Adapter etc.):

```bash
python3 analyzer.py note "Mikrowelle eingeschaltet"
python3 analyzer.py note "Powerline-Adapter im Wohnzimmer blinkt orange"
```

Der Report gleicht Notizen automatisch mit Latenzspitzen/Verlust in einem
±30-Sekunden-Fenster ab.

## 4. Doppel-NAT prüfen

Bei dieser Router-Kette (Kabelrouter + eigener WLAN-Router) routen sehr
häufig **beide** Geräte gleichzeitig (Doppel-NAT), was Latenz und
Instabilität verursachen kann:

```bash
python3 analyzer.py traceroute --target 1.1.1.1
```

Das Tool erkennt automatisch, ob mehrere private IP-Bereiche
(`192.168.x.x`, `10.x.x.x`) hintereinander auftauchen, und schlägt vor, den
Kabelrouter in den Modem-/Bridge-Modus zu versetzen.

## 5. Auswertung

Nach der Messung (kann auch parallel zu einer laufenden Messung erfolgen,
einfach die bisherige CSV-Datei angeben):

```bash
python3 analyzer.py report --csv network_log_*.csv --notes network_notes*.txt --plot
```

Der Bericht enthält:

- Paketverlust, durchschnittliche/mediane/p95-Latenz und Jitter pro Ziel
- die Uhrzeit mit dem höchsten Paketverlust (z.B. Hinweis auf
  Nachbar-WLANs/Nutzungsspitzen am Abend)
- Abgleich mit deinen Notizen
- eine regelbasierte Diagnose in Textform mit konkreten nächsten Schritten
- optional (`--plot`) ein PNG-Diagramm der Latenz über die Zeit

## 6. Alternative: Web-Dashboard (`webui.py`)

Statt alles über SSH/Kommandozeile zu bedienen, gibt es ein kleines
Browser-Dashboard - ideal für einen dauerhaften Betrieb z.B. auf einer NAS.
Nutzt ebenfalls nur die Python-Standardbibliothek (kein Flask/Django nötig).

```bash
python3 webui.py --port 8787
```

Danach im Browser: `http://<IP-des-Geräts>:8787`

Das Dashboard bietet:

- **Start/Stopp-Button** für die Messung (startet/beendet `analyzer.py
  monitor` im Hintergrund als eigenen Prozess)
- **Konfigurationsformular** für Ziele, Intervall und CSV-Pfad, ohne eine
  Datei bearbeiten zu müssen
- **Notiz-Formular**, um Auffälligkeiten direkt im Browser festzuhalten
- **Bericht-Seite** (`/report`) mit Tabelle, Latenz-Diagramm (als SVG,
  ohne matplotlib) und der regelbasierten Diagnose

**Dauerbetrieb auf einer Synology NAS**, damit das Dashboard nach jedem
Neustart automatisch wieder verfügbar ist:
**Systemsteuerung → Aufgabenplaner → Erstellen → Ausgelöstes Skript →
Ereignis: Bootup**, und als Skript:

```bash
cd /volume1/homes/<benutzer>/<ordner> && nohup python3 webui.py --port 8787 > webui.log 2>&1 &
```

Für einen App-artigen Zugriff direkt vom DSM-Desktop aus: Rechtsklick auf den
freien DSM-Desktop → **Hinzufügen** → Verknüpfung mit der URL
`http://<NAS-IP>:8787` anlegen - erscheint dann als Icon im DSM-Hauptmenü.

**Sicherheitshinweis:** Das Dashboard hat keine Anmeldung/Authentifizierung
und ist nur für den Einsatz im eigenen, vertrauenswürdigen Heimnetz gedacht.
Port 8787 nicht per Port-Forwarding aus dem Internet erreichbar machen.

## Typische Ursachen bei dieser Topologie und Gegenmaßnahmen

- **Doppel-NAT**: Kabelrouter in Bridge-/Modem-Modus betreiben, nur der
  WLAN-Router routet.
- **Powerline-Störungen**: Adapter nie in Mehrfachsteckdosen/Verlängerungen
  stecken, sondern direkt in die Wand; nach Möglichkeit auf derselben Phase/
  Sicherungskreis wie der Router betreiben; Firmware der Adapter aktuell
  halten; per Hersteller-Software (z.B. devolo Cockpit, TP-Link tpPLC) die
  Verbindungsrate zwischen den Adaptern prüfen.
- **WLAN-Interferenz**: Kanal manuell setzen (2,4 GHz: 1/6/11, sich nicht
  überlappend), wenn möglich 5 GHz bevorzugen, DFS-Kanäle meiden, Access
  Point nicht direkt neben Powerline-Adapter/Mikrowelle/Babyphone platzieren.
- **Kabel/Hardware**: Ethernet-Kabel zwischen Kabelrouter und WLAN-Router
  testweise tauschen, andere LAN-Ports probieren.
- **Firmware**: Bei allen drei Geräten (Kabelrouter, WLAN-Router,
  Powerline-Adapter) auf aktuelle Firmware prüfen - viele Stabilitätsbugs
  werden dort behoben.

## Dateien

- `analyzer.py` - das CLI-Tool (Subcommands: `monitor`, `note`, `traceroute`, `report`)
- `webui.py` - optionales Browser-Dashboard rund um `analyzer.py` (siehe Abschnitt 6)
- CSV-Logs und Notiz-Dateien werden im aktuellen Verzeichnis erzeugt, sofern
  kein Pfad angegeben wird.
