#!/usr/bin/env python3
"""
Buecherei-Check — standalone script (no AI agent involved at runtime).

Logs into the two library portals (Stadtbibliothek Stuttgart / aDISWeb and
Stadtbuechereien Korntal-Muenchingen / Koha) for every account listed in
library_accounts.yaml, reads due dates, and overwrites uebersicht.txt with
the current status. No email by default -- just open uebersicht.txt when
you want to know where things stand. Pass --email to also send it (needs
email_config.yaml, see README.md), but that's opt-in, not required.

Why this exists as a plain script instead of an AI agent action: entering
stored passwords into a login form is something an AI agent (Claude) is not
allowed to do on your behalf, regardless of authorization -- that rule
applies to the agent, not to code you run yourself. This script is code you
run yourself, on your own machine, so it isn't subject to that restriction.

IMPORTANT LIMITATIONS (read before relying on this):
- The Koha/Korntal-Muenchingen login form and checkouts table structure
  were verified against the real site (read-only inspection, 2026-08-09).
- The Stuttgart/aDISWeb portal LOOKED down for 5 straight attempts (blank
  white page) before it turned out the stored URL pointed at a page with a
  broken template link (sp=Shost:port, never filled in). The correct URL
  (with sp=SOPAC) is now in library_accounts.yaml, and the login form
  itself (fields "Ausweisnummer"/"Passwort") is verified read-only. What's
  still UNVERIFIED: the post-login checkouts table, since verifying that
  would require actually logging in, which is exactly the step Claude
  can't do. `check_stuttgart()`'s table-scraping is a generic fallback
  (scans all tables for DD.MM.YYYY-shaped text) -- run with --debug and
  check the after-login screenshot the first time to see if it actually
  found your loans, and expect to need one more round of fixes there.
- Renewability / due-date parsing depends on the site's exact HTML not
  changing. If a portal redesigns its site, this script will break loudly
  (see the try/except reporting below) rather than silently -- that's
  intentional; it should never report "all clear" when it actually failed.
"""

import argparse
import re
import smtplib
import sys
import traceback
from dataclasses import dataclass, field
from datetime import date
from email.mime.text import MIMEText
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

SCRIPT_DIR = Path(__file__).resolve().parent
ACCOUNTS_FILE = SCRIPT_DIR.parent / "library_accounts.yaml"
EMAIL_CONFIG_FILE = SCRIPT_DIR / "email_config.yaml"
DEBUG_DIR = SCRIPT_DIR / "debug_screenshots"
OVERVIEW_FILE = SCRIPT_DIR / "uebersicht.txt"

URGENT_DAYS = 3   # <= this many days left (and not yet overdue) -> urgent
SOON_DAYS = 7      # <= this many days left -> "bald faellig"


@dataclass
class Loan:
    title: str
    due_date: date | None
    renewable: bool
    renew_note: str = ""
    overdue: bool = False


@dataclass
class AccountResult:
    account_name: str
    portal_label: str
    loans: list[Loan] = field(default_factory=list)
    error: str | None = None  # set if the check itself failed -- never leave this silent


def load_accounts() -> list[dict]:
    if not ACCOUNTS_FILE.exists():
        raise SystemExit(f"Zugangsdaten fehlen: {ACCOUNTS_FILE} existiert nicht.")
    data = yaml.safe_load(ACCOUNTS_FILE.read_text(encoding="utf-8"))
    return data.get("accounts", [])


def load_email_config() -> dict:
    if not EMAIL_CONFIG_FILE.exists():
        raise SystemExit(
            f"E-Mail-Konfiguration fehlt: {EMAIL_CONFIG_FILE} existiert nicht.\n"
            "Siehe README.md, Abschnitt 'E-Mail einrichten'."
        )
    return yaml.safe_load(EMAIL_CONFIG_FILE.read_text(encoding="utf-8"))


def parse_de_date(text: str) -> date | None:
    """Parse a German-format date (DD.MM.YYYY) out of arbitrary cell text."""
    match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", text)
    if not match:
        return None
    day, month, year = map(int, match.groups())
    try:
        return date(year, month, day)
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Korntal-Muenchingen / Koha
# --------------------------------------------------------------------------

