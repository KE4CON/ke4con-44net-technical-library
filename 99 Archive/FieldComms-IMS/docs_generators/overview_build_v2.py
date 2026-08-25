#!/usr/bin/env python3
"""FieldComms IMS v1.0 — Document Generator
Rebuilt from session transcript.
"""
import datetime
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable)
from reportlab.pdfgen import canvas

EOC=HexColor('#1a3a6b');GOLD=HexColor('#f0c040');LINE=HexColor('#c9d3df')
LGRAY=HexColor('#f0f3f6');EOC_LT=HexColor('#2d6ab4');AMBER=HexColor('#b8740a')
GREEN=HexColor('#1a7a3a');PURPLE=HexColor('#5b2d8e');RED=HexColor('#8b1a1a')
SGREEN=HexColor('#1a6b2a')

LOGO='/home/claude/esv-logo.png'
PAGE_W,PAGE_H=letter; M=0.55*inch; CW=PAGE_W-2*M

def S(name,**kw):
    d=dict(fontName='Helvetica',fontSize=9,textColor=black,leading=12,spaceAfter=0)
    d.update(kw); return ParagraphStyle(name,**d)
def P(t,s=None): return Paragraph(t,s or S('b'))
def SP(n=3): return Spacer(1,n)

class NC(canvas.Canvas):
    def __init__(self,*a,**kw): super().__init__(*a,**kw); self._saved=[]
    def showPage(self): self._saved.append(dict(self.__dict__)); self._startPage()
    def save(self):
        total=len(self._saved)
        for st in self._saved:
            self.__dict__.update(st); self._chrome(total); super().showPage()
        super().save()
    def _chrome(self,total):
        self.setFillColor(EOC); self.rect(0,PAGE_H-0.50*inch,PAGE_W,0.50*inch,fill=1,stroke=0)
        self.setFillColor(GOLD); self.rect(0,PAGE_H-0.52*inch,PAGE_W,0.02*inch,fill=1,stroke=0)
        if Path(LOGO).exists():
            try: self.drawImage(LOGO,M,PAGE_H-0.47*inch,width=1.0*inch,height=0.40*inch,preserveAspectRatio=True,mask='auto')
            except: pass
        self.setFillColor(white); self.setFont('Helvetica-Bold',10.5)
        self.drawString(M+1.15*inch,PAGE_H-0.21*inch,'Incident Management System v1.0')
        self.setFont('Helvetica',7.5)
        self.drawString(M+1.15*inch,PAGE_H-0.36*inch,'McHenry County Emergency Services Volunteers · K9ESV · RACES/ARES/Starcom')
        self.setFillColor(EOC); self.rect(0,0,PAGE_W,0.26*inch,fill=1,stroke=0)
        self.setFillColor(GOLD); self.rect(0,0.26*inch,PAGE_W,0.013*inch,fill=1,stroke=0)
        self.setFillColor(white); self.setFont('Helvetica',6.5)
        self.drawString(M,0.085*inch,'For Authorized Personnel Only · EMCOMM-NET · http://192.168.50.1')
        self.drawRightString(PAGE_W-M,0.085*inch,f'Page {self._pageNumber} of {total} · {datetime.date.today().strftime("%B %Y")}')

def feat_section(title,color,cols):
    hdr=Table([[P(title,S('h',fontName='Helvetica-Bold',fontSize=7.5,textColor=white,leading=9.5))]],colWidths=[CW])
    hdr.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),color),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),2.5),('BOTTOMPADDING',(0,0),(-1,-1),2.5)]))
    rows=[[P(f'· {l}',S('fi',fontSize=7.3,leading=9.8)),P(f'· {r}',S('fi',fontSize=7.3,leading=9.8))] for l,r in cols]
    tbl=Table(rows,colWidths=[CW/2,CW/2])
    tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LGRAY),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),0.25,LINE)]))
    return [hdr,tbl,SP(4)]

