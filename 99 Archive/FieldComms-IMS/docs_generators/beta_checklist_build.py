#!/usr/bin/env python3
"""
FieldComms IMS v1.0 — Beta Test Checklist Generator
K9ESV · MCESV/MCEMA
Output: /mnt/user-data/outputs/ESV_Beta_Test_Checklist.pdf
"""
import datetime, io
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, HRFlowable, KeepTogether)
from reportlab.pdfgen import canvas

# ── Palette ──────────────────────────────────────────────────────────────────
EOC    = HexColor('#1a3a6b')
EOC_LT = HexColor('#2d6ab4')
GOLD   = HexColor('#f0c040')
LINE   = HexColor('#c0cfe0')
LGRAY  = HexColor('#f0f3f6')
MGRAY  = HexColor('#e0e8f0')
GREEN  = HexColor('#1a7a3a')
AMBER  = HexColor('#c8760a')
RED    = HexColor('#b82020')

ORG   = ('McHenry County Emergency Services Volunteers and '
         'McHenry County Emergency Management Agency')
SHORT = 'MCESV/MCEMA  ·  K9ESV'
TODAY = datetime.date.today().strftime('%B %d, %Y')
PAGE_W, PAGE_H = letter
M  = 0.65 * inch
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
                self.rect(0, PAGE_H-0.38*inch, PAGE_W, 0.38*inch, fill=1, stroke=0)
                self.setFillColor(GOLD)
                self.rect(0, PAGE_H-0.40*inch, PAGE_W, 0.02*inch, fill=1, stroke=0)
                self.setFillColor(white)
                self.setFont('Helvetica-Bold', 8)
                self.drawString(M, PAGE_H-0.25*inch, SHORT)
                self.setFont('Helvetica', 8)
                self.drawRightString(PAGE_W-M, PAGE_H-0.25*inch,
                    'FieldComms IMS v1.0 — Beta Test Checklist')
            self.setFillColor(EOC)
            self.rect(0, 0, PAGE_W, 0.30*inch, fill=1, stroke=0)
            self.setFillColor(GOLD)
            self.rect(0, 0.30*inch, PAGE_W, 0.013*inch, fill=1, stroke=0)
            self.setFillColor(white)
            self.setFont('Helvetica', 6.5)
            if n > 1:
                self.drawString(M, 0.10*inch, f'© 2026 KE4CON / MCESV K9ESV  ·  CC BY-SA 4.0  ·  creativecommons.org/licenses/by-sa/4.0')
                self.drawRightString(PAGE_W-M, 0.10*inch, f'Page {n} of {total}  ·  {TODAY}')
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
        self.drawCentredString(PAGE_W/2, PAGE_H*0.448, 'BETA TEST CHECKLIST')
        self.setFillColor(HexColor('#c0d4f0'))
        self.setFont('Helvetica', 10)
        self.drawCentredString(PAGE_W/2, PAGE_H*0.395, 'ESV Field Testing & Verification')
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
def HR(c=LINE, t=0.5):
    return HRFlowable(width='100%', thickness=t, color=c, spaceBefore=2, spaceAfter=2)

def section(title, subtitle=''):
    t = Table([[
        P(title, S('sh', fontName='Helvetica-Bold', fontSize=11,
                   textColor=white, leading=14)),
        P(subtitle, S('ss', fontSize=8, textColor=HexColor('#c0d4f0'),
                      leading=10, alignment=TA_LEFT)),
    ]], colWidths=[CW*0.6, CW*0.4])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), EOC),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('RIGHTPADDING',  (0,0), (-1,-1), 8),
        ('TOPPADDING',    (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW',     (0,0), (-1,-1), 2, GOLD),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ]))
    return t

def subsection(title):
    t = Table([[P(title, S('ssh', fontName='Helvetica-Bold', fontSize=9,
                            textColor=EOC_LT, leading=11))]],
              colWidths=[CW])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), MGRAY),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW',     (0,0), (-1,-1), 0.5, EOC_LT),
    ]))
    return t

def rows_table(items):
    """items = list of (feature_text, notes_hint) tuples"""
    PF_W = 0.32*inch
    data = [[
        P('P', S('ph', fontName='Helvetica-Bold', fontSize=7, textColor=white,
                  alignment=TA_CENTER, leading=9)),
        P('F', S('ph', fontName='Helvetica-Bold', fontSize=7, textColor=white,
                  alignment=TA_CENTER, leading=9)),
        P('FEATURE / FUNCTION', S('ph', fontName='Helvetica-Bold', fontSize=7,
                                   textColor=white, leading=9)),
        P('NOTES', S('ph', fontName='Helvetica-Bold', fontSize=7,
                      textColor=white, leading=9)),
    ]]
    for feat, note in items:
        data.append([
            P('□', S('cb', fontSize=11, alignment=TA_CENTER, leading=13, textColor=EOC_LT)),
            P('□', S('cb', fontSize=11, alignment=TA_CENTER, leading=13, textColor=RED)),
            P(feat, S('ft', fontSize=8, leading=11)),
            P(note, S('nt', fontSize=7.5, leading=10, textColor=HexColor('#445566'))),
        ])
    t = Table(data, colWidths=[PF_W, PF_W, CW-PF_W*2-1.8*inch, 1.8*inch],
              repeatRows=1, splitByRow=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  EOC),
        ('TEXTCOLOR',     (0,0), (-1,0),  white),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [white, LGRAY]),
        ('GRID',          (0,0), (-1,-1), 0.3, LINE),
        ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING',   (0,0), (-1,-1), 5),
        ('RIGHTPADDING',  (0,0), (-1,-1), 5),
    ]))
    return t

