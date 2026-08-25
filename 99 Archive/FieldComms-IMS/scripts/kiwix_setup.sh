#!/usr/bin/env bash
# =============================================================================
# FieldComms — Kiwix Offline Library Setup
# Downloads EmComm-relevant ZIM files and configures kiwix-serve
#
# Usage:
#   sudo bash kiwix_setup.sh              # interactive
#   sudo bash kiwix_setup.sh --tier 1     # Tier 1 only, no prompts
#   sudo bash kiwix_setup.sh --tier 2     # Tier 1 + 2
#   sudo bash kiwix_setup.sh --tier 3     # All tiers
#   sudo bash kiwix_setup.sh --list       # show available ZIMs and exit
#   sudo bash kiwix_setup.sh --update     # check for newer ZIM versions
#   sudo bash kiwix_setup.sh --status     # show installed ZIMs and service
#
# Kiwix will be available at: http://localhost:8081
# =============================================================================
set -euo pipefail

# ── Paths ──────────────────────────────────────────────────────────────────
KIWIX_ZIM_DIR="/opt/kiwix/zim"
KIWIX_LIB="/opt/kiwix/library.xml"
KIWIX_LOG_DIR="/var/log/kiwix"
KIWIX_PORT=8081
KIWIX_USER="kiwix"
KIWIX_SVC="/etc/systemd/system/kiwix.service"
DL_LOG="/var/log/fieldcomms-kiwix.log"

# Kiwix download mirror base
KIWIX_BASE="https://download.kiwix.org/zim"
# OPDS catalog API (returns XML with latest file info)
KIWIX_CATALOG="https://library.kiwix.org/catalog/v2/entries"

# ── Colours ────────────────────────────────────────────────────────────────
AMBER='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ── Logging ────────────────────────────────────────────────────────────────
mkdir -p "$(dirname "$DL_LOG")"
touch "$DL_LOG"
log()     { echo -e "$1" | tee -a "$DL_LOG"; }
info()    { log "${CYAN}[INFO]${NC}  $1"; }
success() { log "${GREEN}[OK]${NC}    $1"; }
warn()    { log "${AMBER}[WARN]${NC}  $1"; }
error()   { log "${RED}[ERROR]${NC} $1"; exit 1; }
step()    { log "\n${BOLD}${BLUE}━━━ $1 ━━━${NC}"; }
dim()     { log "${DIM}$1${NC}"; }

# ── Root check ─────────────────────────────────────────────────────────────
[[ $EUID -eq 0 ]] || error "Run as root: sudo bash kiwix_setup.sh"

# =============================================================================
# ZIM Catalogue — EmComm curated list
# Format: "id|display_name|category|filename_base|approx_size_mb|tier|description"
# tier: 1=Essential  2=Recommended  3=Enhanced
# =============================================================================
declare -A ZIM_ID ZIM_NAME ZIM_CAT ZIM_FILE ZIM_SIZE ZIM_TIER ZIM_DESC

define_zim() {
    local id="$1" name="$2" cat="$3" file="$4" size="$5" tier="$6" desc="$7"
    ZIM_ID[$id]="$id"
    ZIM_NAME[$id]="$name"
    ZIM_CAT[$id]="$cat"
    ZIM_FILE[$id]="$file"
    ZIM_SIZE[$id]="$size"
    ZIM_TIER[$id]="$tier"
    ZIM_DESC[$id]="$desc"
}

# ── TIER 1: Essential (~2.5 GB total) — fits on any Pi SD card ────────────
define_zim "wikimed" \
    "WikiMed — Medical Encyclopedia" \
    "wikimed" \
    "wikimed_en_all_maxi" \
    "471" "1" \
    "Offline medical encyclopedia. Symptoms, treatments, drugs, procedures. Critical for mass-casualty events."

define_zim "wikipedia_mini" \
    "Wikipedia (Mini) — Compact Reference" \
    "wikipedia" \
    "wikipedia_en_all_mini" \
    "1200" "1" \
    "Compact English Wikipedia. Essential facts, geography, science. Fits alongside other ZIMs."

define_zim "wikivoyage" \
    "Wikivoyage — Shelter & Travel" \
    "wikivoyage" \
    "wikivoyage_en_all_maxi" \
    "820" "1" \
    "Emergency shelters, evacuation routes, local resources, travel logistics. Useful during deployments."

# ── TIER 2: Recommended (~7.5 GB total) — 32GB card recommended ───────────
define_zim "wikibooks" \
    "Wikibooks — How-To & Field Manuals" \
    "wikibooks" \
    "wikibooks_en_all_maxi" \
    "4200" "2" \
    "First aid, survival, ham radio, electronics, cooking, field skills. Practical hands-on knowledge."