def check_koha(page, account: dict, debug: bool) -> AccountResult:
    label = "Korntal-Muenchingen (Koha)"
    result = AccountResult(account_name=account["name"], portal_label=label)

    page.goto(account["portal_url"], wait_until="networkidle", timeout=30000)

    # Fixed 2026-08-09 after a real run: get_by_label("Login:") hit a strict-mode
    # violation because the page has TWO matching fields -- the visible main
    # form (id="userid") and a hidden duplicate inside the top-nav "Benutzerkonto"
    # dropdown (id="muserid", presumably a mobile/collapsed nav login widget).
    # IDs are unique per the real error output, so target those directly instead
    # of the ambiguous label. Submitting via Enter in the password field sidesteps
    # the same ambiguity for the "Anmelden" button (there are likely two of those
    # too, one per form).
    page.locator("#userid").fill(str(account["username"]))
    page.locator("#password").fill(str(account["password"]))
    page.locator("#password").press("Enter")
    page.wait_for_load_state("networkidle", timeout=30000)

    if debug:
        DEBUG_DIR.mkdir(exist_ok=True)
        page.screenshot(path=str(DEBUG_DIR / f"koha_{account['name']}_after_login.png"), full_page=True)

    # Did the login actually succeed? Koha reloads opac-user.pl either way.
    # No #checkoutst table can mean two different things: (a) login failed and
    # we're still looking at a login page, or (b) login worked and the account
    # genuinely has nothing on loan. Distinguish via #userid -- if that specific
    # field (the main form, confirmed unique in the 2026-08-09 error output,
    # unlike the ambiguous label lookup this replaced) is still present, we're
    # still on the login page and it failed.
    if page.locator("#checkoutst").count() == 0 and page.locator("#userid").count() > 0:
        result.error = "Login fehlgeschlagen (Login-Feld #userid ist nach dem Absenden immer noch da)."
        return result

    table = page.locator("#checkoutst")
    if table.count() == 0:
        # No checkouts table at all usually just means: nothing on loan.
        return result

    rows = table.locator("tbody tr")
    count = rows.count()
    for i in range(count):
        row = rows.nth(i)
        row_class = row.get_attribute("class") or ""
        overdue = "overdue" in row_class

        # Title: first link in the row that points at a biblio detail page.
        title_link = row.locator("a[href*='opac-detail.pl']").first
        title = title_link.inner_text().strip() if title_link.count() > 0 else row.locator("td").first.inner_text().strip()

        due_cell = row.locator("td.date_due")
        due_text = due_cell.first.inner_text().strip() if due_cell.count() > 0 else ""
        due = parse_de_date(due_text)
        if not overdue:
            overdue = "overdue" in (due_cell.first.get_attribute("class") or "") if due_cell.count() > 0 else False

        renew_cell = row.locator("td.renew")
        renew_text = renew_cell.first.inner_text().strip() if renew_cell.count() > 0 else ""
        not_renewable_markers = [
            "nicht verl", "not renewable", "no longer renewable",
            "not allowed", "nicht möglich",
        ]
        renewable = not any(marker in renew_text.lower() for marker in not_renewable_markers)

        result.loans.append(Loan(
            title=title,
            due_date=due,
            renewable=renewable,
            renew_note=renew_text[:200],
            overdue=overdue,
        ))

    return result


# --------------------------------------------------------------------------
# Stuttgart / aDISWeb
# --------------------------------------------------------------------------

