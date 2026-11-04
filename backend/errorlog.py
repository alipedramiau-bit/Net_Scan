"""ثبت لاگ خطا (Task 37) — ذخیرهٔ خطاهای عملیات‌ها در پوشهٔ mik_log/ کنار برنامه.

درخواست کاربر: «نتونست بک اپ بگیره؛ یک گزینه ثبت لاگ خطا در برگهٔ مدیریت سیستم
ایجاد کن؛ خطا را برطرف کن؛ یوزر پسورد ورود مشکلی نداره»

- خطاهای پشتیبان‌گیری rsc و خواندن API (و سایر عملیات‌هایی که بعداً وصل می‌شوند)
  با زمان/منبع/IP/علت در «mik_log/errorlog.jsonl» (هر خط یک JSON) نوشته می‌شود
  تا برخلاف جعبهٔ خطای موقت UI، بعداً هم قابل مرور باشد؛
- «گزینهٔ ثبت لاگ خطا» در برگهٔ راهبری سیستم: کلید فعال/خاموش — وضعیت در
  «mik_log/config.json» ماندگار است (پیش‌فرض: فعال)؛
- چرخش فایل: اگر errorlog.jsonl از ۲ مگابایت گذشت، فقط ۵۰۰ رویداد آخر می‌ماند
  تا فایل بی‌نهایت بزرگ نشود؛
- این ماژول هیچ وابستگی‌ای به دیتابیس/نشست ندارد — حتی اگر backend وسط کار
  ری‌استارت شود، خطاهای قبلی سر جایشان هستند.
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT_DIR / "mik_log"
LOG_FILE = LOG_DIR / "errorlog.jsonl"
CONFIG_FILE = LOG_DIR / "config.json"

_lock = threading.Lock()

# چرخش فایل لاگ
MAX_FILE_BYTES = 2_000_000
KEEP_ON_ROTATE = 500

# سقف طول هر فیلد در هر رویداد
_MAX_FIELD = 500


def _ensure_dir() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _fa_time(ts: float) -> str:
    """زمان محلی (Asia/Tehran در سیستم کاربر) به‌صورت YYYY-MM-DD HH:MM:SS."""
    try:
        from zoneinfo import ZoneInfo
        dt = datetime.fromtimestamp(ts, ZoneInfo("Asia/Tehran"))
    except Exception:  # ویندوز بدون tzdata یا zoneinfo قدیمی
        dt = datetime.fromtimestamp(ts)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ------------------------------- کلید فعال/خاموش ----------------------------
def is_enabled() -> bool:
    """آیا ثبت لاگ خطا فعال است؟ (پیش‌فرض و در نبود فایل تنظیمات: بله)"""
    try:
        return bool(json.loads(CONFIG_FILE.read_text("utf-8")).get("enabled", True))
    except Exception:
        return True


def set_enabled(value: bool) -> bool:
    """کلید «ثبت لاگ خطا» را ماندگار می‌کند و مقدار نهایی را برمی‌گرداند."""
    with _lock:
        _ensure_dir()
        try:
            CONFIG_FILE.write_text(
                json.dumps({"enabled": bool(value)}, ensure_ascii=False), "utf-8")
        except OSError:
            pass
    return bool(value)


# ------------------------------- نوشتن --------------------------------------
def log_error(source: str, message: str, ip: str = "", raw: str = "",
              stage: str = "") -> dict | None:
    """یک رویداد خطا ثبت می‌کند؛ اگر ثبت غیرفعال باشد None برمی‌گرداند.

    source: منبع خطا (backup-rsc / probe-api / …)؛ message: علت فارسیِ آمادهٔ
    نمایش؛ raw: متن خام خطا (اگر جدا از message معنا دارد)؛ stage: مرحلهٔ شکست
    (connect/login/read).
    """
    if not is_enabled():
        return None
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "time": _fa_time(time.time()),
        "source": str(source or "")[:40],
        "ip": str(ip or "")[:64],
        "stage": str(stage or "")[:24],
        "message": str(message or "")[:_MAX_FIELD],
        "raw": str(raw or "")[:_MAX_FIELD],
    }
    with _lock:
        _ensure_dir()
        try:
            if LOG_FILE.exists() and LOG_FILE.stat().st_size > MAX_FILE_BYTES:
                _rotate()
            with LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            return None
    return entry


def _rotate() -> None:
    """فایل بزرگ → فقط KEEP_ON_ROTATE رویداد آخر می‌ماند."""
    try:
        lines = LOG_FILE.read_text("utf-8").splitlines()
        keep = [ln for ln in lines[-KEEP_ON_ROTATE:] if ln.strip()]
        tmp = LOG_FILE.with_suffix(".jsonl.tmp")
        tmp.write_text("\n".join(keep) + ("\n" if keep else ""), "utf-8")
        os.replace(str(tmp), str(LOG_FILE))
    except OSError:
        pass


# ------------------------------- خواندن/پاک کردن ----------------------------
def read_errors(limit: int = 200, source: str = "") -> list[dict]:
    """رویدادهای اخیر (جدیدترین اول) — سقف limit؛ فیلتر منبع اختیاری."""
    try:
        lines = LOG_FILE.read_text("utf-8").splitlines()
    except OSError:
        return []
    out: list[dict] = []
    want = max(1, min(int(limit or 200), 5000))
    for ln in reversed(lines):
        if len(out) >= want:
            break
        ln = ln.strip()
        if not ln:
            continue
        try:
            e = json.loads(ln)
        except Exception:
            continue
        if source and e.get("source") != source:
            continue
        out.append(e)
    return out


def count(source: str = "") -> int:
    """تعداد کل رویدادهای ثبت‌شده (برای نمایش شمارنده در UI)."""
    try:
        lines = LOG_FILE.read_text("utf-8").splitlines()
    except OSError:
        return 0
    n = 0
    for ln in lines:
        if not ln.strip():
            continue
        if source:
            try:
                if json.loads(ln).get("source") != source:
                    continue
            except Exception:
                continue
        n += 1
    return n


def clear() -> None:
    """پاک‌کردن همهٔ رویدادها (فایل خالی می‌شود، تنظیمات دست نمی‌خورد)."""
    with _lock:
        _ensure_dir()
        try:
            LOG_FILE.write_text("", "utf-8")
        except OSError:
            pass
