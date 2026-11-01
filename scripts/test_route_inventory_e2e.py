"""End-to-end verification: interface-IP inventory (+ device ids) saved into the
database BEFORE route processing, and the route report processing the filtered
list using that database inventory (Task 25).

Covers:
1) inventory_rows_from_infos + db.replace_interface_inventory/load roundtrip via
   the real worker pipeline (collect -> inventory -> graph -> pdf)
2) fresh reads replace each device's rows; devices that FAILED to read keep
   their previous inventory rows (per-device replace)
3) processing uses the DB inventory:
   - gateway of a failed device resolves to the REAL device node (ownership
     from DB) — visible in the unreachable-CSV Persian reason
   - an unknown upstream hop is named from the identity stored in the DB
     inventory — visible in the generated PDF text
4) progress/stats expose inventory counters; unauthenticated requests blocked

RouterOS API network layer is monkeypatched (no real device needed).
"""
import csv
import io
import os
import shutil
import sqlite3
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import db as dbm
import route_topology as rt
from fastapi.testclient import TestClient
import main as appm

ok = True
def check(label, cond, extra=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label, extra)
    ok = ok and cond


IF = lambda n, run="true", dis="false": [
    {"name": n, "type": "ether", "running": run, "disabled": dis, "mac_address": "", "comment": ""}]


def _info(ip, identity, addresses, routes=(), ifaces=(), ok_=True, error=None):
    return {"ip": ip, "ok": ok_, "error": (error if error is not None else (None if ok_ else "conn refused")),
            "identity": identity,
            "resource": {"version": "7.14", "board": "RB4011", "uptime": "3w"} if ok_ else {},
            "interfaces": list(ifaces), "addresses": list(addresses),
            "neighbors": [], "routes": list(routes), "arp": []}


client = TestClient(appm.app)
_r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
assert _r.status_code == 200, f"login failed: {_r.status_code} {_r.text[:100]}"

CSV_URL = "/api/reports/route-topology/unreachable-csv"

# کانفیگ سیسکوی واقعی کاربر (اگر هست) موقتاً کنار می‌رود تا سناریوی تست قطعی باشد
REAL_CFG = appm.CISCO_CONFIG_PATH
_backup = None
if REAL_CFG.is_file():
    _backup = REAL_CFG.with_suffix(".txt.bak_test25")
    shutil.move(str(REAL_CFG), str(_backup))

def restore_cfg():
    if REAL_CFG.exists():
        REAL_CFG.unlink()
    if _backup is not None and _backup.is_file():
        shutil.move(str(_backup), str(REAL_CFG))

def reset_state():
    appm.TOPOLOGY_STATE.update({"running": False, "total": 0, "done": 0, "ok": 0, "failed": 0,
                                "current_ip": "", "phase": "", "error": None, "canceled": False,
                                "pdf": None, "stats": {}, "unreachable_rows": None,
                                "unreachable_error": None, "inventory_devices": 0,
                                "inventory_addresses": 0, "inventory_error": None})

def wait_idle(timeout_s=25.0):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        p = client.get("/api/reports/route-topology/progress").json()
        if not p["running"]:
            return p
        time.sleep(0.03)
    return p

TEST_DB = "zz_route_inventory_test"
CORE_IP = "172.19.1.6"
GW_A = "10.40.1.254"     # گیت‌وی A — مالِ دستگاه خارج از انتخاب (شناسه در دیتابیس)
GW_D = "10.40.4.254"     # گیت‌وی D — مالِ دستگاه B که در اجرای جاری خوانده نمی‌شود

# پاک‌سازی دفاعی: اگر از اجرای قبلیِ خراب چیزی مانده باشد
_cat = dbm.list_databases().get("databases") or []
_cat_names = {(d.get("name") if isinstance(d, dict) else str(d)) for d in _cat}
if TEST_DB in _cat_names:
    if dbm.get_active_db_name() == TEST_DB:
        dbm.set_active_database("default")
    try:
        dbm.delete_database(TEST_DB)
    except Exception:
        pass

