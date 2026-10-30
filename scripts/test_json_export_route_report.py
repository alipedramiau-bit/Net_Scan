"""End-to-end verification: POST /devices/export-mikrotik.json + POST /devices/route-report.csv

Feature 1 (JSON export): alongside the MikroTik CSV export, the same selected
MikroTik devices (same 19 Persian fields, same live auto-read flow) can be
exported as a JSON file (devices array + metadata).

Feature 2 (route report / گزارش روت): the command `tracert -d <ip_device>` is
run for every MikroTik device matching the report's search filter; source and
destination IPs are asked from the user (defaults 172.19.1.6) and the output
is a CSV (7 Persian columns). On Linux the backend uses `traceroute -n`
(the equivalent of Windows `tracert -d`). Trace targets that are not
routable in the test sandbox are avoided — 127.0.0.1 is used as the device
IP so every trace resolves in a single instant hop.

Also unit-checks route_report.parse_trace_output against real Windows
tracert -d and Linux traceroute -n / tracepath samples.
"""
import os, sys, sqlite3, csv as _csv, io as _io, json as _json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import db as dbm
import route_report as rr
from fastapi.testclient import TestClient
import main as appm

ok = True
def check(label, cond, extra=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label, extra)
    ok = ok and cond

# ---------- 0) unit: output parsers (no network) ----------
WIN = """Tracing route to 10.20.0.2 over a maximum of 15 hops

  1     1 ms     1 ms     1 ms  192.168.88.1
  2     *        *        *     Request timed out.
  3    12 ms    11 ms    13 ms  10.20.0.2

Trace complete."""
LINUX = """traceroute to 10.20.0.2 (10.20.0.2), 15 hops max, 60 byte packets
 1  192.168.88.1  1.234 ms
 2  * * *
 3  10.20.0.2  12.1 ms"""
TPATH = """ 1:  gateway (192.168.88.1) 1.234ms
 2:  10.20.0.2  12.1ms reached"""
h = rr.parse_trace_output(WIN)
check("win: hop1 ip/latency/status", h[0]["ip"] == "192.168.88.1" and h[0]["latency_ms"] == "1" and h[0]["status"] == "پاسخ داد", str(h[0]))
check("win: hop2 timeout", h[1]["ip"] == "*" and h[1]["status"] == "بدون پاسخ (timeout)", str(h[1]))
check("win: hop3 destination", h[2]["ip"] == "10.20.0.2" and h[2]["latency_ms"] == "12")
h = rr.parse_trace_output(LINUX)
check("linux: hop1", h[0]["ip"] == "192.168.88.1" and h[0]["latency_ms"] == "1.234")
check("linux: 3 hops parsed", len(h) == 3, str(len(h)))
h = rr.parse_trace_output(TPATH)
check("tracepath: reached row", h[-1]["ip"] == "10.20.0.2" and h[-1]["status"] == "پاسخ داد", str(h[-1]))
# error row in CSV builder
b = rr.build_route_report_csv([{"ip": "10.0.0.9", "device_name": "X", "trace": {"ok": False, "error": "ابزار یافت نشد"}}],
                              source_ip="172.19.1.6", dest_ip="172.19.1.6")
check("csv builder: error row", "خطا: ابزار یافت نشد" in b.decode("utf-8-sig"))
# trace_many order + dedupe
many = rr.trace_many(["127.0.0.1", "127.0.0.1"])
check("trace_many dedupes", len(many) == 1 and many[0]["ip"] == "127.0.0.1")
check("trace_many ok", many[0]["trace"]["ok"], many[0]["trace"].get("error", ""))

# ---------- 1) HTTP setup ----------
client = TestClient(appm.app)
_r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
assert _r.status_code == 200, f"login failed: {_r.status_code} {_r.text[:100]}"

TEST_DB = "zz_rt_json_test"
created = dbm.create_database(TEST_DB)
path = dbm.db_path_for(TEST_DB)
print("test db path:", path)
import pathlib
for _p in (path.parent / "ip_info").glob("10.20.0.*.txt"):
    _p.unlink()
