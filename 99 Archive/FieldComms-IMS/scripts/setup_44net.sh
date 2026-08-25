#!/usr/bin/env bash
# =========================================================
# FieldComms AMPRNet / 44Net Gateway — Installer
# Version 1.0  |  For Raspberry Pi 5 (16 GB) + Argon NEO 5
# Runs on the DEDICATED GATEWAY PI (192.168.50.2)
# NOT on the FieldComms server Pi (192.168.50.1)
# =========================================================
set -euo pipefail

GW_VERSION="1.0"
GW_USER="amprgate"
GW_HOME="/opt/amprgate"
GW_LOG="/var/log/amprgate-install.log"
WG_CONF="/etc/wireguard/ampr0.conf"
STATUS_PORT="9000"

AMBER='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log()     { echo -e "$1" | tee -a "$GW_LOG"; }
info()    { log "${CYAN}[INFO]${NC}  $1"; }
success() { log "${GREEN}[OK]${NC}    $1"; }
warn()    { log "${AMBER}[WARN]${NC}  $1"; }
error()   { log "${RED}[ERROR]${NC} $1"; exit 1; }
step()    { log "\n${BOLD}${AMBER}━━━ $1 ━━━${NC}"; }

# ── Root check ────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}This installer must be run as root: sudo bash setup_44net.sh${NC}"
    exit 1
fi

clear
cat << 'BANNER'

  ██╗  ██╗██╗  ██╗███╗   ██╗███████╗████████╗
  ██║  ██║██║  ██║████╗  ██║██╔════╝╚══██╔══╝
  ███████║███████║██╔██╗ ██║█████╗     ██║
  ╚════██║╚════██║██║╚██╗██║██╔══╝     ██║
       ██║     ██║██║ ╚████║███████╗   ██║
       ╚═╝     ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝

    AMPRNet / 44Net Gateway  v1.0
    Dedicated Gateway Pi — FieldComms EMCOMM-NET
    This Pi routes 44.0.0.0/8 for all EMCOMM-NET devices.

BANNER

mkdir -p "$(dirname $GW_LOG)"
touch "$GW_LOG"

# ── Prerequisites ─────────────────────────────────────────────────
step "Checking Prerequisites"

OS=$(lsb_release -si 2>/dev/null || echo "Unknown")
info "OS: $OS $(lsb_release -sr 2>/dev/null || echo '?')"
info "Kernel: $(uname -r)"

RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
RAM_GB=$(( RAM_KB / 1024 / 1024 ))
info "RAM: ${RAM_GB} GB"

[[ $EUID -eq 0 ]] && success "Running as root" || error "Must run as root"

# ── Interactive configuration ─────────────────────────────────────
step "Gateway Configuration"

echo ""
echo -e "${BOLD}This installer sets up the 44Net gateway Pi.${NC}"
echo -e "You will need your AMPRNet allocation details from portal.ampr.org"
echo ""

read -rp "Gateway Pi static IP [192.168.50.2]: " GW_IP
GW_IP=${GW_IP:-192.168.50.2}

read -rp "EMCOMM-NET gateway (router IP) [192.168.50.254]: " GW_ROUTER
GW_ROUTER=${GW_ROUTER:-192.168.50.254}

read -rp "Your 44.x.x.x/29 allocated address (from portal.ampr.org): " AMPR_ADDR
AMPR_ADDR=${AMPR_ADDR:-}

read -rp "Your WireGuard private key (from portal.ampr.org): " WG_PRIVKEY
WG_PRIVKEY=${WG_PRIVKEY:-REPLACE_WITH_YOUR_PRIVATE_KEY_FROM_PORTAL}

read -rp "AMPRNet gateway public key (from portal.ampr.org): " WG_PUBKEY
WG_PUBKEY=${WG_PUBKEY:-REPLACE_WITH_AMPRNET_GATEWAY_PUBLIC_KEY}

