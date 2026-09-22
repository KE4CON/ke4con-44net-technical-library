# AROC Dashboard — Proxmox VE collector.  GPLv3, see dashboard/__init__.py.
"""Proxmox VE via an API token (``Datacenter -> Permissions -> API Tokens``;
the token only needs ``PVEAuditor`` on ``/``).

``GET /api2/json/cluster/resources`` returns nodes, guests and storage in one
call: node CPU/RAM/uptime, every VM/LXC with its status, and storage usage.

Config::

    - id: proxmox
      type: proxmox
      url: https://pve.local:8006
      base_url: https://pve.local:8006
      token_id: ${PVE_TOKEN_ID}          # user@pam!tokenname
      token_secret: ${PVE_TOKEN_SECRET}
      verify_tls: false
"""
from __future__ import annotations

from typing import Any

import httpx

from .base import Card, Collector, Stat, Table, fmt_pct, fmt_uptime
from .http import make_client


def parse_resources(payload: dict[str, Any]) -> dict[str, Any]:
    nodes, guests, storage = [], [], []
    for r in payload.get("data", []):
        t = r.get("type")
        if t == "node":
            nodes.append({"name": r.get("node"), "online": r.get("status") == "online",
                          "cpu": (r.get("cpu") or 0) * 100,
                          "mem": (r.get("mem") or 0) / r["maxmem"] * 100 if r.get("maxmem") else None,
                          "uptime": r.get("uptime")})
        elif t in {"qemu", "lxc"}:
            guests.append({"name": r.get("name") or str(r.get("vmid")), "kind": t, "vmid": r.get("vmid"),
                           "running": r.get("status") == "running", "node": r.get("node")})
        elif t == "storage":
            pct = (r.get("disk") or 0) / r["maxdisk"] * 100 if r.get("maxdisk") else None
            storage.append({"name": r.get("storage"), "node": r.get("node"), "pct": pct,
                            "online": r.get("status") == "available"})
    guests.sort(key=lambda g: (not g["running"], g["name"].lower()))
    return {"nodes": nodes, "guests": guests, "storage": storage}


class ProxmoxCollector(Collector):
    type = "proxmox"
    icon = "server"
    default_title = "Proxmox VE"
    default_description = "Virtualization host, VMs, containers, and storage."

    def __init__(self, cfg: dict[str, Any], history_points: int = 24) -> None:
        super().__init__(cfg, history_points)
        self.base = cfg["base_url"].rstrip("/")
        self._client: httpx.AsyncClient | None = None

    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            auth = f"PVEAPIToken={self.cfg['token_id']}={self.cfg['token_secret']}"
            self._client = make_client(self.cfg, self.timeout, headers={"Authorization": auth})
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def poll(self) -> Card:
        resp = await self.client().get(f"{self.base}/api2/json/cluster/resources")
        resp.raise_for_status()
        data = parse_resources(resp.json())
        nodes, guests, storage = data["nodes"], data["guests"], data["storage"]
        online_nodes = sum(1 for n in nodes if n["online"])
        running = sum(1 for g in guests if g["running"])
        cpu = max((n["cpu"] for n in nodes if n["online"]), default=None)
        mem = max((n["mem"] for n in nodes if n["online"] and n["mem"] is not None), default=None)

        card = self.new_card()
        card.status_label = "NODE ONLINE" if online_nodes == len(nodes) and nodes else "NODE DOWN"
        card.status_level = "ok" if card.status_label == "NODE ONLINE" else "crit"
        card.hero_label = "Guests running"
        card.hero_value = f"{running} / {len(guests)}"
        card.hero_history = self.push_history(cpu)
        card.stats = [
            Stat("CPU", fmt_pct(cpu, 0), level="warn" if (cpu or 0) > 85 else None),
            Stat("Memory", fmt_pct(mem, 0), level="warn" if (mem or 0) > 90 else None),
            Stat("Uptime", fmt_uptime(max((n["uptime"] or 0 for n in nodes), default=None)),
                 ", ".join(n["name"] for n in nodes)),
            Stat("VMs / LXCs", f"{sum(1 for g in guests if g['kind'] == 'qemu')} / "
                               f"{sum(1 for g in guests if g['kind'] == 'lxc')}"),
        ]
        card.items = [{"label": g["name"], "level": "ok" if g["running"] else "unknown",
                       "title": f"{g['kind']} {g['vmid']} on {g['node']}"} for g in guests]
        if storage:
            card.tables.append(Table("Storage", ["Store", "Node", "Used"],
                                     [[s["name"], s["node"], fmt_pct(s["pct"], 0)] for s in storage],
                                     [("ok" if s["online"] else "crit") if (s["pct"] or 0) < 90 else "warn"
                                      for s in storage]))
        return card
