#!/usr/bin/env python3
"""
FieldComms Field Quick-Reference — PDF Generator
K9ESV · MCESV/MCEMA
8-page lean field guide. Print double-sided and hand out at check-in.
Output: /mnt/user-data/outputs/FieldComms_Field_Quick_Reference.pdf
"""
import datetime
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, HRFlowable, KeepTogether)
from reportlab.pdfgen import canvas

# ── Palette ──────────────────────────────────────────────────────────────────
EOC    = HexColor('#1a3a6b')
EOC_LT = HexColor('#2d6ab4')
EOC_BG = HexColor('#eef2f7')
GOLD   = HexColor('#f0c040')
LINE   = HexColor('#b0c4dc')
LGRAY  = HexColor('#f0f3f6')
MUTED  = HexColor('#4a6080')
GREEN  = HexColor('#1a7a3a')
SGREEN = HexColor('#1a6b2a')
SGREEN_BG = HexColor('#e0f0e4')
AMBER  = HexColor('#c8760a')
AMBER_BG = HexColor('#fef3d8')
PURPLE = HexColor('#5b2d8c')
RED_BG = HexColor('#fde8e8')
RED    = HexColor('#b82020')

ORG   = 'McHenry County ESV and EMA  ·  MCESV/MCEMA  ·  K9ESV'
PROD  = 'FieldComms IMS v1.0 — Field Quick-Reference'
TODAY = datetime.date.today().strftime('%B %Y')
PAGE_W, PAGE_H = letter
M  = 0.60 * inch
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
            else:
                self._chrome(total)
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
        self.drawCentredString(PAGE_W/2, PAGE_H*0.448, 'FIELD QUICK REFERENCE')
        self.setFillColor(HexColor('#c0d4f0'))
        self.setFont('Helvetica', 10)
        self.drawCentredString(PAGE_W/2, PAGE_H*0.395, 'Operator Quick Reference Card')
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


    def _chrome(self, total):
        n = self._pageNumber
        LOGO = Path('/home/claude/esv-logo.png')
        if n > 1:
            self.setFillColor(EOC)
            self.rect(0, PAGE_H-0.44*inch, PAGE_W, 0.44*inch, fill=1, stroke=0)
            self.setFillColor(GOLD)
            self.rect(0, PAGE_H-0.46*inch, PAGE_W, 0.02*inch, fill=1, stroke=0)
            if LOGO.exists():
                try:
                    self.drawImage(str(LOGO), M, PAGE_H-0.41*inch,
                                   width=0.85*inch, height=0.34*inch,
                                   preserveAspectRatio=True, mask='auto')
                except Exception:
                    pass
            self.setFillColor(white)
            self.setFont('Helvetica-Bold', 9)
            self.drawString(M+1.0*inch, PAGE_H-0.21*inch, PROD)
            self.setFont('Helvetica', 7)
            self.drawString(M+1.0*inch, PAGE_H-0.34*inch, ORG)
        self.setFillColor(EOC)
        self.rect(0, 0, PAGE_W, 0.30*inch, fill=1, stroke=0)
        self.setFillColor(GOLD)
        self.rect(0, 0.30*inch, PAGE_W, 0.013*inch, fill=1, stroke=0)
        self.setFillColor(white)
        self.setFont('Helvetica', 6.5)
        if n > 1:
            self.drawString(M, 0.10*inch,
                'EMCOMM-NET  ·  http://192.168.50.1  ·  For Authorized Personnel Only  ·  '
                '© 2026 KE4CON / MCESV K9ESV  ·  CC BY-SA 4.0  ·  creativecommons.org/licenses/by-sa/4.0')
            self.drawRightString(PAGE_W-M, 0.10*inch,
                f'Page {n} of {total}  ·  {TODAY}')
        else:
            self.drawCentredString(PAGE_W/2, 0.10*inch,
                f'FieldComms IMS v1.0  ·  {ORG}  ·  {TODAY}')

# ── Style helpers ─────────────────────────────────────────────────────────────
def S(name, **kw):
    d = dict(fontName='Helvetica', fontSize=9, textColor=black,
             leading=12, spaceAfter=0, spaceBefore=0)
    d.update(kw)
    return ParagraphStyle(name, **d)

def P(t, s=None):  return Paragraph(t, s or S('b'))
def SP(n=4):       return Spacer(1, n)
def HR(c=LINE, t=0.4):
    return HRFlowable(width='100%', thickness=t, color=c, spaceBefore=2, spaceAfter=2)
def PB():          return PageBreak()