story=[]; story.append(SP(2))
tag=Table([[P('Offline Emergency Communications Server for Raspberry Pi 5',S('tag',fontName='Helvetica-Bold',fontSize=11,textColor=EOC,leading=14,alignment=TA_CENTER))]],colWidths=[CW])
tag.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),HexColor('#ddeeff')),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('BOX',(0,0),(-1,-1),1,EOC_LT)]))
story.append(tag); story.append(SP(5))

story.append(P('The <b>Incident Management System</b> is a self-contained emergency communications server running on a Raspberry Pi 5 (16 GB) in a Pironman MAX 5 enclosure with dual 1 TB NVMe SSDs in RAID 1. It broadcasts its own Wi-Fi network (<b>EMCOMM-NET</b>) via an ASUS RT-BE58 Go router and serves a full suite of amateur radio, ICS, and SAR tools to any browser on scene — no internet, no app installation, no configuration required. Everything is accessible at <b>http://192.168.50.1</b>.',S('intro',fontSize=8.5,leading=12,alignment=TA_JUSTIFY)))
story.append(SP(5))

# Stats strip — updated to show 3 modes
stats=Table([[
    P('29  <font size="7">Web pages</font>',S('st',fontName='Helvetica-Bold',fontSize=17,textColor=EOC,alignment=TA_CENTER,leading=20)),
    P('3  <font size="7">Dashboard modes</font>',S('st',fontName='Helvetica-Bold',fontSize=17,textColor=SGREEN,alignment=TA_CENTER,leading=20)),
    P('10  <font size="7">Background services</font>',S('st',fontName='Helvetica-Bold',fontSize=17,textColor=AMBER,alignment=TA_CENTER,leading=20)),
    P('RAID 1  <font size="7">2× 1TB NVMe</font>',S('st',fontName='Helvetica-Bold',fontSize=14,textColor=PURPLE,alignment=TA_CENTER,leading=18)),
]],colWidths=[CW/4]*4)
stats.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,LINE),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('BACKGROUND',(0,0),(0,-1),HexColor('#ddeeff')),('BACKGROUND',(1,0),(1,-1),HexColor('#e7f3ec')),('BACKGROUND',(2,0),(2,-1),HexColor('#fbf2e0')),('BACKGROUND',(3,0),(3,-1),HexColor('#f0e8f8')),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
story.append(stats); story.append(SP(5))

