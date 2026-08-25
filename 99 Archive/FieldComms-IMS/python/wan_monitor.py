#!/usr/bin/env python3
"""
wan_monitor.py — WAN Status Monitor Service
Runs on the FieldComms Pi (192.168.50.1)
Polls the ASUS RT-BE58 Go router API and InstyConnect modem
every 30 seconds to determine active WAN source and connection quality.
Writes results to /opt/fieldcomms/data/wan_status.json
for the health monitor and wan-status.html dashboard page.

ASUS RT-BE58 Go exposes a basic HTTP API at its admin interface.
InstyConnect modem admin is at http://10.1.1.1 (accessible when
InstyConnect WAN is active — the modem is upstream of the router).
"""

import json
import socket
import subprocess
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_FILE  = Path("/opt/fieldcomms/data/wan_status.json")
POLL_INTERVAL = 30   # seconds

# Known WAN check targets
PING_TARGETS = [
    ("1.1.1.1",     "Cloudflare DNS"),
    ("8.8.8.8",     "Google DNS"),
    ("44.0.0.1",    "AMPRNet gateway"),
]

# InstyConnect modem — only reachable when cellular WAN is active
INSTY_ADMIN = "http://10.1.1.1"

# ASUS router admin (local — always reachable)
ASUS_ADMIN = "http://192.168.50.254"


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ping_test(host, count=2, timeout=3):
    """Return (success, avg_ms)."""
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), "-W", str(timeout), host],
            capture_output=True, text=True, timeout=timeout * count + 2
        )
        if result.returncode == 0:
            # Parse avg from: rtt min/avg/max/mdev = 10.1/11.2/12.3/0.5 ms
            for line in result.stdout.splitlines():
                if "avg" in line and "/" in line:
                    try:
                        avg = float(line.split("/")[4])
                        return True, round(avg, 1)
                    except (IndexError, ValueError):
                        pass
            return True, None
        return False, None
    except Exception:
        return False, None


def http_test(url, timeout=5):
    """Return (reachable, response_ms)."""
    try:
        start = time.time()
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            resp.read(512)
            ms = round((time.time() - start) * 1000, 1)
            return True, ms
    except Exception:
        return False, None


def detect_active_wan():
    """
    Determine which WAN source is currently active by testing
    internet reachability and checking ASUS WAN status.
    Returns: 'cellular', 'satellite', 'site', or 'none'
    """
    # Try to reach internet
    internet_ok, latency = ping_test("1.1.1.1")

    if not internet_ok:
        return "none", None

    # Check if InstyConnect modem is reachable (upstream of router)
    # It's only reachable when cellular WAN is active
    insty_ok, _ = http_test(INSTY_ADMIN + "/", timeout=3)
    if insty_ok:
        return "cellular", latency

    # Starlink admin is at 192.168.100.1 — only reachable via Starlink network
    # When Starlink is active via USB WAN, the 192.168.100.x subnet is accessible
    sl_ok, _ = ping_test("192.168.100.1", count=1, timeout=2)
    if sl_ok:
        return "satellite", latency

    # Internet is up but neither cellular nor satellite admin is reachable
    # Could be site Ethernet or WISP
    return "site", latency


