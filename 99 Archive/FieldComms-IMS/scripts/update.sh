#!/usr/bin/env bash
# FieldComms one-command update/maintenance script
set -euo pipefail

AMBER='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

FC_HOME="/opt/fieldcomms"
FC_WEB="/opt/fieldcomms/html"
FC_VENV="$FC_HOME/venv"

echo -e "${BOLD}${AMBER}FieldComms Maintenance Menu${NC}"
echo ""
echo "  1) Restart all services"
echo "  2) Stop all services"
echo "  3) Check service status"
echo "  4) View logs (live)"
echo "  5) Refresh FCC database"
echo "  6) Fetch repeater data"
echo "  7) Update web files from current directory"
echo "  8) Backup data to /tmp"
echo "  9) Show disk usage"
echo "  a) Re-download ICS forms PDFs"
echo "  t) Apply theme consistency check"
echo "  0) Exit"
echo ""
read -rp "Select [0-9]: " CHOICE

case "$CHOICE" in
    1)
        echo -e "${CYAN}Restarting services...${NC}"
        for svc in fcc-lookup health-monitor deadmans ics-platform fieldcomms-refs fieldcomms-tiles yaac graywolf nginx; do
            sudo systemctl restart "$svc" && echo -e "${GREEN}✓ $svc${NC}" || echo -e "${RED}✗ $svc${NC}"
        done
        ;;
    2)
        echo -e "${CYAN}Stopping services...${NC}"
        for svc in fcc-lookup health-monitor deadmans ics-platform fieldcomms-refs fieldcomms-tiles yaac graywolf; do
            sudo systemctl stop "$svc" && echo -e "${GREEN}✓ Stopped $svc${NC}" || true
        done
        ;;
    3)
        for svc in fcc-lookup health-monitor deadmans ics-platform fieldcomms-refs fieldcomms-tiles yaac graywolf nginx; do
            STATUS=$(systemctl is-active "$svc" 2>/dev/null || echo "unknown")
            if [[ "$STATUS" == "active" ]]; then
                echo -e "  ${GREEN}●${NC} $svc — active"
            else
                echo -e "  ${RED}●${NC} $svc — $STATUS"
            fi
        done
        ;;
    4)
        echo -e "${CYAN}Streaming logs (Ctrl+C to stop)...${NC}"
        sudo journalctl -fu fcc-lookup -fu health-monitor -fu ics-platform
        ;;
    5)
        echo -e "${CYAN}Refreshing FCC database...${NC}"
        sudo -u fieldcomms "$FC_VENV/bin/python" "$FC_HOME/python/build_fcc_db.py"
        echo -e "${GREEN}Done.${NC}"
        ;;
    6)
        echo -e "${CYAN}Fetching repeater data from RepeaterBook...${NC}"
        TOKEN_FILE="$FC_HOME/data/repeaterbook_token.txt"
        ENV_FILE="$FC_HOME/data/repeaterbook.env"
        if [[ ! -f "$TOKEN_FILE" && ! -f "$ENV_FILE" ]]; then
            echo -e "${CYAN}RepeaterBook now requires an API token.${NC}"
            echo "  Apply at: https://www.repeaterbook.com/api/token_request.php"
            read -rp "Paste your RepeaterBook API token (or leave blank to skip): " RBTOKEN
            if [[ -n "$RBTOKEN" ]]; then
                echo "$RBTOKEN" | sudo -u fieldcomms tee "$TOKEN_FILE" >/dev/null
                echo -e "${GREEN}Token saved to $TOKEN_FILE${NC}"
            fi
        fi
        read -rp "State codes (default IL,WI,IN,IA): " STATES
        STATES="${STATES:-IL,WI,IN,IA}"
        sudo -u fieldcomms "$FC_VENV/bin/python" "$FC_HOME/python/fetch_repeaters.py" --states "$STATES" --bands 2m,70cm
        echo -e "${GREEN}Done. Reload the Repeater Database page (Server API tab) to see the data.${NC}"
        ;;
    7)
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        if [[ -d "$SCRIPT_DIR/../html" ]]; then
            sudo rsync -a "$SCRIPT_DIR/../html/" "$FC_WEB/"
            sudo chown -R www-data:www-data "$FC_WEB"
            echo -e "${GREEN}Web files updated.${NC}"
        else
            echo -e "${RED}html/ directory not found relative to script.${NC}"
        fi
        # Also update Python files so servers stay in sync with HTML
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
            apply_theme.py
            ics_pdf_downloader.py
        )
        PY_UPDATED=0
        for f in "${PY_FILES[@]}"; do
            SRC="$SCRIPT_DIR/../python/$f"
            if [[ -f "$SRC" ]]; then
                sudo cp "$SRC" "$FC_HOME/python/$f"
                sudo chmod 755 "$FC_HOME/python/$f"
                PY_UPDATED=$((PY_UPDATED+1))
            fi
        done
        echo -e "${GREEN}Python files updated: ${PY_UPDATED} files copied to $FC_HOME/python/${NC}"
        # Restart services to pick up changes
        for svc in fcc-lookup health-monitor deadmans ics-platform fieldcomms-refs; do
            sudo systemctl restart "$svc.service" 2>/dev/null && \
                echo -e "  ${GREEN}Restarted: $svc${NC}" || \
                echo -e "  ${AMBER}Could not restart: $svc (may not be running)${NC}"
        done
        ;;
    8)
        DEST="/tmp/fieldcomms-backup-$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$DEST"
        sudo rsync -a "$FC_HOME/data/" "$DEST/data/" 2>/dev/null && echo -e "${GREEN}Data backed up to $DEST${NC}" || echo -e "${RED}Backup failed${NC}"
        ;;
    9)
        echo -e "${CYAN}Disk usage:${NC}"
        df -h / | tail -1
        du -sh "$FC_HOME/data/" 2>/dev/null && echo "  ↑ fieldcomms data"
        du -sh "$FC_WEB/" 2>/dev/null && echo "  ↑ web files"
        ;;
    a)
        echo -e "${CYAN}Re-downloading ICS forms PDFs...${NC}"
        sudo -u fieldcomms "$FC_VENV/bin/python" "$FC_HOME/python/ics_pdf_downloader.py" \
            --output "$FC_HOME/data/ics_forms"
        echo -e "${GREEN}Done.${NC}"
        ;;
    t)
        echo -e "${CYAN}Checking HTML theme consistency...${NC}"
        "$FC_VENV/bin/python" "$FC_HOME/python/apply_theme.py" --dir "$FC_WEB" --check
        read -rp "Apply fixes? [y/N]: " FIX
        [[ "$FIX" =~ ^[Yy] ]] && "$FC_VENV/bin/python" "$FC_HOME/python/apply_theme.py" \
            --dir "$FC_WEB" --apply && echo -e "${GREEN}Theme applied.${NC}"
        ;;
    0)
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid selection${NC}"
        ;;
esac
