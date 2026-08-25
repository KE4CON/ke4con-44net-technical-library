#!/usr/bin/env python3
"""
FieldComms — Operator WiFi Access Cards Generator
Generates Avery 5371-compatible business card sheets (10 cards/sheet, 3.5"x2")
One card per roster member. Cards contain:
  - ESV logo + org name
  - Operator name + callsign
  - WiFi network name + password
  - FieldComms URL
  - QR-code-friendly short URL reminder

Usage:
  python3 gen_operator_cards.py                         # all members, default WiFi
  python3 gen_operator_cards.py --ssid EMCOMM-NET --password ares2026
  python3 gen_operator_cards.py --csv roster.csv --out cards.pdf
  python3 gen_operator_cards.py --demo                  # 10 demo cards

Input can be:
  - SQLite DB (auto-detected if /opt/fieldcomms/data/fieldcomms.db exists)
  - CSV file  (--csv path/to/roster.csv)
  - Demo mode (--demo)
"""

import sys, argparse, sqlite3, csv, os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# ── Config ────────────────────────────────────────────────────────────────────
EOC      = HexColor('#1a3a6b')
EOC_LT   = HexColor('#2d6ab4')
GOLD     = HexColor('#f0c040')
PANEL_BG = HexColor('#eef2f7')
LINE     = HexColor('#b0c4dc')
MUTED    = HexColor('#4a6080')

ORG_SHORT = 'MCESV/MCEMA'
ORG_FULL  = 'McHenry County Emergency Services Volunteers and McHenry County Emergency Management Agency'
CALLSIGN  = 'K9ESV'
FC_URL    = '192.168.50.1'

# Avery 5371 / 5874 / 8371 dimensions
PAGE_W, PAGE_H = letter
CARD_W  = 3.5  * inch
CARD_H  = 2.0  * inch
COLS    = 2
ROWS    = 5
LEFT_M  = (PAGE_W - COLS * CARD_W) / 2   # 0.75"
TOP_M   = (PAGE_H - ROWS * CARD_H) / 2   # 0.5"

LOGO_PATH = str(Path(__file__).parent.parent / 'html' / 'esv-logo.png')
if not Path(LOGO_PATH).exists():
    LOGO_PATH = str(Path('/home/claude/esv-logo.png'))


