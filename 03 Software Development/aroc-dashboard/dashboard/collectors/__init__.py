# AROC Dashboard — collector registry.  GPLv3, see dashboard/__init__.py.
"""Map ``type:`` strings in ``config.yaml`` to collector classes.

Collectors with heavy optional dependencies (SNMP) are imported lazily so a
missing package only breaks the service that needs it.
"""
from __future__ import annotations

import importlib
from typing import Any

from .base import Card, Collector

_REGISTRY: dict[str, str] = {
    "demo": "dashboard.collectors.demo:DemoCollector",
    "link": "dashboard.collectors.link:LinkCollector",
    "pihole": "dashboard.collectors.pihole:PiholeCollector",
    "wazuh": "dashboard.collectors.wazuh:WazuhCollector",
    "chrony": "dashboard.collectors.chrony:ChronyCollector",
    "fortigate": "dashboard.collectors.fortigate:FortiGateCollector",
    "snmp_switch": "dashboard.collectors.snmp_switch:SnmpSwitchCollector",
    "proxmox": "dashboard.collectors.proxmox:ProxmoxCollector",
    "plex": "dashboard.collectors.plex:PlexCollector",
    "ilo": "dashboard.collectors.ilo:IloCollector",
}


def available_types() -> list[str]:
    return sorted(_REGISTRY)


def create_collector(cfg: dict[str, Any], history_points: int) -> Collector:
    kind = cfg["type"]
    if kind not in _REGISTRY:
        raise ValueError(f"service {cfg.get('id')!r}: unknown type {kind!r}; known: {', '.join(available_types())}")
    module_name, _, class_name = _REGISTRY[kind].partition(":")
    cls = getattr(importlib.import_module(module_name), class_name)
    return cls(cfg, history_points)


__all__ = ["Card", "Collector", "available_types", "create_collector"]