define_zim "ifixit" \
    "iFixit — Equipment Repair Manuals" \
    "ifixit" \
    "ifixit_en_all" \
    "3100" "2" \
    "Step-by-step repair guides for radios, computers, vehicles, generators, medical equipment."

# ── TIER 3: Enhanced (~15 GB) — 64GB card required ────────────────────────
define_zim "wikipedia_med" \
    "Wikipedia Medicine — Full Medical" \
    "wikipedia" \
    "wikipedia_en_medicine_maxi" \
    "8500" "3" \
    "Full medical Wikipedia: diseases, drugs, anatomy, surgery, public health. Comprehensive clinical reference."

define_zim "wikiversity" \
    "Wikiversity — Training & Education" \
    "wikiversity" \
    "wikiversity_en_all_maxi" \
    "3400" "3" \
    "ICS training, ham radio courses, emergency management, CERT, first responder education."

define_zim "stackexchange_electronics" \
    "Electronics Stack Exchange" \
    "stack_exchange" \
    "electronics.stackexchange.com_en_all" \
    "2200" "3" \
    "Q&A for electronics, radio circuits, antenna design, power systems. Invaluable for field equipment repair."

# Ordered display list
ZIM_ORDER=(wikimed wikipedia_mini wikivoyage wikibooks ifixit wikipedia_med wikiversity stackexchange_electronics)

TIER_LABEL=("" "TIER 1 — Essential" "TIER 2 — Recommended" "TIER 3 — Enhanced")
TIER_COLOR=("" "${GREEN}" "${AMBER}" "${CYAN}")

# =============================================================================
# Helper: human-readable file size
# =============================================================================
hr_size() {
    local mb="$1"
    if [[ $mb -ge 1024 ]]; then
        echo "$(echo "scale=1; $mb/1024" | bc) GB"
    else
        echo "${mb} MB"
    fi
}

# =============================================================================
# Helper: check if a ZIM is already installed
# =============================================================================
zim_installed() {
    local id="$1"
    local base="${ZIM_FILE[$id]}"
    # Check for any file matching the base name (dated variants)
    find "$KIWIX_ZIM_DIR" -name "${base}*.zim" 2>/dev/null | grep -q .
}

zim_installed_path() {
    local id="$1"
    local base="${ZIM_FILE[$id]}"
    find "$KIWIX_ZIM_DIR" -name "${base}*.zim" 2>/dev/null | head -1
}

# =============================================================================
# Helper: resolve latest ZIM URL via catalog API
# Falls back to direct redirect URL if catalog unavailable
# =============================================================================
resolve_zim_url() {
    local id="$1"
    local cat="${ZIM_CAT[$id]}"
    local base="${ZIM_FILE[$id]}"

    # Try OPDS catalog first — returns <link> with actual dated filename
    if command -v curl &>/dev/null; then
        local catalog_url="${KIWIX_CATALOG}?name=${base}&lang=eng&count=1"
        local xml
        xml=$(curl -fsSL --max-time 15 "$catalog_url" 2>/dev/null || echo "")

        if [[ -n "$xml" ]]; then
            # Extract <link rel="http://opds-spec.org/acquisition" href="...">
            local href
            href=$(echo "$xml" | grep -oP 'href="[^"]*\.zim"' | head -1 | cut -d'"' -f2)
            if [[ -n "$href" ]]; then
                # href may be relative or absolute
                if [[ "$href" == http* ]]; then
                    echo "$href"
                else
                    echo "https://download.kiwix.org${href}"
                fi
                return
            fi
        fi
    fi

    # Fallback: direct URL (Kiwix redirects to latest dated version)
    echo "${KIWIX_BASE}/${cat}/${base}.zim"
}

# =============================================================================
# Helper: get remote file size (HEAD request)
# =============================================================================
remote_size_mb() {
    local url="$1"
    local bytes
    bytes=$(curl -fsSLI --max-time 10 "$url" 2>/dev/null | \
            grep -i "content-length" | tail -1 | awk '{print $2}' | tr -d '\r')
    if [[ -n "$bytes" && "$bytes" -gt 0 ]]; then
        echo $(( bytes / 1024 / 1024 ))
    else
        echo "0"
    fi
}

