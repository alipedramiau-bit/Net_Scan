"""Diagnose smart-report flap detection against the real database."""
import sys, os
sys.path.insert(0, "/home/z/my-project/backend")
os.chdir("/home/z/my-project")

import db
from datetime import datetime

print("active db:", db.get_active_db_name())
print("catalog:", db.list_databases()["databases"])

res = db.query_devices(limit=100000, db_path=str(db.db_path_for("default")))
devices = res["devices"]
print("devices returned:", len(devices))

with_log = [d for d in devices if (d.get("device_log") or "").strip()]
print("devices with non-empty device_log:", len(with_log))

if with_log:
    sample = with_log[0]
    lines = [l for l in sample["device_log"].splitlines() if l.strip()]
    print("sample device:", sample["ip"], "| log lines:", len(lines))
    for l in lines[:8]:
        print("   ", repr(l[:120]))
    # newest parseable stamp across all logs
    import smart_reports as sr
    newest = None
    total_link_events = 0
    for d in with_log:
        for line in d["device_log"].splitlines():
            m = sr._LINE.match(line)
            if not m:
                continue
            ev = sr._LINK_EVENT.match(m.group("message"))
            if not ev:
                continue
            total_link_events += 1
            try:
                when = sr.parse_log_datetime(m.group("stamp"), reference=datetime.now())
            except Exception:
                continue
            if newest is None or when > newest:
                newest = when
    print("total link events matched:", total_link_events)
    print("newest parsed event time:", newest)

rep = sr.interface_flap_report(devices, days_back=5, threshold_minutes=5)
print("report events:", rep["event_count"], "| devices:", rep["device_count"])
