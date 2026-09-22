# AROC Dashboard — run a demo server with fake cards.  GPLv3.
"""``python -m dashboard.demo`` — preview the layout with no real devices."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

DEMO_CONFIG = """
dashboard:
  title: Operations Center (demo)
  subtitle: Fake data — nothing here is real
  refresh_seconds: 5
services:
  # every demo card polls every 5 s so the sparklines fill quickly
  - {id: pihole, type: demo, interval: 5, title: Pi-hole, icon: dns, status_label: BLOCKING ACTIVE, base_value: 16000, url: "http://example.invalid/admin"}
  - {id: wazuh, type: demo, interval: 5, title: Wazuh, icon: shield, status_label: MANAGER ONLINE, hero_label: Agents online, base_value: 3, items: true, url: "http://example.invalid"}
  - {id: ntp, type: demo, interval: 5, title: Time Server, icon: clock, status_label: SERVICE RUNNING, hero_label: Sync status, base_value: 40}
  - {id: fortigate, type: demo, interval: 5, title: FortiGate, icon: firewall, wide: true, status_label: FIREWALL ONLINE, hero_label: Firewall health, base_value: 12, table: true, url: "http://example.invalid"}
  - {id: sg300, type: demo, interval: 5, title: Cisco SG300, icon: switch, status_label: SWITCH ONLINE, hero_label: Uplink Mbps, base_value: 4, table: true, url: "http://example.invalid"}
  - {id: proxmox, type: demo, interval: 5, title: Proxmox VE, icon: server, status_label: NODE ONLINE, hero_label: Guests running, base_value: 9, items: true}
  - {id: plex, type: demo, interval: 5, title: Plex, icon: play, status_label: SERVER ONLINE, hero_label: Active streams, base_value: 2}
  - {id: ilo, type: demo, interval: 5, title: HP iLO, icon: chip, status_label: DEGRADED, status_level: warn, hero_label: Power draw, base_value: 180}
"""


def main() -> None:
    import uvicorn

    path = Path(tempfile.gettempdir()) / "aroc-dashboard-demo.yaml"
    path.write_text(DEMO_CONFIG, encoding="utf-8")
    os.environ["AROC_CONFIG"] = str(path)
    uvicorn.run("dashboard.main:app", host=os.environ.get("AROC_HOST", "127.0.0.1"),
                port=int(os.environ.get("AROC_PORT", "8080")), log_level="info")


if __name__ == "__main__":
    main()