# ══════════════════════════════════════════════════════════════════════════════
story = []

# ── COVER ─────────────────────────────────────────────────────────────────────
story.append(SP(40))
cov = Table([[Table([[
    P('Incident Management System v1.0',
      S('ct1', fontName='Helvetica-Bold', fontSize=22, textColor=white,
        alignment=TA_CENTER, leading=26)),
    SP(4),
    P('Beta Test Checklist',
      S('ct2', fontName='Helvetica-Bold', fontSize=28, textColor=GOLD,
        alignment=TA_CENTER, leading=32)),
]], colWidths=[CW])]], colWidths=[CW])
cov.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,-1), EOC),
    ('TOPPADDING',    (0,0), (-1,-1), 30),
    ('BOTTOMPADDING', (0,0), (-1,-1), 30),
    ('LEFTPADDING',   (0,0), (-1,-1), 20),
    ('RIGHTPADDING',  (0,0), (-1,-1), 20),
]))
story.append(cov)
story.append(SP(20))

# Test session record box
rec = Table([[Table([[
    P('Test Session Record', S('rh', fontName='Helvetica-Bold', fontSize=10,
                                textColor=EOC, leading=13)),
    SP(8),
    *[Table([[
        P(label, S('rl', fontName='Helvetica-Bold', fontSize=8.5, textColor=EOC_LT,
                   leading=11)),
        P(value, S('rv', fontSize=8.5, leading=11)),
    ]], colWidths=[2.2*inch, CW-2.2*inch-0.4*inch]) for label, value in [
        ('Tester (name / callsign):', ''),
        ('Date:', ''),
        ('Device / browser used:', ''),
        ('Server IP confirmed:', '192.168.50.1'),
        ('Overall result (circle):', '  PASS     PASS WITH NOTES     FAIL'),
    ]],
]], colWidths=[CW-0.4*inch])]], colWidths=[CW])
rec.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,-1), LGRAY),
    ('BOX',           (0,0), (-1,-1), 1, EOC_LT),
    ('TOPPADDING',    (0,0), (-1,-1), 12),
    ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ('LEFTPADDING',   (0,0), (-1,-1), 14),
    ('RIGHTPADDING',  (0,0), (-1,-1), 14),
]))
story.append(rec)
story.append(SP(16))

story.append(P('<b>How to use this checklist</b>', S('hh', fontSize=10, textColor=EOC)))
story.append(SP(4))
story.append(P(
    'Work through each section in order. For each item, tick <b>P</b> if it works correctly, '
    'or <b>F</b> and write a note if it does not. The Notes column is for brief observations — '
    'use extra paper for detail. Items marked with a hint in the Notes column are things to '
    'look for specifically. Submit any failures with the page name and what you expected vs. '
    'what happened.',
    S('bl', fontSize=9, leading=13)))
story.append(PB())

# ── SECTION 1 — SYSTEM & INFRASTRUCTURE ──────────────────────────────────────
story.append(KeepTogether([section('1 · System & Infrastructure',
    'Access, services, Wi-Fi AP, and health monitoring'), SP(6)]))

