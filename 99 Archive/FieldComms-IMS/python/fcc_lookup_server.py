#!/usr/bin/env python3
"""
FieldComms EmComm Main API Server  —  Port 5050
All runtime data stored in /opt/fieldcomms/data/fieldcomms.db via db.py
FCC callsign lookup uses the separate fcc.db (read-only).
"""

import json, sqlite3, time, threading, subprocess, socket
import logging, sys
from datetime import datetime, timezone
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import db
from db import get_conn, utcnow, jdump, jload, row_to_dict, rows_to_list

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s [fcc-lookup] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout),
              logging.FileHandler('/var/log/fieldcomms-api.log', mode='a')])
log = logging.getLogger('fcc-lookup')

BASE    = Path("/opt/fieldcomms")
DATA    = BASE / "data"
FCC_DB  = DATA / "fcc.db"

# ── FCC callsign lookup (separate read-only database) ────────────────────────
def fcc_lookup(callsign):
    if not FCC_DB.exists():
        return None
    call = callsign.upper().strip()
    try:
        conn = sqlite3.connect(str(FCC_DB))
        conn.row_factory = sqlite3.Row
        row = conn.execute("""
            SELECT e.callsign, e.first_name, e.last_name, e.city, e.state,
                   e.zip_code, h.license_status, h.grant_date, h.expired_date,
                   a.operator_class, a.group_code
            FROM en e
            LEFT JOIN hd h ON e.unique_system_id = h.unique_system_id
            LEFT JOIN am a ON e.unique_system_id = a.unique_system_id
            WHERE UPPER(e.callsign) = ?
            LIMIT 1
        """, (call,)).fetchone()
        conn.close()
        if row:
            classes = {"A":"Amateur Extra","G":"General","T":"Technician",
                       "N":"Novice","P":"Advanced"}
            return {
                "callsign":       row["callsign"],
                "name":           f"{row['first_name'] or ''} {row['last_name'] or ''}".strip(),
                "first_name":     row["first_name"] or "",
                "last_name":      row["last_name"] or "",
                "city":           row["city"] or "",
                "state":          row["state"] or "",
                "zip":            row["zip_code"] or "",
                "license_status": row["license_status"] or "",
                "operator_class": classes.get(row["operator_class"] or "",
                                              row["operator_class"] or "Unknown"),
                "class_code":     row["operator_class"] or "",
                "grant_date":     row["grant_date"] or "",
                "expired_date":   row["expired_date"] or "",
                "group_code":     row["group_code"] or "",
            }
    except Exception as e:
        log.warning(f"FCC lookup error: {e}")
    return None

# ── GPS / station position ────────────────────────────────────────────────────
_pos_cache = {"ts": 0}
_POS_TTL   = 10

def get_station_position():
    global _pos_cache
    now = time.time()
    if now - _pos_cache.get("ts", 0) < _POS_TTL:
        return _pos_cache
    c = get_conn()
    row = c.execute("SELECT callsign,lat,lon FROM station_config WHERE id=1").fetchone()
    cfg_call = row["callsign"] if row else "W8EOC"
    cfg_lat  = row["lat"]  if row else 42.3247
    cfg_lon  = row["lon"]  if row else -88.3822
    try:
        s = socket.socket()
        s.settimeout(1.5)
        s.connect(("127.0.0.1", 2947))
        s.send(b"?POLL;\n")
        time.sleep(0.3)
        data = b""
        s.settimeout(0.5)
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk: break
                data += chunk
        except Exception:
            pass
        s.close()
        for line in data.decode(errors="ignore").splitlines():
            if '"class":"TPV"' in line:
                tpv  = json.loads(line)
                mode = tpv.get("mode", 0)
                lat  = tpv.get("lat")
                lon  = tpv.get("lon")
                if mode >= 2 and lat and lon:
                    c.execute("UPDATE station_config SET lat=?,lon=?,gps_last_fix=? WHERE id=1",
                              (round(lat,6), round(lon,6), tpv.get("time","")))
                    c.commit()
                    _pos_cache = {"lat":round(lat,6),"lon":round(lon,6),
                        "alt":tpv.get("alt"),"speed":tpv.get("speed"),
                        "track":tpv.get("track"),"time":tpv.get("time"),
                        "fix":True,"mode":mode,
                        "mode_str":"3D Fix" if mode==3 else "2D Fix",
                        "source":"gps","callsign":cfg_call,"ts":now}
                    return _pos_cache
    except Exception:
        pass
    _pos_cache = {"lat":cfg_lat,"lon":cfg_lon,"alt":None,"speed":None,
        "track":None,"time":None,"fix":False,"mode":0,"mode_str":"No Fix",
        "source":"config" if cfg_lat!=42.3247 else "default",
        "callsign":cfg_call,"ts":now}
    return _pos_cache

