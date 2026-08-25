#!/usr/bin/env python3
"""
health_monitor.py — FieldComms Health Monitor Service (port 5051)
Reports CPU temp, memory, disk, service status, internet connectivity,
GPS status, Dead Man's Switch state, preflight results.
"""

import json, os, subprocess, time, socket, threading
from datetime import datetime, timezone
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request

DATA = Path("/opt/fieldcomms/data")
DMS_STATE_F = DATA / "dms_state.json"

SERVICES = [
    ("nginx",           "Web Server"),
    ("fcc-lookup",      "FCC Lookup API"),
    ("health-monitor",  "Health Monitor"),
    ("graywolf",        "Graywolf APRS"),
    ("pat",             "Pat Winlink"),
    ("kiwix-serve",     "Kiwix"),
    ("gpsd",            "GPS Daemon"),
    ("chrony",          "NTP/Chrony"),
    ("deadmans",        "Dead Man's Switch"),
    ("tailscaled",      "Tailscale"),
    ("ics-platform",    "ICS Platform"),
    ("amprgate-poll",   "44Net Gateway Poll"),
    ("wan-monitor",      "WAN Status Monitor"),
]

AMPRGATE_STATUS_FILE = DATA / "amprgate_status.json"

def get_amprgate_status():
    """Read the 44Net gateway status written by amprgate_poll.py."""
    try:
        if AMPRGATE_STATUS_FILE.exists():
            data = json.loads(AMPRGATE_STATUS_FILE.read_text())
            return {
                "reachable": data.get("reachable", False),
                "tunnel": data.get("tunnel", "unknown"),
                "ampr_address": data.get("ampr_address"),
                "last_handshake": data.get("last_handshake"),
                "polled_at": data.get("polled_at"),
            }
    except Exception:
        pass
    return {"reachable": False, "tunnel": "not configured"}


WAN_STATUS_FILE = DATA / "wan_status.json"

def get_wan_status():
    """
    Read WAN status from wan_status.json written by the WAN monitor.
    Falls back to basic internet connectivity check if file is not present.
    """
    # Try the WAN status file first (written by wan_monitor service)
    try:
        if WAN_STATUS_FILE.exists():
            return json.loads(WAN_STATUS_FILE.read_text())
    except Exception:
        pass

    # Fallback: basic internet check and return minimal status
    internet = get_internet()
    connected = internet.get("connected", False)
    return {
        "active_source": "cellular" if connected else "none",
        "instyconnect": {
            "connected": connected,
            "carrier": "Unknown",
            "technology": "Unknown",
            "signal_strength": "Unknown",
            "antenna": "Drum",
        },
        "starlink": {
            "connected": False,
            "dish_present": False,
        },
        "note": "wan_monitor service not running — basic internet check only",
    }

_cache = {}
_cache_lock = threading.Lock()
_CACHE_TTL = 10  # seconds

def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def run(cmd, timeout=3):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""

def get_cpu_temp():
    """Read CPU temperature in Celsius"""
    # Try thermal zone (Linux)
    for tz in Path("/sys/class/thermal").glob("thermal_zone*/temp"):
        try:
            v = int(tz.read_text().strip())
            if 10000 < v < 100000:  # sanity: 10–100°C
                return round(v / 1000, 1)
        except Exception:
            pass
    # Try vcgencmd (Pi-specific)
    out = run(["vcgencmd", "measure_temp"])
    if "temp=" in out:
        try:
            return float(out.split("=")[1].replace("'C","").strip())
        except Exception:
            pass
    return None

