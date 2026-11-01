"""E2E — Task 27: دستگاه همسایهٔ متصل به اینترفیس flapشده در گزارش هوشمند.

گردش کامل با TestClient روی اپ واقعی:
- دیتابیس موقت با ۴ دستگاه: A (flap روی ether2/ether3/ether4)، B (همسایهٔ شناخته‌شدهٔ
  LLDP روی ether2)، C (همسایهٔ هم‌سابنت بدون LLDP روی ether4) و D (بی‌ربط)؛
- اینونتوری IP اینترفیس‌ها با dbm.replace_interface_inventory ذخیره می‌شود؛
- GET /reports/interface-flaps              -> neighbor_name/neighbor_ip در JSON؛
- GET /reports/interface-flaps/export.csv   -> دو ستون جدید در سرستون و ردیف‌ها؛
- GET /reports/interface-flaps/export.xlsx  -> همان ستون‌ها در شیت اکسل.
هیچ دستگاه واقعی تماس گرفته نمی‌شود.
Run: python3 scripts/test_flap_neighbor_e2e.py
"""
import csv
import io
import os
import sqlite3
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

from fastapi.testclient import TestClient

import db as dbm
import main as appm


def _ros_stamp(dt):
    """RouterOS log stamp مثل Oct/20 08:00:01 — نسبت به زمان جاری تا در بازهٔ days بیفتد."""
    return dt.strftime("%b/%d %H:%M:%S")


_NOW = datetime.now()


def _flap_log(iface, start, step_s=2, count=5):
    """count رویداد متناوب link up/down با فاصلهٔ کم (رویداد flap واقعی)."""
    lines, status = [], "up"
    for i in range(count):
        when = start + timedelta(seconds=step_s * i)
        lines.append(f"{_ros_stamp(when)} {iface} link {status}")
        status = "down" if status == "up" else "up"
    return "\n".join(lines)


LOG_A_ETHER2 = _flap_log("ether2", _NOW - timedelta(hours=1))
LOG_A_ETHER3 = _flap_log("ether3", _NOW - timedelta(hours=2))
LOG_A_ETHER4 = _flap_log("ether4", _NOW - timedelta(hours=3))

ok = True


def check(label, cond, extra=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label, extra if not cond else "")
    ok = ok and cond


TEST_DB = "zz_flap_neighbor_test"
if TEST_DB in [d["name"] for d in dbm.list_databases()["databases"]]:
    if dbm.get_active_db_name() == TEST_DB:
        dbm.set_active_database("default")
    dbm.delete_database(TEST_DB)
    print("leftover test db removed")
dbm.create_database(TEST_DB)
path = dbm.db_path_for(TEST_DB)

DEVICES = [
    # A: لاگ flap روی سه اینترفیس + LLDP کامل روی ether2 + آدرس ether4 فقط در متن ip_addresses
    ("10.40.10.1", "Shadegan-Jafal1", "MPLS",
     LOG_A_ETHER2 + "\n" + LOG_A_ETHER3 + "\n" + LOG_A_ETHER4,
     "=== /ip neighbor ===\n"
     "  1  identity=SW-Core-MK  address=10.40.10.2  interface=ether2\n"
     "  2  identity=Mystery-Box  address=172.16.5.9  interface=ether3",
     "=== /ip address ===\n"
     "  1  address=10.40.10.1/24  interface=ether2  network=10.40.10.0\n"
     "  2  address=10.60.0.1/24  interface=ether4  network=10.60.0.0"),
    # B: همسایهٔ شناخته‌شدهٔ LLDP — بدون flap
    ("10.40.10.2", "SW-Core-MK", "Core", "", "", ""),
    # C: همسایهٔ هم‌سابنت ether4 بدون هیچ LLDP
    ("10.60.0.7", "Repeater-C", "", "", "", ""),
    # D: بی‌ربط
    ("10.77.77.7", "Unrelated-RTR", "", "", "", ""),
]

