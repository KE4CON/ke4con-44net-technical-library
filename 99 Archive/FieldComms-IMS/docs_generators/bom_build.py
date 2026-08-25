#!/usr/bin/env python3
"""FieldComms IMS — Bill of Materials with verified June 2026 pricing"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable)
from reportlab.pdfgen import canvas as pdfcanvas
from datetime import date

PAGE_W, PAGE_H = letter
M = 0.6*inch
CW = PAGE_W - 2*M

EOC   = HexColor('#1a3a6b')
EOC_LT= HexColor('#2d6ab4')
GOLD  = HexColor('#f0c040')
LGRAY = HexColor('#eef2f7')
DGRAY = HexColor('#5a6a80')
LINE  = HexColor('#c8d0dc')
CATBG = HexColor('#dce8f8')

TODAY = date.today().strftime('%B %d, %Y')

def S(name, **kw):
    base = dict(fontName='Helvetica', fontSize=8.5, leading=11.5,
                textColor=HexColor('#1a2330'))
    base.update(kw)
    return ParagraphStyle(name, **base)

def P(t, s=None): return Paragraph(t, s or S('b'))
def SP(n=6): return Spacer(1, n)

class BomCanvas(pdfcanvas.Canvas):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._saved = []
    def showPage(self):
        self._saved.append(dict(self.__dict__)); self._startPage()
    def save(self):
        total = len(self._saved)
        for st in self._saved:
            self.__dict__.update(st)
            n = self._pageNumber
            self.setFillColor(EOC)
            self.rect(0, PAGE_H-0.50*inch, PAGE_W, 0.50*inch, fill=1, stroke=0)
            self.setFillColor(GOLD)
            self.rect(0, PAGE_H-0.53*inch, PAGE_W, 0.03*inch, fill=1, stroke=0)
            self.setFillColor(white)
            self.setFont('Helvetica-Bold', 12)
            self.drawString(M, PAGE_H-0.32*inch, 'FIELDCOMMS IMS — BILL OF MATERIALS')
            self.setFillColor(GOLD)
            self.setFont('Helvetica', 8)
            self.drawString(M, PAGE_H-0.44*inch,
                'Verified pricing — June 2026  ·  MCESV / MCEMA  ·  K9ESV')
            self.setFillColor(white)
            self.setFont('Helvetica-Bold', 9)
            self.drawRightString(PAGE_W-M, PAGE_H-0.32*inch, 'v1.0')
            self.setFillColor(DGRAY)
            self.setFont('Helvetica', 7)
            self.drawCentredString(PAGE_W/2, 0.22*inch,
                f'FieldComms IMS Bill of Materials  ·  {TODAY}  ·  Page {n} of {total}  ·  '
                'Raspberry Pi pricing reflects 2026 industry memory shortage')
            super().showPage()
        super().save()

TH = S('th', fontName='Helvetica-Bold', fontSize=8, textColor=white, leading=10)
TC = S('tc', fontSize=8, leading=10.5)
TP = S('tp', fontSize=8, leading=10.5, fontName='Helvetica-Bold')
CAT= S('cat', fontName='Helvetica-Bold', fontSize=9, textColor=EOC, leading=11)
SUB= S('sub', fontName='Helvetica-Bold', fontSize=8.5, textColor=EOC, leading=10.5)

def bom_table(sections):
    """sections = [(cat_name, [(item, detail, qty, unit, ext), ...], subtotal), ...]"""
    data = [[P('ITEM', TH), P('DETAIL', TH), P('QTY', TH), P('UNIT', TH), P('EXT', TH)]]
    style = [
        ('BACKGROUND',    (0,0), (-1,0), EOC),
        ('GRID',          (0,0), (-1,-1), 0.3, LINE),
        ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING',   (0,0), (-1,-1), 5),
        ('RIGHTPADDING',  (0,0), (-1,-1), 5),
        ('ALIGN',         (2,0), (-1,-1), 'RIGHT'),
    ]
    r = 1
    for cat, items, subtotal in sections:
        data.append([P(cat, CAT), '', '', '', ''])
        style.append(('SPAN', (0,r), (-1,r)))
        style.append(('BACKGROUND', (0,r), (-1,r), CATBG))
        r += 1
        for item, detail, qty, unit, ext in items:
            data.append([P(f'<b>{item}</b>', TC), P(detail, TC),
                         P(str(qty), TC), P(unit, TC), P(ext, TC)])
            r += 1
        data.append(['', P(f'{cat} subtotal', SUB), '', '', P(f'<b>{subtotal}</b>', SUB)])
        style.append(('BACKGROUND', (0,r), (-1,r), LGRAY))
        style.append(('LINEABOVE', (0,r), (-1,r), 0.8, EOC_LT))
        r += 1
    t = Table(data, colWidths=[1.55*inch, CW-3.35*inch, 0.42*inch, 0.66*inch, 0.72*inch],
              repeatRows=1)
    t.setStyle(TableStyle(style))
    return t

story = []
story.append(SP(2))
story.append(P('Complete System Bill of Materials',
    S('title', fontName='Helvetica-Bold', fontSize=14, textColor=EOC, leading=18, spaceAfter=2)))
story.append(P('All prices verified against vendor listings and actual purchases, June 2026. Raspberry Pi '
    'and all SSD/NAND storage reflect the current industry memory shortage (SSDs up 2-4× from '
    '2025) and are expected to decline in 2027-2028. Icom frequently runs instant coupons — '
    'check hamradio.com/special_offers before purchase.',
    S('note', fontSize=8, textColor=DGRAY, leading=11, spaceAfter=6)))

sections = [
    ('FieldComms Server  (192.168.50.1)', [
        ('Raspberry Pi 5 — 16 GB', 'Model B, 16 GB RAM — main application server', 1, '$305', '$305'),
        ('Pironman 5-MAX tower', 'SunFounder — dual NVMe RAID 0/1, OLED, tower cooler, RGB', 1, '$95', '$95'),
        ('1 TB NVMe SSD', '2× M.2 2280 PCIe — RAID 1 mirror  (NAND shortage pricing — was ~$75 in 2025)', 2, '$180', '$360'),
        ('Pi 27W USB-C PSU', 'Official Raspberry Pi 27W', 1, '$14', '$14'),
        ('MicroSD 32 GB', 'Boot media / recovery', 1, '$10', '$10'),
    ], '$784'),
    ('44Net Gateway  (192.168.50.2)', [
        ('Raspberry Pi 5 — 16 GB', 'Dedicated AMPRNet WireGuard gateway (8 GB variant ~$130 acceptable)', 1, '$305', '$305'),
        ('Argon NEO 5 case', 'With M.2 SATA expansion', 1, '$35', '$35'),
        ('256 GB M.2 SATA SSD', 'Gateway OS drive  (NAND shortage pricing)', 1, '$45', '$45'),
        ('Pi 27W USB-C PSU', 'Official Raspberry Pi 27W', 1, '$14', '$14'),
    ], '$399'),
    ('Networking', [
        ('ASUS RT-BE58 Go', 'Wi-Fi 7 travel router — 1 primary + 2 AiMesh nodes (street $119; MSRP $160)', 3, '$119', '$357'),
        ('UniFi Switch Lite 16 PoE', '16-port GbE, 8× PoE — central wired hub', 1, '$199', '$199'),
        ('CAT6 cables', 'Assorted lengths', 10, '$3', '$30'),
    ], '$586'),
    ('WAN — Cellular + Satellite', [
        ('InstyConnect Drum', 'Omnidirectional 5G/LTE antenna+modem — T-Mobile + Verizon — primary WAN', 1, '$375', '$375'),
        ('InstyConnect Switchblade', 'Directional folding antenna — backup for weak-signal sites', 1, '$425', '$425'),
        ('Spare PoE cable', 'Outdoor-rated shielded CAT6', 1, '$20', '$20'),
        ('Starlink kit', 'Standard dish — automatic failover WAN (price DROP from $499; regional promos lower)', 1, '$349', '$349'),
        ('Starlink Ethernet adapter', 'Official adapter', 1, '$25', '$25'),
        ('USB-to-Ethernet adapter', 'GbE USB 3.0 — ASUS USB WAN port', 1, '$18', '$18'),
    ], '$1,212'),
    ('Operator Workstations', [
        ('Raspberry Pi 500+', 'Keyboard PC — 16 GB RAM, 256 GB NVMe, mechanical keyboard (Gateron KS-33 Blue)', 4, '$410', '$1,640'),
        ('Raspberry Pi 500+ Desktop Kit upgrade', 'Adds mouse, 27W PSU, HDMI cable per unit (buy as kit @ $430 ea)', 4, '$20', '$80'),
        ('Raspberry Pi Monitor', '15.6" 1080p IPS, USB-C powered', 4, '$100', '$400'),
    ], '$2,120'),
    ('HF Station', [
        ('Icom IC-7300MK2', 'HF/50 MHz 100 W SDR — HDMI out, USB-C, LAN remote, CW decoder, improved RMDR — check Icom coupons at hamradio.com/special_offers', 1, '$1,500', '$1,500'),
        ('Astron RS-35M-AP power supply', '13.8 VDC linear regulated, 25 A cont / 35 A peak, dual meters, Anderson Powerpoles — qty 2: primary for IC-7300MK2 + redundant/spare for field ops', 2, '$344', '$688'),
        ('LDG IT-100', '125 W Icom autotuner — station-side, powered/controlled by transceiver', 1, '$180', '$180'),
        ('USB cable', 'Radio to laptop, shielded', 1, '$10', '$10'),
        ('Windows laptop', 'Winlink Express + VARA HF + JS8Call — budget $1,000 for capable unit with SSD and USB ports', 1, '$1,000', '$1,000'),
    ], '$3,378'),
    ('PACTOR HF Modem', [
        ('SCS PXdragon DR-9400', 'Current-generation PACTOR-4 HF modem — replaces discontinued DR-7800/7400 series — PACTOR-1/-2/-3/-4, Packet Radio 1200/9600 baud, Robust Packet Radio — quad-core ARM v8 @ 1.8 GHz real-time Linux — 1-ppm TCXO — USB-C + Ethernet LAN standard — optional Wi-Fi/Bluetooth dongle — OLED display — Winlink, Airmail, RMS Express compatible — manufactured in Germany by SCS — US dealer warranty via SeaTech Systems (no overseas shipping)', 1, '$2,099', '$2,099'),
        ('IC-7300MK2 interface cable set', 'Audio cable (mic/speaker) + CI-V control cable from modem DIN port to IC-7300MK2 — with ferrite filters — ordered from SeaTech Systems or DX Engineering at time of purchase', 1, '$60', '$60'),
    ], '$2,159'),
    ('VHF / UHF Station', [
        ('Yaesu FTM-510DR', '144/430 MHz dual band C4FM digital + FM — 55W VHF / 50W UHF — built-in GPS + APRS (1200/9600 baud) — Super-DX weak-signal mode — 2.4" color touch display — detachable panel — WiRES-X / Fusion digital — in-stock HRO (FTM-510DR ASP w/ DSP board $749.95 if preferred)', 1, '$670', '$670'),
        ('Comet CA-2X4SRNMO antenna', 'Wideband 2m/70cm mobile vertical designed for SAR/EMCOMM — 140-160 / 435-465 MHz covers Starcom (155.xxx MHz) AND ham bands — 3.8/6.2 dBi — 150W — 40" fold-over — NMO connector', 1, '$72', '$72'),
        ('Comet CM-5NMO mag mount', '3.25" heavy-duty magnetic base, NMO connector, RG-58 coax tail — vehicle roof or equipment case lid mount', 1, '$35', '$35'),
        ('RG-8X coax jumper', 'Short jumper: CM-5NMO coax tail to FTM-510DR SO-239 antenna port', 1, '$15', '$15'),
        ('Digirig Mobile', 'Rev 1.11 — USB digital modes interface — combines audio codec, serial CAT and PTT — single USB-C connection — works with Windows/Mac/Linux — enables FT8, JS8Call, SSTV, VARA FM, packet on VHF/UHF via the FTM-510DR', 1, '$50', '$50'),
        ('Mobilinkd TNC4', '1200/9600 baud KISS TNC — Bluetooth 4.2 (iOS + Android) + USB-C — AFSK/GFSK/4-FSK — DSP modem — TCXO precision timing — 900mAh battery (48 hr) — enables APRS KISS mode for YAAC/Direwolf on FieldComms', 1, '$150', '$150'),
        ('Digirig Yaesu FTM MiniDin10 cable', 'digirig.net SKU YAESU10MOBILE — 10-pin MiniDin to Digirig audio socket — explicitly listed for FTM-510DR — audio + PTT — enables VARA FM, Winlink, JS8Call, SSTV, APRS via laptop', 1, '$20', '$20'),
        ('Mobilinkd Yaesu FTM modem cable', 'store.mobilinkd.com — 10-pin MiniDIN, 1.5m — fits FTM-510DR (same connector as FTM-100/200/300/400/500 series) — connects TNC4 to radio for APRS KISS mode', 1, '$25', '$25'),
        ('USB-C data cable for Digirig', 'Standard USB-C cable supporting both power and data — NOT included with Digirig — required to connect Digirig to laptop', 1, '$10', '$10'),
    ], '$1,027'),
    ('Transport Cases', [
        ('Harbor Freight Apache 4800 XL', 'Weatherproof protective case — IP65 rated — interior 17-7/8 x 12-7/8 x 6-5/8 in — pick-and-pull foam insert — purge valve — latching clasps — polypropylene shell — comparable to Pelican 1550 at a fraction of the cost — available in black, tan, yellow, orange, green  — regular $59.99; coupons bring to $49.99 or $39.99 (Inside Track Club)', 6, '$60', '$360'),
    ], '$360'),
    ('Field Antenna System', [
        ('Chameleon CHA MPAS 2.0', 'Modular Portable Antenna System — 1.8-54 MHz — vertical/sloper/inverted-V/NVIS/man-pack — deploys under 2 min — hybrid match, MIL 2.0 + EXT 2.0 whips, spike mount, wire, coax, bag (USA250 25%-off sale thru mid-July 2026)', 1, '$660', '$660'),
        ('Chameleon CHA URT1', 'Universal Remote Tuner — weatherproof feedpoint tuner — 5-1,500 Ω, 125 W, 16,000 memories — power/control over coax', 1, '$390', '$390'),
        ('Chameleon antenna wire', '300 ft tinned-copper Kevlar PTFE — long wires, NVIS, dipoles, radials', 1, '$300', '$300'),
        ('Wire winders', 'Heavy-duty, 75-100 ft capacity each', 4, '$15', '$60'),
    ], '$1,410'),
    ('Printing & Accessories', [
        ('Brother MFC-L3780CDW', 'Color laser MFP — IAP packages, ICS forms, access cards (L3770 discontinued; successor model)', 1, '$450', '$450'),
        ('LaCie Rugged 1 TB USB-C', 'LaCie Rugged USB-C 1TB (STFR1000800) — drop resistant 4 ft, crush 1 ton, rain resistant — 130 MB/s — USB-C + USB-A adapter included — Seagate Rescue data recovery service included — ideal for field deployment backup', 1, '$125', '$125'),
        ('USB flash 32 GB', 'Sneakernet transfer', 1, '$10', '$10'),
        ('USB GPS receiver', 'u-blox — time + position for dashboard', 1, '$35', '$35'),
    ], '$590'),
]

story.append(bom_table(sections))
story.append(SP(8))

# Totals table
tot_rows = [
    ('Core infrastructure (server, gateway, network, WAN, workstations, printing/accessories)', '$5,691'),
    ('HF station (IC-7300MK2, 2× Astron RS-35M-AP, LDG IT-100, cable, laptop)', '$3,378'),
    ('VHF/UHF station (FTM-510DR, Comet CA-2X4SRNMO, mag mount, coax)', '$792'),
    ('Transport cases (6× Harbor Freight Apache 4800 XL @ $59.99 list)', '$360'),
    ('Field antenna system (MPAS 2.0, URT1, wire, winders)', '$1,410'),
]
data = [[P(l, S('tl', fontSize=9, leading=12)),
         P(f'<b>{v}</b>', S('tv', fontSize=9, leading=12, fontName='Helvetica-Bold'))]
        for l, v in tot_rows]
data.append([P('<b>COMPLETE SYSTEM TOTAL</b>',
               S('gt', fontSize=11, fontName='Helvetica-Bold', textColor=white, leading=14)),
             P('<b>$14,075</b>',
               S('gtv', fontSize=11, fontName='Helvetica-Bold', textColor=GOLD, leading=14))])
t = Table(data, colWidths=[CW-1.2*inch, 1.2*inch])
t.setStyle(TableStyle([
    ('BACKGROUND',    (0,-1), (-1,-1), EOC),
    ('ROWBACKGROUNDS',(0,0), (-1,-2), [LGRAY, white]),
    ('GRID',          (0,0), (-1,-1), 0.3, LINE),
    ('ALIGN',         (1,0), (1,-1), 'RIGHT'),
    ('TOPPADDING',    (0,0), (-1,-1), 5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ('LEFTPADDING',   (0,0), (-1,-1), 8),
    ('RIGHTPADDING',  (0,0), (-1,-1), 8),
]))
story.append(t)
story.append(SP(6))
story.append(P(
    '<b>Recurring costs:</b>  InstyConnect data plan — $5/month standby, $79-99/month during '
    'activations only  ·  Starlink service — ~$120/month or Roam plan (pausable)  ·  No '
    'software licenses, subscriptions, or per-seat fees.',
    S('rec', fontSize=8.5, leading=12, textColor=DGRAY)))
story.append(P(
    '<b>Pricing sources:</b>  raspberrypi.com · R&L Electronics · DX Engineering · GigaParts · '
    'Ham Radio Outlet · chameleonantenna.com · instyconnect.com · starlink.com — verified June 2026.',
    S('src', fontSize=8, leading=11, textColor=DGRAY)))

doc = SimpleDocTemplate('/mnt/user-data/outputs/FieldComms_BOM.pdf',
    pagesize=letter, leftMargin=M, rightMargin=M,
    topMargin=0.72*inch, bottomMargin=0.45*inch,
    title='FieldComms IMS Bill of Materials', author='KE4CON / MCESV')
doc.build(story, canvasmaker=BomCanvas)

from pypdf import PdfReader
r = PdfReader('/mnt/user-data/outputs/FieldComms_BOM.pdf')
print(f"BUILT: {len(r.pages)} pages")