def get_memory():
    try:
        with open("/proc/meminfo") as f:
            lines = {l.split(":")[0]: int(l.split()[1]) for l in f if ":" in l}
        total = lines.get("MemTotal", 0)
        avail = lines.get("MemAvailable", 0)
        used  = total - avail
        pct   = round(used * 100 / total, 1) if total else 0
        return {"total_mb": total//1024, "used_mb": used//1024,
                "free_mb": avail//1024, "percent": pct}
    except Exception:
        return {"total_mb": 0, "used_mb": 0, "free_mb": 0, "percent": 0}

def get_disk():
    disks = []
    for mount in ["/", "/opt", "/mnt/nvme", "/mnt/ssd"]:
        if Path(mount).exists():
            try:
                st = os.statvfs(mount)
                total = st.f_blocks * st.f_frsize
                free  = st.f_bavail * st.f_frsize
                used  = total - free
                pct   = round(used * 100 / total, 1) if total else 0
                disks.append({"mount": mount, "total_gb": round(total/1e9,1),
                               "used_gb": round(used/1e9,1), "free_gb": round(free/1e9,1),
                               "percent": pct})
            except Exception:
                pass
    return disks

def get_services():
    results = {}
    for svc_name, label in SERVICES:
        out = run(["systemctl", "is-active", svc_name])
        results[svc_name] = {"label": label, "active": out == "active", "status": out or "inactive"}
    return results

def get_internet():
    """Check internet via DNS and HTTP"""
    dns_ok = False
    http_ok = False
    try:
        socket.setdefaulttimeout(3)
        socket.getaddrinfo("dns.google", 443)
        dns_ok = True
    except Exception:
        pass
    try:
        urllib.request.urlopen("http://connectivitycheck.gstatic.com/generate_204", timeout=4)
        http_ok = True
    except Exception:
        pass
    return {"connected": dns_ok and http_ok, "dns": dns_ok, "http": http_ok}

def get_gps():
    """Check GPS status via gpsd"""
    try:
        s = socket.socket()
        s.settimeout(2)
        s.connect(("127.0.0.1", 2947))
        s.send(b'?POLL;\n')
        time.sleep(0.5)
        data = b""
        s.settimeout(1)
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk: break
                data += chunk
        except Exception:
            pass
        s.close()
        text = data.decode(errors="ignore")
        # Parse TPV (Time-Position-Velocity) report
        for line in text.splitlines():
            if '"class":"TPV"' in line:
                tpv = json.loads(line)
                return {
                    "fix": tpv.get("mode", 0) >= 2,
                    "mode": tpv.get("mode", 0),
                    "lat": tpv.get("lat"),
                    "lon": tpv.get("lon"),
                    "alt": tpv.get("alt"),
                    "speed": tpv.get("speed"),
                    "time": tpv.get("time"),
                    "satellites": None
                }
        return {"fix": False, "mode": 0, "lat": None, "lon": None}
    except Exception:
        return {"fix": False, "mode": 0, "lat": None, "lon": None, "error": "gpsd unreachable"}

def get_dms():
    try:
        if DMS_STATE_F.exists():
            return json.loads(DMS_STATE_F.read_text())
    except Exception:
        pass
    return {"state": "disarmed"}

def get_tailscale():
    out = run(["tailscale", "status", "--json"])
    if out:
        try:
            ts = json.loads(out)
            return {
                "running": ts.get("BackendState") == "Running",
                "self_ip": ts.get("Self", {}).get("TailscaleIPs", [None])[0],
                "hostname": ts.get("Self", {}).get("HostName"),
            }
        except Exception:
            pass
    return {"running": False, "self_ip": None, "hostname": None}

def collect_health():
    with _cache_lock:
        now = time.time()
        if _cache.get("ts", 0) + _CACHE_TTL > now:
            return _cache.get("data")

    data = {
        "timestamp": utcnow(),
        "uptime": run(["uptime", "-p"]),
        "hostname": run(["hostname"]),
        "cpu_temp": get_cpu_temp(),
        "memory": get_memory(),
        "disk": get_disk(),
        "services": get_services(),
        "internet": get_internet(),
        "gps": get_gps(),
        "dms": get_dms(),
        "tailscale": get_tailscale(),
        "amprgate": get_amprgate_status(),
        "wan": get_wan_status(),
    }

    with _cache_lock:
        _cache["data"] = data
        _cache["ts"]   = time.time()
    return data


class HealthHandler(BaseHTTPRequestHandler):
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

    def do_OPTIONS(self):
        self.send_response(204)
        self.cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/")

        if path in ("", "/", "/api/health"):
            return self.send_json(collect_health())

        elif path == "/api/health/quick":
            # Lightweight check — cached only
            d = _cache.get("data") or collect_health()
            svcs = d.get("services", {})
            return self.send_json({
                "timestamp": d.get("timestamp"),
                "cpu_temp":  d.get("cpu_temp"),
                "memory_pct": d.get("memory", {}).get("percent"),
                "internet": d.get("internet", {}).get("connected"),
                "gps_fix":  d.get("gps", {}).get("fix"),
                "dms_state": d.get("dms", {}).get("state"),
                "services_ok": sum(1 for v in svcs.values() if v.get("active")),
                "services_total": len(svcs),
            })

        elif path == "/api/health/services":
            return self.send_json(get_services())

        elif path == "/api/health/gps":
            return self.send_json(get_gps())

        elif path == "/api/health/internet":
            return self.send_json(get_internet())

        elif path == "/api/preflight":
            # Delegate to fcc_lookup_server's preflight
            try:
                req = urllib.request.urlopen("http://127.0.0.1:5050/api/preflight", timeout=10)
                return self.send_json(json.loads(req.read()))
            except Exception as e:
                return self.send_json({"error": str(e), "verdict": "NO-GO"}, 503)

        else:
            self.send_json({"error": "Not found"}, 404)


if __name__ == "__main__":
    print("[health-monitor] Starting on port 5051")
    # Pre-warm cache in background
    threading.Thread(target=collect_health, daemon=True).start()
    server = HTTPServer(("0.0.0.0", 5051), HealthHandler)
    server.serve_forever()