def check_stuttgart(page, account: dict, debug: bool) -> AccountResult:
    label = "Stadtbibliothek Stuttgart (aDISWeb)"
    result = AccountResult(account_name=account["name"], portal_label=label)

    try:
        page.goto(account["portal_url"], wait_until="networkidle", timeout=30000)
    except PlaywrightTimeoutError:
        result.error = "Portal hat innerhalb von 30s nicht geladen. Mit der korrigierten URL (sp=SOPAC) sollte das eigentlich nicht mehr passieren -- pruefen, ob library_accounts.yaml wirklich die neue URL enthaelt."
        return result

    if debug:
        DEBUG_DIR.mkdir(exist_ok=True)
        page.screenshot(path=str(DEBUG_DIR / f"adis_{account['name']}_before_login.png"), full_page=True)

    # Fixed 2026-08-09: the portal wasn't actually down. The bare /aDISWeb
    # entry point serves a near-empty page whose one link has a broken,
    # unfilled template parameter (sp=Shost:port -- literally unsubstituted),
    # which the server rejects. The real, working entry point needs
    # sp=SOPAC instead -- see the corrected portal_url in library_accounts.yaml.
    # Once on the real page, the login form was verified read-only via
    # Chrome (no credentials entered during verification): labeled fields
    # "Ausweisnummer" / "Passwort", single unambiguous "Anmelden" submit
    # button (unlike Koha, no duplicate here).
    #
    # Bug found 2026-08-09 (Tim's first real run after the URL fix): the
    # homepage itself does NOT have these fields -- they only appear after
    # clicking the "Anmelden" nav link, which navigates to a separate,
    # session-bound login view (aDIS is a server-side-session app; the
    # login page's URL includes a jsessionid that's created fresh per
    # browser session, so it can't just be hardcoded/visited directly).
    # This step was missing entirely, which is why the fields were never
    # found even after the URL itself was fixed.
    anmelden_link = page.get_by_role("link", name="Anmelden")
    if anmelden_link.count() == 0:
        anmelden_link = page.get_by_text("Anmelden", exact=True)
    if anmelden_link.count() == 0:
        result.error = "Konnte den 'Anmelden'-Link auf der Startseite nicht finden. Mit --debug pruefen, ob die Seite anders aussieht als erwartet."
        return result
    anmelden_link.first.click()
    page.wait_for_load_state("networkidle", timeout=30000)

    if debug:
        page.screenshot(path=str(DEBUG_DIR / f"adis_{account['name']}_login_page.png"), full_page=True)

    user_field = page.get_by_label("Ausweisnummer")
    pass_field = page.get_by_label("Passwort")

    if user_field.count() == 0 or pass_field.count() == 0:
        result.error = (
            "Konnte das Login-Formular nicht finden (Felder 'Ausweisnummer'/'Passwort'), "
            "auch nach Klick auf 'Anmelden'. Mit --debug pruefen und Claude Bescheid geben."
        )
        return result

    user_field.fill(str(account["username"]))
    pass_field.fill(str(account["password"]))
    page.get_by_role("button", name="Anmelden", exact=True).click()

    page.wait_for_load_state("networkidle", timeout=30000)

    if debug:
        page.screenshot(path=str(DEBUG_DIR / f"adis_{account['name']}_after_login.png"), full_page=True)

    # Bug found 2026-08-09 (Tim's debug screenshot): submitting login redirects
    # back to the generic homepage, not to the account/loans view -- login DID
    # succeed (nav shows "Abmelden"/"Mein Konto" instead of "Anmelden"), but
    # there's nothing to scrape here. Need one more click on "Mein Konto".
    if page.get_by_text("Abmelden", exact=True).count() == 0:
        result.error = "Login scheint fehlgeschlagen (kein 'Abmelden' in der Navigation nach dem Absenden sichtbar)."
        return result

    mein_konto = page.get_by_role("link", name="Mein Konto")
    if mein_konto.count() == 0:
        mein_konto = page.get_by_text("Mein Konto", exact=True)
    if mein_konto.count() == 0:
        result.error = "Eingeloggt, aber 'Mein Konto'-Link nicht gefunden -- Seite mit --debug pruefen."
        return result
    mein_konto.first.click()
    page.wait_for_load_state("networkidle", timeout=30000)

    if debug:
        page.screenshot(path=str(DEBUG_DIR / f"adis_{account['name']}_account_page.png"), full_page=True)

    # Bug found 2026-08-09 (2nd debug screenshot round): "Mein Konto" is only
    # a SUMMARY (loan count + next due date, e.g. "2 Ausleihen" / "Nächstes
    # Faelligkeitsdatum 25.08.2026") -- no per-book detail here at all. Need
    # to click into the "Ausleihen" tile itself. Confirmed via Konrad's
    # screenshot that a genuinely empty account reliably shows "Keine
    # Ausleihen" (exact text) instead -- treat that as a real, trustworthy
    # zero-loans signal, not an error.
    if page.get_by_text("Keine Ausleihen", exact=True).count() > 0:
        return result

    ausleihen_tile = page.get_by_text(re.compile(r"^\d+\s+Ausleihen$"))
    if ausleihen_tile.count() == 0:
        result.error = "Weder 'Keine Ausleihen' noch eine 'N Ausleihen'-Kachel gefunden -- Seite mit --debug pruefen."
        return result
    ausleihen_tile.first.click()
    page.wait_for_load_state("networkidle", timeout=30000)

    if debug:
        page.screenshot(path=str(DEBUG_DIR / f"adis_{account['name']}_ausleihen_list.png"), full_page=True)

    # Still no verified table structure for the actual itemized loans list
    # (this is now hopefully finally the right page, but the exact markup
    # is still a guess). Best-effort: scan all
    # table rows for German-format dates and treat each such row as a loan.
    # This WILL likely need to be replaced with real selectors once you can
    # see the authenticated page (run with --debug and check the screenshot,
    # or send me the HTML/screenshot and I'll fix this function properly).
    rows = page.locator("table tr")
    count = rows.count()
    found_any_date = False
    for i in range(count):
        row_text = rows.nth(i).inner_text()
        due = parse_de_date(row_text)
        if not due:
            continue
        found_any_date = True
        # Bug found 2026-08-09 (Tim's real output): the first line of the row
        # is often a short UI action label ("Markieren" -- a checkbox/select
        # control), not the book title, so splitlines()[0] picked that up
        # instead. Heuristic fix: take the LONGEST line in the row instead --
        # titles are reliably longer than one-word UI labels. Not verified
        # against the raw HTML (still don't have that), just against what
        # this actually produced.
        candidate_lines = [ln.strip() for ln in row_text.splitlines() if ln.strip()]
        known_ui_labels = {"markieren", "verlaengern", "vormerken", "aktion"}
        candidate_lines = [ln for ln in candidate_lines if ln.lower() not in known_ui_labels]
        title = max(candidate_lines, key=len)[:150] if candidate_lines else "(Titel nicht erkannt)"
        result.loans.append(Loan(
            title=title,
            due_date=due,
            renewable=True,  # unknown -- aDIS parsing not verified, see docstring
            renew_note="(Verlaengerbarkeit fuer Stuttgart nicht zuverlaessig auslesbar -- Selektoren unverifiziert)",
            overdue=due < date.today(),
        ))

    if not found_any_date and result.error is None:
        # Could genuinely mean "no loans" OR "we're not actually logged in
        # and looking at the wrong page". Flag it so you don't mistake
        # silence for good news.
        result.error = (
            "Keine Ausleihen gefunden -- ODER Login/Seiten-Erkennung fehlgeschlagen "
            "(unverifizierte Selektoren). Bei Zweifel mit --debug pruefen."
        )

    return result


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

