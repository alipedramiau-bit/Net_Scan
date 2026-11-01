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
check("A reachable via route-gateway edge to core (1 hop, route evidence)",
      pa["reachable"] and len(pa["hops"]) == 1 and pa["hops"][0]["ev"] == "route"
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
check("route-gateway edge to virtual core", pc["reachable"] and len(pc["hops"]) == 1
      and pc["hops"][0]["to_key"] == "core" and pc["hops"][0]["ev"] == "route", str(pc["hops"]))

# ---- failed connection still gets a node ----
topo4 = rt.build_topology([_info("10.5.5.5", "", [], ok_=False)], [], "172.19.1.6")
check("failed node unreachable", not topo4["paths"]["d:10.5.5.5"]["reachable"])
check("summary counts", topo4["summary"]["devices"] == 1 and topo4["summary"]["unreachable"] == 1)

print("\nALL OK" if ok else "\nFAILURES PRESENT")
sys.exit(0 if ok else 1)
