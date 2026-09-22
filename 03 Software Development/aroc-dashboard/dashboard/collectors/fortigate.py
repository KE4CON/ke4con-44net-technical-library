# AROC Dashboard — FortiGate collector.  GPLv3, see dashboard/__init__.py.
"""FortiGate via its REST API (FortiOS 6.x/7.x) using a REST API admin token.

Endpoints used (all ``GET``, ``Authorization: Bearer <token>``):

* ``/api/v2/monitor/system/status``           firmware, hostname, serial
* ``/api/v2/monitor/system/resource/usage``   CPU / memory percent
* ``/api/v2/monitor/system/interface``        link state, IPs, byte counters
* ``/api/v2/cmdb/system/interface``           VLAN ids / names (to build the VLAN table)
* ``/api/v2/monitor/system/dhcp``             DHCP leases (counted per interface)
* ``/api/v2/monitor/wifi/client``             wireless clients (FortiAP)
* ``/api/v2/monitor/wifi/managed_ap``         AP state

"Public IP" on a double-NAT link is the ISP gateway's address, which the
FortiGate cannot know, so it is looked up from ``public_ip_url`` (default
``https://api.ipify.org``) by the dashboard host.  Set it to ``null`` to skip.

Config::

    - id: fortigate
      type: fortigate
      wide: true
      url: https://192.168.1.99
      base_url: https://192.168.1.99
      token: ${FORTIGATE_TOKEN}
      wan_interface: wan1
      vlan_names: {"10": "Management", "20": "Trusted"}   # optional label overrides
      hide_vlans: [1]                                        # optional
      verify_tls: false
"""
from __future__ import annotations

from collections import Counter
from typing import Any

import httpx

from .base import Card, Collector, RateTracker, Stat, Table, fmt_int, fmt_mbps, fmt_pct
from .http import make_client


def parse_resource_usage(payload: dict[str, Any]) -> tuple[float | None, float | None]:
    res = payload.get("results", {})

    def cur(key: str) -> float | None:
        vals = res.get(key) or []
        return float(vals[0].get("current")) if vals and "current" in vals[0] else None

    return cur("cpu"), cur("mem")


