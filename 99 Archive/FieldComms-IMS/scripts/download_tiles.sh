#!/usr/bin/env bash
# =============================================================================
# FieldComms — Offline Map Tile Downloader
# Downloads USGS/Esri map tiles into MBTiles SQLite databases for offline use.
#
# Usage:
#   sudo bash download_tiles.sh              # interactive menu
#   sudo bash download_tiles.sh --search "dupage"          # search presets
#   sudo bash download_tiles.sh --area county_mchenry      # named preset
#   sudo bash download_tiles.sh --area state_il            # full state
#   sudo bash download_tiles.sh --list [filter]            # list all presets
#   sudo bash download_tiles.sh --status                   # show downloaded
#   sudo bash download_tiles.sh --delete tileset_name      # remove a tileset
#
# Custom area:
#   sudo bash download_tiles.sh \
#       --north 42.70 --south 41.90 --west -89.00 --east -87.80 \
#       --zoom 8-16 --source usgs_imgtopo --name "My Custom Area"
#
# Tile sources (legally downloadable for EmComm use):
#   usgs_imgtopo  USGS Imagery+Topo Hybrid  (public domain — DEFAULT)
#   usgs_topo     USGS Topo Map             (public domain)
#   usgs_imagery  USGS Aerial Imagery       (public domain)
#   esri_street   Esri World Street Map     (free, non-commercial)
#   esri_topo     Esri World Topo Map       (free, non-commercial)
#   esri_imagery  Esri World Imagery        (free, non-commercial)
#   esri_relief   Esri Shaded Relief        (free, non-commercial)
# =============================================================================
set -euo pipefail

TILE_DIR="/opt/fieldcomms/tiles"
TILE_LOG="/var/log/fieldcomms-tiles.log"
SAVED_AREAS_F="/opt/fieldcomms/data/saved_tile_areas.json"
TILE_USER="fieldcomms"
UA="Mozilla/5.0 (compatible; FieldComms/1.0 EmComm)"
DELAY_USGS="0.10"
DELAY_ESRI="0.15"

GREEN='\033[0;32m'; AMBER='\033[0;33m'; BLUE='\033[0;34m'
CYAN='\033[0;36m';  RED='\033[0;31m';   BOLD='\033[1m'
DIM='\033[2m';      NC='\033[0m'

log()     { echo -e "$1" | tee -a "$TILE_LOG"; }
info()    { log "${CYAN}[INFO]${NC}  $1"; }
success() { log "${GREEN}[OK]${NC}    $1"; }
warn()    { log "${AMBER}[WARN]${NC}  $1"; }
error()   { log "${RED}[ERROR]${NC} $1"; exit 1; }
step()    { log "\n${BOLD}${BLUE}━━━ $1 ━━━${NC}"; }

[[ $EUID -eq 0 ]] || error "Run as root: sudo bash download_tiles.sh"

mkdir -p "$(dirname "$TILE_LOG")" && touch "$TILE_LOG"
mkdir -p "$TILE_DIR" && chown "${TILE_USER}:${TILE_USER}" "$TILE_DIR" 2>/dev/null || true
mkdir -p "$(dirname "$SAVED_AREAS_F")" 2>/dev/null || true

# =============================================================================
# Tile source definitions
# =============================================================================
declare -A SRC_URL SRC_DELAY SRC_ATTR SRC_DESC
SRC_ORDER=(usgs_imgtopo usgs_topo usgs_imagery esri_street esri_topo esri_imagery esri_relief)

ds() { SRC_URL[$1]="$2"; SRC_DELAY[$1]="$3"; SRC_ATTR[$1]="$4"; SRC_DESC[$1]="$5"; }

ds "usgs_imgtopo" \
   "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryTopo/MapServer/tile/{z}/{y}/{x}" \
   "$DELAY_USGS" "USGS National Map" \
   "USGS Imagery+Topo Hybrid — aerial photos with road/topo overlay [DEFAULT]"

ds "usgs_topo" \
   "https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopoLarge/MapServer/tile/{z}/{y}/{x}" \
   "$DELAY_USGS" "USGS National Map" \
   "USGS Topo Map — roads, contours, water features, land cover"

ds "usgs_imagery" \
   "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}" \
   "$DELAY_USGS" "USGS National Map" \
   "USGS Aerial Imagery — satellite/aerial photography only"

ds "esri_street" \
   "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}" \
   "$DELAY_ESRI" "© Esri, HERE, Garmin, USGS" \
   "Esri World Street Map — detailed road map with labels"

ds "esri_topo" \
   "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}" \
   "$DELAY_ESRI" "© Esri, USGS, NOAA" \
   "Esri World Topo Map — topographic with roads and terrain"

ds "esri_imagery" \
   "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}" \
   "$DELAY_ESRI" "© Esri, Maxar, Earthstar Geographics" \
   "Esri World Imagery — commercial-quality satellite photos"

ds "esri_relief" \
   "https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}" \
   "$DELAY_ESRI" "© Esri, USGS" \
   "Esri World Shaded Relief — hillshade terrain without labels"

# =============================================================================
# Geographic area presets — built-in library (106 presets)
# =============================================================================
declare -A AREA_N AREA_S AREA_W AREA_E AREA_LABEL AREA_GROUP

da() {
    # da id N S W E "label" "group"
    AREA_N[$1]="$2"; AREA_S[$1]="$3"
    AREA_W[$1]="$4"; AREA_E[$1]="$5"
    AREA_LABEL[$1]="$6"
    AREA_GROUP[$1]="${7:-General}"
}

