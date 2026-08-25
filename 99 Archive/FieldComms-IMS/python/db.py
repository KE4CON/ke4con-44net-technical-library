#!/usr/bin/env python3
"""
FieldComms — Unified SQLite Database Layer
/opt/fieldcomms/data/fieldcomms.db

Provides:
  - Schema creation and migration
  - Thread-safe connection pool (one per thread)
  - JSON-from-file migration (runs once on first startup)
  - Helper functions used by all three API servers

fcc.db stays separate — it is huge (~600 MB), rebuild-only, and never
written to by the application.
"""

import json
import sqlite3
import threading
import time
import shutil
import logging
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("fieldcomms.db")

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE      = Path("/opt/fieldcomms")
DATA      = BASE / "data"
DB_PATH   = DATA / "fieldcomms.db"
REFS_DIR  = DATA / "refs"
FILES_DIR = REFS_DIR / "files"
THUMB_DIR = REFS_DIR / "thumbs"

for _d in [DATA, DATA / "nets", DATA / "forms", DATA / "ics" / "forms",
           REFS_DIR, FILES_DIR, THUMB_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ── Thread-local connection pool ───────────────────────────────────────────────
_local = threading.local()


def get_conn() -> sqlite3.Connection:
    """Return a thread-local connection to fieldcomms.db."""
    if not hasattr(_local, "conn") or _local.conn is None:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA cache_size=-8000")   # 8 MB per thread
        conn.execute("PRAGMA temp_store=MEMORY")
        _local.conn = conn
    return _local.conn


def db() -> sqlite3.Connection:
    """Shorthand for get_conn()."""
    return get_conn()


# ── Utilities ──────────────────────────────────────────────────────────────────
def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(obj) -> str:
    return json.dumps(obj, default=str)


def jload(s, default=None):
    if not s:
        return default
    try:
        return json.loads(s)
    except Exception:
        return default


def row_to_dict(row) -> dict:
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows) -> list:
    return [dict(r) for r in rows]