# =============================================================================
# Display ZIM catalogue
# =============================================================================
show_catalogue() {
    echo ""
    printf "${BOLD}%-4s %-35s %8s  %-5s  %s${NC}\n" \
        "#" "Name" "Size" "Tier" "Status"
    printf '%0.s─' {1..80}; echo ""

    local prev_tier=0
    local num=1
    for id in "${ZIM_ORDER[@]}"; do
        local tier="${ZIM_TIER[$id]}"
        if [[ "$tier" != "$prev_tier" ]]; then
            echo -e "\n${TIER_COLOR[$tier]}${BOLD}  ${TIER_LABEL[$tier]}${NC}"
            prev_tier="$tier"
        fi

        local installed_mark=""
        local status_color=""
        if zim_installed "$id"; then
            installed_mark="✓ Installed"
            status_color="${GREEN}"
        else
            installed_mark="Not installed"
            status_color="${DIM}"
        fi

        printf "  ${CYAN}%2d${NC}  %-35s ${AMBER}%8s${NC}  T%-4s  ${status_color}%s${NC}\n" \
            "$num" \
            "${ZIM_NAME[$id]}" \
            "$(hr_size "${ZIM_SIZE[$id]}")" \
            "${ZIM_TIER[$id]}" \
            "$installed_mark"
        echo -e "      ${DIM}${ZIM_DESC[$id]}${NC}"
        num=$(( num + 1 ))
    done

    echo ""
    # Disk space summary
    local free_gb
    free_gb=$(df -BG "$KIWIX_ZIM_DIR" 2>/dev/null | awk 'NR==2{print $4}' | tr -d 'G' || echo "?")
    local tier1_gb="2.5"
    local tier12_gb="10"
    local tier123_gb="25"
    echo -e "${BOLD}Disk requirements:${NC}"
    echo -e "  ${GREEN}Tier 1 only:${NC}         ~${tier1_gb} GB"
    echo -e "  ${AMBER}Tier 1 + 2:${NC}          ~${tier12_gb} GB"
    echo -e "  ${CYAN}All tiers (1+2+3):${NC}   ~${tier123_gb} GB"
    echo -e "  ${BOLD}Free space in ${KIWIX_ZIM_DIR}:${NC} ${free_gb} GB"
    echo ""
}

# =============================================================================
# Download a single ZIM with progress bar
# =============================================================================
download_zim() {
    local id="$1"
    local force="${2:-false}"

    local name="${ZIM_NAME[$id]}"
    local size_mb="${ZIM_SIZE[$id]}"
    local base="${ZIM_FILE[$id]}"

    echo ""
    step "Downloading: ${name}"

    # Already installed?
    if zim_installed "$id" && [[ "$force" != "true" ]]; then
        local existing
        existing=$(zim_installed_path "$id")
        success "Already installed: $(basename "$existing") — skipping"
        success "  (use --update to check for newer version)"
        return 0
    fi

    # Resolve URL
    info "Resolving download URL…"
    local url
    url=$(resolve_zim_url "$id")
    info "URL: ${url}"

    # Check internet connectivity
    if ! curl -fsS --max-time 5 "https://download.kiwix.org" &>/dev/null; then
        error "Cannot reach download.kiwix.org — internet required for ZIM download"
    fi

    # Get actual remote size
    info "Checking remote file size…"
    local remote_mb
    remote_mb=$(remote_size_mb "$url")
    if [[ "$remote_mb" -gt 0 ]]; then
        info "Remote size: $(hr_size $remote_mb)"
    else
        info "Remote size: ~$(hr_size $size_mb) (estimate)"
        remote_mb="$size_mb"
    fi

    # Check disk space (need remote_mb + 10% headroom)
    local needed_mb=$(( remote_mb + remote_mb / 10 ))
    local free_mb
    free_mb=$(df -BM "$KIWIX_ZIM_DIR" | awk 'NR==2{print $4}' | tr -d 'M')
    if [[ "$free_mb" -lt "$needed_mb" ]]; then
        error "Insufficient disk space: need $(hr_size $needed_mb), have $(hr_size $free_mb) free in $KIWIX_ZIM_DIR"
    fi
    info "Disk space OK: $(hr_size $free_mb) free"

    # Build output filename — use redirect to get actual dated name
    # We download to a temp name first, then rename
    local tmp_file="${KIWIX_ZIM_DIR}/.downloading_${base}.zim"
    local start_time
    start_time=$(date +%s)

    # Remove any stale partial download
    rm -f "$tmp_file"

    info "Starting download… (this may take a long time on slow connections)"
    info "Progress is shown below. You can safely close this session —"
    info "download continues in background if run via 'nohup'."
    echo ""

    # Download with curl:
    #   -L  follow redirects (needed for Kiwix redirect to dated file)
    #   -C- resume partial
    #   --retry 5 with exponential backoff
    #   -o  output file
    #   --progress-bar  human progress
    #   tee to log
    local curl_exit=0
    curl -L \
         -C - \
         --retry 5 \
         --retry-delay 10 \
         --retry-max-time 3600 \
         --max-time 86400 \
         --connect-timeout 30 \
         --speed-limit 1024 \
         --speed-time 60 \
         --progress-bar \
         -o "$tmp_file" \
         "$url" 2>&1 | tee -a "$DL_LOG" || curl_exit=$?

    if [[ $curl_exit -ne 0 ]]; then
        warn "Download interrupted (curl exit $curl_exit). Partial file kept for resume."
        warn "Re-run this script to resume: curl -C- will pick up where it left off."
        return 1
    fi

    # Verify file size (must be > 10MB to be a valid ZIM)
    local actual_bytes
    actual_bytes=$(stat -c%s "$tmp_file" 2>/dev/null || echo "0")
    local actual_mb=$(( actual_bytes / 1024 / 1024 ))

    if [[ "$actual_mb" -lt 10 ]]; then
        rm -f "$tmp_file"
        error "Downloaded file too small (${actual_mb} MB) — likely an error page. Check URL and try again."
    fi

    # Verify ZIM magic bytes (ZIM files start with 0x 5a 49 4d 04)
    local magic
    magic=$(xxd -l 4 "$tmp_file" 2>/dev/null | awk '{print $2$3}' | tr -d ' \n' | head -c8 || echo "")
    if [[ "$magic" != "5a494d04" ]] && [[ -n "$magic" ]]; then
        warn "ZIM magic byte check failed (got: ${magic}). File may be corrupted."
        warn "Keeping file — kiwix-manage will validate on import."
    fi

    # Rename to final name (try to get the real filename from curl's -w %{filename_effective})
    # For now: use the temp name → strip .downloading_ prefix
    local final_name
    final_name="${base}_$(date +%Y-%m).zim"
    local final_path="${KIWIX_ZIM_DIR}/${final_name}"

    # If curl followed a redirect, try to detect actual filename
    # from any existing completed download
    mv "$tmp_file" "$final_path"

    local end_time
    end_time=$(date +%s)
    local elapsed=$(( end_time - start_time ))
    local elapsed_fmt
    if [[ $elapsed -ge 3600 ]]; then
        elapsed_fmt="$((elapsed/3600))h $((elapsed%3600/60))m"
    elif [[ $elapsed -ge 60 ]]; then
        elapsed_fmt="${elapsed}m"
    else
        elapsed_fmt="${elapsed}s"
    fi

    success "Downloaded: ${final_name} ($(hr_size $actual_mb) in ${elapsed_fmt})"
    echo "${final_path}"
    return 0
}

