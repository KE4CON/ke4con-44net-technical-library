#!/usr/bin/env python3
"""
ics_pdf_downloader.py — FieldComms ICS Forms PDF Downloader
=============================================================
Downloads the official FEMA ICS forms as PDFs from the FEMA website
and stores them in /opt/fieldcomms/data/ics_forms/ for offline use
via the Print Center.

Usage
-----
  # Download all ICS forms
  python3 ics_pdf_downloader.py

  # Download specific forms only
  python3 ics_pdf_downloader.py --forms ICS-201 ICS-202 ICS-213

  # Download to a custom directory
  python3 ics_pdf_downloader.py --output /path/to/dir

  # List available forms without downloading
  python3 ics_pdf_downloader.py --list

  # Force re-download even if file already exists
  python3 ics_pdf_downloader.py --force

  # Check which forms are already downloaded
  python3 ics_pdf_downloader.py --status

K9ESV · McHenry County Emergency Services Volunteers
     and McHenry County Emergency Management Agency (MCESV/MCEMA)
FieldComms Incident Management System v1.0
"""

import sys
import os
import time
import hashlib
import argparse
import json
from pathlib import Path
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# ── ICS Forms catalogue ──────────────────────────────────────────────────────
# URL pattern: FEMA publishes ICS forms at:
# https://training.fema.gov/emiweb/is/icsresource/assets/ICS%20Forms/
# Mirror also available via:
# https://www.dhs.gov/sites/default/files/publications/

FEMA_BASE = 'https://training.fema.gov/emiweb/is/icsresource/assets/ICS%20Forms/'
DHS_BASE  = 'https://www.dhs.gov/sites/default/files/publications/'

ICS_FORMS = [
    # form_id, filename, description, local_name
    ('ICS-201', 'ICS%20Form%20201.pdf',
     'Incident Briefing',
     'ICS-201_Incident_Briefing.pdf'),

    ('ICS-202', 'ICS%20Form%20202.pdf',
     'Incident Objectives',
     'ICS-202_Incident_Objectives.pdf'),

    ('ICS-203', 'ICS%20Form%20203.pdf',
     'Organization Assignment List',
     'ICS-203_Organization_Assignment.pdf'),

    ('ICS-204', 'ICS%20Form%20204.pdf',
     'Assignment List',
     'ICS-204_Assignment_List.pdf'),

    ('ICS-205', 'ICS%20Form%20205.pdf',
     'Incident Radio Communications Plan',
     'ICS-205_Radio_Comms_Plan.pdf'),

    ('ICS-205A', 'ICS%20Form%20205A.pdf',
     'Communications List',
     'ICS-205A_Communications_List.pdf'),

    ('ICS-206', 'ICS%20Form%20206.pdf',
     'Medical Plan',
     'ICS-206_Medical_Plan.pdf'),

    ('ICS-207', 'ICS%20Form%20207.pdf',
     'Incident Organization Chart',
     'ICS-207_Org_Chart.pdf'),

    ('ICS-208', 'ICS%20Form%20208.pdf',
     'Safety Message/Plan',
     'ICS-208_Safety_Message.pdf'),

    ('ICS-209', 'ICS%20Form%20209.pdf',
     'Incident Status Summary',
     'ICS-209_Incident_Status_Summary.pdf'),

    ('ICS-210', 'ICS%20Form%20210.pdf',
     'Resource Status Change',
     'ICS-210_Resource_Status_Change.pdf'),

    ('ICS-211', 'ICS%20Form%20211.pdf',
     'Incident Check-In List',
     'ICS-211_Check_In_List.pdf'),

    ('ICS-213', 'ICS%20Form%20213.pdf',
     'General Message',
     'ICS-213_General_Message.pdf'),

    ('ICS-214', 'ICS%20Form%20214.pdf',
     'Activity Log',
     'ICS-214_Activity_Log.pdf'),

    ('ICS-215', 'ICS%20Form%20215.pdf',
     'Operational Planning Worksheet',
     'ICS-215_Ops_Planning_Worksheet.pdf'),

    ('ICS-215A', 'ICS%20Form%20215A.pdf',
     'Incident Action Plan Safety Analysis',
     'ICS-215A_IAP_Safety_Analysis.pdf'),

    ('ICS-218', 'ICS%20Form%20218.pdf',
     'Support Vehicle/Equipment Inventory',
     'ICS-218_Support_Vehicle_Inventory.pdf'),

    ('ICS-219', 'ICS%20Form%20219.pdf',
     'Resource Status Cards (T-Cards)',
     'ICS-219_T-Cards.pdf'),

    ('ICS-220', 'ICS%20Form%20220.pdf',
     'Air Operations Summary',
     'ICS-220_Air_Ops_Summary.pdf'),

    ('ICS-221', 'ICS%20Form%20221.pdf',
     'Demobilization Check-Out',
     'ICS-221_Demobilization_Checkout.pdf'),

    ('ICS-225', 'ICS%20Form%20225.pdf',
     'Incident Personnel Performance Rating',
     'ICS-225_Personnel_Performance.pdf'),

    ('ICS-309', 'ICS%20Form%20309.pdf',
     'Communications Log',
     'ICS-309_Communications_Log.pdf'),
]

DEFAULT_OUTPUT = Path('/opt/fieldcomms/data/ics_forms')
MANIFEST_FILE  = 'download_manifest.json'
USER_AGENT     = ('Mozilla/5.0 (compatible; FieldComms/1.0; '
                  'MCESV/MCEMA K9ESV EmComm)')

# ── Helpers ──────────────────────────────────────────────────────────────────