def run_checks(debug: bool) -> list[AccountResult]:
    accounts = load_accounts()
    results: list[AccountResult] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not debug)
        for account in accounts:
            context = browser.new_context()
            page = context.new_page()
            portal_url = account.get("portal_url", "")
            try:
                if "lmscloud.net" in portal_url:
                    result = check_koha(page, account, debug)
                elif "stadtbibliothek-stuttgart.de" in portal_url:
                    result = check_stuttgart(page, account, debug)
                else:
                    result = AccountResult(
                        account_name=account.get("name", "?"),
                        portal_label=portal_url,
                        error=f"Unbekannte Portal-URL, keine Check-Funktion zustaendig: {portal_url}",
                    )
            except Exception:  # noqa: BLE001 -- must never crash the whole run silently
                result = AccountResult(
                    account_name=account.get("name", "?"),
                    portal_label=portal_url,
                    error="Unerwarteter Fehler:\n" + traceback.format_exc(limit=3),
                )
            results.append(result)
            context.close()
        browser.close()

    return results


def build_report(results: list[AccountResult]) -> str:
    today = date.today()
    lines = [f"BUECHEREI-CHECK -- {today.strftime('%d.%m.%Y')}", ""]

    any_error = any(r.error for r in results)
    any_overdue = any(l.overdue for r in results for l in r.loans)
    any_urgent = any(
        (not l.overdue) and l.due_date and (l.due_date - today).days <= URGENT_DAYS
        for r in results for l in r.loans
    )

    if any_overdue:
        lines.append("⚠️ MINDESTENS EIN BUCH IST UEBERFAELLIG.")
    elif any_urgent:
        lines.append("⚠️ Mindestens ein Buch ist in ≤ 3 Tagen faellig.")
    elif any_error:
        lines.append("⚠️ Nicht alle Konten konnten geprueft werden -- siehe unten.")
    else:
        lines.append("Kein Buch ist ueberfaellig oder dringend faellig.")
    lines.append("")

    for r in results:
        lines.append("=" * 50)
        lines.append(f"{r.account_name} -- {r.portal_label}")
        lines.append("=" * 50)

        if r.error:
            lines.append(f"FEHLER: {r.error}")
            lines.append("")
            continue

        if not r.loans:
            lines.append("Keine ausgeliehenen Medien.")
            lines.append("")
            continue

        for loan in sorted(r.loans, key=lambda l: (l.due_date is None, l.due_date)):
            days_left = (loan.due_date - today).days if loan.due_date else None
            date_str = loan.due_date.strftime("%d.%m.%Y") if loan.due_date else None
            if loan.overdue:
                marker = "\U0001f534 UEBERFAELLIG"
                when = f"seit {abs(days_left)} Tag(en) (faellig war am {date_str})" if days_left is not None else "Datum unklar"
            elif days_left is not None and days_left <= URGENT_DAYS:
                marker = "⚠️ DRINGEND"
                when = f"faellig am {date_str} (in {days_left} Tag(en))"
            elif days_left is not None and days_left <= SOON_DAYS:
                marker = "⚠️ bald faellig"
                when = f"faellig am {date_str} (in {days_left} Tag(en))"
            else:
                marker = "✅"
                when = f"faellig am {date_str} (in {days_left} Tag(en))" if days_left is not None else "Faelligkeit unklar"

            renew = "verlaengerbar" if loan.renewable else f"NICHT verlaengerbar ({loan.renew_note})" if loan.renew_note else "NICHT verlaengerbar"
            lines.append(f"{marker} {loan.title} -- {when}, {renew}")
        lines.append("")

    lines.append("-- Automatischer Buecherei-Check (lokales Skript, kein Agent)")
    return "\n".join(lines)


