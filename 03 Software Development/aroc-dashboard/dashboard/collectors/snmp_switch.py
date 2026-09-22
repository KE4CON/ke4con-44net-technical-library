# AROC Dashboard — SNMP managed-switch collector (Cisco SG300 etc.).  GPLv3.
"""Any managed switch that speaks SNMP (the Cisco SG300 has no REST API).

Standard MIBs only, so this also works for other vendors:

* SNMPv2-MIB      sysUpTime, sysName
* IF-MIB          ifName/ifDescr, ifOperStatus, ifHighSpeed, ifHCIn/OutOctets
* POWER-ETHERNET-MIB  pethPsePortDetectionStatus (3 = deliveringPower)

Ports are addressed by *name* (matched case-insensitively against ifName and
ifDescr, e.g. ``gi28`` or ``GigabitEthernet28``); the collector walks the table
once, caches the ifIndex mapping, then does cheap GETs on every poll.

Config::

    - id: sg300
      type: snmp_switch
      title: Cisco SG300
      url: http://192.168.1.2
      host: 192.168.1.2
      community: ${SNMP_COMMUNITY}       # v2c
      # or SNMPv3:
      # v3: {user: monitor, auth_key: ${SNMP_AUTH}, auth_proto: sha, priv_key: ${SNMP_PRIV}, priv_proto: aes}
      uplink: gi28
      poe_ports: [gi1, gi2, gi3, gi4]
      traffic_ports:                      # any ports/VLAN interfaces to graph
        - {name: "vlan 20", label: Trusted}
        - {name: "vlan 30", label: Servers}
"""
from __future__ import annotations

import re
from typing import Any

from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData, ContextData, ObjectIdentity, ObjectType, SnmpEngine, UdpTransportTarget,
    UsmUserData, bulk_walk_cmd, get_cmd, usmAesCfb128Protocol, usmDESPrivProtocol,
    usmHMACMD5AuthProtocol, usmHMACSHAAuthProtocol, usmHMAC192SHA256AuthProtocol,
)

from .base import Card, Collector, RateTracker, Stat, Table, fmt_mbps, fmt_uptime

OID_SYS_UPTIME = "1.3.6.1.2.1.1.3.0"
OID_SYS_NAME = "1.3.6.1.2.1.1.5.0"
OID_IF_DESCR = "1.3.6.1.2.1.2.2.1.2"
OID_IF_OPER = "1.3.6.1.2.1.2.2.1.8"
OID_IF_NAME = "1.3.6.1.2.1.31.1.1.1.1"
OID_IF_HC_IN = "1.3.6.1.2.1.31.1.1.1.6"
OID_IF_HC_OUT = "1.3.6.1.2.1.31.1.1.1.10"
OID_IF_HIGHSPEED = "1.3.6.1.2.1.31.1.1.1.15"
OID_POE_STATUS = "1.3.6.1.2.1.105.1.1.1.6"  # pethPsePortDetectionStatus.<group>.<port>

POE_STATES = {1: "disabled", 2: "searching", 3: "delivering", 4: "fault", 5: "test", 6: "otherFault"}
AUTH_PROTOS = {"md5": usmHMACMD5AuthProtocol, "sha": usmHMACSHAAuthProtocol, "sha256": usmHMAC192SHA256AuthProtocol}
PRIV_PROTOS = {"des": usmDESPrivProtocol, "aes": usmAesCfb128Protocol}


def norm(name: str) -> str:
    """``GigabitEthernet28`` / ``gi28`` / ``gi 28`` -> ``gi28``; ``vlan 20`` -> ``vlan20``."""
    n = re.sub(r"\s+", "", name.strip().lower())
    n = n.replace("gigabitethernet", "gi").replace("fastethernet", "fa").replace("tengigabitethernet", "te")
    return n


def port_number(name: str) -> int | None:
    m = re.search(r"(\d+)$", norm(name))
    return int(m.group(1)) if m else None


def build_index(names: dict[int, str], descrs: dict[int, str]) -> dict[str, int]:
    """Map every normalised ifName/ifDescr to its ifIndex."""
    idx: dict[str, int] = {}
    for i, d in descrs.items():
        idx.setdefault(norm(d), i)
    for i, n in names.items():
        idx.setdefault(norm(n), i)
    return idx


