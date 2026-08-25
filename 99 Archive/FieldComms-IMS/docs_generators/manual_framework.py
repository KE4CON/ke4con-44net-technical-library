#!/usr/bin/env python3
"""
manual_framework.py — Shared styles, helpers, and canvas for the
FieldComms Complete User Manual.
Import with: from manual_framework import *
"""
import datetime
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (Paragraph, Spacer, Table, TableStyle,
                                PageBreak, HRFlowable, KeepTogether)
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
PURPLE = HexColor('#5b2d8c')

# ── Layout ───────────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = letter
M  = 0.75 * inch
CW = PAGE_W - 2 * M
TODAY = datetime.date.today().strftime('%B %d, %Y')
ORG   = ('McHenry County Emergency Services Volunteers and '
         'McHenry County Emergency Management Agency')
SHORT = 'MCESV/MCEMA  ·  K9ESV'

# ── Style shortcuts ───────────────────────────────────────────────────────────
def _s(name, **kw):
    d = dict(fontName='Helvetica', fontSize=10, textColor=black,
             leading=14, spaceAfter=4, spaceBefore=2)
    d.update(kw)
    return ParagraphStyle(name, **d)

Body   = _s('Body', alignment=TA_JUSTIFY)
H1     = _s('H1',  fontName='Helvetica-Bold', fontSize=16, textColor=EOC,
            leading=20, spaceBefore=10, spaceAfter=6)
H2     = _s('H2',  fontName='Helvetica-Bold', fontSize=12, textColor=EOC_LT,
            leading=15, spaceBefore=8, spaceAfter=4)
H3     = _s('H3',  fontName='Helvetica-Bold', fontSize=10, textColor=EOC,
            leading=13, spaceBefore=6, spaceAfter=3)
Bullet = _s('Bullet', leftIndent=16, firstLineIndent=-10, leading=13, spaceAfter=3)
Code   = _s('Code', fontName='Courier', fontSize=8, leading=11,
            backColor=LGRAY, leftIndent=12, rightIndent=12)

# ── Helpers ───────────────────────────────────────────────────────────────────
def P(text, style=None):
    return Paragraph(text, style or Body)

def SP(n=6):
    return Spacer(1, n)

def HR(c=LINE, t=0.5):
    return HRFlowable(width='100%', thickness=t, color=c,
                      spaceBefore=3, spaceAfter=3)

def PB():
    return PageBreak()

def tbl(headers_or_data, rows_or_widths, widths=None):
    """
    Two calling conventions:
    tbl(['COL1','COL2'], [[r1c1,r1c2],[r2c1,r2c2]], widths=[...])
    tbl([['COL1','COL2'],[r1c1,r1c2]], widths=[...])   ← data already merged
    """
    if widths is None:
        # Called as tbl(data, widths)
        data_raw = headers_or_data
        widths   = rows_or_widths
        data = []
        for row in data_raw:
            data.append([P(str(c), _s('TC', fontSize=9, leading=12)) for c in row])
    else:
        headers = headers_or_data
        rows    = rows_or_widths
        hrow = [P(str(h), _s('TH', fontName='Helvetica-Bold', fontSize=8.5,
                              textColor=white, leading=11)) for h in headers]
        data = [hrow]
        for row in rows:
            data.append([P(str(c), _s('TC', fontSize=9, leading=12)) for c in row])

    t = Table(data, colWidths=widths, repeatRows=1, splitByRow=1)
    style = TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  EOC),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  white),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [white, LGRAY]),
        ('GRID',          (0, 0), (-1, -1), 0.35, LINE),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 7),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 7),
    ])
    t.setStyle(style)
    return t

def steps(items):
    """Return a list of numbered step paragraphs."""
    result = []
    for i, item in enumerate(items, 1):
        result.append(P(f'<b>{i}.</b>  {item}', Bullet))
    return result