def get_insty_status():
    """
    Poll InstyConnect modem admin for signal and carrier info.
    Returns dict or None if modem is not reachable.
    The InstyConnect modem serves a basic web UI at http://10.1.1.1
    We parse what we can from the status page.
    """
    try:
        req = urllib.request.Request(
            INSTY_ADMIN + "/",
            headers={"User-Agent": "FieldComms/1.0"}
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            body = resp.read(8192).decode(errors="ignore")

        # Parse signal information from the InstyConnect status page
        # The exact parsing depends on InstyConnect firmware version
        # These are best-effort extractions
        result = {
            "connected": True,
            "antenna": "Drum",   # Updated manually in wan_status.json if Switchblade is in use
        }

        # Look for carrier name
        for carrier in ["T-Mobile", "Verizon", "AT&T"]:
            if carrier.lower() in body.lower():
                result["carrier"] = carrier
                break
        else:
            result["carrier"] = "Unknown"

        # Look for technology indicators
        for tech in ["5G", "LTE", "4G", "3G"]:
            if tech in body:
                result["technology"] = tech
                break
        else:
            result["technology"] = "Unknown"

        # Signal strength — look for RSSI or bars indication
        import re
        rssi_match = re.search(r"rssi[\":\s]+(-?\d+)", body, re.IGNORECASE)
        if rssi_match:
            rssi = int(rssi_match.group(1))
            result["signal_dbm"] = rssi
            # Convert to descriptive strength
            if rssi >= -70:
                result["signal_strength"] = f"Excellent ({rssi} dBm)"
            elif rssi >= -85:
                result["signal_strength"] = f"Good ({rssi} dBm)"
            elif rssi >= -100:
                result["signal_strength"] = f"Fair ({rssi} dBm)"
            else:
                result["signal_strength"] = f"Poor ({rssi} dBm)"
        else:
            result["signal_strength"] = "Unknown"

        return result

    except urllib.error.URLError:
        return None
    except Exception:
        return None


def get_starlink_status():
    """
    Poll Starlink dish status via its gRPC/HTTP API.
    Starlink exposes a status endpoint at http://192.168.100.1:9201/
    when connected via USB WAN (the dish subnet is 192.168.100.x).
    Returns dict or minimal info if not reachable.
    """
    result = {"connected": False, "dish_present": False}

    # Quick check if Starlink subnet is accessible
    sl_ok, _ = ping_test("192.168.100.1", count=1, timeout=2)
    if not sl_ok:
        return result

    result["dish_present"] = True

    # Try Starlink dish HTTP status endpoint
    try:
        with urllib.request.urlopen(
            "http://192.168.100.1:9201/", timeout=4
        ) as resp:
            body = resp.read(4096).decode(errors="ignore")
            result["connected"] = True

            import re
            # Parse latency
            lat = re.search(r'"popPingLatencyMs":\s*([\d.]+)', body)
            if lat:
                result["latency_ms"] = round(float(lat.group(1)), 1)

            # Parse throughput
            dl = re.search(r'"downlinkThroughputBps":\s*([\d.]+)', body)
            ul = re.search(r'"uplinkThroughputBps":\s*([\d.]+)', body)
            if dl:
                result["download_mbps"] = round(float(dl.group(1)) / 1e6, 1)
            if ul:
                result["upload_mbps"] = round(float(ul.group(1)) / 1e6, 1)

            # Parse obstruction
            obs = re.search(r'"fractionObstructed":\s*([\d.]+)', body)
            if obs:
                result["obstruction_pct"] = round(float(obs.group(1)) * 100, 1)

            # Parse uptime
            up = re.search(r'"uptimeS":\s*(\d+)', body)
            if up:
                secs = int(up.group(1))
                h = secs // 3600
                m = (secs % 3600) // 60
                result["uptime"] = f"{h}h {m}m"

    except Exception:
        # Dish is present (ping worked) but API not responding
        result["connected"] = True
        result["latency_ms"] = None

    return result


def write_status(data):
    """Write status atomically."""
    try:
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = OUTPUT_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(OUTPUT_FILE)
    except Exception as e:
        print(f"[wan-monitor] Write error: {e}")


def poll():
    """Run one complete WAN status poll cycle."""
    ts = utcnow()

    # Determine active WAN source
    active_source, internet_latency_ms = detect_active_wan()

    # Get source-specific details
    insty = get_insty_status() or {
        "connected": active_source == "cellular",
        "carrier": "Unknown",
        "technology": "Unknown",
        "signal_strength": "Unknown",
        "antenna": "Drum",
    }
    starlink = get_starlink_status()

    # If cellular is active but InstyConnect admin unreachable,
    # mark it connected based on WAN detection
    if active_source == "cellular" and not insty.get("connected"):
        insty["connected"] = True

    # Build status object
    status = {
        "timestamp": ts,
        "active_source": active_source,
        "internet_latency_ms": internet_latency_ms,
        "instyconnect": insty,
        "starlink": starlink,
    }

    return status


if __name__ == "__main__":
    print(f"[wan-monitor] Starting — polling every {POLL_INTERVAL}s")
    print(f"[wan-monitor] Output: {OUTPUT_FILE}")

    while True:
        try:
            data = poll()
            write_status(data)
            source = data.get("active_source", "unknown")
            latency = data.get("internet_latency_ms")
            lat_str = f"  {latency}ms" if latency else ""
            print(f"[wan-monitor] {utcnow()}  WAN={source}{lat_str}")
        except Exception as e:
            print(f"[wan-monitor] Poll error: {e}")
            write_status({
                "timestamp": utcnow(),
                "active_source": "unknown",
                "error": str(e),
                "instyconnect": {"connected": False},
                "starlink": {"connected": False, "dish_present": False},
            })

        time.sleep(POLL_INTERVAL)
