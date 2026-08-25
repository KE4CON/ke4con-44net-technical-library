#!/usr/bin/env bash
# =========================================================
# FieldComms EmComm Field Server — Interactive Installer
# Version 1.0  |  For Raspberry Pi 5 (16 GB) / Ubuntu 24
# =========================================================
set -euo pipefail

FC_VERSION="1.0"
FC_USER="fieldcomms"
FC_HOME="/opt/fieldcomms"
FC_DATA="$FC_HOME/data"
FC_PYTHON="$FC_HOME/python"
FC_VENV="$FC_HOME/venv"
FC_WEB="/var/www/html"
FC_LOG="/var/log/fieldcomms-install.log"

AMBER='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Logging ────────────────────────────────────────────────────────
log() { echo -e "$1" | tee -a "$FC_LOG"; }
info()    { log "${CYAN}[INFO]${NC}  $1"; }
success() { log "${GREEN}[OK]${NC}    $1"; }
warn()    { log "${AMBER}[WARN]${NC}  $1"; }
error()   { log "${RED}[ERROR]${NC} $1"; exit 1; }
step()    { log "\n${BOLD}${AMBER}━━━ $1 ━━━${NC}"; }

# ── Root check ─────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}This installer must be run as root: sudo bash install.sh${NC}"
    exit 1
fi

# ── Banner ─────────────────────────────────────────────────────────
clear
cat << 'BANNER'

  ███████╗██╗███████╗██╗      ██████╗  ██████╗ ██████╗ ███╗   ███╗███████╗
  ██╔════╝██║██╔════╝██║     ██╔════╝ ██╔═══██╗██╔══██╗████╗ ████║██╔════╝
  █████╗  ██║█████╗  ██║     ██║      ██║   ██║██╔══██╗██╔████╔██║███████╗
  ██╔══╝  ██║██╔══╝  ██║     ██║      ██║   ██║██║  ██║██║╚██╔╝██║╚════██║
  ██║     ██║███████╗███████╗╚██████╗ ╚██████╔╝██████╔╝██║ ╚═╝ ██║███████║
  ╚═╝     ╚═╝╚══════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝

        EmComm Field Server v1.0  —  Raspberry Pi Installer
BANNER
echo ""

# ── Prerequisites check ────────────────────────────────────────────
step "Checking Prerequisites"

OS=$(lsb_release -si 2>/dev/null || echo "Unknown")
VER=$(lsb_release -sr 2>/dev/null || echo "0")
ARCH=$(uname -m)

info "OS: $OS $VER ($ARCH)"
info "Kernel: $(uname -r)"

if [[ "$OS" != "Raspbian" && "$OS" != "Ubuntu" && "$OS" != "Debian" ]]; then
    warn "Unsupported OS detected. Raspbian/Ubuntu/Debian recommended. Continuing anyway."
fi

RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
RAM_GB=$(( RAM_KB / 1024 / 1024 ))
if [[ $RAM_KB -lt 1048576 ]]; then
    warn "Less than 1 GB RAM detected (${RAM_KB}KB). 2 GB+ recommended."
else
    info "RAM: ${RAM_GB} GB — OK"
fi

DISK_FREE=$(df -BG / | awk 'NR==2 {print $4}' | tr -d 'G')
if [[ $DISK_FREE -lt 4 ]]; then
    warn "Less than 4 GB free disk space (${DISK_FREE}GB available). 8 GB+ recommended."
else
    info "Disk free: ${DISK_FREE} GB — OK"
fi

mkdir -p "$(dirname $FC_LOG)"
touch "$FC_LOG"

# ── Interactive configuration ──────────────────────────────────────
step "Installation Configuration"

echo ""
echo -e "${BOLD}Select installation profile:${NC}"
echo "  1) Full installation (recommended) — all services, WiFi AP, FCC DB"
echo "  2) Server only — Python APIs + web, no WiFi AP config"
echo "  3) Web only — copy HTML files, no Python services"
echo "  4) Update — update files in existing installation"
echo ""
read -rp "Profile [1-4, default=1]: " PROFILE
PROFILE=${PROFILE:-1}

echo ""
read -rp "Station callsign (e.g. W8ABC): " CALLSIGN
CALLSIGN=${CALLSIGN:-W8ABC}
CALLSIGN="${CALLSIGN^^}"

read -rp "Station latitude [42.3153]: " STATION_LAT
STATION_LAT=${STATION_LAT:-42.3153}

read -rp "Station longitude [-88.4473]: " STATION_LON
STATION_LON=${STATION_LON:-88.4473}

read -rp "WiFi AP SSID [EMCOMM-NET]: " AP_SSID
AP_SSID=${AP_SSID:-EMCOMM-NET}

read -rp "WiFi AP password [fieldcomms2026]: " AP_PASS
AP_PASS=${AP_PASS:-fieldcomms2026}

read -rp "Server IP address [192.168.50.1]: " SERVER_IP
SERVER_IP=${SERVER_IP:-192.168.50.1}

if [[ "$PROFILE" == "1" ]]; then
    read -rp "Download FCC amateur database? (~600MB) [y/N]: " DO_FCC
    DO_FCC=${DO_FCC:-N}
fi

if [[ "$PROFILE" == "1" || "$PROFILE" == "2" ]]; then
    echo ""
    echo -e "${BOLD}Offline Map Tiles${NC} (served on port 8083)"
    echo -e "  Downloads map tiles for McHenry County so maps work with no internet."
    echo -e "  Tiles are stored as MBTiles SQLite files on the Pi."
    echo ""
    echo -e "  ${GREEN}1 — Essential${NC}   Z8–Z14  ~8 MB   ~2 min    Overview to street level"
    echo -e "  ${AMBER}2 — Standard${NC}    Z8–Z16  ~180 MB ~25 min   Full street + block detail"
    echo -e "  ${CYAN}3 — Full${NC}         Z8–Z17  ~1.6 GB ~4 hr     Building-level detail"
    echo -e "  ${DIM}0 — Skip (maps use online tiles when available)${NC}"
    echo ""
    read -rp "Map tile preset [0-3, default=1]: " TILE_PRESET
    TILE_PRESET=${TILE_PRESET:-1}
