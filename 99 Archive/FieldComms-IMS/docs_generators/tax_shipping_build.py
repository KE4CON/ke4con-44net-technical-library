#!/usr/bin/env python3
"""FieldComms IMS — Tax & Shipping Summary, Woodstock IL 60098"""

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable)
from reportlab.pdfgen import canvas as pdfcanvas
from datetime import date

PAGE_W, PAGE_H = landscape(letter)
M   = 0.45*inch
CW  = PAGE_W - 2*M

EOC   = HexColor('#1a3a6b')
GOLD  = HexColor('#f0c040')
LGRAY = HexColor('#eef2f7')
DGRAY = HexColor('#5a6a80')
LINE  = HexColor('#c8d0dc')
CATBG = HexColor('#dce8f8')
GREEN = HexColor('#1a7a3a')

TODAY = date.today().strftime('%B %d, %Y')

def S(name, **kw):
    base = dict(fontName='Helvetica', fontSize=8, leading=10.5,
                textColor=HexColor('#1a2330'))
    base.update(kw)
    return ParagraphStyle(name, **base)
def P(t, s=None): return Paragraph(t, s or S('b'))

class TCanvas(pdfcanvas.Canvas):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw); self._saved = []
    def showPage(self):
        self._saved.append(dict(self.__dict__)); self._startPage()
    def save(self):
        total = len(self._saved)
        for st in self._saved:
            self.__dict__.update(st)
            n = self._pageNumber
            self.setFillColor(EOC)
            self.rect(0, PAGE_H-0.52*inch, PAGE_W, 0.52*inch, fill=1, stroke=0)
            self.setFillColor(GOLD)
            self.rect(0, PAGE_H-0.55*inch, PAGE_W, 0.03*inch, fill=1, stroke=0)
            self.setFillColor(white)
            self.setFont('Helvetica-Bold', 13)
            self.drawString(M, PAGE_H-0.30*inch,
                'FIELDCOMMS IMS — COMPLETE COST WITH TAX & SHIPPING')
            self.setFillColor(GOLD)
            self.setFont('Helvetica', 8)
            self.drawString(M, PAGE_H-0.44*inch,
                f'Delivery to Woodstock IL 60098  ·  Sales tax 8.25%  ·  Estimated {TODAY}  ·  MCESV / MCEMA  ·  K9ESV')
            self.setFillColor(white)
            self.setFont('Helvetica-Bold', 9)
            self.drawRightString(PAGE_W-M, PAGE_H-0.30*inch, f'Page {n} of {total}')
            self.setFillColor(HexColor('#c0d4f0'))
            self.setFont('Helvetica', 7)
            self.drawCentredString(PAGE_W/2, 0.17*inch,
                'Tax rate verified: IL 6.25% + McHenry County 0.75% + Woodstock City 1.00% + RTA 0.25% = 8.25%  ·  '
                'Shipping: UPS/USPS ground estimates; many major vendors ship free  ·  Harbor Freight cases available for in-store pickup (free)')
            super().showPage()
        super().save()

TH = S('th', fontName='Helvetica-Bold', fontSize=7.5, textColor=white, leading=9)
TC = S('tc', fontSize=7.5, leading=10)
TS = S('ts', fontSize=7.0, leading=9, textColor=DGRAY)
CAT= S('cat', fontName='Helvetica-Bold', fontSize=8.5, textColor=EOC, leading=11)

TAX_RATE = 0.0825

