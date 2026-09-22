# AROC Dashboard — Plex Media Server collector.  GPLv3, see dashboard/__init__.py.
"""Plex Media Server via its local API with an ``X-Plex-Token``.

* ``/identity``                 server version
* ``/status/sessions``          active streams (who, what, transcode or direct)
* ``/library/sections``         libraries; each is counted with a zero-size page
  so ``totalSize`` comes back without the items.

Config::

    - id: plex
      type: plex
      url: http://plex.local:32400/web
      base_url: http://plex.local:32400
      token: ${PLEX_TOKEN}
"""
from __future__ import annotations

from typing import Any

import httpx

from .base import Card, Collector, Stat, Table, fmt_int
from .http import make_client


def parse_sessions(payload: dict[str, Any]) -> list[dict[str, Any]]:
    mc = payload.get("MediaContainer", {})
    out = []
    for m in mc.get("Metadata", []):
        title = m.get("title", "?")
        if m.get("grandparentTitle"):
            title = f"{m['grandparentTitle']} — {title}"
        player = m.get("Player", {})
        decision = "transcode" if any(s.get("videoDecision") == "transcode"
                                      for s in m.get("TranscodeSession", [{}]) if isinstance(s, dict)) else "direct"
        out.append({"title": title, "user": m.get("User", {}).get("title", "?"),
                    "state": player.get("state", "?"), "player": player.get("product") or player.get("title", ""),
                    "decision": decision})
    return out


def parse_sections(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"key": d.get("key"), "title": d.get("title"), "type": d.get("type")}
            for d in payload.get("MediaContainer", {}).get("Directory", [])]


class PlexCollector(Collector):
    type = "plex"
    icon = "play"
    default_title = "Plex"
    default_description = "Media server, active streams, and library size."

    def __init__(self, cfg: dict[str, Any], history_points: int = 24) -> None:
        super().__init__(cfg, history_points)
        self.base = cfg["base_url"].rstrip("/")
        self._client: httpx.AsyncClient | None = None

    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = make_client(self.cfg, self.timeout,
                                       headers={"X-Plex-Token": self.cfg["token"], "Accept": "application/json"})
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = await self.client().get(f"{self.base}{path}", params=params)
        resp.raise_for_status()
        return resp.json()

    async def poll(self) -> Card:
        identity = (await self._get("/identity")).get("MediaContainer", {})
        sessions = parse_sessions(await self._get("/status/sessions"))
        sections = parse_sections(await self._get("/library/sections"))
        counts = []
        for s in sections:
            mc = (await self._get(f"/library/sections/{s['key']}/all",
                                  {"X-Plex-Container-Start": 0, "X-Plex-Container-Size": 0})).get("MediaContainer", {})
            counts.append((s["title"], s["type"], mc.get("totalSize", mc.get("size", 0))))

        card = self.new_card()
        card.status_label = "SERVER ONLINE"
        card.status_level = "ok"
        card.hero_label = "Active streams"
        card.hero_value = str(len(sessions))
        card.hero_history = self.push_history(len(sessions))
        card.stats = [
            Stat("Transcoding", str(sum(1 for s in sessions if s["decision"] == "transcode"))),
            Stat("Libraries", str(len(sections))),
            Stat("Version", str(identity.get("version", "—"))),
        ]
        if sessions:
            card.tables.append(Table("Now playing", ["Title", "User", "Player"],
                                     [[s["title"], s["user"], f"{s['player']} ({s['decision']})"] for s in sessions],
                                     ["ok" if s["state"] == "playing" else "warn" for s in sessions]))
        if counts:
            card.tables.append(Table("Libraries", ["Library", "Type", "Items"],
                                     [[t, ty, fmt_int(n)] for t, ty, n in counts]))
        return card