# ── Schema ─────────────────────────────────────────────────────────────────────
SCHEMA = """

-- ── Amateur / Starcom nets ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nets (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    type        TEXT NOT NULL DEFAULT 'Amateur',
    starcom     INTEGER NOT NULL DEFAULT 0,   -- 1 = Starcom public safety net
    drill       INTEGER NOT NULL DEFAULT 0,
    active      INTEGER NOT NULL DEFAULT 1,
    freq        TEXT DEFAULT '',
    ncs         TEXT DEFAULT '',              -- net control station callsign
    created     TEXT NOT NULL,
    net_opened  TEXT,                         -- timestamp when net control opens net
    net_closed  TEXT,                         -- timestamp when net control closes net
    closed      TEXT,
    roster_chips TEXT DEFAULT '[]'           -- JSON array of callsigns
);

-- ── Net check-in entries ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS net_entries (
    id          TEXT PRIMARY KEY,
    net_id      TEXT NOT NULL REFERENCES nets(id) ON DELETE CASCADE,
    -- Identifier columns: at least one will be populated
    callsign    TEXT DEFAULT '',             -- amateur callsign (hams only)
    member_id   TEXT DEFAULT '',             -- ESV member ID
    radio_id    TEXT DEFAULT '',             -- Starcom radio ID (all ESV members)
    visitor_agency TEXT DEFAULT '',          -- for mutual aid / visitor
    -- Person info
    name        TEXT DEFAULT '',
    city        TEXT DEFAULT '',
    state       TEXT DEFAULT '',
    -- Log data
    precedence  TEXT DEFAULT 'ROUTINE',
    traffic     TEXT DEFAULT '',
    remarks     TEXT DEFAULT '',
    walk_in     INTEGER NOT NULL DEFAULT 0,  -- 1 = not in roster at check-in
    visitor     INTEGER NOT NULL DEFAULT 0,  -- 1 = mutual aid / outside org
    promoted    INTEGER NOT NULL DEFAULT 0,  -- 1 = promoted to roster
    timestamp   TEXT NOT NULL,
    checkout_time TEXT,                       -- NULL = still on net; set when checked out
    ema_id      TEXT DEFAULT ''              -- EMA/ESV member ID if found in roster
);
CREATE INDEX IF NOT EXISTS idx_ne_net    ON net_entries(net_id);
CREATE INDEX IF NOT EXISTS idx_ne_call   ON net_entries(callsign);
CREATE INDEX IF NOT EXISTS idx_ne_time   ON net_entries(timestamp);

-- ── NTS traffic messages ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS net_traffic (
    id          TEXT PRIMARY KEY,
    net_id      TEXT NOT NULL REFERENCES nets(id) ON DELETE CASCADE,
    msg_number  TEXT DEFAULT '',
    from_call   TEXT DEFAULT '',
    to_call     TEXT DEFAULT '',
    precedence  TEXT DEFAULT 'ROUTINE',
    handling    TEXT DEFAULT '',
    text        TEXT DEFAULT '',
    timestamp   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_nt_net ON net_traffic(net_id);

-- ── Member roster ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS roster (
    id          TEXT PRIMARY KEY,
    member_id   TEXT NOT NULL DEFAULT '', -- ESV member ID (all members)
    callsign    TEXT DEFAULT '',           -- amateur callsign (hams only, may be blank)
    radio_id    TEXT DEFAULT '',           -- Starcom/public safety radio ID (if applicable)
    first_name  TEXT DEFAULT '',
    last_name   TEXT DEFAULT '',
    role        TEXT DEFAULT 'Operator',
    member_type TEXT NOT NULL DEFAULT 'member',  -- 'member' | 'visitor' | 'mutual_aid'
    visitor_agency TEXT DEFAULT '',              -- agency name for non-ESV members
    phone       TEXT DEFAULT '',
    email       TEXT DEFAULT '',
    grid        TEXT DEFAULT '',
    lat         REAL,
    lon         REAL,
    notes       TEXT DEFAULT '',
    -- Certifications (boolean)
    cert_ics100    INTEGER DEFAULT 0,
    cert_ics200    INTEGER DEFAULT 0,
    cert_ics300    INTEGER DEFAULT 0,
    cert_ics400    INTEGER DEFAULT 0,
    cert_ics700    INTEGER DEFAULT 0,
    cert_ics800    INTEGER DEFAULT 0,
    cert_emcomm1   INTEGER DEFAULT 0,
    cert_emcomm2   INTEGER DEFAULT 0,
    cert_cpr       INTEGER DEFAULT 0,
    cert_first_aid INTEGER DEFAULT 0,
    cert_cert      INTEGER DEFAULT 0,
    -- Equipment capabilities (boolean)
    equip_hf       INTEGER DEFAULT 0,
    equip_vhf      INTEGER DEFAULT 0,
    equip_digital  INTEGER DEFAULT 0,
    equip_packet   INTEGER DEFAULT 0,
    equip_pactor   INTEGER DEFAULT 0,
    equip_vara_hf  INTEGER DEFAULT 0,
    equip_vara_fm  INTEGER DEFAULT 0,
    equip_aprs     INTEGER DEFAULT 0,
    equip_winlink  INTEGER DEFAULT 0,
    equip_go_box   INTEGER DEFAULT 0,
    equip_generator INTEGER DEFAULT 0,
    equip_battery  INTEGER DEFAULT 0,
    equip_vehicle  INTEGER DEFAULT 0,
    created     TEXT NOT NULL,
    modified    TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_roster_member ON roster(member_id);
CREATE INDEX IF NOT EXISTS idx_roster_call ON roster(UPPER(callsign))
    WHERE callsign != '';
CREATE INDEX IF NOT EXISTS idx_roster_role ON roster(role);

-- ── Activations ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS activations (
    id          TEXT PRIMARY KEY,
    member_id   TEXT REFERENCES roster(id) ON DELETE SET NULL,
    callsign    TEXT DEFAULT '',            -- denormalised for speed
    net_id      TEXT DEFAULT '',
    incident_id TEXT DEFAULT '',
    role        TEXT DEFAULT '',
    location    TEXT DEFAULT '',
    checked_in  TEXT NOT NULL,
    checked_out TEXT,
    notes       TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_act_member   ON activations(member_id);
CREATE INDEX IF NOT EXISTS idx_act_incident ON activations(incident_id);

-- ── Resource board ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS resources (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    type        TEXT DEFAULT '',            -- Personnel/Vehicle/Equipment/Facility
    capability  TEXT DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'Available',
    assignment  TEXT DEFAULT '',
    contact     TEXT DEFAULT '',
    notes       TEXT DEFAULT '',
    created     TEXT NOT NULL,
    updated     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_res_status ON resources(status);

-- ── ICS Incidents ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS incidents (
    id                  TEXT PRIMARY KEY,
    name                TEXT NOT NULL DEFAULT '',
    type                TEXT DEFAULT '',
    status              TEXT NOT NULL DEFAULT 'active',
    jurisdiction        TEXT DEFAULT '',
    incident_commander  TEXT DEFAULT '',
    location            TEXT DEFAULT '',
    summary             TEXT DEFAULT '',
    current_period      INTEGER NOT NULL DEFAULT 1,
    started             TEXT NOT NULL,
    updated             TEXT,
    closed              TEXT
);
CREATE INDEX IF NOT EXISTS idx_inc_status ON incidents(status);

-- ── ICS Operational Periods ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ics_periods (
    id          TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    period_num  INTEGER NOT NULL,
    started     TEXT NOT NULL,
    ended       TEXT,
    shift_hours INTEGER DEFAULT 12,
    objectives  TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_per_inc ON ics_periods(incident_id);

-- ── ICS Resources ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ics_resources (
    id          TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    resource_id TEXT DEFAULT '',            -- link to resources table (optional)
    name        TEXT NOT NULL DEFAULT '',
    type        TEXT DEFAULT '',
    capability  TEXT DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'Available',
    assignment  TEXT DEFAULT '',
    contact     TEXT DEFAULT '',
    created     TEXT NOT NULL,
    updated     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_icsres_inc ON ics_resources(incident_id);

-- ── ICS T-Cards ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ics_tcards (
    id              TEXT PRIMARY KEY,
    incident_id     TEXT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    resource_id     TEXT DEFAULT '',
    resource_name   TEXT NOT NULL DEFAULT '',
    type            TEXT DEFAULT '',
    status          TEXT NOT NULL DEFAULT 'Available',
    assignment      TEXT DEFAULT '',
    contact         TEXT DEFAULT '',
    created         TEXT NOT NULL,
    updated         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tc_inc    ON ics_tcards(incident_id);
CREATE INDEX IF NOT EXISTS idx_tc_status ON ics_tcards(status);

-- ── ICS Forms (flexible — all form types stored here) ─────────────────────────
CREATE TABLE IF NOT EXISTS ics_forms (
    id          TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL DEFAULT '',
    form_type   TEXT NOT NULL,              -- ics201, ics202, ics205, etc.
    period      INTEGER DEFAULT 1,
    summary     TEXT DEFAULT '',
    data        TEXT NOT NULL DEFAULT '{}', -- full form JSON blob
    created     TEXT NOT NULL,
    updated     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_icsf_inc  ON ics_forms(incident_id);
CREATE INDEX IF NOT EXISTS idx_icsf_type ON ics_forms(form_type);

-- ── ICS Activity Feed ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS activity_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT NOT NULL DEFAULT '',
    section     TEXT DEFAULT '',
    action      TEXT DEFAULT '',
    detail      TEXT DEFAULT '',
    timestamp   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_act_inc  ON activity_log(incident_id);
CREATE INDEX IF NOT EXISTS idx_act_time ON activity_log(timestamp);

-- ── Standalone forms (ICS-213, ICS-214, NTS, etc.) ───────────────────────────
CREATE TABLE IF NOT EXISTS forms (
    id          TEXT PRIMARY KEY,
    form_type   TEXT NOT NULL,
    incident_id TEXT DEFAULT '',
    summary     TEXT DEFAULT '',
    data        TEXT NOT NULL DEFAULT '{}',
    created     TEXT NOT NULL,
    updated     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_forms_type ON forms(form_type);

-- ── Dead Man's Switch (singleton row id=1) ────────────────────────────────────
CREATE TABLE IF NOT EXISTS dms_state (
    id              INTEGER PRIMARY KEY DEFAULT 1,
    state           TEXT NOT NULL DEFAULT 'disarmed',
    armed_nets      TEXT NOT NULL DEFAULT '[]',  -- JSON array
    threshold_min   INTEGER NOT NULL DEFAULT 30,
    last_activity   TEXT,
    armed_at        TEXT,
    triggered_at    TEXT
);
INSERT OR IGNORE INTO dms_state(id) VALUES(1);

-- ── APRS Tactical Map state (singleton) ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS map_state (
    id      INTEGER PRIMARY KEY DEFAULT 1,
    shapes  TEXT NOT NULL DEFAULT '[]',
    markers TEXT NOT NULL DEFAULT '[]',
    updated TEXT
);
INSERT OR IGNORE INTO map_state(id) VALUES(1);

-- ── Starcom Resource Map state (singleton) ────────────────────────────────────
CREATE TABLE IF NOT EXISTS resmap_state (
    id      INTEGER PRIMARY KEY DEFAULT 1,
    markers TEXT NOT NULL DEFAULT '[]',
    updated TEXT
);
INSERT OR IGNORE INTO resmap_state(id) VALUES(1);

-- ── Station configuration (singleton) ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS station_config (
    id              INTEGER PRIMARY KEY DEFAULT 1,
    callsign        TEXT NOT NULL DEFAULT 'W8EOC',
    lat             REAL NOT NULL DEFAULT 42.3247,
    lon             REAL NOT NULL DEFAULT -88.3822,
    gps_enabled     INTEGER NOT NULL DEFAULT 1,
    gps_device      TEXT DEFAULT '/dev/gps0',
    gps_last_fix    TEXT,
    configured_at   TEXT
);
INSERT OR IGNORE INTO station_config(id) VALUES(1);

-- ── Repeater database ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS repeaters (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    callsign    TEXT DEFAULT '',
    output_freq TEXT DEFAULT '',
    input_freq  TEXT DEFAULT '',
    tone        TEXT DEFAULT '',
    tone_input  TEXT DEFAULT '',
    mode        TEXT DEFAULT 'FM',
    digital_code TEXT DEFAULT '',
    city        TEXT DEFAULT '',
    state       TEXT DEFAULT '',
    county      TEXT DEFAULT '',
    lat         REAL,
    lon         REAL,
    status      TEXT DEFAULT 'On-Air',
    use_type    TEXT DEFAULT 'Open',
    ares        INTEGER DEFAULT 0,
    races       INTEGER DEFAULT 0,
    skywarn     INTEGER DEFAULT 0,
    echolink    INTEGER DEFAULT 0,
    allstar     INTEGER DEFAULT 0,
    sponsor     TEXT DEFAULT '',
    notes       TEXT DEFAULT '',
    updated     TEXT,
    source      TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_rep_state  ON repeaters(state);
CREATE INDEX IF NOT EXISTS idx_rep_call   ON repeaters(callsign);
CREATE INDEX IF NOT EXISTS idx_rep_ares   ON repeaters(ares);

-- ── Reference library documents ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ref_documents (
    id              TEXT PRIMARY KEY,
    title           TEXT NOT NULL DEFAULT '',
    filename        TEXT NOT NULL DEFAULT '',
    stored_name     TEXT NOT NULL DEFAULT '',
    category        TEXT NOT NULL DEFAULT 'other',
    sections        TEXT NOT NULL DEFAULT '["amateur"]',  -- JSON array
    description     TEXT DEFAULT '',
    tags            TEXT NOT NULL DEFAULT '[]',            -- JSON array
    source          TEXT DEFAULT '',
    applies_to      TEXT DEFAULT '',
    revision        TEXT DEFAULT '',
    expires         TEXT,
    content_type    TEXT DEFAULT '',
    size_bytes      INTEGER DEFAULT 0,
    sha256          TEXT DEFAULT '',
    uploaded        TEXT NOT NULL,
    modified        TEXT,
    downloads       INTEGER NOT NULL DEFAULT 0,
    last_downloaded TEXT
);
CREATE INDEX IF NOT EXISTS idx_refdoc_cat  ON ref_documents(category);
CREATE INDEX IF NOT EXISTS idx_refdoc_date ON ref_documents(uploaded);

-- ── Preflight run history ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS preflight_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    verdict     TEXT NOT NULL,
    checks      TEXT NOT NULL DEFAULT '{}',   -- JSON blob
    timestamp   TEXT NOT NULL
);

"""