def note(text, kind='note'):
    """Callout box. kind: 'note', 'tip', 'warn'"""
    cfg = {
        'note': (EOC_LT, HexColor('#eef2f7'), '📝'),
        'tip':  (GREEN,  HexColor('#e4f5ea'), '💡'),
        'warn': (AMBER,  HexColor('#fef3d8'), '⚠'),
    }
    color, bg, icon = cfg[kind]
    t = Table([[
        P(icon, _s('ni', fontSize=11, textColor=color, leading=13)),
        P(text, _s('nt', fontSize=9,  textColor=black, leading=13)),
    ]], colWidths=[0.28*inch, CW-0.28*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (-1, -1), bg),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',(0, 0), (-1, -1), 8),
        ('TOPPADDING',  (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING',(0,0), (-1, -1), 6),
        ('VALIGN',      (0, 0), (-1, -1), 'TOP'),
        ('LINEAFTER',   (0, 0), (0, -1),  2, color),
    ]))
    return t

def chapter(num, title, url=''):
    """Return a list of flowables opening a chapter."""
    items = []
    # Chapter number badge — 0.70*inch fits two-digit numbers at 28pt
    # Use fontSize=22 so two-digit numbers (10-36) fit in 0.65*inch without wrapping
    badge = Table([[
        P(str(num), _s('cn', fontName='Helvetica-Bold', fontSize=22,
                        textColor=white, alignment=TA_CENTER, leading=26)),
        P(title + (f'\n<font size="8" color="#8090b0">{url}</font>' if url else ''),
          _s('ct', fontName='Helvetica-Bold', fontSize=16, textColor=EOC,
             leading=20)),
    ]], colWidths=[0.65*inch, CW-0.65*inch])
    badge.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (0, -1),  EOC),
        ('BACKGROUND',  (1, 0), (1, -1),  LGRAY),
        ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',  (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING',(0,0), (-1,-1),  10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',(0, 0), (-1, -1), 10),
        ('LINEBELOW',   (0, 0), (-1, -1), 2, GOLD),
    ]))
    items.append(badge)
    items.append(SP(10))
    return items