def parse_interfaces(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Normalise ``monitor/system/interface`` (dict keyed by name) to name -> fields."""
    res = payload.get("results", {})
    if isinstance(res, list):
        return {i.get("name"): i for i in res}
    return {k: dict(v, name=v.get("name", k)) for k, v in res.items()}


def parse_vlan_interfaces(payload: dict[str, Any]) -> dict[int, str]:
    """``cmdb/system/interface`` -> {vlanid: interface name} for VLAN sub-interfaces."""
    out: dict[int, str] = {}
    for i in payload.get("results", []):
        vid = i.get("vlanid")
        if vid and i.get("type") == "vlan":
            out[int(vid)] = i["name"]
    return out


def count_leases_by_interface(payload: dict[str, Any]) -> Counter[str]:
    c: Counter[str] = Counter()
    for lease in payload.get("results", []):
        if lease.get("status", "leased") in {"leased", "reserved", "bound"} or "status" not in lease:
            c[lease.get("interface", "?")] += 1
    return c


def count_wifi_by_ap(payload: dict[str, Any]) -> Counter[str]:
    c: Counter[str] = Counter()
    for client in payload.get("results", []):
        c[client.get("wtp_name") or client.get("ap") or client.get("wtp_id") or "?"] += 1
    return c


def parse_aps(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for ap in payload.get("results", []):
        status = str(ap.get("status") or ap.get("state") or "").lower()
        out.append({"name": ap.get("name") or ap.get("wtp_id") or "?", "online": status in {"connected", "online"}})
    return out


class FortiGateCollector(Collector):
    type = "fortigate"
    icon = "firewall"
    default_title = "FortiGate"
    default_description = "Security gateway, WAN edge, DHCP, and wireless infrastructure."

    def __init__(self, cfg: dict[str, Any], history_points: int = 24) -> None:
        super().__init__(cfg, history_points)
        self.base = cfg["base_url"].rstrip("/")
        self.wan = cfg.get("wan_interface", "wan1")
        self.rates = RateTracker()
        self._client: httpx.AsyncClient | None = None
        self.wide = bool(cfg.get("wide", True))

    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = make_client(self.cfg, self.timeout,
                                       headers={"Authorization": f"Bearer {self.cfg['token']}"})
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = await self.client().get(f"{self.base}{path}", params=params)
        resp.raise_for_status()
        return resp.json()

    async def _optional(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Some endpoints don't exist on every model (e.g. no FortiAP support)."""
        try:
            return await self._get(path, params)
        except httpx.HTTPStatusError:
            return {}

    async def _public_ip(self) -> str | None:
        url = self.cfg.get("public_ip_url", "https://api.ipify.org")
        if not url:
            return None
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(url)
                return r.text.strip() if r.status_code == 200 else None
        except httpx.HTTPError:
            return None

    async def poll(self) -> Card:
        status = (await self._get("/api/v2/monitor/system/status")).get("results", {})
        cpu, mem = parse_resource_usage(await self._get("/api/v2/monitor/system/resource/usage",
                                                        {"scope": "global", "interval": "1-min"}))
        ifaces = parse_interfaces(await self._get("/api/v2/monitor/system/interface",
                                                  {"include_vlan": "true", "include_aggregate": "true"}))
        vlans = parse_vlan_interfaces(await self._optional("/api/v2/cmdb/system/interface"))
        leases = count_leases_by_interface(await self._optional("/api/v2/monitor/system/dhcp"))
        wifi = count_wifi_by_ap(await self._optional("/api/v2/monitor/wifi/client"))
        aps = parse_aps(await self._optional("/api/v2/monitor/wifi/managed_ap"))
        public_ip = await self._public_ip()

        wan = ifaces.get(self.wan, {})
        wan_up = str(wan.get("link", "")).lower() in {"up", "true", "1"} or wan.get("link") is True
        rx = self.rates.update("wan_rx", wan.get("rx_bytes"))
        tx = self.rates.update("wan_tx", wan.get("tx_bytes"))

        card = self.new_card()
        card.status_label = "FIREWALL ONLINE"
        card.status_level = "ok" if wan_up else "warn"
        card.hero_label = "Firewall health"
        card.hero_value = fmt_pct(cpu, 0) + " CPU" if cpu is not None else "—"
        card.hero_history = self.push_history(cpu)
        card.stats = [
            Stat("Memory", fmt_pct(mem, 0), level="warn" if (mem or 0) > 80 else None),
            Stat("WAN / Internet", "ONLINE" if wan_up else "DOWN", level="ok" if wan_up else "crit"),
            Stat("Public IP", public_ip or "—"),
            Stat("WAN IP", (wan.get("ip") or "—").split(" ")[0]),
            Stat("WAN throughput", f"↑ {fmt_mbps(tx)} / ↓ {fmt_mbps(rx)}"),
            Stat("DHCP clients", fmt_int(sum(leases.values()))),
            Stat("Wi-Fi clients", fmt_int(sum(wifi.values()))),
            Stat("Firmware", str(status.get("version", "—")), status.get("hostname")),
        ]

        names = {int(k): v for k, v in (self.cfg.get("vlan_names") or {}).items()}
        hidden = {int(v) for v in (self.cfg.get("hide_vlans") or [])}
        rows = []
        for vid in sorted(vlans):
            if vid in hidden:
                continue
            iface = vlans[vid]
            rows.append([vid, names.get(vid, iface), leases.get(iface, 0)])
        if rows:
            card.tables.append(Table("VLANs", ["VLAN", "Name", "Clients"], rows))

        if aps or wifi:
            ap_rows = [[ap["name"], wifi.get(ap["name"], 0)] for ap in aps] or \
                      [[name, n] for name, n in wifi.most_common()]
            levels = [("ok" if ap["online"] else "crit") for ap in aps] if aps else None
            card.tables.append(Table("Access points", ["AP", "Clients"], ap_rows, levels))
        return card