def load_manifest(output_dir: Path) -> dict:
    mpath = output_dir / MANIFEST_FILE
    if mpath.exists():
        try:
            return json.loads(mpath.read_text())
        except Exception:
            pass
    return {}


def save_manifest(output_dir: Path, manifest: dict) -> None:
    mpath = output_dir / MANIFEST_FILE
    mpath.write_text(json.dumps(manifest, indent=2))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def download_file(url: str, dest: Path, timeout: int = 30) -> tuple[bool, str]:
    """
    Download url to dest. Returns (success, message).
    """
    req = Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower() and 'octet' not in content_type.lower():
                # Try to read a small chunk to verify it's a PDF (starts with %PDF)
                data = resp.read(8)
                if not data.startswith(b'%PDF'):
                    return False, f'Not a PDF (Content-Type: {content_type})'
                # Read the rest
                data += resp.read()
            else:
                data = resp.read()

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True, f'{len(data):,} bytes'

    except HTTPError as e:
        return False, f'HTTP {e.code}: {e.reason}'
    except URLError as e:
        return False, f'URL error: {e.reason}'
    except Exception as e:
        return False, str(e)


def try_download(form_id: str, filename: str, local_name: str,
                 output_dir: Path, force: bool = False) -> tuple[bool, str]:
    """
    Try to download a form from FEMA, with fallback mirrors.
    Returns (success, message).
    """
    dest = output_dir / local_name

    if dest.exists() and not force:
        return True, f'Already exists ({dest.stat().st_size:,} bytes)'

    # Try primary URL
    primary_url = FEMA_BASE + filename
    ok, msg = download_file(primary_url, dest)
    if ok:
        return True, f'Downloaded from FEMA: {msg}'

    # Fallback: try alternate URL formats
    alt_filename = filename.replace('%20', '_')
    alt_url = FEMA_BASE + alt_filename
    ok, msg = download_file(alt_url, dest)
    if ok:
        return True, f'Downloaded (alt URL): {msg}'

    return False, f'Failed from all sources. Last error: {msg}'


# ── Actions ───────────────────────────────────────────────────────────────────

def action_list() -> None:
    print(f'{"Form ID":<12} {"Description":<45} Local filename')
    print('─' * 100)
    for form_id, _, desc, local in ICS_FORMS:
        print(f'{form_id:<12} {desc:<45} {local}')
    print(f'\n{len(ICS_FORMS)} forms available.')


def action_status(output_dir: Path) -> None:
    manifest = load_manifest(output_dir)
    print(f'{"Form ID":<12} {"Status":<12} {"Size":<12} Downloaded')
    print('─' * 70)
    found = 0
    for form_id, _, desc, local in ICS_FORMS:
        dest = output_dir / local
        if dest.exists():
            size = f'{dest.stat().st_size:,}'
            ts   = manifest.get(form_id, {}).get('downloaded', 'unknown')
            print(f'{form_id:<12} {"✓ Present":<12} {size:<12} {ts}')
            found += 1
        else:
            print(f'{form_id:<12} {"✗ Missing":<12}')
    print(f'\n{found}/{len(ICS_FORMS)} forms downloaded to {output_dir}')


def action_download(output_dir: Path, form_filter: list[str] | None,
                    force: bool) -> int:
    """
    Download forms. Returns count of failures.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(output_dir)

    # Filter forms if requested
    forms = ICS_FORMS
    if form_filter:
        filter_upper = [f.upper() for f in form_filter]
        forms = [f for f in ICS_FORMS if f[0].upper() in filter_upper]
        if not forms:
            print(f'No matching forms found for: {form_filter}')
            return 1

    print(f'Downloading {len(forms)} ICS form(s) to {output_dir}\n')

    failures = 0
    for form_id, filename, desc, local in forms:
        print(f'  {form_id:<10} {desc:<45} ', end='', flush=True)
        ok, msg = try_download(form_id, filename, local, output_dir, force)
        if ok:
            print(f'✓  {msg}')
            manifest[form_id] = {
                'description':  desc,
                'filename':     local,
                'downloaded':   datetime.now().strftime('%Y-%m-%d %H:%M'),
                'size':         (output_dir / local).stat().st_size,
            }
        else:
            print(f'✗  {msg}')
            failures += 1
        time.sleep(0.5)  # Be polite to FEMA servers

    save_manifest(output_dir, manifest)

    print(f'\n{"─"*60}')
    print(f'  Downloaded: {len(forms) - failures}')
    print(f'  Failed:     {failures}')
    print(f'  Location:   {output_dir}')

    if failures:
        print(f'\n  Note: Failed forms can be downloaded manually from:')
        print(f'  {FEMA_BASE}')

    return failures


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Download official FEMA ICS forms PDFs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        '--output', default=str(DEFAULT_OUTPUT),
        help=f'Output directory (default: {DEFAULT_OUTPUT})')
    parser.add_argument(
        '--forms', nargs='+', metavar='FORM_ID',
        help='Download specific forms only (e.g. --forms ICS-201 ICS-213)')
    parser.add_argument(
        '--list', action='store_true',
        help='List all available forms without downloading')
    parser.add_argument(
        '--status', action='store_true',
        help='Show download status of all forms')
    parser.add_argument(
        '--force', action='store_true',
        help='Re-download even if file already exists')
    args = parser.parse_args()

    output_dir = Path(args.output)

    if args.list:
        action_list()
        return

    if args.status:
        action_status(output_dir)
        return

    failures = action_download(output_dir, args.forms, args.force)
    sys.exit(0 if failures == 0 else 1)


if __name__ == '__main__':
    main()
