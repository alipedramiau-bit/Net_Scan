"""پشتیبان‌گیری کانفیگ میکروتیک به‌صورت rsc (Task 34؛ Task 36: پوشهٔ mik_backup + عیب‌یابی واضح).

درخواست کاربر: «یک فولدر به نام backup در مسیر برنامه ایجاد کن که با یک دکمهٔ
backup بتواند از طریق API و ورود یوزر/پسورد بک‌آپ دستگاه‌های میکروتیک با پسوند
rsc بگیرد؛ با نام/ای‌دی دستگاه‌ها و ای‌پی دستگاه در فولدر backup ذخیره کند»
+ «فولدر backup را به نام mik_backup تغییر نام بده» (Task 36).

- پوشهٔ mik_backup در ریشهٔ برنامه (کنار backend/ و frontend/) ساخته می‌شود؛
  اگر پوشهٔ قدیمی backup/ موجود باشد، هنگام ایمپورت خودکار به mik_backup/
  منتقل می‌شود تا فایل‌های قبلی از بین نروند؛
- اتصال با همان کلاینت RouterOS API پروژه (routeros_api.RouterOSClient —
  پورت 8728، احراز هویت v6.43+ و چالش-پاسخ قدیم) برقرار می‌شود؛
- خروجی با دستور «/export» خوانده می‌شود (متن کانفیگ rsc) و در فایل
  «<نام‌دستگاه>_<IP>.rsc» (utf-8) ذخیره می‌شود؛ دستگاه بی‌نام از ای‌دی ردیف
  دیتابیس نام می‌گیرد (device-<id>)؛
- عیب‌یابی (Task 36): خطای هر دستگاه با علت فارسیِ مشخص برمی‌گردد — سرویس api
  غیرفعال/فیلتر (پورت 8728 جدا از Winbox 8291 است)، ورود ناموفق (رمز یا
  policy «api»)، طول‌کشیدن export (روتر پرکانفیگ CPU می‌زند) و قطع‌شدن اتصال؛
- پیشرفت (total/done/ok/failed/current_ip/percent) در BACKUP_PROGRESS نگه
  داشته می‌شود تا UI حین اجرا نمودار پیشرفت را بکشد؛ لغو مشارکتی با Event.
"""
from __future__ import annotations

import os
import re
import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

try:
    from backend import routeros_api as _ros
except ImportError:  # اجرای مستقیم بدون پکیج
    import routeros_api as _ros

ROOT_DIR = Path(__file__).resolve().parent.parent
# Task 36: نام پوشه از backup به mik_backup تغییر کرد (فولدر پشتیبان‌گیری کامل دیتابیس
# هم در backend/main.py با همین نام‌ها قاطی نشود — این پوشه فقط مخصوص rsc دستگاه‌هاست)
BACKUP_DIR = ROOT_DIR / "mik_backup"


def _migrate_old_backup_folder() -> None:
    """پوشهٔ قدیمی backup/ را به mik_backup/ منتقل می‌کند (Task 36).

    - اگر mik_backup وجود نداشته باشد: تغییر نام یک‌جای پوشه (سریع، بدون کپی)؛
    - اگر هر دو موجود باشند: فقط فایل‌های rsc قدیمی که در مقصد نیستند منتقل
      می‌شوند؛ پوشهٔ قدیمی دست‌نخورده می‌ماند تا کاربر خودش حذف کند.
    """
    old = ROOT_DIR / "backup"
    try:
        if not old.is_dir():
            return
        if not BACKUP_DIR.exists():
            try:
                os.replace(str(old), str(BACKUP_DIR))
                return
            except OSError:
                pass
        for p in old.glob("*.rsc"):
            dst = BACKUP_DIR / p.name
            if not dst.exists():
                try:
                    os.replace(str(p), str(dst))
                except OSError:
                    pass
    except OSError:
        pass


_migrate_old_backup_folder()
# با ایمپورت ماژول تضمین می‌شود پوشهٔ mik_backup کنار برنامه هست
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

BACKUP_CANCEL = threading.Event()
BACKUP_PROGRESS = {
    "total": 0, "done": 0, "ok": 0, "failed": 0,
    "current_ip": "", "percent": 0,
    "running": False, "canceled": False, "error": None,
}

