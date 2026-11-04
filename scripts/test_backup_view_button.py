"""Task 38 — دکمهٔ «نمایش کانفیگ» کنار نام هر دستگاه (فایل rsc در mik_backup/).

بررسی‌ها:
1) سورس فرانت: دکمهٔ btn-cfg-rsc با برچسب «نمایش کانفیگ»، وضعیت disabled وقتی
   فایل نیست، اندپوینت‌های check و view و دکمهٔ «دانلود .rsc» در مدال؛
2) CSS: استایل .btn-detail.btn-cfg-rsc + حالت disabled؛
3) بک‌اند: find_backup_for_device (نام دقیق + الگوی *_<IP>.rsc + جدیدترین)؛
4) اندپوینت‌ها با TestClient: check برای دستگاه با/بدون فایل، view محتوای
   درست، 404 برای فایل ناموجود، 400 برای مسیرگیری (../) و پسوند غیر rsc؛
5) پاک‌سازی فایل‌های موقت تست.
"""
import os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "backend"))

ok = True
def check(label, cond, extra=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label, extra)
    ok = ok and cond

# ---------- 1) سورس فرانت ----------
src = open(os.path.join(ROOT, "frontend", "src.jsx"), encoding="utf-8").read()
check("src: show-config button class", "btn-cfg-rsc" in src)
check("src: button label «نمایش کانفیگ»", "نمایش کانفیگ" in src)
check("src: disabled when no backup file", "disabled={!(backupMap[d.ip]&&backupMap[d.ip].exists)}" in src)
check("src: check endpoint called", "/api/devices/backup-rsc/check" in src)
check("src: view endpoint called", "/api/devices/backup-rsc/view" in src)
check("src: modal download .rsc button", "دانلود .rsc" in src)
check("src: table memo depends on backupMap", "[rows,selected,visibleCols,editNameIp,sortBy,sortOrder,backupMap]" in src)

# ---------- 2) CSS ----------
css = open(os.path.join(ROOT, "frontend", "style.css"), encoding="utf-8").read()
check("css: .btn-cfg-rsc styled", ".btn-detail.btn-cfg-rsc{" in css)
check("css: .btn-cfg-rsc disabled state", ".btn-detail.btn-cfg-rsc:disabled{" in css)

# ---------- 3) بک‌اند: یافتن فایل دستگاه ----------
from backup_rsc import BACKUP_DIR, find_backup_for_device, backup_filename, read_backup_file

os.makedirs(BACKUP_DIR, exist_ok=True)
tmp_files: list = []
def _mk(name, content="/export test\n"):
    p = BACKUP_DIR / name
    p.write_text(content, encoding="utf-8")
    tmp_files.append(p)
    return p

NAME, IP = "Test-Dev-38", "10.99.99.38"
_exact_name = backup_filename(NAME, IP)
_mk(_exact_name, "# exact match\n/export\r\nadd name=test")
info = find_backup_for_device(NAME, IP)
check("find: exact filename found", bool(info) and info.get("file") == _exact_name, str(info))

# فایل با نام قدیمی (نام دستگاه عوض شده) — الگوی *_<IP>.rsc
os.remove(BACKUP_DIR / _exact_name)
_mk("old-name_10.99.99.38.rsc", "# old name\n/export")
info = find_backup_for_device(NAME, IP)
check("find: glob by IP fallback", bool(info) and info.get("file") == "old-name_10.99.99.38.rsc", str(info))

# دستگاه بدون بک‌آپ
info = find_backup_for_device("No-Such-Device", "10.99.99.1")
check("find: none for missing device", info is None, str(info))

# ---------- 4) اندپوینت‌ها ----------
from fastapi.testclient import TestClient
import main as appm
client = TestClient(appm.app)
_r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
assert _r.status_code == 200, f"login failed: {_r.status_code}"

r = client.get("/api/devices/backup-rsc/check", params={"ips": f"{IP},10.99.99.1"})
check("endpoint: check -> 200", r.status_code == 200, r.text[:120])
d = r.json()
check("endpoint: check shape", "folder" in d and isinstance(d.get("devices"), dict))
check("endpoint: check exists=true for backed-up ip",
      d["devices"].get(IP, {}).get("exists") is True and d["devices"][IP].get("file") == "old-name_10.99.99.38.rsc",
      str(d["devices"].get(IP)))
check("endpoint: check exists=false for missing ip",
      d["devices"].get("10.99.99.1", {}).get("exists") is False, str(d["devices"].get("10.99.99.1")))

r = client.get("/api/devices/backup-rsc/view", params={"file": "old-name_10.99.99.38.rsc"})
check("endpoint: view -> 200", r.status_code == 200, r.text[:120])
d = r.json()
check("endpoint: view content matches", "# old name" in (d.get("content") or "") and d.get("file") == "old-name_10.99.99.38.rsc")
check("endpoint: view meta size/modified", isinstance(d.get("size"), int) and bool(d.get("modified")))

r = client.get("/api/devices/backup-rsc/view", params={"file": "no_such_file.rsc"})
check("endpoint: view missing -> 404", r.status_code == 404, str(r.status_code))
r = client.get("/api/devices/backup-rsc/view", params={"file": "../backend/main.py"})
check("endpoint: path traversal rejected (400)", r.status_code == 400, r.text[:120])
r = client.get("/api/devices/backup-rsc/view", params={"file": "main.py"})
check("endpoint: non-rsc extension rejected (400)", r.status_code == 400, r.text[:120])

# ---------- 5) پاک‌سازی ----------
for p in tmp_files:
    try:
        os.remove(p)
    except OSError:
        pass
check("cleanup: temp rsc files removed", not any((BACKUP_DIR / p.name).exists() for p in tmp_files))

print("\nALL OK" if ok else "\nFAILURES PRESENT")
sys.exit(0 if ok else 1)
