"""End-to-end verification: CSV report of WHY routers don't reach the central
router + checking ALL interfaces/IPs of every router for routing (Task 21).

Covers:
1) _route_all_next_hops — gateways of ALL covering routes (not just the best),
   best-first order (longest prefix, lower distance), dedup, iface-gateway skip
2) interface_route_verdicts — per-IP/per-interface verdict (direct/route/default/
   none) with interface state (disabled / no link) and ARP hint
3) unreachable_reason_rows — Persian reason per unreachable device (empty routing
   table, no covering route, ghost gateway end, interface down, read-failed,
   canceled, loop)
4) GET /api/reports/route-topology/unreachable-csv — BOM, Persian headers, only
   unreachable devices, 404 when everyone reaches the core, 409 while running,
   unauthenticated blocked

The RouterOS API network layer is monkeypatched (no real device needed).
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


# ===========================================================================
# 1) _route_all_next_hops — همهٔ روت‌های پوشش‌دهنده، نه فقط بهترین
# ===========================================================================
ROUTES = [
    {"dst_address": "0.0.0.0/0", "gateway": "9.9.9.9", "distance": "2", "immediate_gw": ""},
    {"dst_address": "172.19.0.0/16", "gateway": "10.0.0.1", "distance": "1", "immediate_gw": ""},
    {"dst_address": "172.19.1.0/24", "gateway": "10.0.1.1", "distance": "1", "immediate_gw": ""},
    {"dst_address": "172.19.1.0/24", "gateway": "10.0.1.1", "distance": "5", "immediate_gw": ""},
    {"dst_address": "172.19.1.0/24", "gateway": "ether5", "distance": "1", "immediate_gw": ""},
]
all_hops = rt._route_all_next_hops(ROUTES, "172.19.1.6")
check("all-next-hops: 3 deduped IP gateways", [c["gw"] for c in all_hops] == ["10.0.1.1", "10.0.0.1", "9.9.9.9"],
      str([c["gw"] for c in all_hops]))
check("all-next-hops: iface-gateway route skipped", all(c["gw"] != "ether5" for c in all_hops))
check("all-next-hops: longest prefix first", all_hops[0]["dst"] == "172.19.1.0/24"
      and all_hops[0]["kind"] == "specific", str(all_hops[0]))
check("all-next-hops: default route last with kind=default",
      all_hops[-1]["gw"] == "9.9.9.9" and all_hops[-1]["kind"] == "default", str(all_hops[-1]))
check("all-next-hops: backup specific route (worse prefix) included",
      any(c["gw"] == "10.0.0.1" and c["dst"] == "172.19.0.0/16" for c in all_hops))
check("all-next-hops: invalid central ip -> []", rt._route_all_next_hops(ROUTES, "not-an-ip") == [])
check("all-next-hops: no routes -> []", rt._route_all_next_hops([], "172.19.1.6") == [])

# ===========================================================================
# 2) interface_route_verdicts — بررسی تک‌تک اینترفیس‌ها و IPها
# ===========================================================================
V_INFO = {
    "addresses": [
        {"address": "172.19.1.10/24", "interface": "ether1", "network": "172.19.1.0"},
        {"address": "10.5.0.2/24", "interface": "ether2", "network": "10.5.0.0"},
        {"address": "10.6.0.2/24", "interface": "ether3", "network": "10.6.0.0"},
        {"address": "10.7.0.2/24", "interface": "ether4", "network": "10.7.0.0"},
    ],
    "routes": [
        {"dst_address": "172.19.1.0/24", "gateway": "10.5.0.1", "distance": "1", "immediate_gw": ""},
        {"dst_address": "0.0.0.0/0", "gateway": "10.6.0.1", "distance": "1", "immediate_gw": ""},
        {"dst_address": "192.168.50.0/24", "gateway": "10.6.0.99", "distance": "1", "immediate_gw": ""},
    ],
    "interfaces": (IF("ether1") + IF("ether2") + IF("ether3")
                   + IF("ether4", run="false")),
    "arp": [{"address": "10.5.0.1", "mac-address": "AA:BB:CC:00:00:01", "interface": "ether2"}],
}
vv = {x["ip"]: x for x in rt.interface_route_verdicts(V_INFO, "172.19.1.6")}
check("verdicts: 4 IPs checked", len(vv) == 4, str(sorted(vv)))
check("verdicts: central subnet ip -> direct", vv["172.19.1.10"]["verdict"] == "direct", str(vv.get("172.19.1.10")))
check("verdicts: specific route via ether2 gw", vv["10.5.0.2"]["verdict"] == "route"
      and vv["10.5.0.2"]["gateway"] == "10.5.0.1", str(vv.get("10.5.0.2")))
check("verdicts: default route via ether3 gw", vv["10.6.0.2"]["verdict"] == "default"
      and vv["10.6.0.2"]["gateway"] == "10.6.0.1", str(vv.get("10.6.0.2")))
check("verdicts: no covering route -> none", vv["10.7.0.2"]["verdict"] == "none", str(vv.get("10.7.0.2")))
check("verdicts: no-link iface state", vv["10.7.0.2"]["state"] == "down"
      and "اتصال فیزیکی ندارد" in vv["10.7.0.2"]["label"], str(vv.get("10.7.0.2")))
check("verdicts: arp hint true/false", vv["10.5.0.2"]["gw_in_arp"] is True
      and vv["10.6.0.2"]["gw_in_arp"] is False, str((vv["10.5.0.2"]["gw_in_arp"], vv["10.6.0.2"]["gw_in_arp"])))
check("verdicts: disabled iface suffix",
      "غیرفعال" in rt.interface_route_verdicts(
          {"addresses": [{"address": "10.8.0.2/24", "interface": "e9", "network": "10.8.0.0"}],
           "routes": [], "interfaces": IF("e9", dis="true"), "arp": []}, "172.19.1.6")[0]["label"])
check("verdicts: invalid central -> []", rt.interface_route_verdicts(V_INFO, "") == [])

# ===========================================================================
# 3) unreachable_reason_rows — سناریوهای دلیل (بر پایهٔ build_topology)
# ===========================================================================
def _info(ip, identity, addresses, routes=(), ifaces=(), neighbors=(), ok_=True, error=None, arp=()):
    return {"ip": ip, "ok": ok_, "error": (error if error is not None else (None if ok_ else "conn refused")),
            "identity": identity,
            "resource": {"version": "7.14", "board": "RB4011", "uptime": "3w"} if ok_ else {},
            "interfaces": list(ifaces), "addresses": list(addresses),
            "neighbors": list(neighbors), "routes": list(routes), "arp": list(arp)}

D = lambda ip, name: {"ip": ip, "device_name": name, "tags": "t1", "ping_ok": True,
                      "open_ports": [8728], "device_type": "Router"}

# (الف) ghost gateway end
topo_g = rt.build_topology(
    [_info("172.18.1.68", "RB-Salmaneh",
           [{"address": "172.18.1.68/28", "interface": "link-shdgn", "network": "172.18.1.64"}],
           routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.18.1.71", "distance": "1", "immediate_gw": ""}],
           ifaces=IF("link-shdgn"))],
    [D("172.18.1.68", "RB-Salmaneh")], "172.19.1.6")
rows_g = rt.unreachable_reason_rows(topo_g)
check("reason rows: 1 row for ghost scenario", len(rows_g) == 1, str(len(rows_g)))
check("reason rows: ghost-end reason mentions gateway ip",
      "مسیر تا گیت‌وی 172.18.1.71 پیش می‌رود" in rows_g[0]["reason"], rows_g[0]["reason"])
check("reason rows: interfaces & addresses listed",
      "link-shdgn: 172.18.1.68/28" in rows_g[0]["addresses_txt"], rows_g[0]["addresses_txt"])
check("reason rows: verdict text has default-route label",
      "فقط روت پیش‌فرض از طریق گیت‌وی 172.18.1.71" in rows_g[0]["verdicts_txt"], rows_g[0]["verdicts_txt"])
check("reason rows: all-ips-checked detail",
      "تمام 1 آدرس IP روی 1 اینترفیس" in rows_g[0]["details"], rows_g[0]["details"])
check("reason rows: core-unknown detail (no cisco)",
      "کانفیگ Cisco روتر مرکزی بارگذاری نشده" in rows_g[0]["details"], rows_g[0]["details"])

# (ب) حلقهٔ روتینگ
topo_l = rt.build_topology(
    [_info("10.2.2.2", "Loop-A", [{"address": "10.2.2.2/24", "interface": "e1", "network": "10.2.2.0"}],
           routes=[{"dst_address": "0.0.0.0/0", "gateway": "10.2.2.3", "distance": "1", "immediate_gw": ""}],
           ifaces=IF("e1")),
     _info("10.2.2.3", "Loop-B", [{"address": "10.2.2.3/24", "interface": "e1", "network": "10.2.2.0"}],
           routes=[{"dst_address": "0.0.0.0/0", "gateway": "10.2.2.2", "distance": "1", "immediate_gw": ""}],
           ifaces=IF("e1"))],
    [], "172.19.1.6")
rows_l = {r["ip"]: r for r in rt.unreachable_reason_rows(topo_l)}
check("reason rows: loop reason", "حلقه" in rows_l["10.2.2.2"]["reason"], rows_l["10.2.2.2"]["reason"])

# (ج) دستگاه خوانده‌نشده / متوقف‌شده
topo_d = rt.build_topology(
    [_info("10.5.5.5", "", [], ok_=False, error="timed out during api login"),
     _info("10.5.5.6", "", [], ok_=False, error="canceled")],
    [], "172.19.1.6")
rows_d = {r["ip"]: r for r in rt.unreachable_reason_rows(topo_d)}
check("reason rows: read-failed status", rows_d["10.5.5.5"]["status"] == "خوانده نشد", rows_d["10.5.5.5"]["status"])
check("reason rows: timeout cause classified", "پاسخ نداد (timeout)" in rows_d["10.5.5.5"]["reason"],
      rows_d["10.5.5.5"]["reason"])
check("reason rows: raw error in details", "timed out" in rows_d["10.5.5.5"]["details"], rows_d["10.5.5.5"]["details"])
check("reason rows: canceled status", rows_d["10.5.5.6"]["status"] == "بررسی متوقف شد", rows_d["10.5.5.6"]["status"])

# (د) آدرس خالی / جدول روتینگ خالی / بدون روت پوشش‌دهنده
topo_e = rt.build_topology(
    [_info("10.6.6.1", "NoAddr", [], routes=[{"dst_address": "0.0.0.0/0", "gateway": "10.6.6.9", "distance": "1"}]),
     _info("10.6.6.2", "NoRoutes", [{"address": "10.66.6.2/24", "interface": "e1", "network": "10.66.6.0"}],
           routes=[], ifaces=IF("e1")),
     _info("10.6.6.3", "WrongRoutes", [{"address": "10.66.7.3/24", "interface": "e1", "network": "10.66.7.0"}],
           routes=[{"dst_address": "192.168.50.0/24", "gateway": "10.66.7.9", "distance": "1", "immediate_gw": ""}],
           ifaces=IF("e1"))],
    [], "172.19.1.6")
rows_e = {r["ip"]: r for r in rt.unreachable_reason_rows(topo_e)}
check("reason rows: no addresses reason", "هیچ آدرس IP روی دستگاه خوانده نشد" in rows_e["10.6.6.1"]["reason"],
      rows_e["10.6.6.1"]["reason"])
check("reason rows: empty routing table reason", "جدول روتینگ دستگاه خالی است" in rows_e["10.6.6.2"]["reason"],
      rows_e["10.6.6.2"]["reason"])
check("reason rows: no covering route reason", "هیچ روت پیش‌فرض یا مسیر خاصی" in rows_e["10.6.6.3"]["reason"]
      and "172.19.1.6" in rows_e["10.6.6.3"]["reason"], rows_e["10.6.6.3"]["reason"])

# (هـ) اینترفیس خروجی قطع
topo_i = rt.build_topology(
    [_info("10.9.9.2", "R-DOWN",
           [{"address": "10.9.9.2/24", "interface": "ether1", "network": "10.9.9.0"},
            {"address": "10.44.0.2/24", "interface": "ether2", "network": "10.44.0.0"}],
           routes=[{"dst_address": "0.0.0.0/0", "gateway": "10.44.0.1", "distance": "1", "immediate_gw": ""}],
           ifaces=IF("ether1") + IF("ether2", run="false"))],
    [D("10.9.9.2", "R-DOWN")], "172.19.1.6")
rows_i = rt.unreachable_reason_rows(topo_i)
check("reason rows: down egress iface reason", "اینترفیس خروجی مسیر غیرفعال یا قطع است" in rows_i[0]["reason"]
      and "ether2" in rows_i[0]["reason"], rows_i[0]["reason"])

# (و) گیت‌وی خارج از ساب‌نتِ همهٔ اینترفیس‌ها (گیت‌وی اشتباه / مسیر بازگشتی)
topo_o = rt.build_topology(
    [_info("10.60.0.2", "R-RECURSIVE",
           [{"address": "10.60.0.2/24", "interface": "ether1", "network": "10.60.0.0"}],
           routes=[{"dst_address": "0.0.0.0/0", "gateway": "10.99.0.1", "distance": "1", "immediate_gw": ""}],
           ifaces=IF("ether1"))],
    [D("10.60.0.2", "R-RECURSIVE")], "172.19.1.6")
rows_o = rt.unreachable_reason_rows(topo_o)
check("reason rows: off-subnet gateway reason",
      "گیت‌وی در ساب‌نت هیچ‌کدام از اینترفیس‌های دستگاه نیست" in rows_o[0]["reason"]
      and "10.99.0.1" in rows_o[0]["reason"], rows_o[0]["reason"])
check("reason rows: off-subnet gateway verdict is none",
      "مسیری به روتر مرکزی از این اینترفیس نیست" in rows_o[0]["verdicts_txt"], rows_o[0]["verdicts_txt"])

# ===========================================================================
# 4) E2E — اجرای گزارش از API و دریافت CSV
# ===========================================================================
client = TestClient(appm.app)
_r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
assert _r.status_code == 200, f"login failed: {_r.status_code} {_r.text[:100]}"

CSV_URL = "/api/reports/route-topology/unreachable-csv"

# کانفیگ سیسکوی واقعی کاربر (اگر هست) موقتاً کنار می‌رود تا سناریوی تست قطعی باشد
REAL_CFG = appm.CISCO_CONFIG_PATH
_backup = None
if REAL_CFG.is_file():
    _backup = REAL_CFG.with_suffix(".txt.bak_test21")
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
                                "unreachable_error": None})

def wait_idle(timeout_s=25.0):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        p = client.get("/api/reports/route-topology/progress").json()
        if not p["running"]:
            return p
        time.sleep(0.05)
    return p

TEST_DB = "zz_unreach_csv_test"
try:
    restore_cfg()
    reset_state()
    r = client.get(CSV_URL)
    check("csv before any run -> 404", r.status_code == 404, str(r.status_code))
    check("csv 404 message is Persian", "گزارشی ساخته نشده" in r.text, r.text[:120])

    dbm.create_database(TEST_DB)
    path = dbm.db_path_for(TEST_DB)
    prev_active = dbm.get_active_db_name()
    dbm.set_active_database(TEST_DB)
    conn = sqlite3.connect(path)
    for (ip, name) in [("10.30.1.1", "R-OK"), ("10.30.2.1", "R-NOROUTE"), ("10.30.3.1", "R-GHOST"),
                       ("10.30.4.1", "R-DOWN"), ("10.30.5.1", "R-DEAD"), ("10.30.6.1", "R-WRONGROUTE")]:
        conn.execute(
            """INSERT INTO devices (ip, ping_ok, open_ports, port_states, classification,
               first_seen, last_seen, seen_count, device_name, tags, device_type)
               VALUES (?,1,'[8728]','{}','mikrotik_candidate',datetime('now'),datetime('now'),2,?,?,'Router')""",
            (ip, name, "site-test"))
    conn.commit(); conn.close()

    def canned_info(ip, identity, addresses, routes=(), ifaces=(), ok_=True, error=None):
        return _info(ip, identity, addresses, routes=routes, ifaces=ifaces, ok_=ok_, error=error)

    CANNED = {
        # R-OK: default gw == central ip -> reachable (control)
        "10.30.1.1": lambda: canned_info("10.30.1.1", "R-OK",
                                         [{"address": "10.30.1.1/24", "interface": "ether1", "network": "10.30.1.0"}],
                                         routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.19.1.6", "distance": "1", "immediate_gw": ""}],
                                         ifaces=IF("ether1")),
        # R-NOROUTE: routing table empty
        "10.30.2.1": lambda: canned_info("10.30.2.1", "R-NOROUTE",
                                         [{"address": "10.30.2.1/24", "interface": "ether1", "network": "10.30.2.0"}],
                                         routes=[], ifaces=IF("ether1")),
        # R-GHOST: default gw in the interface subnet but the gateway device is not scanned
        "10.30.3.1": lambda: canned_info("10.30.3.1", "R-GHOST",
                                         [{"address": "10.30.3.1/24", "interface": "ether1", "network": "10.30.3.0"}],
                                         routes=[{"dst_address": "0.0.0.0/0", "gateway": "10.30.3.254", "distance": "1", "immediate_gw": ""}],
                                         ifaces=IF("ether1")),
        # R-DOWN: default gw in subnet of a NO-LINK interface
        "10.30.4.1": lambda: canned_info("10.30.4.1", "R-DOWN",
                                         [{"address": "10.30.4.1/24", "interface": "ether1", "network": "10.30.4.0"},
                                          {"address": "10.44.0.2/24", "interface": "ether2", "network": "10.44.0.0"}],
                                         routes=[{"dst_address": "0.0.0.0/0", "gateway": "10.44.0.1", "distance": "1", "immediate_gw": ""}],
                                         ifaces=IF("ether1") + IF("ether2", run="false")),
        # R-DEAD: API read fails (timeout)
        "10.30.5.1": lambda: canned_info("10.30.5.1", "", [], ok_=False, error="timed out during api login"),
        # R-WRONGROUTE: only a route to somewhere else, none toward the central
        "10.30.6.1": lambda: canned_info("10.30.6.1", "R-WRONGROUTE",
                                         [{"address": "10.30.6.1/24", "interface": "ether1", "network": "10.30.6.0"}],
                                         routes=[{"dst_address": "192.168.50.0/24", "gateway": "10.30.6.9", "distance": "1", "immediate_gw": ""}],
                                         ifaces=IF("ether1")),
    }
    rt_collect_original = rt.collect_topology_info
    def _fake_collect(host, username, password, port=8728, timeout=12.0):
        gen = CANNED.get(host)
        if gen:
            return gen()
        return _info(host, "", [], ok_=False)
    rt.collect_topology_info = _fake_collect
    appm.route_topology.collect_topology_info = _fake_collect

    try:
        r = client.post("/api/reports/route-topology/start",
                        json={"database": TEST_DB, "central_router_ip": "172.19.1.6",
                              "username": "netadmin", "password": "x", "max_workers": 3})
        check("run: start -> 200", r.status_code == 200, r.text[:140])
        check("run: 6 mikrotik devices", r.json().get("devices") == 6, r.text[:140])
        prog = wait_idle()
        check("run: finished without error", prog and not prog["running"] and not prog.get("error"), str(prog))
        check("run: progress reports unreachable=5", prog.get("unreachable") == 5, str(prog))

        r = client.get(CSV_URL)
        check("csv -> 200", r.status_code == 200, str(r.status_code))
        check("csv: BOM present", r.content[:3] == b"\xef\xbb\xbf", str(r.content[:6]))
        check("csv: attachment filename", "route_unreachable_" in (r.headers.get("Content-Disposition") or ""),
              r.headers.get("Content-Disposition", ""))
        text = r.content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text)))
        check("csv: header is 12 Persian columns",
              rows[0][:5] == ["ردیف", "IP دستگاه", "نام دستگاه (identity)", "نوع دستگاه", "تگ"]
              and rows[0][5] == "وضعیت" and rows[0][9] == "دلیل اصلی نرسیدن"
              and len(rows[0]) == 12, str(rows[0]))
        body = rows[1:]
        check("csv: exactly 5 unreachable rows (R-OK excluded)",
              len(body) == 5 and all(len(x) == 12 for x in body), str([x[1] for x in body]))
        by_ip = {x[1]: x for x in body}
        check("csv: R-OK not in report", "10.30.1.1" not in by_ip, str(sorted(by_ip)))
        check("csv: rows numbered 1..5", [x[0] for x in body] == [str(i) for i in range(1, 6)],
              str([x[0] for x in body]))
        check("csv: device meta enriched (name/type/tag)",
              by_ip["10.30.2.1"][2] == "R-NOROUTE" and by_ip["10.30.2.1"][3] == "Router"
              and by_ip["10.30.2.1"][4] == "site-test", str(by_ip["10.30.2.1"]))
        check("csv: R-NOROUTE empty routing table reason",
              "جدول روتینگ دستگاه خالی است" in by_ip["10.30.2.1"][9], by_ip["10.30.2.1"][9])
        check("csv: R-NOROUTE verdict column empty (no routes)", by_ip["10.30.2.1"][8] == "",
              by_ip["10.30.2.1"][8])
        check("csv: R-GHOST ghost-gateway reason",
              "مسیر تا گیت‌وی 10.30.3.254 پیش می‌رود" in by_ip["10.30.3.1"][9], by_ip["10.30.3.1"][9])
        check("csv: R-GHOST verdict lists default-route via gw",
              "فقط روت پیش‌فرض از طریق گیت‌وی 10.30.3.254" in by_ip["10.30.3.1"][8], by_ip["10.30.3.1"][8])
        check("csv: R-GHOST addresses listed with iface",
              "ether1: 10.30.3.1/24" in by_ip["10.30.3.1"][7], by_ip["10.30.3.1"][7])
        check("csv: R-GHOST all-ips-checked detail",
              "تمام 1 آدرس IP روی 1 اینترفیس" in by_ip["10.30.3.1"][10], by_ip["10.30.3.1"][10])
        check("csv: R-DOWN down-egress reason",
              "اینترفیس خروجی مسیر غیرفعال یا قطع است" in by_ip["10.30.4.1"][9]
              and "ether2" in by_ip["10.30.4.1"][9], by_ip["10.30.4.1"][9])
        check("csv: R-DOWN verdict marks no-link iface",
              "اتصال فیزیکی ندارد" in by_ip["10.30.4.1"][8], by_ip["10.30.4.1"][8])
        check("csv: R-DOWN iface count 2 ifaces / 2 addresses",
              by_ip["10.30.4.1"][6] == "2 اینترفیس / 2 آدرس IP", by_ip["10.30.4.1"][6])
        check("csv: R-DEAD status خوانده نشد", by_ip["10.30.5.1"][5] == "خوانده نشد", by_ip["10.30.5.1"][5])
        check("csv: R-DEAD timeout cause", "پاسخ نداد (timeout)" in by_ip["10.30.5.1"][9], by_ip["10.30.5.1"][9])
        check("csv: R-DEAD no iface data", by_ip["10.30.5.1"][6] == "—" and by_ip["10.30.5.1"][7] == "",
              str((by_ip["10.30.5.1"][6], by_ip["10.30.5.1"][7])))
        check("csv: R-WRONGROUTE no covering route reason",
              "هیچ روت پیش‌فرض یا مسیر خاصی" in by_ip["10.30.6.1"][9]
              and "172.19.1.6" in by_ip["10.30.6.1"][9], by_ip["10.30.6.1"][9])
        check("csv: timestamp column filled", len(body[0][11]) >= 19, body[0][11])

        # --- اجرای دوم: همه reachable → 404 ---
        reset_state()
        r = client.post("/api/reports/route-topology/start",
                        json={"database": TEST_DB, "central_router_ip": "172.19.1.6",
                              "username": "netadmin", "password": "x", "max_workers": 2,
                              "ips": ["10.30.1.1"]})
        check("run2: start -> 200", r.status_code == 200, r.text[:120])
        prog = wait_idle()
        check("run2: finished", prog and not prog["running"] and not prog.get("error"), str(prog))
        check("run2: unreachable=0", prog.get("unreachable") == 0, str(prog))
        r = client.get(CSV_URL)
        check("csv: all reachable -> 404", r.status_code == 404, str(r.status_code))
        check("csv: 404 message mentions no unreachable device", "بدون مسیر" in r.text, r.text[:140])
    finally:
        rt.collect_topology_info = rt_collect_original
        appm.route_topology.collect_topology_info = rt_collect_original
        dbm.set_active_database(prev_active)
        try:
            dbm.delete_database(TEST_DB)
        except Exception:
            pass
finally:
    restore_cfg()
    reset_state()

plain = TestClient(appm.app)
r = plain.get(CSV_URL)
check("unauthenticated blocked", r.status_code in (401, 403), str(r.status_code))

print("\nALL OK" if ok else "\nFAILURES PRESENT")
sys.exit(0 if ok else 1)