def section_hdr(icon, title, url, color, bg):
    inner = Table([[
        P(f'{icon}  {title}',
          S('sh', fontName='Helvetica-Bold', fontSize=13, textColor=color, leading=16)),
        P(f'<font color="#888888" size="8">{url}</font>',
          S('su', fontSize=8, textColor=MUTED, alignment=TA_LEFT, leading=10)),
    ]], colWidths=[CW*0.55, CW*0.45])
    inner.setStyle(TableStyle([
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING',   (0,0), (-1,-1), 0),
        ('RIGHTPADDING',  (0,0), (-1,-1), 0),
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    outer = Table([[inner]], colWidths=[CW])
    outer.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), bg),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('RIGHTPADDING',  (0,0), (-1,-1), 10),
        ('TOPPADDING',    (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LINEBELOW',     (0,0), (-1,-1), 1.5, color),
    ]))
    return outer

def steps_tbl(rows):
    data = [[P('STEP', S('th', fontName='Helvetica-Bold', fontSize=7.5,
                          textColor=white, leading=9)),
             P('WHAT TO DO', S('th', fontName='Helvetica-Bold', fontSize=7.5,
                                textColor=white, leading=9))]]
    for num, desc in rows:
        data.append([
            P(str(num), S('tn', fontName='Helvetica-Bold', fontSize=9,
                           textColor=EOC_LT, alignment=TA_CENTER, leading=11)),
            P(desc, S('td', fontSize=8.5, leading=12)),
        ])
    t = Table(data, colWidths=[0.36*inch, CW-0.36*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  EOC),
        ('TEXTCOLOR',     (0,0), (-1,0),  white),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [white, LGRAY]),
        ('GRID',          (0,0), (-1,-1), 0.3, LINE),
        ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('RIGHTPADDING',  (0,0), (-1,-1), 6),
        ('LINEBELOW',     (0,0), (-1,0),  1, EOC_LT),
    ]))
    return t

def ref_tbl(headers, rows, widths):
    data = [[P(h, S('th', fontName='Helvetica-Bold', fontSize=7.5,
                      textColor=white, leading=9)) for h in headers]]
    for row in rows:
        data.append([P(c, S('td', fontSize=8, leading=11)) for c in row])
    t = Table(data, colWidths=widths, repeatRows=1, splitByRow=1)
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
        ('LINEBELOW',     (0,0), (-1,0),  1, EOC_LT),
    ]))
    return t

def tip(txt, color=EOC_LT, bg=EOC_BG):
    t = Table([[
        P('▶', S('ti', fontName='Helvetica-Bold', fontSize=9,
                  textColor=color, leading=11)),
        P(txt, S('tt', fontSize=8, leading=11, textColor=black)),
    ]], colWidths=[0.22*inch, CW-0.22*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), bg),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('RIGHTPADDING',  (0,0), (-1,-1), 6),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('LINEAFTER',     (0,0), (0,-1),  1.5, color),
    ]))
    return t

# ══════════════════════════════════════════════════════════════════════════════
story = []

# ── COVER ─────────────────────────────────────────────────────────────────────
story.append(SP(50))
cover = Table([[Table([[
    P('MCESV / MCEMA  ·  K9ESV',
      S('co', fontName='Helvetica', fontSize=10, textColor=GOLD,
        alignment=TA_CENTER, leading=13)),
    SP(6),
    P('FieldComms IMS v1.0',
      S('ct', fontName='Helvetica-Bold', fontSize=30, textColor=white,
        alignment=TA_CENTER, leading=35)),
    SP(4),
    P('FIELD QUICK-REFERENCE',
      S('cs', fontName='Helvetica-Bold', fontSize=18, textColor=GOLD,
        alignment=TA_CENTER, leading=22)),
    SP(16),
    P('Connect to <b>EMCOMM-NET</b>',
      S('ca', fontName='Helvetica-Bold', fontSize=14, textColor=white,
        alignment=TA_CENTER, leading=18)),
    P('Open browser  →  <b>http://192.168.50.1</b>',
      S('ca', fontName='Helvetica-Bold', fontSize=14, textColor=GOLD,
        alignment=TA_CENTER, leading=18)),
    SP(16),
    HR(GOLD, 0.5),
    SP(8),
    P('Amateur Radio  ·  Starcom / Public Safety  ·  ICS Incident Command',
      S('cm', fontName='Helvetica', fontSize=10, textColor=HexColor('#c0d4f0'),
        alignment=TA_CENTER, leading=14)),
    SP(4),
    P('No internet  ·  No app  ·  No login  ·  Any browser',
      S('cm', fontName='Helvetica', fontSize=9, textColor=HexColor('#8090b0'),
        alignment=TA_CENTER, leading=13)),
]], colWidths=[CW])]], colWidths=[CW])
cover.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,-1), EOC),
    ('TOPPADDING',    (0,0), (-1,-1), 40),
    ('BOTTOMPADDING', (0,0), (-1,-1), 40),
    ('LEFTPADDING',   (0,0), (-1,-1), 30),
    ('RIGHTPADDING',  (0,0), (-1,-1), 30),
]))
story.append(cover)
story.append(SP(20))

