"""کارتابل اداری — ذخیره‌سازی نامه‌ها/یادداشت‌ها، اطلاعیه‌ها و رویدادهای تقویم کاری.

دیتابیس مستقل ``databases/kartable.db`` (مستقل از دیتابیس‌های دستگاه‌های شبکه است تا
با تغییر دیتابیسِ فعالِ اسکن، آیتم‌های اداری از بین نروند). در اولین استفاده، جدول‌ها
ساخته و اگر خالی باشند «یک رکورد نمونه برای هر بخش» درج می‌شود تا ذخیره‌سازی هر بخش
قابل تست باشد (درخواست کاربر — Task 32).

ساختار پوشه‌ها عیناً همان منوی کارتابل پروژه دژبان (frontend12.zip) است:
صندوق ورودی، نامه‌های اقدامی، رونوشت‌ها، پیش‌نویس‌ها، ارسال شده ها،
پیگیری و ارجاعات، بایگانی شخصی — هر یک با زیرپوشه‌های همان منو.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
KARTABLE_DB = _ROOT / "databases" / "kartable.db"

# منوی کارتابل — دقیقاً مطابق kartableMenu در کارتابل فایل زیپ (دژبان)
FOLDERS: dict[str, list[str]] = {
    "صندوق ورودی": ["جهت اقدام", "جهت استحضار", "جهت پیگیری"],
    "نامه‌های اقدامی": [
        "جهت اقدام", "جهت استحضار", "جهت پیگیری", "جهت بایگانی", "جهت مذاکره",
        "جهت اطلاع", "جهت امضا", "ارجاع به دبیرخانه جهت...", "جهت عودت",
    ],
    "رونوشت‌ها": ["جهت اطلاع", "جهت استحضار"],
    "پیش‌نویس‌ها": ["پیش‌نویس‌های من", "پیش‌نویس‌های ارجاعی"],
    "ارسال شده ها": [
        "جهت اقدام", "جهت استحضار", "جهت پیگیری", "جهت بایگانی", "جهت مذاکره",
        "جهت اطلاع", "جهت امضا", "ارجاع به دبیرخانه جهت...", "جهت عودت",
    ],
    "پیگیری و ارجاعات": ["فعال", "بایگانی‌شده"],
    "بایگانی شخصی": ["پوشه محرمانه", "پوشه عمومی"],
}

_UPDATABLE_FIELDS = {
    "folder", "subfolder", "subject", "sender", "letter_no", "letter_date",
    "confidentiality", "status", "body",
}

_READY = False


# ---------------- تبدیل تاریخ شمسی (همان الگوریتم smart_reports) ----------------

def gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    """Convert Gregorian date to Jalali using integer day arithmetic."""
    g_days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    j_days_in_month = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]
    gy -= 1600
    g_day_no = (365 * gy + (gy + 3) // 4 - (gy + 99) // 100 + (gy + 399) // 400)
    for month in range(1, gm):
        g_day_no += g_days_in_month[month - 1]
    if gm > 2 and ((gy % 4 == 0 and gy % 100 != 0) or gy % 400 == 0):
        g_day_no += 1
    g_day_no += gd - 1

    j_day_no = g_day_no - 79
    j_np = j_day_no // 12053
    j_day_no %= 12053
    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)
    j_day_no %= 1461
    if j_day_no >= 366:
        jy += (j_day_no - 1) // 365
        j_day_no = (j_day_no - 1) % 365
    jm = 1
    while jm <= 12 and j_day_no >= j_days_in_month[jm - 1]:
        j_day_no -= j_days_in_month[jm - 1]
        jm += 1
    return jy, jm, j_day_no + 1


def today_jalali() -> str:
    """تاریخ امروز به شمسی با قالب YYYY/MM/DD (پُر‌شده با صفر)."""
    n = datetime.now()
    jy, jm, jd = gregorian_to_jalali(n.year, n.month, n.day)
    return f"{jy:04d}/{jm:02d}/{jd:02d}"


# ---------------- اتصال و ساخت جدول‌ها ----------------

def _connect() -> sqlite3.Connection:
    KARTABLE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(KARTABLE_DB), timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def _seed_if_empty(conn: sqlite3.Connection) -> None:
    """اگر جدول‌ها خالی باشند، برای هر بخشِ کارتابل یک رکورد نمونه درج می‌شود."""
    today = today_jalali()
    n_items = conn.execute("SELECT COUNT(*) FROM kartable_items").fetchone()[0]
    if n_items == 0:
        samples = [
            ("صندوق ورودی", "جهت اقدام", "درخواست همکاری فنی برای به‌روزرسانی سوئیچ‌های سایت مرکزی",
             "دبیرخانه مرکزی", "۱۴۰۵/۲۳۱", today, "عادی", "خوانده‌نشده"),
            ("نامه‌های اقدامی", "جهت امضا", "ابلاغ دستورالعمل نگهداری تجهیزات شبکه",
             "مدیریت اداری", "۱۴۰۵/۱۹۸", today, "عادی", "خوانده‌نشده"),
            ("رونوشت‌ها", "جهت اطلاع", "رونوشت صورتجلسه کمیته فنی ماهانه",
             "دفتر مدیریت", "۱۴۰۵/۱۷۶", today, "عادی", "خوانده‌شده"),
            ("پیش‌نویس‌ها", "پیش‌نویس‌های من", "پاسخ به درخواست همکاری فنی سایت مرکزی",
             "", "", today, "عادی", "پیش‌نویس"),
            ("ارسال شده ها", "جهت اطلاع", "گزارش وضعیت پوشش شبکه سایت‌های تابعه",
             "واحد شبکه", "۱۴۰۵/۲۰۴", today, "عادی", "ارسال‌شده"),
            ("پیگیری و ارجاعات", "فعال", "پیگیری نصب آنتن بخش فناوری اطلاعات",
             "واحد شبکه", "۱۴۰۵/۲۲۰", today, "عادی", "در جریان"),
            ("بایگانی شخصی", "پوشه عمومی", "قرارداد پشتیبانی سخت‌افزار سال ۱۴۰۴",
             "واحد قراردادها", "۱۴۰۴/۹۸۷", today, "عادی", "بایگانی"),
            ("بایگانی شخصی", "پوشه محرمانه", "مکاتبات محرمانه کمیته امنیت شبکه",
             "دفتر مدیریت", "۱۴۰۵/۰۴۲", today, "محرمانه", "خوانده‌شده"),
        ]
        conn.executemany(
            "INSERT INTO kartable_items(folder,subfolder,subject,sender,letter_no,letter_date,"
            "confidentiality,status,body,created_at,updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            [(f, s, sub, snd, no, dt, conf, st, "", today, today) for f, s, sub, snd, no, dt, conf, st in samples],
        )
    n_ann = conn.execute("SELECT COUNT(*) FROM kartable_announcements").fetchone()[0]
    if n_ann == 0:
        conn.execute(
            "INSERT INTO kartable_announcements(title,body,attachment,created_at) VALUES (?,?,?,?)",
            ("اطلاعیه مهم اداری",
             "فرایند صدور و پیگیری گواهی‌های اشتغال به کار و فرم‌های پرسنلی از طریق انتخاب قالب استاندارد Word در سامانه فعال گردید.",
             "help.pdf", today),
        )
    n_evt = conn.execute("SELECT COUNT(*) FROM kartable_events").fetchone()[0]
    if n_evt == 0:
        conn.execute(
            "INSERT INTO kartable_events(event_date,title,note,created_at) VALUES (?,?,?,?)",
            (today, "جلسه اداری", "جلسه هم‌اندیشی مدیریت و واحدها", today),
        )


def ensure_ready() -> None:
    """ساخت جدول‌ها + نمونه‌های اولیه (فقط یک‌بار در طول عمر پروسه)."""
    global _READY
    if _READY:
        return
    with _connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS kartable_items(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder TEXT NOT NULL,
                subfolder TEXT NOT NULL DEFAULT '',
                subject TEXT NOT NULL,
                sender TEXT NOT NULL DEFAULT '',
                letter_no TEXT NOT NULL DEFAULT '',
                letter_date TEXT NOT NULL DEFAULT '',
                confidentiality TEXT NOT NULL DEFAULT 'عادی',
                status TEXT NOT NULL DEFAULT 'خوانده‌نشده',
                body TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT ''
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS kartable_announcements(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL DEFAULT '',
                attachment TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT ''
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS kartable_events(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_date TEXT NOT NULL,
                title TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT ''
            )"""
        )
        _seed_if_empty(conn)
    _READY = True


