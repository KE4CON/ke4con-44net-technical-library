/**
 * FieldComms — Shared Map Tile Layer Configuration
 * Handles online tile sources, local offline tile server fallback,
 * and automatic detection of what's available.
 *
 * Usage (in any HTML page using Leaflet):
 *   <script src="/lib/tiles.js"></script>
 *   const layers = FC_TILES.buildLayerControl(map);
 *
 * The tile server (port 8083) is automatically detected.
 * If it's running with downloaded tiles, those are used first.
 * If not, falls back to online sources when internet is available.
 */

const FC_TILES = (() => {
    const TILE_SERVER = 'http://localhost:8083';

    // ── Tile source definitions ───────────────────────────────────────────────
    // Ordered: offline local first, then online fallbacks
    const SOURCES = {
        // ── Offline local (served from MBTiles on the Pi) ────────────────────
        usgs_topo: {
            label:       '🗺 USGS Topo (Offline)',
            group:       'offline',
            url:         `${TILE_SERVER}/tiles/usgs_topo/{z}/{x}/{y}.png`,
            attribution: 'USGS National Map — Public Domain',
            maxZoom:     18,
            minZoom:     1,
            offline:     true,
        },
        usgs_imagery: {
            label:       '🛰 USGS Imagery (Offline)',
            group:       'offline',
            url:         `${TILE_SERVER}/tiles/usgs_imagery/{z}/{x}/{y}.png`,
            attribution: 'USGS National Map — Public Domain',
            maxZoom:     18,
            offline:     true,
        },
        usgs_imgtopo: {
            label:       '🛰 USGS Imagery+Topo ★ (Offline)',  // McHenry County default
            group:       'offline',
            url:         `${TILE_SERVER}/tiles/usgs_imgtopo/{z}/{x}/{y}.png`,
            attribution: 'USGS National Map — Public Domain',
            maxZoom:     18,
            offline:     true,
        },
        esri_street: {
            label:       '🏙 Street Map (Offline)',
            group:       'offline',
            url:         `${TILE_SERVER}/tiles/esri_street/{z}/{x}/{y}.png`,
            attribution: '© Esri, HERE, Garmin, USGS',
            maxZoom:     18,
            offline:     true,
        },
        esri_topo: {
            label:       '⛰ Topo Map (Offline)',
            group:       'offline',
            url:         `${TILE_SERVER}/tiles/esri_topo/{z}/{x}/{y}.png`,
            attribution: '© Esri, USGS, NOAA',
            maxZoom:     18,
            offline:     true,
        },
        esri_imagery: {
            label:       '📷 Satellite (Offline)',
            group:       'offline',
            url:         `${TILE_SERVER}/tiles/esri_imagery/{z}/{x}/{y}.png`,
            attribution: '© Esri, Maxar, Earthstar Geographics',
            maxZoom:     18,
            offline:     true,
        },
        esri_relief: {
            label:       '🏔 Shaded Relief (Offline)',
            group:       'offline',
            url:         `${TILE_SERVER}/tiles/esri_relief/{z}/{x}/{y}.png`,
            attribution: '© Esri, USGS',
            maxZoom:     18,
            offline:     true,
        },

        // ── Online sources (require internet) ────────────────────────────────
        osm: {
            label:       '🌐 OpenStreetMap (Online)',
            group:       'online',
            url:         'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            attribution: '© OpenStreetMap contributors',
            maxZoom:     19,
            offline:     false,
        },
        esri_street_online: {
            label:       '🏙 Esri Street Map (Online)',
            group:       'online',
            url:         'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
            attribution: '© Esri, HERE, Garmin, USGS',
            maxZoom:     19,
            offline:     false,
        },
        esri_imagery_online: {
            label:       '📷 Esri Satellite (Online)',
            group:       'online',
            url:         'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attribution: '© Esri, Maxar, Earthstar Geographics',
            maxZoom:     19,
            offline:     false,
        },
        esri_topo_online: {
            label:       '⛰ Esri Topo (Online)',
            group:       'online',
            url:         'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
            attribution: '© Esri, USGS, NOAA',
            maxZoom:     19,
            offline:     false,
        },
        usgs_topo_online: {
            label:       '🗺 USGS Topo (Online)',
            group:       'online',
            url:         'https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopoLarge/MapServer/tile/{z}/{y}/{x}',
            attribution: 'USGS National Map — Public Domain',
            maxZoom:     17,
            offline:     false,
        },
        opentopomap: {
            label:       '⛰ OpenTopoMap (Online)',
            group:       'online',
            url:         'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
            attribution: '© OpenTopoMap, OpenStreetMap contributors',
            maxZoom:     17,
            offline:     false,
        },
    };

    // State
    let _availableOffline  = [];   // tileset IDs found on tile server
    let _tileServerOnline  = false;
    let _internetAvailable = false;
    let _statusEl          = null;
    let _initialized       = false;

    // ── Probe the local tile server ───────────────────────────────────────────
    async function probeTileServer() {
        try {
            const res = await fetch(`${TILE_SERVER}/tiles`, {
                signal: AbortSignal.timeout(2000),
            });
            if (!res.ok) return false;
            const data = await res.json();
            _availableOffline = (data.tilesets || []).map(t => t.id);
            _tileServerOnline = true;
            return true;
        } catch (e) {
            _tileServerOnline = false;
            _availableOffline = [];
            return false;
        }
    }

    // ── Probe internet availability ───────────────────────────────────────────
    async function probeInternet() {
        try {
            const res = await fetch('https://tile.openstreetmap.org/0/0/0.png', {
                signal: AbortSignal.timeout(3000),
                mode: 'no-cors',
            });
            _internetAvailable = true;
            return true;
        } catch (e) {
            _internetAvailable = false;
            return false;
        }
    }

    // ── Build a Leaflet TileLayer for a source ID ─────────────────────────────
    function buildLayer(sourceId) {
        const src = SOURCES[sourceId];
        if (!src) return null;
        return L.tileLayer(src.url, {
            attribution: src.attribution,
            maxZoom:     src.maxZoom || 19,
            minZoom:     src.minZoom || 0,
            crossOrigin: true,
        });
    }

    // ── Get the best default base layer ──────────────────────────────────────
    // Priority: usgs_topo offline > esri_street offline > osm online > blank
    function getBestDefault() {
        // usgs_imgtopo (USGS Imagery+Topo hybrid) is the preferred default
        // for McHenry County RACES/ARES/Starcom field operations
        const offlinePreference = ['usgs_imgtopo', 'usgs_imagery', 'usgs_topo',
                                   'esri_imagery', 'esri_street', 'esri_topo',
                                   'esri_relief'];
        for (const id of offlinePreference) {
            if (_availableOffline.includes(id)) return id;
        }
        if (_internetAvailable) return 'usgs_topo_online';  // USGS online when no offline tiles
        return null;  // No tiles available
    }

    // ── Build Leaflet layer control ───────────────────────────────────────────
    async function buildLayerControl(map, options = {}) {
        const {
            statusElementId = null,
            defaultSource   = null,
        } = options;

        if (statusElementId) {
            _statusEl = document.getElementById(statusElementId);
        }

        // Probe what's available
        updateStatus('Detecting tile sources…');
        await Promise.allSettled([probeTileServer(), probeInternet()]);

        const baseLayers = {};
        let   defaultLayer = null;
        let   defaultId = defaultSource || getBestDefault();

        // Add offline layers first (those available on tile server)
        if (_tileServerOnline && _availableOffline.length > 0) {
            for (const [id, src] of Object.entries(SOURCES)) {
                if (!src.offline) continue;
                if (!_availableOffline.includes(id)) continue;
                const layer = buildLayer(id);
                if (layer) {
                    baseLayers[src.label] = layer;
                    if (id === defaultId) defaultLayer = layer;
                }
            }
        }

        // Add online layers if internet available
        if (_internetAvailable) {
            for (const [id, src] of Object.entries(SOURCES)) {
                if (src.offline) continue;
                const layer = buildLayer(id);
                if (layer) {
                    baseLayers[src.label] = layer;
                    if (id === defaultId) defaultLayer = layer;
                }
            }
        }

        // If nothing at all — add blank grey layer so map still works
        if (Object.keys(baseLayers).length === 0) {
            const blank = L.tileLayer('', {
                attribution: 'No tiles available — run download_tiles.sh',
            });
            baseLayers['(No tiles — run download_tiles.sh)'] = blank;
            defaultLayer = blank;
        }

        // Add default layer to map
        if (defaultLayer) {
            defaultLayer.addTo(map);
        } else if (Object.keys(baseLayers).length > 0) {
            Object.values(baseLayers)[0].addTo(map);
        }

        // Build control
        const ctrl = L.control.layers(baseLayers, {}, {
            position:  'topright',
            collapsed: true,
        }).addTo(map);

        // Update status display
        updateStatus(buildStatusText());
        _initialized = true;

        return { control: ctrl, baseLayers, defaultLayer };
    }

    // ── Status text ───────────────────────────────────────────────────────────
    function buildStatusText() {
        const parts = [];
        if (_tileServerOnline && _availableOffline.length > 0) {
            parts.push(`📁 ${_availableOffline.length} offline tileset(s)`);
        } else if (!_tileServerOnline) {
            parts.push('📁 Tile server offline');
        }
        if (_internetAvailable) {
            parts.push('🌐 Online tiles available');
        } else {
            parts.push('🌐 No internet');
        }
        if (!_tileServerOnline && !_internetAvailable) {
            return '⚠ No map tiles — run download_tiles.sh on the Pi';
        }
        return parts.join(' · ');
    }

    function updateStatus(text) {
        if (_statusEl) _statusEl.textContent = text;
    }

    // ── Simple single-layer setup (for pages that don't need the control) ─────
    async function addBasemap(map, preferredId = null) {
        await Promise.allSettled([probeTileServer(), probeInternet()]);
        const id = preferredId || getBestDefault();
        if (!id) {
            console.warn('FC_TILES: No tile source available');
            return null;
        }
        const layer = buildLayer(id);
        if (layer) layer.addTo(map);
        return layer;
    }

    // ── Tile server status for UI badges ─────────────────────────────────────
    function getStatus() {
        return {
            tileServerOnline:  _tileServerOnline,
            internetAvailable: _internetAvailable,
            availableOffline:  [..._availableOffline],
            initialized:       _initialized,
        };
    }

    // ── Refresh (re-probe after network change) ───────────────────────────────
    async function refresh(map) {
        await Promise.allSettled([probeTileServer(), probeInternet()]);
        updateStatus(buildStatusText());
    }

    // ── Public API ────────────────────────────────────────────────────────────
    return {
        SOURCES,
        TILE_SERVER,
        buildLayerControl,
        addBasemap,
        buildLayer,
        getStatus,
        refresh,
        probeTileServer,
        probeInternet,
    };
})();
