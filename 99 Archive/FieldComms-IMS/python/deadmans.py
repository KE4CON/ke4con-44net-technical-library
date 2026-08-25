#!/usr/bin/env python3
"""
deadmans.py — Dead Man's Switch service for FieldComms
Monitors active nets for inactivity and triggers alerts.
State is persisted to /opt/fieldcomms/data/dms_state.json
The main API server (port 5050) also handles /api/dms/* endpoints.
This service provides the background monitoring loop and UI API.
"""

import json, time, threading, signal, sys
from datetime import datetime, timezone
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import urllib.request

DATA = Path("/opt/fieldcomms/data")
DMS_STATE_F = DATA / "dms_state.json"
NETS_DIR    = DATA / "nets"

def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def load_json(p, default):
    try:
        if Path(p).exists():
            return json.loads(Path(p).read_text())
    except Exception:
        pass
    return default

def save_json(p, obj):
    Path(p).write_text(json.dumps(obj, indent=2, default=str))

def get_net_last_activity(net_id):
    """Find the most recent entry timestamp in a net"""
    f = NETS_DIR / f"{net_id}.json"
    if not f.exists():
        return None
    try:
        net = json.loads(f.read_text())
        entries = net.get("entries", [])
        if not entries:
            return net.get("created")
        times = [e.get("timestamp") for e in entries if e.get("timestamp")]
        if times:
            return max(times)
    except Exception:
        pass
    return None

def monitor_loop():
    print("[deadmans] Monitor loop started")
    while True:
        try:
            dms = load_json(DMS_STATE_F, {"state":"disarmed","threshold_min":30,"armed_nets":[]})

            if dms.get("state") in ("armed", "warning"):
                threshold_sec = dms.get("threshold_min", 30) * 60
                armed_nets = dms.get("armed_nets", [])

                # Find most recent activity across all armed nets
                latest = dms.get("last_activity")

                for net_id in armed_nets:
                    # Skip drill nets
                    f = NETS_DIR / f"{net_id}.json"
                    if f.exists():
                        net = json.loads(f.read_text())
                        if net.get("drill", False):
                            continue
                        act = get_net_last_activity(net_id)
                        if act and (latest is None or act > latest):
                            latest = act

                dms["last_activity"] = latest

                if latest:
                    last_dt = datetime.fromisoformat(latest.replace("Z","+00:00"))
                    elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds()

                    prev_state = dms.get("state")
                    if elapsed > threshold_sec:
                        dms["state"] = "triggered"
                        if dms.get("triggered_at") is None:
                            dms["triggered_at"] = utcnow()
                            print(f"[deadmans] TRIGGERED! No activity for {elapsed/60:.1f} minutes")
                    elif elapsed > threshold_sec * 0.75:
                        dms["state"] = "warning"
                        if prev_state == "armed":
                            print(f"[deadmans] WARNING: {(threshold_sec - elapsed)/60:.1f} min remaining")
                    else:
                        dms["state"] = "armed"

                save_json(DMS_STATE_F, dms)

        except Exception as e:
            print(f"[deadmans] Monitor error: {e}")

        time.sleep(15)

# ── Minimal HTTP for status UI ─────────────────────────────────────────────
class DmsHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_json(self, obj, code=200):
        body = json.dumps(obj, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.cors()
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/status"):
            return self.send_json(load_json(DMS_STATE_F,
                {"state":"disarmed","threshold_min":30,"armed_nets":[]}))
        self.send_json({"error":"not found"},404)


def handle_signal(sig, frame):
    print(f"\n[deadmans] Shutting down")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    DATA.mkdir(parents=True, exist_ok=True)

    # Initialize state if missing
    if not DMS_STATE_F.exists():
        save_json(DMS_STATE_F, {
            "state": "disarmed",
            "threshold_min": 30,
            "armed_nets": [],
            "last_activity": None,
            "triggered_at": None,
            "armed_at": None
        })

    # Start background monitor
    t = threading.Thread(target=monitor_loop, daemon=True)
    t.start()

    print("[deadmans] Dead Man's Switch service running")
    # Keep alive (the API endpoints are on port 5050 via fcc_lookup_server)
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
