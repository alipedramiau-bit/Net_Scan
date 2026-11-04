"""Task 37 — بررسی «گزینهٔ ثبت لاگ خطا» در برگهٔ راهبری سیستم + رفع خطای پشتیبان rsc.

بررسی‌ها:
1) سورس frontend/src.jsx: کامپوننت ErrorLogCard (کلیک فعال/خاموش، نمایش/فیلتر/پاک‌کردن)،
   memo شده، فقط در برگهٔ «راهبری سیستم» رندر می‌شود، endpointهای /api/errorlog؛
2) باندل dist: index.html → باندل موجود، رشته‌های شاخص فارسی لاگ خطا + CSS کارت؛
3) بک‌اند: endpointهای GET /api/errorlog و toggle/clear با TestClient (جریان کامل:
   ثبت دو رویداد → تازه‌ترین اول → خاموش‌کردن ثبت → پاک‌کردن)؛
4) سورس بک‌اند: روش فایل در export (فراخوانی /export =file= و خواندن contents)،
   تلاش دوبارهٔ ورود روی اتصال تازه در login، و اتصال خطاهای backup-rsc/probe-api
   به ماژول errorlog.
"""
import os, re, sys, tempfile
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "backend"))

ok = True
def check(label, cond, extra=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label, extra)
    ok = ok and cond

# ---------- 1) سورس فرانت ----------
src = open(os.path.join(ROOT, "frontend", "src.jsx"), encoding="utf-8").read()
check("src: ErrorLogCard تعریف شده", "function ErrorLogCard(" in src)
check("src: ErrorLogCard با React.memo بسته شده", "ErrorLogCardM=React.memo(ErrorLogCard)" in src)
check("src: کارت فقط در برگهٔ راهبری سیستم رندر می‌شود",
      src.count("<ErrorLogCardM") == 1 and re.search(r'mainTab==="system".{0,220}<ErrorLogCardM', src, re.S) is not None)
check("src: کلید فعال/خاموش ثبت لاگ", "ثبت لاگ خطا فعال باشد" in src and "/api/errorlog/toggle" in src)
check("src: دکمهٔ پاک‌کردن با تأیید", "/api/errorlog/clear" in src and "پاک شوند" in src)
check("src: نمایش/فیلتر/به‌روزرسانی", "/api/errorlog?limit=200" in src and "errorlog-filter" in src)
check("src: توضیح پوشهٔ mik_log در کارت", "mik_log/" in src)
check("src: ستون‌های زمان/منبع/دستگاه/علت", "لاگ خطاها" in src and "علت خطا" in src and "منبع" in src)

# ---------- 2) باندل dist ----------
DIST = os.path.join(ROOT, "frontend", "dist")
js_files = [f for f in os.listdir(os.path.join(DIST, "assets")) if f.endswith(".js")]
css_files = [f for f in os.listdir(os.path.join(DIST, "assets")) if f.endswith(".css")]
check("dist: یک js + یک css", len(js_files) == 1 and len(css_files) == 1, str(js_files))
html = open(os.path.join(DIST, "index.html"), encoding="utf-8").read()
m = re.search(r"assets/(index-[A-Za-z0-9_-]+\.js)", html)
check("dist: index.html به باندل موجود اشاره می‌کند",
      m is not None and m.group(1) in js_files, m.group(1) if m else "—")
js = open(os.path.join(DIST, "assets", js_files[0]), encoding="utf-8").read()
css = open(os.path.join(DIST, "assets", css_files[0]), encoding="utf-8").read()
check("bundle: endpointهای errorlog", "/api/errorlog" in js and "/api/errorlog/toggle" in js and "/api/errorlog/clear" in js)
check("bundle: متن‌های فارسی کارت", "لاگ خطاها" in js and "ثبت لاگ خطا فعال باشد" in js and "رویداد" in js)
check("bundle: فیلتر لاگ", "فیلتر: IP، منبع یا علت" in js)
check("css: استایل کارت لاگ", ".errorlog-card{" in css and ".errorlog-table{" in css and ".errorlog-toggle{" in css)