story.append(KeepTogether([subsection('1.1  Access & Network'), SP(2), rows_table([
    ('Dashboard loads at http://192.168.50.1 on a device connected to EMCOMM-NET',
     'Try phone, tablet, laptop'),
    ('SSID "EMCOMM-NET" visible and password accepted', 'WPA2'),
    ('Dashboard loads at http://fieldcomms.local (mDNS alias)', ''),
    ('Dashboard loads at http://emcomm.local (mDNS alias)', ''),
    ('Single router coverage verified — EMCOMM-NET reachable throughout the deployment area', ''),
    ('All dashboard cards load without 404 errors', 'Click each card'),
    ('UTC clock in nav bar updates every second', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('1.1b  AiMesh Coverage Extension  (standard 2-node deployment)'), SP(2), rows_table([
    ('Both RT-BE58 Go mesh nodes powered on and showing Connected in primary router AiMesh menu',
     'Router admin → AiMesh → both nodes Connected'),
    ('Mesh Node 1 backhaul type shows Ethernet  (UniFi Switch Port 11)',
     'Confirms CAT 6 wired backhaul is connected'),
    ('Mesh Node 2 backhaul type shows Ethernet  (UniFi Switch Port 12)',
     'Confirms CAT 6 wired backhaul is connected'),
    ('EMCOMM-NET and http://192.168.50.1 reachable from Node 1 coverage zone',
     'Walk to coverage zone with a phone'),
    ('EMCOMM-NET and http://192.168.50.1 reachable from Node 2 coverage zone',
     'Walk to 3rd zone with a phone'),
    ('Device roams between nodes without reconnecting when moving through venue',
     'No reconnection — seamless roam'),
    ('Pi remains at 192.168.50.1 throughout — not affected by which node is connected', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('1.1c  WAN Connectivity  (InstyConnect + Starlink failover)'), SP(2), rows_table([
    ('InstyConnect Drum powered on and connected to ASUS WAN port via PoE cable',
     'Drum LED green or white = carrier connected'),
    ('ASUS WAN port shows Connected status with InstyConnect IP address',
     'Router admin → WAN → Internet Status = Connected'),
    ('WAN Status dashboard shows active source as InstyConnect Cellular',
     'wan-status.html — WAN card must be green'),
    ('Carrier shown on WAN status page  (T-Mobile or Verizon)',
     'Confirms multi-network plan is active'),
    ('NWS weather alerts loading on dashboard  (requires WAN)',
     'Alerts populate — confirms internet is active'),
    ('Starlink dish powered on and connected to ASUS USB WAN port via adapter',
     'Dish LED — allow 3 min to acquire satellite'),
    ('ASUS Dual WAN configured: Primary = WAN port, Secondary = USB, Mode = Failover',
     'Router admin → WAN → Dual WAN = ON'),
    ('Failover test: unplug InstyConnect PoE cable — ASUS switches to Starlink within 60 seconds',
     'Dashboard WAN card turns blue = Starlink active'),
    ('Failback test: reconnect InstyConnect PoE cable — ASUS switches back to cellular within 60 seconds',
     'WAN card returns to green = cellular restored'),
    ('Reconnect InstyConnect PoE cable after failover test', 'Restore normal WAN config'),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('1.1d  AMPRNet / 44Net Gateway'), SP(2), rows_table([
    ('Gateway Pi powered on at 192.168.50.2 (check green power LED)',
     'Must be on same UniFi switch'),
    ('AMPRNet Gateway card on FieldComms dashboard shows green  (tunnel UP)',
     'Dashboard bottom — amprgate card = green'),
    ('Gateway status page loads at http://192.168.50.2:9000',
     'Must show callsign login page'),
    ('Callsign login works — enter a valid FCC callsign at http://192.168.50.2:9000',
     'Tunnel status dashboard must load'),
    ('Tunnel status shows UP with a 44.x.x.x/29 AMPRNet address assigned',
     'WireGuard tunnel to AMPRNet confirmed'),
    ('Last handshake time shown — within the past 5 minutes',
     'Tunnel actively maintained'),
    ('Access log entry created — check /var/log/amprgate-access.log on gateway Pi',
     'SSH gateway Pi: tail /var/log/amprgate-access.log'),
    ('Tunnel control blocked from network — port 9001 not reachable from EMCOMM-NET',
     'curl 192.168.50.2:9001 = connection refused'),
    ('WAN Status dashboard shows AMPRNet tunnel state',
     'wan-status.html — AMPRNet section = UP'),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('1.2  Pre-Flight Health Check (http://192.168.50.1/preflight.html)'), SP(2), rows_table([
    ('Pre-flight checklist page loads', ''),
    ('All checklist items visible and checkable', ''),
    ('Pass/Fail verdict renders correctly (GO / CAUTION / NO-GO)', ''),
    ('Export Report generates a printable summary', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('1.3  Dashboard Health Monitor (port 5051)'), SP(2), rows_table([
    ('Dashboard health panel shows CPU temperature', ''),
    ('Dashboard health panel shows memory usage', ''),
    ('Dashboard health panel shows disk usage', ''),
    ('Service status shown for: nginx, FCC Lookup API, Health Monitor', ''),
    ('Service status shown for: Graywolf APRS, Pat Winlink, Kiwix', ''),
    ('Service status shown for: GPS Daemon, NTP/Chrony, Dead Man\'s Switch, ICS Platform', ''),
    ('Internet connectivity indicator shown', ''),
    ('GPS status shown (fix / no fix)', 'Requires USB GPS'),
    ('Health data refreshes automatically', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('1.4  Dashboard Mode Switcher'), SP(2), rows_table([
    ('Three mode buttons visible in the mode bar: 📻 Amateur Radio · 🚔 Starcom / Public Safety · 🏛 ICS', ''),
    ('Mode selection persists across browser sessions (saved to localStorage)', ''),
    ('Amateur mode — Net Ops: Net Control Logger, Observer Mode, JS8Call, APRS Tactical Map', ''),
    ('Amateur mode — Reference: Callsign Lookup, HF Propagation, Repeaters, Grid Square, Cheat Sheets', ''),
    ('Amateur mode — Forms: NTS Radiogram, ICS-213, ICS-214, Print Center, Reference Library', ''),
    ('Amateur mode — Safety: Dead Man\'s Switch, Roster, Pre-Flight Checklist', ''),
    ('Starcom mode — Net Ops: Starcom Net Logger, Weather Net, SAR Net, Observer Mode',
     'Starcom is now its own dedicated mode'),
    ('Starcom mode — Resources: Resource Tracking Map, Resource Board, Member Roster, Facilities', ''),
    ('Starcom mode — ICS: ICS Platform, ICS-213, ICS-214, Print Center', ''),
    ('ICS mode — Platform: ICS Command, Operations, Planning, Logistics, Finance, Planning P', ''),
    ('ICS mode — Resources: Tactical Map, Resource Map, Resource Board, Roster, Facilities', ''),
    ('ICS mode — Forms: ICS-213, ICS-214, ICS-309, Print Center, Reference Library', ''),
    ('ICS mode — Comms: Net Control, Starcom, Winlink Form Import, Repeater Database, Cheat Sheets', ''),
    ('URL param ?mode=starcom loads dashboard in Starcom mode directly', ''),
])])); story.append(PB())

# ── SECTION 2 — NET CONTROL LOGGING ──────────────────────────────────────────
story.append(KeepTogether([section('2 · Net Control Logging',
    'Amateur net control and Starcom net logging'), SP(6)]))

story.append(KeepTogether([subsection('2.1  Amateur Net Control (http://192.168.50.1/netcontrol.html)'), SP(2), rows_table([
    ('Create a new net — name, type, frequency, drill flag', ''),
    ('Net appears in the net list and can be selected', ''),
    ('Log a net entry (callsign, name, status, location, remarks)', ''),
    ('Entry appears in the log with UTC timestamp', ''),
    ('Log Traffic button adds a traffic / message entry', ''),
    ('Check-In from roster chip works (pre-populated callsign)', ''),
    ('Remove an entry from the log', ''),
    ('Promote an operator to the roster from a net entry', ''),
    ('Export ICS-309 opens a printable comms log for the selected net', ''),
    ('Export JSON downloads the net data as a file', ''),
    ('Close net marks it as closed and archives it', ''),
    ('Multiple nets open simultaneously — each on its own tab', ''),
    ('Observer link copies the read-only URL to clipboard', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('2.2  Starcom Net Logger (http://192.168.50.1/starcom.html)'), SP(2), rows_table([
    ('Create a new Starcom net (name, talkgroup, channel, dispatch center)', ''),
    ('Log a check-in by Radio ID and Unit Name', ''),
    ('Unit status cycles correctly: Available → Deployed → Staging → Out of Service', ''),
    ('Multiple simultaneous nets — each net badge shown in active nets panel', 'Core Starcom feature'),
    ('Clicking a net badge switches to that net log', ''),
    ('Weather Net quick-launch card opens pre-configured weather net', ''),
    ('SAR Net quick-launch card opens pre-configured SAR net', ''),
    ('Export ICS-309 works for the Starcom net', ''),
    ('Close net archives all entries', ''),
])])); story.append(PB())

# ── SECTION 3 — RESOURCE & PERSONNEL ─────────────────────────────────────────
story.append(KeepTogether([section('3 · Resource & Personnel Management', ''), SP(6)]))

story.append(KeepTogether([subsection('3.1  Member Roster (http://192.168.50.1/roster.html)'), SP(2), rows_table([
    ('Member list loads from server database', ''),
    ('Add a new member (name, callsign, role, certifications)', ''),
    ('Edit an existing member', ''),
    ('Delete a member', ''),
    ('Check in a member to the active activation', ''),
    ('Walk-in check-in (non-roster member)', ''),
    ('Export CSV downloads the full roster', ''),
    ('Import CSV loads a roster from file', ''),
    ('Export activation log downloads the check-in record', ''),
    ('Filter / search the roster', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('3.2  Resource Board (http://192.168.50.1/resources.html)'), SP(2), rows_table([
    ('Resource cards load from server', ''),
    ('Add a resource (name, type, owner, location, status)', ''),
    ('Status badge cycles through all 5 states: Available / Assigned / Staging / OOS / Demobilized', ''),
    ('Edit a resource', ''),
    ('Delete a resource', ''),
    ('Filter by type and status', ''),
    ('Stats strip at top updates live', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('3.3  Facilities (http://192.168.50.1/facilities.html)'), SP(2), rows_table([
    ('Seeded facilities load (McHenry County EOC, etc.)', ''),
    ('Add a new facility (name, type, address, lat/lon)', ''),
    ('Edit a facility', ''),
    ('Delete a facility', ''),
    ('Copy address to clipboard', ''),
    ('Export CSV', ''),
    ('Facility detail modal shows all fields', ''),
])])); story.append(PB())

# ── SECTION 4 — MAPS & TACTICAL ───────────────────────────────────────────────
story.append(KeepTogether([section('4 · Maps & Tactical Display', ''), SP(6)]))

story.append(KeepTogether([subsection('4.1  APRS Tactical Map (http://192.168.50.1/tactical.html)'), SP(2), rows_table([
    ('Map loads with offline tile layer (USGS Imagery+Topo)', ''),
    ('APRS stations appear as markers from Graywolf', 'Requires TNC/radio'),
    ('Clicking a station marker shows callsign and details', ''),
    ('Resource overlays from Resource Board appear on the map', ''),
    ('Draw marker, polygon, circle, and route overlays', ''),
    ('KML export downloads current overlays', ''),
    ('Range ring draws around current position', ''),
    ('Station list sidebar filters by callsign', ''),
    ('Station age threshold hides old stations', ''),
    ('Tile set selector switches between USGS/OSM/Esri', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('4.2  Resource Map / Starcom Map (http://192.168.50.1/resmap.html)'), SP(2), rows_table([
    ('Map loads with offline tiles', ''),
    ('Add a unit to the map (place a marker)', ''),
    ('Edit a unit\'s details', ''),
    ('Remove a unit from the map', ''),
    ('Drag unit marker to new position — coordinates update', ''),
    ('Draw a zone polygon', ''),
    ('Zone listed in Zones tab', ''),
    ('Clear zones removes all drawn zones', ''),
    ('Unit status colors display correctly', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('4.3  Grid Square Calculator (http://192.168.50.1/grid.html)'), SP(2), rows_table([
    ('Convert a lat/lon to Maidenhead grid square', ''),
    ('Convert a grid square to lat/lon', ''),
    ('Calculate distance and bearing between two grid squares', ''),
    ('Use My Location gets device GPS coordinates', 'Mobile device'),
])])); story.append(PB())

# ── SECTION 5 — ICS PLATFORM ──────────────────────────────────────────────────
story.append(KeepTogether([section('5 · ICS Platform', 'http://192.168.50.1/ics/'), SP(6)]))

story.append(KeepTogether([subsection('5.1  Incident Management'), SP(2), rows_table([
    ('Create a new incident (name, type, location, IC, op period)', ''),
    ('Incident becomes the active incident for all ICS pages', ''),
    ('Advance operational period increments the period number', ''),
    ('Close / archive an incident', ''),
    ('ICS navigation tabs visible: Command / Operations / Planning / Logistics / Finance / Planning P', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('5.2  Command Section (ics/command.html)'), SP(2), rows_table([
    ('100-item objectives dropdown present and organized into 13 groups', ''),
    ('Selecting an objective pre-fills the text field', ''),
    ('Editing and adding a custom objective works', ''),
    ('Objectives list correctly and can be deleted', ''),
    ('Safety message field accepts input', ''),
    ('Situation report fields save correctly', ''),
    ('Save persists data for the active incident', ''),
    ('MCESV/MCEMA-specific objectives appear in the last group', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('5.3  Operations Section (ics/operations.html)'), SP(2), rows_table([
    ('T-card board loads for the active incident', ''),
    ('Add a resource assignment (callsign, assignment, status)', ''),
    ('Drag-and-drop T-cards between status columns', ''),
    ('Set resource status: Available / Assigned / Staging / Out of Service / Released', ''),
    ('Delete a resource', ''),
    ('Open resource detail panel and update assignment', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('5.4  Planning Section (ics/planning.html)'), SP(2), rows_table([
    ('IAP tracker shows all ICS forms with completion checkboxes', ''),
    ('Resource status table shows counts by type', ''),
    ('Documents tab lists linked incident documents', ''),
    ('Save persists planning section data', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('5.5  Logistics Section (ics/logistics.html)'), SP(2), rows_table([
    ('ICS-205 comms plan pre-filled with McHenry County channels', ''),
    ('Supply tracking entries can be added and deleted', ''),
    ('Meal log entries can be added', ''),
    ('Check-in list (ICS-211) accepts entries', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('5.6  Finance / Admin Section (ics/finance.html)'), SP(2), rows_table([
    ('Cost tracking entries can be added and deleted', ''),
    ('Time tracking entries can be added and deleted', ''),
    ('Procurement entries can be added and deleted', ''),
    ('Export CSV downloads the finance data', ''),
])])); story.append(PB())

# ── SECTION 6 — ICS FORMS ─────────────────────────────────────────────────────
story.append(KeepTogether([section('6 · ICS Forms', ''), SP(6)]))

story.append(KeepTogether([subsection('6.1  ICS-213 General Message (http://192.168.50.1/ics213.html)'), SP(2), rows_table([
    ('Form fields all accept input (To, From, positions, date, time, subject, message, reply)', ''),
    ('Auto-fill date/time populates current UTC', ''),
    ('Save to Log saves the form to the local log', ''),
    ('Form log shows saved forms, most recent first', ''),
    ('Load a saved form from the log', ''),
    ('Delete a saved form', ''),
    ('Print button opens browser print dialog', ''),
    ('Clear Form resets all fields', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('6.2  ICS-214 Activity Log (http://192.168.50.1/ics214.html)'), SP(2), rows_table([
    ('Header fields accept input (incident, unit, leader, op period)', ''),
    ('Add Personnel adds a row (name, position, agency)', ''),
    ('Remove Personnel removes a row', ''),
    ('Add Entry adds an activity log row', ''),
    ('Auto Timestamp populates current UTC on a row', ''),
    ('Remove Entry removes an activity row', ''),
    ('Generate Form renders the print-ready ICS-214', ''),
    ('Print works correctly', ''),
    ('Save Local persists the form on the device', ''),
    ('Clear Form resets everything', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('6.3  ICS-309 Communications Log (http://192.168.50.1/ics309.html)'), SP(2), rows_table([
    ('Header fields accept input (incident name, op period, radio operator, station/net)', ''),
    ('Add (timestamp now) inserts a row with current UTC time', ''),
    ('Log rows accept From, To, and Subject entries', ''),
    ('Delete a log row', ''),
    ('Generate Form renders the print-ready ICS-309', ''),
    ('Save to Incident files the log with the active incident', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('6.4  Planning P (http://192.168.50.1/ics/planningp.html)'), SP(2), rows_table([
    ('Page loads with Planning P reference diagram image on the left', ''),
    ('All 15 phase buttons present in the center panel', ''),
    ('Phase buttons organized in 5 color-coded groups (gray/yellow/red/green/teal)', ''),
    ('Clicking a phase highlights it and populates the right detail panel', ''),
    ('Detail panel shows Standard Agenda, Required Forms, and Who Should Attend', ''),
    ('Form chips in detail panel open the correct form page when clicked', ''),
    ('Generate briefing sheet opens printable one-page cover for the selected phase', ''),
    ('Briefing sheet includes phase name, agenda, forms table, and attendance table', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('6.5  NTS Radiogram (http://192.168.50.1/nts.html)'), SP(2), rows_table([
    ('Auto-fill date/time populates current date and time', ''),
    ('Auto-fill number generates a sequence number', ''),
    ('All preamble fields accept input (number, precedence, handling, origin, check, place, time)', ''),
    ('Address and text fields accept input', ''),
    ('Generate Radiogram renders the formatted radiogram', ''),
    ('Save to Log saves the radiogram', ''),
    ('Load from Log restores a saved radiogram', ''),
    ('Delete a saved radiogram', ''),
    ('Copy Text copies the radiogram to clipboard', ''),
    ('Clear Form resets all fields', ''),
])])); story.append(PB())

# ── SECTION 7 — WINLINK ───────────────────────────────────────────────────────
story.append(KeepTogether([section('7 · Winlink', ''), SP(6)]))

story.append(KeepTogether([subsection('7.1  Pat Winlink Backup (http://192.168.50.1:8090)'), SP(2), rows_table([
    ('Pat Winlink loads at port 8090', ''),
    ('Pat dashboard card on FieldComms opens the correct URL', ''),
    ('Can compose and send a message (requires TNC/radio or internet)', 'Optional'),
    ('Pat service shows as running in Health Monitor', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('7.2  Winlink Form Import (http://192.168.50.1/winlink-import.html)'), SP(2), rows_table([
    ('Page loads from dashboard ICS mode card', ''),
    ('Drop zone accepts an RMS_Express_Form XML file', ''),
    ('Paste text area accepts pasted XML or message text', ''),
    ('Parse Form Data button processes the input', ''),
    ('ICS-213 form is detected and labeled correctly', ''),
    ('ICS-214 form is detected and labeled correctly', ''),
    ('ICS-309 form is detected and labeled correctly', ''),
    ('Unknown form type shows a warning (not an error)', ''),
    ('All mapped fields appear in the editable review grid', ''),
    ('Incident dropdown loads active incidents', ''),
    ('Archive to Incident saves the form to the incident record', ''),
    ('Open in ICS form routes ICS-213/214/309 to the correct form page', ''),
])])); story.append(PB())

# ── SECTION 8 — CALLSIGN & RADIO TOOLS ────────────────────────────────────────
story.append(KeepTogether([section('8 · Callsign & Radio Tools', ''), SP(6)]))

story.append(KeepTogether([subsection('8.1  FCC Callsign Lookup (http://192.168.50.1/callsign.html)'), SP(2), rows_table([
    ('Quick lookup by callsign returns name, license class, address, grid, FRN', ''),
    ('Lookup works offline (from local FCC database)', ''),
    ('Advanced search by name, city, state, license class works', ''),
    ('Add to Roster button adds the licensee to the member roster', ''),
    ('FCC database record count and last-update date shown at bottom', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('8.2  Repeater Database (http://192.168.50.1/repeaters.html)'), SP(2), rows_table([
    ('Page loads and shows the three source tabs (Offline File, Server API, Sample)', ''),
    ('Sample data tab shows SAMPLE-1/2/3 placeholders with "not a real repeater" warning', ''),
    ('Offline File tab: drag-and-drop a RepeaterBook CSV loads and displays repeaters', ''),
    ('Filter by band (2m, 70cm, etc.) works', ''),
    ('Filter by state works', ''),
    ('Filter by ARES / SKYWARN / RACES works', ''),
    ('Filter by mode (FM, DMR, C4FM, etc.) works', ''),
    ('Sort by callsign, frequency, and city works', ''),
    ('Clicking a repeater row opens the detail panel', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('8.3  HF Propagation (http://192.168.50.1/propagation.html)'), SP(2), rows_table([
    ('Page loads and attempts to fetch solar data from HamQSL', 'Requires internet'),
    ('SFI, K-index, A-index displayed', ''),
    ('Band condition indicators show (10m–80m)', ''),
    ('Offline fallback message shown when no internet', ''),
])])); story.append(PB())

# ── SECTION 9 — REFERENCE, PRINT & KIWIX ─────────────────────────────────────
story.append(KeepTogether([section('9 · Reference, Print & Kiwix', ''), SP(6)]))

story.append(KeepTogether([subsection('9.1  Reference Library (http://192.168.50.1/refs.html)'), SP(2), rows_table([
    ('Document list loads from server', ''),
    ('Upload a document (PDF, DOCX, image) via drag-and-drop', ''),
    ('Upload via Browse button works', ''),
    ('PDF thumbnail generated after upload', ''),
    ('Filter by category works', ''),
    ('Search by keyword finds matching documents', ''),
    ('Edit document metadata', ''),
    ('Download a document', ''),
    ('Delete a document', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('9.2  Cheat Sheets (http://192.168.50.1/cheatsheets.html)'), SP(2), rows_table([
    ('Phonetic alphabet table displays correctly', ''),
    ('Q-codes reference table displays', ''),
    ('Band plan reference displays', ''),
    ('CTCSS/DCS tones table displays', ''),
    ('ICS position titles reference displays', ''),
    ('Print button sends page to printer', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('9.3  Print Center (http://192.168.50.1/printcenter.html)'), SP(2), rows_table([
    ('ICS-213 preview and print works', ''),
    ('ICS-214 preview and print works', ''),
    ('NTS Radiogram preview and print works', ''),
    ('Pre-Flight Checklist preview and print works', ''),
    ('Phonetic Alphabet pocket card prints', ''),
    ('Q-Codes & Prowords reference prints', ''),
    ('Net Control Log ICS-309 export and print works', ''),
    ('Starcom Net Log ICS-309 export and print works', ''),
    ('Roster / Member Directory prints', ''),
    ('Resource Board status print works', ''),
    ('Incident cover sheet (Generate Cover) creates a cover page', ''),
    ('Operator Access Cards PDF generates (Avery 5371 format)', ''),
    ('Print button on ICS-213 opens browser print dialog', ''),
    ('If CUPS installed: http://192.168.50.1:631 loads CUPS admin UI', 'Option B — USB printer'),
    ('If CUPS installed: USB printer visible in CUPS printer list', 'Option B'),
    ('If CUPS installed: test page prints successfully from CUPS UI', 'Option B'),
    ('If CUPS installed: Windows device can discover and print to shared printer', 'Option B'),
    ('If network printer: printer visible in browser print dialog from EMCOMM-NET device', 'Option C'),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('9.4  Kiwix Offline Library (http://192.168.50.1:8081)'), SP(2), rows_table([
    ('Kiwix loads at port 8081', ''),
    ('At least one ZIM file (WikiMed, Wikipedia, iFixit, or Wikivoyage) is present', ''),
    ('Can search and retrieve articles', ''),
    ('Kiwix dashboard card opens the correct URL', ''),
])])); story.append(PB())

# ── SECTION 10 — DEAD MAN'S SWITCH ────────────────────────────────────────────
story.append(KeepTogether([section('10 · Dead Man\'s Switch', 'http://192.168.50.1/deadmans.html'), SP(6)]))
story.append(KeepTogether([subsection('10.1  Dead Man\'s Switch'), SP(2), rows_table([
    ('Page loads and shows active nets', ''),
    ('Arm button activates monitoring for a net', ''),
    ('Countdown timer displays and counts down', ''),
    ('Reset button resets the countdown without disarming', ''),
    ('Disarm button stops monitoring', ''),
    ('DMS service shown as active in health monitor', ''),
])])); story.append(PB())

# ── SECTION 11 — OPERATOR IDENTITY ────────────────────────────────────────────
story.append(KeepTogether([section('11 · Operator Identity', ''), SP(6)]))
story.append(KeepTogether([subsection('11.1  Identity System'), SP(2), rows_table([
    ('First load prompts for operator identity (callsign/Radio ID/name, role)', ''),
    ('Identity persists across page reloads and navigation', ''),
    ('Callsign/ID shown in dashboard header after setup', ''),
    ('Role shown correctly: NCS / Operator / Liaison / EC', ''),
    ('Identity can be changed / reset', ''),
    ('Observer page does NOT prompt for identity (read-only)', ''),
])])); story.append(PB())

# ── SECTION 12 — SYSTEM SERVICES ──────────────────────────────────────────────
story.append(KeepTogether([section('12 · System Services',
    'Verify via systemctl status <service> on the Pi, or via the dashboard health monitor.'), SP(6)]))
story.append(KeepTogether([subsection('12.1  Service Status'), SP(2), rows_table([
    ('fcc-lookup.service — main API running on port 5050', ''),
    ('health-monitor.service — health API running on port 5051', ''),
    ('wan-monitor.service — WAN status monitor polling InstyConnect and Starlink', ''),
    ('amprgate-poll.service — polls gateway Pi every 30s for 44Net status', ''),
    ('ics-platform.service — ICS API running on port 5055', ''),
    ('fieldcomms-refs.service — reference library API running on port 5056', ''),
    ('fieldcomms-tiles.service — tile server running on port 8083', ''),
    ('deadmans.service — Dead Man\'s Switch service running', ''),
    ('nginx.service — web server running on port 80', ''),
    ('kiwix.service — Kiwix library running on port 8081', ''),
    ('pat.service — Pat Winlink running on port 8090', ''),
    ('yaac.service — YAAC APRS client running on port 8082', 'If APRS installed'),
    ('graywolf.service — Graywolf APRS running on port 8080', 'If APRS installed'),
    ('cups.service — CUPS print server running on port 631', 'If printer installed'),
    ('avahi-daemon.service — mDNS/Bonjour running', ''),
    ('gpsd.service — GPS daemon running (if USB GPS connected)', 'If GPS installed'),
    ('fcc-refresh.timer — weekly FCC database refresh timer active', ''),
    ('repeater-refresh.timer — monthly repeater database refresh timer active', ''),
    ('Firewall (ufw) enabled — ports 80, 631, 5050-5056, 8080-8090 open', ''),
])])); story.append(SP(6))

story.append(KeepTogether([subsection('12.2  Gateway Pi Services  (192.168.50.2 — SSH separately)'), SP(2), rows_table([
    ('amprgate-status.service — status page running on port 9000',
     'SSH 192.168.50.2: systemctl status amprgate-status'),
    ('wg-quick@ampr0.service — WireGuard tunnel running',
     'SSH 192.168.50.2: systemctl status wg-quick@ampr0'),
    ('Port 9000 accessible from EMCOMM-NET (callsign login page loads)',
     'Open http://192.168.50.2:9000 from EMCOMM-NET'),
    ('Port 9001 NOT accessible from EMCOMM-NET (connection refused)',
     'curl 192.168.50.2:9001 from EMCOMM-NET = fail'),
    ('Access log file exists at /var/log/amprgate-access.log',
     'SSH gateway Pi: check /var/log/amprgate-access.log'),
    ('UFW firewall active on gateway Pi — port 9001 blocked externally',
     'SSH gateway Pi: ufw status — 9001 = DENY'),
])])); story.append(PB())

# ── SIGN-OFF ───────────────────────────────────────────────────────────────────
story.append(section('Beta Test Sign-Off', ''))
story.append(SP(10))

signoff_data = [
    [P('Section', S('sh2', fontName='Helvetica-Bold', fontSize=8, textColor=white, leading=10)),
     P('Items', S('sh2', fontName='Helvetica-Bold', fontSize=8, textColor=white, leading=10)),
     P('Pass', S('sh2', fontName='Helvetica-Bold', fontSize=8, textColor=white, leading=10)),
     P('Fail', S('sh2', fontName='Helvetica-Bold', fontSize=8, textColor=white, leading=10)),
     P('Not Tested', S('sh2', fontName='Helvetica-Bold', fontSize=8, textColor=white, leading=10))],
]
for sec_name in ['1 · System & Infrastructure  (incl. WAN + 44Net)', '2 · Net Control Logging',
                  '3 · Resource & Personnel', '4 · Maps & Tactical',
                  '5 · ICS Platform', '6 · ICS Forms', '7 · Winlink',
                  '8 · Callsign & Radio Tools', '9 · Reference, Print & Kiwix',
                  '10 · Dead Man\'s Switch', '11 · Operator Identity',
                  '12 · System Services', 'TOTALS']:
    bold = sec_name == 'TOTALS'
    fn = 'Helvetica-Bold' if bold else 'Helvetica'
    signoff_data.append([
        P(sec_name, S('sr', fontName=fn, fontSize=8.5, leading=11)),
        P('', S('sc')), P('', S('sc')), P('', S('sc')), P('', S('sc')),
    ])

st = Table(signoff_data, colWidths=[3.0*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1.1*inch])
st.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0),  EOC),
    ('TEXTCOLOR',     (0,0), (-1,0),  white),
    ('ROWBACKGROUNDS',(0,1), (-1,-2), [white, LGRAY]),
    ('BACKGROUND',    (0,-1),(-1,-1), MGRAY),
    ('GRID',          (0,0), (-1,-1), 0.4, LINE),
    ('TOPPADDING',    (0,0), (-1,-1), 6),
    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ('LEFTPADDING',   (0,0), (-1,-1), 8),
    ('RIGHTPADDING',  (0,0), (-1,-1), 8),
    ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
]))
story.append(st)
story.append(SP(16))

story.append(P('<b>Failures requiring follow-up:</b>', S('fl', fontSize=9, textColor=EOC)))
story.append(SP(40))
story.append(HR(LINE, 0.5))
story.append(SP(16))

so_tbl = Table([[
    P('<b>Signed off by (name / callsign):</b>', S('so', fontSize=9)),
    P('', S('so', fontSize=9)),
    P('<b>Date:</b>', S('so', fontSize=9)),
    P('', S('so', fontSize=9)),
]], colWidths=[1.8*inch, 2.2*inch, 0.6*inch, CW-4.6*inch])
so_tbl.setStyle(TableStyle([
    ('LINEBELOW', (1,0), (1,0), 0.5, LINE),
    ('LINEBELOW', (3,0), (3,0), 0.5, LINE),
    ('TOPPADDING', (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
]))
story.append(so_tbl)
story.append(SP(10))
story.append(P(
    'Submit completed checklist (photo or scan) to the project lead. Include this sheet plus '
    'any additional failure notes. Reference the user manual for expected behavior of any item.',
    S('fn', fontSize=8, textColor=HexColor('#445566'), leading=12)))

# ── Build ─────────────────────────────────────────────────────────────────────
out = '/mnt/user-data/outputs/ESV_Beta_Test_Checklist.pdf'
doc = SimpleDocTemplate(
    out, pagesize=letter,
    leftMargin=M, rightMargin=M,
    topMargin=0.55*inch, bottomMargin=0.42*inch,
    title='FieldComms IMS v1.0 — Beta Test Checklist',
    author='McHenry County Emergency Services Volunteers and McHenry County Emergency Management Agency')
doc.build(story, canvasmaker=NC)

# Append Pi 500 addendum
import os, io
from pypdf import PdfReader, PdfWriter
addendum = '/home/claude/pi500_addendum.pdf'
if os.path.exists(addendum):
    base = PdfReader(out); add = PdfReader(addendum)
    w = PdfWriter()
    for p in base.pages: w.add_page(p)
    for p in add.pages:  w.add_page(p)
    buf = io.BytesIO(); w.write(buf)
    with open(out, 'wb') as f: f.write(buf.getvalue())

r = PdfReader(out)
print(f'BUILT: {out}')
print(f'Pages: {len(r.pages)}')
