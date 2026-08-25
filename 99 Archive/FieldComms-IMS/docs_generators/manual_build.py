#!/usr/bin/env python3
"""
manual_build.py — Assembles the FieldComms Complete User Manual v1.0
Imports all chapter modules, builds TOC, and produces the final PDF.
Output: /mnt/user-data/outputs/FieldComms_Complete_User_Manual_v1.0.pdf
"""
import sys, os, io
sys.path.insert(0, os.path.dirname(__file__))

from manual_framework import *
from manual_ch_01_07 import ch1, ch2, ch3, ch4, ch5, ch6, ch7
from manual_ch_08_18 import ch8, ch9, ch10, ch11, ch12, ch13, ch14, ch15, ch16, ch17, ch18
from manual_ch_19_36 import (ch19, ch20, ch21, ch22, ch23, ch24, ch25, ch26,
                              ch27, ch28, ch29, ch30, ch31, ch32, ch33, ch34,
                              ch35, ch36, ch_appendix)

from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.colors import HexColor

# Alias internal style maker for use in this module
_s = lambda name, **kw: ParagraphStyle(
    name,
    fontName=kw.get('fontName','Helvetica'),
    fontSize=kw.get('fontSize',10),
    textColor=kw.get('textColor',black),
    leading=kw.get('leading',14),
    alignment=kw.get('alignment',0),
    spaceAfter=kw.get('spaceAfter',0),
    spaceBefore=kw.get('spaceBefore',0),
)

# ── Cover page — drawn by ManualCanvas._draw_cover() ─────────────────────────
# The cover is rendered entirely on canvas (page 1).
# This function returns just a PageBreak to occupy page 1 in the story.
def cover():
    return [PB()]

