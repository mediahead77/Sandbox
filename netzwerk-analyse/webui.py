#!/usr/bin/env python3
"""
Netzwerk-Analyzer Web-Dashboard
================================

Kleine Weboberfläche für analyzer.py: Messung starten/stoppen, Notizen
hinzufügen und den Analyse-Bericht ansehen - alles im Browser, ohne SSH.
Nutzt nur die Python-Standardbibliothek.

Start:

    python3 webui.py --port 8787

Danach im Browser: http://<NAS-IP>:8787

Für Dauerbetrieb auf einer Synology NAS: im Aufgabenplaner ein "Ausgelöstes
Skript" mit Ereignis "Bootup" anlegen, das obigen Befehl im Hintergrund
startet (siehe README.md).

Sicherheitshinweis: Der Server hat keine Benutzer-Authentifizierung und ist
für den Einsatz im eigenen, vertrauenswürdigen Heimnetz gedacht. Port 8787
nicht ins Internet weiterleiten (Port-Forwarding vermeiden).
"""

import argparse
import html
import json
import os
import signal
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import analyzer

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "webui_config.json"
PID_PATH = BASE_DIR / "monitor.pid"
LOG_PATH = BASE_DIR / "monitor.log"

DEFAULT_CONFIG = {
    "targets": [
        ["kabelrouter", "192.168.0.1"],
        ["wlan_router", "192.168.50.1"],
        ["cloudflare_dns", "1.1.1.1"],
        ["google_dns", "8.8.8.8"],
    ],
    "interval": 5,
    "csv_path": str(BASE_DIR / "network_log.csv"),
    "notes_path": str(BASE_DIR / "network_notes.txt"),
}


# --------------------------------------------------------------------------
# Konfiguration & Prozess-Steuerung
# --------------------------------------------------------------------------

def load_config():
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            cfg.update(json.loads(CONFIG_PATH.read_text()))
        except json.JSONDecodeError:
            pass
    return cfg


def save_config(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))


def get_running_pid():
    if not PID_PATH.exists():
        return None
    try:
        pid = int(PID_PATH.read_text().strip())
    except ValueError:
        return None
    try:
        os.kill(pid, 0)
    except OSError:
        return None
    return pid


def start_monitor(cfg):
    if get_running_pid():
        return
    args = [
        sys.executable, str(BASE_DIR / "analyzer.py"), "monitor",
        "--interval", str(cfg["interval"]),
        "--out", cfg["csv_path"],
    ]
    for name, host in cfg["targets"]:
        args += ["--target", f"{name}={host}"]

    with open(LOG_PATH, "a") as log_f:
        proc = subprocess.Popen(
            args, stdout=log_f, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, start_new_session=True, cwd=str(BASE_DIR),
        )
    PID_PATH.write_text(str(proc.pid))


def stop_monitor():
    pid = get_running_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    if PID_PATH.exists():
        PID_PATH.unlink()


def tail_file(path, n=25):
    if not Path(path).exists():
        return ""
    with open(path, "r", errors="replace") as f:
        return "".join(f.readlines()[-n:])


# --------------------------------------------------------------------------
# SVG-Diagramm (ohne externe Abhängigkeiten wie matplotlib)
# --------------------------------------------------------------------------

CHART_COLORS = ["#2563eb", "#dc2626", "#16a34a", "#ca8a04", "#9333ea", "#0891b2"]