echo ""
echo -e "${BOLD}Configuration summary:${NC}"
echo -e "  Gateway Pi IP:    ${CYAN}$GW_IP${NC}"
echo -e "  Router IP:        ${CYAN}$GW_ROUTER${NC}"
echo -e "  AMPRNet address:  ${CYAN}${AMPR_ADDR:-NOT SET — edit $WG_CONF after install}${NC}"
echo -e "  Status page:      ${CYAN}http://$GW_IP:$STATUS_PORT${NC}"
echo ""
read -rp "Proceed? [Y/n]: " CONFIRM
CONFIRM=${CONFIRM:-Y}
[[ "$CONFIRM" =~ ^[Yy] ]] || { echo "Cancelled."; exit 0; }

# ── System packages ───────────────────────────────────────────────
step "Installing Packages"

apt-get update -qq 2>>"$GW_LOG"
apt-get install -y \
    wireguard wireguard-tools \
    python3 python3-pip python3-venv \
    iptables net-tools curl wget \
    avahi-daemon \
    2>>"$GW_LOG" | grep -E "(Inst|already)" || true
success "Packages installed: wireguard, python3, iptables, avahi-daemon"

# ── System user ───────────────────────────────────────────────────
step "Creating Gateway User"

if ! id "$GW_USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$GW_HOME" "$GW_USER"
    success "Created user: $GW_USER"
else
    info "User $GW_USER already exists"
fi

mkdir -p "$GW_HOME"
chown "$GW_USER:$GW_USER" "$GW_HOME"

# ── Python virtualenv + Flask ─────────────────────────────────────
step "Setting Up Python Environment"

if [[ ! -d "$GW_HOME/venv" ]]; then
    python3 -m venv "$GW_HOME/venv"
    success "Virtual environment created"
fi

"$GW_HOME/venv/bin/pip" install --quiet --upgrade pip 2>>"$GW_LOG"
"$GW_HOME/venv/bin/pip" install --quiet flask 2>>"$GW_LOG"
success "Flask installed"

# ── IP forwarding ─────────────────────────────────────────────────
step "Enabling IP Forwarding"

if ! grep -q "net.ipv4.ip_forward = 1" /etc/sysctl.conf; then
    echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.conf
    success "IP forwarding enabled in /etc/sysctl.conf"
else
    info "IP forwarding already set"
fi

sysctl -p 2>>"$GW_LOG"
success "IP forwarding active now"

# ── WireGuard config ──────────────────────────────────────────────
step "Configuring WireGuard Tunnel"

mkdir -p /etc/wireguard
chmod 700 /etc/wireguard

if [[ -f "$WG_CONF" ]]; then
    info "WireGuard config already exists — backing up to ${WG_CONF}.bak"
    cp "$WG_CONF" "${WG_CONF}.bak"
fi

cat > "$WG_CONF" << WGCONF
# AMPRNet / 44Net WireGuard Tunnel
# Gateway Pi — FieldComms EMCOMM-NET
# Generated by setup_44net.sh v${GW_VERSION}
#
# IMPORTANT: Replace the placeholder values below with the actual values
# from your AMPRNet portal allocation at https://portal.ampr.org
# Subnets → My Subnets → click your allocation → WireGuard Config
#
[Interface]
PrivateKey = ${WG_PRIVKEY}
# Your assigned 44.x.x.x/29 address from the AMPRNet portal:
Address = ${AMPR_ADDR:-44.x.x.x/29}
ListenPort = 51820

# Route 44.0.0.0/8 through this interface when tunnel comes up
PostUp   = ip route add 44.0.0.0/8 dev ampr0 2>/dev/null || true
# Allow forwarding between EMCOMM-NET (eth0) and AMPRNet (ampr0)
PostUp   = iptables -A FORWARD -i ampr0 -o eth0 -j ACCEPT
PostUp   = iptables -A FORWARD -i eth0 -o ampr0 -j ACCEPT
# Masquerade outbound AMPRNet traffic with the gateway Pi's 44.x address
PostUp   = iptables -t nat -A POSTROUTING -o ampr0 -j MASQUERADE

