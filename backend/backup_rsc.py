"""پشتیبان‌گیری کانفیگ میکروتیک به‌صورت rsc (Task 34).

درخواست کاربر: «یک فولدر به نام backup در مسیر برنامه ایجاد کن که با یک دکمهٔ
backup بتواند از طریق API و ورود یوزر/پسورد بک‌آپ دستگاه‌های میکروتیک با پسوند
rsc بگیرد؛ با نام/ای‌دی دستگاه‌ها و ای‌پی دستگاه در فولدر backup ذخیره کند».

- پوشهٔ backup در ریشهٔ برنامه (کنار backend/ و frontend/) ساخته می‌شود؛
- اتصال با همان کلاینت RouterOS API پروژه (routeros_api.RouterOSClient —
  پورت 8728، احراز هویت v6.43+ و چالش-پاسخ قدیم) برقرار می‌شود؛
- خروجی با دستور «/export» خوانده می‌شود (متن کانفیگ rsc) و در فایل
  «<نام‌دستگاه>_<IP>.rsc» (utf-8) ذخیره می‌شود؛ دستگاه بی‌نام از ای‌دی ردیف
  دیتابیس نام می‌گیرد (device-<id>)؛
- پیشرفت (total/done/ok/failed/current_ip/percent) در BACKUP_PROGRESS نگه
  داشته می‌شود تا UI حین اجرا نمودار پیشرفت را بکشد؛ لغو مشارکتی با Event.
"""
from __future__ import annotations

import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

try:
    from backend import routeros_api as _ros
except ImportError:  # اجرای مستقیم بدون پکیج
    import routeros_api as _ros

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = ROOT_DIR / "backup"

# «فولدر به نام backup در مسیر برنامه» — با ایمپورت ماژول تضمین می‌شود
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

BACKUP_CANCEL = threading.Event()
BACKUP_PROGRESS = {
    "total": 0, "done": 0, "ok": 0, "failed": 0,
    "current_ip": "", "percent": 0,
    "running": False, "canceled": False, "error": None,
}

_UNSAFE_RE = re.compile(r'[\\/:*?"<>|\r\n\t ]+')
_MAX_STEM = 80
# خواندن /export ممکن است روی روترهای پرکانفیگ چند ده ثانیه طول بکشد
EXPORT_MIN_TIMEOUT = 60.0


def safe_stem(name: str, fallback: str = "router") -> str:
    """نام مجاز فایل از نام دستگاه: حذف کاراکترهای غیرمجاز ویندوز/لینوکس."""
    s = _UNSAFE_RE.sub("-", str(name or "").strip()).strip("-.")
    s = s[:_MAX_STEM].strip("-.")
    return s or fallback


def backup_filename(device_name: str, ip: str, dev_id=None) -> str:
    """«<نام دستگاه>_<IP>.rsc» — دستگاه بی‌نام از ای‌دی ردیف دیتابیس نام می‌گیرد."""
    name = safe_stem(device_name, fallback="")
    if not name:
        name = f"device-{dev_id}" if dev_id is not None else "device"
    ip_safe = safe_stem(ip, fallback="no-ip")
    return f"{name}_{ip_safe}.rsc"


def export_config_via_api(host: str, username: str, password: str,
                          port: int = 8728, timeout: float = 20.0) -> str:
    """اتصال RouterOS API و خواندن متن کانفیگ (/export) به‌صورت rsc.

    پاسخ API ممکن است یک «!done» با «=ret=» کامل باشد یا چند «!re» تکه‌تکه
    به‌همراه «!done» — هر دو حالت پشتیبانی می‌شوند (تکه‌ها به‌ترتیب چسبانده
    می‌شوند). خطاها با پیام فارسی بالا می‌روند.
    """
    host = str(host or "").strip()
    if not host:
        raise _ros.RouterOSError("IP دستگاه خالی است")
    read_timeout = max(float(timeout or 20.0), EXPORT_MIN_TIMEOUT)
    cli = _ros.RouterOSClient(host, port=int(port or 8728), timeout=read_timeout)
    try:
        cli.connect()
        cli.login(username or "", password or "")
        replies = cli.talk(["/export"], timeout=read_timeout)
    finally:
        cli.close()
    traps = [s for s in replies if s and s[0] == "!trap"]
    fatals = [s for s in replies if s and s[0] == "!fatal"]
    if fatals:
        raise _ros.RouterOSError(_ros._trap_message(fatals[0]) or "خواندن کانفیگ ناموفق")
    if traps:
        raise _ros.RouterOSError(_ros._trap_message(traps[0]) or "خواندن کانفیگ ناموفق")
    parts: list[str] = []
    for s in replies:
        for w in s:
            if isinstance(w, str) and w.startswith("=ret="):
                parts.append(w[5:])
    text = "".join(parts)
    if not text.strip():
        raise _ros.RouterOSError("خروجی /export خالی بود (دسترسی کافی نیست یا نسخهٔ RouterOS از export پشتیبانی نمی‌کند)")
    return text


