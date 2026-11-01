"""End-to-end verification: Cisco central-router config upload (کانفیگ روتر مرکزی سیسکو).

Covers:
1) cisco_config.parse_cisco_config — interfaces (physical/sub-interface/SVI/loopback),
   secondary IPs, shutdown, dot1Q vlan, static routes (vrf/ECMP/interface-gw/distance/name),
   connected networks, longest-prefix helpers
2) POST/GET/DELETE /api/reports/route-topology/cisco-config (multipart + JSON, 400 paths)
3) Full route-topology run with the uploaded config: core ghost node enriched from the
   Cisco config, cisco static-route edges (ev=cisco), X-Topology-Cisco header, and the
   same run WITHOUT the config for comparison.

The RouterOS API network layer is monkeypatched (no real device needed).
"""
import base64
import io
import os
import re
import shutil
import sqlite3
import sys
import time
import zlib

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import cisco_config as cc
import db as dbm
import route_topology as rt
from fastapi.testclient import TestClient
import main as appm

ok = True
def check(label, cond, extra=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label, extra)
    ok = ok and cond


# ===========================================================================
# 1) parser unit checks
# ===========================================================================
CFG = """
!=== Core router ===
version 15.2
hostname CORE-ISR-4331
!
interface GigabitEthernet0/0/0
 description Uplink-to-ISP
 ip address 85.15.1.10 255.255.255.252
 no shutdown
!
interface GigabitEthernet0/0/1.100
 description VLAN100-Mgmt-MikroTiks
 encapsulation dot1Q 100
 ip address 172.19.1.6 255.255.255.0
!
interface GigabitEthernet0/0/1.200
 description VLAN200-Servers
 encapsulation dot1Q 200
 ip address 172.18.1.1 255.255.255.0 secondary
 ip address 172.18.0.1 255.255.255.0
!
interface Vlan900
 description Legacy mgmt
 ip address 10.9.0.1 255.255.255.0
 shutdown
!
interface Loopback0
 ip address 10.255.255.1 255.255.255.255
!
ip route 0.0.0.0 0.0.0.0 85.15.1.9 name DEFAULT-ISP
ip route 172.18.24.0 255.255.255.0 172.18.0.250
ip route 172.29.193.0 255.255.255.0 172.19.1.2 200 name FLOATING-BACKUP
ip route vrf MGMT 10.20.0.0 255.255.255.0 10.9.0.2
ip route 172.28.0.0 255.255.0.0 GigabitEthernet0/0/1.100 172.19.1.9
!
end
"""
c = cc.parse_cisco_config(CFG)
check("parser: hostname", c["hostname"] == "CORE-ISR-4331", c["hostname"])
check("parser: version", c["version"] == "15.2")
check("parser: interface count (5)", len(c["interfaces"]) == 5,
      str([i["name"] for i in c["interfaces"]]))
_names = [i["name"] for i in c["interfaces"]]
check("parser: interface names", _names == ["GigabitEthernet0/0/0", "GigabitEthernet0/0/1.100",
      "GigabitEthernet0/0/1.200", "Vlan900", "Loopback0"], str(_names))
_g0 = c["interfaces"][0]
check("parser: /30 subnet", _g0["addresses"][0]["subnet"] == "85.15.1.8/30", str(_g0["addresses"]))
check("parser: description", _g0["description"] == "Uplink-to-ISP")
_sub = c["interfaces"][2]
check("parser: dot1Q vlan", _sub["vlan"] == 200)
check("parser: subinterface flag", _sub["subinterface"] is True)
check("parser: secondary + primary", len(_sub["addresses"]) == 2
      and _sub["addresses"][0]["secondary"] and _sub["addresses"][0]["subnet"] == "172.18.1.0/24"
      and _sub["primary_ip"] == "172.18.0.1", str(_sub["addresses"]))
check("parser: shutdown", c["interfaces"][3]["shutdown"] is True)
check("parser: loopback /32", c["interfaces"][4]["addresses"][0]["subnet"] == "10.255.255.1/32")
check("parser: 5 static routes", len(c["static_routes"]) == 5, str(len(c["static_routes"])))
_r0 = c["static_routes"][0]
check("parser: default route gw+name", _r0["prefix"] == "0.0.0.0/0"
      and _r0["next_hops"] == ["85.15.1.9"] and _r0["name"] == "DEFAULT-ISP", str(_r0))
