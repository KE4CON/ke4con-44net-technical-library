#!/usr/bin/env python3
"""
gen_user_guide.py — McHenry County RACES/ARES/Starcom FieldComms User Guide
A section-per-tool reference guide covering all 35 tool pages.
Output: /mnt/user-data/outputs/McHenry_County_RACES_ARES_Starcom_FieldComms_User_Guide.pdf
"""
import datetime, io, os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, HRFlowable, KeepTogether)
from reportlab.pdfgen import canvas

# ── Palette ──────────────────────────────────────────────────────────────────
EOC    = HexColor('#1a3a6b')
EOC_LT = HexColor('#2d6ab4')
EOC_BG = HexColor('#eef2f7')
GOLD   = HexColor('#f0c040')
LINE   = HexColor('#c0cfe0')
LGRAY  = HexColor('#f0f3f6')
GREEN  = HexColor('#1a7a3a')
AMBER  = HexColor('#c8760a')
AMBER_BG = HexColor('#fef3d8')
RED    = HexColor('#b82020')
PURPLE = HexColor('#5b2d8c')
MUTED  = HexColor('#4a6080')

ORG    = ('McHenry County Emergency Services Volunteers and '
          'McHenry County Emergency Management Agency')
SHORT  = 'MCESV/MCEMA  ·  K9ESV  ·  RACES/ARES/Starcom'
TODAY  = datetime.date.today().strftime('%B %d, %Y')
PAGE_W, PAGE_H = letter
M  = 0.65*inch
CW = PAGE_W - 2*M

# ── Canvas ────────────────────────────────────────────────────────────────────
class NC(canvas.Canvas):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._saved = []
    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()
    def save(self):
        total = len(self._saved)
        for st in self._saved:
            self.__dict__.update(st)
            self.TOTAL = total
            n = self._pageNumber
            if n == 1:
                self._draw_cover()
            elif n > 1:
                self.setFillColor(EOC)
                self.rect(0, PAGE_H-0.40*inch, PAGE_W, 0.40*inch, fill=1, stroke=0)
                self.setFillColor(GOLD)
                self.rect(0, PAGE_H-0.42*inch, PAGE_W, 0.02*inch, fill=1, stroke=0)
                self.setFillColor(white)
                self.setFont('Helvetica-Bold', 8)
                self.drawString(M, PAGE_H-0.22*inch,
                    'McHenry County RACES/ARES/Starcom')
                self.setFont('Helvetica', 7.5)
                self.drawRightString(PAGE_W-M, PAGE_H-0.22*inch,
                    'FieldComms EmComm Field Server v1.0 — User Guide')
            self.setFillColor(EOC)
            self.rect(0, 0, PAGE_W, 0.32*inch, fill=1, stroke=0)
            self.setFillColor(GOLD)
            self.rect(0, 0.32*inch, PAGE_W, 0.015*inch, fill=1, stroke=0)
            self.setFillColor(white)
            self.setFont('Helvetica', 6.5)
            if n > 1:
                self.drawString(M, 0.11*inch,
                    f'Amateur Radio Emergency Communications  ·  © 2026 KE4CON / MCESV K9ESV  ·  CC BY-SA 4.0')
                self.drawRightString(PAGE_W-M, 0.11*inch,
                    f'Page {n} of {total}')
            super().showPage()
        super().save()
    def _draw_cover(self):
        """Full-page canvas-drawn cover."""
        self.setFillColor(HexColor('#1a3a6b'))
        self.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        self.setFillColor(HexColor('#f0c040'))
        self.rect(0, PAGE_H - 0.18*inch, PAGE_W, 0.18*inch, fill=1, stroke=0)
        self.setFillColor(HexColor('#f0c040'))
        self.rect(0, 0, PAGE_W, 0.18*inch, fill=1, stroke=0)
        self.setFillColor(HexColor('#1e4480'))
        self.rect(0, PAGE_H*0.38, PAGE_W, PAGE_H*0.36, fill=1, stroke=0)
        self.setFillColor(HexColor('#f0c040'))
        self.setFont('Helvetica-Bold', 10)
        self.drawCentredString(PAGE_W/2, PAGE_H - 0.70*inch,
            'K9ESV  ·  McHenry County Emergency Services Volunteers')
        self.setFillColor(HexColor('#c0d4f0'))
        self.setFont('Helvetica', 9)
        self.drawCentredString(PAGE_W/2, PAGE_H - 0.88*inch,
            'and McHenry County Emergency Management Agency')
        self.setFillColor(HexColor('#ffffff'))
        self.setFont('Helvetica-Bold', 58)
        self.drawCentredString(PAGE_W/2, PAGE_H*0.60, 'FIELDCOMMS')
        self.setFillColor(HexColor('#f0c040'))
        self.setFont('Helvetica-Bold', 15)
        self.drawCentredString(PAGE_W/2, PAGE_H*0.545,
            'Incident Management System  v1.0')
        self.setStrokeColor(HexColor('#f0c040'))
        self.setLineWidth(1.5)
        self.line(M*2, PAGE_H*0.505, PAGE_W - M*2, PAGE_H*0.505)
        self.setFillColor(HexColor('#ffffff'))
        self.setFont('Helvetica-Bold', 26)
        self.drawCentredString(PAGE_W/2, PAGE_H*0.448, 'USER GUIDE')
        self.setFillColor(HexColor('#c0d4f0'))
        self.setFont('Helvetica', 10)
        self.drawCentredString(PAGE_W/2, PAGE_H*0.395, 'McHenry County RACES, ARES & Starcom')
        self.setFillColor(HexColor('#8090c0'))
        self.setFont('Helvetica', 9.5)
        self.drawCentredString(PAGE_W/2, PAGE_H*0.30,
            'RACES  ·  ARES  ·  Starcom  ·  K9ESV  ·  MCESV / MCEMA')
        self.setFillColor(HexColor('#6070a0'))
        self.setFont('Helvetica', 9)
        self.drawCentredString(PAGE_W/2, PAGE_H*0.25, TODAY)
        self.setFillColor(HexColor('#1a3a6b'))
        self.setFont('Helvetica', 7)
        self.drawCentredString(PAGE_W/2, 0.05*inch,
            f'FieldComms IMS v1.0  ·  MCESV/MCEMA  ·  {TODAY}')


# ── Style helpers ─────────────────────────────────────────────────────────────
def S(name, **kw):
    d = dict(fontName='Helvetica', fontSize=9, textColor=black,
             leading=12, spaceAfter=0, spaceBefore=0)
    d.update(kw)
    return ParagraphStyle(name, **d)

def P(t, s=None):  return Paragraph(t, s or S('b'))
def SP(n=4):       return Spacer(1, n)
def PB():          return PageBreak()
def HR(c=LINE, t=0.4):
    return HRFlowable(width='100%', thickness=t, color=c, spaceBefore=2, spaceAfter=2)