else
    TILE_PRESET=0
fi

if [[ "$PROFILE" == "1" || "$PROFILE" == "2" ]]; then
    echo ""
    echo -e "${BOLD}Kiwix Offline Library${NC} (served on port 8081)"
    echo -e "  Provides offline reference docs to all devices on EMCOMM-NET."
    echo -e "  Requires internet at install time. Downloads can be resumed."
    echo ""
    echo -e "  ${GREEN}1 — Tier 1 Essential${NC}   ~2.5 GB   WikiMed + Wikipedia Mini + Wikivoyage"
    echo -e "  ${AMBER}2 — Tier 2 Extended${NC}    ~10 GB    + Wikibooks + iFixit repair manuals"
    echo -e "  ${CYAN}3 — Tier 3 Full suite${NC}  ~25 GB    + Medical Wikipedia + Wikiversity + Electronics SE"
    echo -e "  ${DIM}0 — Skip downloads (install Kiwix service only, add ZIMs later)${NC}"
    echo ""
    read -rp "Kiwix content tier [0-3, default=1]: " KIWIX_TIER
    KIWIX_TIER=${KIWIX_TIER:-1}
else
    KIWIX_TIER=0
fi

echo ""
echo -e "${BOLD}Configuration summary:${NC}"
echo -e "  Profile:     ${AMBER}$PROFILE${NC}"
echo -e "  Callsign:    ${AMBER}$CALLSIGN${NC}"
echo -e "  Coordinates: ${AMBER}$STATION_LAT, $STATION_LON${NC}"
echo -e "  WiFi SSID:   ${AMBER}$AP_SSID${NC}"
echo -e "  Server IP:   ${AMBER}$SERVER_IP${NC}"
if [[ "${KIWIX_TIER:-0}" != "0" ]]; then
    echo -e "  Kiwix tier:  ${AMBER}Tier ${KIWIX_TIER}${NC}"
else
    echo -e "  Kiwix:       ${DIM}service only (no ZIM downloads)${NC}"
fi
if [[ "${TILE_PRESET:-0}" != "0" ]]; then
    echo -e "  Map tiles:   ${AMBER}Preset ${TILE_PRESET} (McHenry County)${NC}"
else
    echo -e "  Map tiles:   ${DIM}online only (no offline download)${NC}"
fi
echo ""
read -rp "Proceed with installation? [Y/n]: " CONFIRM
CONFIRM=${CONFIRM:-Y}
[[ "$CONFIRM" =~ ^[Yy] ]] || { echo "Installation cancelled."; exit 0; }

# ── Package installation ───────────────────────────────────────────
step "Installing System Packages"

apt-get update -qq 2>>"$FC_LOG" || warn "apt update had warnings"

PACKAGES=(
    python3 python3-pip python3-venv
    nginx sqlite3
    git curl wget unzip
    gpsd gpsd-clients
    # Note: hostapd/dnsmasq NOT installed — Wi-Fi handled by ASUS RT-BE58 Go router
    rsync
)

if [[ "$PROFILE" != "3" ]]; then
    apt-get install -y "${PACKAGES[@]}" 2>>"$FC_LOG" | grep -E "(Inst|already)" || true
    success "System packages installed"
else
    apt-get install -y nginx rsync 2>>"$FC_LOG" | grep -E "(Inst|already)" || true
    success "nginx installed"
fi

# ── System user ────────────────────────────────────────────────────
step "Creating System User"

if ! id "$FC_USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$FC_HOME" "$FC_USER"
    success "Created user: $FC_USER"
else
    info "User $FC_USER already exists"
fi

# ── Directory structure ────────────────────────────────────────────
step "Creating Directory Structure"

dirs=(
    "$FC_HOME"
    "$FC_DATA"
    "$FC_DATA/nets"
    "$FC_DATA/forms"
    "$FC_DATA/ics"
    "$FC_PYTHON"
)

for d in "${dirs[@]}"; do
    mkdir -p "$d"
    success "Created: $d"
done

# ── Python virtualenv ──────────────────────────────────────────────
if [[ "$PROFILE" != "3" ]]; then
    step "Setting Up Python Environment"
    
    if [[ ! -d "$FC_VENV" ]]; then
        python3 -m venv "$FC_VENV"
        success "Virtual environment created"
    else
        info "Virtual environment exists — updating"
    fi
    
    "$FC_VENV/bin/pip" install --quiet --upgrade pip 2>>"$FC_LOG"
    "$FC_VENV/bin/pip" install --quiet flask flask-cors requests gpsd-py3 2>>"$FC_LOG"
    success "Python packages installed: flask, flask-cors, requests, gpsd-py3"
fi

# ── Copy Python files ──────────────────────────────────────────────
if [[ "$PROFILE" != "3" ]]; then
    step "Installing Python Services"
    
    PY_FILES=(
        db.py
        fcc_lookup_server.py
        build_fcc_db.py
        health_monitor.py
        deadmans.py
        fetch_repeaters.py
        ics_platform_server.py
        reference_server.py
        gen_operator_cards.py
        tile_server.py
        amprgate_poll.py
        wan_monitor.py
    )
    
    for f in "${PY_FILES[@]}"; do
        if [[ -f "$SCRIPT_DIR/python/$f" ]]; then
            cp "$SCRIPT_DIR/python/$f" "$FC_PYTHON/$f"
            chmod 755 "$FC_PYTHON/$f"
            success "Installed: $f"
        else
            warn "Not found (skipping): python/$f"
        fi
    done
fi

# ── Copy web files ─────────────────────────────────────────────────
step "Installing Web Frontend"

if [[ -d "$SCRIPT_DIR/html" ]]; then
    rsync -a --delete "$SCRIPT_DIR/html/" "$FC_WEB/" 2>>"$FC_LOG"
    success "HTML files deployed to $FC_WEB"
