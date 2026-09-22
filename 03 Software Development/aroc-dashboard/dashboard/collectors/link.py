# AROC Dashboard — static link card.  GPLv3, see dashboard/__init__.py.
"""A card with no live data: just a title, description and an "Open" button.

Useful for anything that has no API worth polling (or that you have not wired
up yet) but that you still want one click away.  Optionally performs a plain
HTTP reachability check so the status pill is still meaningful.
"""
from __future__ import annotations

import time

from .base import Card, Collector
from .http import make_client


class LinkCollector(Collector):
    type = "link"
    icon = "link"
    default_title = "Link"

    async def poll(self) -> Card:
        card = self.new_card()
        check = self.cfg.get("check_url", self.url if self.cfg.get("check", False) else None)
        if not check:
            card.status_label = self.cfg.get("status_label", "LINK")
            card.status_level = "unknown"
            return card
        t0 = time.monotonic()
        async with make_client(self.cfg, self.timeout, follow_redirects=True) as client:
            resp = await client.get(check)
        ms = (time.monotonic() - t0) * 1000
        ok = resp.status_code < 500
        card.status_label = "REACHABLE" if ok else f"HTTP {resp.status_code}"
        card.status_level = "ok" if ok else "crit"
        card.hero_label = "Response time"
        card.hero_value = f"{ms:.0f} ms"
        card.hero_history = self.push_history(ms)
        return card