def init_db():
    """Create all tables and indexes. Safe to call multiple times."""
    conn = db()
    conn.executescript(SCHEMA)
    # Migration: add new columns to existing databases (idempotent)
    migrations = [
        "ALTER TABLE nets ADD COLUMN net_opened TEXT",
        "ALTER TABLE nets ADD COLUMN net_closed TEXT",
        "ALTER TABLE net_entries ADD COLUMN checkout_time TEXT",
        "ALTER TABLE net_entries ADD COLUMN ema_id TEXT DEFAULT ''",
    ]
    for sql in migrations:
        try:
            conn.execute(sql)
        except Exception:
            pass  # column already exists
    conn.commit()
    log.info(f"Database initialised: {DB_PATH}")



# ── JSON migration ─────────────────────────────────────────────────────────────
def _migrate_json_file(path: Path, label: str, fn):
    """Load a JSON file, call fn(data), rename file to .migrated."""
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text())
        count = fn(data)
        path.rename(path.with_suffix(".migrated"))
        log.info(f"  Migrated {label}: {count} records → {path.name}.migrated")
        return count
    except Exception as e:
        log.warning(f"  Migration error for {label}: {e}")
        return 0


def migrate_from_json():
    """
    One-time migration: import all legacy JSON files into SQLite.
    Each file is renamed to .migrated after import so this only runs once.
    """
    conn = db()
    total = 0
    log.info("Checking for legacy JSON data to migrate…")

    # ── Nets + entries ────────────────────────────────────────────────────────
    nets_dir = DATA / "nets"
    if nets_dir.exists():
        for jf in sorted(nets_dir.glob("*.json")):
            try:
                nd = json.loads(jf.read_text())
                net_id = nd.get("id", jf.stem)
                conn.execute("""
                    INSERT OR IGNORE INTO nets
                    (id,name,type,starcom,drill,active,freq,ncs,created,closed,roster_chips)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    net_id,
                    nd.get("name", ""),
                    nd.get("type", "Amateur"),
                    1 if nd.get("starcom") else 0,
                    1 if nd.get("drill") else 0,
                    1 if nd.get("active", True) else 0,
                    nd.get("freq", ""),
                    nd.get("ncs", ""),
                    nd.get("created", utcnow()),
                    nd.get("closed"),
                    jdump(nd.get("roster_chips", [])),
                ))
                for e in nd.get("entries", []):
                    conn.execute("""
                        INSERT OR IGNORE INTO net_entries
                        (id,net_id,callsign,name,city,state,radio_id,
                         precedence,traffic,remarks,walk_in,timestamp)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        e.get("id", f"e-{int(time.time()*1000)}"),
                        net_id,
                        e.get("callsign", ""),
                        e.get("name", ""),
                        e.get("city", ""),
                        e.get("state", ""),
                        e.get("radio_id", ""),
                        e.get("precedence", "ROUTINE"),
                        e.get("traffic", ""),
                        e.get("remarks", ""),
                        1 if e.get("walk_in") else 0,
                        e.get("timestamp", utcnow()),
                    ))
                for t in nd.get("traffic", []):
                    conn.execute("""
                        INSERT OR IGNORE INTO net_traffic
                        (id,net_id,msg_number,from_call,to_call,
                         precedence,handling,text,timestamp)
                        VALUES(?,?,?,?,?,?,?,?,?)
                    """, (
                        t.get("id", f"t-{int(time.time()*1000)}"),
                        net_id,
                        t.get("msg_number", ""),
                        t.get("from_call", ""),
                        t.get("to_call", ""),
                        t.get("precedence", "ROUTINE"),
                        t.get("handling", ""),
                        t.get("text", ""),
                        t.get("timestamp", utcnow()),
                    ))
                conn.commit()
                jf.rename(jf.with_suffix(".migrated"))
                total += 1
                log.info(f"  Migrated net: {net_id}")
            except Exception as e:
                log.warning(f"  Net migration error {jf}: {e}")

    # ── Roster ────────────────────────────────────────────────────────────────
    def migrate_roster(data):
        count = 0
        for m in data.get("members", []):
            certs = m.get("certifications", {}) or {}
            equip = m.get("equipment", {}) or {}
            conn.execute("""
                INSERT OR IGNORE INTO roster
                (id,member_id,callsign,radio_id,first_name,last_name,role,phone,email,
                 grid,lat,lon,notes,
                 cert_ics100,cert_ics200,cert_ics300,cert_ics400,
                 cert_ics700,cert_ics800,cert_emcomm1,cert_emcomm2,
                 cert_cpr,cert_first_aid,cert_cert,
                 equip_hf,equip_vhf,equip_digital,equip_packet,equip_pactor,
                 equip_vara_hf,equip_vara_fm,equip_aprs,equip_winlink,
                 equip_go_box,equip_generator,equip_battery,equip_vehicle,
                 created,modified)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,
                       ?,?,?,?,?,?,?,?,?,?,?,
                       ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                m.get("id", f"m-{int(time.time()*1000)}"),
                m.get("member_id", m.get("id", f"m-{int(time.time()*1000)}")),
                m.get("callsign", "").upper(),
                m.get("radio_id", ""),
                m.get("first_name", ""),
                m.get("last_name", ""),
                m.get("role", "Operator"),
                m.get("phone", ""),
                m.get("email", ""),
                m.get("grid", ""),
                m.get("lat"),
                m.get("lon"),
                m.get("notes", ""),
                int(bool(certs.get("ics100"))),
                int(bool(certs.get("ics200"))),
                int(bool(certs.get("ics300"))),
                int(bool(certs.get("ics400"))),
                int(bool(certs.get("ics700"))),
                int(bool(certs.get("ics800"))),
                int(bool(certs.get("emcomm1"))),
                int(bool(certs.get("emcomm2"))),
                int(bool(certs.get("cpr"))),
                int(bool(certs.get("first_aid"))),
                int(bool(certs.get("cert"))),
                int(bool(equip.get("hf"))),
                int(bool(equip.get("vhf"))),
                int(bool(equip.get("digital"))),
                int(bool(equip.get("packet"))),
                int(bool(equip.get("pactor"))),
                int(bool(equip.get("vara_hf"))),
                int(bool(equip.get("vara_fm"))),
                int(bool(equip.get("aprs"))),
                int(bool(equip.get("winlink"))),
                int(bool(equip.get("go_box"))),
                int(bool(equip.get("generator"))),
                int(bool(equip.get("battery"))),
                int(bool(equip.get("vehicle"))),
                m.get("created", utcnow()),
                m.get("modified", utcnow()),
            ))
            count += 1
        for a in data.get("activations", []):
            conn.execute("""
                INSERT OR IGNORE INTO activations
                (id,callsign,net_id,incident_id,role,location,
                 checked_in,checked_out,notes)
                VALUES(?,?,?,?,?,?,?,?,?)
            """, (
                a.get("id", f"a-{int(time.time()*1000)}"),
                a.get("callsign", ""),
                a.get("net_id", ""),
                a.get("incident_id", ""),
                a.get("role", ""),
                a.get("location", ""),
                a.get("checked_in", utcnow()),
                a.get("checked_out"),
                a.get("notes", ""),
            ))
        conn.commit()
        return count

    total += _migrate_json_file(DATA / "roster.json", "roster", migrate_roster)

    # ── Resources ────────────────────────────────────────────────────────────
    def migrate_resources(data):
        for r in (data if isinstance(data, list) else []):
            conn.execute("""
                INSERT OR IGNORE INTO resources
                (id,name,type,capability,status,assignment,contact,notes,created,updated)
                VALUES(?,?,?,?,?,?,?,?,?,?)
            """, (
                r.get("id", f"r-{int(time.time()*1000)}"),
                r.get("name", ""),
                r.get("type", ""),
                r.get("capability", ""),
                r.get("status", "Available"),
                r.get("assignment", ""),
                r.get("contact", ""),
                r.get("notes", ""),
                r.get("created", utcnow()),
                r.get("updated", utcnow()),
            ))
        conn.commit()
        return len(data) if isinstance(data, list) else 0

    total += _migrate_json_file(DATA / "resources.json", "resources", migrate_resources)

    # ── Map state ─────────────────────────────────────────────────────────────
    def migrate_mapstate(data):
        conn.execute("""
            UPDATE map_state SET shapes=?, markers=?, updated=? WHERE id=1
        """, (jdump(data.get("shapes", [])), jdump(data.get("markers", [])), utcnow()))
        conn.commit()
        return 1

    _migrate_json_file(DATA / "mapstate.json", "mapstate", migrate_mapstate)

    def migrate_resmap(data):
        conn.execute("""
            UPDATE resmap_state SET markers=?, updated=? WHERE id=1
        """, (jdump(data.get("markers", [])), utcnow()))
        conn.commit()
        return 1

    _migrate_json_file(DATA / "resmap.json", "resmap", migrate_resmap)

    # ── DMS state ─────────────────────────────────────────────────────────────
    def migrate_dms(data):
        conn.execute("""
            UPDATE dms_state SET
                state=?, armed_nets=?, threshold_min=?,
                last_activity=?, armed_at=?, triggered_at=?
            WHERE id=1
        """, (
            data.get("state", "disarmed"),
            jdump(data.get("armed_nets", [])),
            data.get("threshold_min", 30),
            data.get("last_activity"),
            data.get("armed_at"),
            data.get("triggered_at"),
        ))
        conn.commit()
        return 1

    _migrate_json_file(DATA / "dms_state.json", "dms_state", migrate_dms)

    # ── Station config ────────────────────────────────────────────────────────
    def migrate_station(data):
        conn.execute("""
            UPDATE station_config SET
                callsign=?, lat=?, lon=?, gps_enabled=?,
                gps_device=?, gps_last_fix=?, configured_at=?
            WHERE id=1
        """, (
            data.get("callsign", "W8EOC"),
            data.get("lat", 42.3247),
            data.get("lon", -88.3822),
            1 if data.get("gps_enabled", True) else 0,
            data.get("gps_device", "/dev/gps0"),
            data.get("gps_last_fix"),
            data.get("configured_at", utcnow()),
        ))
        conn.commit()
        return 1

    _migrate_json_file(DATA / "station_config.json", "station_config", migrate_station)

    # ── Repeaters ────────────────────────────────────────────────────────────
    def migrate_repeaters(data):
        reps = data if isinstance(data, list) else []
        for r in reps:
            conn.execute("""
                INSERT OR IGNORE INTO repeaters
                (callsign,output_freq,input_freq,tone,tone_input,mode,
                 digital_code,city,state,county,lat,lon,status,use_type,
                 ares,races,skywarn,echolink,allstar,sponsor,notes,updated,source)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                r.get("callsign", r.get("Callsign", "")),
                r.get("output_freq", r.get("Frequency", "")),
                r.get("input_freq", r.get("Input", "")),
                r.get("tone", r.get("PL Tone", r.get("Tone", ""))),
                r.get("tone_input", ""),
                r.get("mode", r.get("Mode", "FM")),
                r.get("digital_code", r.get("Digital Code", "")),
                r.get("city", r.get("City", "")),
                r.get("state", r.get("State", "")),
                r.get("county", r.get("County", "")),
                r.get("lat", r.get("Lat")),
                r.get("lon", r.get("Long")),
                r.get("status", r.get("Status", "On-Air")),
                r.get("use", r.get("Use", "Open")),
                1 if r.get("ares", r.get("ARES", "No")) not in ("No", "", False, 0) else 0,
                1 if r.get("races", r.get("RACES", "No")) not in ("No", "", False, 0) else 0,
                1 if r.get("skywarn", r.get("SKYWARN", "No")) not in ("No", "", False, 0) else 0,
                1 if r.get("echolink", r.get("EchoLink", "No")) not in ("No", "", False, 0) else 0,
                1 if r.get("allstar", r.get("AllStar", "No")) not in ("No", "", False, 0) else 0,
                r.get("sponsor", ""),
                r.get("notes", r.get("Notes", "")),
                r.get("updated", utcnow()),
                r.get("source", ""),
            ))
        conn.commit()
        return len(reps)

    total += _migrate_json_file(DATA / "repeaters.json", "repeaters", migrate_repeaters)

    # ── Standalone forms (forms/*.json) ───────────────────────────────────────
    forms_dir = DATA / "forms"
    if forms_dir.exists():
        for jf in forms_dir.glob("*.json"):
            try:
                fd = json.loads(jf.read_text())
                fid = jf.stem
                conn.execute("""
                    INSERT OR IGNORE INTO forms
                    (id,form_type,incident_id,summary,data,created,updated)
                    VALUES(?,?,?,?,?,?,?)
                """, (
                    fid,
                    fd.get("form_type", "unknown"),
                    fd.get("incident_id", ""),
                    fd.get("summary", ""),
                    jdump(fd),
                    fd.get("created", utcnow()),
                    fd.get("updated", fd.get("created", utcnow())),
                ))
                conn.commit()
                jf.rename(jf.with_suffix(".migrated"))
                total += 1
            except Exception as e:
                log.warning(f"  Form migration error {jf}: {e}")

    # ── ICS data ──────────────────────────────────────────────────────────────
    ics_data = DATA / "ics"

    def migrate_incidents(data):
        incs = data if isinstance(data, list) else []
        for inc in incs:
            conn.execute("""
                INSERT OR IGNORE INTO incidents
                (id,name,type,status,jurisdiction,incident_commander,
                 location,summary,current_period,started,updated,closed)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                inc["id"],
                inc.get("name", ""),
                inc.get("type", ""),
                inc.get("status", "active"),
                inc.get("jurisdiction", ""),
                inc.get("incident_commander", ""),
                inc.get("location", ""),
                inc.get("summary", ""),
                inc.get("current_period", 1),
                inc.get("created", utcnow()),
                inc.get("updated"),
                inc.get("closed"),
            ))
        conn.commit()
        return len(incs)

    _migrate_json_file(ics_data / "incidents.json", "incidents", migrate_incidents)

    def migrate_periods(data):
        count = 0
        for inc_id, periods in (data if isinstance(data, dict) else {}).items():
            for p in periods:
                pid = f"per-{inc_id}-{p.get('period', count)}"
                conn.execute("""
                    INSERT OR IGNORE INTO ics_periods
                    (id,incident_id,period_num,started,objectives)
                    VALUES(?,?,?,?,?)
                """, (
                    pid, inc_id,
                    p.get("period", 1),
                    p.get("started", utcnow()),
                    p.get("objectives", ""),
                ))
                count += 1
        conn.commit()
        return count

    _migrate_json_file(ics_data / "periods.json", "ics_periods", migrate_periods)

    def migrate_tcards(data):
        cards = data if isinstance(data, list) else []
        for c in cards:
            conn.execute("""
                INSERT OR IGNORE INTO ics_tcards
                (id,incident_id,resource_id,resource_name,type,
                 status,assignment,contact,created,updated)
                VALUES(?,?,?,?,?,?,?,?,?,?)
            """, (
                c.get("id", f"tc-{int(time.time()*1000)}"),
                c.get("incident_id", ""),
                c.get("resource_id", ""),
                c.get("resource_name", ""),
                c.get("type", ""),
                c.get("status", "Available"),
                c.get("assignment", ""),
                c.get("contact", ""),
                c.get("created", utcnow()),
                c.get("updated", utcnow()),
            ))
        conn.commit()
        return len(cards)

    _migrate_json_file(ics_data / "tcards.json", "ics_tcards", migrate_tcards)

    def migrate_ics_resources(data):
        items = data if isinstance(data, list) else []
        for r in items:
            conn.execute("""
                INSERT OR IGNORE INTO ics_resources
                (id,incident_id,resource_id,name,type,capability,
                 status,assignment,contact,created,updated)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """, (
                r.get("id", f"icsres-{int(time.time()*1000)}"),
                r.get("incident_id", ""),
                r.get("resource_id", ""),
                r.get("name", ""),
                r.get("type", ""),
                r.get("capability", ""),
                r.get("status", "Available"),
                r.get("assignment", ""),
                r.get("contact", ""),
                r.get("created", utcnow()),
                r.get("updated", utcnow()),
            ))
        conn.commit()
        return len(items)

    _migrate_json_file(ics_data / "ics_resources.json", "ics_resources", migrate_ics_resources)

    def migrate_activity(data):
        entries = data if isinstance(data, list) else []
        for e in entries:
            conn.execute("""
                INSERT INTO activity_log(incident_id,section,action,detail,timestamp)
                VALUES(?,?,?,?,?)
            """, (
                e.get("incident_id", ""),
                e.get("section", ""),
                e.get("action", ""),
                e.get("detail", ""),
                e.get("timestamp", utcnow()),
            ))
        conn.commit()
        return len(entries)

    _migrate_json_file(ics_data / "activity_feed.json", "activity_log", migrate_activity)

    # ── ICS form files ────────────────────────────────────────────────────────
    ics_forms_dir = ics_data / "forms"
    if ics_forms_dir.exists():
        for type_dir in ics_forms_dir.iterdir():
            if type_dir.is_dir():
                form_type = type_dir.name
                for jf in type_dir.glob("*.json"):
                    try:
                        fd = json.loads(jf.read_text())
                        conn.execute("""
                            INSERT OR IGNORE INTO ics_forms
                            (id,incident_id,form_type,period,summary,data,created,updated)
                            VALUES(?,?,?,?,?,?,?,?)
                        """, (
                            jf.stem,
                            fd.get("incident_id", ""),
                            form_type,
                            fd.get("period", 1),
                            fd.get("summary", ""),
                            jdump(fd),
                            fd.get("created", utcnow()),
                            fd.get("updated", fd.get("created", utcnow())),
                        ))
                        conn.commit()
                        jf.rename(jf.with_suffix(".migrated"))
                        total += 1
                    except Exception as e:
                        log.warning(f"  ICS form migration error {jf}: {e}")

    # ── Reference library ─────────────────────────────────────────────────────
    ref_index = DATA / "refs" / "index.json"

    def migrate_refs(data):
        docs = data if isinstance(data, list) else []
        for d in docs:
            conn.execute("""
                INSERT OR IGNORE INTO ref_documents
                (id,title,filename,stored_name,category,sections,description,
                 tags,source,applies_to,revision,expires,content_type,
                 size_bytes,sha256,uploaded,modified,downloads,last_downloaded)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                d.get("id", f"ref_{int(time.time()*1000):x}"),
                d.get("title", ""),
                d.get("filename", ""),
                d.get("stored_name", ""),
                d.get("category", "other"),
                jdump(d.get("sections", [d.get("section", "amateur")])),
                d.get("description", ""),
                jdump(d.get("tags", [])),
                d.get("source", ""),
                d.get("applies_to", ""),
                d.get("revision", ""),
                d.get("expires"),
                d.get("content_type", ""),
                d.get("size_bytes", 0),
                d.get("sha256", ""),
                d.get("uploaded", utcnow()),
                d.get("modified"),
                d.get("downloads", 0),
                d.get("last_downloaded"),
            ))
        conn.commit()
        return len(docs)

    _migrate_json_file(ref_index, "ref_documents", migrate_refs)

    # ── Preflight history ─────────────────────────────────────────────────────
    def migrate_preflight(data):
        if isinstance(data, dict):
            data = [data]
        for p in (data if isinstance(data, list) else []):
            conn.execute("""
                INSERT INTO preflight_runs(verdict,checks,timestamp)
                VALUES(?,?,?)
            """, (
                p.get("verdict", "?"),
                jdump(p.get("checks", {})),
                p.get("timestamp", utcnow()),
            ))
        conn.commit()
        return len(data) if isinstance(data, list) else 0

    _migrate_json_file(DATA / "preflight.json", "preflight", migrate_preflight)

    if total:
        log.info(f"Migration complete — {total} records imported")
    else:
        log.info("No legacy JSON files found — starting fresh")