# ── Draw one card ─────────────────────────────────────────────────────────────
def draw_card(c: canvas.Canvas, x: float, y: float, member: dict,
              ssid: str, password: str):
    """
    Draw a single 3.5" x 2" operator card at canvas position (x, y).
    y is the BOTTOM of the card (ReportLab origin = bottom-left).
    """
    # ── Card background ───────────────────────────────────────────────────────
    c.setFillColor(white)
    c.rect(x, y, CARD_W, CARD_H, fill=1, stroke=0)

    # ── Top bar (EOC blue) ────────────────────────────────────────────────────
    BAR_H = 0.45 * inch
    c.setFillColor(EOC)
    c.rect(x, y + CARD_H - BAR_H, CARD_W, BAR_H, fill=1, stroke=0)
    # Gold accent line
    c.setFillColor(GOLD)
    c.rect(x, y + CARD_H - BAR_H - 0.018*inch, CARD_W, 0.018*inch, fill=1, stroke=0)

    # Logo in top bar
    LOGO_W = 1.0 * inch
    LOGO_H = 0.38 * inch
    if Path(LOGO_PATH).exists():
        try:
            c.drawImage(LOGO_PATH, x + 0.08*inch,
                        y + CARD_H - BAR_H + 0.035*inch,
                        width=LOGO_W, height=LOGO_H,
                        preserveAspectRatio=True, anchor='sw', mask='auto')
        except Exception:
            pass

    # Org name in top bar (right of logo)
    c.setFillColor(white)
    c.setFont('Helvetica-Bold', 6.5)
    c.drawString(x + LOGO_W + 0.14*inch, y + CARD_H - 0.19*inch, ORG_SHORT)
    c.setFont('Helvetica', 5.5)
    c.setFillColor(HexColor('#c0d4f0'))
    c.drawString(x + LOGO_W + 0.14*inch, y + CARD_H - 0.30*inch,
                 f'EmComm Field Server · {CALLSIGN}')

    # ── Operator name block ───────────────────────────────────────────────────
    name = member.get('name', '').strip()
    if not name:
        name = f"{member.get('first_name','').strip()} {member.get('last_name','').strip()}".strip()
    callsign  = (member.get('callsign') or '').upper().strip()
    member_id = (member.get('member_id') or '').upper().strip()
    radio_id  = (member.get('radio_id')  or '').strip()
    role      = (member.get('role') or 'Operator').strip()
    is_ham    = bool(callsign)

    # ── Primary identifier line ──────────────────────────────────────────
    # Ham: callsign (large, blue)   Non-ham: member_id (large, purple)
    primary_id = callsign if is_ham else (member_id or radio_id or 'GUEST')
    id_color   = EOC if is_ham else HexColor('#5b2d8c')
    id_font_sz = 16 if len(primary_id) <= 8 else 12

    c.setFillColor(id_color)
    c.setFont('Helvetica-Bold', id_font_sz)
    c.drawString(x + 0.12*inch, y + CARD_H - BAR_H - 0.30*inch, primary_id)

    # ── Secondary identifier line ─────────────────────────────────────────
    # Always show ESV Member ID + Starcom Radio ID on one small line
    sec_parts = []
    if member_id and (not is_ham or member_id != primary_id):
        sec_parts.append(f'ESV {member_id}')
    if radio_id:
        sec_parts.append(f'Radio {radio_id}')
    if sec_parts:
        c.setFillColor(MUTED)
        c.setFont('Helvetica', 6.5)
        c.drawString(x + 0.12*inch, y + CARD_H - BAR_H - 0.41*inch,
                     '  ·  '.join(sec_parts))

    # ── Name ──────────────────────────────────────────────────────────────
    c.setFont('Helvetica', 9)
    c.setFillColor(black)
    c.drawString(x + 0.12*inch, y + CARD_H - BAR_H - 0.52*inch, name)

    # ── Role badge ────────────────────────────────────────────────────────
    role_w = c.stringWidth(role, 'Helvetica', 7) + 8
    c.setFillColor(PANEL_BG)
    c.roundRect(x + 0.10*inch, y + CARD_H - BAR_H - 0.66*inch,
                role_w, 0.14*inch, 2, fill=1, stroke=0)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.4)
    c.roundRect(x + 0.10*inch, y + CARD_H - BAR_H - 0.66*inch,
                role_w, 0.14*inch, 2, fill=0, stroke=1)
    c.setFillColor(MUTED)
    c.setFont('Helvetica', 7)
    c.drawString(x + 0.14*inch, y + CARD_H - BAR_H - 0.625*inch, role)

    # ── Divider ───────────────────────────────────────────────────────────────
    c.setStrokeColor(LINE)
    c.setLineWidth(0.4)
    c.line(x + 0.10*inch, y + 0.68*inch, x + CARD_W - 0.10*inch, y + 0.68*inch)

    # ── WiFi / access block ───────────────────────────────────────────────────
    # Label
    c.setFillColor(EOC)
    c.setFont('Helvetica-Bold', 6)
    c.drawString(x + 0.12*inch, y + 0.58*inch, 'EMCOMM-NET ACCESS')

    # WiFi Network
    c.setFillColor(MUTED)
    c.setFont('Helvetica', 6.5)
    c.drawString(x + 0.12*inch, y + 0.46*inch, 'WiFi Network:')
    c.setFillColor(EOC)
    c.setFont('Helvetica-Bold', 7.5)
    c.drawString(x + 0.85*inch, y + 0.46*inch, ssid)

    # Password
    c.setFillColor(MUTED)
    c.setFont('Helvetica', 6.5)
    c.drawString(x + 0.12*inch, y + 0.34*inch, 'Password:')
    c.setFillColor(EOC)
    c.setFont('Helvetica-Bold', 7.5)
    c.drawString(x + 0.85*inch, y + 0.34*inch, password)

    # URL
    c.setFillColor(MUTED)
    c.setFont('Helvetica', 6.5)
    c.drawString(x + 0.12*inch, y + 0.21*inch, 'Dashboard:')
    c.setFillColor(EOC_LT)
    c.setFont('Helvetica-Bold', 7.5)
    c.drawString(x + 0.85*inch, y + 0.21*inch, f'http://{FC_URL}')

    # ── Bottom strip ──────────────────────────────────────────────────────────
    c.setFillColor(EOC)
    c.rect(x, y, CARD_W, 0.10*inch, fill=1, stroke=0)
    c.setFillColor(HexColor('#6080a0'))
    c.setFont('Helvetica', 5)
    c.drawCentredString(x + CARD_W/2, y + 0.025*inch,
                        'Open browser on any device · Connect to WiFi first · No app required')

    # ── Cut guide (light grey border) ────────────────────────────────────────
    c.setStrokeColor(HexColor('#d0d0d0'))
    c.setLineWidth(0.25)
    c.rect(x, y, CARD_W, CARD_H, fill=0, stroke=1)