_UNSAFE_RE = re.compile(r'[\\/:*?"<>|\r\n\t ]+')
_MAX_STEM = 80
# خواندن /export روی روترهای پرکانفیگ (مخصوصاً v7) CPU سنگین می‌زند و ممکن است
# بیش از یک دقیقه طول بکشد — سقف کفِ timeout را ۹۰ ثانیه گذاشتیم (Task 36)
EXPORT_MIN_TIMEOUT = 90.0
# اتصال اولیه نباید ۹۰ ثانیه منتظر بماند — دستگاهی که سرویس api ندارد/فایروال
# فیلتر می‌کند باید سریع با پیام واضح fail شود تا صف پیشرفت گیر نکند (Task 36)
CONNECT_TIMEOUT_CAP = 12.0


def _friendly_error(e: Exception, stage: str) -> str:
    """علت فارسیِ مشخص برای هر خطا بر اساس مرحلهٔ شکست (Task 36).

    stage: connect (اتصال TCP) / login (ورود) / read (خواندن پاسخ export).
    متن خام خطا همیشه داخل پیام می‌ماند تا جزئیات از بین نرود.
    """
    raw = str(e) or e.__class__.__name__
    low = raw.lower()
    timed = isinstance(e, TimeoutError) or "timed out" in low or "timeout" in low
    reset = isinstance(e, (ConnectionResetError, BrokenPipeError)) or "reset" in low or "broken pipe" in low
    refused = isinstance(e, ConnectionRefusedError) or "refused" in low
    if stage == "connect":
        if refused:
            return ("سرویس API روی دستگاه غیرفعال است (اتصال به پورت 8728 رد شد — " + raw
                    + ")؛ Winbox از پورت جداگانهٔ 8291 استفاده می‌کند و ربطی به API ندارد — "
                      "در ترمینال دستگاه: /ip service enable api")
        if timed:
            return ("اتصال به سرویس API (پورت 8728) برقرار نشد (" + raw
                    + ") — سرویس api فعال نیست یا فایروال پورت را فیلتر می‌کند؛ "
                      "Winbox (8291) سرویس جداگانه‌ای است — با /ip service enable api فعالش کنید")
        return "اتصال به دستگاه برقرار نشد (" + raw + ") — IP/شبکه و سرویس api را بررسی کنید"
    if stage == "login":
        if timed:
            return "پاسخ ورود API دیر رسید (" + raw + ") — دستگاه شلوغ یا شبکه کند است؛ دوباره تلاش کنید"
        return ("ورود API ناموفق (" + raw
                + ") — نام کاربری/رمز را بررسی کنید؛ اگر درست است، گروهِ کاربر باید مجوز policy «api» داشته باشد")
    if stage == "read":
        if timed:
            return ("خواندن خروجی /export بیش از حد طول کشید (" + raw
                    + ") — روی روترهای با کانفیگ بزرگ، دستور export CPU سنگین می‌زند و ممکن است دقیقه‌ها طول بکشد؛ "
                      "دوباره تلاش کنید یا timeout بزرگ‌تری بفرستید")
        if reset:
            return "اتصال حین خواندن /export قطع شد (" + raw + ") — دستگاه ری‌استارت شده یا سرویس api محدود است؛ دوباره تلاش کنید"
        return "خطا هنگام خواندن /export (" + raw + ")"
    return raw


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
    می‌شوند). خطاها با علت فارسیِ مرحلهٔ شکست (connect/login/read) بالا
    می‌روند (Task 36).
    """
    host = str(host or "").strip()
    if not host:
        raise _ros.RouterOSError("IP دستگاه خالی است")
    read_timeout = max(float(timeout or 20.0), EXPORT_MIN_TIMEOUT)
    connect_timeout = min(read_timeout, CONNECT_TIMEOUT_CAP)
    cli = _ros.RouterOSClient(host, port=int(port or 8728), timeout=read_timeout,
                              connect_timeout=connect_timeout)
    stage = "connect"
    try:
        cli.connect()
        stage = "login"
        cli.login(username or "", password or "")
        stage = "read"
        replies = cli.talk(["/export"], timeout=read_timeout)
    except Exception as e:  # socket/RouterOSError — علت فارسی بر اساس مرحله
        raise _ros.RouterOSError(_friendly_error(e, stage)) from None
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
    """فهرست فایل‌های rsc پوشهٔ mik_backup (جدیدترین اول) — برای UI/تست."""
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
