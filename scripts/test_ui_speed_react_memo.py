"""Smoke — Task 35: تقویت سرعت رابط کاربری (تایپ در جعبه‌های متنی).

ریشهٔ کندی: DeviceReports یک کامپوننت غول‌پیکر است و هر کلیدِ تایپ در هر ورودی متنی
(جستجو، فرم‌ها، مدال‌ها) کل جدول دستگاه‌ها را دوباره رندر می‌کرد؛ ضمناً MainApp هنگام
اسکن هر ۱.۲ ثانیه setJob می‌زند و همین رندرِ کامل صفحهٔ دستگاه‌ها را تکرار می‌کرد.

بررسی‌ها:
- سورس src.jsx: جدول داخل useMemo با وابستگی‌های درست، liveRef برای توابع جدول،
  ویرایشِ درجایِ نام uncontrolled (ref + defaultValue) بدون stateِ editNameVal،
  React.memo برای شش کارت سنگین + DeviceReportsM در تب‌ها، useCallback برای onRoutes،
  useDeferredValue در جستجوی DevicePickerModal؛
- باندل dist: index.html به فایل JS موجود اشاره می‌کند، باندل حاوی رشته‌های شاخص
  صفحهٔ دستگاه‌ها و defaultValue است؛
- بک‌اند سالم: /api/auth/check و GET / (سرو UI) و مسیر /api/devices بعد از لاگین.
Run: python3 scripts/test_ui_speed_react_memo.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    print(("PASS" if cond else "FAIL") + " - " + name)
    if cond:
        PASS += 1
    else:
        FAIL += 1


def test_src_markers():
    src = (ROOT / "frontend" / "src.jsx").read_text(encoding="utf-8")
    check("import شامل useMemo/useCallback/useDeferredValue است",
          "useMemo,useCallback,useDeferredValue" in src.replace(" ", ""))
    check("جدول دستگاه‌ها داخل useMemo است", "const tableEl=useMemo(" in src)
    check("وابستگی‌های memo جدول کامل است (با backupMap فیچر کانفیگ)",
          "[rows,selected,visibleCols,editNameIp,sortBy,sortOrder,backupMap]" in src)
    check("liveRef توابع جدول را هر رندر به‌روز می‌کند (با showDeviceConfig)",
          "liveRef.current={openWinbox,saveName,toggleSelect,toggleSelectAll,handleSort,showDeviceConfig}" in src)
    check("توابع جدول از liveRef صدا زده می‌شوند",
          src.count("liveRef.current.") >= 4)
    check("ویرایش درجایِ نام uncontrolled است (ref + defaultValue)",
          'ref={editNameInputRef} defaultValue={d.device_name||""}' in src)
    check("state قدیمی editNameVal کاملاً حذف شده", "editNameVal" not in src)
    check("saveName مقدار input را از ref می‌خواند",
          "editNameInputRef.current?editNameInputRef.current.value" in src)
    check("React.memo برای شش کارت سنگین تعریف شده",
          src.count("React.memo(") >= 6)
    check("DeviceReportsM در تب devices/system استفاده شده",
          '<DeviceReportsM mode="devices"/>' in src and '<DeviceReportsM mode="system"/>' in src)
    check("کاربرد خام <DeviceReports در MainApp باقی نمانده",
          "<DeviceReports " not in src.replace("<DeviceReportsM ", ""))
    check("onRoutes با useCallback پایدار شده", "const onRoutesCb=useCallback(" in src)
    check("SmartReports/Kartable/EmailServerCard/VpnManagerCard/BackendCard از نسخهٔ memo استفاده می‌کنند",
          all(t in src for t in ("<SmartReportsM/>", "<KartableM/>", "<EmailServerCardM/>",
                                 "<VpnManagerCardM ", "<BackendCardM ")))
    check("جستجوی DevicePickerModal با useDeferredValue است",
          "const deferredSearch=useDeferredValue(search)" in src
          and "(deferredSearch||\"\").trim().toLowerCase()" in src)


def test_dist_bundle():
    dist = ROOT / "frontend" / "dist"
    html = (dist / "index.html").read_text(encoding="utf-8")
    m = re.search(r"assets/(index-[A-Za-z0-9_-]+\.js)", html)
    check("index.html به باندل JS اشاره می‌کند", bool(m))
    if not m:
        return
    bundle = dist / "assets" / m.group(1)
    check("فایل باندل روی دیسک موجود است", bundle.is_file() and bundle.stat().st_size > 100_000)
    js = bundle.read_text(encoding="utf-8", errors="replace")
    check("باندل حاوی جعبهٔ جستجوی بزرگ است", "main-search-input" in js)
    check("باندل حاوی متن جدول خالی است", "دستگاهی نیست." in js)
    check("باندل حاوی دکمهٔ پشتیبان‌گیری rsc است", "پشتیبان‌گیری rsc" in js)
    check("باندل حاوی defaultValue (ویرایش uncontrolled نام) است", "defaultValue" in js)
    check("باندل حاوی placeholder جستجوی چندواژه‌ای است", "جستجو در IP، نام دستگاه، تگ" in js)


def test_backend_alive():
    from fastapi.testclient import TestClient
    import main as appm
    with TestClient(appm.app) as c:
        r = c.get("/api/auth/check")
        check("GET /api/auth/check بدون نشست → 401", r.status_code == 401)
        r = c.get("/")
        check("GET / سرو UI می‌دهد", r.status_code == 200 and "root" in r.text)
        r = c.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
        check("POST /api/login → 200", r.status_code == 200)
        r = c.get("/api/databases")
        check("GET /api/databases → 200", r.status_code == 200)


if __name__ == "__main__":
    test_src_markers()
    test_dist_bundle()
    try:
        test_backend_alive()
    except Exception as e:  # noqa: BLE001
        check("بک‌اند بدون خطا بالا می‌آید (" + str(e)[:80] + ")", False)
    print(f"\n{PASS} PASS / {FAIL} FAIL")
    sys.exit(1 if FAIL else 0)