for _p in (path.parent / "ip_info").glob("127.0.0.1.txt"):
    _p.unlink()

prev_active = dbm.get_active_db_name()
dbm.set_active_database(TEST_DB)

conn = sqlite3.connect(path)
rows = [
    # ip, name, tags, dtype, interfaces, ip_addr, neighbors, wireless, log, mac, classification, ports
    ("10.20.0.1", "Core-RTR1", "MPLS,Core", "Router", "ether1,ether2,sfp1",
     "10.20.0.1/24,192.168.10.1/24", "NB-10.20.0.2 ether2", "wlan1: bridge/ap bridge",
     "log line A\nlog line B", "AA:BB:CC:DD:EE:01", "mikrotik_candidate", "[8291, 8728]"),
    ("10.20.0.2", "AP-Site2", "Access", "AP", "wlan1,ether3",
     "10.20.0.2/24", "", "wlan1: station ssid=NET2",
     "log C", "AA:BB:CC:DD:EE:02", "mikrotik_candidate", "[8291]"),
    ("10.20.0.3", "SW-L2", "", "", "", "", "", "", "", "", "mikrotik_candidate", "[8728]"),
    ("10.20.0.9", "Printer-HP", "", "", "", "", "", "", "", "", "non_mikrotik", "[]"),
    ("127.0.0.1", "Loopback-RTR", "", "Router", "lo,ether1", "127.0.0.1/8", "", "", "", "",
     "mikrotik_candidate", "[8291, 8728]"),
]
for (ip, name, tags, dtype, ifaces, ipaddr, nb, wl, log, mac, cls, ports) in rows:
    conn.execute(
        """INSERT INTO devices (ip, ping_ok, open_ports, port_states, classification,
           first_seen, last_seen, seen_count, device_name, tags, device_type, interfaces,
           ip_addresses, ip_neighbors, wireless_info, device_log, mac_info)
           VALUES (?,1,?,'{"8291":"","8728":""}',?,datetime('now'),datetime('now'),2,?,?,?,?,?,?,?,?,?)""",
        (ip, ports, cls, name, tags, dtype, ifaces, ipaddr, nb, wl, log, mac))
conn.commit(); conn.close()

ALL_IPS = ["10.20.0.1", "10.20.0.2", "10.20.0.3", "10.20.0.9"]

# ---------- 2) JSON export happy path ----------
r = client.post("/devices/export-mikrotik.json", json={"ips": ALL_IPS})
check("json: mixed selection -> 200", r.status_code == 200, str(r.status_code))
check("json: media type", "application/json" in r.headers.get("content-type", ""))
cd = r.headers.get("content-disposition", "")
check("json: attachment filename", "mikrotik_selected_" in cd and ".json" in cd, cd)
payload = r.json()
check("json: metadata keys", all(k in payload for k in ("exported_at", "database", "count", "fields", "devices")))
check("json: count == 3", payload.get("count") == 3, str(payload.get("count")))
check("json: non-mikrotik excluded", all(d["IP"] != "10.20.0.9" for d in payload.get("devices", [])))
check("json: fields == 19 Persian headers", payload.get("fields") == dbm.MIKROTIK_EXPORT_FIELDS)
d0 = payload["devices"][0]
check("json: row0 ip+identity", d0["IP"] == "10.20.0.1" and d0["نام دستگاه (identity)"] == "Core-RTR1", d0["IP"])
check("json: interfaces value", d0["اینترفیس‌ها"] == "ether1,ether2,sfp1")
check("json: ip addresses value", d0["آدرس‌های IP"] == "10.20.0.1/24,192.168.10.1/24")
check("json: log value multiline", "log line A" in d0["لاگ دستگاه"] and "log line B" in d0["لاگ دستگاه"])
check("json: mac value", d0["اطلاعات MAC"] == "AA:BB:CC:DD:EE:01")
check("json: wireless value", d0["وایرلس"] == "wlan1: bridge/ap bridge")
check("json: read status کامل", d0["وضعیت خواندن"] == "کامل")
d2 = [x for x in payload["devices"] if x["IP"] == "10.20.0.3"][0]
check("json: read status ناقص", d2["وضعیت خواندن"].startswith("ناقص"))
check("json: rows keyed exactly by fields", set(d0.keys()) == set(dbm.MIKROTIK_EXPORT_FIELDS))