SECTIONS = [
  ('FIELDCOMMS SERVER (192.168.50.1)', [
    ('Raspberry Pi 5 16GB', 305.00, 1, 'raspberrypi.com / PiShop.us', 12.00),
    ('SunFounder Pironman 5-MAX', 94.99, 1, 'amazon.com', 0.00),
    ('1TB NVMe SSD ×2', 180.00, 2, 'amazon.com', 0.00),
    ('Pi 27W USB-C PSU', 14.00, 1, 'amazon.com', 0.00),
    ('MicroSD 32GB', 10.00, 1, 'amazon.com', 0.00),
  ]),
  ('44NET GATEWAY PI (192.168.50.2)', [
    ('Raspberry Pi 5 16GB', 305.00, 1, 'raspberrypi.com / PiShop.us', 12.00),
    ('Argon NEO 5 M.2 case', 35.00, 1, 'amazon.com', 0.00),
    ('256GB M.2 SATA SSD', 45.00, 1, 'amazon.com', 0.00),
    ('Pi 27W USB-C PSU', 14.00, 1, 'amazon.com', 0.00),
  ]),
  ('NETWORKING', [
    ('ASUS RT-BE58 Go ×3 @ $119 ea', 119.00, 3, 'amazon.com', 0.00),
    ('UniFi Switch Lite 16 PoE', 199.00, 1, 'store.ui.com', 10.00),
    ('CAT6 patch cables (×10)', 30.00, 1, 'amazon.com', 0.00),
  ]),
  ('WAN — CELLULAR (INSTYCONNECT)', [
    ('InstyConnect Drum system', 375.00, 1, 'instyconnect.com (order builder)', 20.00),
    ('InstyConnect Switchblade', 425.00, 1, 'instyconnect.com (order builder)', 0.00),
    ('Spare outdoor PoE cable', 20.00, 1, 'amazon.com', 0.00),
  ]),
  ('WAN — SATELLITE (STARLINK)', [
    ('Starlink Standard Gen 3 kit', 349.00, 1, 'starlink.com / Home Depot (free delivery)', 0.00),
    ('Starlink Ethernet adapter', 25.00, 1, 'starlink.com', 0.00),
    ('USB 3.0 GbE adapter', 18.00, 1, 'amazon.com', 0.00),
  ]),
  ('OPERATOR WORKSTATIONS', [
    ('Pi 500+ Desktop Kit ×4 @ $430 ea', 430.00, 4, 'raspberrypi.com / PiShop.us', 25.00),
    ('Pi Monitor 15.6" ×4 @ $100 ea', 100.00, 4, 'raspberrypi.com / PiShop.us', 0.00),
  ]),
  ('HF STATION', [
    ('Icom IC-7300MK2', 1499.95, 1, 'hamradio.com (HRO)', 30.00),
    ('Astron RS-35M-AP ×2 @ $343.95 ea', 343.95, 2, 'theantennafarm.com', 25.00),
    ('LDG IT-100 autotuner', 180.00, 1, 'gigaparts.com (free ship >$99)', 0.00),
    ('USB-A to USB-B cable', 10.00, 1, 'amazon.com', 0.00),
    ('Windows laptop', 1000.00, 1, 'bestbuy.com (free ship)', 0.00),
  ]),
  ('PACTOR HF MODEM', [
    ('SCS PXdragon DR-9400-BTWF', 2250.00, 1, 'dxengineering.com (free ship >$99)', 0.00),
    ('IC-7300MK2 interface cable set', 60.00, 1, 'dxengineering.com (same order)', 0.00),
  ]),
  ('VHF / UHF STATION', [
    ('Yaesu FTM-510DR', 669.95, 1, 'hamradio.com (HRO, same order as IC-7300MK2)', 0.00),
    ('Comet CA-2X4SRNMO antenna', 71.95, 1, 'randl.com (R&L Electronics)', 15.00),
    ('Comet CM-5NMO mag mount', 35.00, 1, 'amazon.com', 0.00),
    ('RG-8X coax jumper', 15.00, 1, 'amazon.com', 0.00),
    ('Digirig Mobile rev 1.11', 49.97, 1, 'digirig.net', 6.00),
    ('Mobilinkd TNC4', 149.95, 1, 'store.mobilinkd.com', 10.00),
    ('Digirig Yaesu FTM MiniDin10 cable', 19.95, 1, 'digirig.net (same order)', 0.00),
    ('Mobilinkd Yaesu FTM modem cable', 24.95, 1, 'store.mobilinkd.com (same order)', 0.00),
    ('USB-C data cable', 10.00, 1, 'amazon.com', 0.00),
  ]),
  ('TRANSPORT CASES', [
    ('Harbor Freight Apache 4800 XL ×6', 59.99, 6, 'harborfreight.com — $12 ship or FREE in-store pickup', 12.00),
  ]),
  ('FIELD ANTENNA SYSTEM', [
    ('Chameleon MPAS 2.0', 660.00, 1, 'chameleonantenna.com (USA250 sale may apply ~mid-July)', 25.00),
    ('Chameleon CHA URT1', 389.95, 1, 'randl.com (R&L Electronics, same order)', 0.00),
    ('Antenna wire 300 ft', 300.00, 1, 'chameleonantenna.com (same order)', 0.00),
    ('Wire winders ×4', 60.00, 1, 'chameleonantenna.com (same order)', 0.00),
  ]),
  ('PRINTING & ACCESSORIES', [
    ('Brother MFC-L3780CDW', 450.00, 1, 'bestbuy.com (free ship)', 0.00),
    ('LaCie Rugged 1TB USB-C', 125.00, 1, 'amazon.com (free Prime)', 0.00),
    ('USB flash 32GB', 10.00, 1, 'amazon.com', 0.00),
    ('USB GPS receiver', 35.00, 1, 'amazon.com', 0.00),
  ]),
]

