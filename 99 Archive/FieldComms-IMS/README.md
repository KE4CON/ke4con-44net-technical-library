# FieldComms EmComm Field Server v1.0

Off-grid emergency communications server for Raspberry Pi.

## Quick Start

```bash
sudo bash scripts/install.sh
```

Then browse to: http://192.168.50.1/ (on EMCOMM-NET WiFi)
Or: http://localhost/ (locally)

## What's Included

### Web Frontend (26 pages)
| Page | Description |
|------|-------------|
| index.html | Main dashboard — clock, weather alerts, APRS table |
| netcontrol.html | Amateur net control logger with FCC autofill |
| starcom.html | Starcom net control (Radio IDs, sc- prefix) |
| observer.html | Read-only net viewer (?net= URL param) |
| roster.html | Member directory — 11 certs, 13 equipment fields |
| resources.html | Resource board with status cycling |
| tactical.html | APRS tactical map (Leaflet + Graywolf) |
| resmap.html | Starcom resource map with zone drawing |
| callsign.html | FCC callsign lookup |
| deadmans.html | Dead Man's Switch monitor with countdown |
| preflight.html | GO/CAUTION/NO-GO pre-deployment checklist |
| nts.html | NTS Radiogram generator |
| ics213.html | ICS-213 General Message form |
| ics214.html | ICS-214 Activity Log |
| grid.html | Grid square / Maidenhead calculator |
| repeaters.html | Repeater database browser |
| facilities.html | EOC/hospital/shelter directory |
| cheatsheets.html | Phonetic, Q-codes, prowords, band plan, ICS |
| printcenter.html | Unified print hub + incident cover sheet |
| propagation.html | HF propagation — solar indices, band conditions |
| ics/index.html | ICS Platform overview |
| ics/command.html | ICS Command section (ICS-201, 202, 203) |
| ics/operations.html | ICS Operations — T-cards, resources, ICS-204 |
| ics/planning.html | ICS Planning — situation status, IAP forms |
| ics/logistics.html | ICS Logistics — ICS-205, supply, meals, check-in |
| ics/finance.html | ICS Finance/Admin — cost accounting, time tracking |

### Python Services
| File | Port | Description |
|------|------|-------------|
| fcc_lookup_server.py | 5050 | Main API — FCC, nets, roster, APRS, forms, DMS |
| health_monitor.py | 5051 | System health — CPU, disk, GPS, services |
| deadmans.py | — | Background DMS state machine |
| ics_platform_server.py | 5055 | ICS incident management API |
| build_fcc_db.py | — | Downloads FCC amateur DB, builds SQLite |
| fetch_repeaters.py | — | Downloads RepeaterBook data |

## Port Map
- 80: nginx (web frontend)
- 5050: FCC Lookup / Main API
- 5051: Health Monitor
- 5055: ICS Platform
- 8080: Graywolf APRS
- 8081: Kiwix offline library
- 8090: Pat Winlink
- 2442: JS8Call
- 8300/8310: VARA HF/FM

## Default Credentials
- WiFi SSID: EMCOMM-NET
- WiFi Password: fieldcomms2026
- Server IP: 192.168.50.1

## Data Paths
- /opt/fieldcomms/data/ — runtime data
- /opt/fieldcomms/data/fcc.db — FCC database
- /var/www/html/ — web frontend

## Station Default (Columbus OH)
- Lat: 39.9612
- Lon: -82.9988
- Grid: EN90aa

Configured for your station during install.sh.