conn = sqlite3.connect(path)
ids = {}
for (ip, name, tags, log, neigh, addrs) in DEVICES:
    cur = conn.execute(
        """INSERT INTO devices (ip, ping_ok, open_ports, port_states, classification,
           first_seen, last_seen, seen_count, device_name, tags, device_type,
           device_log, ip_neighbors, ip_addresses)
           VALUES (?,1,'[8291, 8728]','{"8291":"","8728":""}','mikrotik_candidate',
           datetime('now'),datetime('now'),1,?,?,?,?,?,?)""",
        (ip, name, tags, "Router", log, neigh, addrs))
    ids[ip] = cur.lastrowid
conn.commit()
conn.close()

# اینونتوری IP اینترفیس‌ها (Task 25) — همان چیزی که worker گزارش مسیر می‌نویسد
inv = [
    {"device_ip": "10.40.10.1", "device_id": ids["10.40.10.1"], "identity": "Shadegan-Jafal1",
     "interface": "ether2", "address": "10.40.10.1/24", "ip": "10.40.10.1", "network": "10.40.10.0"},
    {"device_ip": "10.40.10.1", "device_id": ids["10.40.10.1"], "identity": "Shadegan-Jafal1",
     "interface": "ether4", "address": "10.60.0.1/24", "ip": "10.60.0.1", "network": "10.60.0.0"},
    {"device_ip": "10.40.10.2", "device_id": ids["10.40.10.2"], "identity": "SW-Core-MK",
     "interface": "ether1", "address": "10.40.10.2/24", "ip": "10.40.10.2", "network": "10.40.10.0"},
    {"device_ip": "10.60.0.7", "device_id": ids["10.60.0.7"], "identity": "Repeater-C",
     "interface": "wlan1", "address": "10.60.0.7/24", "ip": "10.60.0.7", "network": "10.60.0.0"},
]
res = dbm.replace_interface_inventory(inv, db_path=path)
check("inventory seeded", res.get("rows") == 4, str(res))

client = TestClient(appm.app)
r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
check("login", r.status_code == 200, str(r.status_code))

prev_active = dbm.get_active_db_name()
if prev_active == TEST_DB:
    prev_active = "default"