story = []
story.append(Spacer(1, 2))
story.append(P(
    f'<b>Tax rate:</b> 8.25% for Woodstock IL 60098 — verified at TaxHero.net and Avalara (IL state 6.25% + '
    f'McHenry County 0.75% + Woodstock city 1.00% + RTA 0.25%), effective January 1, 2026.  '
    f'<b>Shipping:</b> UPS/USPS Ground estimates to 60098; most major vendors (Amazon, DX Engineering, GigaParts, '
    f'Best Buy, Starlink) ship free. HRO charges ~$30 per order. Harbor Freight cases can be picked up '
    f'in-store (Crystal Lake IL store) for $0 shipping. Digirig on summer break until July 31 — orders ship automatically.',
    S('intro', fontSize=8.5, leading=12, spaceAfter=5)))

# Main table
data = [[P('COMPONENT', TH), P('UNIT', TH), P('QTY', TH), P('SUBTOTAL', TH),
         P('TAX 8.25%', TH), P('SHIP EST', TH), P('VENDOR', TH), P('LINE TOTAL', TH)]]
style = [
    ('BACKGROUND',    (0,0), (-1,0), EOC),
    ('GRID',          (0,0), (-1,-1), 0.3, LINE),
    ('VALIGN',        (0,0), (-1,-1), 'TOP'),
    ('TOPPADDING',    (0,0), (-1,-1), 2.5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ('LEFTPADDING',   (0,0), (-1,-1), 4),
    ('RIGHTPADDING',  (0,0), (-1,-1), 4),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [white, LGRAY]),
    ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
    ('ALIGN', (0,0), (0,-1), 'LEFT'),
    ('ALIGN', (6,0), (6,-1), 'LEFT'),
]
r = 1
grand_sub = grand_tax = grand_ship = 0
for sec_name, items in SECTIONS:
    data.append([P(sec_name, CAT), '', '', '', '', '', '', ''])
    style += [('SPAN', (0,r), (-1,r)), ('BACKGROUND', (0,r), (-1,r), CATBG),
              ('ALIGN', (0,r), (-1,r), 'LEFT')]
    r += 1
    for item, unit, qty, vendor, ship in items:
        sub = round(unit * qty, 2)
        tax = round(sub * TAX_RATE, 2)
        total = sub + tax + ship
        grand_sub += sub; grand_tax += tax; grand_ship += ship
        data.append([
            P(f'<b>{item}</b>', TC),
            P(f'${unit:,.2f}', TC),
            P(str(qty), TC),
            P(f'${sub:,.2f}', TC),
            P(f'${tax:,.2f}', TC),
            P(f'${ship:,.2f}' if ship else '—', TC),
            P(f'<font color="#2d6ab4"><i>{vendor}</i></font>', TS),
            P(f'<b>${total:,.2f}</b>', TC),
        ])
        r += 1

