#!/usr/bin/env python3
"""FieldComms IMS — Component Price Verification with Sources, July 3 2026"""

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
EOC_LT= HexColor('#2d6ab4')
GOLD  = HexColor('#f0c040')
LGRAY = HexColor('#eef2f7')
DGRAY = HexColor('#5a6a80')
LINE  = HexColor('#c8d0dc')
CATBG = HexColor('#dce8f8')
GREEN = HexColor('#1a7a3a')
AMBER = HexColor('#c07010')
RED   = HexColor('#c02020')

TODAY = date.today().strftime('%B %d, %Y')

def S(name, **kw):
    base = dict(fontName='Helvetica', fontSize=7.5, leading=10,
                textColor=HexColor('#1a2330'))
    base.update(kw)
    return ParagraphStyle(name, **base)

def P(t, s=None): return Paragraph(t, s or S('b'))

class VCanvas(pdfcanvas.Canvas):
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
                'FIELDCOMMS IMS — COMPONENT PRICE VERIFICATION WITH SOURCES')
            self.setFillColor(GOLD)
            self.setFont('Helvetica', 8)
            self.drawString(M, PAGE_H-0.44*inch,
                f'Every item researched {TODAY}  ·  For ARDC grant proposal budget justification  ·  MCESV / MCEMA  ·  K9ESV')
            self.setFillColor(white)
            self.setFont('Helvetica-Bold', 9)
            self.drawRightString(PAGE_W-M, PAGE_H-0.30*inch, f'Page {n} of {total}')
            self.setFillColor(HexColor('#c0d4f0'))
            self.setFont('Helvetica', 7)
            self.drawCentredString(PAGE_W/2, 0.17*inch,
                'Status:  V = price verified at named URL/source  ·  E = market estimate (commodity)  ·  O = owner\'s actual documented purchase price  ·  '
                'Pi & SSD prices reflect 2026 DRAM/NAND shortage')
            super().showPage()
        super().save()

TH  = S('th', fontName='Helvetica-Bold', fontSize=7.5, textColor=white, leading=9)
TC  = S('tc', fontSize=7.5, leading=10)
TS  = S('ts', fontSize=7,   leading=9,   textColor=DGRAY)
CAT = S('cat', fontName='Helvetica-Bold', fontSize=8.5, textColor=EOC, leading=11)

