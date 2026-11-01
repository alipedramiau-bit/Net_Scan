"""End-to-end verification: device picker (search / filter / multi-select).

Task 16 — «انتخاب دستگاه‌ها از دیتابیس»:

1. GET /devices gains a `database` query param so the device list of ANY
   database in the catalog can be fetched (previously: active DB only).
2. RouteTopologyReport sends explicit `ips` from the picker; backend
   `_select_topology_targets` honors them (drops non-MikroTik, honors
   max_devices) and the PDF only covers the selected devices.

The network layer is monkeypatched (collect_topology_info) so no real
MikroTik device is needed.
"""
import os, sys, time, sqlite3
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


def _info(ip, identity, addresses, neighbors=(), routes=(), ifaces=(), ok_=True):
    return {"ip": ip, "ok": ok_, "error": None if ok_ else "connection refused",
            "identity": identity,
            "resource": {"version": "7.14", "board": "RB4011", "uptime": "3w"} if ok_ else {},
            "interfaces": list(ifaces), "addresses": list(addresses),
            "neighbors": list(neighbors), "routes": list(routes), "arp": []}


IF = lambda n: [{"name": n, "type": "ether", "running": "true", "disabled": "false",
                 "mac_address": "AA:BB:CC:00:00:01", "comment": ""}]

client = TestClient(appm.app)
_r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
assert _r.status_code == 200, f"login failed: {_r.status_code} {_r.text[:100]}"

# ---------- setup: two temporary databases in the catalog ----------
DB_A, DB_B = "zz_picker_a", "zz_picker_b"
dbm.create_database(DB_A)
dbm.create_database(DB_B)
path_a, path_b = dbm.db_path_for(DB_A), dbm.db_path_for(DB_B)
prev_active = dbm.get_active_db_name()
dbm.set_active_database(DB_A)

ROWS_A = [
    ("10.77.0.1", "CORE-A", "Core,MPLS", "[8291, 8728]", "mikrotik_candidate", 1),
    ("10.77.0.2", "EDGE-A1", "Sites", "[8728]", "mikrotik_candidate", 1),
    ("10.77.0.3", "AP-A1", "Access", "[]", "potential_non_mikrotik", 0),
]
ROWS_B = [
    ("10.88.0.1", "CORE-B", "Core", "[8291, 8728]", "mikrotik_candidate", 1),
    ("10.88.0.2", "EDGE-B1", "Sites,Wireless", "[8728]", "mikrotik_candidate", 1),
    ("10.88.0.3", "Printer-B", "", "[]", "non_mikrotik", 1),
    ("10.88.0.4", "DEAD-B", "", "[8728]", "mikrotik_candidate", 0),
]
for path, rows in ((path_a, ROWS_A), (path_b, ROWS_B)):
    conn = sqlite3.connect(path)
    for (ip, name, tags, ports, cls, ping) in rows:
        conn.execute(
            """INSERT INTO devices (ip, ping_ok, open_ports, port_states, classification,
               first_seen, last_seen, seen_count, device_name, tags)
               VALUES (?,?,?,'{}',?,datetime('now'),datetime('now'),2,?,?)""",
            (ip, ping, ports, cls, name, tags))
    conn.commit(); conn.close()

def ips_of(payload):
    return sorted(d["ip"] for d in payload["devices"])

# ---------- 1) GET /devices: database param ----------
r = client.get("/devices", params={"limit": 1000})
check("no database param -> active DB (A)", r.status_code == 200 and ips_of(r.json()) == sorted(x[0] for x in ROWS_A),
      str(ips_of(r.json())))

r = client.get("/devices", params={"database": DB_B, "limit": 1000})
check("database=B -> only B devices", r.status_code == 200 and ips_of(r.json()) == sorted(x[0] for x in ROWS_B),
      str(ips_of(r.json())))
check("database=B total field", r.json().get("total") == len(ROWS_B), str(r.json().get("total")))

r = client.get("/devices", params={"database": DB_A, "limit": 1000})
check("database=A -> only A devices", ips_of(r.json()) == sorted(x[0] for x in ROWS_A), str(ips_of(r.json())))

# ---------- 2) picker filters combined with database ----------
r = client.get("/devices", params={"database": DB_B, "classification": "mikrotik_candidate", "limit": 1000})
check("B + classification mikrotik", ips_of(r.json()) == ["10.88.0.1", "10.88.0.2", "10.88.0.4"], str(ips_of(r.json())))