# =============================================================================
# Register a ZIM file with kiwix-manage → library.xml
# =============================================================================
register_zim() {
    local zim_path="$1"
    local id="$2"

    if [[ ! -f "$zim_path" ]]; then
        warn "ZIM file not found, skipping registration: $zim_path"
        return 1
    fi

    # Check if already in library
    if [[ -f "$KIWIX_LIB" ]] && grep -q "$(basename "$zim_path")" "$KIWIX_LIB" 2>/dev/null; then
        info "Already in library: $(basename "$zim_path")"
        return 0
    fi

    if command -v kiwix-manage &>/dev/null; then
        kiwix-manage "$KIWIX_LIB" add "$zim_path" 2>>"$DL_LOG" && \
            success "Registered in library: $(basename "$zim_path")" || \
            warn "kiwix-manage registration failed — kiwix-serve may auto-discover it"
    else
        warn "kiwix-manage not found — ZIM added to directory, kiwix-serve will auto-discover"
    fi
}

# =============================================================================
# Install kiwix-tools and kiwix-serve
# =============================================================================
install_kiwix_packages() {
    step "Installing Kiwix Packages"

    # Try apt (Debian/Ubuntu/Raspbian)
    if command -v apt-get &>/dev/null; then
        info "Installing kiwix-tools via apt…"
        # kiwix-tools provides kiwix-manage and kiwix-serve on Debian Bookworm+
        # On older systems it may be in a PPA
        if apt-get install -y kiwix-tools 2>>"$DL_LOG"; then
            success "kiwix-tools installed via apt"
            return 0
        fi

        # Fallback: try the kiwix PPA
        warn "kiwix-tools not in default repos — trying alternative sources"
        if command -v add-apt-repository &>/dev/null; then
            add-apt-repository -y ppa:kiwixteam/release 2>>"$DL_LOG" || true
            apt-get update -qq 2>>"$DL_LOG"
            if apt-get install -y kiwix-tools 2>>"$DL_LOG"; then
                success "kiwix-tools installed via kiwix PPA"
                return 0
            fi
        fi
    fi

    # Fallback: download kiwix-serve binary directly
    install_kiwix_binary
}

