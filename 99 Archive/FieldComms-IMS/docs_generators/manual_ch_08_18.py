#!/usr/bin/env python3
"""manual_ch_08_18.py — Chapters 8–18 of the FieldComms User Manual."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from manual_framework import *


def ch8():
    s = chapter(8, 'Observer Mode — Read-Only Net View',
                'http://192.168.50.1/observer.html')
    s.append(P(
        'Observer Mode provides a read-only, auto-refreshing view of any active net. '
        'It is designed for served-agency personnel, EOC staff, emergency managers, '
        'and section leaders who need to monitor radio traffic without touching the '
        'net control interface. No login, no identity prompt, no setup required.'))
    s.append(SP(6))
    s.append(P('What Observer Mode Shows', H2))
    s.append(tbl(['ELEMENT', 'DESCRIPTION'], [
        ['Net name & status', 'Active net name, type (Amateur/Starcom), and open/closed indicator'],
        ['Live check-in log', 'All stations or units checked in, with timestamp, location, and remarks'],
        ['Traffic log',       'Formal message traffic passed during the net'],
        ['Station count',     'Live count of checked-in stations at the top of the page'],
        ['Auto-refresh',      'Page refreshes automatically every 15 seconds — no manual reload needed'],
    ], widths=[1.8*inch, CW-1.8*inch]))
    s.append(SP(6))
    s.append(P('How to Open Observer Mode', H2))
    s += steps([
        'On the Net Control Logger or Starcom Logger page, click <b>🔗 Observer Link</b> to copy the URL to your clipboard.',
        'Send the link by email, Winlink, JS8Call, or read it over the air to any operator who needs to monitor.',
        'The recipient opens the link in any browser on EMCOMM-NET — phones, tablets, and laptops all work.',
        'Observer Mode shows the net immediately with no identity prompt and no login.',
        'The net name is encoded in the URL so the link can be bookmarked for recurring nets.',
    ])
    s.append(SP(6))
    s.append(note(
        'Observer Mode is completely passive — observers cannot add check-ins, log traffic, '
        'or close the net. If an observer needs to interact, they must switch to the '
        'Net Control Logger or Starcom Logger and identify themselves first.', 'note'))
    s.append(PB())
    return s


def ch9():
    s = chapter(9, 'FCC Callsign Lookup', 'http://192.168.50.1/callsign.html')
    s.append(P(
        'The Callsign Lookup page provides instant offline access to the full FCC '
        'Amateur Radio ULS database — approximately 800,000 active licensees. '
        'No internet connection is required. Lookups are answered in milliseconds '
        'from the local SQLite database on the Pi.'))
    s.append(SP(6))
    s.append(P('Quick Callsign Lookup', H2))
    s += steps([
        'Type a callsign (e.g. K9ESV) in the search box at the top of the page.',
        'Press <b>Enter</b> or click <b>🔍 Look Up</b>.',
        'The result shows: full name, license class, expiration date, mailing address, grid square, and FRN.',
        'Click <b>+ Add to Roster</b> to add the licensee directly to the Member Roster.',
        'Recent lookups are saved automatically and shown below the search box for quick re-access.',
    ])
    s.append(SP(6))
    s.append(P('Advanced Search', H2))
    s += steps([
        'Click the <b>Advanced Search</b> tab.',
        'Enter any combination of: First Name, Last Name, City, State, License Class, or Grid Square.',
        'Click <b>Search</b>. Results show up to 100 matching licensees.',
        'Click any result row to see the full record.',
        'Click <b>+ Roster</b> on any result to add them to the Member Roster.',
    ])
    s.append(SP(6))
    s.append(note(
        'The FCC database is refreshed automatically every Sunday at 03:00 via the '
        '<b>fcc-refresh.timer</b> systemd timer (requires internet connection). '
        'The database status — record count and last update date — is shown at the '
        'bottom of the page.', 'note'))
    s.append(PB())
    return s


def ch10():
    s = chapter(10, 'Tactical APRS Map', 'http://192.168.50.1/tactical.html')
    s.append(P(
        'The Tactical APRS Map is a full-screen interactive map that combines live APRS '
        'station tracking with manual tactical overlays and offline map tiles. '
        'It pulls station data simultaneously from Graywolf (port 8080) and YAAC (port 8082), '
        'merges the feeds, deduplicates by callsign, and keeps every connected browser '
        'updated via WebSocket. The map works completely offline once tiles have been '
        'downloaded — no internet connection is needed to see stations or draw overlays.'))
    s.append(SP(4))
    s.append(P(
        'The default map layer is USGS Imagery+Topo Hybrid — public-domain satellite '
        'imagery with roads, contours, and place names overlaid. Additional tile sets '
        '(OpenStreetMap, Esri World Imagery) are available in the layer selector. '
        'McHenry County map tiles are included with the FieldComms installation. '
        'Additional county and state tile sets are downloaded using the '
        'download_tiles.sh script.'))
    s.append(SP(6))
    s.append(P('Map Layout', H2))
    s.append(tbl(['ELEMENT', 'DESCRIPTION'], [
        ['Left sidebar',  'Station list — all APRS stations received, with callsign, comment, distance, and last heard time'],
        ['Map area',      'Interactive Leaflet map with APRS symbols, custom overlays, and drawing tools'],
        ['Top toolbar',   'Layer toggles, tile selector, auto-refresh interval, range ring, and drawing tools'],
        ['Station labels','Callsign labels on the map — toggleable in settings'],
        ['Status bar',    'Station count, GPS status, last refresh time'],
    ], widths=[1.5*inch, CW-1.5*inch]))
    s.append(SP(6))
    s.append(P('APRS Sources — Graywolf and YAAC', H2))
    s.append(tbl(['SOURCE', 'PORT', 'DESCRIPTION'], [
        ['Graywolf', '8080', 'Primary APRS client — receives RF APRS via connected TNC or soundcard interface'],
        ['YAAC',     '8082', 'Secondary APRS client — backup receive and alternate TNC support'],
    ], widths=[1.2*inch, 0.7*inch, CW-1.9*inch]))
    s.append(SP(6))
    s.append(P('Station Tracking', H2))
    s += steps([
        'Click any station in the left sidebar to center the map on that station.',
        'Click <b>🛤 Track</b> to lock the map view on a specific station as it moves.',
        'Use the <b>Station age threshold</b> setting to hide stations older than N minutes.',
        'The search box filters the station list by callsign or comment text.',
    ])
    s.append(SP(6))
    s.append(P('Drawing Tactical Overlays', H2))
    s += steps([
        'Click a drawing tool in the toolbar: <b>Marker</b>, <b>Polygon</b>, <b>Circle</b>, or <b>Route</b>.',
        'Click on the map to place the shape. For polygons and routes, click multiple points and double-click to finish.',
        'Click a placed marker or shape to add a label or delete it.',
        'Overlays are saved to the server automatically and persist across browser sessions.',
        'Click <b>KML Export</b> to download the current overlay set as a KML file.',
    ])
    s.append(SP(6))
    s.append(P('GPS Position', H2))
    s.append(P(
        'If a USB GPS receiver is connected to the Pi, your current position appears '
        'on the map as a blue dot and is used to calculate distances in the station '
        'list. The GPS status indicator in the status bar shows the fix quality.'))
    s.append(SP(4))
    s.append(P('Range Rings', H2))
    s.append(P(
        'Enter a radius in km in the <b>Range ring</b> field and click <b>Draw Ring</b> '
        'to place a circle on the map centered on your GPS position or the station '
        'default coordinates. Useful for visualizing coverage areas.'))
    s.append(SP(6))

    s.append(P('9.4  Map Layers', H2))
    s.append(tbl(['LAYER', 'DESCRIPTION', 'AVAILABILITY'], [
        ['USGS Topo + Imagery  (default)',
         'USGS satellite imagery with roads, contours, and place names overlaid. '
         'Best for field operations and SAR.',
         'Offline — tiles stored on Pi'],
        ['OpenStreetMap',
         'Detailed street map with building outlines, trails, and POIs. '
         'Good for urban EOC operations.',
         'Offline — tiles stored on Pi'],
        ['Esri World Imagery',
         'High-resolution satellite imagery without overlays. '
         'Best for aerial reconnaissance and damage assessment.',
         'Online only — requires WAN'],
        ['NOAA NWS Radar  (overlay)',
         'Live NOAA radar precipitation overlay on any base layer. '
         'Updates every 5 minutes when WAN is available.',
         'Online only — requires WAN'],
    ], [1.4*inch, 2.4*inch, CW-3.8*inch]))
    s.append(SP(4))
    s.append(note(
        'Offline map tiles for McHenry County and surrounding counties are '
        'pre-loaded during installation. '
        'To download tiles for additional counties or states, run: '
        'sudo bash /opt/fieldcomms/scripts/download_tiles.sh --region [region-name]. '
        'Each county tile set uses approximately 200-500 MB of storage.',
        'tip'))
    s.append(PB())
    return s


def ch11():
    s = chapter(11, 'Starcom Resource Tracking Map',
                'http://192.168.50.1/resmap.html')
    s.append(P(
        'The Resource Tracking Map is a purpose-built situational awareness tool for '
        'Starcom public safety net operations. It shows unit positions on an offline '
        'map with status color coding, supports manual placement and drag-and-drop '
        'repositioning, and synchronizes with the Member Roster for unit information. '
        'Access it from the Starcom / Public Safety dashboard mode.'))
    s.append(SP(6))
    s.append(P('Placing a Unit on the Map', H2))
    s += steps([
        'Click <b>+ Add Unit</b> in the left panel.',
        'Enter the <b>Radio ID</b>, <b>Unit Name</b>, and <b>Type</b> (Law Enforcement, Fire, EMS, Search & Rescue, Communications, EOC, Shelter, Other).',
        'Enter a <b>Latitude</b> and <b>Longitude</b> directly, or click <b>📍 Pick on Map</b> to click the map and set the position.',
        'Set the <b>Status</b> (Available, Deployed, Staging, Out of Service).',
        'Click <b>Save</b>. The unit appears on the map with its status color.',
    ])
    s.append(SP(6))
    s.append(P('Status Colors', H2))
    s.append(tbl(['STATUS', 'COLOR', 'MEANING'], [
        ['Available',     'Green', 'Unit is on scene and available for assignment'],
        ['Deployed',      'Blue',  'Unit is actively assigned and in the field'],
        ['Staging',       'Amber', 'Unit is staging or en route'],
        ['Out of Service','Red',   'Unit is unavailable'],
    ], widths=[1.3*inch, 0.8*inch, CW-2.1*inch]))
    s.append(SP(6))
    s.append(P('Moving Units', H2))
    s += steps([
        'Click and drag a unit marker on the map to a new position.',
        'The unit\'s coordinates update automatically when you release.',
        'Alternatively, click the unit marker, click <b>Edit</b>, and update the coordinates manually.',
    ])
    s.append(SP(6))
    s.append(P('Drawing Zones', H2))
    s += steps([
        'Click <b>Draw Zone</b> to enter zone-drawing mode.',
        'Click multiple points on the map to define the zone boundary.',
        'Double-click to finish. Enter a zone name and color when prompted.',
        'Zones persist across browser sessions and appear on the map for all connected devices.',
        'Click <b>Clear Zones</b> to remove all zones.',
    ])
    s.append(PB())
    return s


def ch12():
    s = chapter(12, 'Resource Board', 'http://192.168.50.1/resources.html')
    s.append(P(
        'The Resource Board tracks all personnel, vehicles, equipment, and facilities '
        'assigned to an activation. Each resource is displayed as a card showing its '
        'current status. A stats strip at the top of the page shows live counts by '
        'status across all resource types.'))
    s.append(SP(6))
    s.append(P('The Five Status States', H2))
    s.append(tbl(['STATUS', 'COLOR', 'MEANING'], [
        ['Available',     'Green', 'On scene and available for assignment'],
        ['Assigned',      'Amber', 'Actively tasked with a specific assignment'],
        ['Staging',       'Blue',  'En route or at the staging area, not yet deployed'],
        ['Out of Service','Red',   'Unavailable — mechanical, medical, or administrative hold'],
        ['Demobilized',   'Gray',  'Released from the incident and departed'],
    ], widths=[1.3*inch, 0.8*inch, CW-2.1*inch]))
    s.append(SP(6))
    s.append(P('Adding a Resource', H2))
    s += steps([
        'Click <b>+ Add Resource</b>.',
        'Enter the <b>Name/Description</b> (e.g. "IC-7300 HF Radio", "Unit 12 — Medic", "Generator — 5kW Honda").',
        'Select the <b>Type</b>: Personnel, Vehicle, Radio, Generator, Antenna, Computer/Tablet, Medical, Shelter/Tent, Repeater, or Other.',
        'Set the <b>Status</b> and optionally fill in Owner/Callsign, Quantity, Location, Assigned To, Contact, and Notes.',
        'Click <b>Save Resource</b>. The card appears immediately.',
    ])
    s.append(SP(6))
    s.append(P('Changing a Resource Status', H2))
    s += steps([
        'Click the colored <b>status badge</b> on any resource card.',
        'Each click cycles through the five states in order: Available → Assigned → Staging → Out of Service → Demobilized → Available.',
        'The stats strip at the top updates instantly.',
    ])
    s.append(SP(6))
    s.append(P('Filtering the Board', H2))
    s += steps([
        'Use the <b>Type</b> filter dropdown to show only Personnel, Vehicles, Equipment, etc.',
        'Use the <b>Status</b> filter to show only Available or only Assigned resources.',
        'Filters can be combined — e.g. show all Assigned Personnel only.',
        'The stats strip always reflects all resources regardless of the active filter.',
    ])
    s.append(PB())
    return s


def ch13():
    s = chapter(13, "Dead Man's Switch — Net Inactivity Monitor",
                'http://192.168.50.1/deadmans.html')
    s.append(P(
        "The Dead Man's Switch (DMS) is a net inactivity monitor. "
        "When armed for a specific net, it watches the last-activity timestamp on that net. "
        "If no check-in, no traffic entry, and no manual reset occurs within the configured "
        "threshold period, the DMS fires: an audible alarm sounds on every browser "
        "that has the DMS page open, the page background turns red, and a countdown "
        "flashes until the situation is resolved. "
        "This gives net control operators an automatic safety net against a silent radio, "
        "a dropped connection, or an unattended console during a long activation."))
    s.append(SP(4))
    s.append(P(
        "The DMS can be armed independently for each active net running in FieldComms. "
        "A major activation running a Starcom General Net, a Weather Net, and a SAR Net "
        "simultaneously can have each net on its own DMS with its own threshold. "
        "The DMS page runs in the browser tab where it was opened — "
        "keep it visible on a dedicated monitor or the net control operator display."))
    s.append(SP(6))

    s.append(P('12.1  How to Arm the DMS', H2))
    s.extend(steps([
        'Open http://192.168.50.1/deadmans.html in a browser on any EMCOMM-NET device.',
        'Select the net you want to monitor from the dropdown. '
        'All active nets in FieldComms appear here automatically.',
        'Set the threshold — how many minutes of inactivity before the alarm fires. '
        'Typical settings: 10 minutes for a busy net, 15 minutes for a weather or traffic net, '
        '5 minutes for a SAR net where frequent check-ins are expected.',
        'Click ARM. The countdown timer starts from the last recorded activity on that net.',
        'Leave the DMS tab open and visible. The alarm fires in this tab and browser only. '
        'For maximum coverage, open the DMS on a dedicated monitor at the net control position.',
    ]))
    s.append(SP(6))

    s.append(P('12.2  When the DMS Fires', H2))
    s.append(P(
        "When the inactivity threshold is exceeded the DMS fires immediately. "
        "The browser tab turns red, a loud alarm tone plays, and the countdown "
        "shows how long ago the last activity was recorded. "
        "Any of the following actions resets the DMS and stops the alarm:"))
    s.append(SP(4))
    s.append(tbl(['RESET ACTION', 'HOW', 'NOTES'], [
        ['Station check-in',
         'Any operator checks in via the Net Control Logger',
         'Most common reset — running the net normally keeps the DMS satisfied'],
        ['Traffic entry',
         'Any operator adds a traffic item to the log',
         'Logging a message or status update counts as activity'],
        ['Manual reset',
         'Click RESET on the DMS page',
         'Use during quiet periods — briefings, breaks, or scheduled silence'],
        ['Disarm',
         'Click DISARM on the DMS page',
         'Use when the net is formally closed'],
    ], [1.2*inch, 1.8*inch, CW-3.0*inch]))
    s.append(SP(6))

    s.append(P('12.3  Multiple Nets', H2))
    s.append(P(
        "Each net in FieldComms can have its own independent DMS instance. "
        "Open http://192.168.50.1/deadmans.html in separate browser tabs, "
        "one per net, and set different thresholds for each. "
        "For example: the Starcom General Net at 10 minutes, "
        "the RACES HF net at 20 minutes during an extended overnight activation, "
        "and the SAR Coordination Net at 5 minutes. "
        "Each tab monitors and alarms independently."))
    s.append(SP(4))
    s.append(note(
        "The DMS runs in the browser tab — it does not send alerts to other devices. "
        "If the operator closes the tab or the device goes to sleep, the DMS stops. "
        "For overnight or extended activations, use a dedicated device on AC power "
        "with screen-saver and sleep disabled for the DMS monitor.",
        'warn'))
    s.append(PB())
    return s

def ch14():
    s = chapter(14, 'Pre-Flight Deployment Checklist',
                'http://192.168.50.1/preflight.html')
    s.append(P(
        'The Pre-Flight Checklist is a structured GO / CAUTION / NO-GO deployment '
        'readiness assessment. Before any activation, run through the checklist to '
        'verify that all critical systems are operational.'))
    s.append(SP(6))
    s.append(P('Checklist Sections', H2))
    s.append(tbl(['SECTION', 'ITEMS COVERED'], [
        ['Power Systems',           'Shore/generator power, battery backup/UPS, solar panels, fuel supply, power distribution'],
        ['Communications Equipment','HF radio, VHF/UHF radio, go-kit radios, HF antenna, VHF antenna, repeater access, Winlink, JS8Call'],
        ['Computing & Software',    'Pi server boot, FCC database, nginx, API server, health monitor, paper backup forms'],
        ['Networking',              'ASUS router, EMCOMM-NET Wi-Fi, DHCP, field device connectivity, UniFi switch'],
        ['Field Supplies',          'Operator cards, printed forms, batteries, cables, tools, maps, personal PPE'],
        ['Coordination',            'Net frequency confirmed, EOC contact established, served agency notified, ICS structure assigned'],
    ], widths=[1.8*inch, CW-1.8*inch]))
    s.append(SP(6))
    s.append(P('Deployment Verdicts', H2))
    s.append(tbl(['VERDICT', 'MEANING'], [
        ['✅ GO',      'All required items passed — system is ready for deployment'],
        ['⚠ CAUTION', 'Some optional items failed — review before deploying'],
        ['🚫 NO-GO',  'One or more required items failed — do not deploy until resolved'],
    ], widths=[1.2*inch, CW-1.2*inch]))
    s.append(SP(6))
    s.append(P('Exporting the Report', H2))
    s += steps([
        'Click <b>Export Report</b> to generate a printable PDF summary of the checklist.',
        'The report includes the verdict, timestamp, and notes for all items.',
        'File the report with the incident documentation.',
    ])
    s.append(SP(4))
    s.append(note(
        'Run the Pre-Flight Checklist before every activation — even for exercises. '
        'It takes less than five minutes and catches configuration issues before they '
        'become problems during a real emergency.', 'tip'))
    s.append(PB())
    return s


def ch15():
    s = chapter(15, 'ICS Platform — Overview', 'http://192.168.50.1/ics/')
    s.append(P(
        'The ICS Platform is the full incident command and documentation system '
        'built into FieldComms. It covers all five standard ICS sections — '
        'Command, Operations, Planning, Logistics, and Finance/Admin — '
        'plus an interactive Planning P cycle guide. '
        'All five sections share a single active incident record, '
        'so changes made in Operations are immediately visible in Planning, '
        'and the Logistics comms plan feeds directly into printed IAP packages.'))
    s.append(SP(4))
    s.append(P(
        'The ICS Platform is accessible by selecting the ICS mode from the dashboard '
        'mode bar, or directly at http://192.168.50.1/ics/. '
        'All data is stored on the Pi and synchronized in real time across every device '
        'on EMCOMM-NET. Section chiefs at different tables in the EOC all see the same '
        'incident state simultaneously without refreshing their browsers.'))
    s.append(SP(6))
    s.append(P('Creating a New Incident', H2))
    s += steps([
        'From the main dashboard (ICS mode), click <b>🆕 New Incident</b>.',
        'Enter the Incident Name (required), Type, Location, Jurisdiction, Incident Commander, Op Period Duration, and an optional Situation Summary.',
        'Click <b>Create Incident</b>. The incident becomes the active incident for all ICS platform pages.',
    ])
    s.append(SP(6))
    s.append(P('ICS Navigation Tabs', H2))
    s.append(tbl(['TAB', 'SECTION', 'PRIMARY USE'], [
        ['⭐ Command',   'Command Section',        'Incident objectives, safety, weather, situation'],
        ['🔴 Operations','Operations Section',      'T-card board, resource assignments'],
        ['📋 Planning',  'Planning Section',        'IAP documents, resource status table, period tracking'],
        ['🟢 Logistics', 'Logistics Section',       'Comms plan, supply tracking, meals'],
        ['💜 Finance',   'Finance / Admin Section', 'Cost accounting, time tracking, procurement'],
        ['🅿 Planning P','Planning Cycle Guide',    'Step-by-step ICS planning cycle with forms and attendees'],
    ], widths=[1.2*inch, 1.5*inch, CW-2.7*inch]))
    s.append(SP(6))
    s.append(P('Supported Incident Types', H2))
    s.append(tbl(['TYPE', 'TYPICAL USE'], [
        ['Natural Disaster',         'Severe weather, flooding, earthquake, tornado response'],
        ['HazMat',                   'Chemical spill, gas leak, radiological incident'],
        ['Search & Rescue',          'Lost person, overdue hiker, water rescue'],
        ['Mass Casualty Incident',   'Multi-patient medical emergency, transportation accident'],
        ['Weather Net',              'Starcom/SKYWARN weather spotter activation'],
        ['Public Health',            'Disease outbreak, mass vaccination, shelter-in-place'],
        ['Other',                    'Any incident not covered by the above types'],
    ], widths=[1.8*inch, CW-1.8*inch]))
    s.append(SP(6))

    s.append(P('14.3  Multi-User Real-Time Collaboration', H2))
    s.append(P(
        'Every device on EMCOMM-NET connected to the ICS Platform sees the same '
        'incident state simultaneously. '
        'Changes made by the Operations Section Chief on one tablet appear immediately '
        'on the Planning Section Chief tablet and the Logistics Section Chief laptop '
        'without anyone pressing a refresh button. '
        'This real-time synchronization uses WebSocket connections maintained by '
        'the ics-platform background service on the Pi.'))
    s.append(SP(4))
    s.append(P(
        'The recommended workflow for a fully-staffed EOC activation is:'))
    s.append(SP(4))
    s.append(tbl(['POSITION', 'DEVICE', 'ICS SECTION'], [
        ['Incident Commander',     'Tablet on EMCOMM-NET', 'ics/command.html — objectives, safety, public info'],
        ['Operations Section Chief','Laptop on EMCOMM-NET','ics/operations.html — T-card board, resource assignments'],
        ['Planning Section Chief', 'Laptop on EMCOMM-NET', 'ics/planning.html — IAP tracker, situation status'],
        ['Logistics Section Chief','Tablet on EMCOMM-NET', 'ics/logistics.html — comms plan, supply requests'],
        ['Finance/Admin',          'Laptop on EMCOMM-NET', 'ics/finance.html — cost tracking, time log'],
        ['Net Control Operator',   'Pi 500 workstation',   'netcontrol.html + starcom.html — radio net logging'],
    ], [1.6*inch, 1.5*inch, CW-3.1*inch]))
    s.append(PB())
    return s


def ch16():
    s = chapter(16, 'ICS Command Section',
                'http://192.168.50.1/ics/command.html')
    s.append(P(
        'The Command Section captures the strategic-level information for the '
        'incident: incident objectives, safety hazards, weather summary, current '
        'situation, accomplishments, and planned actions. This content forms the '
        'core of the Incident Action Plan (IAP).'))
    s.append(SP(6))
    s.append(P('Incident Objectives (ICS-202)', H2))
    s += steps([
        'To add a pre-defined objective: click the <b>Select a common objective</b> dropdown. Choose from 100 common ICS objectives organized in 13 groups.',
        'The selected objective populates the text field below. Edit it if needed — fill in any bracketed placeholders such as [frequency], [location], or [time].',
        'If no edits are needed, click <b>+ Add</b> or press Enter.',
        'To add a completely custom objective: type it directly in the text field and click <b>+ Add</b>.',
        'Objectives are listed above the input field. Click the <b>✕</b> next to any objective to delete it.',
    ])
    s.append(SP(4))
    s.append(note(
        'The 100-item objectives dropdown is organized into 13 groups: Life Safety, '
        'Communications, Resource Management, Incident Command, Search & Rescue, '
        'Shelter & Mass Care, Weather & Natural Disaster, HazMat, Mass Casualty, '
        'Public Information, Finance & Administration, Demobilization, and '
        'MCESV/MCEMA Specific.', 'note'))
    s.append(SP(8))
    s.append(P('Situation Report Fields', H2))
    s.append(tbl(['FIELD', 'WHAT TO ENTER'], [
        ['Safety Message',    'Safety message for this operational period (ICS-208)'],
        ['Current Situation', 'Brief description of current incident status and key facts'],
        ['Accomplishments',   'What has been achieved so far this operational period'],
        ['Planned Actions',   'What operations are planned for the next operational period'],
        ['Weather Summary',   'Current and forecast weather affecting operations'],
    ], widths=[1.8*inch, CW-1.8*inch]))
    s.append(PB())
    return s


def ch17():
    s = chapter(17, 'ICS Operations Section',
                'http://192.168.50.1/ics/operations.html')
    s.append(P(
        'The Operations Section manages the tactical resources assigned to the '
        'incident. It uses a T-card style status board where resource cards can be '
        'dragged between status columns, mirroring a traditional ICS T-card board.'))
    s.append(SP(6))
    s.append(P('The T-Card Board', H2))
    s.append(tbl(['COLUMN', 'MEANING'], [
        ['Available',     'Resource is checked in and available for assignment'],
        ['Assigned',      'Resource has been given a tactical assignment'],
        ['Out of Service','Resource is unavailable — mechanical, medical, or other'],
        ['Staging',       'Resource is at the staging area awaiting assignment'],
        ['Released',      'Resource has been demobilized from the incident'],
    ], widths=[1.5*inch, CW-1.5*inch]))
    s.append(SP(6))
    s.append(P('Adding a Resource to the Board', H2))
    s += steps([
        'Click <b>+ Add Resource</b> or <b>+ Assignment</b>.',
        'Enter the resource name, type, callsign/Radio ID, and initial assignment.',
        'Click <b>Save</b>. The resource appears in the Available column.',
    ])
    s.append(SP(6))
    s.append(P('Moving Resources Between Columns', H2))
    s += steps([
        'Drag a resource card from one column to another to update its status.',
        'Alternatively, click the resource card to open its detail view, then change the status in the dropdown.',
        'All status changes are saved to the server immediately.',
    ])
    s.append(SP(6))
    s.append(P('Assignment Details', H2))
    s += steps([
        'Click any resource card to open the detail panel.',
        'Enter or update the <b>Assignment</b> (Division/Group), <b>Supervisor</b>, <b>Work Location</b>, and notes.',
        'This information feeds the ICS-204 Assignment List.',
        'Click <b>💾 Save</b> to commit the changes.',
    ])
    s.append(PB())
    return s


def ch18():
    s = chapter(18, 'ICS Planning Section',
                'http://192.168.50.1/ics/planning.html')
    s.append(P(
        'The Planning Section manages the Incident Action Plan documents, resource '
        'status summary table, and operational period tracking. It is where the PSC '
        'assembles all the pieces of the IAP before each operational period briefing.'))
    s.append(SP(6))
    s.append(P('IAP Tracker Tab', H2))
    s += steps([
        'Click the <b>IAP Tracker</b> tab.',
        'Each required form (ICS-202 through ICS-208) is listed with a completion checkbox.',
        'Check off each form as it is completed and added to the IAP package.',
        'The tracker shows the percentage of IAP completion at the top.',
    ])
    s.append(SP(6))
    s.append(P('Resource Status Summary', H2))
    s += steps([
        'Click the <b>Resource Status</b> tab.',
        'The table shows all resources by type with current status counts.',
        'Click <b>+ Add Row</b> to manually add a resource category.',
        'Counts update from the Operations Section T-card board automatically.',
    ])
    s.append(SP(6))
    s.append(P('Incident Documents', H2))
    s += steps([
        'Click the <b>Documents</b> tab to manage IAP-associated documents.',
        'Click <b>+ Add Document</b> to link an uploaded reference document to this incident.',
        'Enter the document title, form number, and notes.',
        'Documents are linked to the incident for archival purposes.',
    ])
    s.append(note(
        'The ICS-309 Communications Log (http://192.168.50.1/ics309.html) can be '
        'linked to any active incident from its own page. See Chapter 22 for '
        'details on the ICS-309 form.', 'note'))
    s.append(PB())
    return s


print("Chapters 8-18 module loaded OK")