# read_missing=True with all-complete devices must NOT touch the network
r = client.post("/devices/export-mikrotik.json",
                json={"ips": ["10.20.0.1", "10.20.0.2"], "read_missing": True})
check("json: read_missing complete -> no probe", r.status_code == 200 and r.headers.get("X-Export-Read-Now") == "0",
      f"{r.status_code} read_now={r.headers.get('X-Export-Read-Now')}")

# 400 paths
r = client.post("/devices/export-mikrotik.json", json={"ips": []})
check("json: empty ips -> 400", r.status_code == 400, str(r.status_code))
r = client.post("/devices/export-mikrotik.json", json={"ips": ["10.20.0.9"]})
check("json: only non-mikrotik -> 400", r.status_code == 400, str(r.status_code))

# ---------- 3) route report ----------
RT_IPS = ["127.0.0.1", "10.20.0.9"]
r = client.post("/devices/route-report.csv", json={"ips": RT_IPS})
check("route: 200", r.status_code == 200, str(r.status_code))
check("route: BOM", r.content[:3] == b"\xef\xbb\xbf")
cd = r.headers.get("content-disposition", "")
check("route: attachment filename", "route_report_" in cd and ".csv" in cd, cd)
check("route: X-Route-Devices == 1", r.headers.get("X-Route-Devices") == "1", r.headers.get("X-Route-Devices", ""))
text = r.content.decode("utf-8-sig")
rrows = list(_csv.reader(_io.StringIO(text)))
header, rows_ = rrows[0], [x for x in rrows[1:] if x]
check("route: 7 Persian columns", header == rr.CSV_HEADERS, str(header))
check("route: has rows", len(rows_) > 0, str(len(rows_)))
check("route: no base route when src==dst (defaults)", all(x[2] != rr.BASE_ROUTE_LABEL for x in rows_))
check("route: source column default 172.19.1.6", all(x[0] == "172.19.1.6" for x in rows_))
check("route: dest column is device ip", all(x[1] == "127.0.0.1" for x in rows_))
check("route: destination hop present", any(x[4] == "127.0.0.1" for x in rows_), str(rows_[:3]))
check("route: hop status non-empty", all(x[6] for x in rows_))

# base route when مبدأ != مقصد
r = client.post("/devices/route-report.csv",
                json={"ips": ["127.0.0.1"], "source_ip": "172.19.1.6", "dest_ip": "127.0.0.1"})
check("route: custom src/dst -> 200", r.status_code == 200, str(r.status_code))
text = r.content.decode("utf-8-sig")
rrows = list(_csv.reader(_io.StringIO(text)))
rows_ = [x for x in rrows[1:] if x]
base_rows = [x for x in rows_ if x[2] == rr.BASE_ROUTE_LABEL]
check("route: base route block present", len(base_rows) > 0)
check("route: base route dest column", all(x[1] == "127.0.0.1" for x in base_rows))

# 400 paths
r = client.post("/devices/route-report.csv", json={"ips": []})
check("route: empty ips -> 400", r.status_code == 400, str(r.status_code))
r = client.post("/devices/route-report.csv", json={"ips": ["10.20.0.9"]})
check("route: only non-mikrotik -> 400", r.status_code == 400, str(r.status_code))

# ---------- cleanup ----------
dbm.set_active_database(prev_active)
dbm.delete_database(TEST_DB)

print()
print("ALL PASS" if ok else "SOME CHECKS FAILED")
sys.exit(0 if ok else 1)