# Clean up on tunnel shutdown
PostDown = ip route del 44.0.0.0/8 dev ampr0 2>/dev/null || true
PostDown = iptables -D FORWARD -i ampr0 -o eth0 -j ACCEPT 2>/dev/null || true
PostDown = iptables -D FORWARD -i eth0 -o ampr0 -j ACCEPT 2>/dev/null || true
PostDown = iptables -t nat -D POSTROUTING -o ampr0 -j MASQUERADE 2>/dev/null || true

[Peer]
# AMPRNet gateway public key (from portal.ampr.org):
PublicKey = ${WG_PUBKEY}
Endpoint  = amprgw.ampr.org:51820
# Allow all AMPRNet traffic through this peer
AllowedIPs = 44.0.0.0/8
# Keepalive so the tunnel stays up through NAT
PersistentKeepalive = 25
WGCONF

chmod 600 "$WG_CONF"
success "WireGuard config written: $WG_CONF"

if [[ -z "$AMPR_ADDR" || "$WG_PRIVKEY" == "REPLACE_WITH_YOUR_PRIVATE_KEY_FROM_PORTAL" ]]; then
    warn "AMPRNet credentials not set. Edit $WG_CONF with your portal values before starting the tunnel."
    warn "Then run:  sudo wg-quick up ampr0  to bring up the tunnel."
fi

# ── Static IP ─────────────────────────────────────────────────────
step "Configuring Static IP ($GW_IP)"

ETH_CON=$(nmcli -t -f NAME,TYPE con show 2>/dev/null | grep ethernet | head -1 | cut -d: -f1 || echo "")
if [[ -z "$ETH_CON" ]]; then
    ETH_CON="Wired connection 1"
    warn "Could not detect Ethernet connection name — defaulting to: $ETH_CON"
fi

nmcli con mod "$ETH_CON" \
    ipv4.addresses "$GW_IP/24" \
    ipv4.gateway "$GW_ROUTER" \
    ipv4.dns "8.8.8.8 8.8.4.4" \
    ipv4.method manual 2>>"$GW_LOG" \
    && success "Static IP configured: $GW_IP/24 via $ETH_CON" \
    || warn "nmcli failed — set static IP manually in Network Settings"

# ── Status page ───────────────────────────────────────────────────
step "Installing Gateway Status Page"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Copy the status Python script
if [[ -f "$SCRIPT_DIR/../python/amprgate_status.py" ]]; then
    cp "$SCRIPT_DIR/../python/amprgate_status.py" "$GW_HOME/amprgate_status.py"
    chmod 755 "$GW_HOME/amprgate_status.py"
    success "Installed: amprgate_status.py"
else
    warn "amprgate_status.py not found in python/ — status page will not be available"
fi

