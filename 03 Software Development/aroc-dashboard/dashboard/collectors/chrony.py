# AROC Dashboard — chrony time-server collector.  GPLv3, see dashboard/__init__.py.
"""chrony has no HTTP API, so this collector runs ``chronyc`` either locally
(when the dashboard runs on the time server itself) or over SSH.

``chronyc -c tracking`` prints one CSV line::

    refid_hex,refid_name_or_ip,stratum,ref_time,sys_offset,last_offset,rms_offset,
    freq_ppm,resid_freq,skew,root_delay,root_dispersion,update_interval,leap_status

``chronyc -c sources`` prints one CSV line per source::

    mode,state,name,stratum,poll,reach,lastrx,last_sample,last_sample_err,...

Config::

    - id: ntp
      type: chrony
      title: Time Server
      mode: ssh                      # or "local"
      host: 192.168.1.10
      ssh_user: pi
      ssh_key: /home/user/.ssh/id_ed25519   # or ssh_password: ${NTP_SSH_PASSWORD}
      known_hosts: null              # null = don't verify host key (LAN only)
"""
from __future__ import annotations

import asyncio
import shlex
from typing import Any

from .base import Card, Collector, Stat

LEAP_OK = {"normal"}


def parse_tracking(line: str) -> dict[str, Any]:
    f = line.strip().split(",")
    if len(f) < 14:
        raise ValueError(f"unexpected chronyc tracking output: {line!r}")
    return {
        "refid": f[0],
        "ref_name": f[1],
        "stratum": int(f[2]),
        "offset_s": float(f[4]),
        "rms_offset_s": float(f[6]),
        "freq_ppm": float(f[7]),
        "root_delay_s": float(f[10]),
        "root_dispersion_s": float(f[11]),
        "update_interval_s": float(f[12]),
        "leap": f[13].strip().lower(),
    }


def parse_sources(text: str) -> list[dict[str, Any]]:
    out = []
    for line in text.splitlines():
        f = line.strip().split(",")
        if len(f) < 8:
            continue
        out.append({"mode": f[0], "state": f[1], "name": f[2], "stratum": int(f[3] or 0),
                    "reach": int(f[5] or 0), "selected": f[1] == "*"})
    return out


def fmt_offset(seconds: float) -> str:
    us = seconds * 1e6
    if abs(us) < 1000:
        return f"{us:+.0f} µs"
    return f"{seconds * 1e3:+.2f} ms"


class ChronyCollector(Collector):
    type = "chrony"
    icon = "clock"
    default_title = "Time Server"
    default_description = "Chrony synchronization and upstream time source."

    async def _run(self, cmd: str) -> str:
        mode = self.cfg.get("mode", "local")
        if mode == "local":
            proc = await asyncio.create_subprocess_exec(*shlex.split(cmd), stdout=asyncio.subprocess.PIPE,
                                                        stderr=asyncio.subprocess.PIPE)
            out, err = await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(err.decode().strip() or f"{cmd} exited {proc.returncode}")
            return out.decode()
        if mode == "ssh":
            import asyncssh  # imported lazily so local mode has no SSH dependency

            kw: dict[str, Any] = {"username": self.cfg.get("ssh_user"), "known_hosts": self.cfg.get("known_hosts")}
            if self.cfg.get("ssh_key"):
                kw["client_keys"] = [self.cfg["ssh_key"]]
            if self.cfg.get("ssh_password"):
                kw["password"] = self.cfg["ssh_password"]
            async with asyncssh.connect(self.cfg["host"], port=int(self.cfg.get("ssh_port", 22)), **kw) as conn:
                result = await conn.run(cmd, check=True)
                return str(result.stdout)
        raise ValueError(f"chrony mode must be 'local' or 'ssh', not {mode!r}")

    async def poll(self) -> Card:
        chronyc = self.cfg.get("chronyc", "chronyc")
        tracking = parse_tracking(await self._run(f"{chronyc} -c tracking"))
        sources = parse_sources(await self._run(f"{chronyc} -c sources"))
        selected = next((s for s in sources if s["selected"]), None)
        synced = tracking["leap"] in LEAP_OK and tracking["stratum"] < 16

        card = self.new_card()
        card.status_label = "SERVICE RUNNING" if synced else "NOT SYNCHRONIZED"
        card.status_level = "ok" if synced else "crit"
        card.hero_label = "Sync status"
        card.hero_value = "SYNCED" if synced else "UNSYNCED"
        card.hero_history = self.push_history(abs(tracking["offset_s"]) * 1e6)  # µs offset trend
        source_name = selected["name"] if selected else tracking["ref_name"]
        card.stats = [
            Stat("Stratum", str(tracking["stratum"]), f"leap: {tracking['leap']}"),
            Stat("Offset", fmt_offset(tracking["offset_s"]), f"rms {fmt_offset(tracking['rms_offset_s'])}"),
            Stat("Source", f"{tracking['refid']}", source_name),
            Stat("Sources reachable", f"{sum(1 for s in sources if s['reach'] > 0)} / {len(sources)}"),
        ]
        return card