try:
    # ---------- 1) JSON report ----------
    r = client.get("/reports/interface-flaps", params={"days": 5, "database": TEST_DB})
    check("GET /reports/interface-flaps -> 200", r.status_code == 200, r.text[:200])
    data = r.json()
    events = data.get("events") or []
    check("3 flap events found (one per interface of A)", len(events) == 3, str(len(events)))
    by_iface = {e.get("interface"): e for e in events}

    e2 = by_iface.get("ether2", {})
    check("ether2 neighbor name = SW-Core-MK (LLDP known)", e2.get("neighbor_name") == "SW-Core-MK",
          str(e2.get("neighbor_name")))
    check("ether2 neighbor ip = 10.40.10.2", e2.get("neighbor_ip") == "10.40.10.2", str(e2.get("neighbor_ip")))
    check("ether2 via = lldp", e2.get("neighbor_via") == "lldp", str(e2.get("neighbor_via")))

    e3 = by_iface.get("ether3", {})
    check("ether3 neighbor name = Mystery-Box (LLDP raw)", e3.get("neighbor_name") == "Mystery-Box",
          str(e3.get("neighbor_name")))
    check("ether3 neighbor ip = 172.16.5.9", e3.get("neighbor_ip") == "172.16.5.9", str(e3.get("neighbor_ip")))

    e4 = by_iface.get("ether4", {})
    check("ether4 neighbor name = Repeater-C (subnet fallback)", e4.get("neighbor_name") == "Repeater-C",
          str(e4.get("neighbor_name")))
    check("ether4 neighbor ip = 10.60.0.7", e4.get("neighbor_ip") == "10.60.0.7", str(e4.get("neighbor_ip")))
    check("ether4 via = subnet", e4.get("neighbor_via") == "subnet", str(e4.get("neighbor_via")))

    # ---------- 2) CSV export ----------
    r = client.get("/reports/interface-flaps/export.csv", params={"days": 5, "database": TEST_DB})
    check("CSV export -> 200", r.status_code == 200, str(r.status_code))
    check("CSV has UTF-8 BOM", r.content.startswith(b"\xef\xbb\xbf"))
    rows = list(csv.reader(io.StringIO(r.content.decode("utf-8-sig"))))
    header = rows[0]
    check("CSV header has «نام دستگاه همسایه» at index 3", len(header) > 3 and header[3] == "نام دستگاه همسایه", str(header))
    check("CSV header has «IP دستگاه همسایه» at index 4", len(header) > 4 and header[4] == "IP دستگاه همسایه", str(header))
    # Task 28: نام/آی‌پی دستگاه به انتهای ستون‌ها (لبهٔ چپ گزارش RTL) منتقل شدند
    check("CSV header last column = «نام دستگاه» (left edge)", len(header) == 11 and header[10] == "نام دستگاه", str(header))
    check("CSV header index 9 = «آی‌پی دستگاه»", header[9] == "آی‌پی دستگاه", str(header))
    data_rows = [row for row in rows[1:] if row]
    check("CSV has 3 data rows", len(data_rows) == 3, str(len(data_rows)))
    csv_by_iface = {row[2]: row for row in data_rows}
    check("CSV ether2 neighbor name", csv_by_iface["ether2"][3] == "SW-Core-MK", str(csv_by_iface.get("ether2")))
    check("CSV ether2 neighbor ip", csv_by_iface["ether2"][4] == "10.40.10.2", "")
    check("CSV ether4 neighbor name", csv_by_iface["ether4"][3] == "Repeater-C", str(csv_by_iface.get("ether4")))
    check("CSV ether4 neighbor ip", csv_by_iface["ether4"][4] == "10.60.0.7", "")
    check("CSV ether2 device ip at left edge (index 9)", csv_by_iface["ether2"][9] == "10.40.10.1", str(csv_by_iface.get("ether2")))
    check("CSV ether2 device name at left edge (index 10)", csv_by_iface["ether2"][10] == "Shadegan-Jafal1", "")
    check("CSV row width = header width", all(len(row) == len(header) for row in data_rows))

    # ---------- 3) XLSX export ----------
    r = client.get("/reports/interface-flaps/export.xlsx", params={"days": 5, "database": TEST_DB})
    check("XLSX export -> 200", r.status_code == 200, str(r.status_code))
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(r.content))
    ws = wb.active
    header = [c.value for c in ws[1]]
    check("XLSX header has neighbor name column at index 3", header[3] == "نام دستگاه همسایه", str(header[3]))
    check("XLSX header has neighbor ip column at index 4", header[4] == "IP دستگاه همسایه", str(header[4]))
    check("XLSX header last column = «نام دستگاه» (left edge in RTL sheet)", len(header) == 11 and header[10] == "نام دستگاه", str(header))
    ws_rows = [[c.value for c in row] for row in ws.iter_rows(min_row=2)]
    xl_by_iface = {row[2]: row for row in ws_rows}
    check("XLSX ether2 neighbor name", xl_by_iface["ether2"][3] == "SW-Core-MK", str(xl_by_iface.get("ether2")))
    check("XLSX ether4 neighbor ip", xl_by_iface["ether4"][4] == "10.60.0.7", "")
    check("XLSX ether2 device name at left edge (index 10)", xl_by_iface["ether2"][10] == "Shadegan-Jafal1", "")

finally:
    # ---------- cleanup: restore previous state ----------
    try:
        if dbm.get_active_db_name() == TEST_DB:
            dbm.set_active_database(prev_active or "default")
        dbm.delete_database(TEST_DB)
        print("cleanup ok")
    except Exception as exc:
        print("cleanup warning:", exc)

print(f"\n{'ALL PASS' if ok else 'SOME CHECKS FAILED'}")
sys.exit(0 if ok else 1)