else
    error "html/ directory not found in $SCRIPT_DIR"
fi

# Patch station config into HTML files
info "Patching station configuration into HTML files..."
find "$FC_WEB" -name "*.html" | while read -r f; do
    sed -i "s/STATION_LAT *= *42\.3153/STATION_LAT = $STATION_LAT/g" "$f"
    sed -i "s/STATION_LON *= *-88\.4473/STATION_LON = $STATION_LON/g" "$f"
    sed -i "s/W8ABC/$CALLSIGN/g" "$f"
done
success "Station configuration patched (callsign: $CALLSIGN, lat/lon: $STATION_LAT/$STATION_LON)"

# ── Systemd services ───────────────────────────────────────────────
if [[ "$PROFILE" != "3" ]]; then
    step "Installing Systemd Services"
    
    SERVICES=(
        fcc-lookup.service
        health-monitor.service
        deadmans.service
        ics-platform.service
        fcc-refresh.service
        fcc-refresh.timer
        repeater-refresh.service
        repeater-refresh.timer
        fieldcomms-backup@.service
        fieldcomms-refs.service
        pat.service
        amprgate-poll.service
        wan-monitor.service
    )
    
    for f in "${SERVICES[@]}"; do
        if [[ -f "$SCRIPT_DIR/systemd/$f" ]]; then
            cp "$SCRIPT_DIR/systemd/$f" "/etc/systemd/system/$f"
            success "Installed: $f"
        else
            warn "Not found (skipping): systemd/$f"
        fi
    done
    
    systemctl daemon-reload
    
    for svc in fcc-lookup health-monitor deadmans ics-platform amprgate-poll wan-monitor; do
        systemctl enable "$svc.service" 2>>"$FC_LOG" && success "Enabled: $svc"
    done
    
    systemctl enable fcc-refresh.timer 2>>"$FC_LOG" && success "Enabled: fcc-refresh.timer"
    systemctl enable repeater-refresh.timer 2>>"$FC_LOG" && success "Enabled: repeater-refresh.timer"
fi

# ── nginx configuration ────────────────────────────────────────────
step "Configuring Firewall (ufw)"
if command -v ufw &>/dev/null; then
    ufw allow 22/tcp    comment "SSH"        2>>"$FC_LOG" || true
    ufw allow 80/tcp    comment "nginx HTTP" 2>>"$FC_LOG" || true
    ufw allow 5050/tcp  comment "FCC Lookup API"    2>>"$FC_LOG" || true
    ufw allow 5051/tcp  comment "Health Monitor"    2>>"$FC_LOG" || true
    ufw allow 5055/tcp  comment "ICS Platform API"  2>>"$FC_LOG" || true
    ufw allow 5056/tcp  comment "Reference Library" 2>>"$FC_LOG" || true
    ufw allow 8080/tcp  comment "Graywolf APRS"     2>>"$FC_LOG" || true
    ufw allow 8081/tcp  comment "Kiwix Library"     2>>"$FC_LOG" || true
    ufw allow 8082/tcp  comment "YAAC APRS"         2>>"$FC_LOG" || true
    ufw allow 8083/tcp  comment "Tile Server"       2>>"$FC_LOG" || true
    ufw allow 8090/tcp  comment "Pat Winlink"       2>>"$FC_LOG" || true
    ufw --force enable  2>>"$FC_LOG" && success "Firewall configured (ports 80,5050-5056,8080-8090 open)" || warn "ufw enable failed"
else
    warn "ufw not found — ports may be blocked. Install with: sudo apt-get install ufw"
fi

step "Configuring nginx"

if [[ -f "$SCRIPT_DIR/udev/nginx-fieldcomms.conf" ]]; then
    cp "$SCRIPT_DIR/udev/nginx-fieldcomms.conf" /etc/nginx/sites-available/fieldcomms
    ln -sf /etc/nginx/sites-available/fieldcomms /etc/nginx/sites-enabled/fieldcomms
    rm -f /etc/nginx/sites-enabled/default
    nginx -t 2>>"$FC_LOG" && success "nginx config valid" || warn "nginx config test failed — check manually"
    systemctl enable nginx 2>>"$FC_LOG"
    systemctl restart nginx 2>>"$FC_LOG" && success "nginx restarted"
else
    warn "nginx config not found — using defaults"
    systemctl enable nginx 2>>"$FC_LOG"
fi

# ── WiFi AP configuration ──────────────────────────────────────────
if [[ "$PROFILE" == "1" ]]; then
    step "Configuring Pi 5 Static IP (NetworkManager)"
    info "Wi-Fi is provided by the ASUS RT-BE58 Go router — Pi does NOT run hostapd"
    
    # Find the Ethernet connection name
    ETH_CON=$(nmcli -t -f NAME,TYPE con show | grep ethernet | head -1 | cut -d: -f1)
    if [[ -z "$ETH_CON" ]]; then
        ETH_CON="Wired connection 1"
        warn "Could not detect Ethernet connection name — defaulting to: $ETH_CON"
    fi
    
    info "Setting static IP $SERVER_IP/24 on: $ETH_CON"
    nmcli con mod "$ETH_CON"         ipv4.addresses "$SERVER_IP/24"         ipv4.method manual 2>>"$FC_LOG"         && success "Static IP configured: $SERVER_IP/24 on $ETH_CON"         || warn "nmcli failed — set static IP manually after reboot (see manual Chapter 34.5)"
    
    # Also install the NetworkManager config file for reference
    if [[ -f "$SCRIPT_DIR/udev/NetworkManager-static-ip.conf" ]]; then
        cp "$SCRIPT_DIR/udev/NetworkManager-static-ip.conf"            /opt/fieldcomms/docs/NetworkManager-static-ip.conf
    fi
fi