def reset_for_tests(path=None) -> None:
    """برای تست‌ها: تغییر مسیر دیتابیس و اجبار به ساخت/بذرگیری مجدد."""
    global _READY, KARTABLE_DB
    if path is not None:
        KARTABLE_DB = Path(path)
    _READY = False


# ---------------- آیتم‌های کارتابل (نامه/یادداشت) ----------------

def _row_to_item(row) -> dict:
    return {k: row[k] for k in (
        "id", "folder", "subfolder", "subject", "sender", "letter_no", "letter_date",
        "confidentiality", "status", "body", "created_at", "updated_at")}


def list_items(folder: str | None = None, subfolder: str | None = None) -> list[dict]:
    ensure_ready()
    sql = "SELECT * FROM kartable_items WHERE 1=1"
    args: list = []
    if folder:
        sql += " AND folder = ?"
        args.append(folder)
    if subfolder:
        sql += " AND subfolder = ?"
        args.append(subfolder)
    sql += " ORDER BY id DESC"
    with _connect() as conn:
        return [_row_to_item(r) for r in conn.execute(sql, args).fetchall()]


def create_item(folder: str, subject: str, subfolder: str = "", sender: str = "",
                letter_no: str = "", letter_date: str = "", confidentiality: str = "عادی",
                status: str = "خوانده‌نشده", body: str = "") -> dict:
    ensure_ready()
    if folder not in FOLDERS:
        raise ValueError(f"پوشهٔ نامعتبر: {folder}")
    if subfolder and subfolder not in FOLDERS.get(folder, []):
        raise ValueError(f"زیرپوشهٔ نامعتبر برای «{folder}»: {subfolder}")
    now = today_jalali()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO kartable_items(folder,subfolder,subject,sender,letter_no,letter_date,"
            "confidentiality,status,body,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (folder, subfolder or "", subject, sender, letter_no, letter_date or now,
             confidentiality or "عادی", status or "خوانده‌نشده", body, now, now),
        )
        item_id = cur.lastrowid
    return {"ok": True, "id": item_id, "item": get_item(item_id)}


