"""E2E + unit checks: every CSV download of the project carries the current
system date & time at the end of its filename (Task 22).

Covers all 7 CSV routes:
- GET  /devices/export.csv                         -> devices_YYYYMMDD_HHMMSS.csv (+ new_devices_)
- POST /devices/export-mikrotik.csv                -> mikrotik_selected_...
- POST /devices/route-report.csv                   -> route_report_...        (trace mocked)
- GET  /scans/{id}/reports/{key}                   -> {key}_...               (job injected, csv_bytes mocked)
- GET  /reports/interface-flaps/export.csv         -> interface_flaps_report_...
- GET  /reports/wireless-antenna-issues/export.csv -> wireless_antenna_issues_...
- GET  /api/reports/route-topology/unreachable-csv -> route_unreachable_...   (state injected)
- GET  /api/devices/push-config/failed-csv         -> config_failed_...       (state injected)

Freshness: the stamp is parsed and compared to datetime.now() (< 5 minutes),
proving it is the *current system* date/time — not a frozen value.
RouterOS/network calls are monkeypatched — no real device is contacted.
Run: python3 scripts/test_csv_filename_stamp.py
"""
import os
import re
import sys
import sqlite3
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

from fastapi.testclient import TestClient

import db as dbm
import main as appm

ok = True


def check(label, cond, extra=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label, extra if not cond else "")
    ok = ok and cond


STAMP_RE = re.compile(r"_(\d{8})_(\d{6})\.csv$")


def filename_of(resp):
    cd = resp.headers.get("Content-Disposition", "")
    m = re.search(r'filename="?([^";]+)"?', cd)
    return m.group(1) if m else ""


def stamp_is_fresh(filename, max_age_s=300.0):
    """نام فایل باید الگوی <name>_YYYYMMDD_HHMMSS.csv داشته باشد و مهر آن
    کمتر از ۵ دقیقه با ساعت جاری سیستم فاصله داشته باشد."""
    m = STAMP_RE.search(filename)
    if not m:
        return False
    try:
        stamp = datetime.strptime(m.group(1) + "_" + m.group(2), "%Y%m%d_%H%M%S")
    except ValueError:
        return False
    return abs((datetime.now() - stamp).total_seconds()) <= max_age_s


# ---------- unit: file_stamp helper ----------
st = appm.file_stamp()
check("file_stamp format YYYYMMDD_HHMMSS", bool(re.fullmatch(r"\d{8}_\d{6}", st)), st)
check("file_stamp = current system date/time",
      abs((datetime.now() - datetime.strptime(st, "%Y%m%d_%H%M%S")).total_seconds()) < 5, st)

client = TestClient(appm.app)
r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
check("login", r.status_code == 200, str(r.status_code))

# ---------- Setup: temporary test database ----------
TEST_DB = "zz_csv_stamp_test"
if TEST_DB in [d["name"] for d in dbm.list_databases()["databases"]]:
    if dbm.get_active_db_name() == TEST_DB:
        dbm.set_active_database("default")
    dbm.delete_database(TEST_DB)
    print("leftover test db removed")
dbm.create_database(TEST_DB)
path = dbm.db_path_for(TEST_DB)
prev_active = dbm.get_active_db_name()
if prev_active == TEST_DB:
    prev_active = "default"
dbm.set_active_database(TEST_DB)
conn = sqlite3.connect(path)
for (ip, name, tags, dtype) in [("10.40.0.1", "RTR-TEST", "Core", "Router"),
                                ("10.40.0.2", "AP-TEST", "", "AP")]:
    conn.execute(
        """INSERT INTO devices (ip, ping_ok, open_ports, port_states, classification,
           first_seen, last_seen, seen_count, device_name, tags, device_type)
           VALUES (?,1,'[8291, 8728]','{"8291":"","8728":""}','mikrotik_candidate',
           datetime('now'),datetime('now'),1,?,?,?)""",
        (ip, name, tags, dtype))
conn.commit()
conn.close()

orig = {
    "csv_bytes": appm.csv_bytes,
    "jobs": dict(appm.JOBS),
    "cfg": dict(appm.CFG_PUSH_STATE),
    "topo": dict(appm.TOPOLOGY_STATE),
    "trace_many": appm.route_report.trace_many,
    "trace_route": appm.route_report.trace_route,
    "build_csv": appm.route_report.build_route_report_csv,
}

