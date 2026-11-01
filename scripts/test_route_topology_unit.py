"""Unit checks for route_topology.build_topology (no network, pure functions)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import route_topology as rt

ok = True
def check(label, cond, extra=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label, extra)
    ok = ok and cond


def _info(ip, identity, addresses, neighbors=(), routes=(), ifaces=(), ok_=True):
    return {"ip": ip, "ok": ok_, "error": None if ok_ else "conn refused",
            "identity": identity, "resource": {"version": "7.14", "board": "RB4011", "uptime": "3w"},
            "interfaces": list(ifaces), "addresses": list(addresses),
            "neighbors": list(neighbors), "routes": list(routes), "arp": []}


IF = lambda n: [{"name": n, "type": "ether", "running": "true", "disabled": "false",
                 "mac_address": "AA:BB:CC:00:00:0" + str(len(n)), "comment": ""}]

# topology:
#   R-EDGE (172.18.2.217/29 on ether3; 172.18.8.114/30 on ether5)
#     - MNDP neighbor R2-MAI 172.18.8.113 on ether5  (same /30 as R-EDGE ether5)
#   R2-MAI (172.18.8.113/30 on ether5; 172.19.1.6/24 on ether1)  <- IS the core
infos = [
    _info("172.18.2.217", "RB-Ghonouti",
          [{"address": "172.18.115.62/29", "interface": "ether1", "network": "172.18.115.56"},
           {"address": "172.18.2.217/29", "interface": "ether3", "network": "172.18.2.216"},
           {"address": "172.18.8.114/30", "interface": "ether5", "network": "172.18.8.112"}],
          neighbors=[{"identity": "R2-MAI", "address": "172.18.8.113", "interface": "ether5",
                      "platform": "RouterOS", "version": "7.12", "mac_address": "AA:BB:CC:00:00:99",
                      "uptime": "5w"}],
          routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.18.8.113", "distance": "1", "immediate_gw": ""},
                  {"dst_address": "172.18.8.112/30", "gateway": "ether5", "distance": "0", "immediate_gw": ""}],
          ifaces=IF("ether1") + IF("ether3") + IF("ether5")),
    _info("172.18.8.113", "R2-MAI",
          [{"address": "172.18.8.113/30", "interface": "ether5", "network": "172.18.8.112"},
           {"address": "172.19.1.6/24", "interface": "ether1", "network": "172.19.1.0"}],
          neighbors=[{"identity": "RB-Ghonouti", "address": "172.18.8.114", "interface": "ether5",
                      "platform": "RouterOS", "version": "7.14", "mac_address": "", "uptime": ""}],
          routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.19.1.1", "distance": "1", "immediate_gw": ""}],
          ifaces=IF("ether1") + IF("ether5")),
]
devices = [
    {"ip": "172.18.2.217", "device_name": "RB-Ghonouti", "tags": "tag1", "ping_ok": True,
     "open_ports": [22, 80, 8291, 8728], "device_type": "Router"},
    {"ip": "172.18.8.113", "device_name": "R2-MAI", "tags": "", "ping_ok": True,
     "open_ports": [8728], "device_type": "Router"},
]

topo = rt.build_topology(infos, devices, "172.19.1.6")

check("core node is R2-MAI (holds central ip)",
      topo["core_key"] == "d:172.18.8.113" and topo["nodes"][topo["core_key"]]["is_core"],
      topo["core_key"])
p_edge = topo["paths"]["d:172.18.2.217"]
check("edge device reachable", p_edge["reachable"], str(p_edge))
check("edge device path is 1 hop", len(p_edge["hops"]) == 1, str(len(p_edge["hops"])))
hop = p_edge["hops"][0]
check("hop from=edge to=core", hop["from_key"] == "d:172.18.2.217" and hop["to_key"] == topo["core_key"])
check("hop from_if ether5", hop["from_if"] == "ether5", hop["from_if"])
check("hop to_if ether5 (via neighbor ip lookup)", hop["to_if"] == "ether5", hop["to_if"])
check("hop from_ip is edge /30 ip", hop["from_ip"] == "172.18.8.114", hop["from_ip"])
check("hop evidence mndp", hop["ev"] == "mndp", hop["ev"])
check("main ip = ip toward core", p_edge["main_ip"] == "172.18.8.114", p_edge["main_ip"])
check("core path empty (is_core)", topo["paths"][topo["core_key"]]["is_core"])
check("summary links == 1", topo["summary"]["links"] == 1, str(topo["summary"]))
check("no ghost nodes when both queried", all(not n["ghost"] for k, n in topo["nodes"].items() if k != "core"),
      str([k for k, n in topo["nodes"].items() if n["ghost"]]))

# ---- ghost path: A -> ghost B -> core, B unknown but A's route gw is core ----
infos2 = [
    _info("10.0.0.1", "R-A",
          [{"address": "10.0.0.1/24", "interface": "ether1", "network": "10.0.0.0"},
           {"address": "10.9.9.2/30", "interface": "ether2", "network": "10.9.9.0"}],
          neighbors=[{"identity": "R-B", "address": "10.9.9.1", "interface": "ether2",
                      "platform": "RouterOS", "version": "6.49", "mac_address": "", "uptime": ""}],
          routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.19.1.6", "distance": "2", "immediate_gw": ""}],
          ifaces=IF("ether1") + IF("ether2")),
]
devices2 = [{"ip": "10.0.0.1", "device_name": "R-A", "tags": "", "ping_ok": True, "open_ports": [8728], "device_type": ""}]
topo2 = rt.build_topology(infos2, devices2, "172.19.1.6")
pa = topo2["paths"]["d:10.0.0.1"]
check("ghost created for R-B", "g:10.9.9.1" in topo2["nodes"], str(list(topo2["nodes"])))
check("virtual core node", topo2["core_key"] == "core")
check("A reachable via default-route gateway edge to core (1 hop, default evidence)",
      pa["reachable"] and len(pa["hops"]) == 1 and pa["hops"][0]["ev"] == "default"
      and pa["hops"][0]["to_key"] == "core",
      str([(h['from_key'], h['to_key'], h['ev']) for h in pa['hops']]))
check("edge A-ghost mapped (mndp)",
      any((e["a"] == "d:10.0.0.1" and e["b"] == "g:10.9.9.1" and e["a_if"] == "ether2" and e["ev"] == "mndp")
          for e in topo2["edges"]), str(topo2["edges"]))

# ---- route-gateway edge: device routes via central ip directly ----
infos3 = [
    _info("10.7.7.1", "R-C",
          [{"address": "10.7.7.1/24", "interface": "ether1", "network": "10.7.7.0"}],
          neighbors=[],
          routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.19.1.6", "distance": "1", "immediate_gw": ""}],
          ifaces=IF("ether1")),
]
topo3 = rt.build_topology(infos3, [{"ip": "10.7.7.1", "device_name": "R-C", "tags": "", "ping_ok": True,
                                    "open_ports": [8728], "device_type": ""}], "172.19.1.6")
pc = topo3["paths"]["d:10.7.7.1"]
check("default-route gateway edge to virtual core (Task 17: default route evidence)",
      pc["reachable"] and len(pc["hops"]) == 1
      and pc["hops"][0]["to_key"] == "core" and pc["hops"][0]["ev"] == "default", str(pc["hops"]))

# ---- Task 17: روش بهتر یافتن مسیر — روت پیش‌فرض و hop بالای دستگاه ----
# (۱) طولانی‌ترین پیشوند بر روت پیش‌فرض مقدم است
hh, kk = rt._route_next_hops(
    [{"dst_address": "0.0.0.0/0", "gateway": "10.0.0.254", "distance": "1", "immediate_gw": ""},
     {"dst_address": "172.19.1.0/24", "gateway": "10.0.0.9", "distance": "1", "immediate_gw": ""}],
    "172.19.1.6")
check("longest-prefix beats default route", hh == [("10.0.0.9", "")] and kk == "specific", str((hh, kk)))
# (۲) ECMP — دو گیت‌وی هم‌distance هر دو برمی‌گردند
hh2, kk2 = rt._route_next_hops([{"dst_address": "0.0.0.0/0", "gateway": "1.1.1.1,2.2.2.2", "distance": "1", "immediate_gw": ""}], "172.19.1.6")
check("ECMP default gateways both returned", kk2 == "default" and [g for g, _ in hh2] == ["1.1.1.1", "2.2.2.2"], str((hh2, kk2)))
# (۳) کم‌ترین distance بین دو روت پیش‌فرض انتخاب می‌شود
hh3, kk3 = rt._route_next_hops(
    [{"dst_address": "0.0.0.0/0", "gateway": "9.9.9.9", "distance": "2", "immediate_gw": ""},
     {"dst_address": "0.0.0.0/0", "gateway": "8.8.8.8", "distance": "1", "immediate_gw": ""}],
    "172.19.1.6")
check("min-distance default route wins", kk3 == "default" and hh3 == [("8.8.8.8", "")], str((hh3, kk3)))
# (۴) زنجیرهٔ بالادست: A → B (گیت‌وی پیش‌فرض = دستگاه خوانده‌شده) → core
A_up = _info("10.1.1.2", "Edge-A",
             [{"address": "10.1.1.2/24", "interface": "e1", "network": "10.1.1.0"}],
             routes=[{"dst_address": "0.0.0.0/0", "gateway": "10.1.1.1", "distance": "1", "immediate_gw": ""}],
             ifaces=IF("e1"))
B_up = _info("10.1.1.1", "Mid-B",
             [{"address": "10.1.1.1/24", "interface": "e1", "network": "10.1.1.0"},
              {"address": "172.19.1.2/30", "interface": "e2", "network": "172.19.1.0"}],
             routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.19.1.6", "distance": "1", "immediate_gw": ""}],
             ifaces=IF("e1") + IF("e2"))
topo5 = rt.build_topology([A_up, B_up], [], "172.19.1.6")
pa5 = topo5["paths"]["d:10.1.1.2"]
check("chain via scanned default-gateway device reachable",
      pa5["reachable"] and len(pa5["hops"]) == 2, str([(h['from_key'], h['to_key'], h['ev']) for h in pa5.get('hops', [])]))
check("Mid-B default gw == central ip edge to core",
      any(h["to_key"] == topo5["core_key"] and h["ev"] == "default" for h in pa5["hops"]),
      str([(h['from_key'], h['to_key'], h['ev']) for h in pa5['hops']]))
# (۵) دستگاه بدون مسیر کامل → زنجیرهٔ بالادست best-effort با گرهٔ شبح hop
SA = _info("172.18.1.68", "RB-Salmaneh",
           [{"address": "172.18.1.68/28", "interface": "BR-link-abdn-to-link-shdgn", "network": "172.18.1.64"}],
           routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.18.1.71", "distance": "1", "immediate_gw": ""},
                   {"dst_address": "0.0.0.0/0", "gateway": "172.18.1.65", "distance": "1", "immediate_gw": ""}],
           ifaces=IF("BR-link-abdn-to-link-shdgn"))
topo6 = rt.build_topology([SA], [], "172.19.1.6")
p6 = topo6["paths"]["d:172.18.1.68"]
check("unreachable device gets best-effort upstream chain",
      not p6["reachable"] and len(p6.get("upstream") or []) == 1, str(p6.get("upstream")))
up0 = (p6.get("upstream") or [{}])[0]
check("upstream hop ip = default gateway", up0.get("to_ip") == "172.18.1.71", str(up0))
check("upstream evidence = default", up0.get("ev") == "default", str(up0.get("ev")))
g6 = topo6["nodes"].get("g:172.18.1.71")
check("upstream ghost hop node created", bool(g6) and g6.get("upstream") is True,
      str({k: v for k, v in (g6 or {}).items() if k in ("key", "upstream")}))
check("summary counts upstream_only", topo6["summary"]["upstream_only"] == 1, str(topo6["summary"]))
# (۶) حلقهٔ روتینگ: زنجیرهٔ بالادست بی‌نهایت نمی‌شود
LA = _info("10.2.2.2", "Loop-A",
           [{"address": "10.2.2.2/24", "interface": "e1", "network": "10.2.2.0"}],
           routes=[{"dst_address": "0.0.0.0/0", "gateway": "10.2.2.3", "distance": "1", "immediate_gw": ""}],
           ifaces=IF("e1"))
LB = _info("10.2.2.3", "Loop-B",
           [{"address": "10.2.2.3/24", "interface": "e1", "network": "10.2.2.0"}],
           routes=[{"dst_address": "0.0.0.0/0", "gateway": "10.2.2.2", "distance": "1", "immediate_gw": ""}],
           ifaces=IF("e1"))
topo7 = rt.build_topology([LA, LB], [], "172.19.1.6")
u7a = topo7["paths"]["d:10.2.2.2"].get("upstream") or []
u7b = topo7["paths"]["d:10.2.2.3"].get("upstream") or []
check("routing loop terminates upstream chain", len(u7a) <= 6 and len(u7b) <= 6, str((len(u7a), len(u7b))))

# ---- Task 23: کشف hop بالاسری با default روت — نه میان‌بر ساب‌نت همسایه ----
# D هم‌ساب‌نت S است (یال subnet) ولی default گیت‌وی‌اش U است؛ U به core می‌رسد.
# مسیر گزارش‌شده باید D→U→core باشد (سلسله‌مراتب default)، نه D→S→core.
D23 = _info("10.3.0.2", "D23",
            [{"address": "10.3.0.2/24", "interface": "e1", "network": "10.3.0.0"}],
            routes=[{"dst_address": "0.0.0.0/0", "gateway": "10.4.0.1", "distance": "1", "immediate_gw": ""}],
            ifaces=IF("e1"))
S23 = _info("10.3.0.3", "S23",
            [{"address": "10.3.0.3/24", "interface": "e1", "network": "10.3.0.0"}],
            routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.19.1.6", "distance": "1", "immediate_gw": ""}],
            ifaces=IF("e1"))
U23 = _info("10.4.0.1", "U23",
            [{"address": "10.4.0.1/24", "interface": "e1", "network": "10.4.0.0"}],
            routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.19.1.6", "distance": "1", "immediate_gw": ""}],
            ifaces=IF("e1"))
topo23 = rt.build_topology([D23, S23, U23],
                           [{"ip": "10.3.0.2", "id": 101}, {"ip": "10.4.0.1", "id": 103}], "172.19.1.6")
p23 = topo23["paths"]["d:10.3.0.2"]
check("Task 23: path follows default-route hierarchy (D→U→core)",
      p23["reachable"] and [h["to_key"] for h in p23["hops"]] == ["d:10.4.0.1", topo23["core_key"]],
      str([(h['from_key'], h['to_key'], h['ev']) for h in p23.get('hops', [])]))
check("Task 23: D-U hop is the default gateway edge",
      p23["hops"] and p23["hops"][0]["to_ip"] == "10.4.0.1", str(p23["hops"][:1]))
check("Task 23: inventory carries device id (dev_id)",
      topo23["nodes"]["d:10.3.0.2"]["dev_id"] == 101
      and topo23["nodes"]["d:10.4.0.1"]["dev_id"] == 103,
      str({k: n.get("dev_id") for k, n in topo23["nodes"].items() if not n["ghost"]}))
hh23 = rt._route_default_next_hops(D23["routes"])
check("Task 23: D default next-hop = U only", [c["gw"] for c in hh23] == ["10.4.0.1"], str(hh23))

# ---- failed connection still gets a node ----
topo4 = rt.build_topology([_info("10.5.5.5", "", [], ok_=False)], [], "172.19.1.6")
check("failed node unreachable", not topo4["paths"]["d:10.5.5.5"]["reachable"])
check("summary counts", topo4["summary"]["devices"] == 1 and topo4["summary"]["unreachable"] == 1)

print("\nALL OK" if ok else "\nFAILURES PRESENT")
sys.exit(0 if ok else 1)
