#!/usr/bin/env python3
"""
fetch_repeaters.py — Download repeater data from the RepeaterBook API.

IMPORTANT — API access changed in 2026:
  RepeaterBook now requires an approved API token. As of March 2026 the
  export API uses token-based authentication and rejects keyless requests
  with HTTP 403. To use this script you must:
    1. Create a RepeaterBook.com account.
    2. Apply for API access at https://www.repeaterbook.com/api/token_request.php
    3. Once approved, set your token in the environment before running:
         export REPEATERBOOK_TOKEN="your-issued-token"
       (or pass --token on the command line, or put it in
        /opt/fieldcomms/data/repeaterbook_token.txt)

If you do not have a token, use the OFFLINE FILE method instead:
  repeaterbook.com -> search your area -> Export -> CSV, then load the CSV
  on the "Offline File" tab of the Repeater Database page. No token needed.

Usage: python3 fetch_repeaters.py [--states IL,WI,IN,IA] [--bands 2m,70cm] [--token TOKEN]
"""

import json, time, urllib.request, urllib.parse, urllib.error, argparse, sys, os
from pathlib import Path

DB_PATH = Path("/opt/fieldcomms/data/fieldcomms.db")
JSON_SNAPSHOT = Path("/opt/fieldcomms/data/repeaters.json")
TOKEN_FILE  = Path("/opt/fieldcomms/data/repeaterbook_token.txt")
REPEATERBOOK_URL = "https://www.repeaterbook.com/api/export.php"

# RepeaterBook band codes
BAND_MAP = {
    "10m": "10",
    "6m":  "6",
    "2m":  "2",
    "1.25m": "1.25",
    "70cm": "0.70",
    "33cm": "0.33",
    "23cm": "0.23",
}

# McHenry County IL and surrounding mutual-aid region (IL + bordering states)
DEFAULT_STATES = ["IL", "WI", "IN", "IA"]
DEFAULT_BANDS  = ["2m", "70cm"]


def get_token(cli_token=None):
    """Resolve the RepeaterBook API token from CLI, env, or token file."""
    if cli_token:
        return cli_token.strip()
    env = os.environ.get("REPEATERBOOK_TOKEN", "").strip()
    if env:
        return env
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    return ""


def fetch_repeaters(state, band_code, token):
    """Fetch repeaters for a given state and band from RepeaterBook."""
    params = {
        "state_id": state,
        "band": band_code,
        "freq": "",
        "features": "",
        "status_id": "1",  # On-air only
        "type": "json",
    }
    url = REPEATERBOOK_URL + "?" + urllib.parse.urlencode(params)
    headers = {
        # A descriptive, contactable user-agent is required by RepeaterBook.
        "User-Agent": "FieldComms-EmComm/1.0 (+https://www.anthropic.com; MCESV/MCEMA K9ESV)",
        "Accept": "application/json",
    }
    # New (2026+) token authentication. Without this, expect HTTP 403.
    if token:
        headers["X-RB-App-Token"] = token
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data.get("results", [])

def normalize_repeater(r):
    """Normalize a RepeaterBook result into the FieldComms 'repeaters' table schema."""
    def yn(v): return 1 if str(v).strip().lower() in ("yes", "1", "true") else 0
    digital = r.get("Digital", "") or ""
    mode = digital if digital and digital.lower() not in ("", "no", "none") else "FM"
    return {
        "callsign":    r.get("Callsign", ""),
        "output_freq": str(r.get("Frequency", "") or ""),
        "input_freq":  str(r.get("Input Freq", "") or r.get("input_freq", "") or ""),
        "tone":        r.get("PL", "") or "",
        "tone_input":  r.get("TSQ", "") or "",
        "mode":        mode,
        "digital_code": r.get("Digital Code", "") or "",
        "city":        r.get("Nearest City", "") or "",
        "state":       r.get("State", "") or "",
        "county":      r.get("County", "") or "",
        "lat":         float(r.get("Lat", 0) or 0),
        "lon":         float(r.get("Long", 0) or 0),
        "status":      r.get("Operational Status", "On-Air") or "On-Air",
        "use_type":    r.get("Use", "Open") or "Open",
        "ares":        yn(r.get("ARES", "")),
        "races":       yn(r.get("RACES", "")),
        "skywarn":     yn(r.get("SKYWARN", "")),
        "echolink":    1 if (r.get("EchoLink Node", "") or "").strip() else 0,
        "allstar":     1 if (r.get("AllStar Node", "") or "").strip() else 0,
        "sponsor":     r.get("Sponsor", "") or "",
        "notes":       r.get("Notes", "") or "",
        "source":      "RepeaterBook",
    }


# Columns written to the repeaters table, in order.
REP_COLS = ["callsign", "output_freq", "input_freq", "tone", "tone_input", "mode",
            "digital_code", "city", "state", "county", "lat", "lon", "status",
            "use_type", "ares", "races", "skywarn", "echolink", "allstar",
            "sponsor", "notes", "source", "updated"]


