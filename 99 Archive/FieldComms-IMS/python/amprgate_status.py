#!/usr/bin/env python3
"""
amprgate_status.py — AMPRNet Gateway Status Service
Runs on the dedicated 44Net gateway Pi (192.168.50.2)

SECURITY MODEL:
  - Status API (/api/status, /health): bound to ALL interfaces (0.0.0.0:9000)
    so the FieldComms Pi poll service can read it server-to-server.
    These endpoints are READ-ONLY — no tunnel control.

  - Tunnel control (/api/tunnel/up|down|restart): bound to LOCALHOST ONLY
    (127.0.0.1:9001). Requires physical access to the gateway Pi keyboard.
    Callsign validation via FCC database on FieldComms Pi (192.168.50.1).

  - Web UI (/): served on 0.0.0.0:9000. Requires callsign login before
    showing tunnel controls. Callsign validated against FCC database.
    Session tokens expire after 8 hours. Access log maintained for
    Part 97 station identification compliance.

Endpoints (port 9000 — EMCOMM-NET accessible):
  GET  /              — Dashboard UI (requires callsign login)
  GET  /api/status    — JSON tunnel status (no auth — read only)
  GET  /health        — Service health check (no auth)
  POST /api/login     — Validate callsign, issue session token
  GET  /api/validate  — Check if session token is still valid
  POST /api/logout    — Invalidate session token

Endpoints (port 9001 — localhost only, physical access required):
  POST /api/tunnel/up      — Bring tunnel up
  POST /api/tunnel/down    — Bring tunnel down
  POST /api/tunnel/restart — Restart tunnel
"""

import json
import os
import re
import secrets
import subprocess
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# ── Configuration ─────────────────────────────────────────────────────────────
PUBLIC_PORT    = 9000          # Status + UI — accessible from EMCOMM-NET
CONTROL_PORT   = 9001          # Tunnel control — localhost only
WG_INTERFACE   = "ampr0"
FIELDCOMMS_API = "http://192.168.50.1:5050"  # FCC lookup on FieldComms Pi
SESSION_TTL    = 8 * 3600      # 8 hours in seconds
LOG_FILE       = Path("/var/log/amprgate-access.log")
TEMPLATES      = Path("/opt/amprgate/templates")

# ── In-memory session store ───────────────────────────────────────────────────
# { token: {"callsign": str, "issued": float, "ip": str} }
_sessions: dict = {}
_sessions_lock = threading.Lock()

# ── Logging ───────────────────────────────────────────────────────────────────

def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def access_log(action: str, callsign: str, ip: str, detail: str = ""):
    """Write to Part 97 station identification access log."""
    entry = f"{utcnow()}  {action:<12}  {callsign:<12}  {ip:<16}  {detail}\n"
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(entry)
    except Exception:
        pass
    print(f"[amprgate-access] {entry.strip()}")


# ── FCC callsign validation ───────────────────────────────────────────────────

