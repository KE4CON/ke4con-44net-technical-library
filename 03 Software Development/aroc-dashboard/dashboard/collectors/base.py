# AROC Dashboard — collector base classes.  GPLv3, see dashboard/__init__.py.
"""Every device/service on the dashboard is a *collector*.

A collector knows how to poll one kind of thing (a Pi-hole, a FortiGate, an SNMP
switch...) and turns whatever it gets back into a single, uniform ``Card`` that
the browser renders without knowing anything about the device.  Adding a new
device type therefore never touches the frontend.

Card model (what ``/api/status`` returns for each service)::

    {
      "id": "pihole",              # from config
      "type": "pihole",            # collector type
      "title": "Pi-hole",
      "icon": "dns",               # frontend icon key
      "description": "...",        # one line under the title
      "url": "http://...",         # target of the "Open dashboard" button (optional)
      "wide": false,               # span two columns
      "status": {"label": "BLOCKING ACTIVE", "level": "ok"},   # ok|warn|crit|unknown
      "hero": {"label": "Queries today", "value": "16,265", "history": [..numbers..]},
      "stats": [{"label": "Blocked", "value": "740", "sub": "4.5%", "level": "crit"}],
      "tables": [{"title": "VLAN", "columns": ["VLAN","Name","Clients"], "rows": [[..],..]}],
      "items": [{"label": "Aetherion", "level": "ok"}],
      "error": null,               # string when the last poll failed
      "updated": 1695324000.0      # unix time of last successful poll
    }
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Iterable

log = logging.getLogger("aroc.collector")

Level = str  # "ok" | "warn" | "crit" | "unknown"


@dataclass
class Stat:
    label: str
    value: str
    sub: str | None = None
    level: Level | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"label": self.label, "value": self.value}
        if self.sub is not None:
            d["sub"] = self.sub
        if self.level is not None:
            d["level"] = self.level
        return d


@dataclass
class Table:
    title: str
    columns: list[str]
    rows: list[list[Any]]
    levels: list[Level | None] | None = None  # optional per-row status dot

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"title": self.title, "columns": self.columns, "rows": self.rows}
        if self.levels is not None:
            d["levels"] = self.levels
        return d


@dataclass
class Card:
    id: str
    type: str
    title: str
    icon: str = "generic"
    description: str = ""
    url: str | None = None
    wide: bool = False
    status_label: str = "UNKNOWN"
    status_level: Level = "unknown"
    hero_label: str | None = None
    hero_value: str | None = None
    hero_history: list[float] = field(default_factory=list)
    stats: list[Stat] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    items: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    updated: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "icon": self.icon,
            "description": self.description,
            "url": self.url,
            "wide": self.wide,
            "status": {"label": self.status_label, "level": self.status_level},
            "hero": (
                {"label": self.hero_label, "value": self.hero_value, "history": self.hero_history}
                if self.hero_label is not None
                else None
            ),
            "stats": [s.to_dict() for s in self.stats],
            "tables": [t.to_dict() for t in self.tables],
            "items": self.items,
            "error": self.error,
            "updated": self.updated,
        }


def fmt_int(n: float | int | None) -> str:
    if n is None:
        return "—"
    return f"{int(round(n)):,}"


def fmt_pct(n: float | None, digits: int = 1) -> str:
    if n is None:
        return "—"
    return f"{n:.{digits}f}%"


def fmt_mbps(bps: float | None) -> str:
    """Format a bits-per-second rate as Mbps (or Kbps when tiny)."""
    if bps is None:
        return "—"
    mbps = bps / 1_000_000
    if mbps >= 100:
        return f"{mbps:.0f} Mbps"
    if mbps >= 0.1 or mbps == 0:
        return f"{mbps:.1f} Mbps"
    return f"{bps / 1000:.0f} Kbps"


def fmt_uptime(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    s = int(seconds)
    d, s = divmod(s, 86400)
    h, m = divmod(s // 60, 60)
    if d:
        return f"{d}d {h:02d}h"
    return f"{h}h {m:02d}m"


class RateTracker:
    """Turn monotonically increasing byte counters into bits-per-second rates.

    Keeps the previous (timestamp, value) per key and returns the delta rate on
    the next update, or ``None`` for the first sample / counter wrap.
    """

    def __init__(self) -> None:
        self._last: dict[str, tuple[float, float]] = {}

    def update(self, key: str, counter_bytes: float | None, now: float | None = None) -> float | None:
        if counter_bytes is None:
            return None
        now = time.monotonic() if now is None else now
        prev = self._last.get(key)
        self._last[key] = (now, counter_bytes)
        if prev is None:
            return None
        dt = now - prev[0]
        delta = counter_bytes - prev[1]
        if dt <= 0 or delta < 0:  # counter wrapped or reset
            return None
        return delta * 8 / dt


class Collector:
    """Base class.  Subclasses implement :meth:`poll` and fill in the card."""

    type: str = "generic"
    icon: str = "generic"
    default_title: str = "Service"
    default_description: str = ""

    def __init__(self, cfg: dict[str, Any], history_points: int = 24) -> None:
        self.cfg = cfg
        self.id: str = cfg["id"]
        self.title: str = cfg.get("title", self.default_title)
        self.description: str = cfg.get("description", self.default_description)
        self.url: str | None = cfg.get("url")
        self.wide: bool = bool(cfg.get("wide", False))
        self.interval: float = float(cfg.get("interval", 30))
        self.timeout: float = float(cfg.get("timeout", 10))
        self.history: deque[float] = deque(maxlen=history_points)
        self.card: Card = self.new_card()
        self._lock = asyncio.Lock()

    # -- helpers ---------------------------------------------------------------
    def new_card(self) -> Card:
        return Card(
            id=self.id,
            type=self.type,
            title=self.title,
            icon=self.cfg.get("icon", self.icon),
            description=self.description,
            url=self.url,
            wide=self.wide,
        )

    def push_history(self, value: float | None) -> list[float]:
        if value is not None:
            self.history.append(float(value))
        return list(self.history)

    # -- lifecycle -------------------------------------------------------------
    async def poll(self) -> Card:  # pragma: no cover - abstract
        raise NotImplementedError

    async def refresh(self) -> Card:
        """Poll once; on failure keep the last good card but mark it errored."""
        async with self._lock:
            try:
                card = await asyncio.wait_for(self.poll(), timeout=self.timeout + 5)
                card.updated = time.time()
                card.error = None
                self.card = card
            except Exception as exc:  # noqa: BLE001 - any failure is a card error
                log.warning("%s: poll failed: %s", self.id, exc)
                self.card.error = f"{type(exc).__name__}: {exc}"
                self.card.status_label = "UNREACHABLE"
                self.card.status_level = "crit"
            return self.card

    async def close(self) -> None:
        """Release any long-lived connections."""


def first(iterable: Iterable[Any], default: Any = None) -> Any:
    for item in iterable:
        return item
    return default
