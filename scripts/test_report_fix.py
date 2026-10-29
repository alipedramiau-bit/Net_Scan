"""Tests for smart-report diagnostics + fixed login credentials (Task 6).

Run:  python scripts/test_report_fix.py
Covers:
- report metadata (devices_scanned / devices_with_logs / newest_log_at)
- stale_logs hint + suggested_days when window is older than newest log
- error field when device read fails (no more silent empty reports)
- login accepts admin/NetAdmin and rejects NetAdmin/NetAdmin
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timedelta
from fastapi.testclient import TestClient

PASS = FAIL = 0
def check(name, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  PASS  {name}")
    else: FAIL += 1; print(f"  FAIL  {name}  {extra}")

import smart_reports as sr
import auth as authm

# ---------- 1) report metadata on synthetic devices ----------
now = datetime(2026, 10, 24, 12, 0, 0)
fresh_dev = {"ip": "10.0.0.1", "device_name": "core", "tags": "",
             "device_log": "1  2026/10/23 08:00:00  ether2 link up\n"
                           "2  2026/10/23 08:02:00  ether2 link down\n"}
stale_dev = {"ip": "10.0.0.2", "device_name": "old", "tags": "",
             "device_log": "1  2026/09/01 08:00:00  ether3 link up\n"
                           "2  2026/09/01 08:01:00  ether3 link down\n"}
nolog_dev = {"ip": "10.0.0.3", "device_name": "quiet", "tags": "", "device_log": ""}

rep = sr.interface_flap_report([fresh_dev, stale_dev, nolog_dev], days_back=5, threshold_minutes=5, now=now)
check("event found in 5-day window", rep["event_count"] == 1, str(rep["event_count"]))
check("devices_scanned = 3", rep["devices_scanned"] == 3)
check("devices_with_logs = 2", rep["devices_with_logs"] == 2)
check("newest_log_at present", rep.get("newest_log_at", "").startswith("2026-10-23"), str(rep.get("newest_log_at")))
check("newest_log_at_jalali present", "1405" in rep.get("newest_log_at_jalali", ""), str(rep.get("newest_log_at_jalali")))
check("no stale hint when events exist", "stale_logs" not in rep)

# ---------- 2) stale logs: window older than newest log ----------
rep2 = sr.interface_flap_report([stale_dev, nolog_dev], days_back=5, threshold_minutes=5, now=now)
check("no events for stale logs", rep2["event_count"] == 0)
check("stale_logs flag set", rep2.get("stale_logs") is True)
check("suggested_days sane", isinstance(rep2.get("suggested_days"), int) and rep2["suggested_days"] >= 6, str(rep2.get("suggested_days")))

# ---------- 3) endpoint behavior: metadata + error propagation ----------
import db as dbm
from main import app

TEST_DB = "__test_report_fix"
cat = dbm._read_catalog()
prev_active = cat.get("active")
dbm.create_database(TEST_DB)          # empty database
dbm.set_active_database(TEST_DB)
try:
    client = TestClient(app)

    r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
    check("login admin/NetAdmin -> 200", r.status_code == 200 and r.json().get("username") == "admin", r.text[:80])
    r = client.post("/api/login", json={"username": "NetAdmin", "password": "NetAdmin"})
    check("login NetAdmin/NetAdmin -> 401", r.status_code == 401)

    r = client.get("/reports/interface-flaps?days=5&threshold_minutes=5")
    d = r.json()
    check("report on empty DB -> 200", r.status_code == 200)
    check("empty DB: devices_scanned == 0", d.get("devices_scanned") == 0)
    check("empty DB: devices_with_logs == 0", d.get("devices_with_logs") == 0)
    check("empty DB: no newest_log_at", "newest_log_at" not in d)

    # corrupt the DB file so query_devices raises -> response must carry "error"
    dbm.set_active_database("default")
    cat_path = dbm._CATALOG
    import json as _json
    cat_data = _json.loads(cat_path.read_text(encoding="utf-8"))
    cat_data["databases"] = [x for x in cat_data["databases"] if x != TEST_DB] + ["__no_such_dir_name__"]
    # point a temp name at an unreadable path is complex; instead simulate via monkeypatch
    cat_data["databases"] = [x for x in cat_data["databases"] if x != "__no_such_dir_name__"]
    cat_path.write_text(_json.dumps(cat_data, ensure_ascii=False), encoding="utf-8")

    orig = dbm.query_devices
    import backend.db as bdb  # same module object main.py binds as `db`
    orig_bdb = bdb.query_devices
    boom = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("disk I/O error"))
    dbm.query_devices = boom
    bdb.query_devices = boom
    try:
        r = client.get("/reports/interface-flaps?days=5&threshold_minutes=5")
        d = r.json()
        check("read failure -> 200 with error field", r.status_code == 200 and "error" in d and "disk I/O error" in d["error"], r.text[:120])
        rcsv = client.get("/reports/interface-flaps/export.csv?days=5")
        check("CSV read failure -> 500 (no silent empty file)", rcsv.status_code == 500, str(rcsv.status_code))
    finally:
        dbm.query_devices = orig
        bdb.query_devices = orig_bdb
finally:
    dbm.set_active_database(prev_active)
    try:
        from pathlib import Path
        p = dbm.db_path_for(TEST_DB)
        if p.is_file(): p.unlink()
        cat_data = _json.loads(cat_path.read_text(encoding="utf-8"))
        cat_data["databases"] = [x for x in cat_data["databases"] if x != TEST_DB]
        cat_path.write_text(_json.dumps(cat_data, ensure_ascii=False), encoding="utf-8")
    except Exception as cleanup_error:
        print("  (cleanup note)", cleanup_error)

# ---------- 4) CSV/XLSX still export with metadata present ----------
rep3 = sr.interface_flap_report([fresh_dev], days_back=5, threshold_minutes=5, now=now)
csv_text = sr.interface_flaps_csv(rep3)
check("CSV export works with new metadata", csv_text.count("\n") >= 2 and "ردیف" in csv_text)

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