class SnmpSwitchCollector(Collector):
    type = "snmp_switch"
    icon = "switch"
    default_title = "Switch"
    default_description = "Core switch, PoE devices, uplink, and traffic."

    def __init__(self, cfg: dict[str, Any], history_points: int = 24) -> None:
        super().__init__(cfg, history_points)
        self.engine = SnmpEngine()
        self.rates = RateTracker()
        self._ifindex: dict[str, int] | None = None
        self._poe_index: dict[int, str] | None = None  # port number -> oid suffix

    # -- SNMP plumbing ---------------------------------------------------------
    def _auth(self) -> CommunityData | UsmUserData:
        v3 = self.cfg.get("v3")
        if v3:
            kw: dict[str, Any] = {}
            if v3.get("auth_key"):
                kw["authKey"] = v3["auth_key"]
                kw["authProtocol"] = AUTH_PROTOS[v3.get("auth_proto", "sha").lower()]
            if v3.get("priv_key"):
                kw["privKey"] = v3["priv_key"]
                kw["privProtocol"] = PRIV_PROTOS[v3.get("priv_proto", "aes").lower()]
            return UsmUserData(v3["user"], **kw)
        return CommunityData(self.cfg.get("community", "public"), mpModel=1)

    async def _target(self) -> UdpTransportTarget:
        return await UdpTransportTarget.create((self.cfg["host"], int(self.cfg.get("port", 161))),
                                               timeout=self.timeout, retries=1)

    async def _walk(self, oid: str) -> dict[str, Any]:
        out: dict[str, Any] = {}
        target = await self._target()
        async for err_ind, err_st, _, binds in bulk_walk_cmd(self.engine, self._auth(), target, ContextData(),
                                                             0, 25, ObjectType(ObjectIdentity(oid)),
                                                             lexicographicMode=False):
            if err_ind:
                raise RuntimeError(str(err_ind))
            if err_st:
                raise RuntimeError(err_st.prettyPrint())
            for name, val in binds:
                out[str(name)[len(oid) + 1:]] = val
        return out

    async def _get(self, *oids: str) -> list[Any]:
        target = await self._target()
        err_ind, err_st, _, binds = await get_cmd(self.engine, self._auth(), target, ContextData(),
                                                  *[ObjectType(ObjectIdentity(o)) for o in oids])
        if err_ind:
            raise RuntimeError(str(err_ind))
        if err_st:
            raise RuntimeError(err_st.prettyPrint())
        return [v for _, v in binds]

    async def _discover(self) -> None:
        names = {int(k): str(v) for k, v in (await self._walk(OID_IF_NAME)).items()}
        descrs = {int(k): str(v) for k, v in (await self._walk(OID_IF_DESCR)).items()}
        self._ifindex = build_index(names, descrs)
        poe: dict[int, str] = {}
        try:
            for suffix in await self._walk(OID_POE_STATUS):
                port = int(suffix.split(".")[-1])
                poe.setdefault(port, suffix)
        except RuntimeError:
            pass  # switch has no PoE MIB
        self._poe_index = poe

    def _ifidx(self, name: str) -> int | None:
        assert self._ifindex is not None
        return self._ifindex.get(norm(name))

    # -- poll ------------------------------------------------------------------
    async def poll(self) -> Card:
        if self._ifindex is None:
            await self._discover()
        assert self._ifindex is not None and self._poe_index is not None

        uptime_ticks, sysname = await self._get(OID_SYS_UPTIME, OID_SYS_NAME)
        uptime_s = int(uptime_ticks) / 100

        card = self.new_card()
        card.status_label = "SWITCH ONLINE"
        card.status_level = "ok"
        card.hero_label = "Uptime"
        card.hero_value = fmt_uptime(uptime_s)

        # Uplink
        uplink = self.cfg.get("uplink")
        up_rx = up_tx = None
        if uplink and (i := self._ifidx(uplink)) is not None:
            oper, speed, hc_in, hc_out = await self._get(f"{OID_IF_OPER}.{i}", f"{OID_IF_HIGHSPEED}.{i}",
                                                         f"{OID_IF_HC_IN}.{i}", f"{OID_IF_HC_OUT}.{i}")
            is_up = int(oper) == 1
            up_rx = self.rates.update(f"rx{i}", int(hc_in))
            up_tx = self.rates.update(f"tx{i}", int(hc_out))
            card.stats.append(Stat(f"Uplink — {uplink.upper()}", f"{'UP' if is_up else 'DOWN'} • {int(speed)} Mbps",
                                   f"↓ {fmt_mbps(up_rx)}  ↑ {fmt_mbps(up_tx)}", "ok" if is_up else "crit"))
            if not is_up:
                card.status_label, card.status_level = "UPLINK DOWN", "crit"
        card.hero_history = self.push_history((up_rx or 0) / 1e6 if up_rx is not None else None)
        card.hero_label = "Uplink Mbps (down)" if up_rx is not None else "Uptime"
        if up_rx is not None:
            card.hero_value = fmt_mbps(up_rx)
            card.stats.insert(0, Stat("Uptime", fmt_uptime(uptime_s), str(sysname)))

        # PoE
        poe_ports = [str(p) for p in self.cfg.get("poe_ports", [])]
        if poe_ports and self._poe_index:
            oids, labels = [], []
            for p in poe_ports:
                n = port_number(p)
                if n in self._poe_index:
                    oids.append(f"{OID_POE_STATUS}.{self._poe_index[n]}")
                    labels.append(p.upper())
            if oids:
                states = [int(v) for v in await self._get(*oids)]
                active = sum(1 for s in states if s == 3)
                card.stats.append(Stat("PoE", f"{active} / {len(states)} active",
                                       level="ok" if active == len(states) else ("warn" if active else "crit")))
                card.items = [{"label": lbl, "level": "ok" if s == 3 else ("crit" if s in (4, 6) else "unknown"),
                               "title": POE_STATES.get(s, str(s))} for lbl, s in zip(labels, states)]

        # Per-port / per-VLAN traffic table
        rows, levels = [], []
        for entry in self.cfg.get("traffic_ports", []):
            name = entry["name"] if isinstance(entry, dict) else str(entry)
            label = entry.get("label", name) if isinstance(entry, dict) else name
            i = self._ifidx(name)
            if i is None:
                rows.append([label, "not found", ""])
                levels.append("unknown")
                continue
            oper, hc_in, hc_out = await self._get(f"{OID_IF_OPER}.{i}", f"{OID_IF_HC_IN}.{i}", f"{OID_IF_HC_OUT}.{i}")
            rx = self.rates.update(f"rx{i}", int(hc_in))
            tx = self.rates.update(f"tx{i}", int(hc_out))
            rows.append([label, fmt_mbps(rx), fmt_mbps(tx)])
            levels.append("ok" if int(oper) == 1 else "crit")
        if rows:
            card.tables.append(Table("Traffic", ["Interface", "↓ Down", "↑ Up"], rows, levels))
        return card