# ── Canvas with running header/footer ─────────────────────────────────────────
class ManualCanvas(canvas.Canvas):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._saved = []
        self.TOTAL  = 0   # set after build

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for st in self._saved:
            self.__dict__.update(st)
            self.TOTAL = total   # restore after dict update (update clobbers it)
            n = self._pageNumber
            if n == 1:
                self._draw_cover()
            else:
                self._draw_chrome()
            super().showPage()
        super().save()

    def _draw_cover(self):
        """Full-page canvas-drawn cover — page 1 only."""
        # Full-page deep navy background
        self.setFillColor(EOC)
        self.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        # Gold accent stripes
        self.setFillColor(GOLD)
        self.rect(0, PAGE_H - 0.18*inch, PAGE_W, 0.18*inch, fill=1, stroke=0)
        self.setFillColor(GOLD)
        self.rect(0, 0, PAGE_W, 0.18*inch, fill=1, stroke=0)
        # Mid-tone band behind title
        self.setFillColor(HexColor('#1e4480'))
        self.rect(0, PAGE_H*0.38, PAGE_W, PAGE_H*0.36, fill=1, stroke=0)
        # Org / callsign header
        self.setFillColor(GOLD)
        self.setFont('Helvetica-Bold', 10)
        self.drawCentredString(PAGE_W/2, PAGE_H - 0.70*inch,
            'K9ESV  ·  McHenry County Emergency Services Volunteers')
        self.setFillColor(HexColor('#c0d4f0'))
        self.setFont('Helvetica', 9)
        self.drawCentredString(PAGE_W/2, PAGE_H - 0.88*inch,
            'and McHenry County Emergency Management Agency')
        # FIELDCOMMS title
        self.setFillColor(white)
        self.setFont('Helvetica-Bold', 58)
        self.drawCentredString(PAGE_W/2, PAGE_H*0.60, 'FIELDCOMMS')
        # Subtitle
        self.setFillColor(GOLD)
        self.setFont('Helvetica-Bold', 15)
        self.drawCentredString(PAGE_W/2, PAGE_H*0.545,
            'Incident Management System  v1.0')
        # Gold rule
        self.setStrokeColor(GOLD)
        self.setLineWidth(1.5)
        self.line(M*2, PAGE_H*0.505, PAGE_W - M*2, PAGE_H*0.505)
        # Document type
        self.setFillColor(white)
        self.setFont('Helvetica-Bold', 26)
        self.drawCentredString(PAGE_W/2, PAGE_H*0.448, 'COMPLETE USER MANUAL')
        # Sub-doc line
        self.setFillColor(HexColor('#c0d4f0'))
        self.setFont('Helvetica', 10)
        self.drawCentredString(PAGE_W/2, PAGE_H*0.395, 'v1.0')
        # Hardware / affiliation
        self.setFillColor(HexColor('#8090c0'))
        self.setFont('Helvetica', 9.5)
        self.drawCentredString(PAGE_W/2, PAGE_H*0.30,
            'RACES  ·  ARES  ·  Starcom  ·  K9ESV  ·  MCESV / MCEMA')
        # Date
        self.setFillColor(HexColor('#6070a0'))
        self.setFont('Helvetica', 9)
        self.drawCentredString(PAGE_W/2, PAGE_H*0.25, TODAY)
        # Footer text
        self.setFillColor(EOC)
        self.setFont('Helvetica', 7)
        self.drawCentredString(PAGE_W/2, 0.05*inch,
            f'FieldComms IMS v1.0  ·  For Authorized Operator Use  ·  MCESV/MCEMA')

    def _draw_chrome(self):
        n = self._pageNumber
        LOGO = Path('/home/claude/esv-logo.png')

        if n > 1:
            # Header bar
            self.setFillColor(EOC)
            self.rect(0, PAGE_H-0.42*inch, PAGE_W, 0.42*inch, fill=1, stroke=0)
            self.setFillColor(GOLD)
            self.rect(0, PAGE_H-0.44*inch, PAGE_W, 0.02*inch, fill=1, stroke=0)
            if LOGO.exists():
                try:
                    self.drawImage(str(LOGO), M, PAGE_H-0.39*inch,
                                   width=0.85*inch, height=0.32*inch,
                                   preserveAspectRatio=True, mask='auto')
                except Exception:
                    pass
            self.setFillColor(white)
            self.setFont('Helvetica-Bold', 8)
            self.drawString(M+1.0*inch, PAGE_H-0.20*inch,
                            'Incident Management System v1.0 — Complete User Manual · K9ESV')
            self.setFont('Helvetica', 7)
            self.drawString(M+1.0*inch, PAGE_H-0.32*inch,
                            f'For Authorized Operator Use — {SHORT}')

        # Footer bar
        self.setFillColor(EOC)
        self.rect(0, 0, PAGE_W, 0.34*inch, fill=1, stroke=0)
        self.setFillColor(GOLD)
        self.rect(0, 0.34*inch, PAGE_W, 0.018*inch, fill=1, stroke=0)
        self.setFillColor(white)
        self.setFont('Helvetica', 6.5)
        if n > 1:
            self.drawString(M, 0.12*inch, f'{ORG}  ·  © 2026 KE4CON / MCESV K9ESV  ·  CC BY-SA 4.0')
            self.drawRightString(PAGE_W-M, 0.12*inch,
                f'Page {n} of {self.TOTAL}  ·  {TODAY}')
        else:
            self.drawCentredString(PAGE_W/2, 0.12*inch,
                f'FieldComms IMS v1.0  ·  {ORG}  ·  {TODAY}  ·  CC BY-SA 4.0')


# Track sections for TOC
SECTIONS = []

def register_section(num, title, url=''):
    SECTIONS.append((num, title, url))

print("Framework module loaded OK")