qc = Table([[
    P('QUICK CONNECT', S('qch', fontName='Helvetica-Bold', fontSize=8,
                          textColor=EOC, leading=10)),
    P('<b>1.</b> Wi-Fi: connect to <b>EMCOMM-NET</b>  &nbsp;&nbsp;'
      '<b>2.</b> Browser: <b>http://192.168.50.1</b>  &nbsp;&nbsp;'
      '<b>3.</b> Enter your callsign, Radio ID, or name when prompted',
      S('qcb', fontSize=9, leading=12)),
]], colWidths=[1.1*inch, CW-1.1*inch])
qc.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,-1), LGRAY),
    ('BACKGROUND',    (0,0), (0,-1),  EOC_BG),
    ('GRID',          (0,0), (-1,-1), 0.5, LINE),
    ('TOPPADDING',    (0,0), (-1,-1), 8),
    ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ('LEFTPADDING',   (0,0), (-1,-1), 8),
    ('RIGHTPADDING',  (0,0), (-1,-1), 8),
    ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
]))
story.append(qc)
story.append(PB())

# ── PAGE 2 — DASHBOARD ────────────────────────────────────────────────────────
story.append(section_hdr('🖥', 'Getting Started & Dashboard',
                         'http://192.168.50.1/', EOC, EOC_BG))
story.append(SP(6))
story.append(steps_tbl([
    ('1', '<b>Connect to EMCOMM-NET</b> — select it from your device\'s Wi-Fi list. No password required on the field network.'),
    ('2', '<b>Open any browser</b> — type <b>http://192.168.50.1</b> in the address bar and press Enter.'),
    ('3', '<b>Enter your identity</b> — type your callsign, Radio ID, or name when the prompt appears. Optionally add your ICS position. This is remembered by your browser.'),
    ('4', '<b>Select a dashboard mode</b> from the three buttons at the top of the page:'),
]))
story.append(SP(6))
story.append(ref_tbl(
    ['MODE', 'BUTTON', 'USE IT FOR'],
    [
        ['Amateur Radio',           '📻', 'ARES/RACES nets, APRS, Winlink, JS8Call, NTS, callsign lookup, propagation'],
        ['Starcom / Public Safety', '🚔', 'Starcom nets, SAR nets, weather nets, resource tracking, unit roster'],
        ['ICS',                     '🏛', 'Incident command — all five ICS sections plus Planning P and ICS forms'],
    ],
    [1.5*inch, 0.5*inch, CW-2.0*inch]))
story.append(SP(8))
story.append(P('Dashboard Elements', S('h2', fontName='Helvetica-Bold', fontSize=10,
                                        textColor=EOC, leading=13)))
story.append(SP(4))
story.append(ref_tbl(
    ['ELEMENT', 'WHAT IT DOES'],
    [
        ['Hero bar (top)',        'Station callsign, system name, live UTC clock and local 24-hr clock'],
        ['NWS Weather Alerts',   'Live alerts color-coded by severity — click any alert to expand full details'],
        ['Operation cards',      'Quick-launch tiles for every tool in the current mode — click to open'],
        ['APRS station table',   'Live stations heard by Graywolf, with callsign, distance, and comment'],
        ['Status sidebar',       'CPU/memory/disk/temp, service health dots (green=running), GPS, Dead Man\'s Switch state'],
    ],
    [1.6*inch, CW-1.6*inch]))
story.append(SP(6))
story.append(tip('The dashboard remembers your last-used mode between sessions. '
                 'Return to Starcom mode directly from Starcom pages using the '
                 '🚔 Starcom Dashboard back link.'))
story.append(PB())

# ── PAGE 3 — NET LOGGERS ──────────────────────────────────────────────────────
story.append(section_hdr('📻', 'Amateur Net Control Logger',
                         'http://192.168.50.1/netcontrol.html', EOC, EOC_BG))
story.append(SP(6))
story.append(steps_tbl([
    ('1', '<b>Open a net</b> — click <b>+ New Net</b>, enter the net name, frequency, mode, and type. Click <b>Open Net</b>.'),
    ('2', '<b>Log a check-in</b> — type a callsign and press <b>Enter</b>. FCC data fills automatically. Add location and remarks if needed.'),
    ('3', '<b>Log traffic</b> — click <b>+ Traffic</b>, enter message number, type, sender, addressee, and subject.'),
    ('4', '<b>Close the net</b> — click <b>Close Net</b>. The log is saved and available for export.'),
    ('5', '<b>Export ICS-309</b> — click <b>Export ICS-309</b> to generate the printable comms log.'),
    ('6', '<b>Share observer link</b> — click <b>🔗 Observer Link</b> to copy a read-only view URL for the EOC or served agencies.'),
]))
story.append(SP(6))
story.append(ref_tbl(
    ['FEATURE', 'HOW TO USE'],
    [
        ['Multiple nets',      'Each net has its own tab. Click a tab to switch between active nets.'],
        ['FCC auto-fill',      'Type any US callsign — name and license class fill automatically from the offline FCC database.'],
        ['Precedence levels',  'ROUTINE / WELFARE / PRIORITY / EMERGENCY — set per check-in or traffic entry.'],
        ['Dead Man\'s Switch', 'Click ⚠ Arm on the Dead Man\'s Switch page to monitor this net for inactivity.'],
    ],
    [1.5*inch, CW-1.5*inch]))
