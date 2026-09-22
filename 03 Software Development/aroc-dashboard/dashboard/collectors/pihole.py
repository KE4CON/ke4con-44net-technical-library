# AROC Dashboard — Pi-hole collector.  GPLv3, see dashboard/__init__.py.
"""Pi-hole (v6 REST API, with a v5 ``api.php`` fallback).

v6: ``POST /api/auth`` with the web password yields a session id (``sid``) that
is then sent as a header.  Sessions are limited, so we keep one and only
re-authenticate on 401.  Stats come from ``/api/stats/summary`` and the 24-hour
10-minute buckets from ``/api/history``.

v5: ``/admin/api.php?summaryRaw&auth=<API TOKEN>`` and ``overTimeData10mins``.

Config::

    - id: pihole
      type: pihole
      title: Pi-hole
      url: http://pihole.local/admin
      base_url: http://pihole.local          # v6: http(s)://host[:port]
      password: ${PIHOLE_PASSWORD}           # v6 web password (or app password)
      api_version: 6                          # or 5 with api_token: ${PIHOLE_TOKEN}
"""
from __future__ import annotations

from typing import Any

import httpx

from .base import Card, Collector, Stat, fmt_int, fmt_pct
from .http import make_client


def parse_v6_summary(summary: dict[str, Any]) -> dict[str, Any]:
    q = summary.get("queries", {})
    c = summary.get("clients", {})
    g = summary.get("gravity", {})
    return {
        "total": q.get("total", 0),
        "blocked": q.get("blocked", 0),
        "percent_blocked": q.get("percent_blocked", 0.0),
        "unique_domains": q.get("unique_domains"),
        "active_clients": c.get("active", 0),
        "total_clients": c.get("total"),
        "gravity_domains": g.get("domains_being_blocked"),
    }


def parse_v6_history(history: dict[str, Any], points: int) -> list[float]:
    buckets = history.get("history", [])
    return [float(b.get("total", 0)) for b in buckets[-points:]]


def parse_v5_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "total": summary.get("dns_queries_today", 0),
        "blocked": summary.get("ads_blocked_today", 0),
        "percent_blocked": summary.get("ads_percentage_today", 0.0),
        "unique_domains": summary.get("unique_domains"),
        "active_clients": summary.get("unique_clients", 0),
        "total_clients": None,
        "gravity_domains": summary.get("domains_being_blocked"),
    }


def parse_v5_history(data: dict[str, Any], points: int) -> list[float]:
    series = data.get("domains_over_time", {})
    keys = sorted(series, key=int)
    return [float(series[k]) for k in keys[-points:]]


class PiholeCollector(Collector):
    type = "pihole"
    icon = "dns"
    default_title = "Pi-hole"
    default_description = "DNS filtering and query intelligence."

    def __init__(self, cfg: dict[str, Any], history_points: int = 24) -> None:
        super().__init__(cfg, history_points)
        self.base = cfg["base_url"].rstrip("/")
        self.version = int(cfg.get("api_version", 6))
        self.points = history_points
        self._sid: str | None = None
        self._client: httpx.AsyncClient | None = None

    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = make_client(self.cfg, self.timeout)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            if self.version == 6 and self._sid:
                try:
                    await self._client.delete(f"{self.base}/api/auth", headers={"sid": self._sid})
                except httpx.HTTPError:
                    pass
            await self._client.aclose()

    # -- v6 --------------------------------------------------------------------
    async def _v6_login(self) -> str:
        resp = await self.client().post(f"{self.base}/api/auth", json={"password": self.cfg.get("password", "")})
        resp.raise_for_status()
        session = resp.json().get("session", {})
        if not session.get("valid"):
            raise RuntimeError(f"Pi-hole rejected the password: {session.get('message')}")
        self._sid = session["sid"]
        return self._sid

    async def _v6_get(self, path: str) -> dict[str, Any]:
        if not self._sid:
            await self._v6_login()
        resp = await self.client().get(f"{self.base}{path}", headers={"sid": self._sid or ""})
        if resp.status_code == 401:
            await self._v6_login()
            resp = await self.client().get(f"{self.base}{path}", headers={"sid": self._sid or ""})
        resp.raise_for_status()
        return resp.json()

    async def _fetch_v6(self) -> tuple[dict[str, Any], list[float], bool]:
        summary = parse_v6_summary(await self._v6_get("/api/stats/summary"))
        history = parse_v6_history(await self._v6_get("/api/history"), self.points)
        blocking = (await self._v6_get("/api/dns/blocking")).get("blocking") == "enabled"
        return summary, history, blocking

    # -- v5 --------------------------------------------------------------------
    async def _fetch_v5(self) -> tuple[dict[str, Any], list[float], bool]:
        token = self.cfg.get("api_token", "")
        base = f"{self.base}/admin/api.php"
        r1 = await self.client().get(base, params={"summaryRaw": "", "auth": token})
        r1.raise_for_status()
        raw = r1.json()
        r2 = await self.client().get(base, params={"overTimeData10mins": "", "auth": token})
        r2.raise_for_status()
        return parse_v5_summary(raw), parse_v5_history(r2.json(), self.points), raw.get("status") == "enabled"

    async def poll(self) -> Card:
        summary, history, blocking = await (self._fetch_v6() if self.version == 6 else self._fetch_v5())
        card = self.new_card()
        card.status_label = "BLOCKING ACTIVE" if blocking else "BLOCKING DISABLED"
        card.status_level = "ok" if blocking else "warn"
        card.hero_label = "Queries today"
        card.hero_value = fmt_int(summary["total"])
        card.hero_history = history or self.push_history(summary["total"])
        card.stats = [
            Stat("Blocked", fmt_int(summary["blocked"]), fmt_pct(summary["percent_blocked"]), "crit"),
            Stat("Active clients", fmt_int(summary["active_clients"])),
        ]
        if summary.get("gravity_domains") is not None:
            card.stats.append(Stat("Domains on blocklist", fmt_int(summary["gravity_domains"])))
        return card