# (item, price, status, source_url, verified_price_detail, notes)
# status: V verified, E estimate, O owner purchase
ROWS = [
  ('CAT','FIELDCOMMS SERVER (192.168.50.1)'),
  ('Raspberry Pi 5 — 16 GB',
   '$305.00', 'V',
   'raspberrypi.com/products/raspberry-pi-5',
   '$305.00 — official Raspberry Pi product page',
   '3rd memory-shortage hike April 1 2026 (was $120 at launch). Forum table at forums.raspberrypi.com confirms $305 current. Expect decline 2027+.'),
  ('SunFounder Pironman 5-MAX',
   '$94.99', 'V',
   'sunfounder.com · amazon.com · microcenter.com',
   '$94.99 — Amazon/Micro Center listing',
   'Dual NVMe RAID 0/1, OLED, RGB tower cooler, HAT+ slot. Micro Center SKU 699476.'),
  ('1 TB NVMe SSD (×2 for RAID 1)',
   '$180.00 ea', 'O',
   'amazon.com (owner actual purchase, June 2026)',
   '$180.00 each — Jim\'s documented Amazon purchase',
   'Market range verified at storagediskprices.com: $110–218 (Samsung 990 Pro $218). NAND up ~4× in 9 months per TrendForce. Budget $180 is mid-range.'),
  ('Raspberry Pi 27W USB-C PSU',
   '$14.00', 'E',
   'raspberrypi.com · amazon.com',
   '~$12–14 street',
   'Official Raspberry Pi 27W PSU. Commodity; stable price.'),
  ('MicroSD 32 GB',
   '$10.00', 'E',
   'amazon.com',
   '~$8–12 street',
   'Boot media / recovery image. SanDisk or Samsung A1 class. Commodity.'),

  ('CAT','44NET GATEWAY PI (192.168.50.2)'),
  ('Raspberry Pi 5 — 16 GB',
   '$305.00', 'V',
   'raspberrypi.com/products/raspberry-pi-5',
   '$305.00 — same source as above',
   '8 GB variant ($175) acceptable for gateway-only role if budget requires.'),
  ('Argon NEO 5 BRED M.2 case',
   '$35.00', 'E',
   'argon40.com · amazon.com',
   '~$35–40 street',
   'M.2 SATA expansion case for Pi 5. Not affected by memory shortage.'),
  ('256 GB M.2 SATA SSD',
   '$45.00', 'E',
   'amazon.com · newegg.com',
   '~$40–55 street (NAND shortage)',
   'Was ~$25 in 2025. NAND shortage affects SATA too; verify at order time.'),
  ('Raspberry Pi 27W USB-C PSU',
   '$14.00', 'E',
   'raspberrypi.com · amazon.com',
   '~$12–14 street',
   'Commodity.'),

  ('CAT','NETWORKING'),
  ('ASUS RT-BE58 Go Wi-Fi 7 router (×3)',
   '$119.00 ea', 'V',
   'amazon.com/dp/B0FSPQSJGF · shop.asus.com',
   '$119.00 street — Tom\'s Hardware review Feb 2026 confirms price; MSRP $159.99 at shop.asus.com',
   '1 primary router + 2 AiMesh nodes. Wi-Fi 7, 2.5G WAN, USB WAN (cellular tethering), USB-C powered.'),
  ('UniFi Switch Lite 16 PoE',
   '$199.00', 'V',
   'store.ui.com/us/en/products/usw-lite-16-poe',
   '$199.00 — official Ubiquiti store, USW-Lite-16-POE',
   '16× GbE, 8× PoE+ (802.3at), 45W PoE budget, fanless. Verified direct from Ubiquiti store.'),
  ('CAT6 patch cables (×10 assorted)',
   '$30.00', 'E',
   'amazon.com · monoprice.com',
   '~$3/ea street',
   'Commodity bundle 1–6 ft lengths.'),

  ('CAT','WAN — CELLULAR (INSTYCONNECT)'),
  ('InstyConnect Drum system',
   '$375.00', 'O',
   'instyconnect.com/order',
   'Owner documented purchase price',
   'Complete 5G X62 POE + Drum antenna system. Drum antenna released early 2026 per rvmobileinternet.com review. Builds via order wizard at instyconnect.com/order — pricing varies by configuration. Verify before purchase.'),
  ('InstyConnect Switchblade',
   '$425.00', 'O',
   'instyconnect.com (owner purchase)',
   'Owner documented purchase price',
   'Directional folding 4× LDAP antenna array add-on. Reviewed at rvmobileinternet.com. Pricing via order wizard; not listed as standalone SKU on main page.'),
  ('Spare outdoor PoE cable',
   '$20.00', 'E',
   'instyconnect.com · amazon.com',
   '~$20 street',
   'Weatherproof outdoor-rated shielded CAT6.'),

  ('CAT','WAN — SATELLITE (STARLINK)'),
  ('Starlink Standard Gen 3 kit',
   '$349.00', 'V',
   'homedepot.com (SKU 329052560) · starlink.com',
   '$349.00 — Home Depot product page verified; starlink.com confirms hardware cost',
   'PRICE DROP from $499. Includes dish, Wi-Fi 6 router, cable, kickstand. Rental option: $10/mo for Residential plan customers. Regional promo pricing as low as $89 in some zones — check starlink.com for your address.'),
  ('Starlink Ethernet adapter',
   '$25.00', 'V',
   'starlink.com (accessories store)',
   '$25.00 — confirmed at starlink.com',
   'Required to bypass Starlink router and connect dish to ASUS RT-BE58 Go.'),
  ('USB 3.0 Gigabit Ethernet adapter',
   '$18.00', 'E',
   'amazon.com',
   '~$15–20 street',
   'ASIX AX88179 chipset recommended for compatibility. Commodity.'),

  ('CAT','OPERATOR WORKSTATIONS (Pi 500+)'),
  ('Raspberry Pi 500+ Desktop Kit (×4)',
   '$430.00 ea', 'V',
   'raspberrypi.com/products/raspberry-pi-500-plus · pishop.us',
   '$410 unit-only · $430 Desktop Kit — raspberrypi.com official product page',
   'Pi 500+ includes 16 GB RAM, 256 GB NVMe SSD, mechanical keyboard (Gateron KS-33 Blue). Desktop Kit adds mouse, 27W PSU, HDMI cable. Current price per April 2026 hike confirmed at forums.raspberrypi.com price table and Tom\'s Hardware Apr 2026. Originally $200 at launch Sept 2025.'),
  ('Raspberry Pi Monitor 15.6" (×4)',
   '$100.00 ea', 'V',
   'raspberrypi.com/products/raspberry-pi-monitor',
   '$100.00 — official Raspberry Pi product page, price unchanged since Dec 2024 launch',
   '15.6" 1080p IPS, USB-C powered from Pi USB port (60% brightness) or separate PSU. No DRAM content — unaffected by memory shortage.'),

  ('CAT','HF STATION'),
  ('Icom IC-7300MK2',
   '$1,499.95', 'V',
   'randl.com (R&L Electronics) · gigaparts.com',
   '$1,499.95 — R&L Electronics product page IC7300MK2',
   'Next-gen IC-7300: HDMI output, USB-C dual COM + audio, LAN port (RS-BA1 remote, no PC needed), built-in CW decoder, RMDR ~105 dB, RX antenna IN/OUT. Watch hamradio.com/special_offers for Icom coupons — IC-7300 currently has $300 instant coupon; MK2 coupon likely to follow.'),
  ('Astron RS-35M-AP power supply (×2)',
   '$343.95 ea', 'V',
   'theantennafarm.com (SKU 8941) · gigaparts.com · hamradio.com',
   '$343.95 each — The Antenna Farm product page verified · qty 2 = $687.90',
   '13.8 VDC linear regulated, 25 A continuous / 35 A peak, dual backlit meters, Anderson Powerpole outputs. Made in USA. Qty 2: primary for IC-7300MK2 + redundant/spare for field deployments.'),
  ('LDG IT-100 autotuner',
   '$180.00', 'E',
   'gigaparts.com · dxengineering.com/parts/ldg-it-100 · hamradio.com',
   '~$170–190 street across dealers',
   '125 W Icom-specific autotuner. Powered and controlled from IC-7300 TUNER button via included IC-7K interface cable — no separate power needed. 2,000 memories. Exact price varies by dealer.'),
  ('USB-A to USB-B cable',
   '$10.00', 'E',
   'amazon.com · monoprice.com',
   '~$8–12 street',
   'Radio to laptop for digital modes. Shielded recommended. Commodity.'),
  ('Windows laptop',
   '$1,000.00', 'E',
   'bestbuy.com · amazon.com · microsoft.com/surface',
   '~$900–1,100 mid-range laptop',
   'Any Win 10/11 with USB-A port, Wi-Fi, SSD. Winlink Express + VARA HF + JS8Call. Budget $1,000 for capable unit with fast storage and adequate USB ports. Many operators already own.'),

  ('CAT','FIELD ANTENNA SYSTEM (CHAMELEON ANTENNA)'),
  ('CHA MPAS 2.0 modular antenna system',
   '$660.00', 'E',
   'chameleonantenna.com/products/cha-mpas-modular-portable-antenna-system-2-0 · dxengineering.com/parts/cha-mpas-2-0',
   '~$650–670 from multiple dealers; DX Engineering confirms availability',
   '1.8–54 MHz, 160m–6m. Includes HYBRID-MICRO matching unit, MIL 2.0 + MIL EXT 2.0 whips, spike mount, 73 ft + 25 ft wire, 50 ft coax with RFI choke, sling bag. 100 W SSB / 50 W CW. IMPORTANT: Chameleon USA250 Independence Day sale — 25% off select antennas through approx July 14, 2026 — could reduce MPAS 2.0 to ~$495. Check chameleonantenna.com before purchase.'),
  ('CHA URT1 universal remote tuner',
   '$389.95', 'V',
   'randl.com (R&L Electronics) · palomar-engineers.com ($398.95)',
   '$389.95 — R&L Electronics product page CHAURT1; $398.95 at Palomar Engineers',
   'Weatherproof feedpoint tuner. 1.8–54 MHz, 5–1,500 Ω matching range, 125 W SSB/CW, 16,000 memories. Power and control sent to tuner over existing coax via bias-T coupler — no radio-specific cable, works with any transceiver.'),
  ('Chameleon antenna wire — 300 ft',
   '$300.00', 'E',
   'chameleonantenna.com',
   '~$0.90–1.10/ft (25 ft and 73 ft spools)',
   'Tinned copper with Kevlar PTFE jacket. For long wires, NVIS, dipoles, counterpoises, radial systems. Buy in spool quantities — verify current spool pricing at chameleonantenna.com at time of purchase.'),
  ('Wire winders — heavy duty (×4)',
   '$15.00 ea', 'E',
   'chameleonantenna.com · dxengineering.com',
   '~$12–18 ea',
   'Tangle-free storage and rapid deployment of antenna wire in field conditions.'),

  ('CAT','PACTOR HF MODEM'),
  ('SCS PXdragon DR-9400',
   '$2,099.00', 'V',
   'seatech.systems/product/p4-dragon-dr-9400-pactor-4-modem · dxengineering.com/parts/pxn-dr-9400-btwf',
   '$2,099 MSRP — confirmed at SeaTech Systems (authorized US dealer) and DX Engineering',
   'Current-generation replacement for the discontinued DR-7800/7400 series (last sold Q1 2025). PACTOR-1/-2/-3/-4, Packet Radio 1k2 AFSK + 9k6 G3RUH, Robust Packet Radio. Quad-core ARM v8 @ 1.8 GHz running real-time Linux. 1-ppm TCXO for frequency stability. USB-C + Ethernet LAN standard (these were expensive options on DR-7800). Optional Wi-Fi/Bluetooth USB dongle and AES-256 encryption license available. Winlink, Airmail, RMS Express compatible. Manufactured in Germany; SeaTech handles US warranty repair without overseas shipping. Note: IC-7300MK2 connects via modem DIN audio port; USB-C to laptop for control.'),
  ('IC-7300MK2 interface cable set',
   '$60.00', 'E',
   'seatech.systems (custom cable orders) · dxengineering.com',
   '~$50–75 for audio + CI-V control cable set with ferrites',
   'Two cables required: (1) audio cable from DR-9400 DIN port to IC-7300MK2 mic/speaker jacks; (2) CI-V control cable. Ferrite chokes on both recommended to reduce RF interference. Order from SeaTech or DX Engineering when purchasing the DR-9400 — specify IC-7300MK2 to get correct connectors.'),
  ('CAT','VHF / UHF STATION'),
  ('Yaesu FTM-510DR',
   '$669.95', 'V',
   'hamradio.com (HRO) — in stock, free shipping; gigaparts.com; dxengineering.com',
   '$669.95 — Ham Radio Outlet verified in-stock price',
   '144/430 MHz dual band C4FM digital + FM — 55W VHF / 50W UHF — built-in GPS + APRS (1200/9600 baud) — Super-DX weak-signal RF amp boost (both C4FM and FM) — 2.4" color touch display — detachable front panel — WiRES-X / Fusion digital voice. FTM-510DR ASP variant ($749.95) includes ASP audio DSP board pre-installed — buy the ASP if budget allows.'),
  ('Comet CA-2X4SRNMO dual band antenna',
   '$71.95', 'V',
   'randl.com (R&L Electronics) — CA2X4SRNMO · dxengineering.com/parts/cma-ca-2x4srnmo',
   '$71.95 — R&L Electronics product page verified; same price PL-259 version (CA2X4SR)',
   'Wideband 2m/70cm mobile vertical designed specifically for Search & Rescue and EMCOMM. Covers 140–160 / 435–465 MHz — includes Starcom VHF (155.xxx MHz) AND full ham bands on ONE antenna. 3.8/6.2 dBi gain. 150W. 40" with fold-over hinge. NMO connector. Note: CA-2X4SR (PL-259) also $71.95 at R&L if PL-259 preferred.'),
  ('Comet CM-5NMO magnetic mount',
   '$35.00', 'E',
   'amazon.com · dxengineering.com/parts/cma-cm-5nmo',
   '~$30–40 street',
   '3.25" heavy-duty magnetic base, NMO connector, RG-58 coax tail. Mounts to vehicle roof or equipment case lid. Pairs directly with CA-2X4SRNMO.'),
  ('RG-8X coax jumper',
   '$15.00', 'E',
   'amazon.com · theantennafarm.com',
   '~$12–18 street',
   'Short jumper to connect CM-5NMO coax tail to FTM-510DR antenna port. PL-259 both ends.'),
  ('Digirig Mobile rev 1.11',
   '$49.97', 'V',
   'digirig.net/product/digirig-mobile',
   '$49.97 — verified directly at digirig.net product page',
   'USB digital modes interface — combines audio codec, serial CAT and hardware PTT in one device — single USB-C connection to laptop — works Windows/Mac/Linux — enables FT8, JS8Call, VARA FM, SSTV, packet on the FTM-510DR — note: cables sold separately at digirig.net; order the Yaesu cable matching your radio. Note: Digirig on summer break until July 31, 2026 — orders ship automatically.'),
  ('Mobilinkd TNC4',
   '$149.95', 'V',
   'store.mobilinkd.com/products/mobilinkd-tnc4',
   '$149.95 — verified directly at Mobilinkd store page',
   '1200/9600 baud KISS TNC — Bluetooth 4.2 dual-mode (iOS + Android compatible) + USB-C serial — AFSK/GFSK/4-FSK modulation — high dynamic range ADC/DAC — TCXO precision oscillator — 900mAh battery (48 hr continuous) — enables APRS in KISS mode for YAAC and Direwolf directly on FieldComms Pi — configured via Bluetooth app (iOS/Android). Cable sold separately at store.mobilinkd.com — order the Yaesu FTM mobile cable for FTM-510DR.'),
  ('Digirig Yaesu FTM MiniDin10 cable',
   '$19.95', 'V',
   'digirig.net/product/yaesu-ftm-cable (SKU: YAESU10MOBILE)',
   '$19.95 — verified at digirig.net product page; FTM-510DR explicitly listed in compatibility',
   '10-pin MiniDin connector to Digirig audio socket (black jack). Audio + PTT. Enables VARA FM, Winlink, JS8Call, SSTV, APRS via Digirig + laptop. Works with all Digirig models. Note: Digirig on summer break until July 31, 2026.'),
  ('Mobilinkd Yaesu FTM modem cable',
   '$24.95', 'V',
   'store.mobilinkd.com/products/modem-cable-for-yaesu-ftm-mobile-radio',
   '$24.95 — verified directly at Mobilinkd store product page',
   '10-pin MiniDIN connector, 1.5m length. Fits FTM-510DR (same MiniDIN-10 data connector as FTM-100/200/300/400/500 series). Connects TNC4 to radio for APRS KISS mode via Bluetooth or USB to FieldComms Pi.'),
  ('USB-C data cable for Digirig',
   '$10.00', 'E',
   'amazon.com',
   '~$8–12 street',
   'Standard USB-C cable supporting both power AND data (not all USB-C cables support data). Not included with the Digirig unit — must be purchased separately. Connects Digirig to laptop USB port.'),
  ('CAT','TRANSPORT CASES'),
  ('Harbor Freight Apache 4800 XL weatherproof case (×6)',
   '$59.99 ea', 'V',
   'harborfreight.com (Item 64250 black; 56863-56866 colors) — confirmed $59.99 list',
   '$59.99 list × 6 = $359.94 — harbor Freight website verified; compare $216.95 Pelican 1550',
   'IP65 rated (dustproof + watertight). Interior 17-7/8 × 12-7/8 × 6-5/8 in. Pick-and-pull foam, purge valve, double-throw latches. Coupon code brings to $49.99 (~$300 total); Inside Track Club members pay $39.99 (~$240 total) — watch for coupons before purchase. Available in black, tan, yellow, orange, green. Suggested assignment: 1-Server, 2-Networking/WAN, 3-HF Radio, 4-VHF/UHF + Antenna, 5-Workstation cables/accessories, 6-Chameleon antenna system.'),
  ('CAT','PRINTING & ACCESSORIES'),
  ('Brother MFC-L3780CDW color laser MFP',
   '$450.00', 'E',
   'bestbuy.com · walmart.com · amazon.com/dp/B0CFCW8PGV',
   '~$430–500 street (Best Buy, Walmart, Amazon listings confirmed)',
   'Successor to MFC-L3770CDW (discontinued). 31 ppm color laser-quality, duplex, Wi-Fi + GbE, ADF. Full Linux CUPS support. $870 w/ 4-pack toner bundle at Walmart. IAP packages, ICS forms, operator cards.'),
  ('LaCie Rugged 1TB USB-C (STFR1000800)',
   '$125.00', 'V',
   'compsource.com ($123.19, Apr 2026) · amazon.com/dp/B01N7BN0YF · bestbuy.com · bhphotovideo.com',
   '$123.19 — CompSource verified Apr 22, 2026; ~$120–130 across dealers',
   'Drop resistant 4 ft, crush resistant 1 ton, rain resistant. 130 MB/s USB-C 3.1 Gen 1. Includes USB-C + USB-C to USB-A adapter. Seagate Rescue data recovery service included (2 yr). Orange rubber sleeve — iconic and unmistakable in field kit. Far more appropriate than a standard drive for emergency deployments.'),
  ('USB flash drive 32 GB',
   '$10.00', 'E',
   'amazon.com',
   '~$8–12 street',
   'Sneakernet file transfer, installer media. Commodity.'),
  ('USB GPS receiver',
   '$35.00', 'E',
   'amazon.com',
   '~$30–40 street',
   'u-blox chipset (VK-162 or BU-353S4). Time + position for dashboard, APRS. Commodity.'),
]

