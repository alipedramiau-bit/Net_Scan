"""End-to-end verification of the admin login / session-cookie auth flow."""
import sys
sys.path.insert(0, "/home/z/my-project/backend")

from fastapi.testclient import TestClient
import main as appm
import auth as authm

ok = True
def check(label, cond, extra=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label, extra)
    ok = ok and cond

fresh = TestClient(appm.app)   # no cookies -> unauthenticated browser
authed = TestClient(appm.app)  # will hold the session cookie

# ---------- 1) protected routes reject anonymous access ----------
for path in ("/api/databases", "/devices", "/reports/interface-flaps", "/scans"):
    r = fresh.get(path)
    check(f"anonymous GET {path} -> 401", r.status_code == 401, str(r.status_code))

r = fresh.post("/api/databases", json={"name": "x"})
check("anonymous POST protected -> 401", r.status_code == 401)

# ---------- 2) login validation ----------
r = fresh.post("/api/login", json={"username": "admin", "password": "wrong"})
check("wrong password -> 401", r.status_code == 401)

r = fresh.post("/api/login", json={"username": "NetAdmin", "password": "NetAdmin"})
check("legacy NetAdmin username rejected -> 401", r.status_code == 401)

r = authed.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
set_cookie = r.headers.get("set-cookie", "")
check("correct credentials (admin/NetAdmin) -> 200", r.status_code == 200 and r.json().get("username") == "admin", r.text[:80])
check("session cookie set (HttpOnly)", authm.COOKIE_NAME in set_cookie and "httponly" in set_cookie.lower())

# ---------- 3) authenticated access works ----------
r = authed.get("/api/auth/check")
check("auth/check with cookie -> 200", r.status_code == 200 and r.json().get("authenticated") is True)

r = authed.get("/api/databases")
check("API call with cookie -> 200", r.status_code == 200)

r = authed.get("/devices?limit=5")
check("devices with cookie -> 200", r.status_code == 200)

r = authed.get("/reports/interface-flaps?days=5")
check("flap report with cookie -> 200", r.status_code == 200)

# ---------- 4) open routes stay open ----------
r = fresh.get("/")
check("SPA shell open without auth", r.status_code == 200 and "root" in r.text)

r = fresh.get("/api/auth/check")
check("auth/check reachable anonymously (401, not 403/404)", r.status_code == 401)

r = fresh.options("/api/databases", headers={
    "Origin": "http://185.110.29.189:5001",
    "Access-Control-Request-Method": "GET",
    "Access-Control-Request-Headers": "content-type",
})
check("CORS preflight passes through auth", r.status_code in (200, 204), str(r.status_code))
check("preflight answer allows origin+credentials",
      r.headers.get("access-control-allow-origin") == "http://185.110.29.189:5001"
      and r.headers.get("access-control-allow-credentials") == "true")

r = fresh.get("/health")
check("health stays open", r.status_code == 200)

# ---------- 5) token internals ----------
tok = authm.create_token("NetAdmin")
check("token verifies", authm.verify_token(tok) == "NetAdmin")
check("tampered token rejected", authm.verify_token(tok[:-4] + "aaaa") is None)
check("garbage token rejected", authm.verify_token("abc") is None)
import base64, json as _json
payload = _json.loads(base64.urlsafe_b64decode(tok.split(".")[0] + "=="))
payload["exp"] = payload["exp"] - 86400 * 30
b64 = base64.urlsafe_b64encode(_json.dumps(payload).encode()).decode().rstrip("=")
check("expired token rejected", authm.verify_token(f"{b64}.{tok.split('.')[1]}") is None)

# ---------- 6) logout clears the session ----------
r = authed.post("/api/logout")
check("logout -> 200", r.status_code == 200)
r = authed.get("/api/auth/check")
check("after logout auth/check -> 401", r.status_code == 401)

print("\n" + ("ALL TESTS PASSED ✔" if ok else "SOME TESTS FAILED ✘"))
sys.exit(0 if ok else 1)