story.append(SP(8))

story.append(section_hdr('🚔', 'Starcom Net Logger',
                         'http://192.168.50.1/starcom.html', SGREEN, SGREEN_BG))
story.append(SP(6))
story.append(steps_tbl([
    ('1', '<b>Open a net</b> — click <b>+ New Net</b>. Choose net type: Starcom General / Weather Net / SAR Net / Observer Net.'),
    ('2', '<b>Log a check-in</b> — enter <b>Radio ID</b> (unit number) and <b>Unit Name</b>. Press <b>Enter</b> or click <b>+ Check In</b>.'),
    ('3', '<b>Set unit status</b> — click the status badge on any check-in row to cycle: Available → Deployed → Staging → Out of Service.'),
    ('4', '<b>Run multiple nets simultaneously</b> — click <b>+ New Net</b> again for each additional net. Each open net appears as a badge in the active nets panel on the left. Click any badge to switch between nets. Each net keeps its own independent check-in log and traffic log.'),
    ('5', '<b>Close a net</b> — select the net, then click <b>Close Net</b>. All check-ins and traffic are archived.'),
]))
story.append(SP(6))
story.append(ref_tbl(
    ['FIELD', 'DESCRIPTION'],
    [
        ['Radio ID',      'Starcom unit number (e.g. 2301, 4710). Required for every check-in.'],
        ['Unit Name',     'Agency and unit description (e.g. "McHenry SO — Unit 12")'],
        ['Dispatch Ctr',  'Dispatching agency or center (e.g. MCECC, IDOT)'],
        ['Weather / SAR', 'Use the quick-launch cards on the Starcom dashboard to pre-set net type'],
        ['Multiple nets', 'Typical activation: Starcom General + Weather Net + SAR Net all open simultaneously'],
    ],
    [1.1*inch, CW-1.1*inch]))
story.append(PB())

# ── PAGE 4 — ROSTER + RESOURCE BOARD + RESOURCE MAP ──────────────────────────
story.append(section_hdr('👥', 'Member Roster',
                         'http://192.168.50.1/roster.html', EOC, EOC_BG))
story.append(SP(6))
story.append(ref_tbl(
    ['TAB', 'WHAT TO DO THERE'],
    [
        ['Members',       'Add/edit members. Fields: callsign, name, Radio ID, phone, address, license class, email, notes.'],
        ['Certifications','Check off ICS-100/200/300/400/700/800, EmComm I/II, CERT, First Aid, FEMA IS courses.'],
        ['Equipment',     'Check off capabilities: HF/VHF/UHF radio, Winlink, JS8Call, APRS, generator, antenna, laptop, go-kit.'],
        ['Activations',   'Log check-ins for this incident. Click <b>+ Check In</b> to mark a member as activated. Walk-ins can be added here.'],
        ['Import/Export', 'Export roster to CSV. Import from a previous activation CSV to pre-populate for the next event.'],
    ],
    [1.4*inch, CW-1.4*inch]))
story.append(SP(8))

story.append(section_hdr('📦', 'Resource Board',
                         'http://192.168.50.1/resources.html', AMBER, AMBER_BG))
story.append(SP(6))
story.append(steps_tbl([
    ('1', '<b>Add a resource</b> — click <b>+ Add Resource</b>. Enter name, type, owner/callsign, location, and initial status.'),
    ('2', '<b>Change status</b> — click the colored status badge on any card to cycle through the five states.'),
    ('3', '<b>Filter</b> — use the Type and Status dropdowns to show only the resources you need.'),
]))
story.append(SP(4))
story.append(ref_tbl(
    ['STATUS', 'COLOR', 'MEANING'],
    [
        ['Available',     'Green', 'On scene and ready for assignment'],
        ['Assigned',      'Amber', 'Actively tasked'],
        ['Staging',       'Blue',  'En route or at staging area'],
        ['Out of Service','Red',   'Unavailable — hold, mechanical, or medical'],
        ['Demobilized',   'Gray',  'Released and departed'],
    ],
    [1.2*inch, 0.7*inch, CW-1.9*inch]))
story.append(SP(8))

story.append(section_hdr('🗺️', 'Resource Tracking Map',
                         'http://192.168.50.1/resmap.html', SGREEN, SGREEN_BG))