# ── Table of Contents ─────────────────────────────────────────────────────────
def toc_page(chapters):
    """chapters = list of (num, title, url) tuples"""
    story = []

    toc_hdr = Table([[
        P('Table of Contents',
          _s('toch', fontName='Helvetica-Bold', fontSize=20, textColor=EOC,
             leading=24)),
    ]], colWidths=[CW])
    toc_hdr.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 2, GOLD),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(toc_hdr)
    story.append(SP(10))

    for num, title, url in chapters:
        row = Table([[
            P(str(num),
              _s('tcn', fontName='Helvetica-Bold', fontSize=8.5, textColor=EOC_LT,
                 alignment=TA_CENTER, leading=11)),
            P(title, _s('tct', fontSize=8.5, leading=11)),
            P(url or '',
              _s('tcu', fontName='Courier', fontSize=7, textColor=HexColor('#6080a0'),
                 leading=11)),
        ]], colWidths=[0.35*inch, CW*0.55, CW-0.35*inch-CW*0.55])
        row.setStyle(TableStyle([
            ('LINEBELOW',     (0,0), (-1,-1), 0.2, LINE),
            ('TOPPADDING',    (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING',   (0,0), (-1,-1), 4),
            ('RIGHTPADDING',  (0,0), (-1,-1), 4),
            ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(row)

    story.append(PB())
    return story


# ── Chapter registry ──────────────────────────────────────────────────────────
CHAPTERS = [
    (1,  'Introduction & System Overview',                    ''),
    (2,  'Getting Started — Connecting to FieldComms',        'http://192.168.50.1/'),
    (3,  'The Main Dashboard',                                'http://192.168.50.1/'),
    (4,  'Member Roster',                                     'http://192.168.50.1/roster.html'),
    (5,  'Operator Identity System',                          ''),
    (6,  'Amateur Net Control Logger',                        'http://192.168.50.1/netcontrol.html'),
    (7,  'Starcom Net Logger',                                'http://192.168.50.1/starcom.html'),
    (8,  'Observer Mode — Read-Only Net View',                'http://192.168.50.1/observer.html'),
    (9,  'FCC Callsign Lookup',                               'http://192.168.50.1/callsign.html'),
    (10, 'Tactical APRS Map',                                 'http://192.168.50.1/tactical.html'),
    (11, 'Starcom Resource Tracking Map',                     'http://192.168.50.1/resmap.html'),
    (12, 'Resource Board',                                    'http://192.168.50.1/resources.html'),
    (13, "Dead Man's Switch — Net Inactivity Monitor",        'http://192.168.50.1/deadmans.html'),
    (14, 'Pre-Flight Deployment Checklist',                   'http://192.168.50.1/preflight.html'),
    (15, 'ICS Platform — Overview',                           'http://192.168.50.1/ics/'),
    (16, 'ICS Command Section',                               'http://192.168.50.1/ics/command.html'),
    (17, 'ICS Operations Section',                            'http://192.168.50.1/ics/operations.html'),
    (18, 'ICS Planning Section',                              'http://192.168.50.1/ics/planning.html'),
    (19, 'ICS Logistics Section',                             'http://192.168.50.1/ics/logistics.html'),
    (20, 'ICS Finance / Admin Section',                       'http://192.168.50.1/ics/finance.html'),
    (21, 'NTS Radiogram Generator',                           'http://192.168.50.1/nts.html'),
    (22, 'ICS-213 General Message',                           'http://192.168.50.1/ics213.html'),
    (23, 'ICS-214 Activity Log & ICS-309',                    'http://192.168.50.1/ics214.html'),
    (24, 'Winlink Form Import & Incident Archiving',          'http://192.168.50.1/winlink-import.html'),
    (25, 'HF Propagation',                                    'http://192.168.50.1/propagation.html'),
    (26, 'Repeater Database',                                 'http://192.168.50.1/repeaters.html'),
    (27, 'Facilities Directory',                              'http://192.168.50.1/facilities.html'),
    (28, 'Grid Square Calculator',                            'http://192.168.50.1/grid.html'),
    (29, 'Radio Cheat Sheets',                                'http://192.168.50.1/cheatsheets.html'),
    (30, 'Print Center',                                      'http://192.168.50.1/printcenter.html'),
    (31, 'Reference Library',                                 'http://192.168.50.1/refs.html'),
    (32, 'Kiwix Offline Library',                             'http://192.168.50.1:8081/'),
    (33, 'Offline Maps, GPS & Health Monitor',                ''),
    (34, 'Network Hardware — ASUS RT-BE58 Go & UniFi Switch', ''),
    (35, 'JS8Call — HF Digital Keyboard Messaging (Windows)', ''),
    (36, 'ICS Planning P — Operational Planning Cycle',       'http://192.168.50.1/ics/planningp.html'),
    (34, 'Appendix — Administration & Quick Reference',       ''),
]

CHAPTER_FUNCS = [
    ch1, ch2, ch3, ch4, ch5, ch6, ch7,
    ch8, ch9, ch10, ch11, ch12, ch13, ch14, ch15, ch16, ch17, ch18,
    ch19, ch20, ch21, ch22, ch23, ch24, ch25, ch26, ch27, ch28,
    ch29, ch30, ch31, ch32, ch33, ch34, ch35, ch36, ch_appendix,
]

# ── Build ─────────────────────────────────────────────────────────────────────
out = '/mnt/user-data/outputs/FieldComms_Complete_User_Manual_v1.0.pdf'

story = []
story += cover()
story += toc_page(CHAPTERS)
for fn in CHAPTER_FUNCS:
    story += fn()

doc = SimpleDocTemplate(
    out, pagesize=letter,
    leftMargin=M, rightMargin=M,
    topMargin=0.60*inch, bottomMargin=0.48*inch,
    title='FieldComms IMS v1.0 — Complete User Manual',
    author='McHenry County Emergency Services Volunteers and McHenry County Emergency Management Agency')
doc.build(story, canvasmaker=ManualCanvas)

# Append Pi 500 addendum
from pypdf import PdfReader, PdfWriter
addendum = os.path.join(os.path.dirname(__file__), '../../..', 'pi500_addendum.pdf')
# Also try /home/claude/pi500_addendum.pdf
for apath in [addendum, '/home/claude/pi500_addendum.pdf']:
    if os.path.exists(apath):
        base = PdfReader(out)
        add  = PdfReader(apath)
        w = PdfWriter()
        for p in base.pages: w.add_page(p)
        for p in add.pages:  w.add_page(p)
        buf = io.BytesIO()
        w.write(buf)
        with open(out, 'wb') as f: f.write(buf.getvalue())
        break

r = PdfReader(out)
print(f'BUILT: {out}')
print(f'Pages: {len(r.pages)}')
print(f'Chapters: {len(CHAPTER_FUNCS)}')