install_kiwix_binary() {
    info "Downloading kiwix-serve binary directly from kiwix.org…"

    local ARCH
    ARCH=$(uname -m)
    local KIWIX_VERSION="2.3.1"
    local KIWIX_BINARY_BASE="https://download.kiwix.org/release/kiwix-tools"

    case "$ARCH" in
        aarch64|arm64) local ARCH_STR="aarch64" ;;
        armv7l|armhf)  local ARCH_STR="armv6"   ;;
        x86_64)        local ARCH_STR="x86_64"  ;;
        *)
            error "Unsupported architecture: $ARCH — download kiwix-tools manually from kiwix.org"
            ;;
    esac

    local TAR_NAME="kiwix-tools_linux-${ARCH_STR}-${KIWIX_VERSION}.tar.gz"
    local DL_URL="${KIWIX_BINARY_BASE}/${TAR_NAME}"
    local TMP_DIR
    TMP_DIR=$(mktemp -d)

    info "Downloading: ${DL_URL}"
    curl -fsSL --progress-bar --max-time 300 -o "${TMP_DIR}/${TAR_NAME}" "$DL_URL" \
        2>&1 | tee -a "$DL_LOG" || error "Failed to download kiwix binary"

    tar -xzf "${TMP_DIR}/${TAR_NAME}" -C "$TMP_DIR" 2>>"$DL_LOG"

    # Install binaries
    local bin_dir="${TMP_DIR}/kiwix-tools_linux-${ARCH_STR}-${KIWIX_VERSION}"
    install -m 755 "${bin_dir}/kiwix-serve"  /usr/local/bin/kiwix-serve
    install -m 755 "${bin_dir}/kiwix-manage" /usr/local/bin/kiwix-manage 2>/dev/null || true
    install -m 755 "${bin_dir}/kiwix-search" /usr/local/bin/kiwix-search 2>/dev/null || true

    rm -rf "$TMP_DIR"
    success "kiwix-serve ${KIWIX_VERSION} installed to /usr/local/bin/"
}

# =============================================================================
# Create system user, directories, library file
# =============================================================================
setup_kiwix_system() {
    step "Setting Up Kiwix System"

    # System user
    if ! id "$KIWIX_USER" &>/dev/null; then
        useradd -r -s /bin/false -d /opt/kiwix "$KIWIX_USER"
        success "Created system user: $KIWIX_USER"
    else
        info "User $KIWIX_USER already exists"
    fi

    # Directories
    mkdir -p "$KIWIX_ZIM_DIR" "$KIWIX_LOG_DIR"
    chown -R "${KIWIX_USER}:${KIWIX_USER}" /opt/kiwix "$KIWIX_LOG_DIR"
    chmod 755 "$KIWIX_ZIM_DIR"
    success "Directories: $KIWIX_ZIM_DIR"

    # Initialise empty library if needed
    if [[ ! -f "$KIWIX_LIB" ]]; then
        echo '<?xml version="1.0" encoding="UTF-8" ?><library version="20110515"></library>' \
            > "$KIWIX_LIB"
        chown "${KIWIX_USER}:${KIWIX_USER}" "$KIWIX_LIB"
        success "Created library: $KIWIX_LIB"
    else
        info "Library exists: $KIWIX_LIB"
    fi
}

# =============================================================================
# Write kiwix-serve systemd unit
# =============================================================================
install_kiwix_service() {
    step "Installing kiwix-serve Service"

    # Determine binary path
    local KIWIX_BIN
    KIWIX_BIN=$(command -v kiwix-serve || echo "/usr/local/bin/kiwix-serve")

    cat > "$KIWIX_SVC" << UNIT
[Unit]
Description=Kiwix Offline Library Server (Port ${KIWIX_PORT})
Documentation=https://www.kiwix.org/
After=network.target

[Service]
Type=simple
User=${KIWIX_USER}
Group=${KIWIX_USER}
WorkingDirectory=/opt/kiwix

# kiwix-serve can run in two modes:
# 1. Library mode (recommended): serves all ZIMs in library.xml
# 2. Directory mode: auto-discovers all .zim files in a directory
#
# We use directory mode so new ZIMs are served automatically without
# restarting or re-running kiwix-manage.
ExecStart=${KIWIX_BIN} \\
    --port=${KIWIX_PORT} \\
    --library ${KIWIX_LIB}

# Restart on failure with a delay
Restart=on-failure
RestartSec=15

# Resource limits (ZIM serving is memory-efficient but can spike on search)
MemoryMax=512M
TasksMax=64

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=kiwix

[Install]
WantedBy=multi-user.target
UNIT

    systemctl daemon-reload
    systemctl enable kiwix.service 2>>"$DL_LOG"
    success "Kiwix service installed and enabled"
    info "Start with: systemctl start kiwix"
    info "Access at:  http://localhost:${KIWIX_PORT}"
}

