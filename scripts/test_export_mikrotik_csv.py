"""End-to-end verification: POST /devices/export-mikrotik.csv

Feature: CSV export button for SELECTED MikroTik devices in the
"مدیریت دستگاه‌های شبکه" tab — exports ALL previously-read fields
(identity name, type, tags, interfaces, IPs, neighbors, wireless,
log, MAC) one column per field. Non-MikroTik devices are filtered out.
"""
import os, sys, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import db as dbm
from fastapi.testclient import TestClient
import main as appm

client = TestClient(appm.app)

# Auth middleware: login before hitting protected endpoints.
_r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
assert _r.status_code == 200, f"login failed: {_r.status_code} {_r.text[:100]}"

# ---------- Setup: temporary test database registered in the catalog ----------
TEST_DB = "zz_mt_csv_test"
created = dbm.create_database(TEST_DB)
path = dbm.db_path_for(TEST_DB)
print("test db path:", path)

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
lines = body.strip("\r\n").split("\r\n") if "\r\n" in body else body.strip("\n").split("\n")
header, data_lines = lines[0], lines[1:]
check("header has 18 Persian field columns", header.count(",") == 17, header[:120])
for col in ["نام دستگاه (identity)", "اینترفیس‌ها", "آدرس‌های IP", "همسایه‌ها", "وایرلس", "لاگ دستگاه", "اطلاعات MAC"]:
    check(f"header contains '{col}'", col in header)
check("3 MikroTik rows kept", len(data_lines) == 3, f"got {len(data_lines)} rows")
check("non-mikrotik printer EXCLUDED", "10.20.0.9" not in body)
check("mikrotik rows present", all(ip in body for ip in ["10.20.0.1", "10.20.0.2", "10.20.0.3"]))

# full-field device: every previously-read field must appear in its own column
full_row = next((l for l in data_lines if l.startswith("10.20.0.1")), "")
for val in ["Core-RTR1", "Router", "MPLS", "ether1", "192.168.10.1/24", "NB-10.20.0.2", "bridge/ap bridge", "log line A", "AA:BB:CC:DD:EE:01"]:
    check(f"field value exported: {val}", val in full_row)
row2 = next((l for l in data_lines if l.startswith("10.20.0.2")), "")
check("field value exported: ssid=NET2 (row 10.20.0.2)", "ssid=NET2" in row2)
check("row2 device_name exported", "AP-Site2" in row2)

# ---------- 2) only non-MikroTik selected -> 400 with Persian message ----------
r = client.post("/devices/export-mikrotik.csv", json={"ips": ["10.20.0.9"]})
check("non-mikrotik only -> 400", r.status_code == 400, str(r.status_code))
check("400 message is Persian & clear", "میکروتیک" in r.json().get("detail", ""), r.text[:120])

# ---------- 3) empty selection -> 400 ----------
r = client.post("/devices/export-mikrotik.csv", json={"ips": []})
check("empty selection -> 400", r.status_code == 400, str(r.status_code))

# ---------- 4) unknown ips -> 400 ----------
r = client.post("/devices/export-mikrotik.csv", json={"ips": ["99.99.99.99"]})
check("unknown ips -> 400", r.status_code == 400, str(r.status_code))

# ---------- 5) unauthenticated request is blocked by session middleware ----------
plain = TestClient(appm.app)
r = plain.post("/devices/export-mikrotik.csv", json={"ips": ALL_IPS})
check("unauthenticated blocked", r.status_code in (401, 403), str(r.status_code))

# ---------- Cleanup ----------
dbm.set_active_database(prev_active)
dbm.delete_database(TEST_DB)
print("\ncleanup done:", TEST_DB, "removed from catalog")
print("\n" + ("ALL TESTS PASSED ✔" if ok else "SOME TESTS FAILED ✘"))
sys.exit(0 if ok else 1)
