"""Regression test: ip_info dir resolution must accept filesystem paths.

Root cause of "smart report stopped working" on the user's Windows machine:
query_devices(db_path=<full path>) -> enrich_devices_from_ip_info ->
_ip_info_dir -> db_path_for(<full path>) -> _safe_db_name(<full path>)
raised ValueError when the sanitized path exceeded 64 chars (long Windows
paths). The exception was silently swallowed before Task 6 -> empty report.

Run:  python scripts/test_ip_info_path_fix.py
"""
import sys, os, sqlite3, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
import db

PASS = FAIL = 0
def check(name, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  PASS  {name}")
    else: FAIL += 1; print(f"  FAIL  {name}  {extra}")

ROOT = Path.cwd()
DB_DIR = ROOT / "databases"

# ---------- 1) _ip_info_dir accepts long filesystem paths ----------
long_dir = ROOT / "tmp_long_path_test" / "a_very_long_project_folder_name_deep_net_scan_deployment_2026" / "databases"
long_db = long_dir / "default.db"
long_dir.mkdir(parents=True, exist_ok=True)
check("sanitized path would exceed 64 chars (reproduces the bug)",
      len("".join(c if c.isalnum() else "_" for c in str(long_db)).strip("_")) > 64, str(long_db))

d = db._ip_info_dir(str(long_db))
check("long str path -> sibling ip_info dir", d == long_dir / "ip_info", str(d))
d = db._ip_info_dir(long_db)
check("Path object -> sibling ip_info dir", d == long_dir / "ip_info", str(d))
d = db._ip_info_dir("C:\\Users\\Ali\\Documents\\Net_Scan\\databases\\default.db")
# On Linux a backslash string parses as ONE component ending in .db -> path branch,
# parent resolves to "."; on real Windows Path() splits it natively and the parent
# is the DB folder. Either way: no exception, and an ip_info dir comes back.
check("windows-style path handled (no raise, ip_info dir)", d.name == "ip_info", str(d))

# ---------- 2) _ip_info_dir still accepts database NAMES ----------
d = db._ip_info_dir("default")
check("name 'default' -> databases/ip_info", d == DB_DIR / "ip_info", str(d))
d = db._ip_info_dir()
check("None -> active db ip_info", d == DB_DIR / "ip_info", str(d))

# ---------- 3) end-to-end: query_devices with long path + ip_info enrichment ----------
ip_info_dir = long_dir / "ip_info"
ip_info_dir.mkdir(exist_ok=True)
(ip_info_dir / "10.99.0.9.txt").write_text(
    "IP: 10.99.0.9\nCollected at: 2026-10-23T08:00:00+00:00\nsource: RouterOS API\n"
    "identity: LongPathCore\ndevice_type: Router\n\n"
    "----- log -----\n"
    "  1  2026/10/23 08:00:00  ether5 link up\n"
    "  2  2026/10/23 08:01:00  ether5 link down\n", encoding="utf-8")
conn = sqlite3.connect(str(long_db))
conn.executescript("""
CREATE TABLE IF NOT EXISTS devices (
  ip TEXT PRIMARY KEY, ping_ok INTEGER, open_ports TEXT, port_states TEXT,
  classification TEXT, first_seen TEXT, last_seen TEXT, seen_count INTEGER,
  device_name TEXT DEFAULT '', tags TEXT DEFAULT '', ip_addresses TEXT DEFAULT '',
  ip_neighbors TEXT DEFAULT '', interfaces TEXT DEFAULT '', device_type TEXT DEFAULT '',
  wireless_info TEXT DEFAULT '', device_log TEXT DEFAULT '', mac_info TEXT DEFAULT '');
INSERT OR REPLACE INTO devices (ip, ping_ok, open_ports, port_states, classification,
  first_seen, last_seen, seen_count, device_name, tags)
VALUES ('10.99.0.9', 1, '[]', '{}', 'mikrotik_candidate', '2026-10-01', '2026-10-23', 5, '', '');
""")
conn.commit(); conn.close()

res = db.query_devices(limit=10, db_path=str(long_db))
devs = res.get("devices", [])
check("query_devices with long path returns device", len(devs) == 1, str(res)[:120])
check("ip_info enrichment applied (device_log filled)",
      "ether5 link down" in (devs[0].get("device_log") or ""), repr(devs[0].get("device_log"))[:120])
check("ip_info enrichment applied (device_name filled)",
      devs[0].get("device_name") == "LongPathCore", devs[0].get("device_name"))

# ---------- 4) flap report on the long-path data ----------
import smart_reports as sr
from datetime import datetime
rep = sr.interface_flap_report(devs, days_back=5, threshold_minutes=5)
check("flap report finds events via long path data", rep["event_count"] == 1, str(rep["event_count"]))
check("report carries diagnostics", rep.get("devices_scanned") == 1 and rep.get("devices_with_logs") == 1)

# ---------- 5) real DB still works through the endpoint function ----------
rep2 = sr.interface_flap_report(db.query_devices(limit=100000, db_path=str(db.db_path_for("default")))["devices"],
                                days_back=5, threshold_minutes=5)
check("real default.db report still has events", rep2["event_count"] > 0, str(rep2["event_count"]))

# ---------- cleanup ----------
import shutil
shutil.rmtree(ROOT / "tmp_long_path_test", ignore_errors=True)
print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