# ── udev USB backup rule ───────────────────────────────────────────
if [[ "$PROFILE" == "1" || "$PROFILE" == "2" ]]; then
    step "Installing USB Backup Trigger"
    
    if [[ -f "$SCRIPT_DIR/udev/99-fieldcomms-backup.rules" ]]; then
        cp "$SCRIPT_DIR/udev/99-fieldcomms-backup.rules" /etc/udev/rules.d/
        udevadm control --reload-rules 2>>"$FC_LOG" && success "udev USB backup rule installed"
    fi

    # Install TNC udev rules (Digirig, SignaLink, etc.)
    if [[ -f "$SCRIPT_DIR/udev/99-fieldcomms-tnc.rules" ]]; then
        cp "$SCRIPT_DIR/udev/99-fieldcomms-tnc.rules" /etc/udev/rules.d/
        udevadm control --reload-rules 2>>"$FC_LOG" && success "udev TNC rules installed — /dev/tnc0 symlink will auto-create on plug-in"
    fi
fi

# ── Kiwix offline library ──────────────────────────────────────────
if [[ "$PROFILE" == "1" || "$PROFILE" == "2" ]]; then
    step "Installing Kiwix Offline Library"

    KIWIX_TIER="${KIWIX_TIER:-0}"

    # Copy kiwix.service unit
    if [[ -f "$SCRIPT_DIR/../systemd/kiwix.service" ]]; then
        cp "$SCRIPT_DIR/../systemd/kiwix.service" /etc/systemd/system/kiwix.service
        success "Installed kiwix.service"
    fi

    # Copy the kiwix_setup script to the Pi
    if [[ -f "$SCRIPT_DIR/kiwix_setup.sh" ]]; then
        cp "$SCRIPT_DIR/kiwix_setup.sh" /opt/fieldcomms/scripts/kiwix_setup.sh
        chmod +x /opt/fieldcomms/scripts/kiwix_setup.sh
        success "Installed kiwix_setup.sh → /opt/fieldcomms/scripts/"
    fi

    # Run kiwix setup (install packages, create user/dirs, write service)
    # Pass --tier with --no-prompt so it handles everything non-interactively
    if [[ -f "/opt/fieldcomms/scripts/kiwix_setup.sh" ]]; then
        if [[ "$KIWIX_TIER" != "0" ]]; then
            info "Running Kiwix setup with Tier ${KIWIX_TIER} content…"
            info "This will download up to $([ "$KIWIX_TIER" -eq 1 ] && echo "~2.5 GB" || [ "$KIWIX_TIER" -eq 2 ] && echo "~10 GB" || echo "~25 GB") of ZIM files."
            info "Large downloads may take 30–120 minutes depending on your connection."
            info "If interrupted, re-run: sudo bash /opt/fieldcomms/scripts/kiwix_setup.sh --tier ${KIWIX_TIER}"
            echo ""
            bash /opt/fieldcomms/scripts/kiwix_setup.sh --tier "$KIWIX_TIER" --no-prompt \
                2>>"$FC_LOG" && success "Kiwix setup complete" || \
                warn "Kiwix setup had errors — check $FC_LOG and re-run kiwix_setup.sh"
        else
            # Install service and packages only, no downloads
            info "Installing Kiwix service (no ZIM downloads — run kiwix_setup.sh later)"
            bash /opt/fieldcomms/scripts/kiwix_setup.sh --tier 0 --no-prompt \
                2>>"$FC_LOG" && success "Kiwix service installed" || \
                warn "Kiwix service install had issues — check $FC_LOG"
        fi
    else
        warn "kiwix_setup.sh not found — install Kiwix manually"
        info "Download ZIMs later: sudo bash /opt/fieldcomms/scripts/kiwix_setup.sh"
    fi
fi

