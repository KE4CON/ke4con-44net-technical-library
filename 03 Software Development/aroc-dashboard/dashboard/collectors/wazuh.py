# AROC Dashboard — Wazuh collector.  GPLv3, see dashboard/__init__.py.
"""Wazuh manager API (agents) plus, optionally, the Wazuh indexer (alerts and
vulnerabilities).

Manager (port 55000): ``POST /security/user/authenticate`` with basic auth
returns a JWT; ``GET /agents`` lists agents with ``status``.

Indexer (OpenSearch, port 9200): since Wazuh 4.8 vulnerability state lives in
``wazuh-states-vulnerabilities-*`` and alerts in ``wazuh-alerts-*``.  Both are
plain ``_count`` / ``_search`` queries with basic auth.  If no indexer is
configured those two tiles show "n/a" instead of failing the whole card.

Config::

    - id: wazuh
      type: wazuh
      url: https://wazuh.local
      api_url: https://wazuh.local:55000
      api_user: ${WAZUH_API_USER}
      api_password: ${WAZUH_API_PASSWORD}
      indexer_url: https://wazuh.local:9200          # optional
      indexer_user: ${WAZUH_INDEXER_USER}
      indexer_password: ${WAZUH_INDEXER_PASSWORD}
      alert_level: 12                                 # "high+" threshold
      exclude_manager: true                           # hide agent 000
      verify_tls: false
"""
from __future__ import annotations

from typing import Any

import httpx

from .base import Card, Collector, Stat, fmt_int
from .http import make_client

AGENT_LEVELS = {"active": "ok", "pending": "warn", "disconnected": "crit", "never_connected": "unknown"}


def parse_agents(payload: dict[str, Any], exclude_manager: bool = True) -> list[dict[str, Any]]:
    items = payload.get("data", {}).get("affected_items", [])
    out = []
    for a in items:
        if exclude_manager and a.get("id") == "000":
            continue
        out.append({"id": a.get("id"), "name": a.get("name", "?"), "status": a.get("status", "unknown")})
    return out


def alerts_query(min_level: int, hours: int = 24) -> dict[str, Any]:
    return {
        "size": 0,
        "query": {
            "bool": {
                "filter": [
                    {"range": {"rule.level": {"gte": min_level}}},
                    {"range": {"timestamp": {"gte": f"now-{hours}h"}}},
                ]
            }
        },
        "aggs": {"per_hour": {"date_histogram": {"field": "timestamp", "fixed_interval": "1h", "min_doc_count": 0,
                                                 "extended_bounds": {"min": f"now-{hours}h", "max": "now"}}}},
    }


def parse_alert_histogram(payload: dict[str, Any]) -> tuple[int, list[float]]:
    total = payload.get("hits", {}).get("total", {})
    count = total.get("value", 0) if isinstance(total, dict) else int(total or 0)
    buckets = payload.get("aggregations", {}).get("per_hour", {}).get("buckets", [])
    return count, [float(b.get("doc_count", 0)) for b in buckets]


class WazuhCollector(Collector):
    type = "wazuh"
    icon = "shield"
    default_title = "Wazuh"
    default_description = "Security monitoring, agents, and threat hunting."

    def __init__(self, cfg: dict[str, Any], history_points: int = 24) -> None:
        super().__init__(cfg, history_points)
        self.api = cfg["api_url"].rstrip("/")
        self.indexer = (cfg.get("indexer_url") or "").rstrip("/") or None
        self._token: str | None = None
        self._client: httpx.AsyncClient | None = None

    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = make_client(self.cfg, self.timeout)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def _login(self) -> str:
        resp = await self.client().post(f"{self.api}/security/user/authenticate",
                                        auth=(self.cfg["api_user"], self.cfg["api_password"]))
        resp.raise_for_status()
        self._token = resp.json()["data"]["token"]
        return self._token

    async def _api_get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self._token:
            await self._login()
        hdr = {"Authorization": f"Bearer {self._token}"}
        resp = await self.client().get(f"{self.api}{path}", params=params, headers=hdr)
        if resp.status_code == 401:
            await self._login()
            resp = await self.client().get(f"{self.api}{path}", params=params,
                                           headers={"Authorization": f"Bearer {self._token}"})
        resp.raise_for_status()
        return resp.json()

    async def _indexer_post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        resp = await self.client().post(f"{self.indexer}{path}", json=body,
                                        auth=(self.cfg.get("indexer_user", ""), self.cfg.get("indexer_password", "")))
        resp.raise_for_status()
        return resp.json()

    async def poll(self) -> Card:
        agents = parse_agents(await self._api_get("/agents", {"select": "name,status", "limit": 500}),
                              exclude_manager=bool(self.cfg.get("exclude_manager", True)))
        online = sum(1 for a in agents if a["status"] == "active")

        high_alerts: int | None = None
        crit_vulns: int | None = None
        hist: list[float] = []
        if self.indexer:
            level = int(self.cfg.get("alert_level", 12))
            high_alerts, hist = parse_alert_histogram(
                await self._indexer_post("/wazuh-alerts-*/_search", alerts_query(level)))
            vq = {"query": {"term": {"vulnerability.severity": "Critical"}}}
            crit_vulns = (await self._indexer_post("/wazuh-states-vulnerabilities-*/_count", vq)).get("count", 0)

        card = self.new_card()
        card.status_label = "MANAGER ONLINE"
        card.status_level = "ok" if online == len(agents) else ("warn" if online else "crit")
        card.hero_label = "Agents online"
        card.hero_value = f"{online} / {len(agents)}"
        card.hero_history = hist or self.push_history(online)
        card.stats = [
            Stat("High+ / 24h", fmt_int(high_alerts) if high_alerts is not None else "n/a",
                 level="crit" if high_alerts else None),
            Stat("Critical vulns", fmt_int(crit_vulns) if crit_vulns is not None else "n/a",
                 level="crit" if crit_vulns else None),
        ]
        card.items = [{"label": a["name"], "level": AGENT_LEVELS.get(a["status"], "unknown")} for a in agents]
        return card
