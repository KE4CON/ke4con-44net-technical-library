#!/usr/bin/env python3
"""FieldComms Reference Library Server — Port 5056 (SQLite via db.py)"""

import json, re, time, shutil, mimetypes, hashlib, threading, sys, logging
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from email.parser import BytesHeaderParser

import db
from db import get_conn, utcnow, jdump, jload, rows_to_list, row_to_dict

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s [refs] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout),
              logging.FileHandler('/var/log/fieldcomms-refs.log', mode='a')])
log = logging.getLogger('refs')

FILES_DIR = db.FILES_DIR
THUMB_DIR = db.THUMB_DIR
MAX_UPLOAD = 200 * 1024 * 1024
ALLOWED_EXT = {'.pdf','.doc','.docx','.xls','.xlsx','.ppt','.pptx',
               '.txt','.md','.csv','.jpg','.jpeg','.png','.gif',
               '.zip','.kml','.kmz','.gpx','.mp3','.mp4'}


def file_hash(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda: f.read(65536),b''): h.update(chunk)
    return h.hexdigest()[:16]


def try_thumbnail(file_path, thumb_path):
    try:
        import subprocess
        subprocess.run(['pdftoppm','-r','72','-l','1','-png',
                        str(file_path),str(thumb_path.with_suffix(''))],
                       capture_output=True,timeout=15)
        c=thumb_path.with_suffix('').parent/(thumb_path.with_suffix('').name+'-1.png')
        if c.exists(): c.rename(thumb_path)
    except Exception: pass


def safe_name(name):
    name=re.sub(r'[^\w.\-_ ]','_',Path(name).name.strip())
    return name or "upload"


def parse_multipart(handler):
    ct=handler.headers.get('Content-Type','')
    if 'boundary=' not in ct: return {},{}
    boundary=ct.split('boundary=')[-1].strip().encode()
    length=int(handler.headers.get('Content-Length',0))
    body=handler.rfile.read(min(length,MAX_UPLOAD))
    fields,files={},{}
    for part in body.split(b'--'+boundary)[1:]:
        if part in (b'',b'--',b'--\r\n'): continue
        if part.startswith(b'\r\n'): part=part[2:]
        try: hi=part.index(b'\r\n\r\n')
        except ValueError: continue
        raw=part[:hi]; body_part=part[hi+4:]
        if body_part.endswith(b'\r\n'): body_part=body_part[:-2]
        hdrs={}
        for line in raw.split(b'\r\n'):
            if b':' in line:
                k,_,v=line.partition(b':')
                hdrs[k.strip().lower().decode()]=v.strip().decode()
        disp=hdrs.get('content-disposition','')
        ct2=hdrs.get('content-type','text/plain')
        fname=''; fname_field=''
        for tok in disp.split(';'):
            tok=tok.strip()
            if tok.startswith('name='): fname_field=tok[5:].strip('"')
            elif tok.startswith('filename='): fname=tok[9:].strip('"')
        if fname: files[fname_field]={'filename':fname,'content_type':ct2,'data':body_part}
        elif fname_field: fields[fname_field]=body_part.decode('utf-8',errors='replace')
    return fields,files


class RefsHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def cors(self):
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','GET,POST,PUT,DELETE,OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')

    def send_json(self, obj, code=200):
        body=json.dumps(obj,default=str).encode()
        self.send_response(code)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',len(body))
        self.cors(); self.end_headers(); self.wfile.write(body)

    def send_err(self, msg, code=400):
        self.send_json({'error':msg},code)

    def read_json(self):
        n=int(self.headers.get('Content-Length',0))
        return json.loads(self.rfile.read(n)) if n else {}

    def do_OPTIONS(self):
        self.send_response(204); self.cors(); self.end_headers()

    def do_GET(self):
        parsed=urlparse(self.path); path=parsed.path.rstrip('/')
        qs=parse_qs(parsed.query); c=get_conn()

        if path == '/refs/health':
            n=c.execute("SELECT COUNT(*) FROM ref_documents").fetchone()[0]
            disk=shutil.disk_usage(str(FILES_DIR))
            return self.send_json({'status':'ok','documents':n,
                'disk_free_gb':round(disk.free/1e9,1)})

        elif path == '/refs/categories':
            rows=c.execute("SELECT category,COUNT(*) cnt FROM ref_documents GROUP BY category").fetchall()
            return self.send_json({'categories':{r['category']:r['cnt'] for r in rows}})

        elif path == '/refs/tags':
            rows=c.execute("SELECT tags FROM ref_documents").fetchall()
            tags={}
            for row in rows:
                for t in jload(row['tags'],[]):
                    tags[t]=tags.get(t,0)+1
            return self.send_json({'tags':tags})

        elif path in ('/refs','/refs/'):
            cat  =qs.get('category',[''])[0]
            sect =qs.get('section',[''])[0]
            tag  =qs.get('tag',[''])[0]
            q    =qs.get('q',[''])[0].lower()
            sort =qs.get('sort',['uploaded'])[0]
            sql  ="SELECT * FROM ref_documents WHERE 1=1"; params=[]
            if cat:  sql+=" AND category=?"; params.append(cat)
            desc_sql=sort.startswith('-') or sort=='uploaded' or sort=='downloads'
            col={'uploaded':'uploaded','-title':'title','-source':'source',
                 '-downloads':'downloads','downloads':'downloads',
                 'title':'title','source':'source'}.get(sort,'uploaded')
            sql+=f" ORDER BY {col} {'DESC' if desc_sql else 'ASC'}"
            rows=rows_to_list(c.execute(sql,params).fetchall())
            # Post-filter (sections/tags/search require JSON parsing)
            if sect:
                rows=[r for r in rows if sect in jload(r.get('sections'),[r.get('section','amateur')])]
            if tag:
                rows=[r for r in rows if tag in jload(r.get('tags'),[]) ]
            if q:
                rows=[r for r in rows if q in (
                    (r.get('title','') or '')+(r.get('description','') or '')+
                    (r.get('source','') or '')+(r.get('applies_to','') or '')+
                    (r.get('filename','') or '')+(r.get('tags','') or '')).lower()]
            for r in rows:
                r['sections']=jload(r.get('sections'),[r.get('section','amateur')])
                r['tags']=jload(r.get('tags'),[])
            return self.send_json({'documents':rows,'count':len(rows)})

        m=re.match(r'^/refs/([a-zA-Z0-9_-]+)$',path)
        if m:
            doc_id=m.group(1)
            row=c.execute("SELECT * FROM ref_documents WHERE id=?",(doc_id,)).fetchone()
            if not row: return self.send_err('Not found',404)
            d=dict(row); d['sections']=jload(d.get('sections'),[]); d['tags']=jload(d.get('tags'),[])
            return self.send_json(d)

        m=re.match(r'^/refs/([a-zA-Z0-9_-]+)/file$',path)
        if m:
            doc_id=m.group(1)
            row=c.execute("SELECT * FROM ref_documents WHERE id=?",(doc_id,)).fetchone()
            if not row: return self.send_err('Not found',404)
            fp=FILES_DIR/row['stored_name']
            if not fp.exists(): return self.send_err('File missing',404)
            c.execute("UPDATE ref_documents SET downloads=downloads+1,last_downloaded=? WHERE id=?",
                      (utcnow(),doc_id)); c.commit()
            data=fp.read_bytes()
            mime=row['content_type'] or mimetypes.guess_type(row['filename'])[0] or 'application/octet-stream'
            self.send_response(200)
            self.send_header('Content-Type',mime)
            self.send_header('Content-Length',len(data))
            self.send_header('Content-Disposition',f'attachment; filename="{row["filename"]}"')
            self.cors(); self.end_headers(); self.wfile.write(data)
            return

        m=re.match(r'^/refs/([a-zA-Z0-9_-]+)/thumbnail$',path)
        if m:
            doc_id=m.group(1)
            row=c.execute("SELECT * FROM ref_documents WHERE id=?",(doc_id,)).fetchone()
            if not row: return self.send_err('Not found',404)
            thumb=THUMB_DIR/f"{doc_id}.png"
            if not thumb.exists():
                fp=FILES_DIR/(row['stored_name'] or '')
                if fp.exists() and (row['filename'] or '').lower().endswith('.pdf'):
                    try_thumbnail(fp,thumb)
            if thumb.exists():
                data=thumb.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type','image/png')
                self.send_header('Content-Length',len(data))
                self.send_header('Cache-Control','public, max-age=86400')
                self.cors(); self.end_headers(); self.wfile.write(data)
            else:
                self.send_err('No thumbnail',404)
            return

        self.send_err('Not found',404)

    def do_POST(self):
        parsed=urlparse(self.path); path=parsed.path.rstrip('/')
        if path != '/refs/upload': return self.send_err('Not found',404)
        if 'multipart/form-data' not in self.headers.get('Content-Type',''):
            return self.send_err('Expected multipart/form-data',400)
        fields,files=parse_multipart(self)
        if 'file' not in files: return self.send_err('No file in upload',400)
        f=files['file']
        orig=safe_name(f['filename']); ext=Path(orig).suffix.lower()
        if ext not in ALLOWED_EXT: return self.send_err(f'File type not allowed: {ext}',400)
        data=f['data']
        if len(data)>MAX_UPLOAD: return self.send_err('File too large',400)
        doc_id=f"ref_{int(time.time()*1000):x}"
        stored=f"{doc_id}{ext}"; dest=FILES_DIR/stored
        dest.write_bytes(data)
        tags=[t.strip() for t in fields.get('tags','').split(',') if t.strip()]
        sect_raw=fields.get('section','amateur')
        if sect_raw=='both': sections=['amateur','ics']
        else: sections=[s.strip() for s in sect_raw.split(',') if s.strip() in ('amateur','ics')] or ['amateur']
        c=get_conn()
        c.execute("""INSERT INTO ref_documents
            (id,title,filename,stored_name,category,sections,description,
             tags,source,applies_to,revision,expires,content_type,
             size_bytes,sha256,uploaded)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (doc_id,
             fields.get('title','').strip() or orig,
             orig,stored,
             fields.get('category','other'),
             jdump(sections),
             fields.get('description','').strip(),
             jdump(tags),
             fields.get('source','').strip(),
             fields.get('applies_to','').strip(),
             fields.get('revision','').strip(),
             fields.get('expires','').strip() or None,
             f.get('content_type','') or mimetypes.guess_type(orig)[0] or 'application/octet-stream',
             len(data),
             file_hash(dest),
             utcnow()))
        c.commit()
        if ext=='.pdf':
            threading.Thread(target=try_thumbnail,args=(dest,THUMB_DIR/f"{doc_id}.png"),daemon=True).start()
        row=dict(c.execute("SELECT * FROM ref_documents WHERE id=?",(doc_id,)).fetchone())
        row['sections']=jload(row.get('sections'),[]); row['tags']=jload(row.get('tags'),[])
        return self.send_json({'success':True,'document':row},201)

    def do_PUT(self):
        parsed=urlparse(self.path); path=parsed.path.rstrip('/')
        m=re.match(r'^/refs/([a-zA-Z0-9_-]+)$',path)
        if not m: return self.send_err('Not found',404)
        doc_id=m.group(1); updates=self.read_json(); c=get_conn()
        for k in ('id','stored_name','sha256','uploaded','size_bytes'): updates.pop(k,None)
        if 'section' in updates and 'sections' not in updates:
            s=updates.pop('section')
            updates['sections']=jdump(['amateur','ics'] if s=='both' else
                                      ([s] if s in('amateur','ics') else ['amateur']))
        elif 'sections' in updates:
            updates['sections']=jdump(updates['sections'])
        if 'tags' in updates:
            updates['tags']=jdump(updates['tags'] if isinstance(updates['tags'],list)
                                  else [t.strip() for t in updates['tags'].split(',') if t.strip()])
        updates['modified']=utcnow()
        if updates:
            sets=",".join(f"{k}=?" for k in updates)
            c.execute(f"UPDATE ref_documents SET {sets} WHERE id=?",(*updates.values(),doc_id))
            c.commit()
        row=c.execute("SELECT * FROM ref_documents WHERE id=?",(doc_id,)).fetchone()
        if not row: return self.send_err('Not found',404)
        d=dict(row); d['sections']=jload(d.get('sections'),[]); d['tags']=jload(d.get('tags'),[])
        return self.send_json({'success':True,'document':d})

    def do_DELETE(self):
        parsed=urlparse(self.path); path=parsed.path.rstrip('/')
        m=re.match(r'^/refs/([a-zA-Z0-9_-]+)$',path)
        if not m: return self.send_err('Not found',404)
        doc_id=m.group(1); c=get_conn()
        row=c.execute("SELECT * FROM ref_documents WHERE id=?",(doc_id,)).fetchone()
        if not row: return self.send_err('Not found',404)
        for p in (FILES_DIR/row['stored_name'], THUMB_DIR/f"{doc_id}.png"):
            try: p.unlink(missing_ok=True)
            except Exception: pass
        c.execute("DELETE FROM ref_documents WHERE id=?",(doc_id,)); c.commit()
        return self.send_json({'success':True,'deleted':doc_id})


if __name__ == "__main__":
    db.startup()
    log.info(f"Reference Library on port 5056 — {FILES_DIR}")
    HTTPServer(('0.0.0.0',5056),RefsHandler).serve_forever()