# ── GPS configuration ──────────────────────────────────────────────
if [[ "$PROFILE" == "1" || "$PROFILE" == "2" ]]; then
    step "Configuring GPS (gpsd)"

    # Install gpsd udev rules for common GPS devices
    if [[ -f "$SCRIPT_DIR/../udev/99-fieldcomms-gps.rules" ]]; then
        cp "$SCRIPT_DIR/../udev/99-fieldcomms-gps.rules" \
           /etc/udev/rules.d/99-fieldcomms-gps.rules
        udevadm control --reload-rules 2>>"$FC_LOG"
        success "GPS udev rules installed — /dev/gps0 symlink will auto-create on plug-in"
    fi

    # Write gpsd default config
    if [[ -f "$SCRIPT_DIR/../udev/gpsd.conf" ]]; then
        cp "$SCRIPT_DIR/../udev/gpsd.conf" /etc/default/gpsd
        success "gpsd config written: /etc/default/gpsd"
    fi

    # Detect if a GPS is already connected
    GPS_DEVICE=""
    for dev in /dev/ttyUSB0 /dev/ttyUSB1 /dev/ttyACM0 /dev/ttyACM1 /dev/ttyAMA0; do
        if [[ -e "$dev" ]]; then
            info "Detected serial device: $dev (may be GPS)"
            GPS_DEVICE="$dev"
            break
        fi
    done

    if [[ -n "$GPS_DEVICE" ]]; then
        info "Configuring gpsd to use: $GPS_DEVICE"
        sed -i "s|DEVICES=\"/dev/gps0\"|DEVICES=\"$GPS_DEVICE\"|" /etc/default/gpsd
        # Also create the symlink manually if udev hasn't yet
        ln -sf "$GPS_DEVICE" /dev/gps0 2>/dev/null || true
    else
        info "No GPS device detected yet."
        info "Plug in your USB GPS receiver — it will be auto-detected via udev."
        info "Supported: GlobalSat BU-353, u-blox NEO-6/7/8, Adafruit Ultimate GPS, VK-162"
    fi

    # Write station config with installer-provided coordinates as fallback
    STATION_CONFIG_DIR="$FC_DATA"
    mkdir -p "$STATION_CONFIG_DIR"
    cat > "$STATION_CONFIG_DIR/station_config.json" << SCONF
{
  "callsign": "$CALLSIGN",
  "lat": $STATION_LAT,
  "lon": $STATION_LON,
  "gps_enabled": true,
  "gps_device": "${GPS_DEVICE:-/dev/gps0}",
  "configured_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
SCONF
    success "Station config written: $STATION_CONFIG_DIR/station_config.json"

    # Enable and start gpsd
    systemctl enable gpsd 2>>"$FC_LOG" && success "gpsd enabled"
    systemctl restart gpsd 2>>"$FC_LOG" || warn "gpsd restart failed — attach GPS and restart: sudo systemctl restart gpsd"

    # Test gpsd connection
    sleep 1
    if timeout 3 bash -c 'echo "?WATCH={\"enable\":true}" | nc -q1 127.0.0.1 2947' \
       &>/dev/null 2>&1; then
        success "gpsd is responding on port 2947"
    else
        info "gpsd not yet responding (normal if no GPS attached)"
        info "Once GPS is connected: sudo systemctl restart gpsd"
        info "Test with: gpspipe -w -n 5"
    fi
fi

# ── Offline map tiles ──────────────────────────────────────────────
if [[ "$PROFILE" == "1" || "$PROFILE" == "2" ]]; then
    step "Installing Offline Map Tile System"

    TILE_PRESET="${TILE_PRESET:-0}"

    # Copy tile server Python script
    cp "$SCRIPT_DIR/../python/tile_server.py" "$FC_PYTHON/tile_server.py"
    chmod 755 "$FC_PYTHON/tile_server.py"
    success "Installed: tile_server.py"

    # Copy tile download script
    if [[ -f "$SCRIPT_DIR/download_tiles.sh" ]]; then
        cp "$SCRIPT_DIR/download_tiles.sh" "$FC_HOME/scripts/download_tiles.sh"
        chmod +x "$FC_HOME/scripts/download_tiles.sh"
        success "Installed: download_tiles.sh"
    fi

    # Copy lib/ files to web lib directory (belt-and-suspenders — rsync above should cover it
    # but explicit copies ensure these critical shared files are never missing)
    mkdir -p "$FC_WEB/lib"
    if [[ -f "$SCRIPT_DIR/../html/lib/tiles.js" ]]; then
        cp "$SCRIPT_DIR/../html/lib/tiles.js" "$FC_WEB/lib/tiles.js"
        success "Installed: lib/tiles.js"
    fi
    if [[ -f "$SCRIPT_DIR/../html/lib/identity.js" ]]; then
        cp "$SCRIPT_DIR/../html/lib/identity.js" "$FC_WEB/lib/identity.js"
        success "Installed: lib/identity.js"
    fi

    # Create tile storage directory
    mkdir -p "$FC_HOME/tiles"
    chown "${FC_USER}:${FC_USER}" "$FC_HOME/tiles"
    success "Created: $FC_HOME/tiles/"

    # Install systemd service
    if [[ -f "$SCRIPT_DIR/../systemd/fieldcomms-tiles.service" ]]; then
        cp "$SCRIPT_DIR/../systemd/fieldcomms-tiles.service" \
           /etc/systemd/system/fieldcomms-tiles.service
        systemctl daemon-reload
        systemctl enable fieldcomms-tiles 2>>"$FC_LOG"
        success "Installed: fieldcomms-tiles.service (port 8083)"
    fi

    # Download tiles if requested
    if [[ "$TILE_PRESET" != "0" ]]; then
        case "$TILE_PRESET" in
            1) TILE_FLAGS="--mchenry-essential" ;;
            2) TILE_FLAGS="--mchenry-standard" ;;
            3) TILE_FLAGS="--area mchenry --zoom 8-17 --sources usgs_topo,esri_street,esri_imagery" ;;
        esac

        info "Downloading McHenry County map tiles (Preset ${TILE_PRESET})…"
        info "If interrupted, re-run: sudo bash $FC_HOME/scripts/download_tiles.sh"

        # Run as fieldcomms user can't write to tile dir yet — run as root
        bash "$FC_HOME/scripts/download_tiles.sh" $TILE_FLAGS --no-prompt \
            2>>"$FC_LOG" && success "Map tiles downloaded" || \
            warn "Tile download had issues — re-run download_tiles.sh to retry"
    else
        info "Skipping tile download — maps will use online sources when available"
        info "Download tiles later: sudo bash $FC_HOME/scripts/download_tiles.sh"
    fi
fi

# ── Pat Winlink ────────────────────────────────────────────────────
step "Installing Pat Winlink (backup Winlink client on port 8090)"
info "Pat is the browser-based Winlink backup client. Primary Winlink = Winlink Express on Windows."

PAT_VER="1.0.0"
ARCH=$(dpkg --print-architecture 2>/dev/null || uname -m)
case "$ARCH" in
    arm64|aarch64) PAT_DEB="pat_${PAT_VER}_linux_arm64.deb" ;;
    armhf|armv7l)  PAT_DEB="pat_${PAT_VER}_linux_armhf.deb" ;;
    amd64|x86_64)  PAT_DEB="pat_${PAT_VER}_linux_amd64.deb" ;;
    *)             PAT_DEB="pat_${PAT_VER}_linux_arm64.deb"
                   warn "Unknown arch $ARCH — defaulting to arm64 .deb" ;;
esac

PAT_URL="https://github.com/la5nta/pat/releases/download/v${PAT_VER}/${PAT_DEB}"
PAT_TMP="/tmp/${PAT_DEB}"