rt_collect_original = rt.collect_topology_info
build_topology_original = rt.build_topology
replace_original = dbm.replace_interface_inventory
CANNED = {
    # A: دو اینترفیس، default روت به گیت‌وی‌ای که فقط در اینونتوری دیتابیس ثبت است
    "10.40.1.10": lambda: _info("10.40.1.10", "A-MK",
                                [{"address": "10.40.1.10/24", "interface": "ether1", "network": "10.40.1.0"},
                                 {"address": "10.40.3.10/24", "interface": "ether7", "network": "10.40.3.0"}],
                                routes=[{"dst_address": "0.0.0.0/0", "gateway": GW_A, "distance": "1"}],
                                ifaces=IF("ether1") + IF("ether7")),
    # B: در این اجرا خوانده نمی‌شود (timeout) — اینونتوری قبلی‌اش باید بماند
    "10.40.2.1": lambda: _info("10.40.2.1", "", [], ok_=False, error="timed out during api login"),
    # D: default روت به گیت‌وی‌ای که طبق دیتابیس مالِ دستگاه B است
    "10.40.4.10": lambda: _info("10.40.4.10", "D-MK",
                                [{"address": "10.40.4.10/24", "interface": "ether1", "network": "10.40.4.0"}],
                                routes=[{"dst_address": "0.0.0.0/0", "gateway": GW_D, "distance": "1"}],
                                ifaces=IF("ether1")),
    # R1: خود روتر مرکزی (IP مرکزی روی اینترفیسش)
    "10.40.9.1": lambda: _info("10.40.9.1", "CORE-MK",
                               [{"address": CORE_IP + "/29", "interface": "ether2", "network": "172.19.1.0"},
                                {"address": "10.40.9.1/24", "interface": "ether1", "network": "10.40.9.0"}],
                               routes=[], ifaces=IF("ether1") + IF("ether2")),
}
inv_calls = []
build_calls = []

def _fake_collect(host, username, password, port=8728, timeout=12.0):
    gen = CANNED.get(host)
    if gen:
        return gen()
    return _info(host, "", [], ok_=False)

def _fake_replace(rows, db_path=None):
    inv_calls.append({"rows": list(rows or []), "db_path": db_path})
    return replace_original(rows, db_path=db_path)

def _fake_build(infos, devices, central_ip, cisco=None, inventory=None):
    build_calls.append({"inventory": list(inventory or [])})
    return build_topology_original(infos, devices, central_ip, cisco=cisco, inventory=inventory)