story.append(SP(6))
story.append(ref_tbl(
    ['ACTION', 'HOW'],
    [
        ['Place a unit',  'Click <b>+ Add Unit</b> → enter Radio ID, unit name, type, status → click <b>📍 Pick on Map</b> or enter lat/lon → Save.'],
        ['Move a unit',   'Drag the unit marker to its new position on the map. Coordinates update automatically.'],
        ['Change status', 'Click the marker → Edit → change Status dropdown → Save. Color updates immediately.'],
        ['Draw a zone',   'Click <b>Draw Zone</b> → click map points to define boundary → double-click to finish → enter zone name.'],
    ],
    [1.3*inch, CW-1.3*inch]))
story.append(PB())

# ── PAGE 5 — ICS PLATFORM ─────────────────────────────────────────────────────
story.append(section_hdr('🏛', 'ICS Platform — All Five Sections',
                         'http://192.168.50.1/ics/', EOC, EOC_BG))
story.append(SP(6))
story.append(P('Starting an Incident',
               S('h2', fontName='Helvetica-Bold', fontSize=10, textColor=EOC, leading=13)))
story.append(SP(4))
story.append(steps_tbl([
    ('1', 'Go to <b>http://192.168.50.1/ics/</b> — or click the ICS Platform card from the ICS dashboard mode.'),
    ('2', 'Click <b>🆕 New Incident</b>. Fill in: Incident Name, Type, Location, Incident Commander, Op Period Duration.'),
    ('3', 'Click <b>Activate Incident</b>. All five sections are now active with this incident loaded.'),
    ('4', 'Navigate between sections using the tabs at the top: ⭐ Command · 🔴 Operations · 📋 Planning · 🟢 Logistics · 💜 Finance'),
    ('5', 'Click <b>⏭ Advance Period</b> at the start of each new operational period.'),
]))
story.append(SP(8))
story.append(P('What Each Section Does',
               S('h2', fontName='Helvetica-Bold', fontSize=10, textColor=EOC, leading=13)))
story.append(SP(4))
story.append(ref_tbl(
    ['SECTION', 'KEY TOOLS'],
    [
        ['⭐ Command',
         'Incident objectives (100-item dropdown + free text), safety message, weather summary, '
         'situation report, command staff roster. Forms: ICS-201, ICS-202, ICS-203.'],
        ['🔴 Operations',
         'T-card board — drag resources between Available / Assigned / Staging / Out of Service / Released. '
         'Click any card for assignment details. Forms: ICS-204.'],
        ['📋 Planning',
         'IAP form tracker, resource status table, incident documentation log, operational period notes. '
         'Forms: ICS-209.'],
        ['🟢 Logistics',
         'Communications plan (ICS-205) with pre-filled McHenry County channels, supply tracking, '
         'meal log, personnel check-in list. Forms: ICS-205, ICS-206, ICS-211.'],
        ['💜 Finance/Admin',
         'Expenditure log, personnel time tracking, procurement orders. Export to CSV for agency reporting.'],
    ],
    [1.3*inch, CW-1.3*inch]))
story.append(SP(6))
story.append(tip(
    'The 100-item objectives dropdown in Command section is organized into 13 groups. '
    'Select an objective → it pre-fills the text box → edit if needed → click + Add. '
    'MCESV/MCEMA-specific objectives are in the last group.',
    AMBER, AMBER_BG))
story.append(PB())

# ── PAGE 6 — ICS FORMS + PLANNING P ──────────────────────────────────────────
story.append(section_hdr('📋', 'ICS Forms Quick-Reference',
                         'http://192.168.50.1/', PURPLE, HexColor('#f0e8fc')))
story.append(SP(6))
story.append(ref_tbl(
    ['FORM', 'URL', 'WHAT IT DOES'],
    [
        ['ICS-213 General Message', '/ics213.html',
         'Formal written message. Fill sender, receiver, subject, message body. Print or save to incident.'],
        ['ICS-214 Activity Log', '/ics214.html',
         'Unit activity log. Add personnel, then log timestamped activities. Print for IAP.'],
        ['ICS-309 Comms Log', '/ics309.html',
         'Formal communications log. Add entries with timestamp, from, to, subject. Save to incident.'],
        ['NTS Radiogram', '/nts.html',
         'ARRL formatted radiogram. Auto-fills date/time/number. All preamble fields. Print when complete.'],
        ['Winlink Import', '/winlink-import.html',
         'Drag-and-drop ICS form XML from Winlink Express. Review fields, then archive to active incident.'],
        ['Print Center', '/printcenter.html',
         'Print any blank ICS form, cheat sheet, or operator access card from one location. '
         'Printer options: A) own printer, B) USB printer shared via Pi/CUPS '
         '(admin: http://192.168.50.1:631), C) network printer on EMCOMM-NET.'],
    ],
    [1.3*inch, 1.1*inch, CW-2.4*inch]))
