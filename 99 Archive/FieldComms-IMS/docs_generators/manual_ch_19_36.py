#!/usr/bin/env python3
"""manual_ch_19_36.py — Chapters 19–36 + Appendix of the FieldComms User Manual."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from manual_framework import *


def ch19():
    s = chapter(19, 'ICS Logistics Section',
                'http://192.168.50.1/ics/logistics.html')
    s.append(P(
        'Logistics provides all facilities, services, and materials that support the '
        'incident. It owns the communications plan and tracks supplies, food, medical, '
        'facilities, and check-in.'))
    s.append(SP(6))
    s.append(tbl(['TAB', 'HOW TO USE IT'], [
        ['Comms Plan (ICS-205)',
         'Build the radio communications plan. Each row is a channel: function, channel name, '
         'frequency, CTCSS tone, mode, remarks. Click <b>Add Comms Row</b> to add a channel. '
         'Pre-filled with McHenry County Starcom channels.'],
        ['Supply',
         'Log supply requests: item, category, quantity needed, quantity on hand, priority. '
         'A progress bar shows the fill rate. Use <b>Add Supply</b>.'],
        ['Facilities',
         'ICP location, base/camp details, staging area manager, and medical aid station info.'],
        ['Food / Medical (ICS-206)',
         'Meal service log (meal type, count served, menu) plus medical unit leader, '
         'ambulance status, hospital contacts.'],
        ['Check-In (ICS-211)',
         'Personnel check-in list. Records name, ICS position, agency, and arrival time. '
         'Links to the Member Roster for pre-populated entries.'],
    ], widths=[1.6*inch, CW-1.6*inch]))
    s.append(PB())
    return s


def ch20():
    s = chapter(20, 'ICS Finance / Admin Section',
                'http://192.168.50.1/ics/finance.html')
    s.append(P(
        'Finance/Admin manages all financial aspects of the incident: cost accounting, '
        'time tracking, procurement, and administrative records for reimbursement.'))
    s.append(SP(6))
    s.append(tbl(['TAB', 'HOW TO USE IT'], [
        ['Cost',
         'Log expenditures: category (personnel, equipment, supply, food, transport), '
         'amount, description, vendor, and approver. A running total is shown. Use <b>Add Cost</b>.'],
        ['Time',
         'Log person-hours per operator: name, position, agency, hours worked, hourly rate '
         '(0 = volunteer). Used for reimbursement claims. Use <b>Add Time</b>.'],
        ['Procurement',
         'Track purchase orders: item, vendor, PO number, amount, status '
         '(Requested, Ordered, Delivered, Closed). Use <b>Add Procurement</b>.'],
        ['Admin',
         'Finance/Admin Section Chief info, billing agency, cost-share type, claim deadline, '
         'and supporting documentation notes.'],
    ], widths=[1.4*inch, CW-1.4*inch]))
    s.append(SP(6))
    s.append(note(
        'All finance data can be exported to CSV for submission to the agency '
        'finance officer or FEMA reimbursement process. Click <b>Export CSV</b> '
        'on any Finance tab.', 'tip'))
    s.append(PB())
    return s


def ch21():
    s = chapter(21, 'NTS Radiogram Generator',
                'http://192.168.50.1/nts.html')
    s.append(P(
        'Generate properly formatted ARRL National Traffic System radiograms. '
        'The form produces the standard preamble, address block, and text section, '
        'and keeps a traffic log.'))
    s.append(SP(6))
    s.append(P('Creating a Radiogram', H2))
    s += steps([
        'Click <b>Auto-fill Number</b> for the next sequential message number, or enter one.',
        'Set the <b>Precedence</b>: EMERGENCY, PRIORITY, WELFARE, or ROUTINE.',
        'Choose <b>Handling Instructions</b> (HX codes) if needed — HXA through HXF.',
        'Enter <b>Station of Origin</b>, <b>Place of Origin</b>, and click <b>Auto-fill Date/Time</b>.',
        'Enter the addressee name, address, and phone.',
        'Type the message <b>Text</b> in ARRL all-caps style. The Check (word count) calculates automatically.',
        'Enter the <b>Signature</b>, then click <b>Generate Radiogram</b>.',
        'Click <b>Save to Log</b> to keep a copy, then <b>Print</b> for the paper record.',
    ])
    s.append(SP(6))
    s.append(P('Handling Instruction (HX) Codes', H2))
    s.append(tbl(['CODE', 'MEANING'], [
        ['HXA', 'Collect landline delivery authorized up to $ amount'],
        ['HXB', 'Cancel message if not delivered within X hours'],
        ['HXC', 'Report date and time of delivery to originating station'],
        ['HXD', 'Report to originating station the identity of station from which received'],
        ['HXE', 'Delivering station get reply from addressee'],
        ['HXF', 'Hold delivery until (date)'],
        ['HXG', 'Delivery by mail or landline toll call not required'],
    ], widths=[0.8*inch, CW-0.8*inch]))
    s.append(PB())
    return s


def ch22():
    s = chapter(22, 'ICS-213 General Message',
                'http://192.168.50.1/ics213.html')
    s.append(P(
        'The ICS-213 is the standard written message form for inter- and intra-agency '
        'communications on an incident. Use it when you need a written record of a '
        'request, situation update, or resource order.'))
    s.append(SP(6))
    s.append(P('Completing an ICS-213', H2))
    s += steps([
        'Fill in the header: incident name, To, From, position/agency, date/time, and subject.',
        'Click <b>Auto-fill</b> to populate the current date and time.',
        'Type the message in the body.',
        'Click <b>Generate Form</b> to render a print-formatted version.',
        'Use the <b>Print</b> button to produce a field-ready paper copy.',
        'Click <b>Save to Log</b> to keep a copy in the form log.',
    ])
    s.append(SP(4))
    s.append(note(
        'Use the ICS-213 for formal written traffic. For routine spoken radio traffic, '
        'use the Net Control log instead.', 'note'))
    s.append(PB())
    return s


def ch23():
    s = chapter(23, 'ICS-214 Activity Log & ICS-309',
                'http://192.168.50.1/ics214.html')
    s.append(P(
        'The ICS-214 is a unit-level activity log required for every ICS section and '
        'unit. It records personnel assigned and a timestamped log of activities '
        'through the operational period.'))
    s.append(SP(6))
    s.append(P('Completing an ICS-214', H2))
    s += steps([
        'Enter the incident name, operational period, unit name, and unit leader.',
        'Click <b>Add Personnel</b> to list each person assigned to the unit (name, position, agency).',
        'For each activity, click <b>Add Entry</b>, then <b>Auto Timestamp</b> for the current time, and type what happened.',
        'Entries accumulate in time order throughout the period.',
        'Click <b>Generate Form</b> and <b>Print</b> for the incident record. <b>Save Local</b> keeps a copy on the device.',
    ])
    s.append(SP(8))
    s.append(P('ICS-309 Communications Log', H2))
    s.append(P(
        'The companion ICS-309 page (Dashboard → ICS mode → ICS-309 Comms Log) records '
        'a formal communications log for the operational period. Each entry has a '
        'timestamp, from, to, and message subject. Click <b>Save to Incident</b> to '
        'file it with the active incident for after-action review.'))
    s.append(SP(4))
    s += steps([
        'Click <b>Add (timestamp now)</b> to add a row with the current UTC time.',
        'Fill in From, To, and the message Subject for each entry.',
        'Click <b>Generate Form</b> to render the printable ICS-309.',
        'Click <b>Save to Incident</b> to file it in the incident record.',
    ])
    s.append(PB())
    return s


def ch24():
    s = chapter(24, 'Winlink Form Import & Incident Archiving',
                'http://192.168.50.1/winlink-import.html')
    s.append(P(
        'Winlink Express has its own built-in ICS forms. This chapter explains how to '
        'bring that form data into the FieldComms server so the whole incident is '
        'documented and archived in one place — and how to re-print a received '
        'ICS-213, ICS-214, or ICS-309 on the Pi.'))
    s.append(SP(6))
    s.append(P('Step-by-Step Import', H2))
    s += steps([
        'In Winlink Express, open the ICS form message (sent or received).',
        'Right-click the <b>RMS_Express_Form_*.xml</b> attachment and save it to your computer.',
        'On the Winlink Form Import page, drag the saved XML file onto the drop zone, or click Browse.',
        'Click <b>Parse Form Data</b>. The page detects the form type and extracts all fields.',
        'Review the extracted fields in the editable grid. Fix any fields that need correction.',
        'Choose the Incident and Direction (Received/Sent), then click <b>💾 Archive to incident</b>.',
    ])
    s.append(SP(6))
    s.append(tbl(['FORM', 'RE-PRINT ON PI?', 'NOTES'], [
        ['ICS-213 General Message', 'Yes', 'Re-renders as the Pi\'s ICS-213 for printing'],
        ['ICS-214 Activity Log',    'Yes', 'Activity and personnel lines split into rows automatically'],
        ['ICS-309 Comms Log',       'Yes', 'Log rows parsed into the comms log'],
        ['Other Winlink forms',     'Archive only', 'Data captured and archived — no ICS re-print'],
    ], widths=[1.8*inch, 1.0*inch, CW-2.8*inch]))
    s.append(SP(6))
    s.append(P('Recommended Workflow', H2))
    s += steps([
        'Run Winlink traffic in Express as your operators normally do.',
        'At the end of each operational period, collect any RMS_Express_Form_*.xml files from operators.',
        'Import them via the Winlink Form Import page to complete the incident record.',
        'Cross-check the ICS-309 log with the Net Control log for completeness.',
    ])
    s.append(PB())
    return s


def ch25():
    s = chapter(25, 'HF Propagation', 'http://192.168.50.1/propagation.html')
    s.append(P(
        'The propagation page fetches live solar and geomagnetic data from hamqsl.com '
        '(when internet is available) and uses it to estimate current HF band conditions.'))
    s.append(SP(6))
    s.append(P('Reading the Indicators', H2))
    s.append(tbl(['INDICATOR', 'WHAT IT MEANS FOR HF'], [
        ['SFI (Solar Flux)',  'Higher = better high-band propagation. >130 excellent; 90–130 good; <90 40m/80m only.'],
        ['Sunspot Number',    'More sunspots = more solar activity = better HF. Follows the 11-year cycle.'],
        ['A-Index',           'Daily geomagnetic activity. <10 quiet (good HF); 10–30 unsettled; >30 disturbed.'],
        ['K-Index (0–9)',     '3-hour geomagnetic snapshot. ≤2 quiet; 3–4 unsettled; ≥5 storm (HF degraded); ≥7 severe.'],
        ['X-Ray Flux Class',  'Solar flare class. A/B/C minor; M moderate (SID possible); X strong HF blackout risk.'],
        ['Band Condition Bars','Green = good / Amber = fair / Red = poor for each band from 10m through 80m.'],
    ], widths=[1.6*inch, CW-1.6*inch]))
    s.append(SP(4))
    s.append(note(
        'When the Pi has no internet connection, the propagation page shows the last '
        'fetched values with a timestamp. For field activations without WAN, check '
        'propagation before departing on a device with internet, then switch to the '
        'offline Pi for the activation.', 'note'))
    s.append(PB())
    return s


def ch26():
    s = chapter(26, 'Repeater Database', 'http://192.168.50.1/repeaters.html')
    s.append(P(
        'The Repeater Database displays repeater data with rich filtering. It works '
        'in three modes: an offline file you load yourself (most reliable), the server '
        'API, or built-in sample data. Real repeater data comes from RepeaterBook.com.'))
    s.append(SP(6))
    s.append(P('The Three Sources', H2))
    s.append(tbl(['SOURCE', 'HOW TO USE IT'], [
        ['Offline File (recommended)',
         'Load a RepeaterBook CSV or JSON export. Drag-and-drop the file onto the drop zone, '
         'or click Browse. Data persists in your browser after the first load. '
         'This needs no API token and is the most dependable method.'],
        ['Server API',
         'Pulls from the FieldComms server if the net manager has run fetch_repeaters.py '
         'to download RepeaterBook data. Requires a RepeaterBook API token.'],
        ['Sample Data',
         'Three placeholder entries (SAMPLE-1/2/3) for testing the interface. '
         'Shows a "not a real repeater" warning. Do not use for operations.'],
    ], widths=[1.6*inch, CW-1.6*inch]))
    s.append(SP(6))
    s.append(P('Filtering and Sorting', H2))
    s.append(tbl(['FILTER', 'OPTIONS'], [
        ['Band',  '2m, 70cm, 23cm, 6m, 10m, 1.25m'],
        ['State', 'IL, WI, IN, IA (default), or any US state'],
        ['Affiliation', 'ARES, SKYWARN, RACES, SATERN, EmComm'],
        ['Mode', 'FM, DMR, C4FM/Fusion, D-STAR, P25, NXDN'],
        ['Sort', 'Callsign, Frequency, City, Distance (nearest first)'],
    ], widths=[1.2*inch, CW-1.2*inch]))
    s.append(SP(4))
    s.append(note(
        'A systemd timer (repeater-refresh.timer) runs the fetch automatically on '
        'the first of each month at 04:00, as long as the token is saved in the '
        'repeaterbook.env file and the Pi has internet at that time.', 'tip'))
    s.append(PB())
    return s


def ch27():
    s = chapter(27, 'Facilities Directory',
                'http://192.168.50.1/facilities.html')
    s.append(P(
        'Maintain a directory of EOC locations, hospitals, shelters, staging areas, '
        'and command posts. Each entry stores address, coordinates, radio frequencies, '
        'CTCSS tone, contact person, on-site callsign, generator status, ADA access, '
        'capacity, and operational notes.'))
    s.append(SP(6))
    s.append(P('Default Facilities', H2))
    s.append(P(
        'On first startup, FieldComms seeds four McHenry County facilities: '
        'the McHenry County EOC (Woodstock), Centegra Hospital Woodstock, '
        'the McHenry County Fairgrounds staging area, and Centegra Hospital McHenry. '
        'Edit these with your actual operational details.'))
    s.append(SP(6))
    s.append(P('Managing Facilities', H2))
    s += steps([
        'Click <b>+ Add</b> to create a facility, or click any facility card to view its full detail.',
        'In the detail view, click <b>Edit</b> to change fields, or <b>Delete</b> to remove it.',
        'Use <b>Copy Address</b> to copy the street address to clipboard for navigation apps.',
        'Click <b>Export CSV</b> to download the full directory for offline reference.',
    ])
    s.append(PB())
    return s


def ch28():
    s = chapter(28, 'Grid Square Calculator',
                'http://192.168.50.1/grid.html')
    s.append(P(
        'Convert between decimal latitude/longitude and Maidenhead grid squares in '
        'both directions, and calculate distance and bearing between two grid squares. '
        'Supports 4-character (EN52) and 6-character (EN52ab) precision.'))
    s.append(SP(6))
    s.append(P('Using the Calculator', H2))
    s += steps([
        'To convert coordinates to a grid square: enter latitude and longitude, click <b>Calculate from Lat/Lon</b>.',
        'To convert a grid square to coordinates: enter the grid square, click <b>Calculate from Grid</b>.',
        'To use your current location: click <b>Use My Location</b> (requires location permission, or uses the configured/GPS coordinates).',
        'To find distance and bearing: enter two grid squares and click <b>Calculate Distance</b>.',
    ])
    s.append(SP(4))
    s.append(P(
        'The map on the page highlights the grid square on a North America outline '
        'for quick visual reference. McHenry County, IL is in grid square <b>EN52</b>.'))
    s.append(PB())
    return s


def ch29():
    s = chapter(29, 'Radio Cheat Sheets',
                'http://192.168.50.1/cheatsheets.html')
    s.append(P(
        'A quick-reference set of radio and ICS cheat sheets, organized into tabs. '
        'No internet needed — everything is built in.'))
    s.append(SP(6))
    s.append(tbl(['TAB', 'CONTENTS'], [
        ['Phonetic Alphabet', 'NATO phonetics A–Z with pronunciation, plus ITU number pronunciation (Zero, WUN, TOO, TREE, FOW-er, FIFE, SIX, SEV-en, AIT, NIN-er)'],
        ['Q-Codes',           'Common amateur Q-codes (QRM, QRN, QRP, QSL, QTH...) and EmComm net Q-codes (QNI, QNS, QND, QNN...)'],
        ['Prowords',          'Full procedure word reference — ROGER, WILCO, SAY AGAIN, BREAK, OVER, OUT, CORRECTION, SILENCE, AUTHENTICATE, and more, with meanings and examples'],
        ['Band Plan',         '2m and 70cm segments, HF emergency frequencies (ARES, ARRL, IARU, 60m channels), and service bands (MURS, FRS, GMRS, Marine, Aviation)'],
        ['NTS Precedence',    'EMERGENCY / PRIORITY / WELFARE / ROUTINE — definitions, when to use each, and examples'],
        ['ICS Positions',     'Standard ICS command and general staff titles with abbreviations (IC, OSC, PSC, LSC, FSC, SO, IO, LO)'],
        ['CTCSS/DCS Tones',   'Standard CTCSS tone table (67.0–254.1 Hz) and DCS code table for repeater access'],
        ['Signal Reports',    'RST and RS signal report codes, S-meter calibration, and signal quality descriptions'],
    ], widths=[1.5*inch, CW-1.5*inch]))
    s.append(PB())
    return s


def ch30():
    s = chapter(30, 'Print Center', 'http://192.168.50.1/printcenter.html')
    s.append(P(
        'The Print Center is a one-stop hub for every printable document, plus a '
        'built-in incident cover-sheet generator.'))
    s.append(SP(6))
    s.append(tbl(['CATEGORY', 'DOCUMENTS'], [
        ['ICS / NTS Forms',   'ICS-213 General Message, ICS-214 Activity Log, NTS Radiogram, Pre-Flight Checklist'],
        ['Reference Cards',   'Phonetic Alphabet, Q-Codes & Prowords, ICS Structure & Forms, CTCSS/DCS & Signal Reports'],
        ['Operations',        'Net Control Log (ICS-309), Starcom Net Log (ICS-309), Member Roster, Resource Board'],
        ['Cover Sheet',       'Generate a formatted IAP cover sheet from incident details'],
    ], widths=[1.4*inch, CW-1.4*inch]))
    s.append(SP(6))
    s.append(P('Generating an Incident Cover Sheet', H2))
    s += steps([
        'Fill in incident name, number, IC, operational period, frequency, location, and situation summary.',
        'Click <b>Generate Cover</b> to preview it in the page.',
        'Click <b>Print Cover</b> to print it in a new window.',
        'Click <b>Clear</b> to reset the form.',
    ])
    s.append(SP(6))
    s.append(P('Connecting a Printer to EMCOMM-NET', H2))
    s.append(P(
        'FieldComms has print buttons on 17 pages. All printing uses the browser '
        'standard print function — it sends the job to whatever printer the '
        'operator\'s browser can reach. Three options are supported:'))
    s.append(SP(4))
    s.append(tbl(['OPTION', 'HOW IT WORKS', 'BEST FOR'], [
        ['A — Own printer',
         'Each operator prints to their own locally connected printer. No Pi setup needed.',
         'Single operator with their own printer'],
        ['B — USB printer via Pi (CUPS)',
         'USB printer plugged into the Pi. CUPS shares it across EMCOMM-NET. '
         'Installed automatically. Admin at http://192.168.50.1:631. '
         'Supports Windows, Mac, iOS AirPrint, Android, Chromebook.',
         'Field activations — one shared printer for all operators'],
        ['C — Network printer',
         'Wi-Fi or Ethernet printer connected directly to EMCOMM-NET. '
         'Devices discover it via Bonjour/mDNS automatically.',
         'Sites with an existing Wi-Fi capable printer'],
    ], widths=[1.3*inch, 2.6*inch, CW-3.9*inch]))
    s.append(SP(4))
    s.append(P('Setting Up Option B — USB Printer via CUPS', H2))
    s += steps([
        'Plug the USB printer into the Pi or powered USB hub.',
        'Open <b>http://192.168.50.1:631</b> from any device on EMCOMM-NET.',
        'Click <b>Administration → Add Printer</b> and log in with the Pi username/password.',
        'Select the printer from Local Printers. Check <b>Share This Printer</b>. Click Continue.',
        'Select the driver, click Add Printer, then print a test page.',
        'Windows: Settings → Printers → Add a printer — it appears automatically on EMCOMM-NET.',
        'iOS/iPad: tap Share → Print in any FieldComms page — AirPrint finds it automatically.',
        'Android: install CUPS Print app → add printer at 192.168.50.1 port 631.',
    ])
    s.append(note(
        'Recommended field printers: <b>Brother HL-L2350DW</b> (laser, excellent Linux support), '
        '<b>Canon PIXMA TR150</b> or <b>HP OfficeJet 200</b> (battery-powered portable options). '
        'Color multifunction laser options for full IAP package printing: '
        '<b>Brother MFC-L3770CDW</b>, <b>HP Color LaserJet Pro MFP M479fdw</b>, or '
        '<b>Canon imageCLASS MF743Cdw</b> — all support USB, Wi-Fi, and Ethernet. '
        'See the Installation Guide Step 8 for full setup instructions and the complete '
        'comparison of all three printer connection options.', 'tip'))
    s.append(SP(6))

    s.append(P('29.3  Adding the Printer on Each Device', H2))
    s.append(tbl(['DEVICE TYPE', 'HOW TO ADD SHARED PRINTER'], [
        ['Windows laptop',
         'Settings → Bluetooth & devices → Printers & scanners → Add a printer. '
         'Windows discovers the CUPS printer automatically on EMCOMM-NET via Bonjour.'],
        ['Mac / macOS',
         'System Settings → Printers & Scanners → click + (Add Printer). '
         'Click the Default tab — shared printer appears via Bonjour. Select and click Add.'],
        ['iPad / iPhone  (AirPrint)',
         'No setup required. CUPS + Avahi advertises as AirPrint-compatible. '
         'Tap Share → Print in any FieldComms page and select the printer.'],
        ['Android',
         'Install the free CUPS Print app from Google Play. '
         'Add printer at IP 192.168.50.1, Port 631, Protocol IPP.'],
        ['Raspberry Pi 500 workstation',
         'Chromium discovers CUPS printers via Bonjour automatically. '
         'No additional setup needed — printer appears in the print dialog.'],
    ], [1.5*inch, CW-1.5*inch]))
    s.append(PB())
    return s


def ch31():
    s = chapter(31, 'Reference Library', 'http://192.168.50.1/refs.html')
    s.append(P(
        'The Reference Library is a document-management system for all field reference '
        'materials — radio manuals, interoperability plans, ICS form packages, SOGs, '
        'agency plans, and training documents. Files are stored on the Pi and '
        'accessible from any device on EMCOMM-NET.'))
    s.append(SP(6))
    s.append(tbl(['TAB', 'CONTENTS'], [
        ['📻 Amateur Radio',     'Radio manuals, frequency plans, ARRL publications, band plans, antenna refs'],
        ['🏛 ICS / Emergency Mgmt','SWIC plans, NIMS docs, ICS form packages, agency SOGs, mutual aid plans'],
        ['📂 All Documents',     'Every uploaded document regardless of category'],
    ], widths=[1.6*inch, CW-1.6*inch]))
    s.append(SP(6))
    s.append(P('Uploading a Document', H2))
    s += steps([
        'Click <b>⬆ Upload Document</b>. A panel slides in from the right.',
        'Drag-and-drop a file or click Browse. Accepts PDF, Word, Excel, PowerPoint, images, KML, ZIP, GPX — up to 200 MB.',
        'Fill in Title, Category, Source, Description, Tags, Revision, and Expiry (if relevant).',
        'Under <b>Show on tab(s)</b>, check Amateur Radio, ICS/EmMgmt, or both.',
        'Click <b>⬆ Upload Document</b>. PDFs get an automatic thumbnail.',
    ])
    s.append(SP(6))
    s.append(P('Finding Documents', H2))
    s += steps([
        'Use the Category filter, tag cloud, or sort options (Newest, Title, Most Downloaded).',
        'Switch between grid and list view using the view toggle.',
        'Click any document to open its detail, then Download, Edit, or Delete.',
    ])
    s.append(PB())
    return s


def ch32():
    s = chapter(32, 'Kiwix Offline Library', 'http://192.168.50.1:8081/')
    s.append(P(
        'Kiwix serves a complete offline reference library from the Pi on port 8081. '
        'Every device on EMCOMM-NET can browse it with no internet connection at all. '
        'The content is stored as ZIM files — compressed, self-contained web archives '
        'that function like offline snapshots of entire websites. '
        'WikiMed gives your medical support personnel the same reference content '
        'a physician would look up during a mass casualty event. '
        'Wikipedia Mini provides general field reference for briefings. '
        'iFixit gives your communications team step-by-step repair guides '
        'for radio equipment, laptops, and generators — all without internet.'))
    s.append(SP(4))
    s.append(P(
        'Kiwix has its own built-in full-text search bar that searches across all '
        'installed content at once. Type any medical symptom, procedure, equipment '
        'model number, or topic and results appear instantly, fully offline. '
        'The library is accessible from the dashboard Kiwix Library card, '
        'or directly at http://192.168.50.1:8081.'))
    s.append(SP(6))
    s.append(P('Accessing Kiwix', H2))
    s.append(P(
        'Open a browser to <b>http://192.168.50.1:8081</b>, or tap the Kiwix Library '
        'card on the dashboard. Kiwix has a built-in full-text search bar that searches '
        'across all installed content at once — type any symptom, procedure, or topic '
        'and results appear instantly, offline.'))
    s.append(SP(6))
    s.append(P('Content Catalogue', H2))
    s.append(tbl(['TIER', 'CONTENT', 'SIZE', 'BEST FOR'], [
        ['1', 'WikiMed Medical Encyclopedia', '~471 MB', 'Mass-casualty events, medical support'],
        ['1', 'Wikipedia (Mini)',             '~1.2 GB', 'General field reference, briefings'],
        ['1', 'Wikivoyage',                   '~820 MB', 'Maps, local facilities, travel info'],
        ['2', 'iFixit Repair Guides',         '~2.3 GB', 'Equipment repair in the field'],
        ['2', 'Wikipedia (Full EN)',           '~22 GB',  'Complete reference — large download'],
    ], widths=[0.5*inch, 2.0*inch, 0.9*inch, CW-3.4*inch]))
    s.append(SP(6))
    s.append(P('Adding a Custom ZIM', H2))
    s += steps([
        'Download a ZIM from kiwix.org to a device with internet.',
        'Copy it to the Pi: <font face="Courier" size="9">scp mybook.zim fieldcomms@192.168.50.1:/opt/kiwix/zim/</font>',
        'Register it: <font face="Courier" size="9">sudo kiwix-manage /opt/kiwix/library.xml add /opt/kiwix/zim/mybook.zim</font>',
        'Restart: <font face="Courier" size="9">sudo systemctl restart kiwix</font>',
        'Open http://192.168.50.1:8081 — the new content appears.',
    ])
    s.append(PB())
    return s


def ch33():
    s = chapter(33, 'Offline Maps, GPS & Health Monitor')
    s.append(P(
        'This chapter covers three infrastructure features that operate in the background '
        'to support the rest of FieldComms: the offline map tile system that powers both '
        'the Tactical APRS Map and the Starcom Resource Map, the GPS live position feed '
        'that provides accurate coordinates across all tools, and the Health Monitor '
        'that tracks system vitals and service status in real time.'))
    s.append(SP(6))

    s.append(P('32.1  Offline Map Tile System', H2))
    s.append(P(
        'Map tiles are downloaded in advance, stored as MBTiles files on the Pi, '
        'and served locally on port 8083. Both the Tactical APRS Map and Starcom '
        'Resource Map use offline tiles by default. The default source is USGS '
        'Imagery+Topo Hybrid — public-domain satellite imagery with roads, contours, '
        'and place names.'))
    s.append(SP(4))
    s.append(P('Downloading Tiles', H3))
    s += steps([
        'Run <font face="Courier" size="9">sudo bash /opt/fieldcomms/scripts/download_tiles.sh</font> for the interactive menu (106 presets: all Illinois counties, WI/IN/IA border counties, all 50 states).',
        'Search presets: <font face="Courier" size="9">download_tiles.sh --search "mchenry"</font>',
        'Download a preset: <font face="Courier" size="9">download_tiles.sh --area "McHenry County IL" --zoom 8-16</font>',
        'Tiles are stored in /opt/fieldcomms/data/tiles/ and served by the tile server on port 8083.',
    ])
    s.append(SP(8))

    s.append(P('32.2  GPS Live Position', H2))
    s.append(P(
        'If a USB GPS receiver is connected to the Pi (via the powered USB hub), '
        'gpsd provides live coordinates to the tactical map, health monitor, and '
        'NWS alerts. The GPS receiver creates a stable <b>/dev/gps0</b> device via '
        'udev rules installed automatically.'))
    s.append(SP(4))
    s.append(tbl(['CHECK', 'COMMAND'], [
        ['GPS status',      'gpspipe -w -n 5'],
        ['GPS device',      'ls -la /dev/gps0'],
        ['gpsd status',     'sudo systemctl status gpsd'],
        ['Live fix data',   'cgps -s'],
    ], widths=[1.4*inch, CW-1.4*inch]))
    s.append(SP(8))

    s.append(P('32.3  Health Monitor', H2))
    s.append(P(
        'The health monitor runs as a background service on port 5051 and feeds '
        'the dashboard sidebar with live system diagnostics. '
        'Raw data is at <b>http://192.168.50.1:5051/health</b>.'))
    s.append(SP(4))
    s.append(tbl(['METRIC', 'NORMAL', 'ACTION IF EXCEEDED'], [
        ['CPU Temperature', '< 70°C',   'Improve ventilation. Pi 5 throttles at 85°C.'],
        ['Memory Usage',    '< 80%',    'Close unused browser tabs; restart non-essential services'],
        ['Disk Usage',      '< 90%',    'Archive old logs; remove unused ZIM files'],
        ['Service Status',  'All green','Red dot = service down. Restart with systemctl.'],
        ['Internet',        'Connected (if avail.)', 'Check Ethernet. Core features work offline.'],
        ['GPS',             'Fix (if attached)', 'No GPS is fine — coordinates configured at install.'],
    ], widths=[1.5*inch, 1.2*inch, CW-2.7*inch]))
    s.append(SP(4))
    s.append(P('Restarting a Stopped Service', H3))
    s.append(P('<font face="Courier" size="8.5">sudo systemctl restart fcc-lookup  '
               '# or: health-monitor, ics-platform, fieldcomms-refs, kiwix, deadmans</font>', Body))
    s.append(PB())
    return s


def ch34():
    s = chapter(34, 'Network Hardware — ASUS RT-BE58 Go & UniFi Switch Lite 16')
    s.append(P(
        'FieldComms v1.0 uses a three-router mesh network rather than a single access point. '
        'The primary ASUS RT-BE58 Go travel router manages WAN connectivity, DHCP, and the '
        'EMCOMM-NET Wi-Fi access point. Two additional RT-BE58 Go routers operate as AiMesh '
        'nodes extending EMCOMM-NET to secondary rooms, outdoor staging areas, and upper floors '
        '— all sharing the same SSID and password with seamless device roaming. '
        'The Pi itself never broadcasts Wi-Fi. It communicates over wired Ethernet only.'))
    s.append(SP(4))
    s.append(tbl(['DEVICE', 'ROLE', 'CONNECTION'], [
        ['ASUS RT-BE58 Go  (primary)',
         'Wi-Fi 7 AP  ·  DHCP server  ·  WAN gateway  ·  AiMesh controller',
         'WAN: InstyConnect cellular  ·  USB WAN: Starlink failover  ·  LAN: UniFi switch'],
        ['ASUS RT-BE58 Go  (mesh node 1)',
         'EMCOMM-NET extension — same SSID, seamless roaming',
         'Wired backhaul via UniFi Switch Port 11'],
        ['ASUS RT-BE58 Go  (mesh node 2)',
         'EMCOMM-NET extension — third coverage zone',
         'Wired backhaul via UniFi Switch Port 12'],
        ['UniFi Switch Lite 16 PoE',
         '16-port GbE managed switch  ·  8x PoE  ·  wired distribution hub',
         'Port 1: router uplink  ·  Ports 2-12: devices  ·  Ports 13-16: spare'],
    ], [1.4*inch, 2.4*inch, CW-3.8*inch]))
    s.append(SP(6))

    s.append(P('33.1  EMCOMM-NET Wi-Fi Coverage', H2))
    s.append(P(
        'All three routers broadcast EMCOMM-NET on 2.4 GHz and 5 GHz simultaneously. '
        'Devices connect to whichever band and router provides the strongest signal '
        'and roam automatically as operators move around the venue. '
        'A single RT-BE58 Go covers approximately 2,000 to 2,500 square feet indoors. '
        'With both mesh nodes active, the system covers 7,500 to 20,000 square feet '
        'depending on building construction. '
        'For outdoor SAR staging areas, a node on battery at the perimeter '
        'extends EMCOMM-NET to field positions without additional cabling.'))
    s.append(SP(6))

    s.append(P('33.2  WAN Connectivity — InstyConnect Primary + Starlink Failover', H2))
    s.append(P(
        'The ASUS router manages two WAN sources with automatic failover. '
        'InstyConnect cellular (T-Mobile and Verizon dual-carrier) is always the primary. '
        'Starlink satellite is secondary — the ASUS switches to it automatically '
        'within 30 to 60 seconds when cellular drops, and switches back when cellular recovers. '
        'No operator action is required for the failover in either direction.'))
    s.append(SP(4))
    s.append(tbl(['PRI', 'WAN SOURCE', 'CONNECTION', 'ACTIVATES'], [
        ['1',
         'InstyConnect  (T-Mobile + Verizon)',
         'PoE Ethernet from Drum or Switchblade to ASUS WAN port',
         'Always — default for all activations'],
        ['2',
         'Starlink satellite',
         'Starlink Ethernet adapter + USB-Ethernet to ASUS USB WAN',
         'Auto when cellular drops'],
        ['3',
         'EOC site Ethernet',
         'Site cable to ASUS WAN port',
         'Manual — when site internet available'],
        ['4',
         'USB tether or venue Wi-Fi',
         'Phone USB to ASUS USB port  or  ASUS WISP mode',
         'Manual — emergency fallback'],
    ], [0.4*inch, 1.6*inch, 2.0*inch, CW-4.0*inch]))
    s.append(SP(6))

    s.append(P('33.3  InstyConnect Antennas', H2))
    s.append(P(
        'FieldComms carries two InstyConnect antennas to handle different deployment sites. '
        'Both connect via a single outdoor-rated PoE Ethernet cable to the ASUS WAN port. '
        'The modem is integrated into the outdoor antenna enclosure — '
        'no separate modem box is needed. Power travels up the same cable that carries data.'))
    s.append(SP(4))
    s.append(tbl(['ANTENNA', 'USE WHEN', 'AIMING'], [
        ['Drum  (omni 5G/LTE)',
         'Default — every activation. Mounts on any mast, tripod, or vehicle roof rack.',
         'No aiming needed — picks up all towers equally.'],
        ['Switchblade  (directional)',
         'When Drum signal is poor. Folds flat for transport. '
         'Swap the PoE cable from Drum to Switchblade on the same ASUS WAN port.',
         'Aim toward nearest tower using InstyConnect app. '
         'Rotate slowly — stop at peak signal.'],
    ], [1.3*inch, 2.4*inch, CW-3.7*inch]))
    s.append(SP(4))
    s.append(note(
        'InstyConnect data plan management: '
        'Keep the plan in Standby mode ($5/month) between activations. '
        'Standby maintains the SIM and multi-network capability so you can activate '
        'at full speed the moment an emergency is declared. '
        'Activate and pause plans at instyconnect.com. '
        'Active plan cost is approximately $79-99/month on the Multi-Network Unlimited plan.',
        'tip'))
    s.append(SP(6))

    s.append(P('33.4  WAN Status Dashboard', H2))
    s.append(P(
        'The WAN Status Dashboard at http://192.168.50.1/wan-status.html gives '
        'operators a live view of all WAN sources from any browser on EMCOMM-NET. '
        'The active WAN source is shown in a large color-coded panel: '
        'green for InstyConnect cellular, blue for Starlink satellite, red for offline. '
        'InstyConnect signal strength, carrier, and technology are displayed. '
        'Starlink latency, throughput, and obstruction percentage appear when the dish is active. '
        'A connectivity test panel verifies reachability to NWS weather alerts, '
        'APRS-IS, Cloudflare DNS, and the AMPRNet gateway every 60 seconds. '
        'A WAN event log records every failover and failback with UTC timestamps.'))
    s.append(SP(6))

    s.append(P('33.5  AMPRNet / 44Net Gateway', H2))
    s.append(P(
        'A dedicated Raspberry Pi 5 at 192.168.50.2 runs the AMPRNet gateway service. '
        'It maintains a permanent WireGuard encrypted tunnel to amprgw.ampr.org and '
        'routes the entire 44.0.0.0/8 AMPRNet address block for all EMCOMM-NET devices. '
        'This means any device on EMCOMM-NET — phones, tablets, operator workstations, '
        'and the FieldComms Pi itself — can reach other AMPRNet stations globally '
        'without routing traffic through the commercial internet.'))
    s.append(SP(4))
    s.append(tbl(['AMPRNET USE CASE', 'HOW IT WORKS'], [
        ['Winlink via AMPRNet',
         'Pat Winlink connects to Winlink RMS gateways on 44.x.x.x directly over AMPRNet — '
         'bypassing commercial internet when only amateur radio paths are available.'],
        ['APRS-IS via AMPRNet',
         'Graywolf and YAAC connect to APRS-IS servers on 44.x.x.x — '
         'keeping APRS traffic within the amateur radio network.'],
        ['Inter-node FieldComms',
         'If a second MCESV FieldComms system with its own 44Net gateway is deployed, '
         'the two systems can share data over AMPRNet without commercial internet routing.'],
        ['Direct station connectivity',
         'Any amateur station worldwide with a 44.x.x.x address is directly reachable '
         'from any EMCOMM-NET device for data exchange or status checking.'],
    ], [1.8*inch, CW-1.8*inch]))
    s.append(SP(4))
    s.append(P(
        'The gateway status page at http://192.168.50.2:9000 shows tunnel state, '
        'last handshake time, AMPRNet address, bytes transferred, and system health '
        'of the gateway Pi. '
        'Access requires a valid FCC amateur radio callsign. '
        'The FieldComms dashboard health monitor also shows a 44Net status indicator '
        'updated every 30 seconds by the amprgate-poll background service.'))
    s.append(SP(6))

    s.append(P('33.6  AMPRNet Gateway — Access Control', H2))
    s.append(P(
        'Access to the AMPRNet gateway is restricted to FCC-licensed amateur radio '
        'operators. This is both a security measure and a Part 97 compliance requirement. '
        'The gateway uses a two-level access model:'))
    s.append(SP(4))
    s.append(tbl(['HOW TO ACCESS', 'WHAT YOU CAN DO'], [
        ['Status Dashboard  (any EMCOMM-NET device)  —  '
         'Open http://192.168.50.2:9000.  '
         'Enter your FCC callsign at the login prompt.  '
         'Validated against the local FCC database on the FieldComms Pi.',
         'View tunnel state, AMPRNet address, last handshake, '
         'traffic stats, routes, and gateway health.  Read-only — no tunnel control.'],
        ['Tunnel Control  (gateway Pi keyboard only)  —  '
         'Open Chromium to http://localhost:9001 on the gateway Pi itself.  '
         'Log in with FCC callsign.  '
         'Port 9001 is blocked from the network — physical presence required.',
         'Bring tunnel up / down / restart.  '
         'All actions logged with callsign, timestamp, and IP address.'],
    ], [3.0*inch, CW-3.0*inch]))
    s.append(SP(4))
    s.append(note(
        'The /api/status endpoint on port 9000 does not require authentication. '
        'This is intentional — the FieldComms Pi poll service reads it every 30 seconds '
        'as a machine-to-machine call to update the dashboard WAN indicator. '
        'This endpoint is read-only and returns no sensitive data. '
        'All web UI access and all tunnel control actions are logged to '
        '/var/log/amprgate-access.log on the gateway Pi.',
        'note'))
    s.append(SP(6))

    s.append(P('33.7  Network IP Reference', H2))
    s.append(tbl(['DEVICE', 'IP ADDRESS', 'ADMIN URL'], [
        ['FieldComms Pi 5',  '192.168.50.1',   'http://192.168.50.1'],
        ['44Net Gateway Pi 5',                     '192.168.50.2',   'http://192.168.50.2:9000'],
        ['ASUS RT-BE58 Go  (primary router)',       '192.168.50.254', 'http://192.168.50.254'],
        ['Windows Laptop  (recommended)',           '192.168.50.3',   'DHCP reservation in router'],
        ['Color MFP Printer  (recommended)',        '192.168.50.10',  'DHCP reservation in router'],
        ['Pi 500 Workstations  (×4)',              '192.168.50.20–23', 'DHCP reservations in router'],
        ['InstyConnect modem',                     '10.1.1.1',       'http://10.1.1.1  (via InstyConnect Wi-Fi)'],
        ['Starlink dish admin',                    '192.168.100.1',  'http://192.168.100.1  (via Starlink network)'],
        ['Field devices  (DHCP)',                  '192.168.50.100–200', 'Assigned automatically by ASUS router'],
        ['CUPS print server',                      '192.168.50.1',   'http://192.168.50.1:631'],
        ['Kiwix offline library',                  '192.168.50.1',   'http://192.168.50.1:8081'],
        ['Pat Winlink',                            '192.168.50.1',   'http://192.168.50.1:8090'],
        ['Health Monitor API',                     '192.168.50.1',   'http://192.168.50.1:5050/health'],
        ['WAN Status Dashboard',                   '192.168.50.1',   'http://192.168.50.1/wan-status.html'],
        ['AMPRNet Gateway Status',                 '192.168.50.2',   'http://192.168.50.2:9000'],
    ], [2.2*inch, 1.4*inch, CW-3.6*inch]))
    s.append(PB())
    return s


    s = chapter(35, 'JS8Call — HF Digital Keyboard Messaging (Windows)')
    s.append(P(
        'JS8Call is a weak-signal HF digital mode designed for keyboard-to-keyboard '
        'messaging, store-and-forward relay, and group nets — all without an internet '
        'connection. It runs on the Windows laptop alongside Winlink Express, connected '
        'to the IC-7300 via USB. The FieldComms dashboard provides a quick-launch card '
        'that opens JS8Call\'s built-in web interface from any device on EMCOMM-NET.'))
    s.append(SP(6))
    s.append(P('What JS8Call Does', H2))
    s.append(tbl(['CAPABILITY', 'DESCRIPTION'], [
        ['Keyboard-to-keyboard', 'Type messages directly to any JS8 station within range — no internet required'],
        ['Store and forward',    'Messages are relayed station-to-station across multiple hops when no direct path exists'],
        ['Group / net messaging','Send a message addressed to a group callsign (e.g. @EMCOMM); any station in the group receives it'],
        ['Heartbeats',           'Periodic automatic transmissions that advertise station presence — great for EmComm awareness'],
        ['APRS-like reporting',  'Station info (grid, frequency, status) reported to JS8Call.info when internet is available'],
    ], widths=[1.6*inch, CW-1.6*inch]))
    s.append(SP(6))

    s.append(P('Enabling the JS8Call API', H2))
    s += steps([
        'In JS8Call, go to <b>File → Settings</b> (or press F2).',
        'Click the <b>Reporting</b> tab.',
        'Set <b>TCP Server Hostname</b> to <b>0.0.0.0</b> (allows any device on EMCOMM-NET to connect).',
        'Check <b>Enable TCP Server API</b>.',
        'Verify <b>TCP Server Port</b> is set to <b>2442</b>.',
        'Check <b>Accept TCP Requests</b>.',
        'Check <b>Allow setting station information from network</b>.',
        'Click OK. Restart JS8Call for the settings to take effect.',
    ])
    s.append(SP(6))

    s.append(P('Using JS8Call from FieldComms', H2))
    s += steps([
        'Note the Windows laptop\'s IP address on EMCOMM-NET: run <font face="Courier" size="9">ipconfig</font> in Command Prompt and look for the 192.168.50.x address.',
        'On any EMCOMM-NET device, open FieldComms and tap the <b>JS8Call</b> card.',
        'A prompt appears asking for the Windows laptop\'s IP address.',
        'Enter the IP address (e.g. 192.168.50.105). Click OK.',
        'The card opens JS8Call\'s web interface at http://192.168.50.105:2442.',
        'The IP is saved on that device. Future taps open JS8Call directly.',
    ])
    s.append(SP(4))
    s.append(note(
        'Never leave both Winlink Express and JS8Call connected to the IC-7300 in an '
        'active session simultaneously — they will key over each other. '
        'Close or disconnect one before activating the other.', 'warn'))
    s.append(SP(4))
    s.append(P('Recommended JS8Call Frequency', H3))
    s.append(P(
        '<b>7.078 MHz USB-D</b> — the 40m JS8Call calling frequency. '
        'Also used: 14.078 MHz (20m), 3.578 MHz (80m for regional/night operations).'))
    s.append(PB())
    return s


def ch35():
    s = chapter(35, 'JS8Call — HF Digital Keyboard Messaging  (Windows)',
                'http://192.168.50.1/js8call')
    s.append(P(
        'JS8Call is a keyboard-to-keyboard HF digital messaging mode based on FT8 technology. '
        'It is designed for very weak signal conditions — stations can exchange readable '
        'messages at signal levels 20 dB below what voice would require. '
        'JS8Call supports direct messaging between two stations, group messaging to a '
        'named group callsign such as @EMCOMM, store-and-forward relay through '
        'intermediate stations when no direct path exists, and heartbeat beacons '
        'that advertise a station presence automatically.'))
    s.append(SP(4))
    s.append(P(
        'JS8Call runs on the Windows laptop alongside Winlink Express, both connected '
        'to the IC-7300 via the single USB cable. The FieldComms dashboard provides a '
        'purple JS8Call quick-launch card that opens JS8Call built-in web interface '
        'from any device on EMCOMM-NET — operators at the EOC table can monitor JS8Call '
        'traffic from their phones or tablets without being at the Windows laptop.'))
    s.append(SP(6))

    s.append(P('34.1  Recommended JS8Call Frequencies', H2))
    s.append(tbl(['BAND', 'DIAL FREQUENCY', 'NOTES'], [
        ['40m  (primary for ARES/RACES)', '7.078.0 MHz', 'Primary JS8Call calling frequency — most activity'],
        ['80m  (regional, nighttime)',    '3.578.0 MHz', 'Good regional coverage after dark'],
        ['20m  (long distance)',          '14.078.0 MHz', 'DX and national nets — good during daylight'],
        ['17m  (secondary)',              '18.104.0 MHz', 'Less congested alternative to 20m'],
        ['60m  (emergency designated)',   '5.357.0 MHz USB', 'FCC Part 97.303(h) emergency channels'],
    ], [1.2*inch, 1.6*inch, CW-2.8*inch]))
    s.append(SP(6))

    s.append(P('34.2  JS8Call for EmComm', H2))
    s.append(tbl(['USE CASE', 'HOW TO DO IT'], [
        ['Direct station message',
         'Type @[CALLSIGN]:  followed by your message. The addressed station receives it '
         'even if they are not actively watching — JS8Call stores incoming messages.'],
        ['Group message  (all EMCOMM stations)',
         'Type @EMCOMM:  followed by your message. All stations monitoring the @EMCOMM '
         'group receive it and it appears highlighted in their message window.'],
        ['Heartbeat beacon  (announce presence)',
         'Enable Heartbeat in JS8Call settings. Your station transmits a short beacon '
         'every 15 minutes advertising your callsign, grid, and signal strength.'],
        ['Store-and-forward relay',
         'If direct contact is not possible, any intermediate JS8Call station on the '
         'path can relay your message to the destination automatically.'],
        ['Query station SNR',
         'Send  CALLSIGN SNR?  to ask a station to report your signal strength. '
         'Useful for propagation assessment before attempting Winlink.'],
    ], [1.6*inch, CW-1.6*inch]))
    s.append(PB())
    return s

def ch36():
    s = chapter(36, 'ICS Planning P — Operational Planning Cycle',
                'http://192.168.50.1/ics/planningp.html')
    s.append(P(
        'The Planning P page is an interactive guide to the ICS operational planning '
        'cycle. It presents all 15 phases of the Planning P — from the initial incident '
        'through each operational period — with the standard agenda, required ICS forms, '
        'and attendee list for every phase. Access it from the <b>🅿 Planning P</b> tab '
        'on any ICS platform page.'))
    s.append(SP(6))

    s.append(P('The 15 Phases', H2))
    s.append(tbl(['PHASE', 'NAME', 'KEY FORMS'], [
        ['1',  'Incident / Event',                          'ICS-201 (begin)'],
        ['2',  'Notification',                              'ICS-201'],
        ['3',  'Initial Response & Assessment',             'ICS-201'],
        ['4',  'Initial UC Meeting',                        'ICS-201, ICS-202'],
        ['5',  'Incident Brief — ICS-201',                  'ICS-201'],
        ['6',  'IC/UC Develop/Update Objectives Meeting',   'ICS-202'],
        ['7',  'Command & General Staff Meeting/Briefing',  'ICS-202, ICS-203'],
        ['8',  'Preparing for the Tactics Meeting',         'ICS-215, ICS-215A'],
        ['9',  'Tactics Meeting',                           'ICS-215, ICS-215A, ICS-203, ICS-204'],
        ['10', 'Preparing for the Planning Meeting',        'ICS-204, ICS-205, ICS-206, ICS-207, ICS-208'],
        ['11', 'Planning Meeting',                          'ICS-202 through ICS-206'],
        ['12', 'IAP Prep & Approval',                       'ICS-202 through ICS-208 (complete IAP)'],
        ['13', 'Operations Briefing',                       'Complete IAP, ICS-204 by Division'],
        ['14', 'Execute Plan & Assess Progress',            'ICS-214, ICS-209, ICS-309'],
        ['15', 'New Ops Period Begins',                     'ICS-214, ICS-209'],
    ], widths=[0.4*inch, 2.4*inch, CW-2.8*inch]))
    s.append(SP(6))

    s.append(P('Using the Planning P Page', H2))
    s += steps([
        'Open the ICS Platform (http://192.168.50.1/ics/) and click the <b>🅿 Planning P</b> tab.',
        'The reference image of the official Planning P diagram is shown on the left for reference.',
        'The 15 phase buttons are listed in the center panel, organized into five color-coded groups.',
        'Click any phase button to see its details in the right panel.',
    ])
    s.append(SP(6))

    s.append(P('Phase Detail Panel', H2))
    s.append(tbl(['SECTION', 'WHAT IT SHOWS'], [
        ['Standard Agenda', 'Numbered list of the standard agenda items for that meeting or activity'],
        ['Required Forms',  'ICS form numbers as clickable chips — click to open the form directly'],
        ['Who Should Attend', 'List of ICS roles required or optional for that phase, with red/green roster dots showing who is currently checked in'],
    ], widths=[1.6*inch, CW-1.6*inch]))
    s.append(SP(6))

    s.append(P('The Phase Color Groups', H2))
    s.append(tbl(['COLOR', 'GROUP', 'PHASES', 'ICS PHASE OF PLANNING'], [
        ['Gray',   'Initial Response',           '1–5',   'Stem — initial incident response'],
        ['Yellow', 'Establish Objectives',       '6–7',   'Stem — incident objectives set by IC/UC'],
        ['Red',    'Develop the Plan',           '8–11',  'Loop — tactics through planning meeting'],
        ['Green',  'Prepare & Disseminate',      '12–13', 'Loop — IAP approval and ops briefing'],
        ['Teal',   'Execute, Evaluate & Revise', '14–15', 'Loop — field operations and next period'],
    ], widths=[0.7*inch, 1.6*inch, 0.6*inch, CW-2.9*inch]))
    s.append(SP(4))
    s.append(P('Generating a Briefing Sheet', H2))
    s += steps([
        'Select any phase by clicking its button.',
        'Click <b>Generate briefing sheet</b> in the detail panel.',
        'A printable one-page cover sheet opens with the phase name, agenda, required forms, and an attendance table with signature lines.',
        'Print it for the IAP package or the planning meeting folder.',
    ])
    s.append(note(
        'The Planning P page is a guide, not a workflow enforcer. You do not need to '
        'click through the phases in order. Use it as a quick reference during planning '
        'meetings to ensure nothing is missed — especially on activations where the '
        'planning cycle is compressed.', 'tip'))
    s.append(PB())
    return s


def ch_appendix():
    s = chapter(34, 'Appendix — Administration & Quick Reference')
    s.append(P('A1  Installation & Updates', H2))
    s.append(tbl(['COMMAND', 'WHAT IT DOES'], [
        ['sudo bash install.sh',          'Interactive installer — sets callsign, coordinates, Wi-Fi, services'],
        ['sudo bash update.sh',           'Updates FieldComms code and restarts services'],
        ['sudo bash kiwix_setup.sh',      'Install/manage Kiwix offline content'],
        ['sudo bash download_tiles.sh',   'Download offline map tiles'],
    ], widths=[2.8*inch, CW-2.8*inch]))
    s.append(SP(8))

    s.append(P('A2  Wi-Fi & Network', H2))
    s.append(tbl(['ITEM', 'DETAIL'], [
        ['SSID',         'EMCOMM-NET'],
        ['Pi IP',        '192.168.50.1 (static, set via nmcli on eth0)'],
        ['DHCP range',   '192.168.50.100 – 192.168.50.200'],
        ['Router admin', 'http://192.168.50.1 (ASUS RT-BE58 Go)'],
        ['CUPS admin',   'http://192.168.50.1:631 (printer management)'],
    ], widths=[1.6*inch, CW-1.6*inch]))
    s.append(SP(8))

    s.append(P('A3  Database Backup', H2))
    s.append(P(
        'The main database is a single SQLite file. Back it up by copying '
        '<b>fieldcomms.db</b> to a USB drive. Export the roster CSV monthly '
        'and keep a copy on a USB drive labeled FIELDCOMMS as a secondary backup. '
        'Plugging in a drive labeled FIELDCOMMS automatically triggers a full '
        'rsync backup of the application data via the udev backup rule.'))
    s.append(SP(8))

    s.append(P('A4  Winlink — Email Over Radio', H2))
    s.append(P(
        'MCESV/MCEMA uses <b>Winlink Express</b> as the primary Winlink client on the '
        'Windows laptop with the IC-7300 + VARA HF. '
        'The Pi also runs <b>Pat</b> as a backup browser-based Winlink client on port 8090. '
        'Never run both clients with an active session on the same radio simultaneously.'))
    s.append(SP(8))

    s.append(P('A5  Service & Port Reference', H2))
    s.append(tbl(['SERVICE', 'PORT', 'DESCRIPTION'], [
        ['nginx',              '80',   'Web server — serves all HTML pages'],
        ['fcc-lookup.service', '5050', 'FCC callsign API, net log, forms, DMS, roster, resources'],
        ['health-monitor.service','5051','System health API'],
        ['ics-platform.service','5055','ICS incident platform API'],
        ['fieldcomms-refs.service','5056','Reference library API'],
        ['Graywolf APRS',      '8080', 'APRS client with REST API and WebSocket'],
        ['Kiwix',              '8081', 'Offline library — WikiMed, Wikipedia, iFixit'],
        ['YAAC APRS',          '8082', 'Secondary APRS client'],
        ['Tile server',        '8083', 'Offline map tile server (MBTiles)'],
        ['Pat Winlink',        '8090', 'Browser-based backup Winlink client'],
        ['CUPS printer',       '631',  'Print server — USB printer shared to EMCOMM-NET'],
        ['JS8Call (Windows)',  '2442', 'JS8Call TCP API on Windows laptop'],
    ], widths=[1.8*inch, 0.6*inch, CW-2.4*inch]))
    s.append(PB())
    return s


print("Chapters 19-36 + Appendix module loaded OK")
