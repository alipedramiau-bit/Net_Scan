"""End-to-end verification: POST /devices/export-mikrotik.csv

Feature: CSV export button for SELECTED MikroTik devices in the
"مدیریت دستگاه‌های شبکه" tab — exports ALL previously-read fields
(identity name, type, tags, interfaces, IPs, neighbors, wireless,
log, MAC, read-status) one column per field. Non-MikroTik devices are
filtered out.

Update (Task 12): with read_missing=True the endpoint FIRST live-reads the
selected MikroTik devices that have no complete details via RouterOS API
(persisting them like /api/devices/probe-api does), then builds the CSV —
so the export no longer contains empty detail columns for devices that were
never read. A new «وضعیت خواندن» column explains each row's completeness.
"""
import os, sys, sqlite3, csv as _csv, io as _io
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import db as dbm
from fastapi.testclient import TestClient
import main as appm


def parse_csv(text):
    """Proper CSV parse (multiline quoted fields safe). Returns (header, rows)."""
    rows = list(_csv.reader(_io.StringIO(text)))
    return rows[0], [r for r in rows[1:] if r]

client = TestClient(appm.app)

# Auth middleware: login before hitting protected endpoints.
_r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
assert _r.status_code == 200, f"login failed: {_r.status_code} {_r.text[:100]}"

# ---------- Setup: temporary test database registered in the catalog ----------
TEST_DB = "zz_mt_csv_test"
created = dbm.create_database(TEST_DB)
path = dbm.db_path_for(TEST_DB)
print("test db path:", path)

# Clean leftover per-device txt files from previous runs (delete_database
# removes the .db but the shared databases/ip_info/ dir keeps txt files —
# they would pre-enrich the test devices and break the missing-details setup)
import pathlib
for _p in (path.parent / "ip_info").glob("10.20.0.*.txt"):
    _p.unlink()

prev_active = dbm.get_active_db_name()
dbm.set_active_database(TEST_DB)

conn = sqlite3.connect(path)
rows = [
    # ip, name, tags, dtype, interfaces, ip_addr, neighbors, wireless, log, mac, classification, ports
    ("10.20.0.1", "Core-RTR1", "MPLS,Core", "Router", "ether1,ether2,sfp1",
     "10.20.0.1/24,192.168.10.1/24", "NB-10.20.0.2 ether2", "wlan1: bridge/ap bridge",
     "log line A\nlog line B", "AA:BB:CC:DD:EE:01", "mikrotik_candidate", "[8291, 8728]"),
    ("10.20.0.2", "AP-Site2", "Access", "AP", "wlan1,ether3",
     "10.20.0.2/24", "", "wlan1: station ssid=NET2",
     "log C", "AA:BB:CC:DD:EE:02", "mikrotik_candidate", "[8291]"),
    ("10.20.0.3", "SW-L2", "", "", "", "", "", "", "", "", "mikrotik_candidate", "[8728]"),
    ("10.20.0.9", "Printer-HP", "", "", "", "", "", "", "", "", "non_mikrotik", "[]"),
]
for (ip, name, tags, dtype, ifaces, ipaddr, nb, wl, log, mac, cls, ports) in rows:
    conn.execute(
        """INSERT INTO devices (ip, ping_ok, open_ports, port_states, classification,
           first_seen, last_seen, seen_count, device_name, tags, device_type, interfaces,
           ip_addresses, ip_neighbors, wireless_info, device_log, mac_info)
           VALUES (?,1,?,'{"8291":"","8728":""}',?,datetime('now'),datetime('now'),2,?,?,?,?,?,?,?,?,?)""",
        (ip, ports, cls, name, tags, dtype, ifaces, ipaddr, nb, wl, log, mac))
conn.commit(); conn.close()

ok = True
def check(label, cond, extra=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label, extra)
    ok = ok and cond

# ---------- 1) happy path: mixed selection keeps only MikroTik ----------
ALL_IPS = ["10.20.0.1", "10.20.0.2", "10.20.0.3", "10.20.0.9"]
r = client.post("/devices/export-mikrotik.csv", json={"ips": ALL_IPS})
check("mixed selection -> 200", r.status_code == 200, str(r.status_code))
check("UTF-8 BOM present", r.content[:3] == b"\xef\xbb\xbf")
check("csv media type", "text/csv" in r.headers.get("content-type", ""), r.headers.get("content-type", ""))
check("attachment filename", "mikrotik_selected_" in r.headers.get("content-disposition", ""), r.headers.get("content-disposition", ""))