def send_email(report_text: str, config: dict) -> None:
    msg = MIMEText(report_text, _charset="utf-8")
    msg["Subject"] = f"Buecherei-Check {date.today().strftime('%d.%m.%Y')}"
    msg["From"] = config["sender_email"]
    msg["To"] = config["recipient_email"]

    with smtplib.SMTP(config.get("smtp_server", "smtp.gmail.com"), config.get("smtp_port", 587)) as server:
        server.starttls()
        server.login(config["sender_email"], config["app_password"])
        server.send_message(msg)


def write_overview(report_text: str) -> None:
    """Overwrite the single 'current status' file. This is the default
    output -- no email, no inbox clutter, just open the file when you want
    to know where things stand. It always reflects the latest run only."""
    OVERVIEW_FILE.write_text(report_text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Buecherei-Check (standalone, no AI agent)")
    parser.add_argument("--debug", action="store_true", help="Run browser visibly and save screenshots to debug_screenshots/")
    parser.add_argument("--dry-run", action="store_true", help="Only print the report -- don't write the overview file or send email")
    parser.add_argument("--email", action="store_true", help="Also send the report by email (needs email_config.yaml). Off by default -- the overview file is the primary output.")
    args = parser.parse_args()

    results = run_checks(debug=args.debug)
    report = build_report(results)

    print(report)

    if args.dry_run:
        print("\n[--dry-run] Nichts geschrieben, keine E-Mail gesendet.")
        return 0

    write_overview(report)
    print(f"\nUebersicht aktualisiert: {OVERVIEW_FILE}")

    if args.email:
        try:
            email_config = load_email_config()
            send_email(report, email_config)
            print("E-Mail gesendet.")
        except Exception:
            print("\nFEHLER beim E-Mail-Versand:", file=sys.stderr)
            traceback.print_exc()
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