def SB(num, title, url=''):
    """Section banner."""
    inner = Table([[
        P(str(num), S('sn', fontName='Helvetica-Bold', fontSize=18,
                       textColor=GOLD, leading=22, alignment=TA_CENTER)),
        Table([[
            P(title, S('st', fontName='Helvetica-Bold', fontSize=14,
                        textColor=white, leading=18)),
            P(url,   S('su', fontName='Courier', fontSize=7.5,
                        textColor=HexColor('#b0c8e8'), leading=10)),
        ]], colWidths=[CW-0.7*inch]),
    ]], colWidths=[0.7*inch, CW-0.7*inch])
    inner.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), EOC),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('RIGHTPADDING',  (0,0), (-1,-1), 8),
        ('TOPPADDING',    (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LINEBELOW',     (0,0), (-1,-1), 2, GOLD),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ]))
    return inner

def tbl(data, widths):
    rows = []
    for i, row in enumerate(data):
        fs = 8 if i == 0 else 8.5
        ld = 10 if i == 0 else 12
        rows.append([P(str(c), S('TH' if i==0 else 'TC',
                                  fontName='Helvetica-Bold' if i==0 else 'Helvetica',
                                  fontSize=fs, textColor=white if i==0 else black,
                                  leading=ld)) for c in row])
    t = Table(rows, colWidths=widths, repeatRows=1, splitByRow=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  EOC),
        ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [white, LGRAY]),
        ('GRID',          (0,0), (-1,-1), 0.3, LINE),
        ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING',   (0,0), (-1,-1), 7),
        ('RIGHTPADDING',  (0,0), (-1,-1), 7),
    ]))
    return t

def B(text, bold=False):
    fn = 'Helvetica-Bold' if bold else 'Helvetica'
    return P(f'• {text}', S('bl', fontName=fn, fontSize=9, leading=12,
                             leftIndent=12, firstLineIndent=-8))

def TipBox(text, kind='tip'):
    cfg = {'tip': (EOC_LT, EOC_BG, '💡'), 'warn': (AMBER, AMBER_BG, '⚠'), 'note': (EOC_LT, EOC_BG, '📝')}
    c, bg, icon = cfg[kind]
    t = Table([[
        P(icon, S('ti', fontSize=10, textColor=c, leading=12)),
        P(text, S('tt', fontSize=8.5, leading=12)),
    ]], colWidths=[0.25*inch, CW-0.25*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,-1), bg),
        ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING',  (0,0), (-1,-1), 5), ('BOTTOMPADDING',(0,0), (-1,-1), 5),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ('LINEAFTER',   (0,0), (0,-1),  1.5, c),
    ]))
    return t

def H2(text): return P(text, S('h2', fontName='Helvetica-Bold', fontSize=10,
                                 textColor=EOC_LT, leading=13, spaceBefore=6, spaceAfter=3))

# ══════════════════════════════════════════════════════════════════════════════
story = []

# ── COVER ─────────────────────────────────────────────────────────────────────
story.append(SP(40))
cov = Table([[Table([[
    P('McHenry County', S('c1', fontName='Helvetica-Bold', fontSize=18,
                           textColor=GOLD, alignment=TA_CENTER, leading=22)),
    P('RACES / ARES / Starcom', S('c2', fontName='Helvetica', fontSize=12,
                                   textColor=HexColor('#c0d4f0'), alignment=TA_CENTER, leading=16)),
    SP(10),
    P('FieldComms IMS v1.0', S('c3', fontName='Helvetica-Bold', fontSize=26,
                                 textColor=white, alignment=TA_CENTER, leading=30)),
    SP(4),
    P('User Guide', S('c4', fontName='Helvetica-Bold', fontSize=20,
                       textColor=GOLD, alignment=TA_CENTER, leading=24)),
    SP(12),
    HR(GOLD, 0.5),
    SP(8),
    P('EmComm Field Server v1.0', S('c5', fontName='Helvetica', fontSize=11,
                                     textColor=HexColor('#c0d4f0'), alignment=TA_CENTER, leading=14)),
    SP(4),
    P('http://192.168.50.1  ·  EMCOMM-NET', S('c6', fontName='Courier', fontSize=10,
                                                textColor=HexColor('#8090b0'), alignment=TA_CENTER, leading=13)),
    SP(16),
    P(f'MCESV/MCEMA  ·  K9ESV  ·  {TODAY}',
      S('c7', fontName='Helvetica', fontSize=8.5,
        textColor=HexColor('#6070a0'), alignment=TA_CENTER, leading=12)),
]], colWidths=[CW])]], colWidths=[CW])
cov.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), EOC),
    ('TOPPADDING', (0,0), (-1,-1), 40), ('BOTTOMPADDING', (0,0), (-1,-1), 40),
    ('LEFTPADDING', (0,0), (-1,-1), 30), ('RIGHTPADDING', (0,0), (-1,-1), 30),
]))
story.append(cov)
story.append(PB())

# ── TOC ───────────────────────────────────────────────────────────────────────
toc_hdr = Table([[P('Table of Contents',
    S('th', fontName='Helvetica-Bold', fontSize=18, textColor=EOC, leading=22))]],
    colWidths=[CW])
toc_hdr.setStyle(TableStyle([
    ('LINEBELOW', (0,0), (-1,-1), 2, GOLD),
    ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 8),
]))
story.append(toc_hdr)
story.append(SP(8))

TOC_ENTRIES = [
    (1,'Getting Started','/'), (2,'Main Dashboard','/'), (3,'Amateur Net Control','/netcontrol.html'),
    (4,'Starcom Net Logger','/starcom.html'), (5,'Net Observer','/observer.html'),
    (6,'Member Roster','/roster.html'), (7,'Resource Board','/resources.html'),
    (8,'Tactical APRS Map','/tactical.html'), (9,'Starcom Resource Map','/resmap.html'),
    (10,'FCC Callsign Lookup','/callsign.html'), (11,"Dead Man's Switch",'/deadmans.html'),
    (12,'Pre-Flight Checklist','/preflight.html'), (13,'ICS Platform — Overview','/ics/'),
    (14,'ICS Command','/ics/command.html'), (15,'ICS Operations','/ics/operations.html'),
    (16,'ICS Planning','/ics/planning.html'), (17,'ICS Logistics','/ics/logistics.html'),
    (18,'ICS Finance / Admin','/ics/finance.html'), (19,'NTS Radiogram','/nts.html'),
    (20,'ICS-213 General Message','/ics213.html'), (21,'ICS-309 Comms Log','/ics309.html'),
    (22,'HF Propagation','/propagation.html'), (23,'Repeater Database','/repeaters.html'),
    (24,'Facilities Directory','/facilities.html'), (25,'Grid Square Calculator','/grid.html'),
    (26,'Radio Cheat Sheets','/cheatsheets.html'), (27,'Print Center','/printcenter.html'),
    (28,'Kiwix Offline Library',':8081/'), (29,'Health Monitor',':5051/health'),
    (30,'Quick Reference & Tips','/'), (31,'Reference Library','/refs.html'),
    (32,'Winlink Form Import','/winlink-import.html'), (33,'JS8Call','/'),
    (34,'ICS Planning P','/ics/planningp.html'), (35,'Operator Access Cards','/printcenter.html'),
    (36,'Network — EMCOMM-NET & AiMesh','/'),
    (36.1,'WAN Connectivity — InstyConnect & Starlink','/wan-status.html'),
    (36.2,'AMPRNet / 44Net Gateway','http://192.168.50.2:9000'),
    (37,'Printer Setup',':631'),
]