body = r.content.decode("utf-8-sig")
header_cells, data_rows = parse_csv(body)
colidx = {h: i for i, h in enumerate(header_cells)}
check("header has 19 Persian field columns", len(header_cells) == 19, str(header_cells))
for col in ["نام دستگاه (identity)", "اینترفیس‌ها", "آدرس‌های IP", "همسایه‌ها", "وایرلس", "لاگ دستگاه", "اطلاعات MAC", "وضعیت خواندن"]:
    check(f"header contains '{col}'", col in colidx)
check("3 MikroTik rows kept", len(data_rows) == 3, f"got {len(data_rows)} rows")
check("non-mikrotik printer EXCLUDED", "10.20.0.9" not in body)
check("mikrotik rows present", all(ip in body for ip in ["10.20.0.1", "10.20.0.2", "10.20.0.3"]))

# full-field device: every previously-read field must appear in its own column
full = next(r for r in data_rows if r[0] == "10.20.0.1")
row2 = next(r for r in data_rows if r[0] == "10.20.0.2")
row3 = next(r for r in data_rows if r[0] == "10.20.0.3")
for col, val in [("نام دستگاه (identity)", "Core-RTR1"), ("نوع دستگاه", "Router"), ("تگ", "MPLS"),
                 ("اینترفیس‌ها", "ether1"), ("آدرس‌های IP", "192.168.10.1/24"), ("همسایه‌ها", "NB-10.20.0.2"),
                 ("وایرلس", "bridge/ap bridge"), ("اطلاعات MAC", "AA:BB:CC:DD:EE:01"), ("وضعیت خواندن", "کامل")]:
    got = full[colidx[col]] if col in colidx else "<no col>"
    check(f"field value exported: {col}={val}", val in got, repr(got))
check("multiline log field exported intact", full[colidx["لاگ دستگاه"]] == "log line A\nlog line B", repr(full[colidx["لاگ دستگاه"]]))
check("row2 wireless ssid=NET2", "ssid=NET2" in row2[colidx["وایرلس"]])
check("row2 device_name exported", row2[colidx["نام دستگاه (identity)"]] == "AP-Site2")
check("row2 wireless-only-missing still کامل", row2[colidx["وضعیت خواندن"]] == "کامل")
check("never-read row flagged ناقص", "ناقص" in row3[colidx["وضعیت خواندن"]], row3[colidx["وضعیت خواندن"]])

# ---------- 2) read_missing=True: live-read devices without complete details ----------
orig_probe = appm.routeros_api.probe_devices_via_api_many
captured = {}
def fake_probe(ips, **kw):
    captured["ips"] = list(ips)
    captured.update(kw)
    return [{
        "ip": ip, "ok": True, "device_name": "SW-L2-READ", "device_type": "Switch",
        "interfaces": "ether1,ether2,ether3 (live)", "ip_addresses": "10.20.0.3/24 (live)",
        "ip_neighbors": "NB-live-gw", "wireless_info": "",
        "device_log": "live log line 1\nlive log line 2", "mac_info": "AA:BB:CC:DD:EE:03",
    } for ip in ips]