def get_item(item_id: int) -> dict | None:
    ensure_ready()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM kartable_items WHERE id = ?", (item_id,)).fetchone()
        return _row_to_item(row) if row else None


def update_item(item_id: int, fields: dict) -> dict | None:
    ensure_ready()
    patch = {k: v for k, v in (fields or {}).items() if k in _UPDATABLE_FIELDS and v is not None}
    if "folder" in patch and patch["folder"] not in FOLDERS:
        raise ValueError(f"پوشهٔ نامعتبر: {patch['folder']}")
    if not patch:
        return get_item(item_id)
    sets = ", ".join(f"{k} = ?" for k in patch)
    args = list(patch.values()) + [today_jalali(), item_id]
    with _connect() as conn:
        cur = conn.execute(f"UPDATE kartable_items SET {sets}, updated_at = ? WHERE id = ?", args)
        if cur.rowcount == 0:
            return None
    return get_item(item_id)


def delete_item(item_id: int) -> bool:
    ensure_ready()
    with _connect() as conn:
        cur = conn.execute("DELETE FROM kartable_items WHERE id = ?", (item_id,))
        return cur.rowcount > 0


def summary() -> dict:
    """آمار کارت بنفش «گزارش مکاتبات اداری» + شمارندهٔ بج‌های منو."""
    ensure_ready()
    with _connect() as conn:
        one = lambda sql, args=(): conn.execute(sql, args).fetchone()[0]  # noqa: E731
        data = {
            "unread": one("SELECT COUNT(*) FROM kartable_items WHERE folder='صندوق ورودی' AND status='خوانده‌نشده'"),
            "confidential": one("SELECT COUNT(*) FROM kartable_items WHERE confidentiality='محرمانه'"),
            "total_inbox": one("SELECT COUNT(*) FROM kartable_items WHERE folder='صندوق ورودی'"),
            "drafts": one("SELECT COUNT(*) FROM kartable_items WHERE folder='پیش‌نویس‌ها'"),
            "items_total": one("SELECT COUNT(*) FROM kartable_items"),
            "announcements": one("SELECT COUNT(*) FROM kartable_announcements"),
            "events": one("SELECT COUNT(*) FROM kartable_events"),
        }
        data["folders"] = {f: one("SELECT COUNT(*) FROM kartable_items WHERE folder=?", (f,)) for f in FOLDERS}
        return data


# ---------------- اطلاعیه‌ها ----------------

def list_announcements() -> list[dict]:
    ensure_ready()
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM kartable_announcements ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def create_announcement(title: str, body: str = "", attachment: str = "") -> dict:
    ensure_ready()
    now = today_jalali()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO kartable_announcements(title,body,attachment,created_at) VALUES (?,?,?,?)",
            (title, body, attachment, now),
        )
        ann_id = cur.lastrowid
    with _connect() as conn:
        row = conn.execute("SELECT * FROM kartable_announcements WHERE id = ?", (ann_id,)).fetchone()
        return {"ok": True, "id": ann_id, "announcement": dict(row)}


# ---------------- رویدادهای تقویم کاری ----------------

def list_events() -> list[dict]:
    ensure_ready()
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM kartable_events ORDER BY event_date ASC, id ASC").fetchall()
        return [dict(r) for r in rows]


def create_event(event_date: str, title: str, note: str = "") -> dict:
    ensure_ready()
    if len(event_date) != 10 or event_date.count("/") != 2:
        raise ValueError("قالب تاریخ باید شمسی و به شکل YYYY/MM/DD باشد")
    now = today_jalali()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO kartable_events(event_date,title,note,created_at) VALUES (?,?,?,?)",
            (event_date, title, note, now),
        )
        evt_id = cur.lastrowid
    with _connect() as conn:
        row = conn.execute("SELECT * FROM kartable_events WHERE id = ?", (evt_id,)).fetchone()
        return {"ok": True, "id": evt_id, "event": dict(row)}