def render_svg_chart(by_target, width=900, height=320, max_points=500):
    series = {}
    all_points = []
    for target, trows in by_target.items():
        pts = []
        for r in trows[-max_points:]:
            if not r["rtt_ms"]:
                continue
            try:
                ts = datetime.strptime(r["timestamp"], analyzer.TIMESTAMP_FMT)
                pts.append((ts, float(r["rtt_ms"])))
            except ValueError:
                continue
        if pts:
            series[target] = pts
            all_points += pts

    if not all_points:
        return "<p>Keine Latenzdaten zum Zeichnen vorhanden.</p>"

    min_t = min(p[0] for p in all_points)
    max_t = max(p[0] for p in all_points)
    max_y = max(p[1] for p in all_points) * 1.1 or 1.0
    t_span = (max_t - min_t).total_seconds() or 1.0

    pad_l, pad_r, pad_t, pad_b = 55, 10, 10, 10
    plot_w, plot_h = width - pad_l - pad_r, height - pad_t - pad_b

    def x_of(ts):
        return pad_l + (ts - min_t).total_seconds() / t_span * plot_w

    def y_of(v):
        return pad_t + plot_h - (v / max_y * plot_h)

    parts = [
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;height:auto;background:#0f172a;border-radius:8px;font-family:sans-serif">'
    ]

    for frac in (0, 0.25, 0.5, 0.75, 1.0):
        y = pad_t + plot_h - frac * plot_h
        parts.append(
            f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width - pad_r}" y2="{y:.1f}" '
            f'stroke="#334155" stroke-width="1"/>'
        )
        parts.append(f'<text x="4" y="{y + 4:.1f}" fill="#94a3b8" font-size="11">{frac * max_y:.0f}ms</text>')

    for i, (target, pts) in enumerate(series.items()):
        color = CHART_COLORS[i % len(CHART_COLORS)]
        path = " ".join(f"{'M' if j == 0 else 'L'}{x_of(ts):.1f},{y_of(v):.1f}" for j, (ts, v) in enumerate(pts))
        parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.5"/>')
        parts.append(
            f'<text x="{pad_l + 8}" y="{pad_t + 14 + i * 16}" fill="{color}" font-size="12">{html.escape(target)}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)


# --------------------------------------------------------------------------
# HTML-Seiten
# --------------------------------------------------------------------------

PAGE_STYLE = """
<style>
  body { font-family: -apple-system, "Segoe UI", Roboto, sans-serif; background:#f1f5f9; color:#0f172a; margin:0; padding:24px; }
  .card { background:white; border-radius:10px; padding:20px 24px; margin-bottom:20px; box-shadow:0 1px 3px rgba(0,0,0,.1); max-width:960px; }
  h1 { font-size:1.4rem; margin-top:0; }
  h2 { font-size:1.1rem; }
  table { border-collapse:collapse; width:100%; }
  td, th { text-align:left; padding:4px 10px; border-bottom:1px solid #e2e8f0; font-size:.92rem; }
  .status-on { color:#16a34a; font-weight:600; }
  .status-off { color:#dc2626; font-weight:600; }
  button, input[type=submit] { background:#2563eb; color:white; border:none; border-radius:6px; padding:8px 16px; cursor:pointer; font-size:.92rem; }
  button.stop { background:#dc2626; }
  input[type=text], textarea, input[type=number] { width:100%; box-sizing:border-box; padding:6px 8px; border:1px solid #cbd5e1; border-radius:6px; font-size:.92rem; }
  label { display:block; margin:10px 0 4px; font-size:.85rem; color:#475569; }
  pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; font-size:.8rem; max-height:260px; }
  a { color:#2563eb; }
  .diag li { margin-bottom:10px; }
</style>
"""


def page_shell(title, body):
    return f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>{PAGE_STYLE}</head>
<body>{body}</body></html>"""


def render_dashboard(cfg):
    pid = get_running_pid()
    status_html = (
        f'<span class="status-on">läuft (PID {pid})</span>' if pid
        else '<span class="status-off">gestoppt</span>'
    )
    action_btn = (
        '<form method="post" action="/stop"><button class="stop" type="submit">Messung stoppen</button></form>'
        if pid else
        '<form method="post" action="/start"><button type="submit">Messung starten</button></form>'
    )

    targets_text = "\n".join(f"{n}={h}" for n, h in cfg["targets"])

    config_form = f"""
    <form method="post" action="/config">
      <label>Ziele (ein "name=ip" pro Zeile - "kabelrouter" und "wlan_router" sind für die Diagnose reserviert)</label>
      <textarea name="targets" rows="5">{html.escape(targets_text)}</textarea>
      <label>Intervall (Sekunden)</label>
      <input type="number" step="0.5" min="1" name="interval" value="{cfg['interval']}">
      <label>CSV-Datei</label>
      <input type="text" name="csv_path" value="{html.escape(cfg['csv_path'])}">
      <br><br>
      <input type="submit" value="Konfiguration speichern (wirkt beim nächsten Start)">
    </form>
    """

    note_form = """
    <form method="post" action="/note">
      <label>Notiz (z.B. "Mikrowelle an")</label>
      <input type="text" name="text" required>
      <br><br>
      <input type="submit" value="Notiz speichern">
    </form>
    """

    log_tail = html.escape(tail_file(LOG_PATH, 25))

    body = f"""
    <div class="card">
      <h1>Netzwerk-Stabilitäts-Analyzer</h1>
      <p>Status: {status_html}</p>
      {action_btn}
      <p style="margin-top:16px"><a href="/report">&rarr; Analyse-Bericht anzeigen</a></p>
    </div>
    <div class="card">
      <h2>Konfiguration</h2>
      {config_form}
    </div>
    <div class="card">
      <h2>Notiz hinzufügen</h2>
      {note_form}
    </div>
    <div class="card">
      <h2>Letzte Log-Zeilen</h2>
      <pre>{log_tail or "(noch keine Log-Datei)"}</pre>
    </div>
    """
    return page_shell("Netzwerk-Analyzer", body)


def render_report(cfg):
    rows = analyzer.load_rows([cfg["csv_path"]])
    if not rows:
        return page_shell(
            "Bericht",
            '<div class="card"><p>Noch keine Messdaten vorhanden. <a href="/">Zurück</a></p></div>',
        )

    notes = analyzer.load_notes([cfg["notes_path"]])
    by_target = defaultdict(list)
    for r in rows:
        by_target[r["target"]].append(r)

    stats = analyzer.compute_stats_by_target(by_target)

    rows_html = ""
    for target, s in stats.items():
        if s["avg"] is not None:
            latenz = f"{s['avg']:.1f} / {s['median']:.1f} / {s['p95']:.1f} / {s['max']:.1f} ms"
            jitter = f"{s['jitter']:.1f} ms"
        else:
            latenz = jitter = "-"
        rows_html += (
            f"<tr><td>{html.escape(target)}</td><td>{html.escape(s['host'])}</td>"
            f"<td>{s['total']}</td><td>{s['loss_pct']:.2f}%</td>"
            f"<td>{latenz}</td><td>{jitter}</td></tr>"
        )

    notes_html = ""
    if notes:
        for item in analyzer.correlate_notes(by_target, notes):
            if item["hits"]:
                hit_str = "; ".join(f"{t}: {l}/{n} Verluste" for t, l, n in item["hits"])
            else:
                hit_str = "keine auffälligen Verluste"
            notes_html += (
                f"<tr><td>{item['ts'].strftime(analyzer.TIMESTAMP_FMT)}</td>"
                f"<td>{html.escape(item['text'])}</td><td>{html.escape(hit_str)}</td></tr>"
            )

    diagnosis_html = "".join(f"<li>{html.escape(m)}</li>" for m in analyzer.build_diagnosis(stats))
    chart = render_svg_chart(by_target)

    notes_card = ""
    if notes:
        notes_card = (
            "<div class='card'><h2>Notizen-Abgleich (&plusmn;30s)</h2>"
            "<table><tr><th>Zeit</th><th>Notiz</th><th>Ergebnis</th></tr>"
            f"{notes_html}</table></div>"
        )

    body = f"""
    <div class="card">
      <h1>Analyse-Bericht</h1>
      <p><a href="/">&larr; Zurück zum Dashboard</a></p>
      <h2>Latenz über Zeit</h2>
      {chart}
    </div>
    <div class="card">
      <h2>Messwerte je Ziel</h2>
      <table>
        <tr><th>Ziel</th><th>Host</th><th>Messungen</th><th>Verlust</th>
            <th>Latenz avg/med/p95/max</th><th>Jitter</th></tr>
        {rows_html}
      </table>
    </div>
    {notes_card}
    <div class="card diag">
      <h2>Diagnose</h2>
      <ul>{diagnosis_html}</ul>
    </div>
    """
    return page_shell("Analyse-Bericht", body)


# --------------------------------------------------------------------------
# HTTP-Server
# --------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send_html(self, html_str, code=200):
        data = html_str.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, location):
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        cfg = load_config()
        if path == "/":
            self._send_html(render_dashboard(cfg))
        elif path == "/report":
            self._send_html(render_report(cfg))
        else:
            self._send_html(page_shell("Nicht gefunden", "<div class='card'>404</div>"), code=404)

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        data = parse_qs(body)
        cfg = load_config()

        if path == "/start":
            start_monitor(cfg)
        elif path == "/stop":
            stop_monitor()
        elif path == "/note":
            text = data.get("text", [""])[0].strip()
            if text:
                with open(cfg["notes_path"], "a") as f:
                    f.write(f"{datetime.now().strftime(analyzer.TIMESTAMP_FMT)}\t{text}\n")
        elif path == "/config":
            targets = []
            for line in data.get("targets", [""])[0].splitlines():
                line = line.strip()
                if "=" in line:
                    name, host = line.split("=", 1)
                    if name.strip() and host.strip():
                        targets.append([name.strip(), host.strip()])
            if targets:
                cfg["targets"] = targets
            try:
                cfg["interval"] = float(data.get("interval", [cfg["interval"]])[0])
            except ValueError:
                pass
            csv_path = data.get("csv_path", [cfg["csv_path"]])[0].strip()
            if csv_path:
                cfg["csv_path"] = csv_path
            save_config(cfg)
        else:
            self._send_html(page_shell("Nicht gefunden", "<div class='card'>404</div>"), code=404)
            return

        self._redirect("/")


def main():
    parser = argparse.ArgumentParser(description="Netzwerk-Analyzer Web-Dashboard")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    if not CONFIG_PATH.exists():
        save_config(dict(DEFAULT_CONFIG))

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Netzwerk-Analyzer Dashboard läuft auf http://{args.host}:{args.port}  (Strg+C zum Beenden)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
