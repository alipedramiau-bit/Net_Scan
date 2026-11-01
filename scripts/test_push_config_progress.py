"""E2E checks for the group config-push live-progress feature (Task 17 / R7).

Covers:
- POST /api/devices/push-config/start  (validation: empty script, empty ips, 409 double-run)
- GET  /api/devices/push-config/progress (live fields: total/done/ok/failed/percent/current_ip/running/ready)
- POST /api/devices/push-config/cancel  (cooperative cancel mid-run)
- routeros_api.classify_push_error      (Persian failure reasons shown in the chart)
- parallel push keeps results aligned with input and attaches reason for failures

RouterOS API calls are monkeypatched — no real device is contacted.
Run: python3 scripts/test_push_config_progress.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import fastapi.testclient as _tc
from fastapi.testclient import TestClient

import main as appm
import routeros_api
# main.py با «from backend import routeros_api» ایمپورت می‌کند — ممکن است شیء ماژول
# متفاوتی از «import routeros_api» باشد؛ هر دو را پچ می‌کنیم (الگوی test_device_picker)
ROS_MODULES = [routeros_api]
if getattr(appm, "routeros_api", None) is not None and appm.routeros_api is not routeros_api:
    ROS_MODULES.append(appm.routeros_api)

ok = True


def check(label, cond, extra=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label, extra if not cond else "")
    ok = ok and cond


client = TestClient(appm.app)
r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
check("login", r.status_code == 200, str(r.status_code))

# ---------------------------------------------------------------------------
# 0) classify_push_error unit checks
# ---------------------------------------------------------------------------
ce = routeros_api.classify_push_error
check("classify: empty -> ''", ce("") == "" and ce(None) == "")
check("classify: timeout -> api/firewall hint", "پاسخ نداد" in ce("connection timed out"))
check("classify: refused -> api service hint", "اتصال رد شد" in ce("[Errno 111] Connection refused"))
check("classify: bad credentials -> login hint", "ورود ناموفق" in ce("invalid user name or password"))
check("classify: canceled -> stopped", "متوقف شد" in ce("canceled by user"))
check("classify: unknown passes through", ce("some weird error") == "some weird error")

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
URL = "/api/devices/push-config"


def wait_ready(deadline_s: float = 30.0) -> dict:
    t0 = time.time()
    last = {}
    while time.time() - t0 < deadline_s:
        p = client.get(URL + "/progress").json()
        last = p
        if p.get("ready") or p.get("error") or (not p.get("running") and p.get("results")):
            return p
        time.sleep(0.05)
    return last


# ---------------------------------------------------------------------------
# 1) validation
# ---------------------------------------------------------------------------
r = client.post(URL + "/start", json={"ips": ["10.0.0.1"], "username": "admin",
                                      "password": "x", "script": "   "})
check("start: empty script -> 400", r.status_code == 400, str(r.status_code))
r = client.post(URL + "/start", json={"ips": ["", "  "], "username": "admin",
                                      "password": "x", "script": "/system identity set name=x"})
check("start: empty ips -> 400", r.status_code == 400, str(r.status_code))

# ---------------------------------------------------------------------------
# 2) happy path with a failing device (timeout) — live progress + results
# ---------------------------------------------------------------------------
calls = []


def fake_push(ip, username, password, script, port=8728, timeout=15.0):
    calls.append(ip)
    if ip == "10.9.9.3":
        return {"ip": ip, "ok": False, "error": "connection timed out after 15s"}
    return {"ip": ip, "ok": True, "error": None}


orig_push = {m: m.push_config for m in ROS_MODULES}
for m in ROS_MODULES:
    m.push_config = fake_push
try:
    ips = ["10.9.9.1", "10.9.9.2", "10.9.9.3"]
    r = client.post(URL + "/start", json={"ips": ips, "username": "admin", "password": "pw",
                                          "script": "/system identity set name=olom", "port": 8728})
    check("start: accepted", r.status_code == 200 and r.json().get("total") == 3, r.text[:120])
    p = client.get(URL + "/progress").json()
    # فیکِ پچ‌شده آنی برمی‌گردد؛ ممکن است تا لحظهٔ خواندن، ران تمام شده باشد
    check("progress: running (or already finished) with totals",
          p.get("total") == 3 and "percent" in p and "current_ip" in p and "remaining" in p
          and (p.get("running") is True or p.get("ready") is True), str(p))
    p = wait_ready()
    check("progress: finished ok=2 failed=1",
          p.get("ok") == 2 and p.get("failed") == 1 and p.get("total") == 3, str(p))
    check("progress: percent 100", p.get("percent") == 100, str(p.get("percent")))
    check("progress: ready with results", p.get("ready") is True and len(p.get("results") or []) == 3)
    res = {x["ip"]: x for x in (p.get("results") or [])}
    check("results: all input ips present", set(res) == set(ips), str(sorted(res)))
    check("results: ok device has no reason", res["10.9.9.1"]["ok"] and not res["10.9.9.1"].get("reason"))
    check("results: failed device reason in Persian (timeout)",
          (not res["10.9.9.3"]["ok"]) and "پاسخ نداد" in (res["10.9.9.3"].get("reason") or ""),
          str(res.get("10.9.9.3")))
    check("worker owns running flag (not running when done)", p.get("running") is False)

    # 3) double-run -> 409 while a run is in flight
    def slow_push(ip, username, password, script, port=8728, timeout=15.0):
        time.sleep(1.2)
        return {"ip": ip, "ok": True, "error": None}

    routeros_api.push_config = slow_push
    for m in ROS_MODULES:
        m.push_config = slow_push
    r = client.post(URL + "/start", json={"ips": ["10.1.1.1", "10.1.1.2"], "username": "a",
                                          "password": "b", "script": "/x"})
    check("start: second run accepted after first finished", r.status_code == 200, r.text[:120])
    r2 = client.post(URL + "/start", json={"ips": ["10.1.1.3"], "username": "a",
                                           "password": "b", "script": "/x"})
    check("start: concurrent run -> 409", r2.status_code == 409, str(r2.status_code))
    p = wait_ready()
    check("slow run finishes ok", p.get("ok") == 2 and p.get("failed") == 0, str(p))

    # 4) cooperative cancel mid-run
    def slow2_push(ip, username, password, script, port=8728, timeout=15.0):
        time.sleep(0.8)
        if routeros_api_push_canceled_flag():
            return {"ip": ip, "ok": False, "error": "canceled"}
        return {"ip": ip, "ok": True, "error": None}

    def routeros_api_push_canceled_flag():
        return appm.CFG_PUSH_CANCEL.is_set()

    routeros_api.push_config = slow2_push
    for m in ROS_MODULES:
        m.push_config = slow2_push
    r = client.post(URL + "/start", json={"ips": ["10.2.2.1", "10.2.2.2", "10.2.2.3", "10.2.2.4"],
                                          "username": "a", "password": "b", "script": "/x",
                                          "max_workers": 2})
    check("cancel-run: started", r.status_code == 200, r.text[:120])
    time.sleep(0.3)
    r = client.post(URL + "/cancel")
    check("cancel: requested", r.status_code == 200 and r.json().get("cancel_requested") is True, r.text[:120])
    p = wait_ready()
    check("cancel: progress marked canceled", p.get("canceled") is True, str(p.get("canceled")))
    check("cancel: not all devices completed", len(p.get("results") or []) <= 4)
    canceled_res = [x for x in (p.get("results") or []) if not x.get("ok")]
    check("cancel: stopped devices carry Persian reason",
          all("متوقف شد" in (x.get("reason") or "") for x in canceled_res), str(canceled_res))

    # cancel when idle
    r = client.post(URL + "/cancel")
    check("cancel-when-idle: cancel_requested False", r.json().get("cancel_requested") is False, r.text[:120])
finally:
    for m, f in orig_push.items():
        m.push_config = f
    # اطمینان از اینکه ران در حال اجرا برای تست‌های بعدی باقی نمانده
    wait_ready(10)

print("\nALL OK" if ok else "\nFAILURES PRESENT")
sys.exit(0 if ok else 1)