# ── Load roster from SQLite ───────────────────────────────────────────────────
def load_from_db(db_path: str) -> list:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT member_id, callsign, radio_id, first_name, last_name, role "
        "FROM roster ORDER BY last_name, first_name"
    ).fetchall()
    conn.close()
    members = []
    for r in rows:
        members.append({
            'member_id':  r['member_id'] or '',
            'callsign':   r['callsign']  or '',
            'radio_id':   r['radio_id']  or '',
            'first_name': r['first_name'] or '',
            'last_name':  r['last_name']  or '',
            'name':       f"{r['first_name'] or ''} {r['last_name'] or ''}".strip(),
            'role':       r['role'] or 'Operator',
        })
    return members


# ── Load roster from CSV ──────────────────────────────────────────────────────
def load_from_csv(csv_path: str) -> list:
    members = []
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        # Normalize header names
        for row in reader:
            norm = {k.strip().lower().replace(' ', '_'): v.strip()
                    for k, v in row.items()}
            call = (norm.get('callsign') or norm.get('call_sign') or
                    norm.get('call') or '').upper().strip()
            mid  = (norm.get('member_id') or norm.get('memberid') or
                    norm.get('id') or '').upper().strip()
            rid  = (norm.get('radio_id') or norm.get('radioid') or '').strip()
            # Allow rows that have member_id even without callsign
            if not call and not mid:
                continue
            fn = norm.get('first_name') or norm.get('firstname') or ''
            ln = norm.get('last_name')  or norm.get('lastname')  or ''
            name = (norm.get('name') or f"{fn} {ln}").strip()
            role = (norm.get('role') or 'Operator').strip()
            members.append({'member_id': mid, 'callsign': call, 'radio_id': rid,
                           'first_name': fn, 'last_name': ln,
                           'name': name, 'role': role})
    members.sort(key=lambda m: (m.get('last_name',''), m.get('first_name','')))
    return members