def validate_callsign(callsign: str) -> dict:
    """
    Validate callsign against the FCC database on the FieldComms Pi.
    Returns {"valid": bool, "name": str|None, "license_class": str|None}
    Falls back to format-only validation if FieldComms Pi is unreachable.
    """
    cs = callsign.strip().upper()

    # Basic format check first — US callsigns: 1x2, 1x3, 2x1, 2x2, 2x3
    if not re.match(r'^[A-Z]{1,2}[0-9][A-Z]{1,3}$', cs):
        return {"valid": False, "name": None, "license_class": None,
                "error": "Invalid callsign format"}

    # Try FCC database lookup on FieldComms Pi
    try:
        url = f"{FIELDCOMMS_API}/callsign/{cs}"
        req = urllib.request.Request(url, headers={"User-Agent": "amprgate/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data.get("found"):
                return {
                    "valid": True,
                    "name": data.get("name", ""),
                    "license_class": data.get("license_class", ""),
                    "error": None,
                }
            else:
                return {"valid": False, "name": None, "license_class": None,
                        "error": "Callsign not found in FCC database"}
    except urllib.error.URLError:
        # FieldComms Pi unreachable — fall back to format-only validation
        # This allows access even if FieldComms Pi is down, but logs the fallback
        access_log("FCC-FALLBACK", cs, "localhost",
                   "FieldComms Pi unreachable — format-only validation used")
        return {
            "valid": True,
            "name": None,
            "license_class": "Unknown (FCC DB offline)",
            "error": None,
            "fallback": True,
        }
    except Exception as e:
        return {"valid": False, "name": None, "license_class": None,
                "error": f"Lookup error: {e}"}


# ── Session management ────────────────────────────────────────────────────────

def create_session(callsign: str, ip: str) -> str:
    """Issue a new session token."""
    token = secrets.token_urlsafe(32)
    with _sessions_lock:
        _sessions[token] = {
            "callsign": callsign.upper(),
            "issued": time.time(),
            "ip": ip,
        }
    return token


def validate_session(token: str) -> dict | None:
    """Return session dict if valid and not expired, else None."""
    if not token:
        return None
    with _sessions_lock:
        session = _sessions.get(token)
        if not session:
            return None
        if time.time() - session["issued"] > SESSION_TTL:
            del _sessions[token]
            return None
        return session


def revoke_session(token: str):
    """Invalidate a session token."""
    with _sessions_lock:
        _sessions.pop(token, None)


def purge_expired():
    """Remove expired sessions (called periodically)."""
    now = time.time()
    with _sessions_lock:
        expired = [t for t, s in _sessions.items()
                   if now - s["issued"] > SESSION_TTL]
        for t in expired:
            del _sessions[t]


# ── WireGuard status ──────────────────────────────────────────────────────────

def run(cmd, timeout=5):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode
    except Exception as e:
        return str(e), -1


def get_cpu_temp():
    for tz in Path("/sys/class/thermal").glob("thermal_zone*/temp"):
        try:
            v = int(tz.read_text().strip())
            if 10000 < v < 100000:
                return round(v / 1000, 1)
        except Exception:
            pass
    out, _ = run(["vcgencmd", "measure_temp"])
    if "temp=" in out:
        try:
            return float(out.split("=")[1].replace("'C", "").strip())
        except Exception:
            pass
    return None


def get_mem():
    try:
        lines = Path("/proc/meminfo").read_text().splitlines()
        info = {}
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                info[parts[0].rstrip(":")] = int(parts[1])
        total = info.get("MemTotal", 0) // 1024
        avail = info.get("MemAvailable", 0) // 1024
        return total - avail, total
    except Exception:
        return None, None


def get_uptime():
    try:
        secs = float(Path("/proc/uptime").read_text().split()[0])
        h = int(secs // 3600)
        m = int((secs % 3600) // 60)
        return f"{h}h {m}m"
    except Exception:
        return None


def get_ip_forward():
    try:
        return Path("/proc/sys/net/ipv4/ip_forward").read_text().strip() == "1"
    except Exception:
        return False


def get_wg_status():
    out, rc = run(["sudo", "wg", "show", WG_INTERFACE, "dump"])
    if rc != 0 or not out.strip():
        return {"tunnel": "down", "ampr_address": None,
                "last_handshake": None, "rx_bytes": 0, "tx_bytes": 0}

    lines = [l.split("\t") for l in out.strip().splitlines()]
    if not lines:
        return {"tunnel": "down", "ampr_address": None,
                "last_handshake": None, "rx_bytes": 0, "tx_bytes": 0}

    addr_out, _ = run(["ip", "addr", "show", WG_INTERFACE])
    ampr_addr = None
    for line in addr_out.splitlines():
        m = re.search(r"inet\s+(44\.\d+\.\d+\.\d+/\d+)", line)
        if m:
            ampr_addr = m.group(1)
            break

    rx_total = tx_total = 0
    last_hs = None
    hs_epoch_val = 0

    for line in lines[1:]:
        if len(line) >= 7:
            try:
                hs_epoch = int(line[4])
                rx_total += int(line[5])
                tx_total += int(line[6])
                if hs_epoch > 0:
                    age_s = int(time.time()) - hs_epoch
                    if age_s < 60:
                        last_hs = f"{age_s}s ago"
                    elif age_s < 3600:
                        last_hs = f"{age_s // 60}m ago"
                    else:
                        last_hs = datetime.fromtimestamp(
                            hs_epoch, tz=timezone.utc).strftime("%H:%M UTC")
                    hs_epoch_val = hs_epoch
            except (ValueError, IndexError):
                pass

    tunnel_up = (ampr_addr is not None and
                 hs_epoch_val > 0 and
                 (int(time.time()) - hs_epoch_val) < 300)

    return {
        "tunnel": "up" if tunnel_up else "down",
        "ampr_address": ampr_addr,
        "last_handshake": last_hs or "Never",
        "rx_bytes": rx_total,
        "tx_bytes": tx_total,
    }


def get_routes():
    out, _ = run(["ip", "route", "show"])
    routes = []
    for line in out.splitlines():
        if "44.0.0.0" in line or "ampr0" in line:
            parts = line.split()
            net = parts[0] if parts else "?"
            via = "ampr0"
            for i, p in enumerate(parts):
                if p in ("via", "dev") and i + 1 < len(parts):
                    via = parts[i + 1]
                    break
            routes.append({"net": net, "via": via, "ok": True})
    if not routes:
        routes.append({"net": "44.0.0.0/8", "via": "—", "ok": False})
    return routes


def build_status():
    wg = get_wg_status()
    mem_used, mem_total = get_mem()
    return {
        "timestamp": utcnow(),
        "gateway_ip": "192.168.50.2",
        **wg,
        "cpu_temp": get_cpu_temp(),
        "mem_used_mb": mem_used,
        "mem_total_mb": mem_total,
        "uptime": get_uptime(),
        "ip_forward": get_ip_forward(),
        "routes": get_routes(),
    }


def tunnel_action(action):
    if action == "up":
        out, rc = run(["sudo", "wg-quick", "up", WG_INTERFACE], timeout=15)
        return {"ok": rc == 0, "message": "Tunnel brought up" if rc == 0 else f"Error: {out}"}
    elif action == "down":
        out, rc = run(["sudo", "wg-quick", "down", WG_INTERFACE], timeout=15)
        return {"ok": rc == 0, "message": "Tunnel brought down" if rc == 0 else f"Error: {out}"}
    elif action == "restart":
        run(["sudo", "wg-quick", "down", WG_INTERFACE], timeout=10)
        time.sleep(1)
        out, rc = run(["sudo", "wg-quick", "up", WG_INTERFACE], timeout=15)
        return {"ok": rc == 0, "message": "Tunnel restarted" if rc == 0 else f"Error: {out}"}
    return {"ok": False, "message": "Unknown action"}


# ── HTTP handlers ─────────────────────────────────────────────────────────────

def get_token_from_request(handler):
    """Extract session token from Authorization header or cookie."""
    auth = handler.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    cookie = handler.headers.get("Cookie", "")
    for part in cookie.split(";"):
        part = part.strip()
        if part.startswith("amprtoken="):
            return part[10:]
    return None


def get_client_ip(handler):
    """Get real client IP."""
    xff = handler.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return handler.client_address[0]


class PublicHandler(BaseHTTPRequestHandler):
    """
    Handles port 9000 — accessible from EMCOMM-NET.
    Status and UI only. No tunnel control.
    """

    def log_message(self, fmt, *args):
        pass

    def send_json(self, data, code=200):
        body = json.dumps(data, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, body, code=200):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(b))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/")

        if path in ("", "/"):
            # Serve UI — check for valid session
            token = get_token_from_request(self)
            session = validate_session(token)
            tmpl = TEMPLATES / "index.html"
            if tmpl.exists():
                html = tmpl.read_text()
                if session:
                    # Inject callsign into page
                    html = html.replace(
                        "<!-- CALLSIGN_PLACEHOLDER -->",
                        f'<span id="logged-in-callsign">{session["callsign"]}</span>')
                self.send_html(html)
            else:
                self.send_html(self._login_page() if not session
                               else "<h1>Template not found</h1>", 200)

        elif path == "/api/status":
            # READ-ONLY — no auth required (FieldComms Pi polls this)
            self.send_json(build_status())

        elif path == "/api/validate":
            token = get_token_from_request(self)
            session = validate_session(token)
            if session:
                self.send_json({
                    "valid": True,
                    "callsign": session["callsign"],
                    "expires_in": int(SESSION_TTL - (time.time() - session["issued"])),
                })
            else:
                self.send_json({"valid": False}, 401)

        elif path == "/health":
            self.send_json({"status": "ok", "service": "amprgate-status",
                            "active_sessions": len(_sessions)})

        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        client_ip = get_client_ip(self)

        if path == "/api/login":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_json({"ok": False, "error": "Invalid JSON"}, 400)
                return

            callsign = data.get("callsign", "").strip().upper()
            if not callsign:
                self.send_json({"ok": False, "error": "Callsign required"}, 400)
                return

            result = validate_callsign(callsign)
            if result["valid"]:
                token = create_session(callsign, client_ip)
                access_log("LOGIN-OK", callsign, client_ip,
                           f"class={result.get('license_class','?')}")
                self.send_json({
                    "ok": True,
                    "token": token,
                    "callsign": callsign,
                    "name": result.get("name", ""),
                    "license_class": result.get("license_class", ""),
                    "expires_in": SESSION_TTL,
                    "fallback": result.get("fallback", False),
                })
            else:
                access_log("LOGIN-FAIL", callsign, client_ip,
                           result.get("error", ""))
                self.send_json({
                    "ok": False,
                    "error": result.get("error", "Callsign not valid"),
                }, 401)

        elif path == "/api/logout":
            token = get_token_from_request(self)
            if token:
                session = validate_session(token)
                if session:
                    access_log("LOGOUT", session["callsign"], client_ip)
                revoke_session(token)
            self.send_json({"ok": True})

        elif path.startswith("/api/tunnel/"):
            # Tunnel control blocked on public port — must use localhost:9001
            self.send_json({
                "ok": False,
                "error": "Tunnel control requires physical access to the gateway Pi. "
                         "Use the local keyboard and browser at http://localhost:9001",
            }, 403)

        else:
            self.send_json({"error": "Not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.end_headers()

    def _login_page(self):
        return """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AMPRNet Gateway — Login</title>
<style>
body{background:#0d1117;color:#e0e8f0;font-family:'Share Tech Mono','Courier New',monospace;
     display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}
.box{background:#1a2744;border:1px solid #2d6ab4;border-radius:10px;padding:36px 40px;
     max-width:400px;width:90%;text-align:center}
.logo{font-size:32px;font-weight:bold;color:#fff;letter-spacing:4px;margin-bottom:4px}
.sub{font-size:13px;color:#f0c040;margin-bottom:6px}
.rule{height:2px;background:#f0c040;margin:16px 0}
h2{font-size:15px;color:#c0d4f0;letter-spacing:2px;margin-bottom:20px}
input{width:100%;box-sizing:border-box;background:#0d1117;border:1px solid #2d6ab4;
      color:#fff;font-family:inherit;font-size:18px;padding:12px;border-radius:6px;
      text-align:center;text-transform:uppercase;letter-spacing:4px;margin-bottom:16px}
button{width:100%;background:#1a7a3a;color:#fff;border:none;padding:12px;
       border-radius:6px;font-family:inherit;font-size:14px;cursor:pointer;
       letter-spacing:2px}
button:hover{background:#22a04e}
.err{color:#ff6060;font-size:12px;margin-top:12px;min-height:20px}
.note{color:#6080a0;font-size:11px;margin-top:20px;line-height:1.6}
</style></head><body>
<div class="box">
  <div class="logo">🛰 FIELDCOMMS</div>
  <div class="sub">Incident Management System v1.0</div>
  <div class="rule"></div>
  <h2>AMPRNet Gateway Access</h2>
  <input id="cs" type="text" placeholder="ENTER CALLSIGN"
         maxlength="10" autocomplete="off" autocapitalize="characters">
  <button onclick="login()">VERIFY &amp; ACCESS</button>
  <div class="err" id="err"></div>
  <div class="note">
    Access restricted to FCC-licensed amateur radio operators.<br>
    Callsign validated against local FCC database.<br>
    All access is logged for Part 97 compliance.<br>
    <br>
    Tunnel control requires physical keyboard access<br>
    at the gateway Pi  (localhost only).
  </div>
</div>
<script>
document.getElementById('cs').addEventListener('keydown', e => {
  if (e.key === 'Enter') login();
});
document.getElementById('cs').focus();

function login() {
  const cs = document.getElementById('cs').value.trim().toUpperCase();
  const err = document.getElementById('err');
  if (!cs) { err.textContent = 'Enter your callsign'; return; }
  err.textContent = 'Checking...';

  fetch('/api/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({callsign: cs})
  })
  .then(r => r.json())
  .then(d => {
    if (d.ok) {
      document.cookie = 'amprtoken=' + d.token + '; path=/; max-age=28800; SameSite=Strict';
      err.style.color = '#4caf50';
      err.textContent = 'Welcome ' + (d.name || cs) + ' (' + (d.license_class || '') + ')';
      setTimeout(() => window.location.reload(), 800);
    } else {
      err.textContent = d.error || 'Access denied';
    }
  })
  .catch(() => err.textContent = 'Error — check network connection');
}
</script>
</body></html>"""


class LocalHandler(BaseHTTPRequestHandler):
    """
    Handles port 9001 — localhost only.
    Tunnel control. Requires valid callsign session from public port.
    Physical access to gateway Pi keyboard required to reach this port.
    """

    def log_message(self, fmt, *args):
        pass

    def send_json(self, data, code=200):
        body = json.dumps(data, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/")
        if path == "/health":
            self.send_json({"status": "ok", "service": "amprgate-control",
                            "port": CONTROL_PORT})
        elif path == "/api/status":
            self.send_json(build_status())
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path

        # Require valid session token even on localhost
        token = get_token_from_request(self)
        session = validate_session(token)

        if not session:
            self.send_json({
                "ok": False,
                "error": "Valid callsign session required. "
                         "Log in at http://192.168.50.2:9000 first.",
            }, 401)
            return

        if path.startswith("/api/tunnel/"):
            action = path.split("/")[-1]
            if action in ("up", "down", "restart"):
                access_log(f"TUNNEL-{action.upper()}",
                           session["callsign"],
                           session["ip"],
                           f"from localhost control port")
                result = tunnel_action(action)
                self.send_json(result)
            else:
                self.send_json({"error": "Unknown action"}, 400)
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()


# ── Main ──────────────────────────────────────────────────────────────────────

def run_public_server():
    server = HTTPServer(("0.0.0.0", PUBLIC_PORT), PublicHandler)
    print(f"[amprgate-status] Public API  : http://0.0.0.0:{PUBLIC_PORT}")
    print(f"[amprgate-status]   /api/status   — read-only, no auth")
    print(f"[amprgate-status]   /             — UI requires callsign login")
    server.serve_forever()


def run_local_server():
    server = HTTPServer(("127.0.0.1", CONTROL_PORT), LocalHandler)
    print(f"[amprgate-status] Control port: http://127.0.0.1:{CONTROL_PORT}")
    print(f"[amprgate-status]   /api/tunnel/* — requires session + physical access")
    server.serve_forever()


def session_cleanup():
    """Periodically purge expired sessions."""
    while True:
        time.sleep(300)
        purge_expired()


if __name__ == "__main__":
    print(f"[amprgate-status] AMPRNet Gateway Status Service starting")
    print(f"[amprgate-status] Session TTL: {SESSION_TTL // 3600}h")
    print(f"[amprgate-status] Access log : {LOG_FILE}")

    # Start local control server on dedicated thread
    t_local   = threading.Thread(target=run_local_server,   daemon=True)
    t_cleanup = threading.Thread(target=session_cleanup,    daemon=True)
    t_local.start()
    t_cleanup.start()

    # Public server runs on main thread
    run_public_server()