# ── Startup ────────────────────────────────────────────────────────────────────
def startup():
    """Call once at server startup: create schema, run migration."""
    init_db()
    _alter_existing_tables()
    migrate_from_json()
    _seed_defaults()


def _seed_defaults():
    """Seed default McHenry County facilities if facilities table is empty."""
    conn = db()
    # Facilities are stored as resources with type='Facility'
    n = conn.execute(
        "SELECT COUNT(*) FROM resources WHERE type='Facility'"
    ).fetchone()[0]
    if n > 0:
        return  # Already seeded

    defaults = [
        ("McHenry County EOC", "Facility",
         "Primary Emergency Operations Center",
         "667 Ware Rd, Woodstock IL 60098 · Sheriff frequency: 154.785 MHz / 107.2 Hz",
         "available"),
        ("Centegra Hospital — Woodstock", "Facility",
         "Hospital / Mass Casualty staging",
         "3701 Doty Rd, Woodstock IL 60098 · ER entrance on north side",
         "available"),
        ("McHenry County Fairgrounds — Staging", "Facility",
         "Primary staging area / personnel assembly",
         "11900 IL-Route 14, Woodstock IL 60098 · Use Gate 3",
         "available"),
        ("Centegra Hospital — McHenry", "Facility",
         "Secondary hospital / alternate staging",
         "4201 Medical Center Dr, McHenry IL 60050",
         "available"),
    ]
    now = utcnow()
    for name, rtype, capability, notes, status in defaults:
        rid = f"fac-{int(__import__('time').time()*1000) % 1000000}"
        conn.execute("""
            INSERT OR IGNORE INTO resources
            (id,name,type,capability,status,assignment,contact,notes,created,updated)
            VALUES(?,?,?,?,?,?,?,?,?,?)
        """, (rid, name, rtype, capability, status, "", "", notes, now, now))
        __import__('time').sleep(0.001)  # ensure unique IDs
    conn.commit()
    log.info("Seeded 4 default McHenry County facilities")