story.append(SP(8))

story.append(section_hdr('🅿', 'Planning P — 15-Phase Cycle Guide',
                         'http://192.168.50.1/ics/planningp.html', AMBER, AMBER_BG))
story.append(SP(6))
story.append(P('Click the <b>🅿 Planning P</b> tab on any ICS page. '
               'Click a phase button → see the standard agenda, required forms, and who should attend. '
               'Click <b>Generate briefing sheet</b> to print a one-page phase cover for the IAP.',
               S('bd', fontSize=9, leading=13)))
story.append(SP(6))
story.append(ref_tbl(
    ['COLOR', 'PHASES', 'GROUP'],
    [
        ['Gray',   'Phases 1–5',   'Initial Response — incident through incident brief'],
        ['Yellow', 'Phases 6–7',   'Establish Objectives — IC/UC objectives + C&G Staff Meeting'],
        ['Red',    'Phases 8–11',  'Develop the Plan — tactics meeting through planning meeting'],
        ['Green',  'Phases 12–13', 'Prepare & Disseminate — IAP prep + operations briefing'],
        ['Teal',   'Phases 14–15', 'Execute, Evaluate & Revise — execute plan + new ops period'],
    ],
    [0.7*inch, 0.9*inch, CW-1.6*inch]))
story.append(PB())

# ── PAGE 7 — TOOLS QUICK-REFERENCE ────────────────────────────────────────────
story.append(section_hdr('🔧', 'Tools Quick-Reference',
                         'http://192.168.50.1/', EOC, EOC_BG))
story.append(SP(6))
story.append(ref_tbl(
    ['TOOL', 'URL', 'QUICK USE'],
    [
        ['FCC Callsign Lookup', '/callsign.html',
         'Type callsign → Enter. Results from local FCC database (~800K licensees). Click + Add to Roster.'],
        ['APRS Tactical Map', '/tactical.html',
         'Live APRS stations from Graywolf/YAAC. Click station to center. Draw overlays with toolbar tools.'],
        ['HF Propagation', '/propagation.html',
         'Live SFI, K-index, A-index from HamQSL. Band-by-band conditions. Useful for frequency selection.'],
        ['Repeater Database', '/repeaters.html',
         'Filter by band, tone, mode, ARES affiliation. Click a row to copy frequency to clipboard.'],
        ['Grid Square Calc', '/grid.html',
         'Enter lat/lon → get Maidenhead grid. Enter grid → get lat/lon + distance/bearing from you.'],
        ['Pre-Flight Check', '/preflight.html',
         'GO / CAUTION / NO-GO readiness verdict. Run before every activation. Export report for records.'],
        ['Dead Man\'s Switch', '/deadmans.html',
         'Click ⚠ Arm next to a net. Alerts you if the net goes silent beyond the configured threshold.'],
        ['Observer Mode', '/observer.html',
         'Read-only live net view. Share the URL with EOC or served agencies — no identity prompt needed.'],
        ['Reference Library', '/refs.html',
         'Upload PDFs/docs up to 200 MB. Tag, search, and share field documents across all devices.'],
        ['Kiwix Library', ':8081/',
         'Offline Wikipedia, WikiMed, iFixit, Wikivoyage. No internet needed. Open from dashboard card.'],
        ['Health Monitor', ':5051/health',
         'Live CPU/memory/disk/temp, all service status dots, GPS fix quality, internet status.'],
        ['WAN Status', '/wan-status.html',
         'Active WAN source (InstyConnect cellular or Starlink satellite), signal strength, '
         'carrier, latency, connectivity tests, and WAN event log.'],
        ['AMPRNet Gateway', '192.168.50.2:9000',
         'WireGuard tunnel state, AMPRNet 44.x.x.x address, traffic stats. '
         'Requires FCC callsign login. Tunnel control requires gateway Pi keyboard.'],
        ['Facilities Directory', '/facilities.html',
         'EOC, shelters, hospitals, staging areas with address, phone, and radio frequencies.'],
        ['Radio Cheat Sheets', '/cheatsheets.html',
         'Phonetic alphabet, Q-codes, prowords, band plan, CTCSS tones, ICS position titles.'],
        ['JS8Call', 'dashboard card',
         'Click the JS8Call card → enter Windows laptop IP when prompted → opens JS8Call web interface.'],
    ],
    [1.4*inch, 1.0*inch, CW-2.4*inch]))
story.append(PB())

# ── PAGE 8 — WINLINK + TROUBLESHOOTING ────────────────────────────────────────
story.append(section_hdr('📡', 'Winlink & Digital Comms',
                         'Windows laptop + IC-7300', PURPLE, HexColor('#f0e8fc')))