info "Downloading Pat v${PAT_VER} (${ARCH})..."
if wget -q --show-progress -O "$PAT_TMP" "$PAT_URL" 2>>"$FC_LOG"; then
    if dpkg -i "$PAT_TMP" 2>>"$FC_LOG"; then
        success "Pat installed: $(pat --version 2>/dev/null | head -1)"
        rm -f "$PAT_TMP"

        # Write Pat config — fieldcomms user's home is /opt/fieldcomms (not /home/fieldcomms)
        PAT_CFG_DIR="$FC_HOME/.config/pat"
        mkdir -p "$PAT_CFG_DIR"
        if [[ ! -f "$PAT_CFG_DIR/config.json" ]]; then
            cat > "$PAT_CFG_DIR/config.json" << PATCFG
{
  "mycall": "${CALLSIGN}",
  "secure_login_password": "",
  "locator": "",
  "http_addr": "0.0.0.0:8090",
  "motd": ["Incident Management EmComm Server — K9ESV"],
  "connect_aliases": {},
  "listen": ["http"],
  "ax25": {"port": ""},
  "serial_tnc": {"path": "", "baudrate": 0},
  "vara": {"host": "localhost", "cmdPort": 8300, "dataPort": 8301},
  "gpsd": {"enable_auto_locator": false, "addr": "localhost:2947"}
}
PATCFG
            chown -R "$FC_USER:$FC_USER" "$PAT_CFG_DIR"
            success "Pat config written ($PAT_CFG_DIR, callsign: $CALLSIGN)"
        else
            info "Pat config already exists — skipping"
        fi

        # Install and enable pat.service
        if [[ -f "$SCRIPT_DIR/systemd/pat.service" ]]; then
            cp "$SCRIPT_DIR/systemd/pat.service" /etc/systemd/system/pat.service
            systemctl daemon-reload
            systemctl enable pat.service 2>>"$FC_LOG" && success "pat.service enabled"
        else
            warn "pat.service not found in systemd/ — Pat will not start automatically"
        fi
    else
        warn "Pat .deb install failed — Pat will not be available. Try manually: dpkg -i $PAT_TMP"
    fi
else
    warn "Could not download Pat (needs internet). Install manually after deployment:"
    warn "  wget $PAT_URL && sudo dpkg -i ${PAT_DEB}"
fi

# ── CUPS Print Server ──────────────────────────────────────────────────────
if [[ "${SKIP_CUPS:-0}" != "1" ]]; then
    step "Installing CUPS Print Server"
    info "CUPS allows a USB printer on the Pi to be shared across EMCOMM-NET"
    info "Skip with SKIP_CUPS=1 if printing is not needed"

    if apt-get install -y cups cups-bsd cups-client \
        printer-driver-gutenprint avahi-daemon 2>>"$FC_LOG"; then
        success "CUPS and printer drivers installed"

        # Add fieldcomms user and www-data to lpadmin group
        usermod -aG lpadmin "$FC_USER" 2>>"$FC_LOG" || true
        usermod -aG lpadmin www-data 2>>"$FC_LOG" || true

        # Allow CUPS to be managed remotely from EMCOMM-NET (192.168.50.x)
        # Listen on all interfaces so field devices can reach the web UI
        if [[ -f /etc/cups/cupsd.conf ]]; then
            # Back up original
            cp /etc/cups/cupsd.conf /etc/cups/cupsd.conf.bak

            # Allow remote access from EMCOMM-NET subnet
            python3 - << 'CUPSPY'
import re

with open('/etc/cups/cupsd.conf', 'r') as f:
    cfg = f.read()

# Listen on all interfaces (not just localhost)
cfg = re.sub(r'Listen localhost:631', 'Listen 0.0.0.0:631', cfg)
cfg = re.sub(r'Port 631\nListen /var/run/cups/cups.sock',
             'Port 631\nListen /var/run/cups/cups.sock', cfg)

# Add EMCOMM-NET access to server policy if not present
if '192.168.50.' not in cfg:
    cfg = cfg.replace(
        '<Location />\n  Order allow,deny\n</Location>',
        '<Location />\n  Order allow,deny\n  Allow from 127.0.0.1\n  Allow from 192.168.50.*\n</Location>'
    )
    cfg = cfg.replace(
        '<Location /admin>\n  Order allow,deny\n</Location>',
        '<Location /admin>\n  Order allow,deny\n  Allow from 127.0.0.1\n  Allow from 192.168.50.*\n</Location>'
    )

with open('/etc/cups/cupsd.conf', 'w') as f:
    f.write(cfg)
print("cupsd.conf updated")
CUPSPY
        fi

        # Enable Bonjour/mDNS printer sharing (for automatic discovery)
        cupsctl --share-printers --remote-printers 2>>"$FC_LOG" || true

        # Open CUPS web admin port in firewall
        ufw allow 631/tcp comment "CUPS printer admin" 2>>"$FC_LOG" || true

        # Enable and start CUPS + Avahi
        systemctl enable cups avahi-daemon 2>>"$FC_LOG"
        systemctl restart cups avahi-daemon 2>>"$FC_LOG" \
            && success "CUPS started — admin UI at http://192.168.50.1:631" \
            || warn "CUPS start failed — check: journalctl -u cups"

        info "After connecting a USB printer, add it at: http://192.168.50.1:631"
        info "Then share it so all EMCOMM-NET devices can print to it"
    else
        warn "CUPS install failed — printing will not be available via the Pi"
    fi
else
    info "Skipping CUPS installation (SKIP_CUPS=1)"
    info "Install manually: sudo apt install cups cups-bsd printer-driver-gutenprint avahi-daemon"
fi