def _alter_existing_tables():
    """Add new columns to existing databases that predate this version."""
    conn = db()
    existing = {r[1] for r in conn.execute("PRAGMA table_info(roster)").fetchall()}
    additions = [
        ("member_id",      "TEXT NOT NULL DEFAULT ''"),
        ("radio_id",       "TEXT DEFAULT ''"),
        ("member_type",    "TEXT NOT NULL DEFAULT 'member'"),
        ("visitor_agency", "TEXT DEFAULT ''"),
    ]
    for col, defn in additions:
        if col not in existing:
            try:
                conn.execute(f"ALTER TABLE roster ADD COLUMN {col} {defn}")
                conn.commit()
                log.info(f"Added column roster.{col}")
            except Exception as e:
                log.warning(f"Could not add column {col}: {e}")

    # net_entries new columns
    ne_existing = {r[1] for r in conn.execute("PRAGMA table_info(net_entries)").fetchall()}
    ne_additions = [
        ("member_id",      "TEXT DEFAULT ''"),
        ("visitor_agency", "TEXT DEFAULT ''"),
        ("visitor",        "INTEGER NOT NULL DEFAULT 0"),
        ("promoted",       "INTEGER NOT NULL DEFAULT 0"),
    ]
    for col, defn in ne_additions:
        if col not in ne_existing:
            try:
                conn.execute(f"ALTER TABLE net_entries ADD COLUMN {col} {defn}")
                conn.commit()
                log.info(f"Added column net_entries.{col}")
            except Exception as e:
                log.warning(f"Could not add net_entries.{col}: {e}")