# ── Demo members ──────────────────────────────────────────────────────────────
DEMO_MEMBERS = [
    # Amateur operators (have callsigns)
    {'member_id':'ESV-001','callsign':'K9ESV',  'radio_id':'1001','first_name':'Jim',        'last_name':'Anderson',
     'name':'Jim Anderson',       'role':'Emergency Coordinator'},
    {'member_id':'ESV-002','callsign':'W9XYZ',  'radio_id':'1002','first_name':'Sarah',      'last_name':'Mitchell',
     'name':'Sarah Mitchell',     'role':'Net Control Station'},
    {'member_id':'ESV-003','callsign':'KD9ABC', 'radio_id':'1003','first_name':'Robert',     'last_name':'Johnson',
     'name':'Robert Johnson',     'role':'Operator'},
    {'member_id':'ESV-004','callsign':'N9DEF',  'radio_id':'1004','first_name':'Mary',       'last_name':'Williams',
     'name':'Mary Williams',      'role':'Operator'},
    {'member_id':'ESV-005','callsign':'WB9GHI', 'radio_id':'1005','first_name':'David',      'last_name':'Thompson',
     'name':'David Thompson',     'role':'Safety Officer'},
    # Non-amateur ESV members (member_id only — no callsign)
    {'member_id':'ESV-006','callsign':'',       'first_name':'Jennifer',   'last_name':'Davis',
     'name':'Jennifer Davis',     'role':'Logistics Support', 'radio_id':'1042'},
    {'member_id':'ESV-007','callsign':'',       'first_name':'Michael',    'last_name':'Garcia',
     'name':'Michael Garcia',     'role':'Medical Support',   'radio_id':'1087'},
    {'member_id':'ESV-008','callsign':'KA9JKL', 'radio_id':'1008','first_name':'Lisa',       'last_name':'Martinez',
     'name':'Lisa Martinez',      'role':'Planning Section Chief'},
    {'member_id':'ESV-009','callsign':'',       'first_name':'Christopher','last_name':'Lee',
     'name':'Christopher Lee',    'role':'CERT Member',       'radio_id':'2201'},
    {'member_id':'ESV-010','callsign':'N9VWX',  'radio_id':'1010','first_name':'Amanda',     'last_name':'Wilson',
     'name':'Amanda Wilson',      'role':'Operator'},
]


# ── Generate PDF ──────────────────────────────────────────────────────────────
def generate_cards(members: list, output: str, ssid: str, password: str):
    c = canvas.Canvas(output, pagesize=letter)
    c.setTitle(f'{ORG_FULL} — Operator Access Cards')
    c.setAuthor(ORG_FULL)

    print(f'Generating {len(members)} operator cards...')

    for i, member in enumerate(members):
        pos_on_page = i % (COLS * ROWS)

        # New page at start of each sheet
        if pos_on_page == 0 and i > 0:
            c.showPage()

        col = pos_on_page % COLS
        row = pos_on_page // COLS

        # Card origin (bottom-left corner)
        x = LEFT_M + col * CARD_W
        # ReportLab: y=0 at bottom. Row 0 = top of page.
        y = PAGE_H - TOP_M - (row + 1) * CARD_H

        draw_card(c, x, y, member, ssid, password)

        if (i + 1) % 10 == 0:
            print(f'  {i+1}/{len(members)} cards...')

    c.save()
    print(f'Done: {output}  ({len(members)} cards, '
          f'{(len(members)-1)//(COLS*ROWS)+1} sheet(s))')


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description='Generate FieldComms operator access cards')
    p.add_argument('--ssid',     default='EMCOMM-NET',    help='WiFi network name')
    p.add_argument('--password', default='fieldcomms2026', help='WiFi password')
    p.add_argument('--csv',      default=None,             help='CSV roster file')
    p.add_argument('--db',       default=None,             help='SQLite DB path')
    p.add_argument('--out',      default='operator_cards.pdf', help='Output PDF path')
    p.add_argument('--demo',     action='store_true',      help='Use demo data')
    args = p.parse_args()

    # Load members
    if args.demo:
        members = DEMO_MEMBERS
        print('Using demo roster (10 members)')
    elif args.csv:
        members = load_from_csv(args.csv)
        print(f'Loaded {len(members)} members from {args.csv}')
    elif args.db:
        members = load_from_db(args.db)
        print(f'Loaded {len(members)} members from {args.db}')
    else:
        # Auto-detect DB
        default_db = '/opt/fieldcomms/data/fieldcomms.db'
        if Path(default_db).exists():
            members = load_from_db(default_db)
            print(f'Loaded {len(members)} members from {default_db}')
        else:
            print('No data source found. Using demo data.')
            print('Options: --csv roster.csv  OR  --db fieldcomms.db  OR  --demo')
            members = DEMO_MEMBERS

    if not members:
        print('No members found — nothing to generate.')
        sys.exit(1)

    generate_cards(members, args.out, args.ssid, args.password)


if __name__ == '__main__':
    main()
