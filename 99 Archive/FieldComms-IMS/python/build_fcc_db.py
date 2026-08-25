#!/usr/bin/env python3
"""
build_fcc_db.py — Build SQLite FCC callsign database from ULS l_amat.zip
Usage: python3 build_fcc_db.py [--zip /path/to/l_amat.zip] [--db /path/to/fcc.db]
Downloads from FCC if zip not found locally.
"""

import sys, os, sqlite3, zipfile, csv, io, shutil, argparse, urllib.request
from pathlib import Path

FCC_URL = "https://data.fcc.gov/download/pub/uls/complete/l_amat.zip"
DEFAULT_ZIP = "/opt/fieldcomms/data/l_amat.zip"
DEFAULT_DB  = "/opt/fieldcomms/data/fcc.db"

def download_fcc(zip_path):
    print(f"Downloading FCC ULS database from {FCC_URL}")
    print("This file is ~200MB and may take several minutes...")
    Path(zip_path).parent.mkdir(parents=True, exist_ok=True)
    def progress(count, block, total):
        pct = min(100, count * block * 100 // total)
        print(f"\r  {pct}% ({count*block//1024//1024}MB/{total//1024//1024}MB)", end="", flush=True)
    urllib.request.urlretrieve(FCC_URL, zip_path, reporthook=progress)
    print(f"\nDownloaded to {zip_path}")

def build_db(zip_path, db_path):
    print(f"Building FCC database from {zip_path}")
    tmp_dir = Path("/tmp/fcc_build")
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir()

    print("Extracting ZIP...")
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        for name in names:
            if name.upper() in ("EN.DAT","HD.DAT","AM.DAT"):
                print(f"  Extracting {name}...")
                z.extract(name, tmp_dir)

    # Find extracted files (case-insensitive)
    files = {f.name.upper(): f for f in tmp_dir.iterdir()}
    en_file = files.get("EN.DAT")
    hd_file = files.get("HD.DAT")
    am_file = files.get("AM.DAT")

    if not en_file:
        print("ERROR: EN.DAT not found in ZIP")
        sys.exit(1)

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_db = str(db_path) + ".tmp"

    print(f"Building SQLite database at {db_path}")
    conn = sqlite3.connect(tmp_db)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA cache_size=-64000")

    # EN — Entity records (name, address)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS en (
            record_type TEXT,
            unique_system_id TEXT PRIMARY KEY,
            uls_file_number TEXT,
            ebf_number TEXT,
            call_sign TEXT,
            callsign TEXT GENERATED ALWAYS AS (UPPER(call_sign)) VIRTUAL,
            entity_type TEXT,
            licensee_id TEXT,
            entity_name TEXT,
            first_name TEXT,
            mi TEXT,
            last_name TEXT,
            suffix TEXT,
            phone TEXT,
            fax TEXT,
            email TEXT,
            street_address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            po_box TEXT,
            attention_line TEXT,
            sgin TEXT,
            frn TEXT,
            applicant_type_code TEXT,
            applicant_type_other TEXT,
            status_code TEXT,
            status_date TEXT
        )
    """)

    # HD — License header
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hd (
            record_type TEXT,
            unique_system_id TEXT PRIMARY KEY,
            uls_file_number TEXT,
            ebf_number TEXT,
            call_sign TEXT,
            license_status TEXT,
            radio_service_code TEXT,
            grant_date TEXT,
            expired_date TEXT,
            cancellation_date TEXT,
            eligibility_rule_num TEXT,
            applicant_type_code TEXT,
            alien TEXT,
            alien_government TEXT,
            alien_corporation TEXT,
            alien_officer TEXT,
            alien_control TEXT,
            revoked TEXT,
            convicted TEXT,
            adjudged TEXT,
            involved TEXT,
            common_carrier TEXT,
            non_common_carrier TEXT,
            private_comm TEXT,
            fixed TEXT,
            mobile TEXT,
            radiolocation TEXT,
            satellite TEXT,
            developmental TEXT,
            interconnected TEXT,
            certifier_first_name TEXT,
            certifier_mi TEXT,
            certifier_last_name TEXT,
            certifier_suffix TEXT,
            certifier_title TEXT,
            gender TEXT,
            african_american TEXT,
            native_american TEXT,
            hawaiian TEXT,
            asian TEXT,
            white TEXT,
            ethnicity TEXT,
            effective_date TEXT,
            last_action_date TEXT,
            auction_id TEXT,
            reg_stat_broad_serv TEXT,
            band_manager TEXT,
            type_serv_broad_serv TEXT,
            alien_ruling TEXT,
            licensee_name TEXT,
            prev_license_callsign TEXT,
            parent_callsign TEXT,
            license_name TEXT,
            common_carrier_2 TEXT
        )
    """)

    # AM — Amateur license details
    conn.execute("""
        CREATE TABLE IF NOT EXISTS am (
            record_type TEXT,
            unique_system_id TEXT PRIMARY KEY,
            uls_file_number TEXT,
            ebf_number TEXT,
            call_sign TEXT,
            operator_class TEXT,
            group_code TEXT,
            region_code TEXT,
            trustee_callsign TEXT,
            trustee_indicator TEXT,
            physician_certification TEXT,
            ve_signature TEXT,
            systematic_callsign_change TEXT,
            vanity_callsign_change TEXT,
            vanity_relationship TEXT,
            previous_callsign TEXT,
            previous_operator_class TEXT,
            trustee_name TEXT
        )
    """)

    # Create indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_en_callsign ON en(callsign)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_en_state ON en(state)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_en_last ON en(last_name)")

    def import_dat(filepath, table, conn):
        count = 0
        cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]
        # Remove generated columns
        insert_cols = [c for c in cols if c != "callsign"]
        placeholders = ",".join("?" * len(insert_cols))
        sql = f"INSERT OR REPLACE INTO {table} ({','.join(insert_cols)}) VALUES ({placeholders})"
        batch = []
        BATCH_SIZE = 10000

        with open(filepath, "r", encoding="latin-1", errors="replace") as f:
            reader = csv.reader(f, delimiter="|")
            for row in reader:
                # Pad row to column count
                padded = (row + [""] * len(insert_cols))[:len(insert_cols)]
                batch.append(padded)
                count += 1
                if len(batch) >= BATCH_SIZE:
                    conn.executemany(sql, batch)
                    conn.commit()
                    batch = []
                    if count % 100000 == 0:
                        print(f"    {count:,} records processed...", end="\r")
        if batch:
            conn.executemany(sql, batch)
            conn.commit()
        print(f"    {count:,} records loaded into {table}    ")
        return count

    print("Loading EN.DAT (entity/name data)...")
    en_count = import_dat(en_file, "en", conn)

    if hd_file:
        print("Loading HD.DAT (license headers)...")
        import_dat(hd_file, "hd", conn)
    else:
        print("WARNING: HD.DAT not found — license status will be missing")

    if am_file:
        print("Loading AM.DAT (amateur class data)...")
        import_dat(am_file, "am", conn)
    else:
        print("WARNING: AM.DAT not found — operator class will be missing")

    conn.close()

    # Replace old db with new
    if db_path.exists():
        db_path.replace(str(db_path) + ".bak")
    Path(tmp_db).replace(db_path)

    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"\nFCC database built successfully!")
    print(f"  Records: {en_count:,}")
    print(f"  Location: {db_path}")
    print(f"  Size: {db_path.stat().st_size // 1024 // 1024}MB")

def main():
    parser = argparse.ArgumentParser(description="Build FCC callsign database")
    parser.add_argument("--zip", default=DEFAULT_ZIP, help="Path to l_amat.zip")
    parser.add_argument("--db",  default=DEFAULT_DB,  help="Path for output fcc.db")
    parser.add_argument("--download", action="store_true", help="Download fresh from FCC")
    args = parser.parse_args()

    zip_path = Path(args.zip)

    if args.download or not zip_path.exists():
        if not zip_path.exists():
            print(f"ZIP not found at {zip_path}, downloading...")
        download_fcc(str(zip_path))

    build_db(str(zip_path), args.db)

if __name__ == "__main__":
    main()
