"""E2E — Task 33: حذف گزارش تکراری دستگاه‌ها در «ایجاد گزارش مسیر (PDF)».

سناریوی واقعی کاربر روی اپ واقعی + دیتابیس موقت:
  1) یک دستگاه با دو IP (دو ردیف هم‌نام CORE-SW) → فقط یک صفحهٔ PDF +
     duplicates_skipped=1 + هدر X-Topology-Duplicates-Skipped + پیام فارسی «تکراری»؛
  2) دو ردیف بی‌نام که اینونتوری اینترفیس‌ها (device_interface_ips) هر دو را با
     یک identity ثبت کرده → باز هم فقط یک گزارش (fallback نام از اینونتوری).

شبکه با monkeypatch جمع‌آوری می‌شود — به هیچ دستگاه واقعی وصل نمی‌شود.
"""
import os, re, sys, time, sqlite3
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


def _info(ip, identity, addresses, routes=(), ifaces=(), ok_=True):
    return {"ip": ip, "ok": ok_, "error": None if ok_ else "connection refused",
            "identity": identity,
            "resource": {"version": "7.14", "board": "RB4011", "uptime": "3w"} if ok_ else {},
            "interfaces": list(ifaces), "addresses": list(addresses),
            "neighbors": [], "routes": list(routes), "arp": []}


IF = lambda n: [{"name": n, "type": "ether", "running": "true", "disabled": "false",
                 "mac_address": "AA:BB:CC:00:00:01", "comment": ""}]

client = TestClient(appm.app)
_r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
assert _r.status_code == 200, f"login failed: {_r.status_code} {_r.text[:100]}"

DB = "zz_dedupe_e2e"
dbm.create_database(DB)
path = dbm.db_path_for(DB)
prev_active = dbm.get_active_db_name()
dbm.set_active_database(DB)

conn = sqlite3.connect(path)
for (ip, name) in (("10.77.0.1", "CORE-SW"),   # نخستین ردیفِ دستگاه CORE-SW
                   ("10.77.0.9", "CORE-SW"),   # همان دستگاه با IP دوم → تکراری
                   ("10.77.0.2", "EDGE-MK")):
    conn.execute(
        """INSERT INTO devices (ip, ping_ok, open_ports, port_states, classification,
           first_seen, last_seen, seen_count, device_name, tags)
           VALUES (?,1,'[8291, 8728]','{}','mikrotik_candidate',datetime('now'),datetime('now'),2,?, 'Core')""",
        (ip, name))
# دو ردیف بی‌نام با اینونتوری هم‌نام (fallback نام از device_interface_ips)
for ip in ("10.77.1.1", "10.77.1.9"):
    conn.execute(
        """INSERT INTO devices (ip, ping_ok, open_ports, port_states, classification,
           first_seen, last_seen, seen_count, device_name, tags)
           VALUES (?,1,'[8728]','{}','mikrotik_candidate',datetime('now'),datetime('now'),2,'','')""",
        (ip,))
conn.commit(); conn.close()

# اینونتوری: هر دو IP بی‌نام متعلق به یک دستگاه با identity واحد هستند
rows = []
for ip in ("10.77.1.1", "10.77.1.9"):
    rows.append({"device_ip": ip, "device_id": None, "identity": "UNNAMED-MK",
                 "interface": "ether1", "address": ip + "/24", "ip": ip, "network": "10.77.1.0"})
dbm.replace_interface_inventory(rows, db_path=path)

rt_collect_original = rt.collect_topology_info
def _fake_collect(host, username, password, port=8728, timeout=12.0):
    if host == "10.77.0.1":
        return _info("10.77.0.1", "CORE-SW",
                     [{"address": "172.19.1.6/24", "interface": "ether9", "network": "172.19.1.0"}],
                     ifaces=IF("ether9"))
    if host == "10.77.0.2":
        return _info("10.77.0.2", "EDGE-MK",
                     [{"address": "172.19.1.7/30", "interface": "ether5", "network": "172.19.1.4"}],
                     routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.19.1.6",
                              "distance": "1", "immediate_gw": ""}],
                     ifaces=IF("ether5"))
    if host == "10.77.1.1":
        return _info("10.77.1.1", "UNNAMED-MK",
                     [{"address": "172.19.1.8/30", "interface": "ether2", "network": "172.19.1.8"}],
                     routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.19.1.6",
                              "distance": "1", "immediate_gw": ""}],
                     ifaces=IF("ether2"))
    return _info(host, "", [], ok_=False)