story.append(SP(6))
story.append(ref_tbl(
    ['METHOD', 'HOW TO USE'],
    [
        ['Winlink Express\n(primary)',
         'Runs on Windows laptop. IC-7300 connected via single USB-A→USB-B cable. '
         'Use VARA HF or VARA FM mode. After sending/receiving an ICS form, '
         'save the RMS_Express_Form_*.xml and import it at /winlink-import.html.'],
        ['Pat Winlink\n(backup)',
         'Runs on the Pi at port 8090. Open from dashboard card. Browser-based. '
         'Use when Windows laptop is unavailable.'],
        ['JS8Call\n(digital messaging)',
         'Runs on Windows laptop. Enable API at File → Settings → API → port 2442. '
         'Click the JS8Call dashboard card → enter Windows laptop IP. '
         'Recommended frequency: 7.078 MHz USB-D (40m calling).'],
    ],
    [1.4*inch, CW-1.4*inch]))
story.append(SP(8))

story.append(section_hdr('🌐', 'Network — Admin URLs & IP Reference',
                         'All addresses on EMCOMM-NET (192.168.50.0/24)', EOC, EOC_BG))
story.append(SP(6))
story.append(ref_tbl(
    ['DEVICE / SERVICE', 'ADDRESS', 'NOTES'],
    [
        ['FieldComms dashboard', 'http://192.168.50.1', 'Main entry point — all 32 tools'],
        ['WAN Status dashboard', '/wan-status.html',
         'InstyConnect + Starlink + WAN event log'],
        ['AMPRNet gateway status', 'http://192.168.50.2:9000',
         'Requires FCC callsign login'],
        ['ASUS router admin  (primary)', 'http://192.168.50.254',
         'Wi-Fi settings, dual WAN failover, AiMesh'],
        ['InstyConnect modem admin', 'http://10.1.1.1  or  http://my.insty',
         'Connect to InstyConnect Wi-Fi first'],
        ['Starlink dish admin', 'http://192.168.100.1',
         'Or use Starlink app on phone'],
        ['CUPS print server', 'http://192.168.50.1:631',
         'Printer management and shared queue'],
        ['Pat Winlink', 'http://192.168.50.1:8090',
         'Browser-based Winlink backup'],
        ['Kiwix offline library', 'http://192.168.50.1:8081',
         'Wikipedia, WikiMed, iFixit offline'],
        ['Health monitor API', 'http://192.168.50.1:5051/health',
         'JSON health data for all services'],
        ['44Net tunnel control', 'http://localhost:9001',
         'Gateway Pi keyboard only — callsign login required'],
    ],
    [2.0*inch, 1.8*inch, CW-3.8*inch]))
story.append(SP(6))

story.append(section_hdr('📡', 'WAN Connectivity Quick Reference',
                         'InstyConnect Primary  ·  Starlink Automatic Failover', AMBER, AMBER_BG))
story.append(SP(6))
story.append(ref_tbl(
    ['WAN SOURCE', 'HOW CONNECTED', 'WHEN ACTIVE'],
    [
        ['InstyConnect Drum',
         'PoE cable from outdoor antenna to ASUS WAN port',
         'Default — primary WAN at all activations  ·  10.1.1.1'],
        ['InstyConnect Switchblade',
         'Same PoE cable to same ASUS WAN port  (swap Drum)',
         'When Drum signal is poor — aim toward tower  ·  10.1.1.1'],
        ['Starlink satellite',
         'Ethernet adapter + USB adapter → ASUS USB WAN',
         'Auto when cellular drops — switches in 60s  ·  192.168.100.1'],
        ['Site Ethernet',
         'Site cable to ASUS WAN port',
         'Manual — when site internet available  ·  192.168.50.254'],
    ],
    [1.6*inch, 2.3*inch, CW-3.9*inch]))
story.append(SP(6))

story.append(section_hdr('🛰', 'EMCOMM-NET Coverage — AiMesh Nodes',
                         'Three ASUS RT-BE58 Go routers — same SSID, seamless roaming', EOC, EOC_BG))
story.append(SP(6))
story.append(ref_tbl(
    ['ROUTER', 'SWITCH PORT', 'PLACEMENT'],
    [
        ['ASUS RT-BE58 Go  (primary)',
         'Uplink — Port 1',
         'Central position — command post or EOC entrance. Manages WAN and DHCP.'],
        ['ASUS RT-BE58 Go  (mesh node 1)',
         'Port 11',
         'Secondary room, opposite wing, or upper floor.'],
        ['ASUS RT-BE58 Go  (mesh node 2)',
         'Port 12',
         'Third coverage zone — outdoor staging, parking, or far wing.'],
    ],
    [1.8*inch, 1.0*inch, CW-2.8*inch]))
story.append(SP(4))
story.append(tip(
    'All three routers broadcast EMCOMM-NET on 2.4 GHz and 5 GHz. '
    'Devices roam between them automatically — no reconnection or password re-entry needed. '
    'Pairing a new mesh node to the primary takes under 5 minutes via '
    'http://192.168.50.254 → AiMesh → Add Node.',
    EOC, EOC_BG))
