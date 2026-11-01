"""Visual-check helper (Task 25): build a sample route PDF that mirrors the
user's attached screenshot (22Bahman-MK -> KhezNabi-MK -> SW-Wireless1 core)
and render page JPEGs so the new readable link labels can be inspected.

Output: /tmp/render/route_label_sample.pdf (+ page-1 JPEG via pdftoppm)
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import route_topology as rt
import route_pdf as rpdf

IF = lambda n, run="true", dis="false", t="ether": [
    {"name": n, "type": t, "running": run, "disabled": dis, "mac_address": "", "comment": ""}]


def info(ip, identity, addresses, routes=(), ifaces=(), neighbors=()):
    return {"ip": ip, "ok": True, "error": None, "identity": identity,
            "resource": {"version": "6.49.19 (long-term)", "board": "RB2011UiAS", "uptime": "4h32m13s"},
            "interfaces": list(ifaces), "addresses": list(addresses),
            "neighbors": list(neighbors), "routes": list(routes), "arp": []}


infos = [
    # 22Bahman-MK — ۹ آدرس واقعی تصویر کاربر به‌صورت فشرده + MNDP به کژه‌نبی
    info("172.18.4.49", "22Bahman-MK",
         [{"address": "172.18.9.12/29", "interface": "ether10", "network": "172.18.9.8"},
          {"address": "172.18.9.177/29", "interface": "ether1", "network": "172.18.9.176"},
          {"address": "172.29.72.1/25", "interface": "bridge1", "network": "172.29.72.0"},
          {"address": "172.18.9.193/28", "interface": "ether1", "network": "172.18.9.192"},
          {"address": "172.18.9.209/29", "interface": "ether2", "network": "172.18.9.208"},
          {"address": "192.168.10.2/30", "interface": "ether1", "network": "192.168.10.0"},
          {"address": "172.18.4.49/29", "interface": "ether9", "network": "172.18.4.48"},
          {"address": "192.168.0.5/24", "interface": "bridge1", "network": "192.168.0.0"},
          {"address": "172.18.9.217/29", "interface": "ether8", "network": "172.18.9.216"}],
         routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.18.4.33", "distance": "1"}],
         ifaces=IF("ether1") + IF("ether2") + IF("ether4") + IF("ether5") + IF("ether6")
                + IF("ether9") + IF("ether10") + IF("bridge1", t="bridge")
                + IF("ether3", run="false") + IF("ether7", run="false")
                + IF("ether8", run="false") + IF("sfp1", run="false"),
         neighbors=[{"identity": "KhezNabi-MK", "address": "172.18.4.33", "interface": "ether10",
                     "platform": "MikroTik", "version": "6.49.19", "mac-address": "", "uptime": "3w"}]),
    # KhezNabi-MK — hop میانی؛ سمت سیسکو با ether24
    info("172.18.4.33", "KhezNabi-MK",
         [{"address": "172.18.4.33/29", "interface": "ether10", "network": "172.18.4.48"},
          {"address": "172.19.1.2/29", "interface": "ether24", "network": "172.19.1.0"}],
         routes=[{"dst_address": "0.0.0.0/0", "gateway": "172.19.1.6", "distance": "1"}],
         ifaces=IF("ether10") + IF("ether24")),
    # SW-Wireless1 — خود روتر مرکزی (IP مرکزی روی اینترفیسش)
    info("172.19.1.6", "SW-Wireless1",
         [{"address": "172.19.1.6/29", "interface": "ether24", "network": "172.19.1.0"}],
         ifaces=IF("ether24")),
]

devices = [{"id": i + 1, "ip": x["ip"], "device_name": x["identity"], "tags": "22",
            "ping_ok": True, "open_ports": [22, 80, 8291, 8728], "device_type": "Router"}
           for i, x in enumerate(infos)]

# کانفیگ سیسکوی مرکز — روت استاتیک به ساب‌نتِ 22Bahman از گیت‌ویِ KhezNabi
CISCO = """
hostname SW-Wireless1
interface GigabitEthernet0/0/1.200
 description LINK-TO-KHEZNABI
 encapsulation dot1Q 200
 ip address 172.19.1.6 255.255.255.248
ip route 172.18.4.48 255.255.255.248 172.19.1.2
"""
try:
    from backend import cisco_config as cc
except ImportError:
    import cisco_config as cc
cisco = cc.parse_cisco_config(CISCO)

topo = rt.build_topology(infos, devices, "172.19.1.6", cisco=cisco)
pdf = rpdf.build_route_topology_pdf(topo, devices, central_ip="172.19.1.6", database="olompz")

os.makedirs("/tmp/render", exist_ok=True)
out = "/tmp/render/route_label_sample.pdf"
with open(out, "wb") as f:
    f.write(pdf)
print("pdf written:", out, len(pdf), "bytes")
subprocess.run(["pdftoppm", "-r", "110", "-jpeg", "-jpegopt", "quality=85",
                "-f", "1", "-l", "1", out, "/tmp/render/route_label_sample"], check=True)
print("page renders:", sorted(x for x in os.listdir("/tmp/render") if x.startswith("route_label_sample")))

# گزاره‌های ساختاری: مسیر ۲ hop با برچسب شاهد
p = topo["paths"]["d:172.18.4.49"]
print("hops:", [(h["from_if"], h["to_if"], h["ev"]) for h in p["hops"]])
assert len(p["hops"]) == 2 and p["reachable"], p["hops"]
assert p["hops"][0]["ev"] == "mndp" and p["hops"][0]["from_if"] == "ether10", p["hops"]
print("STRUCTURE OK")
