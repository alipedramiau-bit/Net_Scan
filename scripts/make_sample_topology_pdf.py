"""Generate a sample Route Topology PDF (data mirrors the user's sample report)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import route_topology as rt
import route_pdf


def ifaces(names_types):
    out = []
    for n, t in names_types:
        out.append({"name": n, "type": t, "running": "true" if "wlan" not in n else "false",
                    "disabled": "false", "mac_address": "48:8F:5A:12:" + f"{len(out):02X}:" + f"{abs(hash(n)) % 255:02X}",
                    "comment": ""})
    return out


def addr(a, i, n):
    return {"address": a, "interface": i, "network": n}


gh_addresses = [
    addr("172.18.115.62/29", "ether1", "172.18.115.56"),
    addr("172.18.2.217/29", "ether3", "172.18.2.216"),
    addr("172.18.8.114/30", "ether5", "172.18.8.112"),
    addr("10.10.10.1/24", "ether7", "10.10.10.0"),
    addr("192.168.20.1/24", "bridge-lan", "192.168.20.0"),
    addr("172.18.50.1/24", "vlan50", "172.18.50.0"),
    addr("172.31.8.1/30", "sfp-sfpplus1", "172.31.8.0"),
]
gh_ifaces = ifaces([(f"ether{i}", "ether") for i in range(1, 16)] +
                   [("bridge-lan", "bridge"), ("vlan50", "vlan"), ("vlan60", "vlan"),
                    ("wlan1", "wlan"), ("wlan2", "wlan"), ("sfp-sfpplus1", "sfp"),
                    ("sfp-sfpplus2", "sfp"), ("pppoe-out1", "pppoe-out"), ("lo", "loopback")])

mai_addresses = [
    addr("172.18.8.113/30", "ether3", "172.18.8.112"),
    addr("172.19.1.6/24", "ether1", "172.19.1.0"),
    addr("10.20.0.1/24", "ether2", "10.20.0.0"),
]
mai_ifaces = ifaces([(f"ether{i}", "ether") for i in range(1, 9)] + [("bridge-core", "bridge")])

infos = [
    {"ip": "172.18.2.217", "ok": True, "error": None, "identity": "RB-Ghonouti",
     "resource": {"version": "7.14.3 (stable)", "board": "RB4011iGS+RM", "uptime": "12w3d 04:11:22", "cpu_load": "4"},
     "interfaces": gh_ifaces, "addresses": gh_addresses,
     "neighbors": [{"identity": "R2-MAI(Router.Amozeshi)", "address": "172.18.8.113", "interface": "ether5",
                    "platform": "RouterOS", "version": "7.12.1", "mac_address": "48:8F:5A:AA:00:01", "uptime": "5w2d"}],
     "routes": [
         {"dst_address": "0.0.0.0/0", "gateway": "172.18.8.113", "distance": "1", "immediate_gw": ""},
         {"dst_address": "172.18.8.112/30", "gateway": "ether5", "distance": "0", "immediate_gw": ""},
         {"dst_address": "172.19.1.0/24", "gateway": "172.18.8.113", "distance": "1", "immediate_gw": ""},
         {"dst_address": "10.20.0.0/24", "gateway": "172.18.8.113", "distance": "1", "immediate_gw": ""},
     ], "arp": []},
    {"ip": "172.18.8.113", "ok": True, "error": None, "identity": "R2-MAI(Router.Amozeshi)",
     "resource": {"version": "7.12.1 (stable)", "board": "CCR2004-1G-12S+2XS", "uptime": "30w1d", "cpu_load": "2"},
     "interfaces": mai_ifaces, "addresses": mai_addresses,
     "neighbors": [{"identity": "RB-Ghonouti", "address": "172.18.8.114", "interface": "ether3",
                    "platform": "RouterOS", "version": "7.14.3", "mac_address": "48:8F:5A:12:03:11", "uptime": "12w"}],
     "routes": [{"dst_address": "0.0.0.0/0", "gateway": "172.19.1.1", "distance": "1", "immediate_gw": ""}],
     "arp": []},
    {"ip": "172.18.1.50", "ok": False, "error": "[Errno 113] No route to host (login timeout after 12s)",
     "identity": "", "resource": {}, "interfaces": [], "addresses": [], "neighbors": [], "routes": [], "arp": []},
]
devices = [
    {"ip": "172.18.2.217", "device_name": "RB-Ghonouti", "tags": "Sites/North,Wireless-Backhaul",
     "ping_ok": True, "open_ports": [22, 80, 8291, 8728], "device_type": "Router"},
    {"ip": "172.18.8.113", "device_name": "R2-MAI", "tags": "Core",
     "ping_ok": True, "open_ports": [22, 8728], "device_type": "Router"},
    {"ip": "172.18.1.50", "device_name": "", "tags": "Site-East",
     "ping_ok": False, "open_ports": [], "device_type": ""},
]

topo = rt.build_topology(infos, devices, "172.19.1.6")
pdf = route_pdf.build_route_topology_pdf(topo, devices, central_ip="172.19.1.6",
                                         database="network_main",
                                         generated="2026-11-01 09:30 UTC")
out = "/home/z/my-project/download/نمونه-گزارش-توپولوژی-مسیر.pdf"
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "wb") as f:
    f.write(pdf)
print("written:", out, len(pdf), "bytes; pages:", len(devices))