_r3 = c["static_routes"][3]
check("parser: vrf route", _r3["vrf"] == "MGMT" and _r3["next_hops"] == ["10.9.0.2"], str(_r3))
_r4 = c["static_routes"][4]
check("parser: interface next-hop + distance", _r4["next_hops"] == ["172.19.1.9"]
      and _r4["interface"] == "GigabitEthernet0/0/1.100", str(_r4))
_r2 = c["static_routes"][2]
check("parser: floating distance 200", _r2["distance"] == "200", str(_r2))
check("parser: 6 connected networks", len(c["networks"]) == 6, str(len(c["networks"])))
check("helper: find_connected_iface exact subnet",
      cc.find_connected_iface(c, "172.18.1.250") == ("GigabitEthernet0/0/1.200", "172.18.1.1"),
      str(cc.find_connected_iface(c, "172.18.1.250")))
check("helper: mgmt iface", cc.find_connected_iface(c, "172.19.1.2") == ("GigabitEthernet0/0/1.100", "172.19.1.6"))
check("helper: shutdown iface skipped", cc.find_connected_iface(c, "10.9.0.5") == ("", ""))
check("helper: unknown net", cc.find_connected_iface(c, "8.8.8.8") == ("", ""))
_rts = cc.routes_toward(c, "172.18.24.10")
check("helper: routes_toward longest-first",
      [r["prefix"] for r in _rts] == ["172.18.24.0/24", "0.0.0.0/0"], str([r["prefix"] for r in _rts]))
check("helper: central_ip_known", cc.central_ip_known(c, "172.19.1.6") is True
      and cc.central_ip_known(c, "172.19.1.7") is False)
check("helper: looks_like_cisco_config positive", cc.looks_like_cisco_config(CFG) is True)
check("helper: looks_like_cisco_config negative",
      cc.looks_like_cisco_config("hello world\nsome random\nfile content") is False)
_s = cc.summary(c)
check("helper: summary counts", _s["interfaces"] == 5 and _s["addresses"] == 6
      and _s["static_routes"] == 5 and _s["hostname"] == "CORE-ISR-4331", str(_s))

# minimal-but-valid MikroTik-flavored text must NOT pass the cisco sniff test
check("sniff: random text rejected", cc.looks_like_cisco_config("totally unrelated text") is False)


# ===========================================================================
# 2) HTTP setup
# ===========================================================================
client = TestClient(appm.app)
_r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
assert _r.status_code == 200, f"login failed: {_r.status_code} {_r.text[:100]}"

# keep any real uploaded config safe
REAL_CFG = appm.CISCO_CONFIG_PATH
_backup = None
if REAL_CFG.is_file():
    _backup = REAL_CFG.with_suffix(".txt.bak_test")
    shutil.move(str(REAL_CFG), str(_backup))

def restore_cfg():
    if REAL_CFG.exists():
        REAL_CFG.unlink()
    if _backup is not None and _backup.is_file():
        shutil.move(str(_backup), str(REAL_CFG))

def reset_state():
    appm.TOPOLOGY_STATE.update({"running": False, "total": 0, "done": 0, "ok": 0, "failed": 0,
                                "current_ip": "", "phase": "", "error": None, "canceled": False,
                                "pdf": None, "stats": {}})

def wait_idle(timeout_s=25.0):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        p = client.get("/api/reports/route-topology/progress").json()
        if not p["running"]:
            return p
        time.sleep(0.05)
    return p

def pdf_text(content: bytes) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(content))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception:
        pass
    blob = bytearray(content)
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", content, re.DOTALL):
        chunk = m.group(1)
        try:
            dec = base64.a85decode(chunk, adobe=True)
            try:
                dec = zlib.decompress(dec)
            except Exception:
                pass
            blob += dec
        except Exception:
            blob += chunk
    return blob.decode("latin-1", "replace")