# Illinois Counties
da "county_cook"       42.154 41.469 -88.263 -87.524 "Cook County IL (Chicago)"          "IL Counties"
da "county_dupage"     41.986 41.591 -88.258 -87.924 "DuPage County IL"                   "IL Counties"
da "county_lake_il"    42.494 42.058 -88.097 -87.528 "Lake County IL"                     "IL Counties"
da "county_mchenry"    42.496 42.154 -88.708 -88.056 "McHenry County IL"                  "IL Counties"
da "county_kane"       42.154 41.728 -88.708 -88.196 "Kane County IL"                     "IL Counties"
da "county_kendall"    41.728 41.469 -88.708 -88.196 "Kendall County IL"                  "IL Counties"
da "county_will"       41.728 41.196 -88.263 -87.524 "Will County IL"                     "IL Counties"
da "county_dekalb"     42.154 41.728 -89.033 -88.584 "DeKalb County IL"                   "IL Counties"
da "county_boone"      42.496 42.154 -89.033 -88.584 "Boone County IL"                    "IL Counties"
da "county_winnebago"  42.496 42.154 -89.622 -89.033 "Winnebago County IL (Rockford)"     "IL Counties"
da "county_ogle"       42.154 41.728 -89.622 -89.033 "Ogle County IL"                     "IL Counties"
da "county_stephenson" 42.496 42.154 -90.049 -89.622 "Stephenson County IL (Freeport)"    "IL Counties"
da "county_jo_daviess" 42.510 42.154 -90.669 -89.920 "Jo Daviess County IL (Galena)"      "IL Counties"
da "county_carroll"    42.154 41.728 -90.049 -89.622 "Carroll County IL"                  "IL Counties"
da "county_whiteside"  41.896 41.586 -90.049 -89.622 "Whiteside County IL"                "IL Counties"
da "county_lee"        41.896 41.586 -89.622 -89.033 "Lee County IL (Dixon)"              "IL Counties"
da "county_lasalle"    41.586 41.196 -89.622 -88.879 "LaSalle County IL (Ottawa)"         "IL Counties"
da "county_grundy"     41.469 41.196 -88.584 -88.196 "Grundy County IL"                   "IL Counties"
da "county_kankakee"   41.196 40.908 -88.263 -87.524 "Kankakee County IL"                 "IL Counties"
da "county_iroquois"   40.908 40.479 -87.955 -87.524 "Iroquois County IL"                 "IL Counties"
da "county_vermilion"  40.479 39.906 -88.008 -87.524 "Vermilion County IL (Danville)"     "IL Counties"
da "county_champaign"  40.479 39.906 -88.584 -88.008 "Champaign County IL (Urbana)"       "IL Counties"
da "county_sangamon"   39.906 39.564 -89.909 -89.374 "Sangamon County IL (Springfield)"   "IL Counties"
da "county_peoria"     40.883 40.479 -89.909 -89.374 "Peoria County IL"                   "IL Counties"
da "county_mclean"     40.883 40.102 -89.374 -88.584 "McLean County IL (Bloomington)"     "IL Counties"
da "county_madison_il" 38.930 38.548 -90.207 -89.672 "Madison County IL (Edwardsville)"   "IL Counties"
da "county_st_clair"   38.548 38.165 -90.207 -89.672 "St. Clair County IL (Belleville)"   "IL Counties"

# Wisconsin Counties
da "county_walworth"   42.843 42.494 -88.706 -88.258 "Walworth County WI"                 "WI Counties"
da "county_kenosha"    42.843 42.494 -88.258 -87.764 "Kenosha County WI"                  "WI Counties"
da "county_racine"     43.195 42.843 -88.258 -87.764 "Racine County WI"                   "WI Counties"
da "county_milwaukee"  43.195 42.843 -88.068 -87.764 "Milwaukee County WI"                "WI Counties"
da "county_waukesha"   43.195 42.843 -88.540 -88.068 "Waukesha County WI"                 "WI Counties"
da "county_rock"       42.843 42.494 -89.229 -88.706 "Rock County WI (Janesville)"        "WI Counties"
da "county_dane"       43.195 42.843 -89.901 -89.229 "Dane County WI (Madison)"           "WI Counties"
da "county_green"      42.843 42.494 -89.901 -89.229 "Green County WI (Monroe)"           "WI Counties"

# Indiana Counties
da "county_lake_in"    41.728 41.469 -87.764 -87.280 "Lake County IN (Gary)"              "IN Counties"
da "county_porter"     41.728 41.469 -87.280 -86.794 "Porter County IN (Valparaiso)"      "IN Counties"
da "county_laporte"    41.896 41.469 -86.794 -86.308 "LaPorte County IN"                  "IN Counties"
da "county_newton"     41.228 40.748 -87.764 -87.280 "Newton County IN"                   "IN Counties"

# Iowa Counties
da "county_dubuque"    42.910 42.490 -91.130 -90.669 "Dubuque County IA"                  "IA Counties"
da "county_jackson_ia" 42.490 42.060 -91.130 -90.669 "Jackson County IA"                  "IA Counties"
da "county_clinton_ia" 42.060 41.750 -90.669 -90.148 "Clinton County IA (Clinton)"        "IA Counties"
da "county_scott"      41.860 41.448 -90.669 -90.148 "Scott County IA (Davenport)"        "IA Counties"

# Multi-county EmComm regions
da "northern_il"       42.700 41.400 -89.500 -87.500 "Northern Illinois (9-county region)" "IL Regions"
da "chicago_metro"     42.200 41.500 -88.400 -87.400 "Chicago Metropolitan Area"           "IL Regions"
da "mchenry_buffer"    42.700 41.900 -89.000 -87.800 "McHenry County + 25mi buffer"        "IL Regions"
da "mchenry_core"      42.496 42.154 -88.708 -88.056 "McHenry County core boundary"        "IL Regions"
da "quad_cities"       41.860 41.448 -90.800 -90.000 "Quad Cities IL/IA metro"             "IL Regions"
da "rockford_metro"    42.600 41.900 -89.700 -88.800 "Rockford IL metro area"              "IL Regions"
da "springfield_il"    40.000 39.500 -90.000 -89.200 "Springfield IL metro"                "IL Regions"
da "peoria_metro"      41.000 40.400 -90.100 -89.200 "Peoria IL metro"                     "IL Regions"
da "champaign_metro"   40.300 39.800 -88.400 -87.900 "Champaign-Urbana IL metro"           "IL Regions"
da "lake_mi_shore"     43.200 41.500 -88.200 -87.400 "Lake Michigan Shoreline (NE IL / SE WI)" "IL Regions"
da "il_wi_border"      42.900 42.100 -89.200 -87.800 "Illinois/Wisconsin Border Region"    "IL Regions"
da "il_ia_border"      42.500 40.400 -91.500 -90.000 "Illinois/Iowa Border Region"         "IL Regions"