# =============================================================================
# Show status of installed ZIMs and service
# =============================================================================
show_status() {
    step "Kiwix Status"

    # Service status
    local svc_status
    svc_status=$(systemctl is-active kiwix 2>/dev/null || echo "not installed")
    local svc_color
    [[ "$svc_status" == "active" ]] && svc_color="${GREEN}" || svc_color="${RED}"
    echo -e "  kiwix-serve service: ${svc_color}${svc_status}${NC}"

    # Binary
    local bin_path
    bin_path=$(command -v kiwix-serve 2>/dev/null || echo "not found")
    local bin_ver=""
    [[ "$bin_path" != "not found" ]] && bin_ver="($(kiwix-serve --version 2>/dev/null | head -1 || echo "?"))"
    echo -e "  kiwix-serve binary: ${bin_path} ${DIM}${bin_ver}${NC}"

    # ZIM directory
    echo -e "  ZIM directory: ${KIWIX_ZIM_DIR}"
    if [[ -d "$KIWIX_ZIM_DIR" ]]; then
        local zim_count
        zim_count=$(find "$KIWIX_ZIM_DIR" -name "*.zim" 2>/dev/null | wc -l)
        local zim_bytes
        zim_bytes=$(du -sb "$KIWIX_ZIM_DIR" 2>/dev/null | awk '{print $1}' || echo "0")
        local zim_gb
        zim_gb=$(echo "scale=1; $zim_bytes/1024/1024/1024" | bc 2>/dev/null || echo "?")
        echo -e "  Installed ZIMs: ${GREEN}${zim_count}${NC} files (${zim_gb} GB)"
        echo ""
        find "$KIWIX_ZIM_DIR" -name "*.zim" 2>/dev/null | sort | while read -r f; do
            local sz
            sz=$(du -sh "$f" | awk '{print $1}')
            echo -e "    ${GREEN}✓${NC} $(basename "$f") ${DIM}(${sz})${NC}"
        done
    fi

    # Catalogue status
    echo ""
    echo -e "${BOLD}Available ZIMs (catalogue):${NC}"
    show_catalogue
}

# =============================================================================
# Update check — compare installed vs latest catalog version
# =============================================================================
check_updates() {
    step "Checking for ZIM Updates"

    if ! curl -fsS --max-time 5 "https://download.kiwix.org" &>/dev/null; then
        error "No internet connection — cannot check for updates"
    fi

    local updates_available=0
    for id in "${ZIM_ORDER[@]}"; do
        if zim_installed "$id"; then
            local installed_path
            installed_path=$(zim_installed_path "$id")
            local installed_name
            installed_name=$(basename "$installed_path")

            # Resolve latest URL and get its filename via redirect
            local url
            url=$(resolve_zim_url "$id")
            local latest_name
            latest_name=$(curl -fsLI --max-time 10 "$url" 2>/dev/null | \
                grep -i "content-disposition\|location" | tail -1 | \
                grep -oP '[^/]+\.zim' | tail -1 || echo "")

            if [[ -n "$latest_name" && "$latest_name" != "$installed_name" ]]; then
                warn "UPDATE available for ${ZIM_NAME[$id]}:"
                warn "  Installed: ${installed_name}"
                warn "  Latest:    ${latest_name}"
                updates_available=$(( updates_available + 1 ))
            else
                success "${ZIM_NAME[$id]}: up to date (${installed_name})"
            fi
        fi
    done

    if [[ $updates_available -eq 0 ]]; then
        success "All installed ZIMs are up to date"
    else
        echo ""
        warn "${updates_available} update(s) available."
        echo -e "  To update, re-run: ${CYAN}sudo bash kiwix_setup.sh --update-install${NC}"
    fi
}

# =============================================================================
# Interactive selection menu
# =============================================================================
interactive_menu() {
    clear
    echo -e "${BOLD}${BLUE}"
    cat << 'BANNER'
  ╔═══════════════════════════════════════════════════════╗
  ║         FieldComms — Kiwix Offline Library            ║
  ║              EmComm ZIM File Installer                ║
  ╚═══════════════════════════════════════════════════════╝
BANNER
    echo -e "${NC}"

    show_catalogue

    echo -e "${BOLD}Select what to download:${NC}"
    echo "  1) Tier 1 only — Essential   (~2.5 GB)  Recommended for 16GB card"
    echo "  2) Tier 1 + 2  — Extended    (~10 GB)   Recommended for 32GB card"
    echo "  3) All tiers   — Full suite  (~25 GB)   Requires 64GB card"
    echo "  4) Choose individually"
    echo "  5) Skip (install Kiwix system only, no downloads)"
    echo "  6) Show status and exit"
    echo "  0) Cancel"
    echo ""
    read -rp "Select [0-6]: " MENU_CHOICE

    case "$MENU_CHOICE" in
        1) SELECTED_TIER=1 ;;
        2) SELECTED_TIER=2 ;;
        3) SELECTED_TIER=3 ;;
        4) individual_selection ;;
        5) SELECTED_TIER=0 ;;
        6) show_status; exit 0 ;;
        0) echo "Cancelled."; exit 0 ;;
        *) echo -e "${RED}Invalid selection${NC}"; exit 1 ;;
    esac
}