def write_to_db(repeaters, db_path):
    """Replace the repeaters table contents with the freshly fetched data."""
    import sqlite3, datetime
    conn = sqlite3.connect(str(db_path))
    now = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    try:
        # Clear only RepeaterBook-sourced rows so any manual entries survive.
        conn.execute("DELETE FROM repeaters WHERE source = 'RepeaterBook'")
        placeholders = ",".join("?" * len(REP_COLS))
        sql = f"INSERT INTO repeaters ({','.join(REP_COLS)}) VALUES ({placeholders})"
        for rep in repeaters:
            row = [rep.get(c, "") for c in REP_COLS[:-1]] + [now]
            conn.execute(sql, row)
        conn.commit()
        n = conn.execute("SELECT COUNT(*) FROM repeaters").fetchone()[0]
        return n
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Fetch repeater database from RepeaterBook")
    parser.add_argument("--states", default=",".join(DEFAULT_STATES),
                        help=f"Comma-separated state codes (default: {','.join(DEFAULT_STATES)})")
    parser.add_argument("--bands",  default=",".join(DEFAULT_BANDS),
                        help=f"Comma-separated bands (default: {','.join(DEFAULT_BANDS)})")
    parser.add_argument("--db", default=str(DB_PATH),
                        help=f"FieldComms SQLite database (default: {DB_PATH})")
    parser.add_argument("--json", default=str(JSON_SNAPSHOT),
                        help=f"Optional JSON snapshot path (default: {JSON_SNAPSHOT}); "
                             f"pass empty string to skip")
    parser.add_argument("--token", default=None,
                        help="RepeaterBook API token (or set REPEATERBOOK_TOKEN env var)")
    parser.add_argument("--rate-limit", type=float, default=3.0,
                        help="Seconds between API calls (default: 3.0)")
    args = parser.parse_args()

    token = get_token(args.token)
    if not token:
        print("WARNING: No RepeaterBook API token found.")
        print("  As of 2026 the RepeaterBook API requires an approved token and will")
        print("  reject keyless requests with HTTP 403 Forbidden.")
        print("  Set one with:  export REPEATERBOOK_TOKEN=\"your-token\"")
        print("  Apply at:      https://www.repeaterbook.com/api/token_request.php")
        print("  Alternatively, skip this script and load a RepeaterBook CSV export")
        print("  on the 'Offline File' tab of the Repeater Database page.")
        print("  Continuing anyway (will likely fail)...\n")

    states = [s.strip().upper() for s in args.states.split(",")]
    bands  = [b.strip().lower() for b in args.bands.split(",")]

    all_repeaters = []
    seen_ids = set()
    total_calls = 0
    forbidden = False

    for state in states:
        for band in bands:
            band_code = BAND_MAP.get(band)
            if not band_code:
                print(f"  Unknown band: {band}, skipping")
                continue

            print(f"Fetching {state} / {band}...", end=" ", flush=True)
            try:
                results = fetch_repeaters(state, band_code, token)
                new_count = 0
                for r in results:
                    norm = normalize_repeater(r)
                    # Dedupe on callsign + output frequency (rptr_id no longer returned)
                    key = (norm["callsign"].upper(), norm["output_freq"])
                    if key not in seen_ids:
                        seen_ids.add(key)
                        all_repeaters.append(norm)
                        new_count += 1
                print(f"{new_count} repeaters")
                total_calls += 1
            except urllib.error.HTTPError as e:
                print(f"HTTP {e.code}: {e.reason}")
                if e.code == 403:
                    forbidden = True
            except Exception as e:
                print(f"ERROR: {e}")

            # Polite rate limiting
            if total_calls > 0:
                time.sleep(args.rate_limit)

    if forbidden and not all_repeaters:
        print("\nAll requests returned 403 Forbidden.")
        print("This almost always means a missing or invalid RepeaterBook API token.")
        print("See the instructions at the top of this script, or use the Offline File")
        print("method (RepeaterBook CSV export) which needs no token.")
        sys.exit(2)

    if not all_repeaters:
        print("\nNo repeaters fetched — nothing to write. Database left unchanged.")
        sys.exit(1)

    # Sort by state, then callsign
    all_repeaters.sort(key=lambda r: (r["state"], r["callsign"]))

    # Write into the FieldComms database (the source the web UI reads).
    try:
        total = write_to_db(all_repeaters, args.db)
        print(f"\nWrote {len(all_repeaters)} repeaters to database: {args.db}")
        print(f"Repeaters table now has {total} rows total.")
    except Exception as e:
        print(f"\nERROR writing to database: {e}")
        sys.exit(3)

    # Also keep a JSON snapshot for backup / portability.
    if args.json:
        out_path = Path(args.json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(all_repeaters, indent=2))
        print(f"JSON snapshot saved to {out_path}")

    print(f"States: {', '.join(states)}  ·  Bands: {', '.join(bands)}")

if __name__ == "__main__":
    main()
