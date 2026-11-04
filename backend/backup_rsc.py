"""پشتیبان‌گیری کانفیگ میکروتیک به‌صورت rsc (Task 34؛ 36: پوشهٔ mik_backup + عیب‌یابی؛
37: روش فایل برای دستگاه‌هایی که /export را خالی برمی‌گردانند + ثبت لاگ خطا).

درخواست کاربر: «یک فولدر به نام backup در مسیر برنامه ایجاد کن که با یک دکمهٔ
backup بتواند از طریق API و ورود یوزر/پسورد بک‌آپ دستگاه‌های میکروتیک با پسوند
rsc بگیرد؛ با نام/ای‌دی دستگاه‌ها و ای‌پی دستگاه در فولدر backup ذخیره کند»
+ «فولدر backup را به نام mik_backup تغییر نام بده» (Task 36)
+ «نتونست بک اپ بگیره؛ یک گزینه ثبت لاگ خطا در برگهٔ مدیریت سیستم ایجاد کن؛
خطا را برطرف کن؛ یوزر پسورد ورود مشکلی نداره» (Task 37).

- پوشهٔ mik_backup در ریشهٔ برنامه (کنار backend/ و frontend/) ساخته می‌شود؛
  اگر پوشهٔ قدیمی backup/ موجود باشد، هنگام ایمپورت خودکار به mik_backup/
  منتقل می‌شود تا فایل‌های قبلی از بین نروند؛
- اتصال با همان کلاینت RouterOS API پروژه (routeros_api.RouterOSClient —
  پورت 8728، احراز هویت v6.43+ و چالش-پاسخ قدیم) برقرار می‌شود؛
- خروجی /export به دو روش خوانده می‌شود (Task 37): روش مستقیم (ROS 7: تکه‌های
  =ret=) و اگر خالی/خطا بود روش فایل — «/export =file=…» روی دستگاه (مجوز
  write لازم دارد) + پول اندازهٔ فایل + خواندن =contents= (سقف ~۴KB RouterOS)
  + حذف فایل موقت؛
- عیب‌یابی (Task 36): خطای هر دستگاه با علت فارسیِ مشخص برمی‌گردد — سرویس api
  غیرفعال/فیلتر (پورت 8728 جدا از Winbox 8291 است)، ورود ناموفق (رمز یا
  policy «api»)، طول‌کشیدن export (روتر پرکانفیگ CPU می‌زند) و قطع‌شدن اتصال؛
- لاگ خطا (Task 37): هر دستگاه ناموفق + خلاصهٔ پایان کار در
  mik_log/errorlog.jsonl ثبت می‌شود (ماژول errorlog؛ کلید فعال/خاموش در
  برگهٔ راهبری سیستم) تا علت شکست بعداً هم قابل مرور باشد؛
- پیشرفت (total/done/ok/failed/current_ip/percent) در BACKUP_PROGRESS نگه
  داشته می‌شود تا UI حین اجرا نمودار پیشرفت را بکشد؛ لغو مشارکتی با Event.
"""
from __future__ import annotations

import os
import re
import socket
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

try:
    from backend import routeros_api as _ros
except ImportError:  # اجرای مستقیم بدون پکیج
    import routeros_api as _ros
try:
    from backend import errorlog as _errorlog
except ImportError:
    import errorlog as _errorlog

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

