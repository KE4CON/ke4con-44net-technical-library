# AROC Dashboard — HP iLO (Redfish) collector.  GPLv3, see dashboard/__init__.py.
"""HPE iLO 4 / iLO 5 / iLO 6 via the Redfish API with basic auth.

* ``/redfish/v1/Systems/1``        power state, health, model, host name
* ``/redfish/v1/Chassis/1/Thermal`` temperatures and fans
* ``/redfish/v1/Chassis/1/Power``   power draw in watts

iLO 4 uses ``CurrentReading`` for fan speed; iLO 5+ uses ``Reading``.  Both are
handled.  Works with any other Redfish BMC (iDRAC, Supermicro) for the basics.

Config::

    - id: ilo
      type: ilo
      title: HP iLO
      url: https://ilo.local
      base_url: https://ilo.local
      username: ${ILO_USER}
      password: ${ILO_PASSWORD}
      verify_tls: false
"""
from __future__ import annotations

from typing import Any

import httpx

from .base import Card, Collector, Stat
from .http import make_client

HEALTH_LEVEL = {"ok": "ok", "warning": "warn", "critical": "crit"}


def parse_system(payload: dict[str, Any]) -> dict[str, Any]:
    status = payload.get("Status", {})
    return {
        "power": payload.get("PowerState", "?"),
        "health": str(status.get("Health") or status.get("HealthRollup") or "Unknown"),
        "model": payload.get("Model", ""),
        "hostname": payload.get("HostName", ""),
        "post": payload.get("Oem", {}).get("Hp", payload.get("Oem", {}).get("Hpe", {})).get("PostState"),
    }


def parse_thermal(payload: dict[str, Any]) -> dict[str, Any]:
    temps = [(t.get("Name", "?"), t.get("ReadingCelsius"))
             for t in payload.get("Temperatures", []) if t.get("ReadingCelsius") is not None]
    fans = []
    for f in payload.get("Fans", []):
        reading = f.get("Reading", f.get("CurrentReading"))
        if reading is not None:
            fans.append((f.get("Name") or f.get("FanName") or "?", reading, f.get("ReadingUnits") or f.get("Units") or "%"))

    def pick(substr: str) -> float | None:
        vals = [v for n, v in temps if substr.lower() in n.lower()]
        return max(vals) if vals else None

    return {"cpu_c": pick("cpu"), "inlet_c": pick("inlet") or pick("ambient"), "max_c": max((v for _, v in temps), default=None),
            "fan_pct": max((r for _, r, u in fans if "%" in u or "percent" in u.lower()), default=None),
            "fan_count": len(fans)}


def parse_power(payload: dict[str, Any]) -> float | None:
    pc = payload.get("PowerControl", [])
    return float(pc[0]["PowerConsumedWatts"]) if pc and pc[0].get("PowerConsumedWatts") is not None else None


class IloCollector(Collector):
    type = "ilo"
    icon = "chip"
    default_title = "HP iLO"
    default_description = "Out-of-band server management, power, and thermals."

    def __init__(self, cfg: dict[str, Any], history_points: int = 24) -> None:
        super().__init__(cfg, history_points)
        self.base = cfg["base_url"].rstrip("/")
        self.system_id = cfg.get("system_id", "1")
        self._client: httpx.AsyncClient | None = None

    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = make_client(self.cfg, self.timeout, auth=(self.cfg["username"], self.cfg["password"]))
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def _get(self, path: str) -> dict[str, Any]:
        resp = await self.client().get(f"{self.base}{path}")
        resp.raise_for_status()
        return resp.json()

    async def poll(self) -> Card:
        sid = self.system_id
        system = parse_system(await self._get(f"/redfish/v1/Systems/{sid}"))
        thermal = parse_thermal(await self._get(f"/redfish/v1/Chassis/{sid}/Thermal"))
        watts = parse_power(await self._get(f"/redfish/v1/Chassis/{sid}/Power"))

        card = self.new_card()
        on = system["power"].lower() == "on"
        card.status_label = "POWER ON" if on else system["power"].upper()
        card.status_level = HEALTH_LEVEL.get(system["health"].lower(), "warn") if on else "warn"
        card.hero_label = "Power draw"
        card.hero_value = f"{watts:.0f} W" if watts is not None else "—"
        card.hero_history = self.push_history(watts)
        card.stats = [
            Stat("Health", system["health"].upper(), system["model"], HEALTH_LEVEL.get(system["health"].lower())),
            Stat("Host", system["hostname"] or "—", system["post"]),
            Stat("CPU temp", f"{thermal['cpu_c']:.0f} °C" if thermal["cpu_c"] is not None else "—",
                 level="warn" if (thermal["cpu_c"] or 0) > 80 else None),
            Stat("Inlet temp", f"{thermal['inlet_c']:.0f} °C" if thermal["inlet_c"] is not None else "—"),
            Stat("Fans", f"{thermal['fan_pct']:.0f}%" if thermal["fan_pct"] is not None else "—",
                 f"{thermal['fan_count']} fans"),
        ]
        return card
