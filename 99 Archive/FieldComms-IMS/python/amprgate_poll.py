#!/usr/bin/env python3
"""
amprgate_poll.py — AMPRNet Gateway Status Poller
Runs on the FieldComms Pi (192.168.50.1)
Polls the gateway Pi (192.168.50.2:9000) every 30 seconds
and writes the result to /opt/fieldcomms/data/amprgate_status.json
so the health monitor and dashboard can display 44Net status.
"""

import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

GATEWAY_URL = "http://192.168.50.2:9000/api/status"
OUTPUT_FILE = Path("/opt/fieldcomms/data/amprgate_status.json")
POLL_INTERVAL = 30  # seconds
TIMEOUT = 5         # seconds per request


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def poll():
    """Fetch status from the gateway Pi. Returns dict."""
    try:
        with urllib.request.urlopen(GATEWAY_URL, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            data["polled_at"] = utcnow()
            data["reachable"] = True
            return data
    except urllib.error.URLError as e:
        return {
            "reachable": False,
            "tunnel": "unknown",
            "error": str(e.reason),
            "polled_at": utcnow(),
            "gateway_ip": "192.168.50.2",
        }
    except Exception as e:
        return {
            "reachable": False,
            "tunnel": "unknown",
            "error": str(e),
            "polled_at": utcnow(),
            "gateway_ip": "192.168.50.2",
        }


def write(data):
    """Write status to the data directory atomically."""
    try:
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = OUTPUT_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(OUTPUT_FILE)
    except Exception as e:
        print(f"[amprgate-poll] Write error: {e}")


if __name__ == "__main__":
    print(f"[amprgate-poll] Starting — polling {GATEWAY_URL} every {POLL_INTERVAL}s")
    print(f"[amprgate-poll] Writing status to {OUTPUT_FILE}")

    while True:
        data = poll()
        write(data)

        status = data.get("tunnel", "unknown")
        reachable = data.get("reachable", False)
        addr = data.get("ampr_address", "—")

        if reachable:
            print(f"[amprgate-poll] {utcnow()}  tunnel={status}  addr={addr}")
        else:
            err = data.get("error", "no response")
            print(f"[amprgate-poll] {utcnow()}  gateway unreachable: {err}")

        time.sleep(POLL_INTERVAL)
