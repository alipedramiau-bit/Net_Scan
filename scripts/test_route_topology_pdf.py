"""End-to-end verification: route topology report (گزارش مسیر تا روتر مرکزی).

POST /api/reports/route-topology/start  → background thread collects RouterOS
API info for every MikroTik device of the selected database, builds the link
graph, computes the shortest path to the user-supplied core router IP and
renders a one-page-per-device PDF.
GET  /api/reports/route-topology/progress (+ /cancel)
GET  /api/reports/route-topology/result.pdf

The network layer is monkeypatched (collect_topology_info) so no real
MikroTik device is needed. build_topology unit checks live in
test_route_topology_unit.py.
"""
import os, sys, re, time, sqlite3
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

# canned API data:
#   10.20.0.1 (R-CORE)  holds 172.19.1.6/24  -> IS the core router
#   10.20.0.2 (R-EDGE)  /30 with core, MNDP neighbor  -> 1 hop
#   10.20.0.3 (SW-L2)   no addresses/neighbors/routes -> unreachable
CANNED = {
    "10.20.0.1": lambda: _info("10.20.0.1", "R-CORE",
                               [{"address": "10.20.0.1/24", "interface": "ether1", "network": "10.20.0.0"},
                                {"address": "172.19.1.6/24", "interface": "ether9", "network": "172.19.1.0"}],
                               routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.19.1.1", "distance": "1", "immediate_gw": ""}],
                               ifaces=IF("ether1") + IF("ether9")),
    "10.20.0.2": lambda: _info("10.20.0.2", "R-EDGE",
                               [{"address": "172.19.1.7/30", "interface": "ether5", "network": "172.19.1.4"}],
                               neighbors=[{"identity": "R-CORE", "address": "172.19.1.6", "interface": "ether5",
                                           "platform": "RouterOS", "version": "7.12", "mac_address": "", "uptime": ""}],
                               routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.19.1.6", "distance": "1", "immediate_gw": ""}],
                               ifaces=IF("ether5")),
    "10.20.0.3": lambda: _info("10.20.0.3", "SW-L2", [], ifaces=IF("ether1")),
}

rt_collect_original = rt.collect_topology_info
def _fake_collect(host, username, password, port=8728, timeout=12.0):
    assert username == "netadmin", "user-supplied API username must reach the collector"
    gen = CANNED.get(host)
    if gen:
        return gen()
    return _info(host, "", [], ok_=False)


# ---------- HTTP setup ----------
client = TestClient(appm.app)
_r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
assert _r.status_code == 200, f"login failed: {_r.status_code} {_r.text[:100]}"

TEST_DB = "zz_rt_topology_test"
dbm.create_database(TEST_DB)
path = dbm.db_path_for(TEST_DB)
prev_active = dbm.get_active_db_name()
dbm.set_active_database(TEST_DB)

conn = sqlite3.connect(path)
rows = [
    ("10.20.0.1", "R-CORE", "Core", "[8291, 8728]", "mikrotik_candidate"),
    ("10.20.0.2", "R-EDGE", "Sites", "[8728]", "mikrotik_candidate"),
    ("10.20.0.3", "SW-L2", "", "[8728]", "mikrotik_candidate"),
    ("10.20.0.9", "Printer", "", "[]", "non_mikrotik"),   # must be skipped
]
for (ip, name, tags, ports, cls) in rows:
    conn.execute(
        """INSERT INTO devices (ip, ping_ok, open_ports, port_states, classification,
           first_seen, last_seen, seen_count, device_name, tags)
           VALUES (?,1,?,'{}',?,datetime('now'),datetime('now'),2,?,?)""",
        (ip, ports, cls, name, tags))
conn.commit(); conn.close()

# reset global report state so result.pdf starts out 404
def reset_state():
    appm.TOPOLOGY_STATE.update({"running": False, "total": 0, "done": 0, "ok": 0, "failed": 0,
                                "current_ip": "", "phase": "", "error": None, "canceled": False,
                                "pdf": None, "stats": {}})

def wait_idle(timeout_s=20.0):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        p = client.get("/api/reports/route-topology/progress").json()
        if not p["running"]:
            return p
        time.sleep(0.05)
    return p

reset_state()

# patch the collector BEFORE any start call so no real network is touched
rt_collect_original = rt.collect_topology_info
def _fake_collect(host, username, password, port=8728, timeout=12.0):
    assert username == "netadmin", "user-supplied API username must reach the collector"
    gen = CANNED.get(host)
    if gen:
        return gen()
    return _info(host, "", [], ok_=False)

rt.collect_topology_info = _fake_collect
appm.route_topology.collect_topology_info = _fake_collect