# ── Roster helpers ────────────────────────────────────────────────────────────
CERT_COLS  = ["ics100","ics200","ics300","ics400","ics700","ics800",
              "emcomm1","emcomm2","cpr","first_aid","cert"]
EQUIP_COLS = ["hf","vhf","digital","packet","pactor","vara_hf","vara_fm",
              "aprs","winlink","go_box","generator","battery","vehicle"]

def member_to_dict(row):
    if row is None: return None
    d = dict(row)
    d["certifications"] = {c: bool(d.pop(f"cert_{c}", 0))  for c in CERT_COLS}
    d["equipment"]      = {e: bool(d.pop(f"equip_{e}", 0)) for e in EQUIP_COLS}
    # Ensure member_id always present (may be missing on older rows)
    if not d.get("member_id"):
        d["member_id"] = d.get("id", "")
    # display_id priority: callsign → radio_id → member_id
    d["display_id"] = (d.get("callsign") or d.get("radio_id") or
                       d.get("member_id") or d.get("id",""))
    d["is_ham"]     = bool(d.get("callsign"))
    d["is_visitor"] = d.get("member_type","member") in ("visitor","mutual_aid")
    return d

def member_upsert_sql():
    cols  = (["id","member_id","callsign","radio_id","member_type",
               "visitor_agency","first_name","last_name",
               "role","phone","email","grid","lat","lon","notes"] +
             [f"cert_{c}" for c in CERT_COLS] +
             [f"equip_{e}" for e in EQUIP_COLS] +
             ["created","modified"])
    up    = [c for c in cols if c not in ("id","created")]
    ph    = ",".join("?"*len(cols))
    upd   = ",".join(f"{c}=excluded.{c}" for c in up)
    return f"INSERT INTO roster({','.join(cols)}) VALUES({ph}) ON CONFLICT(id) DO UPDATE SET {upd}"

def member_vals(m, mid, now):
    certs = m.get("certifications",{}) or {}
    equip = m.get("equipment",{}) or {}
    # Generate member_id if not provided: ESV- + 4-digit sequence from id
    member_id = m.get("member_id","").strip()
    if not member_id:
        member_id = m.get("id", mid)
    mtype = m.get("member_type","member").strip() or "member"
    return [mid, member_id,
            (m.get("callsign","")).upper(),
            m.get("radio_id",""),
            mtype,
            m.get("visitor_agency",""),
            m.get("first_name",""), m.get("last_name",""),
            m.get("role","Operator"), m.get("phone",""), m.get("email",""),
            m.get("grid",""), m.get("lat"), m.get("lon"), m.get("notes",""),
            *(int(bool(certs.get(c))) for c in CERT_COLS),
            *(int(bool(equip.get(e))) for e in EQUIP_COLS),
            m.get("created", now), now]