# Task 37 — روش فایل: RouterOS 6 خروجی مستقیم /export را از API برنمی‌گرداند
# (تأیید فروم میکروتیک «Export configuration via API» و «How to read file
# content using API?»): باید export=file گرفت و محتوا را خواند؛ خواندن محتوا
# سقف ~۴ کیلوبایت دارد. پول اندازهٔ فایل: حداکثر ۱۲ بار، هر ثانیه تا ثبات.
_FILE_SIZE_CAP_HINT = 4096
_FILE_POLL_TRIES = 12
_FILE_POLL_INTERVAL = 1.0


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
        if "invalid user name or password" in low or "cannot log in" in low or "invalid username" in low:
            # Task 37 (ادامه): پیام (6) ردِ سمت خودِ روتر است — تجربهٔ واقعی کاربر:
            # همان یوزر/رمز روی برخی دستگاه‌ها ورود موفق داشته و فقط روی بقیه رد شده؛
            # یعنی مشکل از تنظیم همان دستگاه‌هاست (کاربر محلی/مجوز گروه/RADIUS).
            return ("ورود API از سمت روتر رد شد (" + raw + ") — سه علت رایج: "
                    "۱) روی «این دستگاه» رمز این کاربر چیز دیگری ست شده یا کاربر وجود ندارد "
                    "(هر روتر کاربرانِ محلی خودش را دارد)؛ "
                    "۲) گروهِ کاربر مجوز policy «api» ندارد؛ "
                    "۳) احراز هویت از RADIUS/سرور مرکزی انجام می‌شود و آن سمت رد کرده. "
                    "با Winbox وارد شوید ← System → Users ← کاربر را بررسی/رمز را یکسان کنید "
                    "و گروه باید مجوز api و read داشته باشد")
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


def _export_via_file(cli, read_timeout: float) -> str:
    """روش دوم خواندن کانفیگ (Task 37): «/export =file=…» + خواندن محتوای فایل.

    RouterOS 6 خروجی مستقیم /export را از API برنمی‌گرداند (فقط !done) — کار
    مستندشده: export در فایل روی دستگاه (مجوز write لازم دارد)، پول تا ثبات
    اندازه، خواندن =contents= (سقف ~۴KB) و حذف فایل موقت. نام فایل بدون پسوند
    فرستاده می‌شود؛ RouterOS خودش «.rsc» اضافه می‌کند (پسوندِ اضافه‌نشدن هم
    پوشش داده می‌شود).
    """
    tmp = "mikbk-" + uuid.uuid4().hex[:8]
    fname = tmp + ".rsc"
    replies = cli.talk(["/export", f"=file={tmp}"], timeout=read_timeout)
    traps = [s for s in replies if s and s[0] == "!trap"]
    fatals = [s for s in replies if s and s[0] == "!fatal"]
    if fatals or traps:
        raw = _ros._trap_message((fatals or traps)[0]) or "export به فایل ناموفق"
        raise _ros.RouterOSError(
            "دستور /export =file= اجرا نشد (" + raw + ") — این دستور مجوز write لازم "
            "دارد؛ گروه کاربر باید policy «read,write,api» داشته باشد")
    fid = ""
    found_name = ""
    size = -1
    stable = 0
    for attempt in range(_FILE_POLL_TRIES):
        if attempt:
            time.sleep(_FILE_POLL_INTERVAL)
        for qname in (fname, tmp):
            replies = cli.talk(["/file/print", f"?name={qname}",
                                "=.proplist=.id,name,size"], timeout=read_timeout)
            rows = [s for s in replies if s and s[0] == "!re"]
            if rows:
                found_name = qname
                fid = next((w[5:] for w in rows[0] if isinstance(w, str) and w.startswith("=.id=")), fid)
                try:
                    sz = int(next((w[6:] for w in rows[0] if isinstance(w, str) and w.startswith("=size=")), "-1"))
                except ValueError:
                    sz = -1
                if sz >= 0 and sz == size:
                    stable += 1
                else:
                    size = sz
                    stable = 0
                break
        if found_name and stable >= 2:
            break
    target = found_name or fname
    replies = cli.talk(["/file/print", f"?name={target}",
                        "=.proplist=contents"], timeout=read_timeout)
    rows = [s for s in replies if s and s[0] == "!re"]
    text = ""
    for w in (rows[0] if rows else []):
        if isinstance(w, str) and w.startswith("=contents="):
            text += w[10:]
    if fid:  # پاک‌سازی فایل موقت روی دستگاه — خطایش پشتیبان را ناموفق نمی‌کند
        try:
            cli.talk(["/file/remove", f"=.id={fid}"], timeout=min(read_timeout, 15.0))
        except Exception:
            pass
    if not text.strip():
        hint = ""
        if size > _FILE_SIZE_CAP_HINT:
            hint = (f" — فایل روی دستگاه {size} بایت است؛ سقف خواندن محتوا از طریق API حدود "
                    "۴ کیلوبایت است (RouterOS محتویات فایل بزرگ‌تر را برنمی‌گرداند — "
                    "برای این دستگاه از Winbox/FTP یا ارتقای به ROS 7 استفاده کنید)")
        elif size < 0:
            hint = " — فایل export روی دستگاه ساخته نشد (نام کاربر مجوز write ندارد یا دیسک پر است)"
        raise _ros.RouterOSError("محتوای فایل export خوانده نشد" + hint)
    return text