story += feat_section('📻  Amateur Radio Mode', EOC, [
    ('Net Control Logger — multi-net, FCC auto-fill, ICS-309 export', 'Callsign Lookup — full FCC database (~800K licensees) offline'),
    ('Observer Mode — read-only live net view for served agencies', 'HF Propagation — band conditions, MUF/LUF, solar indices'),
    ('Repeater Database — RepeaterBook data, band/ARES/mode filters', "Dead Man's Switch — inactivity alert per armed net"),
    ('NTS Radiogram — formatted ARRL traffic with log', 'APRS Tactical Map — live Graywolf + YAAC stations on Leaflet'),
])
story += feat_section('🚔  Starcom / Public Safety Mode', SGREEN, [
    ('Starcom Net Logger — Radio ID / unit-based public safety nets', 'Weather Net — quick-launch storm spotter check-in net'),
    ('SAR Net — quick-launch Search & Rescue net with unit tracking', 'Resource Tracking Map — unit placement, status, zone drawing'),
    ('Resource Board — 5-state status cycle (Available → Demobilized)', 'Member Roster — Radio IDs, certifications, activation check-in'),
    ('Facilities Directory — EOC, shelters, hospitals with frequencies', 'ICS Platform access — full incident command from Starcom mode'),
])
story += feat_section('🏛  ICS Incident Command — including SAR Activations', AMBER, [
    ('Incident types: Natural Disaster, HazMat, <b>Search &amp; Rescue</b>, MCI', 'Command Section — objectives, safety, weather, staff (ICS-201–203)'),
    ('Operations Section — T-card board, resource assignments (ICS-204)', 'Planning Section — ICS-209, IAP tracker, resource status table'),
    ('Logistics Section — comms plan, supply tracking (ICS-205/206/211)', 'Finance/Admin — cost accounting, time tracking, procurement'),
    ('ICS-213 / ICS-214 / ICS-309 forms — fill, print, archive by incident', 'Winlink Form Import — parse ICS XML from Winlink Express'),
])
story += feat_section('🔍  SAR & Personnel Operations', RED, [
    ('SAR incident type — full ICS platform for search and rescue ops', 'Search & Rescue Net — Starcom logger net type for SAR radio ops'),
    ('SAR unit tracking — resource map with 🔍 Search & Rescue unit type', 'Activation tracking — check-ins, walk-ins, deployment log per incident'),
    ('Member certifications — ICS-100 through ICS-800, EmComm I/II, CERT', 'Operator access cards — Avery 5371 printable laminated cards'),
])
story += feat_section('📡  Winlink & Digital Comms — Windows Laptop + Pi', PURPLE, [
    ('Winlink Express (Windows) — primary Winlink with IC-7300 + VARA HF', 'Pat Winlink (Pi) — browser-based backup email-over-radio, port 8090'),
    ('JS8Call (Windows) — HF keyboard-to-keyboard weak-signal digital mode', 'JS8Call API — open from any EMCOMM-NET device via dashboard card'),
    ('Single USB cable from IC-7300 — no interface box required', 'Winlink Form Import — ICS-213/214/309 XML archived to incident'),
])
story += feat_section('📚  Reference & Administration', HexColor('#5b6675'), [
    ('Reference Library — upload, search, tag, and serve field documents', 'Radio Cheat Sheets — phonetic, Q-codes, prowords, band plan, CTCSS'),
    ('Kiwix Offline Library — WikiMed, Wikipedia, iFixit, Wikivoyage', 'Print Center — all forms, reference cards, incident cover sheet'),
    ('Pre-Flight Checklist — GO / CAUTION / NO-GO deployment readiness', 'System Health Monitor — CPU, memory, disk, services, GPS, internet'),
])

story.append(SP(2)); story.append(HRFlowable(width='100%',thickness=0.5,color=LINE,spaceBefore=0,spaceAfter=3))
acc=Table([
    [P('HOW TO ACCESS',S('ah',fontName='Helvetica-Bold',fontSize=7,textColor=EOC,leading=9)),
     P('Connect to Wi-Fi <b>EMCOMM-NET</b>, open any browser to <b>http://192.168.50.1</b> — no app, no login, no internet.',S('ad',fontSize=8,leading=11))],
    [P('HARDWARE',S('ah',fontName='Helvetica-Bold',fontSize=7,textColor=EOC,leading=9)),
     P('Raspberry Pi 5 (16 GB) · Pironman MAX 5 · 2× 1 TB NVMe RAID 1 · ASUS RT-BE58 Go Wi-Fi 7 · UniFi Switch Flex 2.5G-5 · Windows laptop (Winlink Express + JS8Call).',S('ad',fontSize=8,leading=11))],
],colWidths=[0.85*inch,CW-0.85*inch])
acc.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LGRAY),('BACKGROUND',(0,0),(0,-1),HexColor('#ddeeff')),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),0.4,LINE)]))
story.append(acc)

out='/mnt/user-data/outputs/IncidentManagement_Overview.pdf'
doc=SimpleDocTemplate(out,pagesize=letter,leftMargin=M,rightMargin=M,topMargin=0.62*inch,bottomMargin=0.37*inch,title='Incident Management System v1.0 — Overview',author='McHenry County Emergency Services Volunteers')
doc.build(story,canvasmaker=NC)
from pypdf import PdfReader
r=PdfReader(out); print(f'BUILT: {out}  Pages: {len(r.pages)}')