r = client.get("/devices", params={"database": DB_B, "q": "Printer", "limit": 1000})
check("B + search by name", ips_of(r.json()) == ["10.88.0.3"], str(ips_of(r.json())))

r = client.get("/devices", params={"database": DB_B, "ping_ok": "true", "limit": 1000})
check("B + only ping responders", ips_of(r.json()) == ["10.88.0.1", "10.88.0.2", "10.88.0.3"], str(ips_of(r.json())))

r = client.get("/devices", params={"database": "zz_no_such_db", "limit": 10})
check("unknown database -> 404", r.status_code == 404, str(r.status_code))

# ---------- 3) route topology with explicit picker selection ----------
def reset_state():
    appm.TOPOLOGY_STATE.update({"running": False, "total": 0, "done": 0, "ok": 0, "failed": 0,
                                "current_ip": "", "phase": "", "error": None, "canceled": False,
                                "pdf": None, "stats": {}})

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

rt_collect_original = rt.collect_topology_info
def _fake_collect(host, username, password, port=8728, timeout=12.0):
    assert username == "netadmin", "user-supplied API username must reach the collector"
    if host == "10.88.0.1":
        return _info("10.88.0.1", "CORE-B",
                     [{"address": "172.19.1.6/24", "interface": "ether9", "network": "172.19.1.0"}],
                     ifaces=IF("ether9"))
    if host == "10.88.0.2":
        return _info("10.88.0.2", "EDGE-B1",
                     [{"address": "172.19.1.7/30", "interface": "ether5", "network": "172.19.1.4"}],
                     neighbors=[{"identity": "CORE-B", "address": "172.19.1.6", "interface": "ether5",
                                 "platform": "RouterOS", "version": "7.12", "mac_address": "", "uptime": ""}],
                     routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.19.1.6", "distance": "1", "immediate_gw": ""}],
                     ifaces=IF("ether5"))
    if host == "10.88.0.4":
        return _info("10.88.0.4", "DEAD-B", [], ifaces=IF("ether1"))
    return _info(host, "", [], ok_=False)

rt.collect_topology_info = _fake_collect
appm.route_topology.collect_topology_info = _fake_collect

try:
    reset_state()
    # non-MikroTik-only selection must be rejected
    r = client.post("/api/reports/route-topology/start",
                    json={"database": DB_B, "ips": ["10.88.0.3"], "username": "u"})
    check("picker: only non-mikrotik ips -> 400", r.status_code == 400, str(r.status_code))

    # explicit selection: 2 mikrotik + 1 non-mikrotik -> printer dropped
    r = client.post("/api/reports/route-topology/start",
                    json={"database": DB_B, "ips": ["10.88.0.1", "10.88.0.2", "10.88.0.3"],
                          "central_router_ip": "172.19.1.6", "username": "netadmin", "password": "s"})
    check("picker: explicit ips -> 200", r.status_code == 200, r.text[:120])
    check("picker: non-mikrotik dropped (devices=2)", r.json().get("devices") == 2, r.text[:120])

    prog = wait_idle()
    check("picker report finished", prog and not prog.get("running") and prog.get("ready") is True, str(prog))

    r = client.get("/api/reports/route-topology/result.pdf")
    check("picker result.pdf -> 200", r.status_code == 200, str(r.status_code))
    check("picker: X-Topology-Devices == 2", r.headers.get("X-Topology-Devices") == "2",
          r.headers.get("X-Topology-Devices", ""))
    check("picker: X-Topology-Reachable == 2", r.headers.get("X-Topology-Reachable") == "2")
    import re
    pages = len(re.findall(rb"/Type\s*/Page[^s]", r.content))
    check("picker: one page per selected device (2 pages)", pages == 2, str(pages))

    # max_devices caps an explicit selection
    reset_state()
    r = client.post("/api/reports/route-topology/start",
                    json={"database": DB_B, "ips": ["10.88.0.1", "10.88.0.2"],
                          "username": "netadmin", "max_devices": 1})
    check("picker: max_devices caps selection (devices=1)", r.status_code == 200 and r.json().get("devices") == 1,
          r.text[:120])
    wait_idle()
finally:
    rt.collect_topology_info = rt_collect_original
    appm.route_topology.collect_topology_info = rt_collect_original

# ---------- cleanup ----------
dbm.set_active_database(prev_active)
for n in (DB_A, DB_B):
    try:
        dbm.delete_database(n)
    except Exception:
        pass

print("\nALL OK" if ok else "\nFAILURES PRESENT")
sys.exit(0 if ok else 1)