story.append(PB())

story.append(section_hdr('⚠', 'Troubleshooting',
                         '', RED, RED_BG))
story.append(SP(6))
story.append(ref_tbl(
    ['SYMPTOM', 'LIKELY CAUSE', 'FIX'],
    [
        ['Cards give errors',
         'Not on EMCOMM-NET — device is on a different network',
         'Check Wi-Fi — must show EMCOMM-NET. Reconnect if needed.'],
        ['Cannot reach http://192.168.50.1',
         'Pi not running or ASUS router not powered',
         'Check Pi power (green LED). Check ASUS router power. Wait 60s after Pi boot.'],
        ['FCC lookup no results',
         'FCC database not built or not a US amateur callsign',
         'Run: sudo systemctl start fcc-refresh.service (needs internet)'],
        ['APRS map no stations',
         'Graywolf/YAAC not running or no RF received yet',
         'Check Health Monitor for service status. Confirm antenna connected to IC-7300.'],
        ['Winlink import fails',
         'Wrong file — must be the XML attachment, not message body',
         'In Winlink Express, right-click the .xml attachment → Save As → then import that file.'],
        ['Service dot is red',
         'A background service has stopped',
         'SSH to Pi: sudo systemctl restart <service-name>  (e.g. fcc-lookup, ics-platform)'],
        ['WAN shows offline',
         'InstyConnect disconnected or plan inactive',
         'Check Drum LED. Try Switchblade. Check plan at instyconnect.com. '
         'If Starlink is connected, failover should be automatic.'],
        ['Starlink failover not working',
         'USB adapter not seated or ASUS Dual WAN not enabled',
         'Check ASUS admin → WAN → Dual WAN → must be ON with USB as secondary.'],
        ['AMPRNet login fails',
         'Callsign not in FCC DB or FieldComms Pi unreachable',
         'Verify callsign is valid at http://192.168.50.1/callsign.html. '
         'If FCC DB offline, format-only validation is used as fallback.'],
        ['Cannot reach 192.168.50.2:9000',
         'Gateway Pi off or not on EMCOMM-NET',
         'Check gateway Pi power (green LED). It must be connected to UniFi switch.'],
    ],
    [1.5*inch, 1.9*inch, CW-3.4*inch]))
story.append(SP(8))
story.append(tip(
    'For any issue not covered here — open the Health Monitor at '
    'http://192.168.50.1:5051/health or check the system log with: '
    'journalctl -u fcc-lookup -n 50',
    RED, RED_BG))
story.append(SP(10))
story.append(HR(EOC_LT, 0.8))
story.append(SP(8))

bm = Table([[
    P('K9ESV  ·  McHenry County Emergency Services Volunteers\n'
      'and McHenry County Emergency Management Agency',
      S('bm', fontName='Helvetica-Bold', fontSize=9, textColor=EOC, leading=13)),
    P('RACES · ARES · Starcom\nhttp://192.168.50.1',
      S('bm', fontName='Helvetica-Bold', fontSize=9, textColor=EOC,
        leading=13, alignment=TA_CENTER)),
    P(f'FieldComms IMS v1.0\n{TODAY}',
      S('bm', fontName='Helvetica', fontSize=8, textColor=MUTED,
        leading=12, alignment=TA_LEFT)),
]], colWidths=[CW*0.45, CW*0.30, CW*0.25])
bm.setStyle(TableStyle([
    ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING',    (0,0), (-1,-1), 6),
    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ('LINEABOVE',     (0,0), (-1,-1), 0.3, LINE),
]))
story.append(bm)

# ── Build ─────────────────────────────────────────────────────────────────────
out = '/mnt/user-data/outputs/FieldComms_Field_Quick_Reference.pdf'
doc = SimpleDocTemplate(
    out, pagesize=letter,
    leftMargin=M, rightMargin=M,
    topMargin=0.58*inch, bottomMargin=0.40*inch,
    title='FieldComms IMS v1.0 — Field Quick-Reference',
    author='McHenry County Emergency Services Volunteers and McHenry County Emergency Management Agency')
doc.build(story, canvasmaker=NC)

from pypdf import PdfReader, PdfWriter
import io

# Append the Pi 500 addendum if it exists
addendum = '/home/claude/pi500_addendum.pdf'
import os
if os.path.exists(addendum):
    base = PdfReader(out)
    add  = PdfReader(addendum)
    w = PdfWriter()
    for p in base.pages: w.add_page(p)
    for p in add.pages:  w.add_page(p)
    buf = io.BytesIO()
    w.write(buf)
    with open(out, 'wb') as f: f.write(buf.getvalue())

r = PdfReader(out)
print(f'BUILT: {out}')
print(f'Pages: {len(r.pages)}')
