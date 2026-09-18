#!/usr/bin/env python3
"""
Netzwerk-Stabilitäts-Analyzer
=============================

Werkzeug zur Fehlersuche in einem Heimnetz der Form

    Internet -> Kabelrouter -> WLAN/Ethernet-Router -> Powerline-Adapter -> Endgeräte

Es misst über einen längeren Zeitraum Latenz und Paketverlust zu mehreren
Punkten der Kette gleichzeitig (Kabelrouter, WLAN-Router, externe Server)
und ordnet Aussetzer dadurch einem Segment zu:

  - Schwankt schon der Ping zum Kabelrouter -> Problem an der Anschlussleitung
    / beim Provider / Kabelmodem.
  - Ist der Kabelrouter stabil, aber der WLAN-Router / Powerline-Segment nicht
    -> Problem im Heimnetz (WLAN-Interferenz, Powerline-Störung, Verkabelung).
  - Sind nur externe Ziele betroffen, obwohl beide Router stabil sind
    -> Problem beim Provider/DNS außerhalb der eigenen Kontrolle.

Funktioniert ohne Zusatz-Pakete (nur Python-Standardbibliothek). Für Plots
wird optional matplotlib genutzt, falls installiert.

Nutzung
-------

1) Messung laufen lassen (in einem Terminal, mehrere Stunden/Tage laufen lassen):

    python3 analyzer.py monitor \
        --target kabelrouter=192.168.0.1 \
        --target wlan_router=192.168.2.1 \
        --interval 5

2) Während der Messung Ereignisse notieren (Mikrowelle an, Powerline blinkt rot, ...)
   in einem zweiten Terminal:

    python3 analyzer.py note "Mikrowelle eingeschaltet"

3) Traceroute-Diagnose (Doppel-NAT erkennen):

    python3 analyzer.py traceroute --target 1.1.1.1

4) Auswertung nach der Messung:

    python3 analyzer.py report --csv network_log_*.csv --notes network_notes_*.txt --plot
"""

import argparse
import csv
import glob
import ipaddress
import platform
import re
import shutil
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_TARGETS = [
    ("kabelrouter", "192.168.0.1"),
    ("wlan_router", "192.168.2.1"),
    ("cloudflare_dns", "1.1.1.1"),
    ("google_dns", "8.8.8.8"),
]

TIME_RE = re.compile(r"time[=<]\s*([\d.]+)\s*ms", re.IGNORECASE)
IP_RE = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b")

TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S"


# --------------------------------------------------------------------------
# Ping
# --------------------------------------------------------------------------

def ping_once(host: str, timeout_s: float = 2.0):
    """Führt genau einen Ping aus. Gibt RTT in ms zurück, oder None bei Verlust."""
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", "1", "-w", str(int(timeout_s * 1000)), host]
    else:
        cmd = ["ping", "-c", "1", host]

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout_s + 2
        )
    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        raise SystemExit("Das Kommando 'ping' wurde nicht gefunden. Bitte installieren.")

    match = TIME_RE.search(proc.stdout)
    if match:
        return float(match.group(1))
    return None


# --------------------------------------------------------------------------
# WLAN-Signal (best effort, optional)
# --------------------------------------------------------------------------

def get_wifi_signal(iface: str):
    """Best-effort Auslesen von Signalstärke (dBm) und Bitrate. None wenn nicht möglich."""
    system = platform.system().lower()
    try:
        if system == "linux" and shutil.which("iw"):
            out = subprocess.run(
                ["iw", "dev", iface, "link"], capture_output=True, text=True, timeout=2
            ).stdout
            sig = re.search(r"signal:\s*(-?\d+)\s*dBm", out)
            rate = re.search(r"tx bitrate:\s*([\d.]+)\s*MBit/s", out)
            if sig:
                return {
                    "signal_dbm": float(sig.group(1)),
                    "bitrate_mbit": float(rate.group(1)) if rate else None,
                }
        elif system == "windows" and shutil.which("netsh"):
            out = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True, text=True, timeout=2,
            ).stdout
            sig = re.search(r"Signal\s*:?\s*(\d+)%", out)
            if sig:
                pct = float(sig.group(1))
                # grobe Umrechnung Prozent -> dBm, nur zur Orientierung
                dbm = (pct / 2) - 100
                return {"signal_dbm": dbm, "bitrate_mbit": None}
    except Exception:
        return None
    return None


