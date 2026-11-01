"""ساخت نمونهٔ واقعی «گزارش CSV دلایل نرسیدن به روتر مرکزی» از مسیر اندپوینت."""
import csv
import io
import os
import shutil
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import db as dbm
import route_topology as rt
from fastapi.testclient import TestClient
import main as appm

OUT = "/home/z/my-project/download/نمونه-گزارش-CSV-دلایل-نرسیدن-به-روتر-مرکزی.csv"

IF = lambda n, run="true": [{"name": n, "type": "ether", "running": run, "disabled": "false",
                             "mac_address": "", "comment": ""}]

client = TestClient(appm.app)
assert client.post("/api/login", json={"username": "admin", "password": "NetAdmin"}).status_code == 200

REAL_CFG = appm.CISCO_CONFIG_PATH
_backup = None
if REAL_CFG.is_file():
    _backup = REAL_CFG.with_suffix(".txt.bak_sample21")
    shutil.move(str(REAL_CFG), str(_backup))

TEST_DB = "zz_unreach_sample"
try:
    if REAL_CFG.exists():
        REAL_CFG.unlink()
    appm.TOPOLOGY_STATE.update({"running": False, "unreachable_rows": None, "pdf": None, "stats": {}})
    dbm.create_database(TEST_DB)
    prev_active = dbm.get_active_db_name()
    dbm.set_active_database(TEST_DB)
    conn = sqlite3.connect(dbm.db_path_for(TEST_DB))
    for (ip, name) in [("10.30.1.1", "R-CORE-LINK"), ("10.30.2.1", "RB-NoRoute"),
                       ("10.30.3.1", "RB-GhostGw"), ("10.30.4.1", "RB-LinkDown"),
                       ("10.30.5.1", "RB-ApiDead"), ("10.30.6.1", "RB-WrongRoute")]:
        conn.execute(
            """INSERT INTO devices (ip, ping_ok, open_ports, port_states, classification,
               first_seen, last_seen, seen_count, device_name, tags, device_type)
               VALUES (?,1,'[8728]','{}','mikrotik_candidate',datetime('now'),datetime('now'),2,?,?,'Router')""",
            (ip, name, "site-sample"))
    conn.commit(); conn.close()

    def _info(ip, identity, addresses, routes=(), ifaces=(), ok_=True, error=None):
        return {"ip": ip, "ok": ok_, "error": (None if ok_ else error), "identity": identity,
                "resource": {}, "interfaces": list(ifaces), "addresses": list(addresses),
                "neighbors": [], "routes": list(routes), "arp": []}

    CANNED = {
        "10.30.1.1": lambda: _info("10.30.1.1", "R-CORE-LINK",
                                   [{"address": "10.30.1.1/24", "interface": "ether1", "network": "10.30.1.0"}],
                                   routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.19.1.6", "distance": "1", "immediate_gw": ""}],
                                   ifaces=IF("ether1")),
        "10.30.2.1": lambda: _info("10.30.2.1", "RB-NoRoute",
                                   [{"address": "10.30.2.1/24", "interface": "ether1", "network": "10.30.2.0"}],
                                   routes=[], ifaces=IF("ether1")),
        "10.30.3.1": lambda: _info("10.30.3.1", "RB-GhostGw",
                                   [{"address": "10.30.3.1/24", "interface": "BR-link-up", "network": "10.30.3.0"}],
                                   routes=[{"dst_address": "0.0.0.0/0", "gateway": "10.30.3.254", "distance": "1", "immediate_gw": ""}],
                                   ifaces=IF("BR-link-up")),
        "10.30.4.1": lambda: _info("10.30.4.1", "RB-LinkDown",
                                   [{"address": "10.30.4.1/24", "interface": "ether1", "network": "10.30.4.0"},
                                    {"address": "10.44.0.2/24", "interface": "ether2", "network": "10.44.0.0"}],
                                   routes=[{"dst_address": "0.0.0.0/0", "gateway": "10.44.0.1", "distance": "1", "immediate_gw": ""}],
                                   ifaces=IF("ether1") + IF("ether2", run="false")),
        "10.30.5.1": lambda: _info("10.30.5.1", "", [], ok_=False, error="timed out during api login"),
        "10.30.6.1": lambda: _info("10.30.6.1", "RB-WrongRoute",
                                   [{"address": "10.30.6.1/24", "interface": "ether1", "network": "10.30.6.0"}],
                                   routes=[{"dst_address": "192.168.50.0/24", "gateway": "10.30.6.9", "distance": "1", "immediate_gw": ""}],
                                   ifaces=IF("ether1")),
    }
    orig = rt.collect_topology_info
    rt.collect_topology_info = lambda host, username, password, port=8728, timeout=12.0: (
        CANNED[host]() if host in CANNED else _info(host, "", [], ok_=False, error="timed out"))
    appm.route_topology.collect_topology_info = rt.collect_topology_info
    try:
        r = client.post("/api/reports/route-topology/start",
                        json={"database": TEST_DB, "central_router_ip": "172.19.1.6",
                              "username": "u", "password": "p", "max_workers": 3})
        assert r.status_code == 200, r.text[:200]
        for _ in range(300):
            if not client.get("/api/reports/route-topology/progress").json()["running"]:
                break
            import time; time.sleep(0.05)
        r = client.get("/api/reports/route-topology/unreachable-csv")
        assert r.status_code == 200, r.text[:200]
        with open(OUT, "wb") as f:
            f.write(r.content)
        rows = list(csv.reader(io.StringIO(r.content.decode("utf-8-sig"))))
        print("rows:", len(rows) - 1, "->", OUT)
    finally:
        rt.collect_topology_info = orig
        appm.route_topology.collect_topology_info = orig
        dbm.set_active_database(prev_active)
        try:
            dbm.delete_database(TEST_DB)
        except Exception:
            pass
finally:
    if REAL_CFG.exists():
        REAL_CFG.unlink()
    if _backup is not None and _backup.is_file():
        shutil.move(str(_backup), str(REAL_CFG))
    appm.TOPOLOGY_STATE.update({"running": False, "unreachable_rows": None, "pdf": None, "stats": {}})