# ── HTTP Handler ──────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def cors(self):
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.send_header("Access-Control-Allow-Methods","GET,POST,PUT,DELETE,OPTIONS")

    def send_json(self, obj, code=200):
        body = json.dumps(obj, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",len(body))
        self.cors(); self.end_headers(); self.wfile.write(body)

    def read_body(self):
        n = int(self.headers.get("Content-Length",0))
        return json.loads(self.rfile.read(n)) if n else {}

    def do_OPTIONS(self):
        self.send_response(204); self.cors(); self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/")
        qs     = parse_qs(parsed.query)
        c      = get_conn()

        if path == "/api/fcc":
            call = qs.get("call",[""])[0]
            if not call: return self.send_json({"error":"Missing call"},400)
            r = fcc_lookup(call)
            return self.send_json(r) if r else self.send_json({"error":"Not found"},404)

        elif path == "/api/fcc/status":
            if FCC_DB.exists():
                stat = FCC_DB.stat()
                age  = (time.time()-stat.st_mtime)/86400
                fc   = sqlite3.connect(str(FCC_DB))
                n    = fc.execute("SELECT COUNT(*) FROM en").fetchone()[0]
                fc.close()
                return self.send_json({"exists":True,"age_days":round(age,1),
                    "records":n,"path":str(FCC_DB),
                    "modified":datetime.fromtimestamp(stat.st_mtime).isoformat()})
            return self.send_json({"exists":False,"age_days":None,"records":0})

        elif path == "/api/position":
            return self.send_json(get_station_position())

        elif path == "/api/nets":
            sc = qs.get("starcom",[None])[0]
            sql = ("SELECT id,name,type,starcom,drill,active,created,closed,freq,ncs,"
                   "(SELECT COUNT(*) FROM net_entries e WHERE e.net_id=n.id) entry_count"
                   " FROM nets n")
            if sc is not None:
                sql += " WHERE starcom=?"; params = [1 if sc.lower()=="true" else 0]
            else:
                params = []
            sql += " ORDER BY created DESC"
            return self.send_json(rows_to_list(c.execute(sql,params).fetchall()))

        elif path.startswith("/api/nets/"):
            parts  = path.split("/"); net_id = parts[3] if len(parts)>3 else ""
            sub    = "/".join(parts[4:]) if len(parts)>4 else ""
            row    = c.execute("SELECT * FROM nets WHERE id=?",(net_id,)).fetchone()
            if not row: return self.send_json({"error":"Not found"},404)
            if sub in ("",""):
                net = dict(row)
                net["roster_chips"] = jload(net.get("roster_chips"),[])
                net["entries"] = rows_to_list(c.execute(
                    "SELECT * FROM net_entries WHERE net_id=? ORDER BY timestamp",(net_id,)).fetchall())
                net["traffic"] = rows_to_list(c.execute(
                    "SELECT * FROM net_traffic WHERE net_id=? ORDER BY timestamp",(net_id,)).fetchall())
                return self.send_json(net)
            elif sub == "entries":
                return self.send_json(rows_to_list(c.execute(
                    "SELECT * FROM net_entries WHERE net_id=? ORDER BY timestamp",(net_id,)).fetchall()))
            elif sub == "traffic":
                return self.send_json(rows_to_list(c.execute(
                    "SELECT * FROM net_traffic WHERE net_id=? ORDER BY timestamp",(net_id,)).fetchall()))
            elif sub == "roster_chips":
                return self.send_json(jload(row["roster_chips"],[]))
            return self.send_json({"error":"Not found"},404)

        elif path == "/api/roster":
            members = [member_to_dict(r) for r in
                       c.execute("SELECT * FROM roster ORDER BY callsign").fetchall()]
            acts = rows_to_list(c.execute(
                "SELECT * FROM activations ORDER BY checked_in DESC").fetchall())
            return self.send_json({"members":members,"activations":acts})

        elif path == "/api/roster/members":
            return self.send_json([member_to_dict(r) for r in
                c.execute("SELECT * FROM roster ORDER BY callsign").fetchall()])

        elif path == "/api/roster/activations":
            return self.send_json(rows_to_list(c.execute(
                "SELECT * FROM activations ORDER BY checked_in DESC").fetchall()))

        elif path == "/api/resources":
            return self.send_json(rows_to_list(
                c.execute("SELECT * FROM resources ORDER BY name").fetchall()))

        elif path == "/api/mapstate":
            row = c.execute("SELECT * FROM map_state WHERE id=1").fetchone()
            return self.send_json({
                "shapes":  jload(row["shapes"],[]) if row else [],
                "markers": jload(row["markers"],[]) if row else []})

        elif path == "/api/resmap":
            row = c.execute("SELECT * FROM resmap_state WHERE id=1").fetchone()
            return self.send_json({"markers":jload(row["markers"],[]) if row else []})

        elif path == "/api/repeaters":
            band  = qs.get("band",[None])[0]
            state = qs.get("state",[None])[0]
            srch  = qs.get("q",[""])[0].lower()
            sql   = "SELECT * FROM repeaters WHERE 1=1"; params=[]
            if band:  sql+=" AND mode LIKE ?"; params.append(f"%{band}%")
            if state: sql+=" AND UPPER(state)=?"; params.append(state.upper())
            reps = rows_to_list(c.execute(sql+" ORDER BY state,city",params).fetchall())
            # Add page-friendly aliases so the web UI reads ARES/RACES/SKYWARN and Use.
            for r in reps:
                r["use"]     = r.get("use_type","Open")
                r["ARES"]    = "Yes" if r.get("ares") else ""
                r["RACES"]   = "Yes" if r.get("races") else ""
                r["SKYWARN"] = "Yes" if r.get("skywarn") else ""
                r["last_updated"] = r.get("updated","")
            if srch: reps=[r for r in reps if srch in json.dumps(r).lower()]
            return self.send_json(reps)

        elif path == "/api/dms":
            row = c.execute("SELECT * FROM dms_state WHERE id=1").fetchone()
            if row:
                d=dict(row); d["armed_nets"]=jload(d.get("armed_nets"),[])
                return self.send_json(d)
            return self.send_json({"state":"disarmed","armed_nets":[],"threshold_min":30})

        elif path == "/api/forms":
            ft = qs.get("type",["all"])[0]
            if ft=="all":
                rows=c.execute("SELECT id,form_type,incident_id,summary,created,updated FROM forms ORDER BY created DESC").fetchall()
            else:
                rows=c.execute("SELECT id,form_type,incident_id,summary,created,updated FROM forms WHERE form_type=? ORDER BY created DESC",(ft,)).fetchall()
            return self.send_json(rows_to_list(rows))

        elif path.startswith("/api/forms/"):
            fid = path.split("/api/forms/")[1]
            row = c.execute("SELECT * FROM forms WHERE id=?",(fid,)).fetchone()
            if row:
                d=dict(row); d.update(jload(d.get("data"),{}))
                return self.send_json(d)
            return self.send_json({"error":"Not found"},404)

        elif path == "/api/preflight":
            return self.send_json(self._preflight_check())

        elif path == "/wan/status" or path == "/api/wan/status":
            # Serve WAN status written by wan_monitor.py
            wan_file = Path("/opt/fieldcomms/data/wan_status.json")
            try:
                if wan_file.exists():
                    return self.send_json(json.loads(wan_file.read_text()))
                return self.send_json({"active_source": "unknown",
                    "error": "wan_monitor has not written status yet"})
            except Exception as e:
                return self.send_json({"active_source": "unknown",
                    "error": str(e)}, 500)

        elif path == "/amprgate/status" or path == "/api/amprgate/status":
            # Serve AMPRNet gateway status written by amprgate_poll.py
            ampr_file = Path("/opt/fieldcomms/data/amprgate_status.json")
            try:
                if ampr_file.exists():
                    return self.send_json(json.loads(ampr_file.read_text()))
                return self.send_json({"tunnel": "unknown",
                    "error": "amprgate_poll has not written status yet"})
            except Exception as e:
                return self.send_json({"tunnel": "unknown",
                    "error": str(e)}, 500)

        elif path == "/api/status":
            return self.send_json({"service":"fcc-lookup","version":"2.0.0",
                "utc":utcnow(),"fcc_db":FCC_DB.exists(),"db":str(db.DB_PATH)})

        else:
            self.send_json({"error":"Not found"},404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/")
        body   = self.read_body()
        c      = get_conn()
        now    = utcnow()

        if path == "/api/nets":
            net_id = body.get("id") or f"net-{int(time.time())}"
            sc = 1 if (body.get("starcom") or net_id.startswith("sc-")) else 0
            c.execute("""
                INSERT INTO nets(id,name,type,starcom,drill,active,freq,ncs,created,net_opened,roster_chips)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET name=excluded.name,type=excluded.type,
                drill=excluded.drill,active=excluded.active,freq=excluded.freq,
                ncs=excluded.ncs,roster_chips=excluded.roster_chips
            """,(net_id,body.get("name",f"Net {net_id}"),
                 body.get("type","SC Dispatch" if sc else "Amateur"),sc,
                 1 if body.get("drill") else 0,1 if body.get("active",True) else 0,
                 body.get("freq",""),body.get("ncs",""),now,now,
                 jdump(body.get("roster_chips",[]))))
            c.commit()
            return self.send_json({"ok":True,"id":net_id})

        elif path.startswith("/api/nets/"):
            parts  = path.split("/"); net_id=parts[3] if len(parts)>3 else ""
            sub    = parts[4] if len(parts)>4 else ""

            if sub == "entry":
                eid = body.get("id") or f"e-{int(time.time()*1000)}"
                # Look up EMA ID from roster by callsign (ham net) or radio_id (Starcom)
                ema_id = ""
                callsign = body.get("callsign","").strip().upper()
                radio_id = body.get("radio_id","").strip()
                if callsign:
                    row = c.execute(
                        "SELECT member_id FROM roster WHERE UPPER(callsign)=? AND member_type='member'",
                        (callsign,)).fetchone()
                    if row: ema_id = row[0]
                if not ema_id and radio_id:
                    row = c.execute(
                        "SELECT member_id FROM roster WHERE radio_id=? AND member_type='member'",
                        (radio_id,)).fetchone()
                    if row: ema_id = row[0]
                c.execute("""INSERT OR REPLACE INTO net_entries
                    (id,net_id,callsign,member_id,radio_id,visitor_agency,
                     name,city,state,precedence,traffic,remarks,
                     walk_in,visitor,timestamp,ema_id)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (eid,net_id,
                     body.get("callsign",""),
                     body.get("member_id",""),
                     radio_id,
                     body.get("visitor_agency",""),
                     body.get("name",""),
                     body.get("city",""),body.get("state",""),
                     body.get("precedence","ROUTINE"),
                     body.get("traffic",""),body.get("remarks",""),
                     1 if body.get("walk_in") else 0,
                     1 if body.get("visitor") else 0,
                     now,ema_id))
                c.execute("UPDATE dms_state SET last_activity=? WHERE id=1",(now,))
                c.commit()
                return self.send_json({"ok":True,"entry":{**body,"id":eid,"timestamp":now,"ema_id":ema_id}})

            elif sub == "traffic":
                tid = body.get("id") or f"t-{int(time.time()*1000)}"
                c.execute("""INSERT OR REPLACE INTO net_traffic
                    (id,net_id,msg_number,from_call,to_call,precedence,handling,text,timestamp)
                    VALUES(?,?,?,?,?,?,?,?,?)""",
                    (tid,net_id,body.get("msg_number",""),body.get("from_call",""),
                     body.get("to_call",""),body.get("precedence","ROUTINE"),
                     body.get("handling",""),body.get("text",""),now))
                c.commit()
                return self.send_json({"ok":True,"msg":{**body,"id":tid,"timestamp":now}})

            elif sub == "update":
                updates={k:body[k] for k in("name","type","drill","active","freq","ncs") if k in body}
                if "roster_chips" in body: updates["roster_chips"]=jdump(body["roster_chips"])
                if updates:
                    sets=", ".join(f"{k}=?" for k in updates)
                    c.execute(f"UPDATE nets SET {sets} WHERE id=?",(*updates.values(),net_id))
                    c.commit()
                return self.send_json({"ok":True})

            elif sub == "checkout":
                # Check out a single entry before net closes
                entry_id = body.get("entry_id","")
                if not entry_id:
                    return self.send_json({"error":"entry_id required"},400)
                c.execute("UPDATE net_entries SET checkout_time=? WHERE id=? AND net_id=?",
                          (now,entry_id,net_id))
                c.commit()
                return self.send_json({"ok":True,"checkout_time":now})

            elif sub == "open":
                # Explicitly open net (record net_opened timestamp)
                c.execute("UPDATE nets SET net_opened=?,active=1 WHERE id=?",(now,net_id))
                c.commit()
                return self.send_json({"ok":True,"net_opened":now})

            elif sub == "close":
                # Auto-checkout any entries that haven't checked out
                c.execute("""UPDATE net_entries SET checkout_time=?
                             WHERE net_id=? AND checkout_time IS NULL""",(now,net_id))
                c.execute("UPDATE nets SET active=0,net_closed=?,closed=? WHERE id=?",
                          (now,now,net_id))
                c.commit()
                return self.send_json({"ok":True,"net_closed":now})

        elif path == "/api/roster/members":
            mid = body.get("id") or f"m-{int(time.time()*1000)}"
            c.execute(member_upsert_sql(), member_vals(body,mid,now))
            c.commit()
            return self.send_json({"ok":True,"member":member_to_dict(
                c.execute("SELECT * FROM roster WHERE id=?",(mid,)).fetchone())})

        elif path == "/api/roster/activations":
            aid = body.get("id") or f"a-{int(time.time()*1000)}"
            c.execute("""INSERT OR REPLACE INTO activations
                (id,callsign,net_id,incident_id,role,location,checked_in,checked_out,notes)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (aid,body.get("callsign",""),body.get("net_id",""),
                 body.get("incident_id",""),body.get("role",""),
                 body.get("location",""),body.get("checked_in",now),
                 body.get("checked_out"),body.get("notes","")))
            c.commit()
            return self.send_json({"ok":True,"activation":{**body,"id":aid}})

        elif path == "/api/roster/promote":
            # Promote a walk-in / visitor to the roster
            # Body: entry data from a net_entry (callsign/name/radio_id etc.)
            mid = body.get("id") or f"m-{int(time.time()*1000)}"
            # Assign visitor member_id if no ESV number
            member_id = body.get("member_id","").strip()
            mtype = body.get("member_type","member")
            if not member_id:
                if mtype in ("visitor","mutual_aid"):
                    member_id = f"VIS-{int(time.time()*1000) % 100000:05d}"
                else:
                    member_id = f"ESV-{int(time.time()*1000) % 10000:04d}"
            c.execute(member_upsert_sql(), member_vals({
                **body,
                "id": mid,
                "member_id": member_id,
                "member_type": mtype,
            }, mid, now))
            # Mark the net_entry as promoted
            entry_id = body.get("entry_id","")
            if entry_id:
                c.execute("UPDATE net_entries SET promoted=1 WHERE id=?", (entry_id,))
            c.commit()
            return self.send_json({"ok": True, "member_id": member_id,
                                   "roster_id": mid})

        elif path == "/api/roster/import":
            added=0
            for m in body.get("members",[]):
                mid=m.get("id") or f"m-{int(time.time()*1000)+added}"
                c.execute(member_upsert_sql(), member_vals(m,mid,now))
                added+=1
            c.commit()
            return self.send_json({"ok":True,"added":added})

        elif path == "/api/resources":
            rid = body.get("id") or f"r-{int(time.time()*1000)}"
            c.execute("""INSERT OR REPLACE INTO resources
                (id,name,type,capability,status,assignment,contact,notes,created,updated)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (rid,body.get("name",""),body.get("type",""),body.get("capability",""),
                 body.get("status","Available"),body.get("assignment",""),
                 body.get("contact",""),body.get("notes",""),body.get("created",now),now))
            c.commit()
            return self.send_json({"ok":True,"resource":{**body,"id":rid,"updated":now}})

        elif path == "/api/mapstate":
            c.execute("UPDATE map_state SET shapes=?,markers=?,updated=? WHERE id=1",
                      (jdump(body.get("shapes",[])),jdump(body.get("markers",[])),now))
            c.commit(); return self.send_json({"ok":True})

        elif path == "/api/resmap":
            c.execute("UPDATE resmap_state SET markers=?,updated=? WHERE id=1",
                      (jdump(body.get("markers",[])),now))
            c.commit(); return self.send_json({"ok":True})

        elif path == "/api/forms":
            fid = body.get("id") or f"f-{int(time.time()*1000)}"
            body["id"]=fid; body.setdefault("created",now)
            c.execute("""INSERT OR REPLACE INTO forms
                (id,form_type,incident_id,summary,data,created,updated)
                VALUES(?,?,?,?,?,?,?)""",
                (fid,body.get("form_type","unknown"),body.get("incident_id",""),
                 body.get("summary",""),jdump(body),body.get("created",now),now))
            c.commit(); return self.send_json({"ok":True,"id":fid})

        elif path == "/api/dms/arm":
            c.execute("""UPDATE dms_state SET state='armed',armed_at=?,
                threshold_min=?,armed_nets=?,last_activity=? WHERE id=1""",
                (now,body.get("threshold_min",30),jdump(body.get("nets",[])),now))
            c.commit(); return self.send_json({"ok":True})

        elif path == "/api/dms/reset":
            row=c.execute("SELECT state FROM dms_state WHERE id=1").fetchone()
            ns="armed" if row and row["state"]!="disarmed" else "disarmed"
            c.execute("UPDATE dms_state SET state=?,triggered_at=NULL,last_activity=? WHERE id=1",(ns,now))
            c.commit(); return self.send_json({"ok":True})

        elif path == "/api/dms/disarm":
            c.execute("UPDATE dms_state SET state='disarmed' WHERE id=1")
            c.commit(); return self.send_json({"ok":True})

        else:
            self.send_json({"error":"Not found"},404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/")
        c      = get_conn()

        if path.startswith("/api/nets/"):
            c.execute("DELETE FROM nets WHERE id=?",(path.split("/api/nets/")[1],))
        elif path.startswith("/api/resources/"):
            c.execute("DELETE FROM resources WHERE id=?",(path.split("/api/resources/")[1],))
        elif path.startswith("/api/roster/members/"):
            c.execute("DELETE FROM roster WHERE id=?",(path.split("/api/roster/members/")[1],))
        elif path.startswith("/api/roster/activations/"):
            c.execute("DELETE FROM activations WHERE id=?",(path.split("/api/roster/activations/")[1],))
        elif path.startswith("/api/forms/"):
            c.execute("DELETE FROM forms WHERE id=?",(path.split("/api/forms/")[1],))
        else:
            return self.send_json({"error":"Not found"},404)
        c.commit()
        return self.send_json({"ok":True})

    def _preflight_check(self):
        results={}; c=get_conn(); now=utcnow()
        def svc(n):
            try:
                r=subprocess.run(["systemctl","is-active",n],capture_output=True,text=True,timeout=3)
                return r.stdout.strip()=="active"
            except: return False
        for n,lbl in [("nginx","Web Server"),("graywolf","Graywolf APRS"),
                      ("pat","Pat Winlink"),("fcc-lookup","FCC Lookup API"),
                      ("kiwix","Kiwix Library"),("gpsd","GPS Daemon"),
                      ("chrony","Time Sync"),("deadmans","Dead Man's Switch")]:
            results[n]={"ok":svc(n),"label":lbl}
        fcc_ok={"ok":False,"label":"FCC Database","detail":"Not found"}
        if FCC_DB.exists():
            try:
                fc=sqlite3.connect(str(FCC_DB))
                n=fc.execute("SELECT COUNT(*) FROM en").fetchone()[0]; fc.close()
                age=(time.time()-FCC_DB.stat().st_mtime)/86400
                fcc_ok={"ok":age<14,"label":"FCC Database","detail":f"{n:,} records, {age:.1f}d"}
            except Exception as e: fcc_ok["detail"]=str(e)
        results["fcc_db"]=fcc_ok
        gps_ok=False
        try:
            s=socket.socket(); s.settimeout(2); s.connect(("127.0.0.1",2947))
            s.send(b'?WATCH={"enable":true,"json":true}\n')
            d=s.recv(1024).decode(errors="ignore"); s.close()
            gps_ok='"class":"VERSION"' in d or '"class":"SKY"' in d
        except: pass
        results["gps_fix"]={"ok":gps_ok,"label":"GPS Fix"}
        ap_ok=False
        try:
            r=subprocess.run(["nmcli","-t","-f","NAME,TYPE,DEVICE","connection","show","--active"],
                             capture_output=True,text=True,timeout=3)
            ap_ok="wifi" in r.stdout.lower() and "EMCOMM" in r.stdout
        except: pass
        results["wifi_ap"]={"ok":ap_ok,"label":"EMCOMM-NET WiFi AP"}
        n_reps=c.execute("SELECT COUNT(*) FROM repeaters").fetchone()[0]
        results["repeater_db"]={"ok":n_reps>0,"label":"Repeater Database","detail":f"{n_reps} repeaters"}
        dms=c.execute("SELECT state FROM dms_state WHERE id=1").fetchone()
        dms_s=dms["state"] if dms else "disarmed"
        results["dms_state"]={"ok":dms_s!="triggered","label":"Dead Man's Switch","state":dms_s}
        critical=["nginx","fcc_lookup","wifi_ap"]; important=["graywolf","pat","fcc_db","gps_fix"]
        crit_ok=all(results[k]["ok"] for k in critical)
        imp_ok=all(results[k]["ok"] for k in important if k in results)
        verdict="GO" if (crit_ok and imp_ok) else "CAUTION" if crit_ok else "NO-GO"
        c.execute("INSERT INTO preflight_runs(verdict,checks,timestamp) VALUES(?,?,?)",
                  (verdict,jdump(results),now)); c.commit()
        return {"verdict":verdict,"checks":results,"timestamp":now}


def dms_monitor():
    while True:
        try:
            c=get_conn()
            row=c.execute("SELECT * FROM dms_state WHERE id=1").fetchone()
            if row and row["state"]=="armed":
                thr=(row["threshold_min"] or 30)*60; last=row["last_activity"]
                if last:
                    dt=datetime.fromisoformat(last.replace("Z","+00:00"))
                    el=(datetime.now(timezone.utc)-dt).total_seconds()
                    if el>thr:
                        c.execute("UPDATE dms_state SET state='triggered',triggered_at=? WHERE id=1",(utcnow(),))
                    elif el>thr*0.75:
                        c.execute("UPDATE dms_state SET state='warning' WHERE id=1")
                    c.commit()
        except Exception as e: log.warning(f"DMS monitor: {e}")
        time.sleep(30)


if __name__ == "__main__":
    db.startup()
    threading.Thread(target=dms_monitor, daemon=True).start()
    log.info("FCC Lookup API server on port 5050")
    HTTPServer(("0.0.0.0", 5050), Handler).serve_forever()