# ---------- 1) idle result -> 404 ----------
r = client.get("/api/reports/route-topology/result.pdf")
check("idle result.pdf -> 404", r.status_code == 404, str(r.status_code))

# ---------- 2) 400/422 validation ----------
r = client.post("/api/reports/route-topology/start",
                json={"database": TEST_DB, "ips": ["10.20.0.9"], "username": "u"})
check("only non-mikrotik selection -> 400", r.status_code == 400, str(r.status_code))
r = client.post("/api/reports/route-topology/start",
                json={"database": TEST_DB, "central_router_ip": "not-an-ip", "username": "u"})
check("invalid central ip -> 422", r.status_code == 422, str(r.status_code))
r = client.post("/api/reports/route-topology/start",
                json={"database": "no_such_db_xyz", "username": "u"})
check("unknown database -> 404", r.status_code == 404, str(r.status_code))

# ---------- 3) happy path ----------
try:
    r = client.post("/api/reports/route-topology/start",
                    json={"database": TEST_DB, "central_router_ip": "172.19.1.6",
                          "username": "netadmin", "password": "secret", "max_workers": 4})
    check("start -> 200", r.status_code == 200, r.text[:120])
    check("start: 3 mikrotik devices planned", r.json().get("devices") == 3, r.text[:120])
    check("start: central ip echoed", r.json().get("central_router_ip") == "172.19.1.6")

    prog = wait_idle()
    check("progress finished", prog and not prog["running"], str(prog))
    check("progress: 3 done / 3 ok", prog["done"] == 3 and prog["ok"] == 3 and prog["failed"] == 0, str(prog))
    check("progress: ready", prog.get("ready") is True, str(prog.get("ready")))

    r = client.get("/api/reports/route-topology/result.pdf")
    check("result.pdf -> 200", r.status_code == 200, str(r.status_code))
    check("result: application/pdf", r.headers.get("content-type", "").startswith("application/pdf"))
    check("result: %PDF magic", r.content[:5] == b"%PDF-")
    check("result: attachment filename", "route_topology_" in r.headers.get("content-disposition", ""))
    check("result: X-Topology-Devices == 3", r.headers.get("X-Topology-Devices") == "3",
          r.headers.get("X-Topology-Devices", ""))
    check("result: X-Topology-Reachable == 2", r.headers.get("X-Topology-Reachable") == "2",
          r.headers.get("X-Topology-Reachable", ""))
    check("result: X-Topology-Unreachable == 1", r.headers.get("X-Topology-Unreachable") == "1")
    check("result: central router header", r.headers.get("X-Topology-Central-Router") == "172.19.1.6")
    pages = len(re.findall(rb"/Type\s*/Page[^s]", r.content))
    check("result: one page per device (3 pages)", pages == 3, str(pages))
    check("result: non-trivial size", len(r.content) > 2000, str(len(r.content)))
finally:
    rt.collect_topology_info = rt_collect_original
    appm.route_topology.collect_topology_info = rt_collect_original

# ---------- 4) cancel endpoint (idle) ----------
r = client.post("/api/reports/route-topology/cancel")
check("cancel when idle -> ok", r.status_code == 200 and r.json().get("cancel_requested") is False, r.text[:80])

# ---------- 5) failed connections still produce pages ----------
def _all_fail(host, username, password, port=8728, timeout=12.0):
    return _info(host, "", [], ok_=False)
rt.collect_topology_info = _all_fail
appm.route_topology.collect_topology_info = _all_fail
try:
    reset_state()
    r = client.post("/api/reports/route-topology/start",
                    json={"database": TEST_DB, "username": "u"})
    check("failed-conn start -> 200", r.status_code == 200, str(r.status_code))
    prog = wait_idle()
    check("failed-conn: done with ok=0", prog["done"] == 3 and prog["ok"] == 0, str(prog))
    r = client.get("/api/reports/route-topology/result.pdf")
    check("failed-conn result.pdf -> 200", r.status_code == 200, str(r.status_code))
    pages = len(re.findall(rb"/Type\s*/Page[^s]", r.content))
    check("failed-conn: still 3 pages", pages == 3, str(pages))
    check("failed-conn: error string visible on page", b"No route to host" in r.content
          or b"connection refused" in r.content or len(r.content) > 2500)
finally:
    rt.collect_topology_info = rt_collect_original
    appm.route_topology.collect_topology_info = rt_collect_original

# ---------- cleanup ----------
dbm.set_active_database(prev_active)
try:
    dbm.delete_database(TEST_DB)
except Exception:
    pass

print("\nALL OK" if ok else "\nFAILURES PRESENT")
sys.exit(0 if ok else 1)