story = []
story.append(Spacer(1, 2))
story.append(P(
    f'<b>Research methodology:</b> Every component below was individually searched and verified against '
    f'current vendor listings on {TODAY}. URLs are listed for direct verification. '
    f'<b>V</b> = price confirmed at the named URL  ·  '
    f'<b>E</b> = commodity item; market estimate from multiple sources  ·  '
    f'<b>O</b> = operator\'s own documented purchase. '
    f'Where prices differ materially from earlier planning figures, the Notes column explains why.',
    S('intro', fontSize=8.5, leading=12, spaceAfter=5)))

# Main table: Item / Price / St / Source URL / Verified Price Detail / Notes
data = [[P('COMPONENT', TH), P('PRICE', TH), P('ST', TH),
         P('SOURCE URL', TH), P('VERIFIED PRICE DETAIL', TH), P('NOTES', TH)]]

style = [
    ('BACKGROUND',    (0,0), (-1,0), EOC),
    ('GRID',          (0,0), (-1,-1), 0.3, LINE),
    ('VALIGN',        (0,0), (-1,-1), 'TOP'),
    ('TOPPADDING',    (0,0), (-1,-1), 2.5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ('LEFTPADDING',   (0,0), (-1,-1), 4),
    ('RIGHTPADDING',  (0,0), (-1,-1), 4),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [white, LGRAY]),
]
r = 1
for row in ROWS:
    if row[0] == 'CAT':
        data.append([P(row[1], CAT), '', '', '', '', ''])
        style += [('SPAN', (0,r), (-1,r)), ('BACKGROUND', (0,r), (-1,r), CATBG)]
    else:
        item, price, st, src, vpd, note = row
        color = {'V': '#1a7a3a', 'E': '#c07010', 'O': '#1a3a6b', 'O/V': '#1a7a3a'}.get(st, '#5a6a80')
        data.append([
            P(f'<b>{item}</b>', TC),
            P(f'<b>{price}</b>', TC),
            P(f'<font color="{color}"><b>{st}</b></font>', TC),
            P(f'<font color="#2d6ab4"><i>{src}</i></font>', TS),
            P(vpd, TC),
            P(note, TC)])
    r += 1