# US States
da "state_il"    42.510 36.970 -91.513 -87.020 "Illinois (full state)"             "US States"
da "state_wi"    47.309 42.492 -92.889 -86.250 "Wisconsin (full state)"            "US States"
da "state_in"    41.761 37.772 -88.097 -84.785 "Indiana (full state)"              "US States"
da "state_ia"    43.501 40.375 -96.640 -90.140 "Iowa (full state)"                 "US States"
da "state_mn"    49.385 43.499 -97.239 -89.489 "Minnesota (full state)"            "US States"
da "state_oh"    42.320 38.404 -84.820 -80.519 "Ohio (full state)"                 "US States"
da "state_mi"    48.306 41.696 -90.418 -82.413 "Michigan (full state)"             "US States"
da "state_mo"    40.614 35.996 -95.774 -89.099 "Missouri (full state)"             "US States"
da "state_ky"    39.147 36.497 -89.572 -81.965 "Kentucky (full state)"             "US States"
da "state_al"    35.008 30.138 -88.474 -84.889 "Alabama (full state)"              "US States"
da "state_fl"    31.001 24.396 -87.635 -80.032 "Florida (full state)"              "US States"
da "state_tx"    36.501 25.837 -106.645 -93.508 "Texas (full state)"               "US States"
da "state_ca"    42.009 32.534 -124.482 -114.131 "California (full state)"         "US States"
da "state_ny"    45.015 40.496 -79.762 -71.856  "New York (full state)"            "US States"
da "state_pa"    42.270 39.720 -80.519 -74.690  "Pennsylvania (full state)"        "US States"
da "state_wa"    49.002 45.544 -124.736 -116.916 "Washington State (full state)"   "US States"
da "state_or"    46.237 41.992 -124.566 -116.463 "Oregon (full state)"             "US States"
da "state_co"    41.003 36.993 -109.060 -102.042 "Colorado (full state)"           "US States"
da "state_az"    37.004 31.333 -114.816 -109.045 "Arizona (full state)"            "US States"
da "state_nc"    36.588 33.752 -84.322  -75.460  "North Carolina (full state)"     "US States"
da "state_va"    39.466 36.541 -83.675  -75.242  "Virginia (full state)"           "US States"
da "state_ga"    35.001 30.358 -85.605  -80.840  "Georgia (full state)"            "US States"
da "state_tn"    36.678 34.983 -90.310  -81.647  "Tennessee (full state)"          "US States"
da "state_la"    33.019 28.928 -94.043  -88.758  "Louisiana (full state)"          "US States"
da "state_ms"    35.008 30.146 -91.655  -88.098  "Mississippi (full state)"        "US States"
da "state_ar"    36.500 33.004 -94.618  -89.645  "Arkansas (full state)"           "US States"
da "state_ok"    37.002 33.616 -103.002 -94.431  "Oklahoma (full state)"           "US States"
da "state_ks"    40.003 36.993 -102.052 -94.589  "Kansas (full state)"             "US States"
da "state_ne"    43.001 39.999 -104.054 -95.308  "Nebraska (full state)"           "US States"
da "state_sd"    45.946 42.480 -104.058 -96.436  "South Dakota (full state)"       "US States"
da "state_nd"    49.001 45.935 -104.049 -96.554  "North Dakota (full state)"       "US States"
da "state_mt"    49.001 44.358 -116.050 -104.040 "Montana (full state)"            "US States"
da "state_wy"    45.006 40.995 -111.057 -104.053 "Wyoming (full state)"            "US States"
da "state_id"    49.001 41.988 -117.243 -111.044 "Idaho (full state)"              "US States"
da "state_ut"    42.002 36.998 -114.053 -109.041 "Utah (full state)"               "US States"
da "state_nv"    42.002 35.002 -120.006 -114.040 "Nevada (full state)"             "US States"
da "state_nm"    37.000 31.332 -109.050 -103.002 "New Mexico (full state)"         "US States"
da "state_ak"    71.538 54.676 -168.000 -130.000 "Alaska (full state)"             "US States"
da "state_hi"    22.236 18.917 -160.247 -154.806 "Hawaii (main islands)"           "US States"
da "state_me"    47.460 43.057  -71.084  -66.949 "Maine (full state)"              "US States"
da "state_vt"    45.017 42.727  -73.438  -71.465 "Vermont (full state)"            "US States"
da "state_nh"    45.305 42.697  -72.557  -70.610 "New Hampshire (full state)"      "US States"
da "state_ma"    42.887 41.238  -73.508  -69.928 "Massachusetts (full state)"      "US States"
da "state_ri"    42.019 41.146  -71.908  -71.120 "Rhode Island (full state)"       "US States"
da "state_ct"    42.051 40.986  -73.728  -71.787 "Connecticut (full state)"        "US States"
da "state_nj"    41.358 38.929  -75.563  -73.894 "New Jersey (full state)"         "US States"
da "state_de"    39.839 38.451  -75.789  -75.048 "Delaware (full state)"           "US States"
da "state_md"    39.723 37.912  -79.487  -75.048 "Maryland (full state)"           "US States"
da "state_wv"    40.638 37.201  -82.644  -77.720 "West Virginia (full state)"      "US States"
da "state_sc"    35.215 32.034  -83.354  -78.541 "South Carolina (full state)"     "US States"
da "state_mi_lp" 44.165 41.696  -86.505  -82.413 "Michigan Lower Peninsula"        "US States"

# Master list (used by --list and search)
AREA_ORDER=(
county_cook county_dupage county_lake_il county_mchenry county_kane county_kendall
county_will county_dekalb county_boone county_winnebago county_ogle county_stephenson
county_jo_daviess county_carroll county_whiteside county_lee county_lasalle
county_grundy county_kankakee county_iroquois county_vermilion county_champaign
county_sangamon county_peoria county_mclean county_madison_il county_st_clair
county_walworth county_kenosha county_racine county_milwaukee county_waukesha
county_rock county_dane county_green
county_lake_in county_porter county_laporte county_newton
county_dubuque county_jackson_ia county_clinton_ia county_scott
northern_il chicago_metro mchenry_buffer mchenry_core quad_cities
rockford_metro springfield_il peoria_metro champaign_metro
lake_mi_shore il_wi_border il_ia_border
state_il state_wi state_in state_ia state_mn state_oh state_mi state_mo
state_ky state_al state_fl state_tx state_ca state_ny state_pa
state_wa state_or state_co state_az state_nc state_va state_ga state_tn
state_la state_ms state_ar state_ok state_ks state_ne state_sd state_nd
state_mt state_wy state_id state_ut state_nv state_nm state_ak state_hi
state_me state_vt state_nh state_ma state_ri state_ct state_nj
state_de state_md state_wv state_sc state_mi_lp
)

# =============================================================================
# Saved custom areas (persisted in JSON)
# =============================================================================
load_saved_areas() {
    [[ -f "$SAVED_AREAS_F" ]] || return
    # Load each saved area from JSON into bash arrays
    python3 << PYEOF
import json, sys
try:
    with open("$SAVED_AREAS_F") as f:
        areas = json.load(f)
    for a in areas:
        print(f"da 'saved_{a['id']}' {a['n']} {a['s']} {a['w']} {a['e']} '{a['label']}' 'Saved'")
        print(f"AREA_ORDER+=('saved_{a['id']}')")
except Exception as e:
    pass
PYEOF
}
eval "$(load_saved_areas)"

save_custom_area() {
    local id="$1" label="$2" n="$3" s="$4" w="$5" e="$6"
    python3 << PYEOF
import json, os
path = "$SAVED_AREAS_F"
try:
    areas = json.load(open(path)) if os.path.exists(path) else []
except:
    areas = []
# Replace if same id exists
areas = [a for a in areas if a.get('id') != '$id']
areas.append({"id": "$id", "label": "$label",
               "n": $n, "s": $s, "w": $w, "e": $e})
os.makedirs(os.path.dirname(path), exist_ok=True)
json.dump(areas, open(path,'w'), indent=2)
print(f"Saved area: $label")
PYEOF
    chown "${TILE_USER}:${TILE_USER}" "$SAVED_AREAS_F" 2>/dev/null || true
}