# --------------------------------------------------------------------------
# Traceroute / Doppel-NAT-Erkennung
# --------------------------------------------------------------------------

def is_private_ip(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def run_traceroute(target: str):
    system = platform.system().lower()
    if system == "windows":
        cmd = ["tracert", "-d", "-h", "15", target]
    else:
        cmd = ["traceroute", "-n", "-m", "15", target]

    if not shutil.which(cmd[0]):
        print(f"'{cmd[0]}' ist nicht installiert. Unter Linux z.B.: sudo apt install traceroute")
        return

    print(f"Traceroute zu {target} ...\n")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    print(proc.stdout)

    hops = []
    for line in proc.stdout.splitlines():
        m = IP_RE.search(line)
        if m:
            hops.append(m.group(1))

    if not hops:
        print("Konnte keine Hops auslesen (evtl. Firewall blockiert ICMP/UDP).")
        return

    private_hops_before_public = 0
    for ip in hops:
        if is_private_ip(ip):
            private_hops_before_public += 1
        else:
            break

    print("Gefundene Hops:", " -> ".join(hops))
    if private_hops_before_public >= 2:
        print(
            "\n⚠️  Es liegen mind. zwei private IP-Hops vor dem ersten öffentlichen Hop.\n"
            "    Das deutet auf DOPPEL-NAT hin: Kabelrouter UND WLAN-Router routen beide "
            "und vergeben je ein eigenes privates Netz.\n"
            "    Empfehlung: Den Kabelrouter in den Modem-/Bridge-Modus versetzen, sodass "
            "nur der WLAN-Router routet und NAT/DHCP macht. Das reduziert Latenz, "
            "vereinfacht Port-Freigaben und beseitigt eine mögliche Fehlerquelle."
        )
    else:
        print("\nKein Hinweis auf Doppel-NAT in den ersten Hops gefunden.")


# --------------------------------------------------------------------------
# Monitor
# --------------------------------------------------------------------------

def cmd_monitor(args):
    targets = args.parsed_targets or DEFAULT_TARGETS
    out_path = Path(args.out or f"network_log_{datetime.now():%Y%m%d_%H%M%S}.csv")

    print(f"Schreibe Messwerte nach: {out_path}")
    print("Ziele:", ", ".join(f"{n}={h}" for n, h in targets))
    if args.wifi_iface:
        print(f"WLAN-Interface für Signalmessung: {args.wifi_iface}")
    print("Abbrechen mit Strg+C. Notizen in einem zweiten Terminal via:")
    print(f"  python3 {Path(__file__).name} note \"<text>\"\n")

    end_time = None
    if args.duration_min:
        end_time = time.time() + args.duration_min * 60

    new_file = not out_path.exists()
    with open(out_path, "a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["timestamp", "target", "host", "rtt_ms", "loss", "wifi_signal_dbm"])

        try:
            while True:
                ts = datetime.now().strftime(TIMESTAMP_FMT)
                wifi = get_wifi_signal(args.wifi_iface) if args.wifi_iface else None
                wifi_dbm = wifi["signal_dbm"] if wifi else ""

                row_summary = []
                for name, host in targets:
                    rtt = ping_once(host, timeout_s=args.timeout)
                    loss = 1 if rtt is None else 0
                    writer.writerow([ts, name, host, rtt if rtt is not None else "", loss, wifi_dbm])
                    f.flush()
                    row_summary.append(f"{name}={'TIMEOUT' if rtt is None else f'{rtt:.0f}ms'}")

                print(f"[{ts}] " + "  ".join(row_summary) + (f"  wifi={wifi_dbm:.0f}dBm" if wifi_dbm != "" else ""))

                if end_time and time.time() >= end_time:
                    break
                time.sleep(max(0.1, args.interval))
        except KeyboardInterrupt:
            print("\nMessung beendet.")

    print(f"\nMesswerte gespeichert in: {out_path}")
    print("Auswertung mit:")
    print(f"  python3 {Path(__file__).name} report --csv {out_path}")


# --------------------------------------------------------------------------
# Note
# --------------------------------------------------------------------------

def cmd_note(args):
    notes_path = Path(args.file or "network_notes.txt")
    ts = datetime.now().strftime(TIMESTAMP_FMT)
    with open(notes_path, "a") as f:
        f.write(f"{ts}\t{args.text}\n")
    print(f"Notiz gespeichert ({notes_path}): [{ts}] {args.text}")


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------

def load_rows(csv_paths):
    rows = []
    for pattern in csv_paths:
        for path in sorted(glob.glob(pattern)):
            with open(path, newline="") as f:
                for row in csv.DictReader(f):
                    rows.append(row)
    return rows


def load_notes(notes_paths):
    notes = []
    for pattern in notes_paths or []:
        for path in sorted(glob.glob(pattern)):
            with open(path) as f:
                for line in f:
                    line = line.rstrip("\n")
                    if not line or "\t" not in line:
                        continue
                    ts_str, text = line.split("\t", 1)
                    try:
                        ts = datetime.strptime(ts_str, TIMESTAMP_FMT)
                    except ValueError:
                        continue
                    notes.append((ts, text))
    return notes


def percentile(values, pct):
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * pct
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def compute_stats_by_target(by_target):
    """Berechnet Kennzahlen je Ziel. Wird von der CLI und vom Web-Dashboard genutzt."""
    stats_by_target = {}
    for target, trows in by_target.items():
        total = len(trows)
        losses = sum(1 for r in trows if r["loss"] == "1")
        rtts = [float(r["rtt_ms"]) for r in trows if r["rtt_ms"]]
        loss_pct = 100.0 * losses / total if total else 0.0

        if rtts:
            jitter = statistics.pstdev(rtts) if len(rtts) > 1 else 0.0
            avg = statistics.mean(rtts)
            median = statistics.median(rtts)
            p95 = percentile(rtts, 0.95)
            rtt_max = max(rtts)
        else:
            jitter = avg = median = p95 = rtt_max = None

        hourly = defaultdict(list)
        for r in trows:
            try:
                ts = datetime.strptime(r["timestamp"], TIMESTAMP_FMT)
            except ValueError:
                continue
            hourly[ts.hour].append(r)
        worst_hour, worst_hour_loss = None, -1
        for h, hrows in hourly.items():
            hl = sum(1 for r in hrows if r["loss"] == "1")
            pct = 100.0 * hl / len(hrows)
            if pct > worst_hour_loss:
                worst_hour_loss, worst_hour = pct, h

        stats_by_target[target] = {
            "host": trows[0]["host"], "total": total, "losses": losses, "loss_pct": loss_pct,
            "avg": avg, "median": median, "p95": p95, "max": rtt_max, "jitter": jitter,
            "worst_hour": worst_hour,
            "worst_hour_loss": worst_hour_loss if worst_hour_loss >= 0 else None,
            "rows": trows,
        }
    return stats_by_target


def correlate_notes(by_target, notes):
    """Gleicht Notizen mit Latenz-/Verlustwerten in einem ±30s Fenster ab."""
    results = []
    for ts, text in notes:
        window_start, window_end = ts - timedelta(seconds=30), ts + timedelta(seconds=30)
        hits = []
        for target, trows in by_target.items():
            near = [
                r for r in trows
                if window_start <= datetime.strptime(r["timestamp"], TIMESTAMP_FMT) <= window_end
            ]
            near_loss = sum(1 for r in near if r["loss"] == "1")
            if near and near_loss > 0:
                hits.append((target, near_loss, len(near)))
        results.append({"ts": ts, "text": text, "hits": hits})
    return results


def cmd_report(args):
    rows = load_rows(args.csv)
    if not rows:
        print("Keine Messdaten gefunden. Prüfe den --csv Pfad/Pattern.")
        return
    notes = load_notes(args.notes)

    by_target = defaultdict(list)
    for r in rows:
        by_target[r["target"]].append(r)

    stats_by_target = compute_stats_by_target(by_target)

    print("=" * 70)
    print("NETZWERK-ANALYSE-BERICHT")
    print("=" * 70)

    for target, s in stats_by_target.items():
        print(f"\n--- Ziel: {target} ({s['host']}) ---")
        print(f"  Messungen:       {s['total']}")
        print(f"  Paketverlust:    {s['loss_pct']:.2f} %  ({s['losses']}/{s['total']})")
        if s["avg"] is not None:
            print(f"  Latenz avg/median/p95/max: "
                  f"{s['avg']:.1f} / {s['median']:.1f} / {s['p95']:.1f} / {s['max']:.1f} ms")
            print(f"  Jitter (Std.abw.): {s['jitter']:.1f} ms")
        else:
            print("  Keine erfolgreichen Antworten erhalten.")
        if s["worst_hour"] is not None and s["worst_hour_loss"] > 0:
            print(f"  Höchster Paketverlust um {s['worst_hour']:02d}:00 Uhr ({s['worst_hour_loss']:.1f} %)")

    # Notizen-Korrelation
    if notes:
        print("\n--- Abgleich mit Notizen (±30s Fenster) ---")
        for item in correlate_notes(by_target, notes):
            note_str = f"[{item['ts'].strftime(TIMESTAMP_FMT)}] '{item['text']}'"
            if item["hits"]:
                hit_str = "; ".join(f"{t}: {l}/{n} Verluste" for t, l, n in item["hits"])
                print(f"  {note_str} -> mögliche Korrelation: {hit_str}")
            else:
                print(f"  {note_str} -> keine auffälligen Verluste im Zeitfenster")

    # Diagnose / Empfehlungen
    print("\n" + "=" * 70)
    print("DIAGNOSE")
    print("=" * 70)
    diagnosis = build_diagnosis(stats_by_target)
    for line in diagnosis:
        print(f"- {line}")

    if args.plot:
        make_plot(by_target, args.plot if isinstance(args.plot, str) else "network_report.png")


LOSS_WARN_PCT = 1.0
JITTER_WARN_MS = 20.0


def build_diagnosis(stats_by_target):
    msgs = []

    def get(name):
        for key in stats_by_target:
            if key == name:
                return stats_by_target[key]
        return None

    gateway = get("kabelrouter")
    wlan = get("wlan_router")
    externals = {k: v for k, v in stats_by_target.items()
                 if k not in ("kabelrouter", "wlan_router")}

    if gateway and (gateway["loss_pct"] > LOSS_WARN_PCT or (gateway["jitter"] or 0) > JITTER_WARN_MS):
        msgs.append(
            "Bereits der Ping zum Kabelrouter zeigt Paketverlust/Jitter. Das deutet auf ein "
            "Problem VOR oder AM Kabelrouter hin: Anschlussleitung, Stecker/Kabel, "
            "Kabelmodem-Firmware oder Provider-seitige Störung. Prüfe die Signalwerte im "
            "Kabelrouter-Interface (Pegel/SNR), teste mit einem anderen Ethernet-Kabel, "
            "und kontaktiere ggf. den Provider mit den gesammelten Messwerten."
        )
    elif gateway:
        msgs.append(
            "Der Kabelrouter selbst ist stabil (kein signifikanter Verlust/Jitter) - "
            "die Internetanbindung an sich scheint in Ordnung zu sein."
        )

    if gateway and wlan:
        gw_bad = gateway["loss_pct"] > LOSS_WARN_PCT or (gateway["jitter"] or 0) > JITTER_WARN_MS
        wlan_bad = wlan["loss_pct"] > LOSS_WARN_PCT or (wlan["jitter"] or 0) > JITTER_WARN_MS
        if wlan_bad and not gw_bad:
            msgs.append(
                "Der WLAN-Router zeigt deutlich mehr Verlust/Jitter als der Kabelrouter, "
                "obwohl die Strecke zum Kabelrouter stabil ist. Das Problem liegt also "
                "vermutlich im Segment WLAN-Router -> Powerline -> Endgeräte: "
                "WLAN-Kanalstörung, Powerline-Störung im Stromnetz, oder ein schwaches/"
                "defektes Ethernet-Kabel zwischen Kabelrouter und WLAN-Router."
            )
        elif gw_bad and wlan_bad:
            msgs.append(
                "Sowohl Kabelrouter als auch WLAN-Router zeigen Probleme - das deutet auf "
                "eine gemeinsame Ursache hin (z.B. Stromausfälle/Spannungsschwankungen, "
                "ein überlasteter Switch/Port, oder tatsächlich die Internetleitung selbst, "
                "die sich bis in alle nachgelagerten Messungen durchzieht)."
            )
        elif not gw_bad and not wlan_bad:
            msgs.append(
                "Kabelrouter und WLAN-Router sind beide stabil. Falls trotzdem Aussetzer "
                "spürbar sind, liegt die Ursache wahrscheinlich hinter dem WLAN-Router: "
                "Powerline-Adapter, WLAN-Interferenz am jeweiligen Endgerät oder die "
                "Verbindung zwischen Powerline und Endgerät."
            )

    ext_bad = [k for k, v in externals.items()
               if v["loss_pct"] > LOSS_WARN_PCT or (v["jitter"] or 0) > JITTER_WARN_MS]
    ext_ok = [k for k, v in externals.items() if k not in ext_bad]
    if ext_bad and wlan and wlan["loss_pct"] <= LOSS_WARN_PCT and (wlan["jitter"] or 0) <= JITTER_WARN_MS:
        if len(ext_bad) == len(externals) and externals:
            msgs.append(
                "Alle externen Ziele (Internet) zeigen Probleme, während der WLAN-Router "
                "lokal stabil ist. Das spricht für ein Problem beim Provider, DNS oder "
                "der Route ins Internet - nicht im Heimnetz. Mit "
                "'analyzer.py traceroute --target 1.1.1.1' die Hops außerhalb des "
                "eigenen Netzes prüfen."
            )
        else:
            msgs.append(
                f"Nur einzelne externe Ziele ({', '.join(ext_bad)}) sind auffällig, "
                f"andere ({', '.join(ext_ok)}) nicht - das deutet eher auf ein Problem "
                "bei diesem speziellen Anbieter/Server als auf das eigene Netz hin."
            )

    # WLAN-Signal
    wifi_samples = []
    for v in stats_by_target.values():
        wifi_samples += [float(r["wifi_signal_dbm"]) for r in v["rows"] if r.get("wifi_signal_dbm")]
    if wifi_samples:
        avg_signal = statistics.mean(wifi_samples)
        if avg_signal < -70:
            msgs.append(
                f"Die gemessene WLAN-Signalstärke ist im Schnitt schwach ({avg_signal:.0f} dBm). "
                "Router/Access Point näher positionieren, Kanal wechseln (2,4GHz: 1/6/11, "
                "5GHz nach Möglichkeit bevorzugen) oder einen Mesh-/Repeater-Access-Point "
                "in Reichweite des Powerline-Netzes ergänzen."
            )

    if not msgs:
        msgs.append("Keine auffälligen Muster in den vorliegenden Daten gefunden.")

    msgs.append(
        "Allgemein bei dieser Topologie (Kabelrouter -> WLAN/Ethernet-Router -> Powerline): "
        "Doppel-NAT vermeiden, indem der Kabelrouter in den Modem-/Bridge-Modus versetzt "
        "wird und nur der WLAN-Router routet (siehe 'analyzer.py traceroute')."
    )
    msgs.append(
        "Powerline-Adapter immer direkt in die Wanddose stecken (nicht in Mehrfachsteckdosen "
        "oder Verlängerungskabel) und nach Möglichkeit auf derselben Phase/Sicherungskreis "
        "betreiben - das reduziert Störungen durch andere Geräte im Stromnetz erheblich."
    )
    return msgs


def make_plot(by_target, out_file):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\nmatplotlib ist nicht installiert - Plot wird übersprungen "
              "(pip install matplotlib für Diagramme).")
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    for target, trows in by_target.items():
        xs, ys = [], []
        for r in trows:
            if not r["rtt_ms"]:
                continue
            try:
                xs.append(datetime.strptime(r["timestamp"], TIMESTAMP_FMT))
                ys.append(float(r["rtt_ms"]))
            except ValueError:
                continue
        if xs:
            ax.plot(xs, ys, label=target, marker=".", linewidth=0.8, markersize=2)

    ax.set_xlabel("Zeit")
    ax.set_ylabel("Latenz (ms)")
    ax.set_title("Netzwerk-Latenz über Zeit")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_file, dpi=120)
    print(f"\nDiagramm gespeichert: {out_file}")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def parse_target_arg(value):
    if "=" not in value:
        raise argparse.ArgumentTypeError("Format muss name=host sein, z.B. wlan_router=192.168.2.1")
    name, host = value.split("=", 1)
    return name, host


