# AROC Dashboard — demo collector (fake data for layout preview).  GPLv3.
"""Generates plausible but fake data so the page can be previewed with no real
devices configured.  ``python -m dashboard.demo`` starts a demo server.
"""
from __future__ import annotations

import random
from typing import Any

from .base import Card, Collector, Stat, Table, fmt_int, fmt_mbps


class DemoCollector(Collector):
    type = "demo"
    icon = "generic"
    default_title = "Demo service"
    default_description = "Fake data for previewing the layout."

    def __init__(self, cfg: dict[str, Any], history_points: int = 24) -> None:
        super().__init__(cfg, history_points)
        self.rng = random.Random(cfg["id"])
        self.base_value = cfg.get("base_value", 1000)

    async def poll(self) -> Card:
        v = self.base_value * self.rng.uniform(0.6, 1.4)
        card = self.new_card()
        card.status_label = self.cfg.get("status_label", "ONLINE")
        card.status_level = self.cfg.get("status_level", "ok")
        card.hero_label = self.cfg.get("hero_label", "Queries today")
        card.hero_value = fmt_int(v)
        card.hero_history = self.push_history(v)
        card.stats = [
            Stat("Blocked", fmt_int(v * 0.045), "4.5%", "crit"),
            Stat("Active clients", str(self.rng.randint(8, 14))),
        ]
        if self.cfg.get("table"):
            rows = [[i * 10, n, self.rng.randint(0, 20)] for i, n in enumerate(["Management", "Trusted", "Servers", "IoT"], 1)]
            card.tables.append(Table("VLANs", ["VLAN", "Name", "Clients"], rows))
            card.tables.append(Table("Traffic", ["Interface", "↓ Down", "↑ Up"],
                                     [["Trusted", fmt_mbps(1.2e6), fmt_mbps(3e5)], ["IoT", fmt_mbps(3.9e6), fmt_mbps(4e5)]],
                                     ["ok", "ok"]))
        if self.cfg.get("items"):
            card.items = [{"label": n, "level": "ok"} for n in ("Aetherion", "Athena", "Argus")]
        return card