list_saved_areas() {
    [[ -f "$SAVED_AREAS_F" ]] || return
    python3 -c "
import json
try:
    areas = json.load(open('$SAVED_AREAS_F'))
    for a in areas:
        print(f\"  saved_{a['id']:<20}  {a['label']}\")
except:
    pass
"
}

delete_saved_area() {
    local id="$1"
    python3 << PYEOF
import json, os
path = "$SAVED_AREAS_F"
if not os.path.exists(path): exit()
areas = json.load(open(path))
before = len(areas)
areas = [a for a in areas if a.get('id') != '$id' and f"saved_{a.get('id')}" != '$id']
json.dump(areas, open(path,'w'), indent=2)
print(f"Removed {before - len(areas)} saved area(s)")
PYEOF
}

# =============================================================================
# Search areas by name/keyword
# =============================================================================
search_areas() {
    local q="${1,,}"  # lowercase
    local found=0
    echo ""
    echo -e "${BOLD}Search results for: '${q}'${NC}"
    echo ""
    for id in "${AREA_ORDER[@]}"; do
        local label="${AREA_LABEL[$id]:-}"
        local group="${AREA_GROUP[$id]:-}"
        if [[ "${label,,}" == *"$q"* || "${id,,}" == *"$q"* || "${group,,}" == *"$q"* ]]; then
            printf "  ${CYAN}%-28s${NC}  ${DIM}%-20s${NC}  %s\n" \
                "$id" "$group" "$label"
            found=$(( found + 1 ))
        fi
    done
    if [[ $found -eq 0 ]]; then
        echo -e "  ${AMBER}No presets match '$q'${NC}"
        echo "  Try: county name, state abbreviation, city name, or region keyword"
    else
        echo ""
        echo -e "  ${found} result(s) found. Use:  ${CYAN}sudo bash download_tiles.sh --area PRESET_ID${NC}"
    fi
    echo ""
}

# =============================================================================
# Tile math
# =============================================================================
count_tiles() {
    python3 -c "
import math
def d2xy(lat,lon,z):
    lr=math.radians(lat); n=2**z
    x=int((lon+180)/360*n)
    y=int((1-math.log(math.tan(lr)+1/math.cos(lr))/math.pi)/2*n)
    return max(0,min(n-1,x)), max(0,min(n-1,y))
total=0
for z in range($4,$5+1):
    x0,y0=d2xy($1,$3,z); x1,y1=d2xy($2,$4_EAST,z)
    total+=(abs(x1-x0)+1)*(abs(y1-y0)+1)
print(total)
" 2>/dev/null || echo "0"
}

# Simpler version using positional args: N S W E zmin zmax
count_tiles() {
    local n="$1" s="$2" w="$3" e="$4" zmin="$5" zmax="$6"
    python3 -c "
import math
def d2xy(lat,lon,z):
    if abs(lat)>=90: lat=89.9*(1 if lat>0 else -1)
    lr=math.radians(lat); n=2**z
    x=int((lon+180)/360*n)
    y=int((1-math.log(math.tan(lr)+1/math.cos(lr))/math.pi)/2*n)
    return max(0,min(n-1,x)), max(0,min(n-1,y))
total=0
for z in range($zmin,$zmax+1):
    x0,y0=d2xy($n,$w,z); x1,y1=d2xy($s,$e,z)
    total+=(abs(x1-x0)+1)*(abs(y1-y0)+1)
print(total)
"
}

hr_size() {
    local mb="$1"
    if   [[ $mb -gt 10240 ]]; then echo "$(( mb/1024 )) GB"
    elif [[ $mb -gt 1024  ]]; then echo "$(echo "scale=1; $mb/1024" | bc) GB"
    else echo "${mb} MB"
    fi
}

est_mb() {
    # ~15 KB average per tile
    local tiles="$1"
    echo $(( tiles * 15 / 1024 ))
}

# =============================================================================
# MBTiles helpers
# =============================================================================
mbtiles_init() {
    local db="$1" name="$2" desc="$3" attr="$4"
    python3 -c "
import sqlite3
db=sqlite3.connect('$db')
db.execute('''CREATE TABLE IF NOT EXISTS tiles (
    zoom_level INTEGER NOT NULL, tile_column INTEGER NOT NULL,
    tile_row INTEGER NOT NULL, tile_data BLOB NOT NULL,
    PRIMARY KEY(zoom_level,tile_column,tile_row))''')
db.execute('''CREATE TABLE IF NOT EXISTS metadata (
    name TEXT NOT NULL PRIMARY KEY, value TEXT NOT NULL)''')
db.execute('CREATE UNIQUE INDEX IF NOT EXISTS tile_index ON tiles(zoom_level,tile_column,tile_row)')
for n,v in [('name','$name'),('type','baselayer'),('version','1.0'),
            ('description','$desc'),('format','png'),('attribution','$attr')]:
    db.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)',(n,v))
db.commit(); db.close()
"
}

mbtiles_count() {
    python3 -c "
import sqlite3,os
db=sqlite3.connect('$1')
n=db.execute('SELECT COUNT(*) FROM tiles').fetchone()[0]
sz=os.path.getsize('$1')
db.close()
print(f'{n} tiles, {sz//1024//1024} MB')
"
}

mbtiles_has_tile() {
    # Returns 0 (true) if tile exists, 1 if not
    python3 -c "
import sqlite3
db=sqlite3.connect('$1')
r=db.execute('SELECT 1 FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?',
             ($2,$3,$4)).fetchone()
db.close()
import sys; sys.exit(0 if r else 1)
" 2>/dev/null
}

mbtiles_store() {
    python3 -c "
import sqlite3
with open('$4','rb') as f: data=f.read()
db=sqlite3.connect('$1')
db.execute('INSERT OR REPLACE INTO tiles VALUES(?,?,?,?)',($2,$3,$5,data))
db.commit(); db.close()
"
}

mbtiles_finalize() {
    local db="$1" n="$2" s="$3" w="$4" e="$5" zmin="$6" zmax="$7"
    python3 -c "
import sqlite3
db=sqlite3.connect('$db')
meta=[('bounds','$w,$s,$e,$n'),
      ('center',f'{($e+$w)/2},{($n+$s)/2},{($zmin+$zmax)//2}'),
      ('minzoom','$zmin'),('maxzoom','$zmax'),
      ('area_label','${8:-}'),
      ('downloaded','$(date -u +%Y-%m-%dT%H:%M:%SZ)')]
db.executemany('INSERT OR REPLACE INTO metadata VALUES(?,?)',meta)
db.execute('PRAGMA optimize')
db.commit(); db.close()
"
}

# =============================================================================
# Download one tile — returns 0 on success
# =============================================================================
dl_tile() {
    local url="$1" out="$2" delay="$3"
    local code
    code=$(curl -fsSL -A "$UA" --max-time 15 --connect-timeout 8 \
        --retry 3 --retry-delay 2 --retry-max-time 30 \
        -w "%{http_code}" -o "$out" "$url" 2>/dev/null)
    sleep "$delay"
    [[ "$code" == "200" ]] && [[ -s "$out" ]]
}