def main():
    parser = argparse.ArgumentParser(description="Netzwerk-Stabilitäts-Analyzer")
    sub = parser.add_subparsers(dest="command", required=True)

    p_monitor = sub.add_parser("monitor", help="Kontinuierlich Latenz/Verlust messen")
    p_monitor.add_argument("--target", action="append", type=parse_target_arg, dest="parsed_targets",
                            help="name=host, mehrfach angebbar. Default: Kabelrouter/WLAN-Router/DNS-Server")
    p_monitor.add_argument("--interval", type=float, default=5.0, help="Sekunden zwischen Messungen")
    p_monitor.add_argument("--timeout", type=float, default=2.0, help="Ping-Timeout in Sekunden")
    p_monitor.add_argument("--duration-min", type=float, default=None, help="Messdauer in Minuten (default: bis Strg+C)")
    p_monitor.add_argument("--out", type=str, default=None, help="Ausgabedatei (CSV)")
    p_monitor.add_argument("--wifi-iface", type=str, default=None, help="WLAN-Interface für Signalmessung, z.B. wlan0")
    p_monitor.set_defaults(func=cmd_monitor)

    p_note = sub.add_parser("note", help="Zeitgestempelte Notiz speichern (z.B. 'Mikrowelle an')")
    p_note.add_argument("text")
    p_note.add_argument("--file", type=str, default=None, help="Notizdatei (default: network_notes.txt)")
    p_note.set_defaults(func=cmd_note)

    p_trace = sub.add_parser("traceroute", help="Traceroute + Doppel-NAT-Erkennung")
    p_trace.add_argument("--target", type=str, default="1.1.1.1")
    p_trace.set_defaults(func=lambda a: run_traceroute(a.target))

    p_report = sub.add_parser("report", help="Messdaten auswerten und Diagnose erstellen")
    p_report.add_argument("--csv", action="append", required=True, help="CSV-Datei(en) oder Glob-Pattern, mehrfach angebbar")
    p_report.add_argument("--notes", action="append", default=None, help="Notiz-Datei(en) oder Glob-Pattern")
    p_report.add_argument("--plot", nargs="?", const=True, default=False, help="PNG-Diagramm erzeugen (optional: Dateiname)")
    p_report.set_defaults(func=cmd_report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