for num, title, url in TOC_ENTRIES:
    row = Table([[
        P(str(num), S('tn', fontName='Helvetica-Bold', fontSize=8.5,
                       textColor=EOC_LT, alignment=TA_CENTER, leading=11)),
        P(title, S('tt', fontSize=8.5, leading=11)),
        P(url, S('tu', fontName='Courier', fontSize=7.5,
                  textColor=MUTED, leading=11)),
    ]], colWidths=[0.35*inch, CW*0.55, CW*0.42])
    row.setStyle(TableStyle([
        ('LINEBELOW',     (0,0), (-1,-1), 0.2, LINE),
        ('TOPPADDING',    (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING',   (0,0), (-1,-1), 3), ('RIGHTPADDING',  (0,0), (-1,-1), 3),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(row)

story.append(PB())

# ── SECTIONS ──────────────────────────────────────────────────────────────────

# Section 1 — Getting Started
story += [SB(1,'Getting Started — Connecting to FieldComms','http://192.168.50.1/'), SP(8)]
story.append(P(
    'FieldComms is a self-contained emergency communications server running on two Raspberry Pi 5 units. '
    'The primary Pi runs all 32 web tools and 15 background services. '
    'A second Pi at 192.168.50.2 serves as the dedicated AMPRNet / 44Net WireGuard gateway. '
    'Three ASUS RT-BE58 Go Wi-Fi 7 routers form the EMCOMM-NET access point: '
    'one primary router managing WAN connectivity and DHCP, and two AiMesh nodes extending '
    'coverage to secondary rooms and outdoor areas. '
    'InstyConnect cellular (T-Mobile and Verizon) is the primary internet source. '
    'Starlink satellite provides automatic failover when cellular drops. '
    'Any smartphone, tablet, or laptop on EMCOMM-NET reaches the full dashboard at '
    'http://192.168.50.1 in under a minute — no app, no login, no internet required.'))
story.append(SP(6))
story.append(tbl([['FIELD','VALUE'],['Wi-Fi Network Name (SSID)','EMCOMM-NET'],
    ['Password','Provided by your net manager'],['Security','WPA2'],
    ['Your device will receive IP','192.168.50.100 – 192.168.50.200']],
    [2.0*inch, CW-2.0*inch]))
story.append(SP(6))
story.append(P('<b>Step 2 — Open the Dashboard</b>', S('h2b', fontName='Helvetica-Bold', fontSize=10, textColor=EOC_LT, leading=13)))
story.append(P('Open any web browser and go to: <b>http://192.168.50.1</b>'))
story.append(SP(4))
story.append(P('<b>Step 3 — Identify Yourself</b>', S('h2b', fontName='Helvetica-Bold', fontSize=10, textColor=EOC_LT, leading=13)))
story.append(P('Enter your callsign, Radio ID, or name when prompted. '
               'Your identity is saved by your browser and remembered between sessions.'))
story.append(PB())

# Section 2 — Main Dashboard
story += [SB(2,'Main Dashboard','http://192.168.50.1/'), SP(8)]
story.append(P(
    'The dashboard at http://192.168.50.1 is your central hub for every activation. '
    'It shows live NWS weather alerts color-coded by severity, a real-time APRS station table '
    'fed by Graywolf and YAAC, system health indicators, Dead Man Switch state for any active net, '
    'and quick-launch cards for every tool in the system. '
    'Select a mode from the three-button mode bar to reorganize the cards for the task at hand.'))
story.append(SP(6))
story.append(H2('Three Dashboard Modes'))
story.append(tbl([['MODE','BUTTON','TOOLS AVAILABLE'],
    ['Amateur Radio','📻','Net Control Logger, Observer Mode, Callsign Lookup, JS8Call, APRS Tactical Map, HF Propagation, Repeaters, Grid Square, NTS Radiogram, ICS-213, ICS-214, Dead Man\'s Switch, Roster, Pre-Flight, Cheat Sheets, Print Center, Reference Library, WAN Status, AMPRNet Gateway'],
    ['Starcom / Public Safety','🚔','Starcom Net Logger, Weather Net, SAR Net, Observer Mode, Resource Tracking Map, Resource Board, Member Roster, Facilities, ICS Platform, ICS-213, ICS-214, Print Center, WAN Status, AMPRNet Gateway'],
    ['ICS / Incident Command','🏛','ICS Platform (all five sections + Planning P), Tactical Map, Resource Map, Resource Board, Roster, Facilities, ICS forms, Winlink Import, Repeaters, Cheat Sheets, WAN Status, AMPRNet Gateway'],
    ],
    [1.2*inch, 0.5*inch, CW-1.7*inch]))
story.append(SP(6))
story.append(H2('Connectivity Status Cards'))
story.append(P(
    'Two live connectivity cards appear at the bottom of every dashboard mode:'))
story.append(SP(4))
story.append(tbl([['CARD','COLOR','SHOWS','LINKS TO'],
    ['WAN Status',
     'Green = cellular  Blue = satellite  Red = offline',
     'Active WAN source (InstyConnect or Starlink), carrier, and signal. Updates every 30 seconds.',
     '/wan-status.html — full WAN dashboard with signal strength, latency, connectivity tests, and event log'],
    ['AMPRNet Gateway',
     'Green = tunnel UP  Red = tunnel DOWN',
     'WireGuard tunnel state, 44.x.x.x address. Updates every 30 seconds from gateway Pi.',
     'http://192.168.50.2:9000 — gateway dashboard (requires FCC callsign login)'],
    ], [1.0*inch, 1.5*inch, 1.8*inch, CW-4.3*inch]))
story.append(PB())

# Section 3 — Amateur Net Control
story += [SB(3,'Amateur Net Control Logger','http://192.168.50.1/netcontrol.html'), SP(8)]
story.append(P(
    'The Amateur Net Control Logger is the primary tool for running ARES/RACES nets. '
    'Type a callsign and press Enter — FieldComms looks it up in the local FCC database instantly '
    'and fills the operator name and license class automatically. '
    'Every check-in is timestamped in UTC and saved to the server. '
    'Served-agency staff and EOC observers can watch the live log in Observer Mode '
    'without touching the net control interface.'))
story.append(SP(6))
story.append(H2('Starting a Net'))
for i, step in enumerate([
    'Click <b>[+ New Net]</b>',
    'Enter Net Name → e.g. "McHenry County ARES Thursday Evening Net"',
    'Enter Frequency → e.g. "147.015 MHz / 107.2 Hz"',
    'Enter Net Control → your callsign',
    'Click <b>[Activate Net]</b> → The net is now live',
], 1):
    story.append(P(f'<b>{i}.</b>  {step}', S('bl', fontSize=9, leading=12, leftIndent=14, firstLineIndent=-10)))
story.append(SP(6))
story.append(H2('Net Control Features'))
for feat in [
    '<b>FCC Auto-Fill</b> — Type any US amateur callsign — name and location fill automatically from the local FCC database. No internet required.',
    '<b>Multiple Nets</b> — Run several nets simultaneously. Each has its own log, frequency, and NCS.',
    '<b>Observer Link</b> — Copy a read-only URL for served-agency staff or EOC viewers.',
    '<b>ICS-309 Export</b> — Export the complete net log as a formatted ICS-309 Communications Log.',
    '<b>Roster Chips</b> — Quick-tap chips for known stations. Tap to instantly log a check-in.',
]:
    story.append(B(feat))
story.append(PB())

# Section 4 — Starcom Net Logger
story += [SB(4,'Starcom Net Logger','http://192.168.50.1/starcom.html'), SP(8)]
story.append(P('Purpose-built for public safety Starcom radio net logging. Identifies units by Radio ID '
               'and unit number rather than amateur callsigns, uses the sc- prefix convention for net names.'))
story.append(SP(6))
story.append(tbl([['FEATURE','AMATEUR NET CONTROL','STARCOM LOGGER'],
    ['Unit identification','FCC Callsign (e.g. W9XYZ)','Radio ID / Unit number (e.g. 1234)'],
    ['Net name prefix','Free form','sc- prefix (e.g. sc-McHenry-TAC1)'],
    ['ID lookup','FCC database auto-fill','Unit name / callsign manual entry'],
    ['Dispatch field','Not applicable','Dispatch center name field included'],
    ['Export format','ICS-309','ICS-309 (Starcom header)'],
    ],
    [1.5*inch, 1.7*inch, CW-3.2*inch]))
story.append(SP(4))
story.append(TipBox('Starcom nets are distinguished from amateur nets by the sc- prefix. '
                    'Keep this prefix on all Starcom net names.'))
story.append(PB())

# Section 5 — Net Observer
story += [SB(5,'Net Observer (Read-Only View)','http://192.168.50.1/observer.html'), SP(8)]
story.append(P('Provides a read-only, auto-refreshing view of any active net. Share the link with served agency '
               'personnel, EOC staff, or section leaders who need to monitor traffic without touching '
               'the net control interface. No login required.'))
story.append(SP(4))
story.append(TipBox('The net name is passed in the URL: http://192.168.50.1/observer.html?net=Thursday-Net '
                    '— The page refreshes automatically every 15 seconds. Bookmark it for quick access.'))
story.append(PB())

# Section 6 — Member Roster
story += [SB(6,'Member Roster','http://192.168.50.1/roster.html'), SP(8)]
story.append(P('The authoritative directory for McHenry County RACES/ARES/Starcom personnel. '
               'Tracks certifications, equipment capabilities, contact information, and deployment activations.'))
story.append(SP(6))
story.append(tbl([['TAB','CONTENTS'],
    ['Directory','Full member list with callsign, name, role, phone, email, grid square, certification dots, and equipment badges.'],
    ['Certifications','ICS-100/200/300/400/700/800, EmComm I/II, CPR/AED, First Aid, FEMA IS courses — 11 total.'],
    ['Equipment','HF/VHF/UHF radio, Winlink, JS8Call, APRS, generator, antenna, laptop, go-kit — 10 capabilities.'],
    ['Activations','Track which members are deployed, their assigned role, check-in time, and location.'],
    ['Import/Export','Export roster to CSV for backup. Import from CSV to bulk-load members.'],
    ], [1.2*inch, CW-1.2*inch]))
story.append(PB())

# Section 7 — Resource Board
story += [SB(7,'Resource Board','http://192.168.50.1/resources.html'), SP(8)]
story.append(P('Track all personnel, vehicles, and equipment assigned to an activation. '
               'Each resource card shows current status and can be cycled through states with a single click.'))
story.append(SP(6))
story.append(tbl([['STATUS','COLOR','MEANING'],
    ['Available','Green','Resource is on scene and available for assignment'],
    ['Assigned','Amber','Resource is actively tasked with a specific assignment'],
    ['Staging','Blue','Resource is en route or at the staging area, not yet deployed'],
    ['Out of Service','Red','Resource is unavailable — mechanical, medical, or administrative'],
    ['Demobilized','Grey','Resource has been released from the incident'],
    ], [1.2*inch, 0.8*inch, CW-2.0*inch]))
story.append(PB())

# Section 8 — Tactical APRS Map
story += [SB(8,'Tactical APRS Map','http://192.168.50.1/tactical.html'), SP(8)]
story.append(P('Displays live APRS station positions on an interactive Leaflet map. Pulls data from Graywolf '
               'TNC (port 8080) and YAAC (port 8082), merging them into a unified picture. Works completely offline.'))
story.append(SP(6))
story.append(tbl([['SIDEBAR TAB','CONTENTS'],
    ['Stations','All heard APRS stations sorted by most recent. Filter by source or search by callsign. Click any station to pan the map.'],
    ['Messages','Incoming and outgoing APRS messages. Send a message to any callsign via Graywolf or YAAC.'],
    ['Markers','Place manual overlay markers on the map. Add labels, colors, and notes.'],
    ], [1.3*inch, CW-1.3*inch]))
story.append(SP(4))
story.append(TipBox('Click any station icon on the map to see full detail: APRS symbol, type, comment, speed, course, '
                    'altitude, path, and last-heard time. The popup also has Track and Message buttons.'))
story.append(PB())

# Section 9 — Starcom Resource Map
story += [SB(9,'Starcom Resource Map','http://192.168.50.1/resmap.html'), SP(8)]
story.append(P('A Leaflet-based map for manually placing and tracking Starcom units. Unlike the APRS tactical map, '
               'positions here are placed manually by the operator. Supports unit placement, status color coding, '
               'zone drawing, and polygon area markup for tactical overlays.'))
story.append(SP(4))
story.append(TipBox('Use the Starcom Resource Map alongside the Starcom Net Logger during a public safety activation. '
                    'Place units on the map as they check in, and update their status as assignments change.'))
story.append(PB())

# Section 10 — FCC Callsign Lookup
story += [SB(10,'FCC Callsign Lookup','http://192.168.50.1/callsign.html'), SP(8)]
story.append(P('Search the local FCC amateur license database — the entire US amateur callsign database '
               '(~800,000 licensees) stored offline on the Pi. No internet required. Results include licensee name, '
               'address, license class, grant date, expiry date, and trustee callsign for club licenses.'))
story.append(SP(4))
story.append(TipBox('Direct URL lookup: http://192.168.50.1/callsign.html?call=W9XYZ '
                    '— Useful for bookmarking specific calls or linking from net control exports.'))
story.append(PB())

# Section 11 — Dead Man's Switch
story += [SB(11,"Dead Man's Switch Monitor",'http://192.168.50.1/deadmans.html'), SP(8)]
story.append(P("Monitors each active net for inactivity. If a net goes silent beyond a configured threshold, "
               "it escalates through warning and trigger states — alerting operators that the net may have lost communications."))
story.append(SP(6))
story.append(tbl([["STATE","COLOR","MEANING","ACTION"],
    ["DISARMED","Grey","Not being monitored","Click ARM to activate monitoring"],
    ["ARMED","Green","Net is communicating","Normal operations. Reset timer on each check-in."],
    ["WARNING","Amber","75% of threshold reached","Contact net control. Resume activity to clear."],
    ["TRIGGERED","Red","Threshold exceeded","Immediate action required — check radio and net."],
    ], [0.9*inch, 0.8*inch, 1.5*inch, CW-3.2*inch]))
story.append(PB())

# Section 12 — Pre-Flight
story += [SB(12,'Pre-Flight Deployment Checklist','http://192.168.50.1/preflight.html'), SP(8)]
story.append(P('A structured GO / CAUTION / NO-GO readiness assessment to complete before any deployment. '
               'Covers all critical systems and saves a timestamped JSON record.'))
story.append(SP(6))
story.append(tbl([['SECTION','ITEMS CHECKED'],
    ['Power Systems','Shore/generator power, battery backup, UPS, fuel supply, runtime estimate'],
    ['Communications Equipment','HF radio, VHF/UHF radio, TNC, antennas, coax, SWR check'],
    ['Computing & Software','Pi boot, all FieldComms services green, Kiwix, FCC DB, browser access'],
    ['Personnel & Staffing','NCS identified, EC notified, backup NCS available'],
    ['Field Supplies','Operator cards, printed forms, batteries, cables, tools, PPE'],
    ], [1.8*inch, CW-1.8*inch]))
story.append(PB())

# Section 13 — ICS Platform Overview
story += [SB(13,'ICS Platform — Overview','http://192.168.50.1/ics/'), SP(8)]
story.append(P(
    'The ICS Platform provides a complete Incident Command System management interface '
    'organized into the five standard ICS sections. '
    'All data is saved to the FieldComms server and synchronized in real time across '
    'every device on EMCOMM-NET — section chiefs at different workstations all see '
    'the same incident state simultaneously without refreshing their browsers. '
    'The Planning P tab walks you through all 15 phases of the ICS planning cycle '
    'with agendas, required forms, and attendee lists for each phase.'))
story.append(SP(6))
story.append(H2('Creating an Incident'))
for i, step in enumerate([
    'Open http://192.168.50.1/ics/',
    'Click <b>[+ New Incident]</b>',
    'Fill in Incident Name, Type, Jurisdiction, Incident Commander, Op Period Duration',
    'Click <b>Activate Incident</b> — all five sections are now live',
], 1):
    story.append(P(f'<b>{i}.</b>  {step}', S('bl', fontSize=9, leading=12, leftIndent=14, firstLineIndent=-10)))
story.append(PB())

# Sections 14-18 — ICS Sections
for num, title, url, content in [
    (14, 'ICS Command', 'http://192.168.50.1/ics/command.html', [
        ('Incident Objectives (ICS-202)', 'Enter numbered tactical objectives. Use the 100-item dropdown to select common objectives organized in 13 groups — or type custom objectives directly.'),
        ('Safety Message', 'Free-text safety message for the period — weather, hazards, PPE requirements.'),
        ('Weather Summary', 'Current conditions and forecast for the operational area.'),
        ('Command Staff (ICS-203)', 'Fill in name and agency for each ICS position: IC, Safety Officer, PIO, Liaison Officer, and section chiefs.'),
        ('Situation Report', 'Current situation, accomplishments, and planned actions for the IAP.'),
    ]),
    (15, 'ICS Operations', 'http://192.168.50.1/ics/operations.html', [
        ('T-Card Board', 'Visual Kanban-style board with four columns: Available / Staged / Assigned / Out of Service. Drag cards to move resources between columns.'),
        ('Resource List', 'Table view of all resources with ID, type, name, capability, status, assignment, and contact.'),
        ('Assignments (ICS-204)', 'List of all resources in Assigned status with their tasking and contact info.'),
    ]),
    (16, 'ICS Planning', 'http://192.168.50.1/ics/planning.html', [
        ('Situation Status (ICS-209)', 'Status summary: total personnel, resources by status, incident narrative, weather, agency list.'),
        ('IAP Forms', 'Checklist of all ICS forms with status indicators and links to open each one.'),
        ('Resource Status Table', 'Grid showing how many of each resource kind are ordered, on scene, assigned, available, out of service, still needed.'),
        ('Documentation', 'Running log of all documents produced during the incident.'),
    ]),
    (17, 'ICS Logistics', 'http://192.168.50.1/ics/logistics.html', [
        ('Comms Plan (ICS-205)', 'Build the radio communications plan. Each row is a channel: function, name, frequency, CTCSS tone, mode, remarks. Pre-filled with McHenry County channels.'),
        ('Supply Tracking', 'Log supply requests with item, category, quantity needed, quantity on hand, and priority.'),
        ('Food / Medical (ICS-206)', 'Meal service log and medical unit leader, ambulance service, nearest hospital info.'),
        ('Check-In (ICS-211)', 'Personnel check-in list with name, ICS position, agency, and arrival time.'),
    ]),
    (18, 'ICS Finance / Admin', 'http://192.168.50.1/ics/finance.html', [
        ('Cost Accounting', 'Log all expenditures: category, amount, description, vendor, approver. Running total shown.'),
        ('Time Tracking', 'Log person-hours for each operator: name, position, agency, hours, hourly rate (0 = volunteer).'),
        ('Procurement', 'Track purchase orders: item, vendor, PO number, amount, status.'),
        ('Export', 'Export all finance data to CSV for submission to agency finance officer.'),
    ]),
]:
    story += [SB(num, title, url), SP(6)]
    story.append(tbl([['FEATURE','HOW TO USE IT']] + [[f,d] for f,d in content],
                     [1.8*inch, CW-1.8*inch]))
    story.append(PB())

# Section 19 — NTS Radiogram
story += [SB(19,'NTS Radiogram Generator','http://192.168.50.1/nts.html'), SP(8)]
story.append(tbl([['FIELD','DESCRIPTION','EXAMPLE'],
    ['Message Number','Sequential message number','001'],
    ['Precedence','EMERGENCY / PRIORITY / WELFARE / ROUTINE','ROUTINE'],
    ['Handling Instructions','HX codes — delivery special instructions','HXC'],
    ['Station of Origin','Originating station callsign','W9XYZ'],
    ['Check (word count)','Word count of text — auto-calculated','22'],
    ['Place of Origin','City and state of originating station','WOODSTOCK IL'],
    ['Time Filed','UTC time — auto-fill button provided','2145Z'],
    ], [1.5*inch, 2.2*inch, CW-3.7*inch]))
story.append(PB())

# Section 20 — ICS-213 and ICS-214
story += [SB(20,'ICS-213 General Message  &  ICS-214 Activity Log','http://192.168.50.1/ics213.html'), SP(8)]
story.append(P('<b>ICS-213</b> — The standard written message form for inter-agency and intra-agency '
               'communications. Fill in the header (incident name, to/from, position/agency, date/time, subject) '
               'and the message body. Click <b>Print</b> to produce a field-ready paper copy.'))
story.append(SP(4))
story.append(TipBox('ICS-213 is for formal written communications. For routine spoken radio traffic, '
                    'use the net control log. Use 213 when you need a written record of requests, '
                    'situation updates, or resource orders.', 'note'))
story.append(SP(8))
story.append(P('<b>ICS-214</b> — A unit-level activity log required for every ICS section and unit. '
               'Records personnel assigned and a timestamped log of activities through the operational period. '
               'Click Add Personnel to list team members, then Add Entry for each activity.'))
story.append(PB())

# Section 21 — ICS-309
story += [SB(21,'ICS-309 Communications Log','http://192.168.50.1/ics309.html'), SP(8)]
story.append(tbl([['FIELD','WHAT TO ENTER'],
    ['Incident Name','Name of the active incident (auto-populated if incident is active)'],
    ['Operational Period','Current period number and date range'],
    ['Radio Operator','Your name and callsign'],
    ['Station/Net','Net name or radio station identifier'],
    ['Log Rows','Date/Time, From, To, Subject/Message summary — one row per message'],
    ], [1.8*inch, CW-1.8*inch]))
story.append(SP(4))
story.append(P('Click <b>Add (timestamp now)</b> to add a row with the current UTC time. '
               'Click <b>Save to Incident</b> to file the completed log with the active incident.'))
story.append(PB())

# Section 22 — HF Propagation
story += [SB(22,'HF Propagation','http://192.168.50.1/propagation.html'), SP(8)]
story.append(tbl([['INDICATOR','WHAT IT MEANS FOR HF'],
    ['SFI (Solar Flux Index)','Higher = better high-band propagation. >130: excellent. 90–130: good. <90: 40m/80m only.'],
    ['Sunspot Number','More sunspots = better HF. Follows 11-year cycle.'],
    ['A-Index','Daily geomagnetic activity. <10 quiet (good HF). 10–30 unsettled. >30 disturbed.'],
    ['K-Index (0–9)','3-hour snapshot. ≤2 quiet. 3–4 unsettled. ≥5 storm (HF degraded). ≥7 severe.'],
    ['Band Condition Bars','Green=good / Amber=fair / Red=poor for each band from 10m through 80m.'],
    ], [1.8*inch, CW-1.8*inch]))
story.append(PB())

# Section 23 — Repeater Database
story += [SB(23,'Repeater Database','http://192.168.50.1/repeaters.html'), SP(8)]
story.append(tbl([['SOURCE TAB','HOW TO USE'],
    ['Offline File (recommended)','Load a RepeaterBook CSV or JSON export. Drag-and-drop or Browse. Data persists in the browser after first load.'],
    ['Server API','Pulls from FieldComms server if fetch_repeaters.py has been run. Requires RepeaterBook API token.'],
    ['Sample Data','Demo repeaters for testing the interface. Not real — do not use for operations.'],
    ], [1.5*inch, CW-1.5*inch]))
story.append(SP(4))
story.append(P('Filters: <b>Band</b> (2m, 70cm, etc.) · <b>State</b> · <b>Affiliation</b> '
               '(ARES, SKYWARN, RACES) · <b>Mode</b> (FM, DMR, C4FM, D-STAR) · '
               '<b>Sort</b> by callsign, frequency, city, or distance'))
story.append(PB())

# Section 24 — Facilities
story += [SB(24,'Facilities Directory','http://192.168.50.1/facilities.html'), SP(8)]
story.append(P('Maintain a directory of EOC locations, hospitals, shelters, staging areas, and command posts. '
               'Each entry stores address, coordinates, radio frequencies, CTCSS tone, contact person, '
               'on-site callsign, generator status, ADA access, capacity, and operational notes.'))
story.append(SP(4))
story.append(TipBox('Four default facilities are pre-loaded for McHenry County. Edit these with your actual '
                    'EOC, shelter, and staging area information. Click any card to expand full detail.'))
story.append(PB())

# Section 25 — Grid Square
story += [SB(25,'Grid Square Calculator','http://192.168.50.1/grid.html'), SP(8)]
story.append(P('Convert between decimal latitude/longitude and Maidenhead grid squares in both directions. '
               'Supports 4-character (EN52) and 6-character (EN52ab) precision. Also calculates distance '
               'and bearing between any two grid squares. McHenry County, IL is in grid square <b>EN52</b>.'))
story.append(PB())

# Section 26 — Cheat Sheets
story += [SB(26,'Radio Cheat Sheets','http://192.168.50.1/cheatsheets.html'), SP(8)]
story.append(tbl([['TAB','CONTENTS'],
    ['Phonetic Alphabet','NATO phonetics A–Z with pronunciation, plus ITU number pronunciation'],
    ['Q-Codes','Common amateur Q-codes and EmComm net Q-codes (QNI, QNS, QND, QNN, etc.)'],
    ['Prowords','ROGER, WILCO, SAY AGAIN, BREAK, OVER, OUT, CORRECTION, SILENCE, and 25 others'],
    ['Band Plan','2m and 70cm segments, HF emergency frequencies, MURS, FRS, GMRS, Marine, Aviation'],
    ['NTS Precedence','EMERGENCY / PRIORITY / WELFARE / ROUTINE — definitions and when to use each'],
    ['ICS Positions','Standard ICS command and general staff titles with abbreviations'],
    ['CTCSS / DCS','Standard CTCSS tone table (67.0–254.1 Hz) and DCS code table'],
    ], [1.4*inch, CW-1.4*inch]))
story.append(PB())

# Section 27 — Print Center
story += [SB(27,'Print Center','http://192.168.50.1/printcenter.html'), SP(8)]
story.append(tbl([['CATEGORY','AVAILABLE DOCUMENTS'],
    ['ICS / NTS Forms','ICS-213 General Message, ICS-214 Activity Log, NTS Radiogram, Pre-Flight Checklist'],
    ['Reference Cards','Phonetic Alphabet, Q-Codes & Prowords, ICS Structure & Forms, CTCSS/DCS & Signal Reports'],
    ['Operations','Net Control Log (ICS-309), Starcom Net Log, Member Roster, Resource Board'],
    ['Cover Sheet Generator','Fill in incident details → generates formatted IAP cover sheet'],
    ['Operator Access Cards','Avery 5371 format — 10 cards per sheet — callsign, EMCOMM-NET, IP address'],
    ], [1.5*inch, CW-1.5*inch]))
story.append(PB())

# Section 28 — Kiwix
story += [SB(28,'Kiwix Offline Library','http://192.168.50.1:8081/'), SP(8)]
story.append(tbl([['CONTENT','WHAT\'S IN IT','BEST FOR'],
    ['WikiMed Medical Encyclopedia','Symptoms, diagnoses, treatments, medications, procedures, anatomy','Mass casualty events, medical support operations'],
    ['Wikipedia (Mini)','Compact English Wikipedia — facts, geography, science, history','General field reference, briefing preparation'],
    ['Wikivoyage','Travel guides, emergency shelters, local resources, evacuation routes','Shelter-in-place planning, unfamiliar jurisdictions'],
    ['iFixit Repair Guides','Equipment repair procedures for electronics, tools, vehicles','Field equipment troubleshooting'],
    ], [1.8*inch, 2.0*inch, CW-3.8*inch]))
story.append(PB())

# Section 29 — Health Monitor
story += [SB(29,'Health Monitor','http://192.168.50.1:5051/health'), SP(8)]
story.append(tbl([['METRIC','NORMAL RANGE','ACTION IF EXCEEDED'],
    ['CPU Temperature','< 70°C','Improve ventilation. Pi 5 throttles at 85°C.'],
    ['Memory Usage','< 80%','Close unused browser tabs. Restart non-essential services.'],
    ['Disk Usage','< 90%','Archive old logs. Remove unused ZIM files.'],
    ['Service Status','All green dots','Red dot = service down. Restart with: sudo systemctl restart SERVICE'],
    ['Internet','Connected (when available)','Check Ethernet. All core features work offline.'],
    ], [1.5*inch, 1.2*inch, CW-2.7*inch]))
story.append(PB())

# Section 30 — Quick Reference
story += [SB(30,'Quick Reference & Tips','/'), SP(8)]
story.append(tbl([['TOOL','URL','WHEN TO USE'],
    ['Dashboard','/','Opening screen — system status, weather alerts, APRS, tool access'],
    ['Net Control','/netcontrol.html','Running any ARES/RACES amateur radio net'],
    ['Starcom Logger','/starcom.html','Public safety Starcom nets with Radio IDs'],
    ['ICS Platform','/ics/','Any formally-declared ICS incident'],
    ['Tactical Map','/tactical.html','APRS situational awareness, unit tracking'],
    ['Pre-Flight','/preflight.html','Before every activation — GO/CAUTION/NO-GO'],
    ['Roster','/roster.html','Member management, activation tracking'],
    ['NTS Radiogram','/nts.html','Generating and logging formal ARRL traffic'],
    ['Kiwix Library',':8081/','Medical reference, equipment repair, field skills'],
    ['Health Monitor',':5051/health','Check service status, system temperature, disk usage'],
    ], [1.4*inch, 1.4*inch, CW-2.8*inch]))
story.append(SP(6))
story.append(TipBox(
    'During an activation, the Health Monitor at http://192.168.50.1:5051/health shows complete '
    'system status including CPU temperature, memory, disk usage, service health dots, '
    'GPS fix quality, and internet connectivity. '
    'If a service dot is red, SSH to the Pi and run:  sudo systemctl restart <service-name>. '
    'Common service names: fcc-lookup, health-monitor, ics-platform, kiwix, deadmans, nginx.  '
    'The install log is at /var/log/fieldcomms-install.log.',
    'note'))
story.append(PB())

# Section 31 — Reference Library
story += [SB(31,'Reference Library','http://192.168.50.1/refs.html'), SP(8)]
story.append(P('Stores all field reference documents — radio manuals, interoperability plans, ICS form packages, '
               'SOGs, agency plans, and training materials. Files stored on the Pi, accessible from any device on EMCOMM-NET.'))
story.append(SP(6))
for step in [
    'Click <b>⬆ Upload Document</b>. A panel slides in from the right.',
    'Drag-and-drop the file or click Browse. Accepts PDF, Word, Excel, images, KML, ZIP, GPX — up to 200 MB.',
    'Fill in Title, Category, Source, Description, Tags, Revision, and Expiry.',
    'Click <b>⬆ Upload Document</b>. PDFs get an automatic thumbnail.',
]:
    story.append(B(step))
story.append(PB())

# Section 32 — Winlink Form Import
story += [SB(32,'Winlink Form Import & Incident Archiving','http://192.168.50.1/winlink-import.html'), SP(8)]
story.append(P('Brings ICS form data from Winlink Express into the FieldComms incident record. '
               'When Winlink Express sends or receives an ICS form, it attaches an XML data file. '
               'This page parses that XML, maps the fields, and archives the form to the active incident.'))
story.append(SP(6))
story.append(H2('Step-by-Step Import'))
for i, step in enumerate([
    'In Winlink Express, open the ICS form message (sent or received).',
    'Right-click the <b>RMS_Express_Form_*.xml</b> attachment and save it.',
    'On the Winlink Form Import page, drag the saved XML file onto the drop zone, or click Browse.',
    'Click <b>Parse Form Data</b>. The page detects the form type and extracts all fields.',
    'Review the extracted fields, select the Incident, then click <b>Archive to Incident</b>.',
], 1):
    story.append(P(f'<b>{i}.</b>  {step}', S('bl', fontSize=9, leading=12, leftIndent=14, firstLineIndent=-10)))
story.append(PB())

# Section 33 — JS8Call
story += [SB(33,'JS8Call — HF Digital Keyboard Messaging','/'), SP(8)]
story.append(P('JS8Call is a keyboard-to-keyboard HF digital mode based on FT8 that provides store-and-forward '
               'messaging, heartbeats, and directed messaging at very weak signal levels. Runs on the Windows laptop '
               'connected to the IC-7300.'))
story.append(SP(6))
story.append(H2('Setup'))
for step in [
    'JS8Call must be running on the Windows laptop (not the Pi).',
    'Enable the API: File → Settings → API — enable, set port to <b>2442</b>.',
    'Set hostname to <b>0.0.0.0</b> to allow EMCOMM-NET devices to connect.',
    'Note the Windows laptop IP address on EMCOMM-NET (e.g. 192.168.50.105).',
    'On FieldComms dashboard, tap the JS8Call card → enter the laptop IP → tap OK.',
]:
    story.append(B(step))
story.append(PB())

# Section 34 — Planning P
story += [SB(34,'ICS Planning P — Operational Planning Cycle','http://192.168.50.1/ics/planningp.html'), SP(8)]
story.append(P('Interactive guide to the ICS operational planning cycle. Presents all 15 phases from incident '
               'through each operational period, with the standard agenda, required ICS forms, and attendees.'))
story.append(SP(6))
story.append(tbl([['COLOR','GROUP','PHASES'],
    ['Gray','Initial Response — incident through incident brief','Phases 1–5'],
    ['Yellow','Establish Objectives — IC/UC objectives + C&G Staff Meeting','Phases 6–7'],
    ['Red','Develop the Plan — tactics through planning meeting','Phases 8–11'],
    ['Green','Prepare & Disseminate — IAP prep + operations briefing','Phases 12–13'],
    ['Teal','Execute, Evaluate & Revise — execute plan + new ops period','Phases 14–15'],
    ], [0.7*inch, 3.0*inch, CW-3.7*inch]))
story.append(SP(4))
story.append(P('Click any phase button → see the standard agenda, required forms (as clickable links), '
               'and attendees. Click <b>Generate briefing sheet</b> to print a one-page cover for the IAP.'))
story.append(PB())

# Section 35 — Operator Access Cards
story += [SB(35,'Operator Access Cards','http://192.168.50.1/printcenter.html'), SP(8)]
story.append(P('Printable Avery 5371 business-card-size reference cards (2" × 3.5", 10 per sheet). Each card '
               'shows the network name, server IP address, and quick-reference steps. Print, cut, laminate, '
               'and give one to every operator at a deployment.'))
story.append(SP(6))
story.append(tbl([['CARD FIELD','CONTENT'],
    ['Network','EMCOMM-NET (Wi-Fi name)'],
    ['Server address','http://192.168.50.1'],
    ['Quick steps','Connect → Open browser → Enter identity'],
    ['Callsign / ID','Member callsign (large, blue) or Radio ID (large, purple)'],
    ['ESV Member ID + Radio ID','Shown on all cards regardless of type'],
    ], [1.5*inch, CW-1.5*inch]))
story.append(PB())

# Section 36 — Network / AiMesh / WAN
story += [SB(36,'Network — EMCOMM-NET, WAN & 44Net Gateway','/'), SP(8)]
story.append(P(
    'EMCOMM-NET is the Wi-Fi network broadcast by three ASUS RT-BE58 Go Wi-Fi 7 routers '
    'operating as an AiMesh. One primary router manages WAN connectivity and DHCP. '
    'Two mesh nodes extend EMCOMM-NET coverage to secondary rooms, outdoor areas, and upper floors. '
    'All three broadcast the same EMCOMM-NET SSID — devices roam between them automatically.'))
story.append(SP(6))
story.append(H2('AiMesh Coverage'))
story.append(tbl([['ROUTER','PORT','PLACEMENT'],
    ['Primary Router','Port 1','Central — command post or EOC entrance. Manages WAN and DHCP.'],
    ['Mesh Node 1','Port 11','Secondary room, opposite wing, or upper floor.'],
    ['Mesh Node 2','Port 12','Third zone — outdoor staging, parking, or far wing.'],
    ], [1.5*inch, 0.7*inch, CW-2.2*inch]))
story.append(SP(6))
story.append(H2('WAN Connectivity — InstyConnect Primary + Starlink Failover'))
story.append(P(
    'InstyConnect cellular (T-Mobile and Verizon dual-carrier) is the primary internet source '
    'connected to the ASUS WAN port via a single PoE Ethernet cable from the outdoor antenna. '
    'Starlink satellite is the automatic secondary — the ASUS switches to it within 30-60 seconds '
    'if cellular drops, and switches back when it recovers. No operator action is required.'))
story.append(SP(4))
story.append(tbl([['ANTENNA','WHEN TO USE'],
    ['InstyConnect Drum','Default — every activation. Mounts on any mast or tripod. No aiming needed.'],
    ['InstyConnect Switchblade','When Drum signal is poor. Swap PoE cable to same ASUS WAN port. Aim toward tower.'],
    ['Starlink dish','Active automatically when cellular drops. Requires clear sky view. No inbound connections.'],
    ], [2.2*inch, CW-2.2*inch]))
story.append(SP(4))
story.append(tbl([['WAN STATE','DASHBOARD SHOWS','FEATURES AVAILABLE'],
    ['InstyConnect UP','WAN card green — cellular + carrier','All features: NWS, APRS-IS, FCC refresh, Pat Winlink via internet'],
    ['Starlink UP  (failover)','WAN card blue — Starlink failover','All features except inbound connections. ~20-40ms higher latency.'],
    ['Both DOWN  (offline)','WAN card red — Offline mode','All 32 local tools work normally. NWS, APRS-IS, FCC refresh paused.'],
    ], [1.4*inch, 1.5*inch, CW-2.9*inch]))
story.append(SP(4))
story.append(TipBox(
    'View full WAN details at http://192.168.50.1/wan-status.html — shows active source, '
    'carrier, signal strength, Starlink latency, connectivity test results, and a WAN event log '
    'recording every failover and failback with UTC timestamps.'))
story.append(SP(6))
story.append(H2('AMPRNet / 44Net Gateway'))
story.append(P(
    'A dedicated Raspberry Pi 5 at 192.168.50.2 maintains a permanent WireGuard tunnel to '
    'amprgw.ampr.org, routing the 44.0.0.0/8 AMPRNet address block for all EMCOMM-NET devices. '
    'Any device on EMCOMM-NET can reach other AMPRNet stations worldwide.'))
story.append(SP(4))
story.append(tbl([['ACCESS LEVEL','HOW','WHAT YOU CAN DO'],
    ['Status Dashboard','http://192.168.50.2:9000 — enter FCC callsign at login prompt','View tunnel state, AMPRNet address, traffic stats. Read-only.'],
    ['Tunnel Control','Gateway Pi keyboard only — open http://localhost:9001 on the gateway Pi. Callsign login required.','Bring tunnel up/down/restart. All actions logged.'],
    ], [1.2*inch, 2.4*inch, CW-3.6*inch]))
story.append(SP(4))
story.append(TipBox(
    'The AMPRNet dashboard card on the FieldComms main dashboard shows live tunnel state '
    '(green = UP, red = DOWN) updated every 30 seconds. Click it to open the full gateway status page. '
    'Access requires a valid FCC amateur radio callsign — all access is logged for Part 97 compliance.'))
story.append(PB())

# Section 37 — Printer Setup
story += [SB(37,'Printer Setup','http://192.168.50.1:631'), SP(8)]
story.append(P('FieldComms has print buttons on 17 pages — all using the browser standard print function. '
               'Three connection options are available:'))
story.append(SP(6))
story.append(tbl([['OPTION','HOW IT WORKS','BEST FOR'],
    ['A — Own printer','Each operator prints to their own locally connected printer. No Pi setup needed — works immediately.','Single operator or when every device already has a printer'],
    ['B — USB printer via Pi (CUPS)','USB printer plugged into the Pi. CUPS shares it across EMCOMM-NET. Admin at http://192.168.50.1:631. Installed automatically by the FieldComms installer.','Field activations — one shared printer for all operators. Supports Windows, Mac, iOS AirPrint, Android, Chromebook.'],
    ['C — Network printer','Wi-Fi or Ethernet printer connected directly to EMCOMM-NET. Devices discover it via Bonjour/mDNS automatically.','Sites with an existing Wi-Fi capable printer'],
    ], [1.2*inch, 2.8*inch, CW-4.0*inch]))
story.append(SP(4))
for step in [
    'Plug the USB printer into the Pi or powered USB hub.',
    'Open <b>http://192.168.50.1:631</b> from any device on EMCOMM-NET.',
    'Click <b>Administration → Add Printer</b> and log in with Pi username/password.',
    'Select printer from Local Printers. Check <b>Share This Printer</b>. Click Continue.',
    'Select driver, click Add Printer, print a test page.',
]:
    story.append(B(step))
story.append(SP(4))
story.append(TipBox('Recommended field printers: Brother HL-L2350DW (laser, excellent Linux support), '
                    'Canon PIXMA TR150 or HP OfficeJet 200 (battery-powered portable options).'))

# ── Build ─────────────────────────────────────────────────────────────────────
out = '/mnt/user-data/outputs/McHenry_County_RACES_ARES_Starcom_FieldComms_User_Guide.pdf'
doc = SimpleDocTemplate(
    out, pagesize=letter,
    leftMargin=M, rightMargin=M,
    topMargin=0.55*inch, bottomMargin=0.42*inch,
    title='McHenry County RACES/ARES/Starcom FieldComms User Guide',
    author='McHenry County Emergency Services Volunteers and McHenry County Emergency Management Agency')
doc.build(story, canvasmaker=NC)

# Append Pi 500 addendum
from pypdf import PdfReader, PdfWriter
addendum = '/home/claude/pi500_addendum.pdf'
if os.path.exists(addendum):
    base = PdfReader(out); add = PdfReader(addendum)
    w = PdfWriter()
    for p in base.pages: w.add_page(p)
    for p in add.pages:  w.add_page(p)
    buf = io.BytesIO()
    w.write(buf)
    with open(out, 'wb') as f: f.write(buf.getvalue())

r = PdfReader(out)
print(f'BUILT: {out}')
print(f'Pages: {len(r.pages)}')