# ===========================================================================
# 3) cisco-config endpoints
# ===========================================================================
try:
    restore_cfg()

    r = client.get("/api/reports/route-topology/cisco-config")
    check("GET before upload: loaded=False", r.status_code == 200 and r.json().get("loaded") is False, r.text[:120])

    r = client.post("/api/reports/route-topology/cisco-config", json={"text": ""})
    check("POST empty text -> 400", r.status_code == 400, str(r.status_code))
    r = client.post("/api/reports/route-topology/cisco-config",
                    json={"text": "random notes\nnothing like a cisco config here"})
    check("POST non-cisco text -> 400", r.status_code == 400, r.text[:100])
    r = client.post("/api/reports/route-topology/cisco-config", json={})
    check("POST json without text -> 400", r.status_code == 400, str(r.status_code))

    r = client.post("/api/reports/route-topology/cisco-config", json={"text": CFG})
    check("POST json text -> 200", r.status_code == 200, r.text[:160])
    check("POST: saved flag", r.json().get("saved") is True)
    check("POST: parsed summary hostname", r.json().get("summary", {}).get("hostname") == "CORE-ISR-4331", r.text[:160])
    check("POST: message mentions counts", "اینترفیس" in r.json().get("message", ""))

    r = client.get("/api/reports/route-topology/cisco-config")
    check("GET after upload: loaded=True", r.json().get("loaded") is True, r.text[:120])
    check("GET after upload: summary routes", r.json().get("summary", {}).get("static_routes") == 5)
    check("GET after upload: uploaded_at present", bool(r.json().get("uploaded_at")))

    # multipart upload (like the browser <input type=file>)
    r = client.post("/api/reports/route-topology/cisco-config",
                    files={"file": ("core-run.txt", CFG.encode("utf-8"), "text/plain")})
    check("POST multipart -> 200", r.status_code == 200, r.text[:160])
    check("POST multipart: filename echoed", r.json().get("filename") == "core-run.txt", r.text[:120])
    r = client.post("/api/reports/route-topology/cisco-config", files={})
    check("POST multipart without file -> 400", r.status_code == 400, str(r.status_code))

    r = client.delete("/api/reports/route-topology/cisco-config")
    check("DELETE -> ok", r.status_code == 200 and r.json().get("deleted") is True)
    r = client.get("/api/reports/route-topology/cisco-config")
    check("GET after delete: loaded=False", r.json().get("loaded") is False)

    # =========================================================================
    # 4) full route-topology run WITH the uploaded cisco config
    # =========================================================================
    r = client.post("/api/reports/route-topology/cisco-config", json={"text": CFG})
    assert r.status_code == 200, r.text[:200]

    TEST_DB = "zz_cisco_topology_test"
    dbm.create_database(TEST_DB)
    path = dbm.db_path_for(TEST_DB)
    prev_active = dbm.get_active_db_name()
    dbm.set_active_database(TEST_DB)
    conn = sqlite3.connect(path)
    rows = [
        ("10.20.0.2", "R-BRANCH", "Sites", "[8728]", "mikrotik_candidate"),
        ("10.20.0.3", "DEV-24", "", "[8728]", "mikrotik_candidate"),
        ("10.20.0.9", "Printer", "", "[]", "non_mikrotik"),   # must be skipped
    ]
    for (ip, name, tags, ports, cls) in rows:
        conn.execute(
            """INSERT INTO devices (ip, ping_ok, open_ports, port_states, classification,
               first_seen, last_seen, seen_count, device_name, tags)
               VALUES (?,1,?,'{}',?,datetime('now'),datetime('now'),2,?,?)""",
            (ip, ports, cls, name, tags))
    conn.commit(); conn.close()

    def _info(ip, identity, addresses, routes=(), ifaces=(), neighbors=(), ok_=True):
        return {"ip": ip, "ok": ok_, "error": None if ok_ else "connection refused",
                "identity": identity,
                "resource": {"version": "7.14", "board": "RB4011", "uptime": "3w"} if ok_ else {},
                "interfaces": list(ifaces), "addresses": list(addresses),
                "neighbors": list(neighbors), "routes": list(routes), "arp": []}

    def _if(n):
        return [{"name": n, "type": "ether", "running": "true", "disabled": "false",
                 "mac_address": "", "comment": ""}]

    # R-BRANCH: mgmt 10.20.0.2, LAN 172.18.0.250/24 (same subnet as cisco Gi0/0/1.200),
    #           default gw = 172.18.0.1 (the Cisco itself)
    # DEV-24:   mgmt 10.20.0.3, LAN 172.18.24.10/24, default gw = R-BRANCH
    CANNED = {
        "10.20.0.2": lambda: _info("10.20.0.2", "R-BRANCH",
                                   [{"address": "172.18.0.250/24", "interface": "ether1", "network": "172.18.0.0"}],
                                   routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.18.0.1", "distance": "1", "immediate_gw": ""}],
                                   ifaces=_if("ether1") + _if("ether2")),
        "10.20.0.3": lambda: _info("10.20.0.3", "DEV-24",
                                   [{"address": "172.18.24.10/24", "interface": "ether1", "network": "172.18.24.0"}],
                                   routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.18.0.250", "distance": "1", "immediate_gw": ""}],
                                   ifaces=_if("ether1")),
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
        reset_state()
        r = client.post("/api/reports/route-topology/start",
                        json={"database": TEST_DB, "central_router_ip": "172.19.1.6",
                              "username": "netadmin", "password": "x", "max_workers": 2})
        check("cisco run: start -> 200", r.status_code == 200, r.text[:140])
        check("cisco run: 2 mikrotik devices", r.json().get("devices") == 2, r.text[:140])
        prog = wait_idle()
        check("cisco run: finished", prog and not prog["running"], str(prog))
        check("cisco run: no error", not prog.get("error"), str(prog.get("error")))
        check("cisco run: 2 done / 2 ok", prog["done"] == 2 and prog["ok"] == 2, str(prog))
        r = client.get("/api/reports/route-topology/result.pdf")
        check("cisco run: result.pdf -> 200", r.status_code == 200, str(r.status_code))
        check("cisco run: X-Topology-Cisco == CORE-ISR-4331",
              r.headers.get("X-Topology-Cisco") == "CORE-ISR-4331", r.headers.get("X-Topology-Cisco", ""))
        check("cisco run: both devices reachable (X-Topology-Reachable == 2)",
              r.headers.get("X-Topology-Reachable") == "2", r.headers.get("X-Topology-Reachable", ""))
        txt = pdf_text(r.content)
        check("cisco run: core hostname in PDF", "CORE-ISR-4331" in txt)
        check("cisco run: cisco iface name in PDF (Gi0/0/1.200)", "GigabitEthernet0/0/1.200" in txt)
        check("cisco run: CISCO-ROUTE evidence tag in PDF", "CISCO-ROUTE" in txt)
        check("cisco run: 'Cisco static route' in hop table", "Cisco static route" in txt)
        check("cisco run: cisco static route evidence line",
              re.search(r"cisco CORE-ISR-4331: route 172\.18\.24\.0/24 via 172\.18\.0\.250", txt) is not None,
              "evidence line")
        check("cisco run: default-route cisco evidence line",
              re.search(r"cisco CORE-ISR-4331: route 0\.0\.0\.0/0 via 85\.15\.1\.9", txt) is not None,
              "default evidence line")
        pages = len(re.findall(rb"/Type\s*/Page[^s]", r.content))
        check("cisco run: one page per device (2 pages)", pages == 2, str(pages))

        # --- the same run WITHOUT the cisco config: R-BRANCH default gw (172.18.0.1)
        # is now an unknown ghost -> DEV-24 falls back to best-effort upstream chain
        REAL_CFG.unlink()
        reset_state()
        r = client.post("/api/reports/route-topology/start",
                        json={"database": TEST_DB, "central_router_ip": "172.19.1.6",
                              "username": "netadmin", "password": "x", "max_workers": 2})
        check("no-cisco run: start -> 200", r.status_code == 200, r.text[:120])
        prog = wait_idle()
        r = client.get("/api/reports/route-topology/result.pdf")
        check("no-cisco run: result.pdf -> 200", r.status_code == 200, str(r.status_code))
        check("no-cisco run: X-Topology-Cisco empty", (r.headers.get("X-Topology-Cisco") or "") == "",
              r.headers.get("X-Topology-Cisco", ""))
        check("no-cisco run: DEV-24 not fully reachable (X-Topology-Reachable < 2)",
              int(r.headers.get("X-Topology-Reachable", "0")) < 2,
              r.headers.get("X-Topology-Reachable", ""))
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

print("\nALL OK" if ok else "\nFAILURES PRESENT")
sys.exit(0 if ok else 1)