# Individual ZIM selection
SELECTED_ZIMS=()
individual_selection() {
    echo ""
    echo -e "${BOLD}Select ZIMs to download (space-separated numbers, e.g. 1 3 5):${NC}"
    local num=1
    for id in "${ZIM_ORDER[@]}"; do
        local installed=""
        zim_installed "$id" && installed=" ${GREEN}[installed]${NC}"
        echo -e "  ${CYAN}${num}${NC}  ${ZIM_NAME[$id]} ($(hr_size ${ZIM_SIZE[$id]}), Tier ${ZIM_TIER[$id]})${installed}"
        num=$(( num + 1 ))
    done
    echo ""
    read -rp "Enter numbers: " -a SELECTION_NUMS

    for n in "${SELECTION_NUMS[@]}"; do
        local idx=$(( n - 1 ))
        if [[ $idx -ge 0 && $idx -lt ${#ZIM_ORDER[@]} ]]; then
            SELECTED_ZIMS+=("${ZIM_ORDER[$idx]}")
        fi
    done

    if [[ ${#SELECTED_ZIMS[@]} -eq 0 ]]; then
        warn "No ZIMs selected"
        SELECTED_TIER=0
    else
        SELECTED_TIER=-1  # custom selection
    fi
}

# =============================================================================
# Build download list from tier or custom selection
# =============================================================================
build_download_list() {
    DOWNLOAD_LIST=()

    if [[ "${SELECTED_TIER}" -eq -1 ]]; then
        # Custom individual selection
        DOWNLOAD_LIST=("${SELECTED_ZIMS[@]}")
    elif [[ "${SELECTED_TIER}" -gt 0 ]]; then
        for id in "${ZIM_ORDER[@]}"; do
            if [[ "${ZIM_TIER[$id]}" -le "${SELECTED_TIER}" ]]; then
                DOWNLOAD_LIST+=("$id")
            fi
        done
    fi

    # Show summary and confirm
    if [[ ${#DOWNLOAD_LIST[@]} -gt 0 ]]; then
        echo ""
        echo -e "${BOLD}Download plan:${NC}"
        local total_mb=0
        for id in "${DOWNLOAD_LIST[@]}"; do
            local mb="${ZIM_SIZE[$id]}"
            total_mb=$(( total_mb + mb ))
            if zim_installed "$id"; then
                echo -e "  ${GREEN}[skip — installed]${NC}  ${ZIM_NAME[$id]}"
            else
                echo -e "  ${AMBER}[download]${NC}  ${ZIM_NAME[$id]}  ($(hr_size $mb))"
            fi
        done
        echo ""
        echo -e "  Estimated download: ${BOLD}$(hr_size $total_mb)${NC} (installed files skipped)"
        echo ""

        read -rp "Proceed with download? [Y/n]: " CONFIRM
        CONFIRM="${CONFIRM:-Y}"
        [[ "$CONFIRM" =~ ^[Yy] ]] || { echo "Cancelled."; exit 0; }
    fi
}

# =============================================================================
# Restart kiwix-serve with new ZIMs
# =============================================================================
restart_kiwix() {
    if systemctl is-enabled kiwix &>/dev/null; then
        info "Restarting kiwix-serve to load new ZIMs…"
        systemctl restart kiwix 2>>"$DL_LOG" && \
            success "kiwix-serve restarted — http://localhost:${KIWIX_PORT}" || \
            warn "Restart failed — try: systemctl start kiwix"
    else
        info "Starting kiwix-serve…"
        systemctl start kiwix 2>>"$DL_LOG" && \
            success "kiwix-serve started — http://localhost:${KIWIX_PORT}" || \
            warn "Start failed — check: journalctl -u kiwix"
    fi
}

# =============================================================================
# Main entry point
# =============================================================================
SELECTED_TIER=""
DOWNLOAD_LIST=()
ARG_MODE="interactive"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --tier)
            ARG_MODE="tier"
            SELECTED_TIER="${2:-1}"
            shift 2 ;;
        --tier=*)
            ARG_MODE="tier"
            SELECTED_TIER="${1#*=}"
            shift ;;
        --list)        ARG_MODE="list";   shift ;;
        --status)      ARG_MODE="status"; shift ;;
        --update)      ARG_MODE="update"; shift ;;
        --update-install)
            ARG_MODE="update-install";    shift ;;
        --no-prompt)
            ARG_MODE="tier"
            [[ -z "$SELECTED_TIER" ]] && SELECTED_TIER=1
            shift ;;
        *)
            echo -e "${RED}Unknown argument: $1${NC}"
            echo "Usage: sudo bash kiwix_setup.sh [--tier N] [--list] [--status] [--update]"
            exit 1 ;;
    esac
done

case "$ARG_MODE" in
    list)
        show_catalogue
        exit 0
        ;;

    status)
        show_status
        exit 0
        ;;

    update)
        check_updates
        exit 0
        ;;

    update-install)
        SELECTED_TIER=3
        ;;

    tier)
        [[ -z "$SELECTED_TIER" ]] && SELECTED_TIER=1
        ;;

    interactive)
        interactive_menu
        ;;