# ── APRS Clients — YAAC and Graywolf ──────────────────────────────────────
if [[ "${SKIP_APRS:-0}" != "1" ]]; then
    step "Installing APRS Clients (YAAC + Graywolf)"
    info "Both are optional — skip with SKIP_APRS=1 if APRS is not needed"

    # ── Java runtime (required by both YAAC and Graywolf) ──────────────────
    info "Installing Java runtime (required by YAAC and Graywolf)..."
    if apt-get install -y default-jre 2>>"$FC_LOG"; then
        success "Java installed: $(java -version 2>&1 | head -1)"
    else
        warn "Java install failed — YAAC and Graywolf will not run without it"
    fi

    # ── YAAC — Yet Another APRS Client ─────────────────────────────────────
    YAAC_DIR="/opt/yaac"
    YAAC_JAR="$YAAC_DIR/YAAC.jar"
    YAAC_URL="http://www.ka2ddo.org/ka2ddo/YAAC.zip"

    if [[ ! -f "$YAAC_JAR" ]]; then
        info "Downloading YAAC from ka2ddo.org..."
        mkdir -p "$YAAC_DIR"
        YAAC_TMP="/tmp/YAAC.zip"
        if wget -q --show-progress -O "$YAAC_TMP" "$YAAC_URL" 2>>"$FC_LOG"; then
            if unzip -q "$YAAC_TMP" "*.jar" -d "$YAAC_DIR" 2>>"$FC_LOG"; then
                # YAAC.jar may be nested — find and move it
                find "$YAAC_DIR" -name "YAAC.jar" ! -path "$YAAC_JAR" -exec mv {} "$YAAC_JAR" \; 2>/dev/null
                chown -R "$FC_USER:$FC_USER" "$YAAC_DIR"
                rm -f "$YAAC_TMP"
                success "YAAC installed: $YAAC_JAR"
            else
                warn "YAAC unzip failed — install manually: unzip YAAC.zip to /opt/yaac/"
            fi
        else
            warn "Could not download YAAC — install manually after deployment:"
            warn "  wget $YAAC_URL && sudo unzip YAAC.zip -d /opt/yaac/"
        fi
    else
        info "YAAC already installed — skipping"
    fi

    # Install and enable yaac.service
    if [[ -f "$YAAC_JAR" && -f "$SCRIPT_DIR/systemd/yaac.service" ]]; then
        cp "$SCRIPT_DIR/systemd/yaac.service" /etc/systemd/system/yaac.service
        systemctl daemon-reload
        systemctl enable yaac.service 2>>"$FC_LOG" \
            && success "yaac.service enabled" \
            || warn "yaac.service enable failed — enable manually: systemctl enable yaac"
    fi

    # ── YAAC Post-install note ──────────────────────────────────────────────
    info "YAAC requires manual port configuration before first use:"
    info "  Run YAAC once on a desktop: java -jar /opt/yaac/YAAC.jar"
    info "  File → Configure → Web Server tab"
    info "  Set port to 8082 · Enable REST API · Enable WebSocket · Save"
    info "  After saving config, yaac.service will use these settings headlessly"

    # ── Graywolf APRS ───────────────────────────────────────────────────────
    # Graywolf is a TNC/APRS client with REST API (port 8080) and WebSocket.
    # It is distributed as a self-contained JAR — check GitHub for latest release.
    GRAY_DIR="/opt/graywolf"
    GRAY_JAR="$GRAY_DIR/graywolf.jar"
    # NOTE: Update this URL when a new Graywolf release is available
    GRAY_URL="https://github.com/vk2tds/graywolf/releases/latest/download/graywolf.jar"

    if [[ ! -f "$GRAY_JAR" ]]; then
        info "Downloading Graywolf APRS client..."
        mkdir -p "$GRAY_DIR"
        if wget -q --show-progress -O "$GRAY_JAR" "$GRAY_URL" 2>>"$FC_LOG"; then
            chown -R "$FC_USER:$FC_USER" "$GRAY_DIR"
            success "Graywolf installed: $GRAY_JAR"

            # Write Graywolf systemd service
            cat > /etc/systemd/system/graywolf.service << 'GWSVC'
[Unit]
Description=Graywolf APRS Client (Port 8080)
After=network.target

[Service]
Type=simple
User=fieldcomms
Group=fieldcomms
WorkingDirectory=/opt/graywolf
ExecStart=/usr/bin/java -jar /opt/graywolf/graywolf.jar --port 8080 --nogui
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=graywolf

[Install]
WantedBy=multi-user.target
GWSVC
            systemctl daemon-reload
            systemctl enable graywolf.service 2>>"$FC_LOG" \
                && success "graywolf.service created and enabled" \
                || warn "graywolf.service enable failed"
        else
            warn "Could not download Graywolf — install manually after deployment:"
            warn "  See https://github.com/vk2tds/graywolf for the latest release"
            warn "  Place graywolf.jar in /opt/graywolf/ and enable graywolf.service"
            # Write service file anyway so it is ready when Graywolf is installed
            cat > /etc/systemd/system/graywolf.service << 'GWSVC'
[Unit]
Description=Graywolf APRS Client (Port 8080)
After=network.target

[Service]
Type=simple
User=fieldcomms
Group=fieldcomms
WorkingDirectory=/opt/graywolf
ExecStart=/usr/bin/java -jar /opt/graywolf/graywolf.jar --port 8080 --nogui
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=graywolf

[Install]
WantedBy=multi-user.target
GWSVC
            systemctl daemon-reload
        fi
    else
        info "Graywolf already installed — skipping"
    fi

else
    info "Skipping APRS client installation (SKIP_APRS=1)"
    info "Install manually later:"
    info "  sudo apt install default-jre"
    info "  sudo mkdir /opt/yaac && wget http://www.ka2ddo.org/ka2ddo/YAAC.zip"
    info "  sudo unzip YAAC.zip -d /opt/yaac/ && sudo systemctl enable yaac"
fi

# ── Set permissions ────────────────────────────────────────────────
step "Setting Permissions"

chown -R "$FC_USER:$FC_USER" "$FC_HOME"
chown -R www-data:www-data "$FC_WEB"
chmod -R 755 "$FC_WEB"
chmod -R 770 "$FC_DATA"
usermod -aG "$FC_USER" www-data 2>>/dev/null || true
success "Permissions set"

# ── ICS PDF forms download ─────────────────────────────────────────────────
if [[ "${SKIP_ICS_PDF:-0}" != "1" ]]; then
    step "Downloading FEMA ICS Forms PDFs"
    info "Downloads 22 official FEMA ICS forms — requires internet connection"
    info "Skip with:  SKIP_ICS_PDF=1 bash install.sh"
    mkdir -p "$FC_DATA/ics_forms"
    if "$FC_HOME/venv/bin/python" "$FC_HOME/python/ics_pdf_downloader.py" \
        --output "$FC_DATA/ics_forms" >> "$FC_LOG" 2>&1; then
        success "ICS forms downloaded to $FC_DATA/ics_forms/"
    else
        warn "Some ICS forms failed — run manually after deployment:"
        warn "  python3 $FC_HOME/python/ics_pdf_downloader.py"
    fi
