#!/usr/bin/env python3
"""FieldComms ICS Platform API — Port 5055 (SQLite via db.py)"""

import json, time, sys, logging
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import db
from db import get_conn, utcnow, jdump, jload, rows_to_list, row_to_dict

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s [ics-platform] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout),
              logging.FileHandler('/var/log/fieldcomms-ics.log', mode='a')])
log = logging.getLogger('ics-platform')


def log_activity(incident_id, section, action, detail):
    get_conn().execute(
        "INSERT INTO activity_log(incident_id,section,action,detail,timestamp)"
        " VALUES(?,?,?,?,?)",
        (incident_id, section, action, detail, utcnow()))
    get_conn().commit()


class ICSHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def cors(self):
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.send_header("Access-Control-Allow-Methods","GET,POST,PUT,DELETE,OPTIONS")

    def send_json(self, obj, code=200):
        body=json.dumps(obj,default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",len(body))
        self.cors(); self.end_headers(); self.wfile.write(body)

    def read_body(self):
        n=int(self.headers.get("Content-Length",0))
        return json.loads(self.rfile.read(n)) if n else {}

    def do_OPTIONS(self):
        self.send_response(204); self.cors(); self.end_headers()

    def do_GET(self):
        parsed=urlparse(self.path); path=parsed.path.rstrip("/")
        qs=parse_qs(parsed.query); c=get_conn()

        if path == "/api/ics/incidents":
            return self.send_json(rows_to_list(
                c.execute("SELECT * FROM incidents ORDER BY started DESC").fetchall()))

        elif path.startswith("/api/ics/incidents/"):
            inc_id=path.split("/api/ics/incidents/")[1].split("/")[0]
            sub=path[len(f"/api/ics/incidents/{inc_id}"):]
            row=c.execute("SELECT * FROM incidents WHERE id=?",(inc_id,)).fetchone()
            if not row: return self.send_json({"error":"Not found"},404)
            if sub in ("","/"): return self.send_json(row_to_dict(row))
            elif sub=="/periods":
                return self.send_json(rows_to_list(c.execute(
                    "SELECT * FROM ics_periods WHERE incident_id=? ORDER BY period_num",(inc_id,)).fetchall()))
            elif sub=="/stats":
                obj_count  = c.execute("SELECT COUNT(*) FROM ics_periods WHERE incident_id=?",(inc_id,)).fetchone()[0]
                res_count  = c.execute("SELECT COUNT(*) FROM ics_resources WHERE incident_id=?",(inc_id,)).fetchone()[0]
                form_count = c.execute("SELECT COUNT(*) FROM ics_forms WHERE incident_id=?",(inc_id,)).fetchone()[0]
                inc_d = row_to_dict(row)
                return self.send_json({"objectives":obj_count,"current_period":inc_d.get("current_period",1),"resources":res_count,"forms":form_count})
            elif sub=="/planningp":
                inc_d = row_to_dict(row)
                periods = rows_to_list(c.execute(
                    "SELECT * FROM ics_periods WHERE incident_id=? ORDER BY period_num",(inc_id,)).fetchall())
                resources = rows_to_list(c.execute(
                    "SELECT callsign,name,role,status FROM ics_resources WHERE incident_id=?",(inc_id,)).fetchall())
                return self.send_json({"incident":inc_d,"periods":periods,"resources":resources})
            return self.send_json({"error":"Not found"},404)

        elif path.startswith("/api/ics/forms/"):
            parts=path.split("/api/ics/forms/")[1].split("/")
            form_type=parts[0]
            if len(parts)==1:
                inc_id=qs.get("incident_id",[None])[0]
                if inc_id:
                    rows=c.execute(
                        "SELECT id,incident_id,form_type,period,summary,created,updated"
                        " FROM ics_forms WHERE form_type=? AND incident_id=? ORDER BY created DESC",
                        (form_type,inc_id)).fetchall()
                else:
                    rows=c.execute(
                        "SELECT id,incident_id,form_type,period,summary,created,updated"
                        " FROM ics_forms WHERE form_type=? ORDER BY created DESC",
                        (form_type,)).fetchall()
                return self.send_json(rows_to_list(rows))
            else:
                fid=parts[1]
                row=c.execute("SELECT * FROM ics_forms WHERE id=?",(fid,)).fetchone()
                if row:
                    d=dict(row); d.update(jload(d.get("data"),{}))
                    return self.send_json(d)
                return self.send_json({"error":"Not found"},404)

        elif path == "/api/ics/tcards":
            inc_id=qs.get("incident_id",[None])[0]
            if inc_id:
                rows=c.execute("SELECT * FROM ics_tcards WHERE incident_id=? ORDER BY status,resource_name",(inc_id,)).fetchall()
            else:
                rows=c.execute("SELECT * FROM ics_tcards ORDER BY status,resource_name").fetchall()
            return self.send_json(rows_to_list(rows))

        elif path.startswith("/api/ics/tcards/"):
            card_id=path.split("/api/ics/tcards/")[1]
            row=c.execute("SELECT * FROM ics_tcards WHERE id=?",(card_id,)).fetchone()
            return self.send_json(row_to_dict(row)) if row else self.send_json({"error":"Not found"},404)

        elif path == "/api/ics/resources":
            inc_id=qs.get("incident_id",[None])[0]
            if inc_id:
                rows=c.execute("SELECT * FROM ics_resources WHERE incident_id=? ORDER BY name",(inc_id,)).fetchall()
            else:
                rows=c.execute("SELECT * FROM ics_resources ORDER BY name").fetchall()
            return self.send_json(rows_to_list(rows))

        elif path == "/api/ics/activity":
            inc_id=qs.get("incident_id",[None])[0]
            limit=int(qs.get("limit",[50])[0])
            if inc_id:
                rows=c.execute("SELECT * FROM activity_log WHERE incident_id=? ORDER BY timestamp DESC LIMIT ?",(inc_id,limit)).fetchall()
            else:
                rows=c.execute("SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT ?",(limit,)).fetchall()
            return self.send_json(rows_to_list(rows))

        elif path == "/api/ics/status":
            incs=c.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
            active=c.execute("SELECT COUNT(*) FROM incidents WHERE status='active'").fetchone()[0]
            return self.send_json({"service":"ics-platform","version":"2.0.0",
                "utc":utcnow(),"incidents":incs,"active":active,"db":str(db.DB_PATH)})

        else:
            self.send_json({"error":"Not found"},404)

    def do_POST(self):
        parsed=urlparse(self.path); path=parsed.path.rstrip("/")
        body=self.read_body(); c=get_conn(); now=utcnow()

        if path == "/api/ics/incidents":
            inc_id=body.get("id") or f"inc-{int(time.time()*1000)}"
            c.execute("""INSERT INTO incidents
                (id,name,type,status,jurisdiction,incident_commander,
                 location,summary,current_period,started)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (inc_id,body.get("name",""),body.get("type",""),
                 "active",body.get("jurisdiction",""),
                 body.get("incident_commander",""),body.get("location",""),
                 body.get("summary",""),1,now))
            # Create period 1
            c.execute("INSERT INTO ics_periods(id,incident_id,period_num,started) VALUES(?,?,?,?)",
                      (f"per-{inc_id}-1",inc_id,1,now))
            c.commit()
            log_activity(inc_id,"Command","Incident Created",body.get("name",""))
            inc=row_to_dict(c.execute("SELECT * FROM incidents WHERE id=?",(inc_id,)).fetchone())
            return self.send_json({"ok":True,"incident":inc})

        elif path.startswith("/api/ics/incidents/"):
            parts=path.split("/api/ics/incidents/")[1].split("/")
            inc_id=parts[0]; sub="/".join(parts[1:]) if len(parts)>1 else ""
            row=c.execute("SELECT * FROM incidents WHERE id=?",(inc_id,)).fetchone()

            if sub in ("","update"):
                if not row: return self.send_json({"error":"Not found"},404)
                allowed=["name","type","status","jurisdiction","incident_commander",
                         "location","summary"]
                sets=[]; vals=[]
                for k in allowed:
                    if k in body: sets.append(f"{k}=?"); vals.append(body[k])
                if sets:
                    vals+=[now,inc_id]
                    c.execute(f"UPDATE incidents SET {','.join(sets)},updated=? WHERE id=?",vals)
                    c.commit()
                log_activity(inc_id,"Command","Incident Updated","")
                return self.send_json({"ok":True})

            elif sub == "advance_period":
                if not row: return self.send_json({"error":"Not found"},404)
                new_period=row["current_period"]+1
                c.execute("UPDATE incidents SET current_period=?,updated=? WHERE id=?",
                          (new_period,now,inc_id))
                c.execute("INSERT INTO ics_periods(id,incident_id,period_num,started,objectives) VALUES(?,?,?,?,?)",
                          (f"per-{inc_id}-{new_period}",inc_id,new_period,now,
                           body.get("objectives","")))
                c.commit()
                log_activity(inc_id,"Command","Period Advanced",f"Period {new_period}")
                return self.send_json({"ok":True,"period":new_period})

            elif sub == "close":
                if not row: return self.send_json({"error":"Not found"},404)
                c.execute("UPDATE incidents SET status='closed',closed=?,updated=? WHERE id=?",
                          (now,now,inc_id)); c.commit()
                log_activity(inc_id,"Command","Incident Closed","")
                return self.send_json({"ok":True})

            elif sub == "command":
                # Save command section data (objectives, safety message, weather)
                fid = f"command-{inc_id}"
                c.execute("""INSERT OR REPLACE INTO ics_forms
                    (id,incident_id,form_type,period,summary,data,created,updated)
                    VALUES(?,?,?,?,?,?,COALESCE((SELECT created FROM ics_forms WHERE id=?),?),?)""",
                    (fid,inc_id,"command",body.get("period",1),"Command Section",jdump(body),fid,now,now))
                c.commit()
                log_activity(inc_id,"Command","Command Section Saved","")
                return self.send_json({"ok":True})

        elif path.startswith("/api/ics/forms/"):
            form_type=path.split("/api/ics/forms/")[1].split("/")[0]
            fid=body.get("id") or f"{form_type}-{int(time.time()*1000)}"
            body.update({"id":fid,"form_type":form_type,"updated":now})
            body.setdefault("created",now)
            c.execute("""INSERT OR REPLACE INTO ics_forms
                (id,incident_id,form_type,period,summary,data,created,updated)
                VALUES(?,?,?,?,?,?,?,?)""",
                (fid,body.get("incident_id",""),form_type,body.get("period",1),
                 body.get("summary",""),jdump(body),body.get("created",now),now))
            c.commit()
            log_activity(body.get("incident_id",""),form_type.upper(),"Form Saved",fid)
            return self.send_json({"ok":True,"id":fid})

        elif path == "/api/ics/tcards":
            cid=body.get("id") or f"tc-{int(time.time()*1000)}"
            c.execute("""INSERT OR REPLACE INTO ics_tcards
                (id,incident_id,resource_id,resource_name,type,
                 status,assignment,contact,created,updated)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (cid,body.get("incident_id",""),body.get("resource_id",""),
                 body.get("resource_name",""),body.get("type",""),
                 body.get("status","Available"),body.get("assignment",""),
                 body.get("contact",""),body.get("created",now),now))
            c.commit()
            log_activity(body.get("incident_id",""),"Resources","T-Card Updated",
                         body.get("resource_name",""))
            return self.send_json({"ok":True,"card":row_to_dict(
                c.execute("SELECT * FROM ics_tcards WHERE id=?",(cid,)).fetchone())})

        elif path == "/api/ics/resources":
            rid=body.get("id") or f"icsres-{int(time.time()*1000)}"
            c.execute("""INSERT OR REPLACE INTO ics_resources
                (id,incident_id,resource_id,name,type,capability,
                 status,assignment,contact,created,updated)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (rid,body.get("incident_id",""),body.get("resource_id",""),
                 body.get("name",""),body.get("type",""),body.get("capability",""),
                 body.get("status","Available"),body.get("assignment",""),
                 body.get("contact",""),body.get("created",now),now))
            c.commit()
            return self.send_json({"ok":True,"resource":row_to_dict(
                c.execute("SELECT * FROM ics_resources WHERE id=?",(rid,)).fetchone())})

        else:
            self.send_json({"error":"Not found"},404)

    def do_DELETE(self):
        parsed=urlparse(self.path); path=parsed.path.rstrip("/"); c=get_conn()
        if path.startswith("/api/ics/tcards/"):
            c.execute("DELETE FROM ics_tcards WHERE id=?",(path.split("/api/ics/tcards/")[1],))
        elif path.startswith("/api/ics/resources/"):
            c.execute("DELETE FROM ics_resources WHERE id=?",(path.split("/api/ics/resources/")[1],))
        elif path.startswith("/api/ics/incidents/"):
            inc_id=path.split("/api/ics/incidents/")[1]
            c.execute("DELETE FROM incidents WHERE id=?",(inc_id,))
        else:
            return self.send_json({"error":"Not found"},404)
        c.commit(); return self.send_json({"ok":True})


if __name__ == "__main__":
    db.startup()
    log.info("ICS Platform API on port 5055")
    HTTPServer(("0.0.0.0", 5055), ICSHandler).serve_forever()