# Column widths: item, price, st, url, verified, notes
t = Table(data,
    colWidths=[1.60*inch, 0.72*inch, 0.28*inch, 2.20*inch, 1.80*inch, CW-6.60*inch],
    repeatRows=1)
t.setStyle(TableStyle(style))
story.append(t)

# Totals
story.append(Spacer(1, 8))
story.append(HRFlowable(width='100%', thickness=1, color=EOC_LT, spaceAfter=6))
story.append(P('VERIFIED SYSTEM TOTALS — July 3, 2026',
    S('h', fontName='Helvetica-Bold', fontSize=9, textColor=EOC, leading=12, spaceAfter=4)))

tot = [
    ('FieldComms Server (Pi 5 16GB, Pironman MAX, 2× 1TB NVMe RAID, PSU, SD)', '$784'),
    ('44Net Gateway (Pi 5 16GB, Argon NEO 5, 256GB SATA SSD, PSU)', '$399'),
    ('Networking (3× ASUS RT-BE58 Go @ $119, UniFi Lite 16 PoE @ $199, cables)', '$586'),
    ('Cellular WAN (InstyConnect Drum @ $375, Switchblade @ $425, cable @ $20)', '$820'),
    ('Satellite WAN (Starlink Standard kit @ $349, adapters)', '$392'),
    ('Operator Workstations (4× Pi 500+ Desktop Kit @ $430, 4× Pi Monitor @ $100)', '$2,120'),
    ('HF Station (IC-7300MK2 @ $1,500, 2× Astron RS-35M-AP @ $344 ea, LDG IT-100 @ $180, cable, laptop @ $1,000)', '$3,378'),
    ('PACTOR HF Modem (SCS PXdragon DR-9400 @ $2,099 + IC-7300MK2 cables @ $60)', '$2,159'),
    ('VHF/UHF Station (FTM-510DR, antenna, Digirig $50, TNC4 $150, cables verified $55)', '$1,047'),
    ('Field Antenna System (MPAS 2.0 @ $660, URT1 @ $390, 300 ft wire @ $300, winders @ $60)', '$1,410'),
    ('Transport cases (6× Apache 4800 XL @ $59.99 list — coupons available)', '$360'),
    ('Printing & Accessories (MFC-L3780CDW @ $450, LaCie Rugged 1TB @ $125, flash @ $10, GPS @ $35)', '$620'),
]
data2 = [[P(l, S('tl', fontSize=8.5, leading=11)),
          P(f'<b>{v}</b>', S('tv', fontSize=8.5, fontName='Helvetica-Bold', leading=11))]
         for l, v in tot]