appm.routeros_api.probe_devices_via_api_many = fake_probe
try:
    r = client.post("/devices/export-mikrotik.csv", json={
        "ips": ALL_IPS, "read_missing": True,
        "username": "admin", "password": "pw", "port": 8728, "timeout": 5, "max_workers": 3})
    check("read_missing export -> 200", r.status_code == 200, str(r.status_code))
    check("only the incomplete device was probed", captured.get("ips") == ["10.20.0.3"], str(captured.get("ips")))
    check("probe got credentials + progress + pool", captured.get("username") == "admin" and captured.get("progress") is not None and captured.get("max_workers") == 3, str({k: type(v).__name__ for k, v in captured.items()}))
    check("X-Export-Missing-Before = 1", r.headers.get("X-Export-Missing-Before") == "1", r.headers.get("X-Export-Missing-Before", ""))
    check("X-Export-Read-Now = 1", r.headers.get("X-Export-Read-Now") == "1", r.headers.get("X-Export-Read-Now", ""))
    check("X-Export-Read-Failed = 0", r.headers.get("X-Export-Read-Failed") == "0", r.headers.get("X-Export-Read-Failed", ""))

    body2 = r.content.decode("utf-8-sig")
    hdr2, rows2 = parse_csv(body2)
    ci2 = {h: i for i, h in enumerate(hdr2)}
    check("live-read data now IN the CSV", "(live)" in body2 and "SW-L2-READ" in body2 and "NB-live-gw" in body2)
    row3b = next(r for r in rows2 if r[0] == "10.20.0.3")
    check("row 10.20.0.3 now کامل", row3b[ci2["وضعیت خواندن"]] == "کامل", row3b[ci2["وضعیت خواندن"]])

    # persistence: DB + txt file like the regular probe endpoint
    conn = sqlite3.connect(path); conn.row_factory = sqlite3.Row
    d3 = conn.execute("SELECT * FROM devices WHERE ip='10.20.0.3'").fetchone()
    conn.close()
    check("DB persisted interfaces", "(live)" in (d3["interfaces"] or ""))
    check("DB persisted device_log", "live log line 1" in (d3["device_log"] or ""))
    check("DB persisted mac_info", "AA:BB:CC:DD:EE:03" in (d3["mac_info"] or ""))
    txt = dbm.db_path_for(TEST_DB).parent / "ip_info" / "10.20.0.3.txt"
    check("ip_info txt written with standard sections", txt.is_file() and "----- interfaces -----" in txt.read_text(encoding="utf-8"), str(txt))

    # second export: nothing missing anymore -> probe NOT called again
    captured.clear()
    r2 = client.post("/devices/export-mikrotik.csv", json={"ips": ALL_IPS, "read_missing": True})
    check("second export -> 200", r2.status_code == 200, str(r2.status_code))
    check("no re-read when everything complete", "ips" not in captured, str(captured))
    check("X-Export-Missing-Before = 0 on second run", r2.headers.get("X-Export-Missing-Before") == "0", r2.headers.get("X-Export-Missing-Before", ""))
finally:
    appm.routeros_api.probe_devices_via_api_many = orig_probe

# ---------- 3) only non-MikroTik selected -> 400 with Persian message ----------
r = client.post("/devices/export-mikrotik.csv", json={"ips": ["10.20.0.9"]})
check("non-mikrotik only -> 400", r.status_code == 400, str(r.status_code))
check("400 message is Persian & clear", "میکروتیک" in r.json().get("detail", ""), r.text[:120])

# ---------- 4) empty selection -> 400 ----------
r = client.post("/devices/export-mikrotik.csv", json={"ips": []})
check("empty selection -> 400", r.status_code == 400, str(r.status_code))

# ---------- 5) unknown ips -> 400 ----------
r = client.post("/devices/export-mikrotik.csv", json={"ips": ["99.99.99.99"]})
check("unknown ips -> 400", r.status_code == 400, str(r.status_code))

# ---------- 6) unauthenticated request is blocked by session middleware ----------
plain = TestClient(appm.app)
r = plain.post("/devices/export-mikrotik.csv", json={"ips": ALL_IPS})
check("unauthenticated blocked", r.status_code in (401, 403), str(r.status_code))

# ---------- 7) unit: device_details_complete / device_read_status ----------
check("unit: complete device", dbm.device_details_complete({"interfaces": "x", "ip_addresses": "y", "device_log": "z", "mac_info": "w"}))
check("unit: missing mac -> incomplete", not dbm.device_details_complete({"interfaces": "x", "ip_addresses": "y", "device_log": "z", "mac_info": ""}))
check("unit: status label ناقص", "ناقص" in dbm.device_read_status({"interfaces": "", "ip_addresses": "", "device_log": "", "mac_info": ""}))

# ---------- Cleanup ----------
for _p in (path.parent / "ip_info").glob("10.20.0.*.txt"):
    _p.unlink()
dbm.set_active_database(prev_active)
dbm.delete_database(TEST_DB)
print("\ncleanup done:", TEST_DB, "removed from catalog")
print("\n" + ("ALL TESTS PASSED ✔" if ok else "SOME TESTS FAILED ✘"))
sys.exit(0 if ok else 1)