def export_config_via_api(host: str, username: str, password: str,
                          port: int = 8728, timeout: float = 20.0) -> str:
    """اتصال RouterOS API و خواندن متن کانفیگ (/export) به‌صورت rsc.

    روش اول: پاسخ مستقیم /export — ممکن است یک «!done» با «=ret=» کامل باشد یا
    چند «!re» تکه‌تکه به‌همراه «!done» (ROS 7). روش دوم (Task 37): اگر روش اول
    خالی یا خطا داد — الگوی رایج ROS 6 — کانفیگ با «/export =file=…» روی دستگاه
    نوشته و محتوایش خوانده می‌شود (_export_via_file). خطاها با علت فارسیِ
    مرحلهٔ شکست (connect/login/read) بالا می‌روند (Task 36).
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
        cli.close()
        raise _ros.RouterOSError(_friendly_error(e, stage)) from None
    traps = [s for s in replies if s and s[0] == "!trap"]
    fatals = [s for s in replies if s and s[0] == "!fatal"]
    text = ""
    direct_err = ""
    if fatals:
        direct_err = _ros._trap_message(fatals[0]) or "خواندن کانفیگ ناموفق"
    elif traps:
        direct_err = _ros._trap_message(traps[0]) or "خواندن کانفیگ ناموفق"
    else:
        parts: list[str] = []
        for s in replies:
            for w in s:
                if isinstance(w, str) and w.startswith("=ret="):
                    parts.append(w[5:])
        text = "".join(parts)
    if text.strip():
        cli.close()
        return text

    # Task 37 — ROS 6.x: /export مستقیم فقط !done می‌دهد → روش فایل
    try:
        text = _export_via_file(cli, read_timeout)
    except Exception as e2:
        cli.close()
        msg = "خروجی /export خالی بود (این نسخهٔ RouterOS خروجی export را مستقیم از API برنمی‌گرداند)"
        if direct_err:
            msg += f" — پاسخ مستقیم: {direct_err}"
        msg += f" — روش فایل هم ناموفق بود: {e2}"
        raise _ros.RouterOSError(msg) from None
    cli.close()
    if not text.strip():
        msg = "خروجی /export خالی بود (روش مستقیم و روش فایل هر دو بی‌نتیجه بود)"
        if direct_err:
            msg += f" — پاسخ مستقیم: {direct_err}"
        raise _ros.RouterOSError(msg)
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
            # Task 37: ثبت در لاگ خطا (برگهٔ راهبری سیستم) — خطا نباید پشتیبان‌گیری را متوقف کند
            try:
                _errorlog.log_error(source="backup-rsc", ip=ip, message=row["error"])
            except Exception:
                pass
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
    # Task 37 (ادامه): خلاصهٔ هر اجرا همیشه ثبت می‌شود — با سطح warn (شکست داشته)
    # یا info (تماماً موفق) تا لاگ فقط خطا نباشد و مرور تاریخچه ممکن باشد
    try:
        summary = (f"پشتیبان‌گیری rsc پایان یافت: {prog['ok']} موفق، "
                   f"{prog['failed']} ناموفق از {prog['total']} دستگاه (پوشهٔ mik_backup/)")
        if cancel.is_set():
            summary += " — متوقف شد"
        if prog["failed"]:
            _errorlog.log_warn(source="backup-rsc", ip="", message=summary)
        else:
            _errorlog.log_info(source="backup-rsc", ip="", message=summary)
    except Exception:
        pass
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