# =============================================================================
# Download all tiles for one source+area combo
# =============================================================================
download_tileset() {
    local source="$1" n="$2" s="$3" w="$4" e="$5" zmin="$6" zmax="$7" label="${8:-}"
    local url_tmpl="${SRC_URL[$source]}"
    local delay="${SRC_DELAY[$source]}"
    local attr="${SRC_ATTR[$source]}"
    local desc="${SRC_DESC[$source]}"
    local db="${TILE_DIR}/${source}.mbtiles"
    local tmp
    tmp=$(mktemp /tmp/fc_tile_XXXXXX.png)
    trap "rm -f '$tmp'" EXIT

    step "Downloading: $desc"
    info "Area:     $label"
    info "Bounds:   N${n} S${s} W${w} E${e}"
    info "Zoom:     Z${zmin}–Z${zmax}"
    info "Database: $db"

    local total
    total=$(count_tiles "$n" "$s" "$w" "$e" "$zmin" "$zmax")
    local est
    est=$(est_mb "$total")
    info "Tiles to check: ${total}  (~$(hr_size $est) new)"

    [[ ! -f "$db" ]] && mbtiles_init "$db" "$source" "$desc" "$attr"
    [[ -f "$db" ]]   && info "Resuming existing database: $(mbtiles_count "$db")"

    local dl=0 skip=0 fail=0 consec_fail=0

    for (( z=zmin; z<=zmax; z++ )); do
        local coords
        coords=$(python3 -c "
import math
def d2xy(lat,lon,z):
    if abs(lat)>=90: lat=89.9*(1 if lat>0 else -1)
    lr=math.radians(lat); n=2**z
    x=int((lon+180)/360*n); y=int((1-math.log(math.tan(lr)+1/math.cos(lr))/math.pi)/2*n)
    return max(0,min(n-1,x)),max(0,min(n-1,y))
x0,y0=d2xy($n,$w,$z); x1,y1=d2xy($s,$e,$z)
print(min(x0,x1),max(x0,x1),min(y0,y1),max(y0,y1))
")
        local xmin xmax ymin ymax
        read -r xmin xmax ymin ymax <<< "$coords"
        local z_total=$(( (xmax-xmin+1)*(ymax-ymin+1) )) z_n=0

        for (( x=xmin; x<=xmax; x++ )); do
            for (( y=ymin; y<=ymax; y++ )); do
                z_n=$(( z_n+1 ))
                local tms_y=$(( (1<<z) - 1 - y ))

                # Skip if already stored
                if mbtiles_has_tile "$db" "$z" "$x" "$tms_y" 2>/dev/null; then
                    skip=$(( skip+1 ))
                    continue
                fi

                # Build URL (TMS sources use {y}/{x} with pre-flipped row)
                local url="${url_tmpl/\{z\}/$z}"
                url="${url/\{y\}/$tms_y}"
                url="${url/\{x\}/$x}"

                printf "\r  Z%02d [%4d/%-4d] ✓%-6d skip%-6d ✗%-4d" \
                    "$z" "$z_n" "$z_total" "$dl" "$skip" "$fail"

                if dl_tile "$url" "$tmp" "$delay"; then
                    mbtiles_store "$db" "$z" "$x" "$tms_y" "$tmp"
                    dl=$(( dl+1 ))
                    consec_fail=0
                    rm -f "$tmp"
                else
                    fail=$(( fail+1 ))
                    consec_fail=$(( consec_fail+1 ))
                    if [[ $consec_fail -ge 20 ]]; then
                        echo ""
                        warn "20 consecutive failures — check internet connection"
                        warn "Partial download saved — re-run to resume"
                        break 3
                    fi
                fi
            done
        done
        echo ""
        info "Z${z} done — ${dl} downloaded, ${skip} skipped, ${fail} failed"
    done

    mbtiles_finalize "$db" "$n" "$s" "$w" "$e" "$zmin" "$zmax" "$label"
    chown "${TILE_USER}:${TILE_USER}" "$db" 2>/dev/null || true
    success "Complete: $(mbtiles_count "$db")"
    log "$(date): $source/$label Z${zmin}-${zmax} — ${dl}dl/${skip}skip/${fail}fail"
}

# =============================================================================
# Show status
# =============================================================================
show_status() {
    step "Offline Tile Cache Status"
    local total_bytes=0 found=0
    shopt -s nullglob
    for db in "$TILE_DIR"/*.mbtiles; do
        found=$(( found+1 ))
        local name
        name=$(basename "$db" .mbtiles)
        local info
        info=$(python3 -c "
import sqlite3,os
db=sqlite3.connect('$db')
def m(k):
    r=db.execute('SELECT value FROM metadata WHERE name=?',(k,)).fetchone()
    return r[0] if r else '?'
n=db.execute('SELECT COUNT(*) FROM tiles').fetchone()[0]
sz=os.path.getsize('$db')
print(f\"{n:,} tiles | Z{m('minzoom')}-{m('maxzoom')} | {sz//1024//1024} MB | {m('area_label')} | {m('downloaded')}\")
db.close()
" 2>/dev/null || echo "error reading db")
        echo -e "  ${GREEN}✓${NC} ${CYAN}${name}${NC}"
        echo -e "    ${DIM}${SRC_DESC[$name]:-Unknown source}${NC}"
        echo -e "    $info"
        echo ""
        total_bytes=$(( total_bytes + $(stat -c%s "$db" 2>/dev/null || echo 0) ))
    done
    [[ $found -eq 0 ]] && echo -e "  ${DIM}No tilesets downloaded yet.${NC}"
    [[ $found -gt 0 ]] && echo -e "  Total: ${found} tileset(s), $(( total_bytes/1024/1024 )) MB"

    echo ""
    echo -e "${BOLD}Saved custom areas:${NC}"
    local saved_out
    saved_out=$(list_saved_areas)
    [[ -z "$saved_out" ]] && echo -e "  ${DIM}None saved.${NC}" || echo "$saved_out"
    echo ""
    local svc
    svc=$(systemctl is-active fieldcomms-tiles 2>/dev/null || echo "not installed")
    local col; [[ "$svc" == "active" ]] && col="${GREEN}" || col="${AMBER}"
    echo -e "  Tile server: ${col}${svc}${NC}  (port 8083)"
}

# =============================================================================
# List presets grouped
# =============================================================================
show_list() {
    local filter="${1:-}"
    echo ""
    if [[ -n "$filter" ]]; then
        search_areas "$filter"; return
    fi

    local cur_group=""
    printf "  ${BOLD}%-28s  %-20s  %s${NC}\n" "PRESET ID" "GROUP" "DESCRIPTION"
    printf '  %0.s─' {1..75}; echo ""

    for id in "${AREA_ORDER[@]}"; do
        local g="${AREA_GROUP[$id]:-General}"
        if [[ "$g" != "$cur_group" ]]; then
            echo ""
            echo -e "  ${AMBER}${BOLD}▶ ${g}${NC}"
            cur_group="$g"
        fi
        local installed=""
        [[ -f "${TILE_DIR}/${id}.mbtiles" ]] && installed=" ${GREEN}[DL]${NC}"
        printf "  ${CYAN}%-28s${NC}${installed}  %s\n" "$id" "${AREA_LABEL[$id]}"
    done
    echo ""
    echo -e "  ${BOLD}${#AREA_ORDER[@]} presets total.${NC}"
    echo -e "  Search:   ${CYAN}sudo bash download_tiles.sh --list dupage${NC}"
    echo -e "  Download: ${CYAN}sudo bash download_tiles.sh --area PRESET_ID${NC}"
    echo ""
    echo -e "${BOLD}Tile Sources:${NC}"
    for id in "${SRC_ORDER[@]}"; do
        local installed=""
        [[ -f "${TILE_DIR}/${id}.mbtiles" ]] && installed=" ${GREEN}[downloaded]${NC}"
        printf "  ${CYAN}%-18s${NC}${installed}  ${DIM}%s${NC}\n" "$id" "${SRC_DESC[$id]}"
    done
}

# =============================================================================
# Delete a tileset
# =============================================================================
delete_tileset() {
    local name="$1"
    local db="${TILE_DIR}/${name}.mbtiles"
    if [[ ! -f "$db" ]]; then
        # Maybe it's a saved area id
        delete_saved_area "$name" && return
        error "Tileset not found: $db"
    fi
    local sz
    sz=$(stat -c%s "$db" 2>/dev/null || echo 0)
    echo -e "${RED}Delete: ${db} ($(( sz/1024/1024 )) MB)${NC}"
    read -rp "Confirm? [y/N]: " C
    [[ "$C" =~ ^[Yy] ]] || { echo "Cancelled."; return; }
    rm -f "$db"
    success "Deleted: $db"
    systemctl restart fieldcomms-tiles 2>/dev/null || true
}

# =============================================================================
# Zoom reference
# =============================================================================
show_zoom_ref() {
    echo ""
    echo -e "${BOLD}Zoom Level Reference for EmComm Operations:${NC}"
    echo ""
    printf "  %-5s  %-22s  %-10s  %-10s  %s\n" "ZOOM" "SCALE" "TILE(px)" "DETAIL" "BEST FOR"
    printf '  %0.s─' {1..70}; echo ""
    declare -A ZS ZD ZB
    ZS[8]="1:4,000,000"   ZD[8]="~5km/px"    ZB[8]="State overview, incident context"
    ZS[9]="1:2,000,000"   ZD[9]="~2.5km/px"  ZB[9]="Multi-county view"
    ZS[10]="1:1,000,000"  ZD[10]="~1.2km/px" ZB[10]="County overview"
    ZS[11]="1:500,000"    ZD[11]="~600m/px"  ZB[11]="County operational picture"
    ZS[12]="1:250,000"    ZD[12]="~300m/px"  ZB[12]="City/township level"
    ZS[13]="1:125,000"    ZD[13]="~150m/px"  ZB[13]="Neighborhood / mutual aid sectors"
    ZS[14]="1:60,000"     ZD[14]="~75m/px"   ZB[14]="Street-level navigation ★"
    ZS[15]="1:30,000"     ZD[15]="~38m/px"   ZB[15]="Block-level detail"
    ZS[16]="1:15,000"     ZD[16]="~19m/px"   ZB[16]="Building-level detail ★"
    ZS[17]="1:7,500"      ZD[17]="~9m/px"    ZB[17]="Parcel / SAR grid"
    ZS[18]="1:4,000"      ZD[18]="~5m/px"    ZB[18]="Maximum detail"
    for z in 8 9 10 11 12 13 14 15 16 17 18; do
        printf "  Z%-4s  %-22s  %-10s  %-10s  %s\n" \
            "$z" "${ZS[$z]}" "${ZD[$z]}" "" "${ZB[$z]}"
    done
    echo ""
    echo -e "  ${BOLD}Recommended for McHenry County RACES/ARES/Starcom:${NC}"
    echo -e "    Quick deployment:    Z8–Z14   ~8 MB    2 min"
    echo -e "    Standard ops:        Z8–Z16   ~60 MB   10 min"
    echo -e "    Full detail:         Z8–Z17   ~550 MB  45 min"
}

# =============================================================================
# Interactive menu
# =============================================================================
interactive_menu() {
    clear
    echo -e "${BOLD}${BLUE}"
    cat << 'BANNER'
  ╔═══════════════════════════════════════════════════════════════╗
  ║        FieldComms — Offline Map Tile Downloader               ║
  ║          McHenry County RACES/ARES/Starcom                    ║
  ╚═══════════════════════════════════════════════════════════════╝
BANNER
    echo -e "${NC}"

    echo -e "${BOLD}Select download option:${NC}"
    echo ""
    echo -e "  ${GREEN}── Quick Presets ──────────────────────────────────────${NC}"
    echo "  1)  McHenry County — Essential   Z8–Z14  ~8 MB   ~2 min"
    echo "      USGS Img+Topo + Esri Street"
    echo ""
    echo "  2)  McHenry County — Standard    Z8–Z16  ~60 MB  ~10 min"
    echo "      USGS Img+Topo + USGS Topo + Esri Street"
    echo ""
    echo "  3)  McHenry County — Full        Z8–Z17  ~550 MB ~45 min"
    echo "      All USGS sources + Esri Street"
    echo ""
    echo "  4)  Northern Illinois Region     Z8–Z14  ~40 MB  ~8 min"
    echo "      9-county mutual aid area"
    echo ""
    echo "  5)  Illinois + Border (WI/IN/IA) Z8–Z12  ~25 MB  ~5 min"
    echo "      State overview for statewide incidents"
    echo ""
    echo -e "  ${AMBER}── Other Options ──────────────────────────────────────${NC}"
    echo "  6)  Search presets by name / county / state"
    echo "  7)  Browse all 106 presets by group"
    echo "  8)  Enter coordinates manually"
    echo "  9)  Choose individual source + area"
    echo ""
    echo -e "  ${CYAN}── Management ─────────────────────────────────────────${NC}"
    echo "  s)  Show status of downloaded tilesets"
    echo "  d)  Delete a tileset"
    echo "  z)  Zoom level reference guide"
    echo "  0)  Exit"
    echo ""
    read -rp "Select: " CHOICE

    case "${CHOICE,,}" in
        1)
            MENU_AREA="county_mchenry"; MENU_ZMIN=8; MENU_ZMAX=14
            MENU_SOURCES=(usgs_imgtopo esri_street)
            ;;
        2)
            MENU_AREA="county_mchenry"; MENU_ZMIN=8; MENU_ZMAX=16
            MENU_SOURCES=(usgs_imgtopo usgs_topo esri_street)
            ;;
        3)
            MENU_AREA="county_mchenry"; MENU_ZMIN=8; MENU_ZMAX=17
            MENU_SOURCES=(usgs_imgtopo usgs_topo usgs_imagery esri_street)
            ;;
        4)
            MENU_AREA="northern_il"; MENU_ZMIN=8; MENU_ZMAX=14
            MENU_SOURCES=(usgs_imgtopo esri_street)
            ;;
        5)
            MENU_AREA="state_il"; MENU_ZMIN=8; MENU_ZMAX=12
            MENU_SOURCES=(usgs_imgtopo)
            ;;
        6)
            read -rp "  Search term (county, city, state abbrev): " SRCH
            search_areas "$SRCH"
            read -rp "  Enter preset ID to download (or Enter to go back): " PICKED
            [[ -z "$PICKED" ]] && interactive_menu && return
            [[ -z "${AREA_N[$PICKED]+x}" ]] && { warn "Unknown preset: $PICKED"; interactive_menu; return; }
            MENU_AREA="$PICKED"; MENU_ZMIN=8; MENU_ZMAX=16
            MENU_SOURCES=(usgs_imgtopo esri_street)
            select_zoom_and_confirm
            return
            ;;
        7)
            show_list
            read -rp "  Enter preset ID to download (or Enter to go back): " PICKED
            [[ -z "$PICKED" ]] && interactive_menu && return
            [[ -z "${AREA_N[$PICKED]+x}" ]] && { warn "Unknown preset: $PICKED"; interactive_menu; return; }
            MENU_AREA="$PICKED"; MENU_ZMIN=8; MENU_ZMAX=16
            MENU_SOURCES=(usgs_imgtopo esri_street)
            select_zoom_and_confirm
            return
            ;;
        8)
            manual_area_menu
            ;;
        9)
            pick_source_area_menu
            ;;
        s) show_status; exit 0 ;;
        d)
            read -rp "  Tileset name to delete: " DEL
            delete_tileset "$DEL"
            exit 0
            ;;
        z) show_zoom_ref; read -rp "Press Enter to continue…" _; interactive_menu; return ;;
        0) exit 0 ;;
        *) warn "Invalid selection"; interactive_menu; return ;;
    esac
    confirm_and_run
}

select_zoom_and_confirm() {
    echo ""
    echo -e "  Area: ${CYAN}${AREA_LABEL[$MENU_AREA]}${NC}"
    read -rp "  Min zoom [8]: "  MENU_ZMIN; MENU_ZMIN="${MENU_ZMIN:-8}"
    read -rp "  Max zoom [16]: " MENU_ZMAX; MENU_ZMAX="${MENU_ZMAX:-16}"
    echo ""
    echo "  Sources:"
    echo "    1) usgs_imgtopo + esri_street (recommended)"
    echo "    2) usgs_imgtopo only"
    echo "    3) All USGS sources"
    echo "    4) Choose individually"
    read -rp "  Source preset [1]: " SP; SP="${SP:-1}"
    case "$SP" in
        1) MENU_SOURCES=(usgs_imgtopo esri_street) ;;
        2) MENU_SOURCES=(usgs_imgtopo) ;;
        3) MENU_SOURCES=(usgs_imgtopo usgs_topo usgs_imagery) ;;
        4) pick_sources_only ;;
        *) MENU_SOURCES=(usgs_imgtopo esri_street) ;;
    esac
    confirm_and_run
}

manual_area_menu() {
    echo ""
    echo -e "${BOLD}Enter bounding box coordinates:${NC}"
    echo -e "  ${DIM}Tip: Find at bboxfinder.com or use GPS coordinates${NC}"
    echo ""
    read -rp "  North latitude (e.g. 42.70): "  CUSTOM_N
    read -rp "  South latitude (e.g. 41.90): "  CUSTOM_S
    read -rp "  West longitude (e.g. -89.00): " CUSTOM_W
    read -rp "  East longitude (e.g. -87.80): " CUSTOM_E
    read -rp "  Area name (for your records):   " CUSTOM_LABEL
    CUSTOM_LABEL="${CUSTOM_LABEL:-Custom Area}"

    read -rp "  Min zoom [8]: "  MENU_ZMIN;  MENU_ZMIN="${MENU_ZMIN:-8}"
    read -rp "  Max zoom [16]: " MENU_ZMAX; MENU_ZMAX="${MENU_ZMAX:-16}"

    # Save this area for future use
    local safe_id
    safe_id="${CUSTOM_LABEL,,}"
    safe_id="${safe_id// /_}"
    safe_id="${safe_id//[^a-z0-9_]/}"
    safe_id="${safe_id:0:20}"
    save_custom_area "$safe_id" "$CUSTOM_LABEL" \
        "$CUSTOM_N" "$CUSTOM_S" "$CUSTOM_W" "$CUSTOM_E"

    MENU_AREA="saved_${safe_id}"
    AREA_N[saved_${safe_id}]="$CUSTOM_N"; AREA_S[saved_${safe_id}]="$CUSTOM_S"
    AREA_W[saved_${safe_id}]="$CUSTOM_W"; AREA_E[saved_${safe_id}]="$CUSTOM_E"
    AREA_LABEL[saved_${safe_id}]="$CUSTOM_LABEL"

    MENU_SOURCES=(usgs_imgtopo esri_street)
    success "Area saved as 'saved_${safe_id}' — reuse with: --area saved_${safe_id}"
}

pick_source_area_menu() {
    echo ""
    echo -e "${BOLD}Choose source:${NC}"
    local i=1
    for id in "${SRC_ORDER[@]}"; do
        echo "  $i) $id — ${SRC_DESC[$id]}"
        i=$(( i+1 ))
    done
    read -rp "Source (number or id): " SN
    if [[ "$SN" =~ ^[0-9]+$ ]]; then
        MENU_SOURCES=("${SRC_ORDER[$(( SN-1 ))]}")
    else
        MENU_SOURCES=("$SN")
    fi

    echo ""
    read -rp "Preset ID or 'search TERM': " AREA_IN
    if [[ "$AREA_IN" == search* ]]; then
        search_areas "${AREA_IN#search }"
        read -rp "Preset ID: " MENU_AREA
    else
        MENU_AREA="$AREA_IN"
    fi
    [[ -z "${AREA_N[$MENU_AREA]+x}" ]] && error "Unknown area: $MENU_AREA"

    read -rp "Min zoom [8]: "  MENU_ZMIN;  MENU_ZMIN="${MENU_ZMIN:-8}"
    read -rp "Max zoom [16]: " MENU_ZMAX; MENU_ZMAX="${MENU_ZMAX:-16}"
}

pick_sources_only() {
    echo ""
    local i=1
    for id in "${SRC_ORDER[@]}"; do
        echo "  $i) $id — ${SRC_DESC[$id]}"
        i=$(( i+1 ))
    done
    read -rp "  Source numbers (space-separated): " -a SNUMS
    MENU_SOURCES=()
    for sn in "${SNUMS[@]}"; do
        MENU_SOURCES+=("${SRC_ORDER[$(( sn-1 ))]}")
    done
}

# =============================================================================
# Confirm and execute downloads
# =============================================================================
confirm_and_run() {
    echo ""
    echo -e "${BOLD}Download plan:${NC}"
    echo -e "  Area:    ${CYAN}${AREA_LABEL[$MENU_AREA]:-$MENU_AREA}${NC}"
    echo -e "  Bounds:  N${AREA_N[$MENU_AREA]} S${AREA_S[$MENU_AREA]} W${AREA_W[$MENU_AREA]} E${AREA_E[$MENU_AREA]}"
    echo -e "  Zoom:    ${CYAN}Z${MENU_ZMIN}–Z${MENU_ZMAX}${NC}"
    echo ""

    local grand_total=0
    for src in "${MENU_SOURCES[@]}"; do
        local t
        t=$(count_tiles "${AREA_N[$MENU_AREA]}" "${AREA_S[$MENU_AREA]}" \
                        "${AREA_W[$MENU_AREA]}" "${AREA_E[$MENU_AREA]}" \
                        "$MENU_ZMIN" "$MENU_ZMAX")
        local mb; mb=$(est_mb "$t")
        grand_total=$(( grand_total + mb ))
        echo -e "  ${CYAN}${src}${NC} — ${SRC_DESC[$src]}"
        echo -e "    ~${t} tiles, ~$(hr_size $mb)"
        # Warn if tileset already exists
        [[ -f "${TILE_DIR}/${src}.mbtiles" ]] && \
            echo -e "    ${GREEN}(resuming existing — already-downloaded tiles skipped)${NC}"
    done

    echo ""
    echo -e "  ${BOLD}Total new download: ~$(hr_size $grand_total)${NC}"
    echo -e "  ${DIM}Re-running resumes from where it stopped.${NC}"
    echo ""

    read -rp "Proceed? [Y/n]: " CONFIRM
    CONFIRM="${CONFIRM:-Y}"
    [[ "$CONFIRM" =~ ^[Yy] ]] || { echo "Cancelled."; exit 0; }

    for src in "${MENU_SOURCES[@]}"; do
        download_tileset "$src" \
            "${AREA_N[$MENU_AREA]}" "${AREA_S[$MENU_AREA]}" \
            "${AREA_W[$MENU_AREA]}" "${AREA_E[$MENU_AREA]}" \
            "$MENU_ZMIN" "$MENU_ZMAX" \
            "${AREA_LABEL[$MENU_AREA]:-$MENU_AREA}"
        echo ""
    done

    echo ""
    success "All downloads complete"
    show_status
    echo ""
    success "Restart tile server to serve new tilesets:"
    echo -e "  ${CYAN}sudo systemctl restart fieldcomms-tiles${NC}"
}

# =============================================================================
# Main / argument parsing
# =============================================================================
MENU_AREA=""; MENU_ZMIN=8; MENU_ZMAX=16; MENU_SOURCES=()
MODE="interactive"
CLI_AREA=""; CLI_N=""; CLI_S=""; CLI_W=""; CLI_E=""
CLI_ZMIN=8; CLI_ZMAX=16; CLI_SOURCES=(); CLI_NAME=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --area)      CLI_AREA="$2";   MODE="cli"; shift 2 ;;
        --north)     CLI_N="$2";      shift 2 ;;
        --south)     CLI_S="$2";      shift 2 ;;
        --west)      CLI_W="$2";      shift 2 ;;
        --east)      CLI_E="$2";      shift 2 ;;
        --zoom)      IFS='-' read -r CLI_ZMIN CLI_ZMAX <<< "$2"
                     [[ -z "$CLI_ZMAX" ]] && CLI_ZMAX="$CLI_ZMIN"; shift 2 ;;
        --source)    CLI_SOURCES+=("$2"); shift 2 ;;
        --sources)   IFS=',' read -ra CLI_SOURCES <<< "$2"; shift 2 ;;
        --name)      CLI_NAME="$2";   shift 2 ;;
        --list)      show_list "${2:-}"; exit 0 ;;
        --search)    search_areas "$2"; exit 0 ;;
        --status)    show_status; exit 0 ;;
        --delete)    delete_tileset "$2"; exit 0 ;;
        --zoom-ref)  show_zoom_ref; exit 0 ;;
        --mchenry-essential)
            CLI_AREA="county_mchenry"; CLI_ZMIN=8; CLI_ZMAX=14
            CLI_SOURCES=(usgs_imgtopo esri_street); MODE="cli" ;;
        --mchenry-standard)
            CLI_AREA="county_mchenry"; CLI_ZMIN=8; CLI_ZMAX=16
            CLI_SOURCES=(usgs_imgtopo usgs_topo esri_street); MODE="cli" ;;
        --no-prompt)
            [[ -z "$CLI_AREA" ]] && CLI_AREA="county_mchenry"
            [[ ${#CLI_SOURCES[@]} -eq 0 ]] && CLI_SOURCES=(usgs_imgtopo esri_street)
            MODE="cli" ;;
        *) warn "Unknown argument: $1"; shift ;;
    esac
done

if [[ "$MODE" == "cli" ]]; then
    # Custom bounding box?
    if [[ -n "$CLI_N" ]]; then
        local_id="custom_$(date +%s)"
        CLI_NAME="${CLI_NAME:-Custom Area}"
        da "$local_id" "$CLI_N" "$CLI_S" "$CLI_W" "$CLI_E" "$CLI_NAME" "Custom"
        save_custom_area "$(echo "${CLI_NAME,,}" | tr ' ' '_' | tr -dc 'a-z0-9_' | cut -c1-20)" \
            "$CLI_NAME" "$CLI_N" "$CLI_S" "$CLI_W" "$CLI_E"
        CLI_AREA="$local_id"
    fi

    [[ -z "$CLI_AREA" ]] && error "No area. Use --area PRESET_ID or --north/south/east/west"
    [[ -z "${AREA_N[$CLI_AREA]+x}" ]] && error "Unknown area: '$CLI_AREA'  (use --list or --search)"
    [[ ${#CLI_SOURCES[@]} -eq 0 ]] && CLI_SOURCES=(usgs_imgtopo esri_street)

    MENU_AREA="$CLI_AREA"
    MENU_ZMIN="$CLI_ZMIN"
    MENU_ZMAX="$CLI_ZMAX"
    MENU_SOURCES=("${CLI_SOURCES[@]}")

    confirm_and_run
else
    interactive_menu
fi