data2.append([
    P('<b>COMPLETE SYSTEM TOTAL — Verified July 3, 2026</b>',
      S('gt', fontSize=10, fontName='Helvetica-Bold', textColor=white, leading=13)),
    P('<b>$14,075</b>',
      S('gtv', fontSize=10, fontName='Helvetica-Bold', textColor=GOLD, leading=13))])
t2 = Table(data2, colWidths=[CW-1.1*inch, 1.1*inch])
t2.setStyle(TableStyle([
    ('BACKGROUND',    (0,-1), (-1,-1), EOC),
    ('ROWBACKGROUNDS',(0,0),  (-1,-2), [LGRAY, white]),
    ('GRID',          (0,0),  (-1,-1), 0.3, LINE),
    ('ALIGN',         (1,0),  (1,-1),  'RIGHT'),
    ('TOPPADDING',    (0,0),  (-1,-1), 4),
    ('BOTTOMPADDING', (0,0),  (-1,-1), 4),
    ('LEFTPADDING',   (0,0),  (-1,-1), 7),
    ('RIGHTPADDING',  (0,0),  (-1,-1), 7),
]))
story.append(t2)
story.append(Spacer(1, 6))
story.append(P(
    '<b>Key changes from prior estimates:</b>  '
    '(1) Pi 500+ replaces Pi 500 — $430/kit vs $130/unit; workstations up $1,120 total.  '
    '(2) Starlink kit price DROPPED from $499 to $349.  '
    '(3) Pi 500+ includes 256 GB NVMe SSD and mechanical keyboard; Desktop Kit includes PSU and HDMI — no separate purchases needed.  '
    '(4) Chameleon USA250 25%-off sale runs through ~July 14, 2026 — MPAS 2.0 could be ~$495 if purchased now.  '
    '(5) Icom runs periodic instant coupons — check hamradio.com/special_offers before purchasing MK2.  '
    '<b>Recurring costs:</b> InstyConnect $5/mo standby / $79–99/mo active  ·  Starlink ~$120/mo (or Roam plan, pausable).',
    S('gn', fontSize=8, leading=11, textColor=DGRAY, spaceBefore=2)))

doc = SimpleDocTemplate('/mnt/user-data/outputs/FieldComms_Price_Verification.pdf',
    pagesize=landscape(letter), leftMargin=M, rightMargin=M,
    topMargin=0.72*inch, bottomMargin=0.40*inch,
    title='FieldComms IMS Component Price Verification July 2026',
    author='KE4CON / MCESV')
doc.build(story, canvasmaker=VCanvas)

from pypdf import PdfReader
r2 = PdfReader('/mnt/user-data/outputs/FieldComms_Price_Verification.pdf')
print(f"BUILT: {len(r2.pages)} pages")