# ---------- 3) endpointهای بک‌اند ----------
from fastapi.testclient import TestClient
import main as appm
elog = appm.errorlog  # همان ماژولی که endpointها استفاده می‌کنند

client = TestClient(appm.app)
_r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
assert _r.status_code == 200, f"login failed: {_r.status_code}"

tmp = tempfile.mkdtemp(prefix="miklog_test_")
_old_log, _old_cfg = elog.LOG_FILE, elog.CONFIG_FILE
try:
    elog.LOG_FILE = Path(tmp) / "errorlog.jsonl"
    elog.CONFIG_FILE = Path(tmp) / "config.json"

    r = client.get("/api/errorlog")
    check("endpoint: GET /api/errorlog -> 200", r.status_code == 200, r.text[:120])
    d = r.json()
    check("endpoint: شکل پاسخ (enabled/count/entries/folder)",
          isinstance(d.get("enabled"), bool) and isinstance(d.get("entries"), list)
          and "count" in d and "mik_log" in d.get("folder", ""))

    elog.log_error(source="backup-rsc", ip="172.17.12.34", message="ورود API ناموفق (6) — تست")
    elog.log_error(source="probe-api", ip="172.18.1.106", message="export خالی بود — تست")
    d = client.get("/api/errorlog").json()
    check("endpoint: دو رویداد ثبت شد", d["count"] == 2, str(d["count"]))
    check("endpoint: تازه‌ترین اول", d["entries"][0]["ip"] == "172.18.1.106")
    check("endpoint: فیلتر منبع", len(client.get("/api/errorlog?source=probe-api").json()["entries"]) == 1)

    r = client.post("/api/errorlog/toggle", json={"enabled": False})
    check("endpoint: toggle -> خاموش", r.status_code == 200 and r.json()["enabled"] is False)
    check("endpoint: ثبتِ خاموش لاگ نمی‌نویسد", elog.log_error(source="backup-rsc", ip="1.2.3.4", message="x") is None
          and client.get("/api/errorlog").json()["count"] == 2)
    client.post("/api/errorlog/toggle", json={"enabled": True})
    check("endpoint: toggle -> روشن", elog.is_enabled() is True)

    r = client.post("/api/errorlog/clear")
    check("endpoint: clear -> 200 و خالی", r.status_code == 200 and client.get("/api/errorlog").json()["count"] == 0)
finally:
    elog.LOG_FILE, elog.CONFIG_FILE = _old_log, _old_cfg

# ---------- 4) سورس بک‌اند: رفع خطا ----------
br = open(os.path.join(ROOT, "backend", "backup_rsc.py"), encoding="utf-8").read()
ra = open(os.path.join(ROOT, "backend", "routeros_api.py"), encoding="utf-8").read()
mn = open(os.path.join(ROOT, "backend", "main.py"), encoding="utf-8").read()
check("backend: روش فایل export پیاده شده", "_export_via_file" in br and "=file={" in br and "=.proplist=contents" in br)
check("backend: پول اندازهٔ فایل تا ثبات", "_FILE_POLL_TRIES" in br and "stable >= 2" in br)
check("backend: حذف فایل موقت روی دستگاه", "/file/remove" in br)
check("backend: پیام مجوز write برای export=file", "read,write,api" in br)
check("backend: تلاش چالش-پاسخ روی اتصال تازه در login",
      "first_err = _trap_message(traps[0])" in ra and re.search(r"def login.{0,1500}self\.close\(\).{0,80}self\.connect\(\)", ra, re.S) is not None)
check("backend: خطاهای backup-rsc به errorlog وصل شده", '_errorlog.log_error(source="backup-rsc"' in br)
check("backend: خطاهای probe-api به errorlog وصل شده", 'errorlog.log_error(source="probe-api"' in mn)
check("backend: سه endpoint لاگ خطا", mn.count('"/api/errorlog') >= 3)

print("\nALL OK" if ok else "\nFAILURES PRESENT")
sys.exit(0 if ok else 1)