try:
    # ---------- 1) devices export ----------
    r = client.get("/devices/export.csv")
    fn = filename_of(r)
    check("export.csv -> 200", r.status_code == 200, str(r.status_code))
    check("devices_<stamp>.csv", fn.startswith("devices_") and bool(STAMP_RE.search(fn)), fn)
    check("devices stamp = current system date/time", stamp_is_fresh(fn), fn)

    r2 = client.get("/devices/export.csv?new_only=true")
    fn2 = filename_of(r2)
    check("new_devices_<stamp>.csv",
          r2.status_code == 200 and fn2.startswith("new_devices_") and bool(STAMP_RE.search(fn2)), fn2)

    time.sleep(1.1)  # دو دانلود در ثانیه‌های متفاوت → نام متفاوت (اثبات مهر در نام)
    fn3 = filename_of(client.get("/devices/export.csv"))
    check("two downloads -> different filenames", fn3 != fn, fn3 + " vs " + fn)

    # ---------- 2) mikrotik selected export ----------
    r = client.post("/devices/export-mikrotik.csv", json={"ips": ["10.40.0.1", "10.40.0.2"]})
    fn = filename_of(r)
    check("mikrotik csv -> 200", r.status_code == 200, r.text[:120])
    check("mikrotik_selected_<stamp>.csv", fn.startswith("mikrotik_selected_") and stamp_is_fresh(fn), fn)

    # ---------- 3) route report (tracert mocked) ----------
    fake = {"hops": [{"hop": 1, "ip": "10.40.0.1"}], "ok": True}
    appm.route_report.trace_route = lambda *a, **k: dict(fake)
    appm.route_report.trace_many = lambda ips, **k: [{"ip": ip, "trace": dict(fake)} for ip in ips]
    appm.route_report.build_route_report_csv = lambda entries, **k: "a,b\n1,2"
    r = client.post("/devices/route-report.csv",
                    json={"ips": ["10.40.0.1"], "source_ip": "172.19.1.6", "dest_ip": "172.19.1.6"})
    fn = filename_of(r)
    check("route-report csv -> 200", r.status_code == 200, r.text[:150])
    check("route_report_<stamp>.csv", fn.startswith("route_report_") and stamp_is_fresh(fn), fn)

    # ---------- 4) scan report {key}.csv (job injected, csv_bytes mocked) ----------
    appm.csv_bytes = lambda report, key: "x,y\n1,2"
    appm.JOBS["zz-stamp-job"] = {"status": "done", "report": {}}
    r = client.get("/scans/zz-stamp-job/reports/ping_responders")
    fn = filename_of(r)
    check("scan report csv -> 200", r.status_code == 200, r.text[:120])
    check("ping_responders_<stamp>.csv", fn.startswith("ping_responders_") and stamp_is_fresh(fn), fn)

    # ---------- 5) interface flaps csv ----------
    r = client.get("/reports/interface-flaps/export.csv?days=7")
    fn = filename_of(r)
    check("flaps csv -> 200", r.status_code == 200, r.text[:120])
    check("interface_flaps_report_<stamp>.csv",
          fn.startswith("interface_flaps_report_") and stamp_is_fresh(fn), fn)

    # ---------- 6) wireless antenna csv ----------
    r = client.get("/reports/wireless-antenna-issues/export.csv?days=7")
    fn = filename_of(r)
    check("wireless csv -> 200", r.status_code == 200, r.text[:120])
    check("wireless_antenna_issues_<stamp>.csv",
          fn.startswith("wireless_antenna_issues_") and stamp_is_fresh(fn), fn)

    # ---------- 7) route-topology unreachable csv ----------
    appm.TOPOLOGY_STATE.update({"running": False,
                                "unreachable_rows": [{"ip": "10.40.0.9", "reason": "timeout"}]})
    r = client.get("/api/reports/route-topology/unreachable-csv")
    fn = filename_of(r)
    check("unreachable csv -> 200", r.status_code == 200, r.text[:150])
    check("route_unreachable_<stamp>.csv",
          fn.startswith("route_unreachable_") and stamp_is_fresh(fn), fn)

    # ---------- 8) group-push failed csv ----------
    appm.CFG_PUSH_STATE.update({"running": False,
                                "results": [{"ip": "10.40.0.2", "ok": False,
                                             "error": "connection timed out"}],
                                "finished_at": "2026-01-01T10:00:00"})
    r = client.get("/api/devices/push-config/failed-csv")
    fn = filename_of(r)
    check("failed csv -> 200", r.status_code == 200, r.text[:150])
    check("config_failed_<stamp>.csv", fn.startswith("config_failed_") and stamp_is_fresh(fn), fn)

finally:
    appm.csv_bytes = orig["csv_bytes"]
    appm.JOBS.clear()
    appm.JOBS.update(orig["jobs"])
    appm.CFG_PUSH_STATE.clear()
    appm.CFG_PUSH_STATE.update(orig["cfg"])
    appm.TOPOLOGY_STATE.clear()
    appm.TOPOLOGY_STATE.update(orig["topo"])
    appm.route_report.trace_many = orig["trace_many"]
    appm.route_report.trace_route = orig["trace_route"]
    appm.route_report.build_route_report_csv = orig["build_csv"]
    try:
        dbm.set_active_database(prev_active)
    except Exception:
        pass
    try:
        dbm.delete_database(TEST_DB)
    except Exception:
        pass

print("\n" + ("ALL PASS" if ok else "SOME CHECKS FAILED"))
sys.exit(0 if ok else 1)
