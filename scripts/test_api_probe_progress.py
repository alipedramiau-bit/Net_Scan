"""End-to-end verification: API probe review (parallel + segmented progress).

Covers:
- probe_devices_via_api_many runs concurrently (wall time << sequential)
- progress dict tracks total/done/ok/failed/current_ip/running
- results keep input order; failed probes reported per-device
- GET /api/devices/probe-api/progress exposes ok/failed/remaining
- cancel skips remaining devices (partial results, canceled=True)
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import routeros_api
import main as appm
from fastapi.testclient import TestClient

ok = True
def check(label, cond, extra=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label, extra)
    ok = ok and cond

# ---------- 1) parallel run with live ok/failed progress ----------
# 4 unreachable hosts (non-routable) with 3s timeout: sequential would be ~12s,
# 4 workers should finish in well under 9s.
IPS = ["10.255.255.1", "10.255.255.2", "10.255.255.3", "10.255.255.4"]
progress = appm.API_PROBE_PROGRESS  # the module-level dict the endpoint exposes
t0 = time.monotonic()
results = routeros_api.probe_devices_via_api_many(
    IPS, username="admin", password="", port=8728, timeout=3.0,
    progress=progress, max_workers=4,
)
elapsed = time.monotonic() - t0
check("4 probes finished", len(results) == 4, f"{elapsed:.1f}s")
check("input order preserved", [r["ip"] for r in results] == IPS, str([r["ip"] for r in results]))
check("all reported failed (unreachable)", all(not r["ok"] for r in results))
check("progress total", progress.get("total") == 4, str(progress))
check("progress done==4", progress.get("done") == 4, str(progress))
check("progress ok==0", progress.get("ok") == 0, str(progress))
check("progress failed==4", progress.get("failed") == 4, str(progress))
check("progress stopped (running=False)", progress.get("running") is False)
check("current_ip cleared", progress.get("current_ip") == "")
check("parallel wall time < sequential/1.5", elapsed < 12 * 4 / 4 / 1.5, f"{elapsed:.2f}s")

# ---------- 2) progress endpoint shape ----------
client = TestClient(appm.app)
_r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
assert _r.status_code == 200, f"login failed: {_r.status_code}"
r = client.get("/api/devices/probe-api/progress")
d = r.json()
check("progress endpoint 200", r.status_code == 200)
for field in ("total", "done", "percent", "ok", "failed", "remaining", "current_ip", "running", "canceled"):
    check(f"progress field '{field}' present", field in d, str(d))
check("progress endpoint reflects last run", d.get("total") == 4 and d.get("failed") == 4, str(d))

# ---------- 3) cancel: pre-canceled event skips all devices ----------
from threading import Event
cancel = Event(); cancel.set()
prog2 = {}
res2 = routeros_api.probe_devices_via_api_many(
    IPS, username="admin", password="", port=8728, timeout=3.0,
    cancel_event=cancel, progress=prog2, max_workers=4,
)
check("pre-canceled -> no results", res2 == [], str(res2))
check("pre-canceled -> canceled=True", prog2.get("canceled") is True, str(prog2))
check("pre-canceled -> done==0", prog2.get("done") == 0, str(prog2))
check("pre-canceled -> running=False", prog2.get("running") is False, str(prog2))

# ---------- 4) empty list edge ----------
prog3 = {}
res3 = routeros_api.probe_devices_via_api_many([], username="admin", progress=prog3)
check("empty ips -> []", res3 == [])
check("empty ips -> running=False", prog3.get("running") is False, str(prog3))

print("\n" + ("ALL TESTS PASSED ✔" if ok else "SOME TESTS FAILED ✘"))
sys.exit(0 if ok else 1)
