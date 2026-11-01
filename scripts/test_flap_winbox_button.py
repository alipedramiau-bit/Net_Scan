"""Smoke — Task 31: دکمهٔ Winbox کنار نام دستگاه در جدول گزارش flap.

بررسی‌ها:
- باندل ساخته‌شدهٔ frontend/dist حاوی دکمهٔ Winbox جدول flap است
  (کلاس btn-winbox btn-winbox-inline + فراخوانی POST /devices/{ip}/winbox
  + پیام موفقیت مخصوص پنل گزارش flap)؛
- همان مسیری که دکمه صدا می‌زند روی اپ واقعی درست پاسخ می‌دهد:
  IP نامعتبر -> 400؛ نبودن exe -> 404 با پیام فارسی؛ exe ساختگی ->
  اجرای winbox با IP همان ردیف (بدون هیچ تماس واقعی).
Run: python3 scripts/test_flap_winbox_button.py
"""
import os
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient

import auth
import main as appm

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    print(("PASS" if cond else "FAIL") + " - " + name)
    if cond:
        PASS += 1
    else:
        FAIL += 1


def test_bundle_has_flap_winbox_button():
    assets = ROOT / "frontend" / "dist" / "assets"
    bundles = sorted(assets.glob("index-*.js"))
    check("dist bundle exists", bool(bundles))
    if not bundles:
        return
    js = bundles[-1].read_text(encoding="utf-8", errors="ignore")
    check("bundle has inline winbox button class", "btn-winbox btn-winbox-inline" in js)
    check("bundle calls POST /devices/{ip}/winbox", "}/winbox" in js and "encodeURIComponent" in js)
    check("bundle has flap-panel success message", "Winbox اجرا شد" in js)
    check("bundle has flap-panel failure hint", "مسیر Winbox" in js)


def test_winbox_endpoint_for_flap_button():
    client = TestClient(appm.app)
    client.cookies.set(auth.COOKIE_NAME, auth.create_token(auth.ADMIN_USER))

    r = client.post("/devices/999.999.1.1/winbox")
    check("invalid IP -> 400", r.status_code == 400)

    with mock.patch.object(appm, "_resolve_winbox_exe", lambda _id=None: None):
        r = client.post("/devices/172.18.1.12/winbox")
    check("no exe -> 404", r.status_code == 404)
    check("404 detail mentions Winbox", "Winbox" in r.json().get("detail", ""))

    called = []

    def fake_popen(cmd, **kwargs):
        called.append(list(cmd))
        return None

    with mock.patch.object(appm, "_resolve_winbox_exe", lambda _id=None: "C:\\fake\\winbox64.exe"), \
         mock.patch.object(appm.subprocess, "Popen", fake_popen):
        r = client.post("/devices/172.18.1.12/winbox")
    d = r.json()
    check("launch -> 200 ok", r.status_code == 200 and d.get("ok") is True)
    check("launch uses row IP", d.get("ip") == "172.18.1.12")
    check("launch command is [exe, ip]", called == [["C:\\fake\\winbox64.exe", "172.18.1.12"]])


if __name__ == "__main__":
    test_bundle_has_flap_winbox_button()
    test_winbox_endpoint_for_flap_button()
    print(f"\n{PASS} PASS, {FAIL} FAIL")
    sys.exit(1 if FAIL else 0)
