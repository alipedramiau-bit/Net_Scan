"""End-to-end verification for search optimization + report database selection."""
import os, sys, sqlite3, tempfile
sys.path.insert(0, "/home/z/my-project/backend")

import db as dbm
from fastapi.testclient import TestClient
import main as appm

client = TestClient(appm.app)

# Task 4 added auth middleware: login before hitting protected endpoints.
_r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
assert _r.status_code == 200, f"login failed: {_r.status_code} {_r.text[:100]}"

# ---------- Setup: temporary test database registered in the catalog ----------
TEST_DB = "zz_search_test"
created = dbm.create_database(TEST_DB)          # registers + inits db file
path = dbm.db_path_for(TEST_DB)
print("test db path:", path)

# /devices operates on the ACTIVE database by design — switch to the test DB
# for the search tests, then restore.
prev_active = dbm.get_active_db_name()
dbm.set_active_database(TEST_DB)

conn = sqlite3.connect(path)
rows = [
    ("10.10.1.5",  "Shadegan-Jafal1", "MPLS,Core",   "Router", "ether1,ether2"),
    ("10.10.1.6",  "CL-Flat-C",       "Access",      "AP",     "wlan1"),
    ("192.168.88.1", "CRS-Darkhovein", "MPLS,Access", "Router", "ether1,sfp1"),
]
for ip, name, tags, dtype, ifaces in rows:
    conn.execute(
        """INSERT INTO devices (ip, ping_ok, open_ports, port_states, classification,
           first_seen, last_seen, seen_count, device_name, tags, device_type, interfaces)
           VALUES (?,1,'[]','{}','mikrotik_candidate',datetime('now'),datetime('now'),1,?,?,?,?)""",
        (ip, name, tags, dtype, ifaces))
conn.commit(); conn.close()

def ips(payload):
    return sorted(d["ip"] for d in payload["devices"])

ok = True
def check(label, cond, extra=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label, extra)
    ok = ok and cond

# ---------- 1) single-term search across all fields ----------
r = client.get("/devices", params={"q": "Darkhovein", "limit": 100})
check("single term finds device by name", r.status_code == 200 and ips(r.json()) == ["192.168.88.1"], r.json().get("total"))

# ---------- 2) multi-term AND search ----------
r = client.get("/devices", params={"q": "10.10.1 MPLS", "limit": 100})
# both terms must match: ip prefix 10.10.1 AND tag MPLS -> only 10.10.1.5
check("multi-term AND (ip prefix + tag)", ips(r.json()) == ["10.10.1.5"], str(ips(r.json())))

r = client.get("/devices", params={"q": "MPLS Router", "limit": 100})
check("multi-term AND (tag + type)", set(ips(r.json())) == {"10.10.1.5", "192.168.88.1"}, str(ips(r.json())))

# ---------- 3) scoped search via q_fields ----------
r = client.get("/devices", params={"q": "MPLS", "q_fields": "ip", "limit": 100})
check("scope ip: tag word NOT found in ip", ips(r.json()) == [], str(ips(r.json())))

r = client.get("/devices", params={"q_fields": "tags", "q": "access", "limit": 100})
check("scope tags: case-insensitive LIKE", set(ips(r.json())) == {"10.10.1.6", "192.168.88.1"}, str(ips(r.json())))

r = client.get("/devices", params={"q_fields": "bogus_field", "q": "MPLS", "limit": 100})
check("unknown scope falls back to all fields", r.status_code == 200 and r.json()["total"] == 2)

# ---------- 4) empty q ignores q_fields + csv export with scoped q ----------
r = client.get("/devices", params={"q_fields": "ip", "limit": 100})
check("no q -> all devices", r.status_code == 200 and r.json()["total"] == 3)

r = client.get("/devices/export.csv", params={"q": "10.10.1", "q_fields": "ip"})
check("devices csv with scoped q", r.status_code == 200 and r.text.count("\n") >= 2)

# ---------- 5) restore active database before flap-report tests ----------
dbm.set_active_database(prev_active)

# ---------- 6) flap report from the selected database ----------
r = client.get("/reports/interface-flaps", params={"days": 5, "threshold_minutes": 5, "database": TEST_DB})
check("flap report honors database param", r.status_code == 200 and r.json().get("database") == TEST_DB, r.text[:120])

r = client.get("/reports/interface-flaps", params={})
check("flap report default = active db", r.status_code == 200 and r.json().get("database") == dbm.get_active_db_name())

r = client.get("/reports/interface-flaps", params={"database": "no_such_db_xyz"})
check("unknown database -> 404", r.status_code == 404, str(r.status_code))

# ---------- 7) CSV export from selected database ----------
r = client.get("/reports/interface-flaps/export.csv", params={"database": TEST_DB, "days": 5})
check("csv export ok from selected db", r.status_code == 200 and r.text.startswith("\ufeffردیف"))

# ---------- Cleanup ----------
dbm.set_active_database(prev_active)   # ensure test DB is not active before delete
dbm.delete_database(TEST_DB)
print("\ncleanup done:", TEST_DB, "removed from catalog")
print("\n" + ("ALL TESTS PASSED ✔" if ok else "SOME TESTS FAILED ✘"))
sys.exit(0 if ok else 1)
