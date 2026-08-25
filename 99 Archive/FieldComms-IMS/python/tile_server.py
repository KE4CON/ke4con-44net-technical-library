#!/usr/bin/env python3
"""
FieldComms — Offline Map Tile Server
Serves MBTiles databases as XYZ tile endpoints for Leaflet.js
Port 8083  —  http://localhost:8083/tiles/{tileset}/{z}/{x}/{y}.png

MBTiles stores tiles in TMS format (Y-flipped).
We flip Y back to XYZ/Slippy format for Leaflet.

Endpoints:
  GET /tiles/                          → JSON list of available tilesets
  GET /tiles/{tileset}/metadata.json   → tileset metadata
  GET /tiles/{tileset}/{z}/{x}/{y}.png → tile image (PNG or JPEG)
  GET /tiles/{tileset}/{z}/{x}/{y}.jpg → tile image (JPEG)
  GET /health                          → health check JSON
"""

import os
from typing import Optional, List, Dict
import sys
import json
import sqlite3
import hashlib
import threading
import logging
from functools import lru_cache
from flask import Flask, Response, jsonify, abort, request
from flask_cors import CORS

# ── Configuration ─────────────────────────────────────────────────────────────
TILE_DIR  = os.environ.get('FC_TILE_DIR',  '/opt/fieldcomms/tiles')
PORT      = int(os.environ.get('FC_TILE_PORT', 8083))
HOST      = os.environ.get('FC_TILE_HOST', '0.0.0.0')
CACHE_TTL = int(os.environ.get('FC_TILE_CACHE', 3600))   # seconds