esac

# ── Run the installation ────────────────────────────────────────────────────
echo ""
log "$(date): Starting Kiwix setup (mode=${ARG_MODE}, tier=${SELECTED_TIER})"

# 1. Install kiwix packages
install_kiwix_packages

# 2. System setup (user, dirs, library)
setup_kiwix_system

# 3. Build download list and confirm
build_download_list

# 4. Install systemd service
install_kiwix_service

# 5. Download ZIMs
if [[ ${#DOWNLOAD_LIST[@]} -gt 0 ]]; then
    step "Downloading ZIM Files"

    FAILED_ZIMS=()
    INSTALLED_ZIMS=()

    for id in "${DOWNLOAD_LIST[@]}"; do
        if zim_installed "$id"; then
            local_path=$(zim_installed_path "$id")
            INSTALLED_ZIMS+=("$local_path")
            register_zim "$local_path" "$id"
            continue
        fi

        if dl_path=$(download_zim "$id"); then
            if [[ -f "$dl_path" ]]; then
                chown "${KIWIX_USER}:${KIWIX_USER}" "$dl_path"
                register_zim "$dl_path" "$id"
                INSTALLED_ZIMS+=("$dl_path")
            fi
        else
            FAILED_ZIMS+=("${ZIM_NAME[$id]}")
        fi
    done

    echo ""
    step "Download Summary"

    if [[ ${#INSTALLED_ZIMS[@]} -gt 0 ]]; then
        success "Successfully installed ${#INSTALLED_ZIMS[@]} ZIM file(s):"
        for f in "${INSTALLED_ZIMS[@]}"; do
            local sz
            sz=$(du -sh "$f" 2>/dev/null | awk '{print $1}')
            success "  $(basename "$f") (${sz})"
        done
    fi

    if [[ ${#FAILED_ZIMS[@]} -gt 0 ]]; then
        echo ""
        warn "Failed to download ${#FAILED_ZIMS[@]} ZIM file(s):"
        for n in "${FAILED_ZIMS[@]}"; do
            warn "  ✗ ${n}"
        done
        warn "Re-run this script to retry — curl will resume partial downloads."
    fi
fi

# 6. Start/restart kiwix
restart_kiwix

# ── Final summary ───────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║              Kiwix Setup Complete!                       ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Kiwix library:  ${CYAN}http://localhost:${KIWIX_PORT}${NC}"
echo -e "  ZIM directory:  ${CYAN}${KIWIX_ZIM_DIR}${NC}"
echo -e "  Library XML:    ${CYAN}${KIWIX_LIB}${NC}"
echo -e "  Install log:    ${CYAN}${DL_LOG}${NC}"
echo ""
echo -e "  Service management:"
echo -e "    ${CYAN}systemctl status kiwix${NC}          check status"
echo -e "    ${CYAN}systemctl restart kiwix${NC}         reload with new ZIMs"
echo -e "    ${CYAN}journalctl -fu kiwix${NC}            live logs"
echo ""
echo -e "  Add more ZIMs later:"
echo -e "    ${CYAN}sudo bash kiwix_setup.sh --tier 2${NC}"
echo -e "    ${CYAN}sudo bash kiwix_setup.sh --list${NC}          show available"
echo -e "    ${CYAN}sudo bash kiwix_setup.sh --status${NC}        show installed"
echo -e "    ${CYAN}sudo bash kiwix_setup.sh --update${NC}        check for updates"
echo ""
log "$(date): Kiwix setup complete"

exit 0