else
    info "Skipping ICS PDF download (SKIP_ICS_PDF=1)"
fi

# ── Theme consistency check ────────────────────────────────────────────────
step "Verifying HTML Theme Consistency"
if "$FC_HOME/venv/bin/python" "$FC_HOME/python/apply_theme.py" \
    --dir "$FC_WEB" --check >> "$FC_LOG" 2>&1; then
    success "All HTML files have correct theme variables"
else
    info "Applying theme fixes..."
    "$FC_HOME/venv/bin/python" "$FC_HOME/python/apply_theme.py" \
        --dir "$FC_WEB" --apply >> "$FC_LOG" 2>&1
    success "Theme variables applied"
fi

# ── FCC database download ──────────────────────────────────────────
if [[ "${DO_FCC:-N}" =~ ^[Yy] ]]; then
    step "Downloading FCC Amateur Database"
    info "This will download ~600MB from FCC.gov and build the SQLite database."
    info "This may take 10–20 minutes on a Raspberry Pi."
    
    if sudo -u "$FC_USER" "$FC_VENV/bin/python" "$FC_PYTHON/build_fcc_db.py" 2>>"$FC_LOG"; then
        success "FCC database built: $FC_DATA/fcc.db"
    else
        warn "FCC database build failed. Run manually: sudo -u fieldcomms $FC_VENV/bin/python $FC_PYTHON/build_fcc_db.py"
    fi
fi

# ── Start services ─────────────────────────────────────────────────
if [[ "$PROFILE" != "3" ]]; then
    step "Starting Services"
    
    for svc in fcc-lookup health-monitor deadmans ics-platform fieldcomms-tiles fieldcomms-refs amprgate-poll wan-monitor; do
        if systemctl start "$svc.service" 2>>"$FC_LOG"; then
            success "Started: $svc"
        else
            warn "Failed to start $svc — check: journalctl -u $svc"
        fi
    done
    
    systemctl start fcc-refresh.timer 2>>"$FC_LOG" && success "Started: fcc-refresh.timer"
    systemctl start repeater-refresh.timer 2>>"$FC_LOG" && success "Started: repeater-refresh.timer"
fi

# ── Done ───────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║           FieldComms Installation Complete!              ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BOLD}Access the dashboard:${NC}"
echo -e "  Local:    ${CYAN}http://localhost/${NC}"
echo -e "  Network:  ${CYAN}http://$SERVER_IP/${NC}"
if [[ "$PROFILE" == "1" ]]; then
    echo -e "  WiFi:     Connect to ${CYAN}$AP_SSID${NC} (password: $AP_PASS)"
    echo -e "            Then browse to ${CYAN}http://$SERVER_IP/${NC}"
fi
echo ""
echo -e "${BOLD}Service status:${NC}"
echo -e "  ${CYAN}systemctl status fcc-lookup health-monitor deadmans ics-platform${NC}"
echo ""
echo -e "${BOLD}Logs:${NC}"
echo -e "  ${CYAN}journalctl -fu fcc-lookup${NC}"
echo -e "  ${CYAN}journalctl -fu ics-platform${NC}"
echo -e "  Install log: ${CYAN}$FC_LOG${NC}"
echo ""
echo -e "${BOLD}AMPRNet / 44Net Gateway:${NC}"
echo -e "  Gateway Pi:   ${CYAN}http://192.168.50.2:9000${NC}  (configure separately)"
echo -e "  This Pi:      ${CYAN}http://$SERVER_IP/amprgate.html${NC}"
echo -e "  Setup guide:  ${CYAN}sudo bash scripts/setup_44net.sh${NC}  (run on gateway Pi)"
echo -e "  See Installation Guide Step 11 for complete setup instructions."
echo ""
echo -e "${BOLD}FCC Database (if not downloaded):${NC}"
echo -e "  ${CYAN}sudo -u fieldcomms $FC_VENV/bin/python $FC_PYTHON/build_fcc_db.py${NC}"
echo ""
echo -e "${BOLD}Offline Map Tiles (port 8083):${NC}"
if [[ "${TILE_PRESET:-0}" != "0" ]]; then
    echo -e "  ${GREEN}✓${NC} McHenry County tiles downloaded — ${CYAN}http://$SERVER_IP:8083/${NC}"
else
    echo -e "  ${AMBER}No tiles downloaded. Maps use online tiles when available.${NC}"
fi
echo -e "  Download tiles: ${CYAN}sudo bash /opt/fieldcomms/scripts/download_tiles.sh${NC}"
echo -e "  List options:   ${CYAN}sudo bash /opt/fieldcomms/scripts/download_tiles.sh --list${NC}"
echo ""
if [[ "${KIWIX_TIER:-0}" != "0" ]]; then
    echo -e "  ${GREEN}✓${NC} Tier ${KIWIX_TIER} ZIMs installed — ${CYAN}http://$SERVER_IP:8081${NC}"
else
    echo -e "  ${AMBER}Service installed, no ZIMs downloaded yet.${NC}"
fi
echo -e "  Add/update ZIMs: ${CYAN}sudo bash /opt/fieldcomms/scripts/kiwix_setup.sh${NC}"
echo -e "  List available:  ${CYAN}sudo bash /opt/fieldcomms/scripts/kiwix_setup.sh --list${NC}"
echo ""
if [[ "$PROFILE" == "1" ]]; then
    echo -e "${AMBER}Reboot recommended to activate WiFi AP and all services.${NC}"
    read -rp "Reboot now? [y/N]: " DO_REBOOT
    [[ "$DO_REBOOT" =~ ^[Yy] ]] && reboot
fi

exit 0