def _reset_progress(total: int) -> None:
    BACKUP_CANCEL.clear()
    BACKUP_PROGRESS.update({"total": int(total), "done": 0, "ok": 0, "failed": 0,
                            "current_ip": "", "percent": 0,
                            "running": True, "canceled": False, "error": None})


def backup_devices(devices: list[dict], username: str, password: str,
                   port: int = 8728, timeout: float = 20.0, max_workers: int = 6,
                   cancel: threading.Event | None = None) -> list[dict]:
    """پشتیبان rsc برای هر دستگاه (موازی) — خروجی: ردیف‌های نتیجه.

    devices: ردیف‌های دیتابیس (ip / device_name / id). هر دستگاه فقط یک‌بار
    (بر اساس IP) پشتیبان گرفته می‌شود؛ نخستین ردیفِ هر IP ملاک نام فایل است.
    """
    devices = list(devices or [])
    seen: set[str] = set()
    unique: list[dict] = []
    for d in devices:
        ip = str((d or {}).get("ip") or "").strip()
        if not ip or ip in seen:
            continue
        seen.add(ip)
        unique.append(d)
    _reset_progress(len(unique))
    cancel = cancel or BACKUP_CANCEL
    prog = BACKUP_PROGRESS
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict] = [None] * len(unique)  # type: ignore[list-item]

    def _one(i: int, d: dict) -> None:
        if cancel.is_set():
            return
        ip = str(d.get("ip") or "").strip()
        name = str(d.get("device_name") or "").strip()
        prog["current_ip"] = ip
        fname = backup_filename(name, ip, d.get("id"))
        row = {"ip": ip, "device_name": name, "file": "", "ok": False, "error": ""}
        try:
            text = export_config_via_api(ip, username, password, port=port, timeout=timeout)
            # اگر نام فایل تکراری شد (دو ردیف هم‌نام هم‌IP) همان فایل به‌روز می‌شود
            fpath = BACKUP_DIR / fname
            fpath.write_text(text, encoding="utf-8")
            row.update(file=fname, ok=True)
        except Exception as e:  # RouterOSError / socket / OSError
            row["error"] = str(e)[:300]
        results[i] = row
        prog["done"] += 1
        if row["ok"]:
            prog["ok"] += 1
        else:
            prog["failed"] += 1
        prog["percent"] = int(round(100 * prog["done"] / prog["total"])) if prog["total"] else 0

    workers = max(1, min(int(max_workers or 1), len(unique) or 1))
    try:
        if workers == 1 or len(unique) <= 1:
            for i, d in enumerate(unique):
                _one(i, d)
        else:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                futs = [ex.submit(_one, i, d) for i, d in enumerate(unique)]
                for f in futs:
                    f.result()
    except Exception as e:  # نباید رخ دهد؛ برای اطمینان در progress می‌نشیند
        prog["error"] = str(e)[:300]
    prog["current_ip"] = ""
    prog["running"] = False
    prog["canceled"] = cancel.is_set()
    prog["percent"] = 100 if prog["done"] >= prog["total"] and prog["total"] else prog["percent"]
    out = [r for r in results if r is not None]
    return out


def list_backup_files() -> list[dict]:
    """فهرست فایل‌های rsc پوشهٔ backup (جدیدترین اول) — برای UI/تست."""
    items: list[dict] = []
    try:
        for p in sorted(BACKUP_DIR.glob("*.rsc")):
            st = p.stat()
            items.append({
                "file": p.name,
                "size": st.st_size,
                "modified": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
            })
    except OSError:
        return []
    items.sort(key=lambda x: x["modified"], reverse=True)
    return items


def ensure_backup_folder() -> str:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    return str(BACKUP_DIR)