rt.collect_topology_info = _fake_collect
appm.route_topology.collect_topology_info = _fake_collect

def reset_state():
    appm.TOPOLOGY_STATE.update({"running": False, "total": 0, "done": 0, "ok": 0, "failed": 0,
                                "current_ip": "", "phase": "", "error": None, "canceled": False,
                                "pdf": None, "stats": {}, "duplicates_skipped": 0})

def wait_idle(timeout_s=20.0):
    deadline = time.time() + timeout_s
    p = {}
    while time.time() < deadline:
        p = client.get("/api/reports/route-topology/progress").json()
        if p.get("ready") or p.get("error") or p.get("canceled") \
           or p.get("phase") in ("done", "error", "canceled"):
            return p
        time.sleep(0.05)
    return p

try:
    # ---------- 1) سناریوی اصلی کاربر: دو ردیف هم‌نام ----------
    reset_state()
    r = client.post("/api/reports/route-topology/start",
                    json={"database": DB, "ips": ["10.77.0.1", "10.77.0.9", "10.77.0.2"],
                          "central_router_ip": "172.19.1.6", "username": "netadmin", "password": "s"})
    check("start -> 200", r.status_code == 200, r.text[:140])
    check("devices == 2 (هم‌نام‌ها یکی شد)", r.json().get("devices") == 2, str(r.json().get("devices")))
    check("duplicates_skipped == 1", r.json().get("duplicates_skipped") == 1,
          str(r.json().get("duplicates_skipped")))
    check("message mentions تکراری", "تکراری" in (r.json().get("message") or ""), r.json().get("message", "")[:120])

    prog = wait_idle()
    check("report finished", prog.get("ready") is True, str(prog))
    check("progress keeps duplicates_skipped", prog.get("duplicates_skipped") == 1,
          str(prog.get("duplicates_skipped")))

    r = client.get("/api/reports/route-topology/result.pdf")
    check("result.pdf -> 200", r.status_code == 200, str(r.status_code))
    check("X-Topology-Devices == 2", r.headers.get("X-Topology-Devices") == "2",
          r.headers.get("X-Topology-Devices", ""))
    check("X-Topology-Duplicates-Skipped == 1", r.headers.get("X-Topology-Duplicates-Skipped") == "1",
          r.headers.get("X-Topology-Duplicates-Skipped", ""))
    pages = len(re.findall(rb"/Type\s*/Page[^s]", r.content))
    check("PDF pages == 2 (بدون صفحهٔ تکراری)", pages == 2, str(pages))

    # ---------- 2) انتخاب «همهٔ دستگاه‌های دیتابیس» هم تکراری‌ها را حذف می‌کند ----------
    reset_state()
    r = client.post("/api/reports/route-topology/start",
                    json={"database": DB, "central_router_ip": "172.19.1.6",
                          "username": "netadmin", "password": "s"})
    # همهٔ میکروتیک‌ها: 3 ردیف نام‌دار (۱ تکراری) + 2 ردیف بی‌نام (۱ تکراری اینونتوری)
    check("all-devices start -> 200", r.status_code == 200, r.text[:140])
    check("all-devices devices == 3", r.json().get("devices") == 3, str(r.json().get("devices")))
    check("all-devices duplicates_skipped == 2", r.json().get("duplicates_skipped") == 2,
          str(r.json().get("duplicates_skipped")))
    wait_idle()

    # ---------- 3) بدون تکراری: صفر ----------
    reset_state()
    r = client.post("/api/reports/route-topology/start",
                    json={"database": DB, "ips": ["10.77.0.2"], "username": "netadmin"})
    check("single device: skipped == 0", r.json().get("duplicates_skipped") == 0,
          str(r.json().get("duplicates_skipped")))
    wait_idle()
finally:
    rt.collect_topology_info = rt_collect_original
    appm.route_topology.collect_topology_info = rt_collect_original
    dbm.set_active_database(prev_active)
    try:
        dbm.delete_database(DB)
    except Exception:
        pass

print("\nALL OK" if ok else "\nFAILURES PRESENT")
sys.exit(0 if ok else 1)