# Install status page HTML template
mkdir -p "$GW_HOME/templates"
cat > "$GW_HOME/templates/index.html" << 'STATUSHTML'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="30">
<title>AMPRNet Gateway Status — FieldComms</title>
<style>
  :root {
    --bg:#eef2f7; --panel:#fff; --eoc:#1a3a6b; --eoc-lt:#2d6ab4;
    --green:#1a7a3a; --red:#b82020; --amber:#c8760a;
    --txt:#0f1e38; --line:#b0c4dc; --accent:#f0c040;
    --font:'Share Tech Mono','Courier New',monospace;
  }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:var(--bg); color:var(--txt); font-family:var(--font); font-size:14px; }
  .header {
    background:var(--eoc); color:#fff; padding:14px 24px;
    display:flex; align-items:center; justify-content:space-between;
    border-bottom:3px solid var(--accent);
  }
  .header-left h1 { font-size:20px; letter-spacing:2px; }
  .header-left p  { font-size:11px; color:rgba(255,255,255,0.7); margin-top:2px; }
  .header-right   { font-size:12px; color:rgba(255,255,255,0.8); text-align:right; }
  .main { max-width:900px; margin:24px auto; padding:0 16px; }
  .card {
    background:var(--panel); border:1px solid var(--line);
    border-radius:8px; padding:20px; margin-bottom:16px;
  }
  .card h2 { color:var(--eoc); font-size:14px; letter-spacing:1px; margin-bottom:14px;
              border-bottom:1px solid var(--line); padding-bottom:8px; }
  .status-big {
    font-size:42px; font-weight:bold; text-align:center;
    padding:20px; border-radius:6px; margin-bottom:16px;
  }
  .status-up   { color:var(--green); background:#e4f5ea; }
  .status-down { color:var(--red);   background:#fde8e8; }
  .stat-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
  .stat { background:var(--bg); border-radius:6px; padding:12px; }
  .stat .label { font-size:10px; color:var(--eoc-lt); letter-spacing:1px; text-transform:uppercase; }
  .stat .value { font-size:16px; font-weight:bold; color:var(--txt); margin-top:4px; }
  table { width:100%; border-collapse:collapse; font-size:12px; }
  th { background:var(--eoc); color:#fff; padding:8px 10px; text-align:left; font-size:11px; letter-spacing:1px; }
  td { padding:8px 10px; border-bottom:1px solid var(--line); }
  tr:nth-child(even) td { background:var(--bg); }
  .dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; }
  .dot-green { background:var(--green); }
  .dot-red   { background:var(--red); }
  .dot-amber { background:var(--amber); }
  .footer { text-align:center; color:#7a96b8; font-size:11px; padding:16px; }
  .refresh-note { font-size:10px; color:#7a96b8; text-align:right; margin-top:-10px; margin-bottom:12px; }
</style>
</head>
<body>
<div class="header">
  <div class="header-left">
    <h1>🛰 AMPRNet Gateway</h1>
    <p>FieldComms EMCOMM-NET  ·  K9ESV  ·  44.0.0.0/8</p>
  </div>
  <div class="header-right">
    <div id="clock">--:--:-- UTC</div>
    <div style="margin-top:4px">Gateway IP: <strong>192.168.50.2</strong></div>
  </div>
</div>

<div class="main">
  <div class="refresh-note">Auto-refreshes every 30 seconds</div>

  <div class="card">
    <h2>TUNNEL STATUS</h2>
    <div id="tunnel-status" class="status-big status-down">Checking...</div>
    <div class="stat-grid">
      <div class="stat">
        <div class="label">Tunnel Interface</div>
        <div class="value" id="iface">ampr0</div>
      </div>
      <div class="stat">
        <div class="label">AMPRNet Address</div>
        <div class="value" id="ampr-addr">—</div>
      </div>
      <div class="stat">
        <div class="label">Last Handshake</div>
        <div class="value" id="handshake">—</div>
      </div>
      <div class="stat">
        <div class="label">Data Transferred</div>
        <div class="value" id="transfer">—</div>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>EMCOMM-NET ROUTING</h2>
    <table>
      <thead>
        <tr><th>NETWORK</th><th>VIA</th><th>STATUS</th></tr>
      </thead>
      <tbody id="routes">
        <tr><td colspan="3" style="text-align:center;color:#7a96b8">Loading...</td></tr>
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>SYSTEM</h2>
    <div class="stat-grid">
      <div class="stat">
        <div class="label">CPU Temperature</div>
        <div class="value" id="cpu-temp">—</div>
      </div>
      <div class="stat">
        <div class="label">Memory Used</div>
        <div class="value" id="mem">—</div>
      </div>
      <div class="stat">
        <div class="label">Uptime</div>
        <div class="value" id="uptime">—</div>
      </div>
      <div class="stat">
        <div class="label">IP Forwarding</div>
        <div class="value" id="forwarding">—</div>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>QUICK ACTIONS</h2>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <button onclick="tunnelAction('up')"
        style="background:var(--green);color:#fff;border:none;padding:10px 20px;
               border-radius:6px;font-family:var(--font);font-size:13px;cursor:pointer">
        ▲ Bring Tunnel UP
      </button>
      <button onclick="tunnelAction('down')"
        style="background:var(--red);color:#fff;border:none;padding:10px 20px;
               border-radius:6px;font-family:var(--font);font-size:13px;cursor:pointer">
        ▼ Bring Tunnel DOWN
      </button>
      <button onclick="tunnelAction('restart')"
        style="background:var(--amber);color:#fff;border:none;padding:10px 20px;
               border-radius:6px;font-family:var(--font);font-size:13px;cursor:pointer">
        ↺ Restart Tunnel
      </button>
      <button onclick="load()"
        style="background:var(--eoc-lt);color:#fff;border:none;padding:10px 20px;
               border-radius:6px;font-family:var(--font);font-size:13px;cursor:pointer">
        ⟳ Refresh Now
      </button>
    </div>
    <div id="action-msg" style="margin-top:10px;font-size:12px;color:var(--eoc-lt)"></div>
  </div>
</div>

<div class="footer">
  FieldComms IMS v1.0  ·  AMPRNet Gateway  ·  K9ESV  ·  MCESV/MCEMA
</div>

<script>
function fmt(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes/1024).toFixed(1) + ' KB';
  if (bytes < 1073741824) return (bytes/1048576).toFixed(1) + ' MB';
  return (bytes/1073741824).toFixed(2) + ' GB';
}

function load() {
  fetch('/api/status')
    .then(r => r.json())
    .then(d => {
      const up = d.tunnel === 'up';
      const el = document.getElementById('tunnel-status');
      el.textContent = up ? '▲  TUNNEL UP' : '▼  TUNNEL DOWN';
      el.className = 'status-big ' + (up ? 'status-up' : 'status-down');

      document.getElementById('ampr-addr').textContent = d.ampr_address || '—';
      document.getElementById('handshake').textContent = d.last_handshake || '—';
      document.getElementById('transfer').textContent =
        d.rx_bytes !== undefined
          ? '↓ ' + fmt(d.rx_bytes) + '  ↑ ' + fmt(d.tx_bytes)
          : '—';
      document.getElementById('cpu-temp').textContent =
        d.cpu_temp ? d.cpu_temp + ' °C' : '—';
      document.getElementById('mem').textContent =
        d.mem_used_mb ? d.mem_used_mb + ' / ' + d.mem_total_mb + ' MB' : '—';
      document.getElementById('uptime').textContent = d.uptime || '—';
      document.getElementById('forwarding').textContent =
        d.ip_forward ? '✓ Enabled' : '✗ Disabled';

      const routes = document.getElementById('routes');
      if (d.routes && d.routes.length) {
        routes.innerHTML = d.routes.map(r =>
          `<tr>
            <td>${r.net}</td>
            <td>${r.via}</td>
            <td><span class="dot dot-${r.ok ? 'green':'red'}"></span>${r.ok ? 'Active' : 'Down'}</td>
          </tr>`
        ).join('');
      } else {
        routes.innerHTML = '<tr><td colspan="3">No routes found — tunnel may be down</td></tr>';
      }
    })
    .catch(() => {
      document.getElementById('tunnel-status').textContent = '? CANNOT REACH API';
    });
}

function tunnelAction(action) {
  fetch('/api/tunnel/' + action, {method:'POST'})
    .then(r => r.json())
    .then(d => {
      document.getElementById('action-msg').textContent = d.message || 'Done';
      setTimeout(load, 2000);
    })
    .catch(() => {
      document.getElementById('action-msg').textContent = 'Error — check gateway Pi terminal';
    });
}

function clock() {
  const n = new Date();
  document.getElementById('clock').textContent =
    n.getUTCHours().toString().padStart(2,'0') + ':' +
    n.getUTCMinutes().toString().padStart(2,'0') + ':' +
    n.getUTCSeconds().toString().padStart(2,'0') + ' UTC';
}

load();
setInterval(load, 30000);
setInterval(clock, 1000);
clock();
</script>
</body>
</html>
STATUSHTML

success "Status page HTML template created"

# ── Sudoers entry for amprgate ─────────────────────────────────────────────
step "Configuring Sudoers for WireGuard Access"

SUDOERS_FILE="/etc/sudoers.d/amprgate"
cat > "$SUDOERS_FILE" << 'SUDEOF'
# Allow amprgate service user to manage WireGuard tunnel without password
# Required for tunnel up/down/restart via authenticated web interface (localhost:9001)
# Access requires valid FCC callsign session — see /var/log/amprgate-access.log
amprgate ALL=(ALL) NOPASSWD: /usr/bin/wg, /usr/bin/wg-quick
SUDEOF
chmod 440 "$SUDOERS_FILE"
visudo -c -f "$SUDOERS_FILE" 2>>"$GW_LOG" \
    && success "Sudoers entry created: $SUDOERS_FILE" \
    || { warn "Invalid sudoers file — removing"; rm -f "$SUDOERS_FILE"; }

# ── Firewall — protect control port 9001 ──────────────────────────────────
step "Configuring Firewall — Access Control"

if command -v ufw &>/dev/null; then
    # Allow status/UI from EMCOMM-NET (read-only + callsign-authenticated UI)
    ufw allow from 192.168.50.0/24 to any port 9000 proto tcp \
        comment "AMPRNet status and UI (callsign auth)" 2>>"$GW_LOG" || true
    # Block control port from all external sources — localhost only by design
    ufw deny in on eth0 to any port 9001 proto tcp \
        comment "AMPRNet control port — localhost only" 2>>"$GW_LOG" || true
    success "Port 9000: EMCOMM-NET accessible (callsign login required for UI)"
    success "Port 9001: Blocked externally — localhost access only (physical keyboard)"
fi

# ── Systemd services ──────────────────────────────────────────────
step "Installing Systemd Services"

# WireGuard tunnel service (built-in to wg-quick)
systemctl enable wg-quick@ampr0 2>>"$GW_LOG" && success "wg-quick@ampr0 enabled at boot"

# Status page service
if [[ -f "$SCRIPT_DIR/../systemd/amprgate-status.service" ]]; then
    cp "$SCRIPT_DIR/../systemd/amprgate-status.service" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable amprgate-status 2>>"$GW_LOG" && success "amprgate-status.service enabled"
else
    # Write it inline as fallback
    cat > /etc/systemd/system/amprgate-status.service << SVCEOF
[Unit]
Description=AMPRNet Gateway Status Page (Port $STATUS_PORT)
After=network.target wg-quick@ampr0.service
Wants=wg-quick@ampr0.service

[Service]
Type=simple
User=$GW_USER
Group=$GW_USER
WorkingDirectory=$GW_HOME
ExecStart=$GW_HOME/venv/bin/python $GW_HOME/amprgate_status.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=amprgate-status

[Install]
WantedBy=multi-user.target
SVCEOF
    systemctl daemon-reload
    systemctl enable amprgate-status 2>>"$GW_LOG" && success "amprgate-status.service created and enabled"
fi

chown -R "$GW_USER:$GW_USER" "$GW_HOME"

# ── Firewall ──────────────────────────────────────────────────────
step "Configuring Firewall"

if command -v ufw &>/dev/null; then
    ufw allow 22/tcp    comment "SSH"                  2>>"$GW_LOG" || true
    ufw allow 9000/tcp  comment "AMPRNet status page"  2>>"$GW_LOG" || true
    ufw allow 51820/udp comment "WireGuard tunnel"     2>>"$GW_LOG" || true
    ufw --force enable  2>>"$GW_LOG" && success "Firewall configured" || warn "ufw enable failed"
fi

# ── Desktop autostart (Raspberry Pi OS Desktop) ───────────────────
step "Setting Up Desktop Autostart"

# Create a desktop shortcut for the status page
DESKTOP_DIR="/etc/xdg/autostart"
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/amprgate-status.desktop" << DESKEOF
[Desktop Entry]
Type=Application
Name=AMPRNet Gateway Status
Comment=Opens the 44Net tunnel status and control page in Chromium
Exec=chromium-browser --app=http://localhost:$STATUS_PORT --start-maximized --disable-session-crashed-bubble
Icon=network-wired
Terminal=false
Categories=Network;
X-GNOME-Autostart-enabled=true
DESKEOF

# Also create a tunnel control shortcut (localhost:9001 — only works here)
cat > "$DESKTOP_DIR/amprgate-control.desktop" << DESKEOF
[Desktop Entry]
Type=Application
Name=AMPRNet Tunnel Control
Comment=Local-only tunnel control interface (requires callsign login)
Exec=chromium-browser --app=http://localhost:9001 --start-maximized
Icon=network-wired
Terminal=false
Categories=Network;
X-GNOME-Autostart-enabled=false
DESKEOF
success "Desktop autostart configured — Chromium will open status page on login"

# Also add a desktop shortcut on the Pi desktop
if [[ -d /home/pi/Desktop ]]; then
    cp "$DESKTOP_DIR/amprgate-status.desktop" /home/pi/Desktop/
    chmod +x /home/pi/Desktop/amprgate-status.desktop
    success "Desktop shortcut added for pi user"
fi

# ── ASUS router static route reminder ────────────────────────────
step "Post-Install Steps Required"

echo ""
echo -e "${AMBER}${BOLD}━━━ MANUAL STEPS REQUIRED ━━━${NC}"
echo ""
echo -e "${BOLD}1. Add your AMPRNet credentials to the WireGuard config:${NC}"
echo -e "   ${CYAN}sudo nano $WG_CONF${NC}"
echo -e "   Replace the placeholder values with your portal.ampr.org allocation."
echo ""
echo -e "${BOLD}2. Start the WireGuard tunnel:${NC}"
echo -e "   ${CYAN}sudo wg-quick up ampr0${NC}"
echo -e "   Then verify:  ${CYAN}sudo wg show ampr0${NC}"
echo ""
echo -e "${BOLD}3. Add the 44Net static route on the ASUS router:${NC}"
echo -e "   Open ${CYAN}http://192.168.50.254${NC}  (ASUS router admin)"
echo -e "   Go to:  LAN → Route → Add"
echo -e "   Network/Host IP:  ${CYAN}44.0.0.0${NC}"
echo -e "   Netmask:          ${CYAN}255.0.0.0${NC}"
echo -e "   Gateway:          ${CYAN}$GW_IP${NC}"
echo -e "   Interface:        ${CYAN}LAN${NC}"
echo -e "   Click Apply."
echo ""
echo -e "${BOLD}4. Verify from the FieldComms Pi:${NC}"
echo -e "   ${CYAN}ping 44.0.0.1 -c 4${NC}"
echo ""

# ── Done ──────────────────────────────────────────────────────────
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║      AMPRNet Gateway Installation Complete!              ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Status page:  ${CYAN}http://$GW_IP:$STATUS_PORT${NC}"
echo -e "  WireGuard config:  ${CYAN}$WG_CONF${NC}"
echo -e "  Install log:  ${CYAN}$GW_LOG${NC}"
echo ""
echo -e "${AMBER}Complete the 3 manual steps above, then reboot.${NC}"
echo ""
read -rp "Reboot now? [y/N]: " DO_REBOOT
[[ "$DO_REBOOT" =~ ^[Yy] ]] && reboot

exit 0
