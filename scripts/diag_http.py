"""End-to-end test: start backend, login, call smart-report endpoint over HTTP."""
import sys, os, json, threading, time, urllib.request
sys.path.insert(0, "/home/z/my-project/backend")
os.chdir("/home/z/my-project")

import uvicorn
from main import app

config = uvicorn.Config(app, host="127.0.0.1", port=5777, log_level="error")
server = uvicorn.Server(config)
thread = threading.Thread(target=server.run, daemon=True)
thread.start()
for _ in range(60):
    time.sleep(0.3)
    if server.started:
        break
print("server started:", server.started)

BASE = "http://127.0.0.1:5777"
import http.cookiejar
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1) unauthenticated -> expect 401
import urllib.error
try:
    opener2 = urllib.request.build_opener()
    opener2.open(BASE + "/reports/interface-flaps?days=5&threshold_minutes=5", timeout=30)
    print("UNAUTH: unexpectedly 200")
except urllib.error.HTTPError as e:
    print("UNAUTH status:", e.code)

# 2) login
req = urllib.request.Request(BASE + "/api/login", method="POST",
                             data=json.dumps({"username": "admin", "password": "NetAdmin"}).encode(),
                             headers={"Content-Type": "application/json"})
resp = opener.open(req, timeout=30)
print("login:", resp.status, json.loads(resp.read()))

# 3) report without database param (active DB)
resp = opener.open(BASE + "/reports/interface-flaps?days=5&threshold_minutes=5", timeout=300)
data = json.loads(resp.read())
print("REPORT(active):", resp.status, "| events:", data.get("event_count"),
      "| devices:", data.get("device_count"), "| database:", data.get("database"))

# 4) report with database=default
resp = opener.open(BASE + "/reports/interface-flaps?days=5&threshold_minutes=5&database=default", timeout=300)
data = json.loads(resp.read())
print("REPORT(default):", resp.status, "| events:", data.get("event_count"),
      "| devices:", data.get("device_count"), "| database:", data.get("database"))

# 5) databases endpoint (fills the UI dropdown)
resp = opener.open(BASE + "/api/databases", timeout=60)
d = json.loads(resp.read())
print("DATABASES:", resp.status, [(x["name"], x["devices"], x["active"]) for x in d["databases"]])

# 6) CSV export
resp = opener.open(BASE + "/reports/interface-flaps/export.csv?days=5&threshold_minutes=5&database=default", timeout=300)
body = resp.read().decode("utf-8-sig")
lines = body.strip().splitlines()
print("CSV:", resp.status, "| lines:", len(lines), "| header ok:", lines[0].split(",")[0] == "ردیف")

server.should_exit = True
