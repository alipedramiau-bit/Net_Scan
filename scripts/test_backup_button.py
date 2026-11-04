"""Task 34/36 — بررسی باندل dist برای جعبهٔ جستجوی جدید و دکمهٔ پشتیبان‌گیری rsc.

بررسی‌ها:
1) باندل JS شامل: کلاس main-search-bar / main-search-input، دکمهٔ
   btn-backup-rsc، endpointهای backup-rsc، پیام‌های فارسی پشتیبان‌گیری
   با نام جدید پوشهٔ mik_backup (Task 36)؛
2) CSS شامل .main-search-bar (مرکزچین) و .btn-backup-rsc؛
3) فیلتر قبلی (filter-search) دیگر در باندل رندر نمی‌شود (کلاس حذف شده)؛
4) endpoint فایل‌ها با TestClient پاسخ می‌دهد (200) و پوشهٔ mik_backup/ کنار
   برنامه وجود دارد (و پوشهٔ قدیمی backup/ منتقل شده است).
"""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")

ok = True
def check(label, cond, extra=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label, extra)
    ok = ok and cond

js_files = [f for f in os.listdir(os.path.join(DIST, "assets")) if f.endswith(".js")]
css_files = [f for f in os.listdir(os.path.join(DIST, "assets")) if f.endswith(".css")]
check("dist has one js + one css", len(js_files) == 1 and len(css_files) == 1, str(js_files) + str(css_files))
js = open(os.path.join(DIST, "assets", js_files[0]), encoding="utf-8").read()
css = open(os.path.join(DIST, "assets", css_files[0]), encoding="utf-8").read()

# ---------- 1) جعبهٔ جستجوی جدید ----------
check("bundle: main-search-bar rendered", 'main-search-bar' in js)
check("bundle: main-search-input class", 'main-search-input' in js)
check("bundle: search placeholder (RTL)", "جستجو در IP، نام دستگاه" in js)
check("bundle: old filter-search label removed", "جست\u200cوجو در فیلدها" not in js and 'filter-search' not in js,
      "کلاس/برچسب قدیمی نباید رندر شود")
check("css: .main-search-bar centered", ".main-search-bar{" in css and "justify-content:center" in css)
check("css: .main-search-input larger font", ".main-search-input{" in css and re.search(r"\.main-search-input\{[^}]*font-size:15", css) is not None)

# ---------- 2) دکمهٔ پشتیبان‌گیری rsc ----------
check("bundle: btn-backup-rsc button", 'btn-backup-rsc' in js)
check("bundle: backup button label", "پشتیبان\u200cگیری rsc" in js)
check("bundle: backup endpoints", "/api/devices/backup-rsc" in js
      and "/api/devices/backup-rsc/progress" in js
      and "/api/devices/backup-rsc/cancel" in js)
check("bundle: backup progress chart title", "نمودار پیشرفت پشتیبان\u200cگیری rsc" in js)
check("bundle: stop backup button", "توقف پشتیبان" in js)
check("css: .btn-backup-rsc styled", ".btn-backup-rsc{" in css)

# ---------- 3) endpoint واقعی + پوشهٔ mik_backup ----------
from fastapi.testclient import TestClient
import main as appm
client = TestClient(appm.app)
_r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
assert _r.status_code == 200, f"login failed: {_r.status_code}"

r = client.get("/api/devices/backup-rsc/files")
check("endpoint: files list -> 200", r.status_code == 200, r.text[:120])
check("endpoint: files payload shape", isinstance(r.json().get("files"), list) and "folder" in r.json())

from backup_rsc import BACKUP_DIR
check("folder: mik_backup/ exists next to app (Task 36 rename)", os.path.isdir(BACKUP_DIR) and os.path.basename(BACKUP_DIR) == "mik_backup", str(BACKUP_DIR))
check("folder: mik_backup/ is absolute app root", os.path.basename(os.path.dirname(BACKUP_DIR)) not in ("", "/")
      and os.path.exists(os.path.join(os.path.dirname(BACKUP_DIR), "backend")))
_old = os.path.join(os.path.dirname(BACKUP_DIR), "backup")
check("folder: old backup/ migrated away (renamed or emptied)", not os.path.isdir(_old) or not any(f.endswith(".rsc") for f in os.listdir(_old)), _old)

# ---------- 4) عیب‌یابی فارسی خطاها (Task 36) در سورس/باندل — endpoint پیشرفت ----------
import backup_rsc as _br
_m = _br._friendly_error(ConnectionRefusedError("connection refused"), "connect")
check("friendly error: connect refused mentions /ip service enable api", "enable api" in _m and "8728" in _m)
_m = _br._friendly_error(TimeoutError("timed out"), "read")
check("friendly error: slow export explains timeout", "طول کشید" in _m)

print("\nALL OK" if ok else "\nFAILURES PRESENT")
sys.exit(0 if ok else 1)