db_path_used = None
prev_active = None
try:
    restore_cfg()
    reset_state()
    inv_calls.clear(); build_calls.clear()

    dbm.create_database(TEST_DB)
    db_path_used = str(dbm.db_path_for(TEST_DB))
    prev_active = dbm.get_active_db_name()
    dbm.set_active_database(TEST_DB)

    conn = sqlite3.connect(db_path_used)
    for (ip, name) in [("10.40.1.10", "A-MK"), ("10.40.2.1", "B-MK"),
                       ("10.40.4.10", "D-MK"), ("10.40.9.1", "CORE-MK")]:
        conn.execute(
            """INSERT INTO devices (ip, ping_ok, open_ports, port_states, classification,
               first_seen, last_seen, seen_count, device_name, tags, device_type)
               VALUES (?,1,'[8728]','{}','mikrotik_candidate',datetime('now'),datetime('now'),2,?,?,'Router')""",
            (ip, name, "site-test"))
    conn.commit()
    # «ای‌دی دستگاه» = شناسهٔ ردیف دیتابیس (rowid) — همان چیزی که query_devices هم می‌دهد
    ids = {r[1]: r[0] for r in conn.execute("SELECT rowid AS id, ip FROM devices").fetchall()}
    conn.close()

    # --- پیش‌seed اینونتوری «قبلی» در دیتابیس (مثل خواندِ دستگاه‌جزئیات قبلی) ---
    preseed = [
        {"device_ip": "10.40.2.1", "device_id": ids["10.40.2.1"], "identity": "B-MK",
         "interface": "ether5", "address": GW_D + "/24", "ip": GW_D, "network": "10.40.4.0"},
        {"device_ip": "9.9.9.77", "device_id": 999, "identity": "Up-Core-MK",
         "interface": "ether1", "address": GW_A + "/24", "ip": GW_A, "network": "10.40.1.0"},
    ]
    dbm.replace_interface_inventory(preseed, db_path=db_path_used)

    # پچ لایهٔ شبکه + ثبت فراخوانی‌های خط لوله (collect → inventory → graph)
    rt.collect_topology_info = _fake_collect
    appm.route_topology.collect_topology_info = _fake_collect
    dbm.replace_interface_inventory = _fake_replace
    appm.db.replace_interface_inventory = _fake_replace
    rt.build_topology = _fake_build
    appm.route_topology.build_topology = _fake_build

    try:
        # ------------------------------- اجرای اول -------------------------------
        r = client.post("/api/reports/route-topology/start",
                        json={"database": TEST_DB, "central_router_ip": CORE_IP,
                              "username": "netadmin", "password": "x", "max_workers": 3})
        check("run1: start -> 200", r.status_code == 200, r.text[:140])
        check("run1: 4 mikrotik devices", r.json().get("devices") == 4, r.text[:140])
        prog = wait_idle()
        check("run1: finished without error", prog and not prog["running"] and not prog.get("error"),
              str(prog.get("error") or prog.get("phase")))
        check("run1: unreachable=3 (A, B, D)", prog.get("unreachable") == 3, str(prog.get("unreachable")))

        # ۱) اینونتوری «قبل از پردازش» در دیتابیس ذخیره شده است
        check("run1: inventory saved via db layer (one call)",
              len(inv_calls) == 1 and inv_calls[0]["db_path"] == db_path_used,
              str((len(inv_calls), inv_calls[0]["db_path"] if inv_calls else None)))
        saved_rows = inv_calls[0]["rows"] if inv_calls else []
        saved_devs = {r_["device_ip"] for r_ in saved_rows}
        check("run1: fresh rows only for successfully-read devices (A, D, R1)",
              saved_devs == {"10.40.1.10", "10.40.4.10", "10.40.9.1"}, str(sorted(saved_devs)))
        check("run1: failed device B has NO fresh rows (its stored rows survive)",
              "10.40.2.1" not in saved_devs, str(sorted(saved_devs)))
        check("run1: progress exposes inventory counters",
              prog.get("inventory_devices") == 3 and prog.get("inventory_addresses") == 5,
              str((prog.get("inventory_devices"), prog.get("inventory_addresses"))))
        stats = appm.TOPOLOGY_STATE.get("stats") or {}
        check("run1: stats carry inventory counters",
              stats.get("inventory_devices") == 3 and stats.get("inventory_addresses") == 5,
              str((stats.get("inventory_devices"), stats.get("inventory_addresses"))))

        # ۲) محتوای دیتابیس: ردیف‌های تازه با ای‌دی دستگاه + حفظ ردیف‌های قبلی
        loaded = dbm.load_interface_inventory(db_path=db_path_used)
        by_ip = {}
        for r_ in loaded:
            by_ip.setdefault(r_["ip"], r_)
        check("db: total rows = 5 fresh + 2 preseed", len(loaded) == 7, str(len(loaded)))
        check("db: fresh rows carry real device ids",
              by_ip["10.40.1.10"]["device_id"] == ids["10.40.1.10"]
              and by_ip[GW_A]["device_id"] == 999  # مالِ دستگاه خارج از انتخاب (pre-seed)
              and by_ip[CORE_IP]["device_id"] == ids["10.40.9.1"],
              str({k: by_ip[k]["device_id"] for k in ("10.40.1.10", GW_A, CORE_IP)}))
        check("db: identity stored per row",
              by_ip["10.40.1.10"]["identity"] == "A-MK" and by_ip[CORE_IP]["identity"] == "CORE-MK",
              str((by_ip["10.40.1.10"]["identity"], by_ip[CORE_IP]["identity"])))
        check("db: ip column is maskless, address keeps the mask",
              by_ip["10.40.3.10"]["ip"] == "10.40.3.10" and by_ip["10.40.3.10"]["address"] == "10.40.3.10/24",
              str((by_ip["10.40.3.10"]["ip"], by_ip["10.40.3.10"]["address"])))
        check("db: pre-seeded rows of failed device kept as-is",
              by_ip[GW_D]["device_id"] == ids["10.40.2.1"] and by_ip[GW_D]["identity"] == "B-MK",
              str(by_ip.get(GW_D)))
        check("db: pre-seeded row of non-participating device kept",
              by_ip[GW_A]["identity"] == "Up-Core-MK", str(by_ip.get(GW_A)))

        # ۳) پردازش «از روی دیتابیس»: build_topology اینونتوریِ خوانده‌شده از DB را گرفته
        check("pipeline: build_topology received DB-loaded inventory",
              len(build_calls) == 1 and len(build_calls[0]["inventory"]) == 7,
              str(len(build_calls[0]["inventory"]) if build_calls else "no-call"))

        # ۳-الف) مالکیت گیت‌وی D از دیتابیس → یال به دستگاه واقعی B؛ دلیل CSV نام B را دارد
        r = client.get(CSV_URL)
        check("run1: unreachable csv -> 200", r.status_code == 200, str(r.status_code))
        text = r.content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text)))
        body = rows[1:]
        by_ip_csv = {x[1]: x for x in body}
        check("run1: csv has 3 unreachable rows", len(body) == 3, str([x[1] for x in body]))
        reason_d = by_ip_csv["10.40.4.10"][9]
        check("run1: D reached real failed device B via DB inventory (reason names B-MK)",
              "B-MK" in reason_d and "هیچ روت" in reason_d, reason_d)
        check("run1: D reason is NOT the ghost wording",
              "دستگاه‌های بررسی‌شده نیست" not in reason_d, reason_d)
        reason_a = by_ip_csv["10.40.1.10"][9]
        check("run1: A still ends at unknown gateway (ghost wording)",
              "مسیر تا گیت‌وی " + GW_A in reason_a, reason_a)

        # ۳-ب) نام‌گذاری hop بالادست از اینونتوری دیتابیس — داخل PDF قابل مشاهده است
        pdf_bytes = appm.TOPOLOGY_STATE.get("pdf") or b""
        check("run1: pdf built", isinstance(pdf_bytes, bytes) and pdf_bytes[:5] == b"%PDF-",
              str(len(pdf_bytes)))
        try:
            from pypdf import PdfReader
            pdf_text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(pdf_bytes)).pages)
        except Exception as _pe:
            pdf_text = ""
            check("run1: pdf text extraction", False, str(_pe)[:120])
        check("run1: PDF names the upstream ghost from DB inventory (Up-Core-MK)",
              "Up-Core-MK" in pdf_text, "ghost name missing in pdf text")
        check("run1: PDF shows readable split interface labels on link",
              "ether1" in pdf_text and GW_A in pdf_text, "")

        # ------------------------------- اجرای دوم -------------------------------
        reset_state()
        inv_calls.clear(); build_calls.clear()
        r = client.post("/api/reports/route-topology/start",
                        json={"database": TEST_DB, "central_router_ip": CORE_IP,
                              "username": "netadmin", "password": "x", "max_workers": 2,
                              "ips": ["10.40.9.1"]})
        check("run2: start -> 200", r.status_code == 200, r.text[:140])
        prog = wait_idle()
        check("run2: finished", prog and not prog["running"] and not prog.get("error"),
              str(prog.get("error") or prog.get("phase")))
        check("run2: only core selected -> unreachable=0", prog.get("unreachable") == 0,
              str(prog.get("unreachable")))
        check("run2: inventory replaced only for the selected device",
              prog.get("inventory_devices") == 1 and prog.get("inventory_addresses") == 2,
              str((prog.get("inventory_devices"), prog.get("inventory_addresses"))))
        loaded2 = dbm.load_interface_inventory(db_path=db_path_used)
        ips2 = sorted({r_["ip"] for r_ in loaded2})
        check("run2: rows of non-selected devices untouched (total stays 7)",
              by_ip.get(GW_D) is not None and len(loaded2) == 7, str((len(loaded2), ips2)))
        check("run2: A rows survive untouched", "10.40.1.10" in ips2 and GW_A in ips2, str(ips2))
        r = client.get(CSV_URL)
        check("run2: all reachable -> csv 404", r.status_code == 404, str(r.status_code))
    finally:
        # بازگرداندن پچ‌ها پیش از پاک‌سازی دیتابیس (پاک‌سازی کامل در finally بیرونی)
        rt.collect_topology_info = rt_collect_original
        appm.route_topology.collect_topology_info = rt_collect_original
        dbm.replace_interface_inventory = replace_original
        appm.db.replace_interface_inventory = replace_original
        rt.build_topology = build_topology_original
        appm.route_topology.build_topology = build_topology_original
finally:
    # پاک‌سازی تضمینی در «هر» مسیر خروج (حتی خرابی وسطِ setup)
    try:
        if prev_active:
            dbm.set_active_database(prev_active)
    except Exception:
        pass
    try:
        if db_path_used:
            dbm.delete_database(TEST_DB)
    except Exception:
        pass
    restore_cfg()
    reset_state()

plain = TestClient(appm.app)
r = plain.get("/api/reports/route-topology/progress")
check("unauthenticated progress blocked", r.status_code in (401, 403), str(r.status_code))

print("\nALL OK" if ok else "\nFAILURES PRESENT")
sys.exit(0 if ok else 1)