t = Table(data,
    colWidths=[2.10*inch, 0.68*inch, 0.32*inch, 0.72*inch, 0.72*inch, 0.62*inch, 2.30*inch, 0.80*inch],
    repeatRows=1)
t.setStyle(TableStyle(style))
story.append(t)

# Grand total
story.append(Spacer(1, 8))
grand_total = grand_sub + grand_tax + grand_ship
summary = [
    ('Equipment subtotal (all sections)', f'${grand_sub:,.2f}'),
    (f'Illinois sales tax — Woodstock 60098 @ 8.25%', f'${grand_tax:,.2f}'),
    ('Estimated shipping (UPS/USPS ground to 60098)', f'${grand_ship:,.2f}'),
]
data2 = [[P(l, S('tl', fontSize=9, leading=12)),
          P(f'<b>{v}</b>', S('tv', fontSize=9, fontName='Helvetica-Bold', leading=12, alignment=2))]
         for l, v in summary]
data2.append([
    P('<b>TOTAL DELIVERED COST — Woodstock IL 60098</b>',
      S('gt', fontSize=11, fontName='Helvetica-Bold', textColor=white, leading=14)),
    P(f'<b>${grand_total:,.2f}</b>',
      S('gtv', fontSize=11, fontName='Helvetica-Bold', textColor=GOLD, leading=14, alignment=2))])
t2 = Table(data2, colWidths=[CW-1.30*inch, 1.30*inch])
t2.setStyle(TableStyle([
    ('BACKGROUND',    (0,-1), (-1,-1), EOC),
    ('ROWBACKGROUNDS',(0,0),  (-1,-2), [LGRAY, white, LGRAY]),
    ('GRID',          (0,0),  (-1,-1), 0.3, LINE),
    ('ALIGN',         (1,0),  (1,-1),  'RIGHT'),
    ('TOPPADDING',    (0,0),  (-1,-1), 5),
    ('BOTTOMPADDING', (0,0),  (-1,-1), 5),
    ('LEFTPADDING',   (0,0),  (-1,-1), 8),
    ('RIGHTPADDING',  (0,0),  (-1,-1), 8),
]))
story.append(t2)
story.append(Spacer(1, 6))
story.append(P(
    f'<b>Notes:</b>  '
    f'(1) Tax applies to all tangible goods delivered to IL 60098; rate confirmed 8.25% effective Jan 1, 2026 (TaxHero / Avalara).  '
    f'(2) Shipping estimates based on UPS/USPS Ground from each vendor\'s distribution point to 60098; actual rates '
    f'calculated at checkout.  '
    f'(3) Harbor Freight Crystal Lake store (approx. 10 mi from Woodstock) allows free in-store pickup — saving ~$72 on cases.  '
    f'(4) DX Engineering, GigaParts, Amazon, Best Buy, Starlink ship free — no minimum for most items.  '
    f'(5) Digirig summer break through July 31, 2026 — auto-ships.  '
    f'(6) DR-9400-BTWF budgeted at $2,250 — standard model $2,099; premium for BT/WiFi bundle estimated; confirm at dxengineering.com.  '
    f'(7) Chameleon USA250 25%-off sale through ~July 14, 2026 could reduce MPAS 2.0 to ~$495, saving ~$137 + tax.',
    S('gn', fontSize=7.5, leading=11, textColor=DGRAY)))

doc = SimpleDocTemplate('/mnt/user-data/outputs/FieldComms_Tax_Shipping.pdf',
    pagesize=landscape(letter), leftMargin=M, rightMargin=M,
    topMargin=0.72*inch, bottomMargin=0.40*inch,
    title='FieldComms IMS Tax and Shipping — Woodstock IL 60098',
    author='KE4CON / MCESV')
doc.build(story, canvasmaker=TCanvas)

from pypdf import PdfReader
pages = len(PdfReader('/mnt/user-data/outputs/FieldComms_Tax_Shipping.pdf').pages)
print(f"BUILT: {pages} pages")
print(f"Subtotal: ${grand_sub:,.2f} | Tax: ${grand_tax:,.2f} | Ship: ${grand_ship:,.2f} | TOTAL: ${grand_total:,.2f}")