# 1×1 transparent PNG (returned when a tile is not in the database)
TRANSPARENT_PNG = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
    b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/fieldcomms-tiles.log', mode='a'),
    ]
)
log = logging.getLogger('tile-server')

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/tiles/*": {"origins": "*"}})

# ── Database connection pool ──────────────────────────────────────────────────
# One connection per thread per tileset
_local = threading.local()

def get_db(tileset: str) -> object:
    """Get or create a thread-local SQLite connection for the tileset."""
    db_path = os.path.join(TILE_DIR, f'{tileset}.mbtiles')
    if not os.path.isfile(db_path):
        return None

    key = f'db_{tileset}'
    if not hasattr(_local, key):
        try:
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            # Performance tuning for read-only tile serving
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=OFF')
            conn.execute('PRAGMA cache_size=2000')    # 2000 pages × 4KB = 8MB cache
            conn.execute('PRAGMA temp_store=MEMORY')
            setattr(_local, key, conn)
            log.info(f'Opened MBTiles: {db_path}')
        except Exception as e:
            log.error(f'Failed to open {db_path}: {e}')
            return None

    return getattr(_local, key)


def list_tilesets() -> List[str]:
    """Return names of all available MBTiles files."""
    if not os.path.isdir(TILE_DIR):
        return []
    return [
        f[:-8] for f in os.listdir(TILE_DIR)
        if f.endswith('.mbtiles') and os.path.isfile(os.path.join(TILE_DIR, f))
    ]


def get_metadata(tileset: str) -> Dict:
    """Read metadata table from MBTiles."""
    db = get_db(tileset)
    if not db:
        return {}
    try:
        rows = db.execute('SELECT name, value FROM metadata').fetchall()
        return {r['name']: r['value'] for r in rows}
    except Exception:
        return {}


def xyz_to_tms_y(z: int, y: int) -> int:
    """Convert XYZ tile Y to TMS tile_row (MBTiles stores TMS)."""
    return (1 << z) - 1 - y


def fetch_tile(tileset: str, z: int, x: int, y: int) -> Optional[bytes]:
    """Fetch raw tile bytes from MBTiles. Returns None if not found."""
    db = get_db(tileset)
    if not db:
        return None

    tms_y = xyz_to_tms_y(z, y)
    try:
        row = db.execute(
            'SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?',
            (z, x, tms_y)
        ).fetchone()
        return bytes(row['tile_data']) if row else None
    except Exception as e:
        log.warning(f'Tile fetch error {tileset}/{z}/{x}/{y}: {e}')
        return None


def detect_format(data: bytes) -> str:
    """Detect whether tile data is PNG or JPEG."""
    if data[:4] == b'\x89PNG':
        return 'image/png'
    if data[:2] == b'\xff\xd8':
        return 'image/jpeg'
    return 'image/png'


def etag_for(tileset: str, z: int, x: int, y: int) -> str:
    return hashlib.md5(f'{tileset}/{z}/{x}/{y}'.encode()).hexdigest()[:16]


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/health')
def health():
    tilesets = list_tilesets()
    info = {}
    for ts in tilesets:
        meta = get_metadata(ts)
        db = get_db(ts)
        count = 0
        if db:
            try:
                count = db.execute('SELECT COUNT(*) FROM tiles').fetchone()[0]
            except Exception:
                pass
        info[ts] = {
            'tiles':   count,
            'minzoom': meta.get('minzoom', '?'),
            'maxzoom': meta.get('maxzoom', '?'),
            'bounds':  meta.get('bounds', '?'),
            'format':  meta.get('format', 'png'),
        }
    return jsonify({
        'status':    'ok',
        'tile_dir':  TILE_DIR,
        'tilesets':  tilesets,
        'count':     len(tilesets),
        'detail':    info,
    })


@app.route('/tiles/')
@app.route('/tiles')
def index():
    tilesets = list_tilesets()
    result = []
    for ts in sorted(tilesets):
        meta = get_metadata(ts)
        result.append({
            'id':          ts,
            'name':        meta.get('name', ts),
            'description': meta.get('description', ''),
            'attribution': meta.get('attribution', ''),
            'minzoom':     int(meta.get('minzoom', 0)),
            'maxzoom':     int(meta.get('maxzoom', 22)),
            'bounds':      meta.get('bounds', ''),
            'tiles_url':   f'http://{{server}}/tiles/{ts}/{{z}}/{{x}}/{{y}}.png',
        })
    return jsonify({'tilesets': result, 'count': len(result)})


@app.route('/tiles/<tileset>/metadata.json')
def metadata(tileset):
    if tileset not in list_tilesets():
        abort(404)
    meta = get_metadata(tileset)
    # Add TileJSON-compatible fields
    meta['tiles'] = [f'/tiles/{tileset}/{{z}}/{{x}}/{{y}}.png']
    meta['tilejson'] = '2.2.0'
    return jsonify(meta)


@app.route('/tiles/<tileset>/<int:z>/<int:x>/<int:y>.png')
@app.route('/tiles/<tileset>/<int:z>/<int:x>/<int:y>.jpg')
def serve_tile(tileset, z, x, y):
    # Validate zoom range
    if z < 0 or z > 22:
        abort(400)
    # Validate tile coordinates
    max_coord = (1 << z)
    if x < 0 or x >= max_coord or y < 0 or y >= max_coord:
        return Response(TRANSPARENT_PNG, 200, {
            'Content-Type': 'image/png',
            'Cache-Control': f'public, max-age={CACHE_TTL}',
        })

    # Check ETags for browser caching
    etag = etag_for(tileset, z, x, y)
    if request.headers.get('If-None-Match') == etag:
        return Response(status=304)

    # Fetch tile
    data = fetch_tile(tileset, z, x, y)

    if data is None:
        # Return transparent pixel — allows Leaflet to continue without error
        return Response(TRANSPARENT_PNG, 200, {
            'Content-Type':  'image/png',
            'Cache-Control': f'public, max-age={CACHE_TTL}',
            'X-Tile-Miss':   '1',
        })

    content_type = detect_format(data)
    return Response(data, 200, {
        'Content-Type':   content_type,
        'Cache-Control':  f'public, max-age={CACHE_TTL}',
        'ETag':           etag,
        'X-Tile-Source':  tileset,
        'Access-Control-Allow-Origin': '*',
    })


@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.errorhandler(404)
def not_found(e):
    tilesets = list_tilesets()
    return jsonify({
        'error':     'Not found',
        'tilesets':  tilesets,
        'tile_dir':  TILE_DIR,
    }), 404


# ── Startup ───────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    if not os.path.isdir(TILE_DIR):
        log.warning(f'Tile directory does not exist: {TILE_DIR}')
        log.warning('Run download_tiles.sh to download map tiles.')
        os.makedirs(TILE_DIR, exist_ok=True)

    tilesets = list_tilesets()
    if tilesets:
        log.info(f'Found {len(tilesets)} tileset(s): {", ".join(sorted(tilesets))}')
    else:
        log.warning(f'No MBTiles files found in {TILE_DIR}')
        log.warning('Maps will show blank until tiles are downloaded.')
        log.warning('Run: sudo bash /opt/fieldcomms/scripts/download_tiles.sh')

    log.info(f'Starting tile server on {HOST}:{PORT}')
    app.run(host=HOST, port=PORT, threaded=True, debug=False)
