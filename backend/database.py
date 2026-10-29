# -*- coding: utf-8 -*-
"""
مدیریت دیتابیس متمرکز (Single Database)

معماری:
  - یک فایل SQLite واحد: data/co_db.db
  - جدول companies : شرکت‌های تابعه (کد سه‌رقمی از ۱۰۰)
  - جدول personnel و بقیه جداول عملیاتی در همان دیتابیس
  - فیلتر چندشرکتی با ستون company_code (نه فایل جدا)

مزیت: بدون همگام‌سازی بین چند فایل، تراکنش یکپارچه، بک‌آپ ساده، بدون ریسک
ناهماهنگی schema بین co_XXX.db ها.

سازگاری: get_company_db() همچنان وجود دارد ولی به همان دیتابیس مرکزی وصل می‌شود.
"""
import os
import re
import sqlite3
import unicodedata
from contextlib import contextmanager
from datetime import datetime

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_DIR, "data")
# دیتابیس واحد متمرکز
MAIN_DB = os.path.join(DATA_DIR, "co_db.db")
# نام قدیمی برای سازگاری importهای احتمالی
COMPANIES_DB = MAIN_DB
# مسیر پیش‌فرض ریشه مدارک پرسنل (قابل تغییر از تنظیمات برنامه)
DEFAULT_DOCS_ROOT = os.path.join(APP_DIR, "docs")
SETTING_DOCS_ROOT = "personnel_docs_root"

# کد شرکت‌ها از این عدد شروع می‌شود
COMPANY_CODE_START = 100

# ──────────────────────────────────────────────
# سیاست داده (الزامی):
# جداول «اطلاعات پایه» منبع حقیقت (Source of Truth) برای مقادیر مرجع هستند.
# هر فیلد در سایر برگه‌ها که معادلش در اطلاعات پایه است (مثل رشته تحصیلی)
# باید حتماً مقدارش از API اطلاعات پایه خوانده شود — نه متن آزاد و نه hard-code.
# از units / education_fields / LOOKUP_TABLES / baseinfo entities استفاده کنید.
# جزئیات: docs/ARCHITECTURE.md
# ──────────────────────────────────────────────

PERSONAL_FIELDS = [
    # — هویتی —
    ("row_num", "ردیف"),
    ("indicator_num", "کد پرسنلی"),
    ("first_name", "نام"),
    ("last_name", "نام خانوادگی"),
    ("previous_last_name", "نام خانوادگی سابق"),
    ("nickname", "نام نانبر"),
    ("nickname_family", "نام خانوادگی نانبر"),
    ("father_name", "نام پدر"),
    ("national_id", "کد ملی"),
    ("id_cert_number", "شماره شناسنامه"),
    ("id_cert_place", "محل صدور شناسنامه"),
    ("gender", "جنسیت"),
    ("birth_date", "تاریخ تولد"),
    ("birth_place", "محل تولد"),
    ("religion", "دین"),
    ("denomination", "مذهب"),
    ("blood_type", "گروه خونی"),
    ("nationality", "تابعیت"),
    ("marital_status", "وضعیت تاهل"),
    ("children_count", "تعداد فرزندان"),
    ("is_native", "بومی"),
    # — شغلی —
    ("company_code", "کد شرکت"),
    ("company", "شرکت"),
    ("center", "مرکز"),
    ("department", "واحد"),
    ("position", "سمت"),
    ("workplace", "محل خدمت"),
    ("room_floor", "اتاق/طبقه"),
    ("rank", "رتبه"),
    ("membership_type", "نوع عضویت"),
    ("responsibility_group", "گروه مسئولیت"),
    ("hire_date", "تاریخ استخدام"),
    ("employment_type", "نوع استخدام"),
    ("education_degree", "مدرک تحصیلی"),
    ("education_field", "رشته تحصیلی"),
    ("military_status", "نظام وظیفه"),
    ("military_exemption_type", "نوع معافیت نظام وظیفه"),
    ("is_retired", "بازنشسته"),
    ("active_status", "فعال/غیرفعال"),
    # — تماس —
    ("phone", "تلفن همراه"),
    ("landline", "تلفن ثابت"),
    ("internal_phone1", "داخلی ۱"),
    ("internal_phone2", "داخلی ۲"),
    ("internal_phone3", "داخلی ۳"),
    ("email", "ایمیل"),
    ("postal_code", "کد پستی"),
    ("address", "آدرس منزل"),
    ("issued_from", "صادره"),
    # — کارت و گواهینامه —
    ("card_number", "شماره کارت"),
    ("card_status", "وضعیت کارت"),
    ("time_card_code", "کد کارت ساعت"),
    ("validity_start", "تاریخ شروع اعتبار"),
    ("validity_end", "تاریخ پایان اعتبار"),
    ("card_return_date", "تاریخ عودت کارت"),
    ("return_code", "کد/متن عودت"),
    ("license_type", "نوع گواهینامه"),
    ("license_number", "شماره گواهینامه"),
    ("license_issue_place", "محل صدور گواهینامه"),
    ("access_group", "مجموعه دسترسی"),
    ("online_display_name", "نام نمایشی آنلاین"),
    ("print_count", "دفعات چاپ"),
    # — محدودیت‌ها —
    ("banned_entry", "ممنوع‌الورود"),
    ("banned_security", "ممنوع انتظامات"),
    ("settlement_done", "تسویه حساب"),
    ("show_on_internet", "نمایش در اینترنت"),
    ("description", "توضیحات"),
    ("photo", "عکس"),
    ("signature", "امضا"),
]


def normalize_for_search(text: str) -> str:
    """نرمال‌سازی متن برای جستجو (فارسی/عربی، ارقام، نیم‌فاصله)."""
    if not text:
        return ""
    t = str(text).strip()
    digits = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    t = t.translate(digits)
    t = (
        t.replace("ي", "ی")
        .replace("ك", "ک")
        .replace("ة", "ه")
        .replace("أ", "ا")
        .replace("إ", "ا")
        .replace("آ", "ا")
        .replace("\u200c", "")
        .replace("\u200d", "")
        .replace("\u0640", "")
    )
    return t


def normalize_national_id(raw) -> str:
    if raw is None:
        return ""
    text = str(raw).strip()
    digits = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    text = text.translate(digits).replace(" ", "").replace("-", "")
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    if text.isdigit() and 8 <= len(text) <= 9:
        text = text.zfill(10)
    return text


def row_to_dict(row) -> dict:
    if row is None:
        return {}
    return dict(row)


def company_db_path(company_code: int = None) -> str:
    """
    مسیر دیتابیس — همیشه دیتابیس متمرکز.
    پارامتر company_code فقط برای سازگاری API قدیمی نگه داشته شده است.
    """
    return MAIN_DB


def _tune_sqlite(conn: sqlite3.Connection) -> None:
    """تنظیمات عملکردی SQLite برای خواندن/نوشتن بهتر."""
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=30000")
        # حدود ۶۴MB کش صفحه در حافظه
        conn.execute("PRAGMA cache_size=-64000")
        conn.execute("PRAGMA mmap_size=268435456")
    except Exception:
        pass


@contextmanager
def get_main_db():
    """اتصال به دیتابیس واحد متمرکز (co_db.db)."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(MAIN_DB, timeout=60)
    conn.row_factory = sqlite3.Row
    _tune_sqlite(conn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_companies_db():
    """سازگاری با نام قبلی — همان دیتابیس متمرکز."""
    with get_main_db() as conn:
        yield conn


@contextmanager
def get_company_db(company_code: int = None):
    """
    سازگاری با API قبلی.
    دیگر فایل co_XXX جدا باز نمی‌شود؛ همه به co_db.db وصل می‌شوند.
    فیلتر شرکت در لایه کوئری با company_code انجام می‌شود.
    """
    with get_main_db() as conn:
        yield conn




# حروف مجاز پلاک ملی ایران (بدون حروف رزرو شده غیررایج)
IRAN_PLATE_LETTERS = (
    "الف", "ب", "پ", "ت", "ث", "ج", "د", "ز", "س", "ش", "ص", "ط",
    "ع", "ف", "ق", "ک", "گ", "ل", "م", "ن", "و", "ه", "ی",
    "ا",  # گاهی به‌جای الف
)

def normalize_iran_plate(value: str) -> str:
    """
    نرمال‌سازی شماره پلاک ایران به فرمت استاندارد:
    «۱۲ ب ۳۴۵ - ۶۷»  (دو رقم + حرف + سه رقم + خط تیره + دو رقم سری/منطقه)
    ورودی‌های بدون فاصله/با ارقام لاتین هم پذیرفته می‌شوند.
    """
    if value is None:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    # ارقام فارسی/عربی → لاتین برای پردازش
    trans = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    s2 = s.translate(trans)
    # حذف جداکننده‌ها
    cleaned = (
        s2.replace(" ", "").replace("-", "").replace("_", "")
        .replace("ایران", "").replace("IRAN", "").replace("Iran", "")
        .replace("|", "").replace("ـ", "")
    )
    # استخراج حرف (یک یا چند کاراکتر غیرعددی متوالی در وسط)
    import re
    m = re.match(r"^(\d{2})([^\d]{1,3})(\d{3})(\d{2})$", cleaned)
    if not m:
        # اگر از قبل فرمت درست ذخیره شده فقط فاصله‌ها را یکدست کن
        m2 = re.match(r"^(\d{1,2})\s*([^\d\s\-]{1,3})\s*(\d{1,3})\s*-?\s*(\d{1,2})$", s2.strip())
        if not m2:
            return s  # بدون تغییر اجباری اگر قابل تشخیص نبود
        a, letter, b, c = m2.groups()
    else:
        a, letter, b, c = m.groups()
    letter = letter.strip()
    # تبدیل ارقام به فارسی برای نمایش یکدست
    fa = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    a = a.zfill(2).translate(fa)
    b = b.zfill(3).translate(fa)
    c = c.zfill(2).translate(fa)
    return f"{a} {letter} {b} - {c}"


def is_valid_iran_plate(value: str) -> bool:
    """اعتبارسنجی ساده پلاک ایران پس از نرمال‌سازی."""
    import re
    n = normalize_iran_plate(value)
    if not n or n == str(value).strip() and not re.search(r"\d", n):
        # اگر normalize چیزی نساخته
        pass
    return bool(re.match(
        r"^[۰-۹]{2}\s+\S{1,3}\s+[۰-۹]{3}\s+-\s+[۰-۹]{2}$",
        normalize_iran_plate(value),
    ))


def _norm_company_code(code) -> str:
    """یکدست‌سازی کد شرکت به‌صورت رشته — برای استفاده مؤثر از ایندکس."""
    if code is None or code == "":
        return ""
    try:
        return str(int(code))
    except (TypeError, ValueError):
        return str(code).strip()


def _ensure_personnel_indexes(conn):
    """
    ایندکس‌های پرسنل — اولویت با مسیرهای داغ:
    - فیلتر شرکت + صفحه‌بندی (company_code, id)
    - جستجوی کدملی / کد پرسنلی / تلفن
    - فیلتر وضعیت و واحد/مرکز
    """
    stmts = [
        # مسیر اصلی لیست: WHERE company_code=? ORDER BY id DESC
        "CREATE INDEX IF NOT EXISTS idx_pers_company_id ON personnel(company_code, id DESC)",
        # جستجو
        "CREATE INDEX IF NOT EXISTS idx_pers_national_id ON personnel(national_id)",
        "CREATE INDEX IF NOT EXISTS idx_pers_indicator ON personnel(indicator_num)",
        "CREATE INDEX IF NOT EXISTS idx_pers_phone ON personnel(phone)",
        "CREATE INDEX IF NOT EXISTS idx_pers_last_name ON personnel(last_name)",
        "CREATE INDEX IF NOT EXISTS idx_pers_first_name ON personnel(first_name)",
        # فیلترهای فرم/گزارش
        "CREATE INDEX IF NOT EXISTS idx_pers_company_active ON personnel(company_code, active_status)",
        "CREATE INDEX IF NOT EXISTS idx_pers_company_dept ON personnel(company_code, department)",
        "CREATE INDEX IF NOT EXISTS idx_pers_center ON personnel(center)",
        "CREATE INDEX IF NOT EXISTS idx_pers_position ON personnel(position)",
    ]
    for s in stmts:
        conn.execute(s)
    # حذف ایندکس‌های قدیمی تکراری (نام‌گذاری قبلی)
    for legacy in (
        "idx_personnel_national_id", "idx_personnel_last_name", "idx_personnel_first_name",
        "idx_personnel_phone", "idx_personnel_indicator", "idx_personnel_position",
        "idx_personnel_department", "idx_personnel_active", "idx_personnel_company_code",
        "idx_personnel_id_desc",
    ):
        conn.execute(f"DROP INDEX IF EXISTS {legacy}")


def _ensure_all_indexes(conn):
    """ایندکس همه جداول عملیاتی و اطلاعات پایه."""
    _ensure_personnel_indexes(conn)

    # وابستگان / کارت
    conn.execute("CREATE INDEX IF NOT EXISTS idx_dep_personnel ON dependents(personnel_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_dep_national ON dependents(national_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_card_personnel ON access_cards(personnel_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_card_number ON access_cards(card_number)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_card_status ON access_cards(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_card_personnel_status ON access_cards(personnel_id, status)")

    # واحدها
    conn.execute("CREATE INDEX IF NOT EXISTS idx_units_center ON units(center_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_units_name ON units(name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_units_company ON units(company_code)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_units_center_name ON units(center_name, name)")

    # درب و دسترسی
    conn.execute("CREATE INDEX IF NOT EXISTS idx_doors_active ON access_doors(is_active)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_doors_code ON access_doors(code)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_doors_center ON access_doors(center_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_doors_name ON access_doors(name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_door_access_door ON door_user_access(door_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_door_access_user ON door_user_access(user_name)")

    # سایر اطلاعات پایه
    conn.execute("CREATE INDEX IF NOT EXISTS idx_goods_name ON goods_destinations(name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_clients_code ON client_companies(code)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_clients_name ON client_companies(name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_services_name ON services(name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_entry_exit_name ON entry_exit_types(name)")

    # شرکت‌ها (علاوه بر UNIQUE code)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_companies_active ON companies(is_active)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name)")


def _init_personnel_schema(conn):
    """ایجاد جدول پرسنل داخل دیتابیس شرکت"""
    personal_cols = [f"{name} TEXT" for name, _ in PERSONAL_FIELDS if name != "photo"]
    cols_sql = ", ".join(personal_cols)
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS personnel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {cols_sql},
            photo TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    existing = {r[1] for r in conn.execute("PRAGMA table_info(personnel)").fetchall()}
    for name, _ in PERSONAL_FIELDS:
        if name not in existing:
            if name == "photo":
                conn.execute("ALTER TABLE personnel ADD COLUMN photo TEXT DEFAULT ''")
            else:
                conn.execute(f"ALTER TABLE personnel ADD COLUMN {name} TEXT")
    if "photo" not in existing:
        conn.execute("ALTER TABLE personnel ADD COLUMN photo TEXT DEFAULT ''")
    if "created_at" not in existing:
        conn.execute("ALTER TABLE personnel ADD COLUMN created_at TEXT")
    if "updated_at" not in existing:
        conn.execute("ALTER TABLE personnel ADD COLUMN updated_at TEXT")

    _ensure_personnel_indexes(conn)



def _init_personnel_records_schema(conn):
    """سوابق خدماتی، سفر خارجی و پزشکی پرسنل"""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS personnel_service_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            personnel_id INTEGER NOT NULL,
            from_date TEXT DEFAULT '',
            to_date TEXT DEFAULT '',
            organization TEXT DEFAULT '',
            position TEXT DEFAULT '',
            unit_name TEXT DEFAULT '',
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT '',
            updated_at TEXT DEFAULT '',
            FOREIGN KEY (personnel_id) REFERENCES personnel(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS personnel_travel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            personnel_id INTEGER NOT NULL,
            country TEXT DEFAULT '',
            from_date TEXT DEFAULT '',
            to_date TEXT DEFAULT '',
            purpose TEXT DEFAULT '',
            visa_no TEXT DEFAULT '',
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT '',
            updated_at TEXT DEFAULT '',
            FOREIGN KEY (personnel_id) REFERENCES personnel(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS personnel_medical (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            personnel_id INTEGER NOT NULL,
            record_date TEXT DEFAULT '',
            record_type TEXT DEFAULT '',
            diagnosis TEXT DEFAULT '',
            physician TEXT DEFAULT '',
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT '',
            updated_at TEXT DEFAULT '',
            FOREIGN KEY (personnel_id) REFERENCES personnel(id) ON DELETE CASCADE
        )
        """
    )
    for tname in ("personnel_service_history", "personnel_travel", "personnel_medical"):
        try:
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{tname}_pid ON {tname}(personnel_id)")
        except Exception:
            pass


def _init_dependents_schema(conn):
    """جدول وابستگان پرسنل"""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dependents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            personnel_id INTEGER NOT NULL,
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            national_id TEXT DEFAULT '',
            relation TEXT DEFAULT '',
            birth_date TEXT DEFAULT '',
            gender TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            description TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (personnel_id) REFERENCES personnel(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_dep_personnel ON dependents(personnel_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_dep_national ON dependents(national_id)")


def _init_cards_schema(conn):
    """جدول کارت‌های شناسایی پرسنل"""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS access_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            personnel_id INTEGER NOT NULL,
            card_number TEXT DEFAULT '',
            card_type TEXT DEFAULT 'شناسایی',
            issue_date TEXT DEFAULT '',
            expiry_date TEXT DEFAULT '',
            status TEXT DEFAULT 'فعال',
            printed INTEGER DEFAULT 0,
            description TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (personnel_id) REFERENCES personnel(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_card_personnel ON access_cards(personnel_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_card_number ON access_cards(card_number)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_card_status ON access_cards(status)")



def _migrate_legacy_company_dbs():
    """
    اگر از نسخهٔ چندفایلی (co_XXX.db) داده مانده باشد، یک‌بار به co_db.db منتقل می‌شود.
    """
    flag = get_setting("legacy_co_db_migrated", "")
    if flag == "1":
        return
    if not os.path.isdir(DATA_DIR):
        set_setting("legacy_co_db_migrated", "1")
        return

    ensure_company_database()
    migrated_any = False
    for fname in os.listdir(DATA_DIR):
        if not (fname.startswith("co_") and fname.endswith(".db")):
            continue
        raw = fname[3:-3]
        if not raw.isdigit():
            continue
        code = int(raw)
        src = os.path.join(DATA_DIR, fname)
        try:
            src_conn = sqlite3.connect(src, timeout=30)
            src_conn.row_factory = sqlite3.Row
        except Exception:
            continue
        try:
            tables = {
                r[0]
                for r in src_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            with get_main_db() as dst:
                if "personnel" in tables:
                    for row in src_conn.execute("SELECT * FROM personnel").fetchall():
                        d = dict(row)
                        d["company_code"] = str(d.get("company_code") or code)
                        # جلوگیری از تکرار با national_id+company
                        nid = d.get("national_id") or ""
                        exists = None
                        if nid:
                            exists = dst.execute(
                                "SELECT id FROM personnel WHERE national_id=? AND company_code=?",
                                (nid, _norm_company_code(code)),
                            ).fetchone()
                        if exists:
                            continue
                        cols = [c for c in d.keys() if c != "id"]
                        placeholders = ", ".join(["?"] * len(cols))
                        dst.execute(
                            f"INSERT INTO personnel ({', '.join(cols)}) VALUES ({placeholders})",
                            [d.get(c) for c in cols],
                        )
                        migrated_any = True
                if "dependents" in tables:
                    for row in src_conn.execute("SELECT * FROM dependents").fetchall():
                        d = dict(row)
                        cols = [c for c in d.keys() if c != "id"]
                        try:
                            dst.execute(
                                f"INSERT INTO dependents ({', '.join(cols)}) VALUES ({', '.join(['?']*len(cols))})",
                                [d.get(c) for c in cols],
                            )
                            migrated_any = True
                        except Exception:
                            pass
                if "access_cards" in tables:
                    for row in src_conn.execute("SELECT * FROM access_cards").fetchall():
                        d = dict(row)
                        cols = [c for c in d.keys() if c != "id"]
                        try:
                            dst.execute(
                                f"INSERT INTO access_cards ({', '.join(cols)}) VALUES ({', '.join(['?']*len(cols))})",
                                [d.get(c) for c in cols],
                            )
                            migrated_any = True
                        except Exception:
                            pass
        finally:
            src_conn.close()

    # مهاجرت companies.db قدیمی اگر جدا بود
    old_companies = os.path.join(DATA_DIR, "companies.db")
    if os.path.isfile(old_companies) and os.path.abspath(old_companies) != os.path.abspath(MAIN_DB):
        try:
            src = sqlite3.connect(old_companies, timeout=30)
            src.row_factory = sqlite3.Row
            with get_main_db() as dst:
                for tbl in (
                    "companies", "units", "education_fields", "responsibility_groups",
                    "employment_types", "app_settings", "services", "access_doors",
                    "goods_destinations", "client_companies", "entry_exit_types",
                    "door_user_access",
                ):
                    try:
                        rows = src.execute(f"SELECT * FROM {tbl}").fetchall()
                    except Exception:
                        continue
                    for row in rows:
                        d = dict(row)
                        cols = [c for c in d.keys() if c != "id"]
                        if not cols:
                            continue
                        try:
                            if tbl == "companies" and d.get("code") is not None:
                                ex = dst.execute("SELECT id FROM companies WHERE code=?", (d["code"],)).fetchone()
                                if ex:
                                    continue
                            dst.execute(
                                f"INSERT INTO {tbl} ({', '.join(cols)}) VALUES ({', '.join(['?']*len(cols))})",
                                [d.get(c) for c in cols],
                            )
                            migrated_any = True
                        except Exception:
                            pass
            src.close()
        except Exception:
            pass

    set_setting("legacy_co_db_migrated", "1")
    return migrated_any


_SCHEMA_READY = False

def ensure_company_database(company_code: int = None) -> str:
    """
    اطمینان از وجود اسکیمای جداول عملیاتی در دیتابیس متمرکز.
    پس از اولین بار، دیگر CREATE TABLE تکراری اجرا نمی‌شود (سریع‌تر).
    """
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return MAIN_DB
    with get_main_db() as conn:
        _init_personnel_schema(conn)
        _init_dependents_schema(conn)
        _init_personnel_records_schema(conn)
        _init_cards_schema(conn)
        _init_lookup_tables(conn)
    _SCHEMA_READY = True
    return MAIN_DB


def _ensure_settings_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT
        )
        """
    )


def get_setting(key: str, default: str = "") -> str:
    """خواندن یک تنظیم از companies.db"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with get_companies_db() as conn:
        _ensure_settings_table(conn)
        row = conn.execute(
            "SELECT value FROM app_settings WHERE key=?", (key,)
        ).fetchone()
        if row is None:
            return default
        return str(row["value"] if isinstance(row, sqlite3.Row) else row[0] or default)


def set_setting(key: str, value: str) -> str:
    """ذخیره یک تنظیم در companies.db"""
    os.makedirs(DATA_DIR, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_companies_db() as conn:
        _ensure_settings_table(conn)
        conn.execute(
            """
            INSERT INTO app_settings (key, value, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
            """,
            (key, value, now),
        )
    return value


def get_docs_root() -> str:
    """
    مسیر ریشه فولدرهای پرسنل.
    ساختار: docs_root / نام شرکت تابعه / کدملی / مدارک و عکس
    """
    stored = get_setting(SETTING_DOCS_ROOT, "").strip()
    if stored:
        return os.path.abspath(stored)
    return os.path.abspath(DEFAULT_DOCS_ROOT)


def set_docs_root(path: str) -> str:
    """تنظیم مسیر ریشه مدارک پرسنل و ایجاد پوشه در صورت نیاز."""
    path = (path or "").strip()
    if not path:
        path = DEFAULT_DOCS_ROOT
    abs_path = os.path.abspath(path)
    os.makedirs(abs_path, exist_ok=True)
    set_setting(SETTING_DOCS_ROOT, abs_path)
    return abs_path


def safe_folder_name(name: str, fallback: str = "Unknown") -> str:
    """
    نام امن برای فولدر با نرمال‌سازی یونیکد فارسی.
    - NFC برای یکسان‌سازی کدپوینت‌ها
    - یکسان‌سازی ی/ک عربی به فارسی
    - حذف کاراکترهای غیرمجاز ویندوز/لینوکس و کنترل‌کاراکترها
    """
    n = (name or "").strip()
    if not n:
        return fallback
    # نرمال‌سازی یونیکد (جلوگیری از فرم‌های ترکیبی متفاوت)
    n = unicodedata.normalize("NFC", n)
    # ی و ک عربی → فارسی (جلوگیری از دو فولدر متفاوت برای یک نام)
    n = (
        n.replace("ي", "ی")
        .replace("ك", "ک")
        .replace("ة", "ه")
        .replace("ؤ", "و")
        .replace("ئ", "ی")
    )
    # حذف کنترل‌کاراکتر، جداکننده‌های صفرعرض و کاراکترهای ممنوع مسیر
    n = re.sub(r"[\x00-\x1f\x7f/*?:\"<>|\\\\]", "", n)
    n = n.replace("\u200c", "").replace("\u200d", "").replace("\u0640", "")
    n = n.strip().strip(". ")
    if not n:
        n = fallback
    if len(n) > 180:
        n = n[:180].rstrip(". ")
    return n or fallback


def company_docs_folder(company_name: str = "", company_code=None, create: bool = True) -> str:
    """
    مسیر فولدر یک شرکت تابعه زیر ریشه مدارک:
    docs_root / نام شرکت
    """
    root = get_docs_root()
    label = (company_name or "").strip()
    if not label and company_code is not None:
        try:
            c = get_company_by_code(int(company_code))
            if c:
                label = c.get("name") or ""
        except Exception:
            label = ""
    if not label:
        label = f"Company_{company_code}" if company_code is not None else "Unknown"
    safe = safe_folder_name(label, fallback=f"Company_{company_code or 'X'}")
    folder = os.path.join(root, safe)
    if create:
        os.makedirs(folder, exist_ok=True)
    return folder


def person_docs_folder(
    national_id: str,
    company_name: str = "",
    company_code=None,
    create: bool = True,
) -> str:
    """
    مسیر فولدر یک پرسنل:
    docs_root / نام شرکت تابعه / کدملی
    """
    nid = normalize_national_id(national_id)
    if not nid:
        raise ValueError("کد ملی برای ساخت فولدر الزامی است")
    comp_folder = company_docs_folder(
        company_name=company_name,
        company_code=company_code,
        create=create,
    )
    folder = os.path.join(comp_folder, nid)
    if create:
        os.makedirs(folder, exist_ok=True)
    return folder


# ─── کاتالوگ/ایندکس فولدرهای مدارک (برای جلوگیری از ساخت تکراری) ───

FOLDER_INDEX_NAME = ".folder_index.json"


def _folder_index_path() -> str:
    return os.path.join(get_docs_root(), FOLDER_INDEX_NAME)


def load_folder_index() -> dict:
    """بارگذاری ایندکس نقشه فولدرها از زیر ریشه مدارک."""
    path = _folder_index_path()
    root = os.path.abspath(get_docs_root())
    empty = {
        "docs_root": root,
        "updated_at": "",
        "paths": [],  # مسیرهای نسبی موجود: "شرکت" و "شرکت/کدملی"
        "companies": {},  # code -> folder name
        "personnel": {},  # "code:nid" -> relative path
    }
    if not os.path.isfile(path):
        return empty
    try:
        import json
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return empty
        # اگر مسیر ریشه عوض شده، ایندکس نامعتبر است
        if os.path.abspath(str(data.get("docs_root") or "")) != root:
            return empty
        data.setdefault("paths", [])
        data.setdefault("companies", {})
        data.setdefault("personnel", {})
        data["docs_root"] = root
        return data
    except Exception:
        return empty


def save_folder_index(index: dict) -> None:
    """ذخیره ایندکس نقشه فولدرها."""
    import json
    root = os.path.abspath(get_docs_root())
    os.makedirs(root, exist_ok=True)
    index = dict(index or {})
    index["docs_root"] = root
    index["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # یکتا کردن paths
    paths = index.get("paths") or []
    index["paths"] = sorted(set(str(p).replace("\\", "/").strip("/") for p in paths if p))
    path = _folder_index_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=0)


def scan_docs_paths() -> set:
    """
    یک‌بار پیمایش سطح‌۱ و سطح‌۲ ریشه مدارک:
    شرکت‌ها + کدملی‌ها → مجموعه مسیرهای نسبی موجود.
    """
    root = get_docs_root()
    os.makedirs(root, exist_ok=True)
    found = set()
    try:
        for name in os.listdir(root):
            if name.startswith("."):
                continue
            comp_path = os.path.join(root, name)
            if not os.path.isdir(comp_path):
                continue
            found.add(name)
            try:
                for sub in os.listdir(comp_path):
                    if sub.startswith("."):
                        continue
                    sub_path = os.path.join(comp_path, sub)
                    if os.path.isdir(sub_path):
                        found.add(f"{name}/{sub}")
            except OSError:
                pass
    except OSError:
        pass
    return found


def ensure_path_from_index(rel_path: str, index_paths: set) -> bool:
    """
    اگر rel_path در ایندکس/دیسک نباشد، بساز و به مجموعه اضافه کن.
    برمی‌گرداند: True اگر تازه ساخته شد، False اگر از قبل بود.
    """
    rel = (rel_path or "").replace("\\", "/").strip().lstrip("/")
    if not rel:
        return False
    if rel in index_paths:
        # تأیید سریع وجود — فقط اگر شک داریم
        full = os.path.join(get_docs_root(), *rel.split("/"))
        if os.path.isdir(full):
            return False
        # ایندکس کهنه: مسیر نیست → بساز
        os.makedirs(full, exist_ok=True)
        index_paths.add(rel)
        return True
    full = os.path.join(get_docs_root(), *rel.split("/"))
    if os.path.isdir(full):
        index_paths.add(rel)
        return False
    os.makedirs(full, exist_ok=True)
    index_paths.add(rel)
    return True


def sync_all_docs_folders(rebuild_scan: bool = True) -> dict:
    """
    همگام‌سازی فولدر شرکت‌ها و پرسنل با دیتابیس.
    - با ایندکس/کاتالوگ از ساخت تکراری جلوگیری می‌کند
    - فقط مسیرهای غایب ساخته می‌شوند
    """
    root = get_docs_root()
    os.makedirs(root, exist_ok=True)

    index = load_folder_index()
    if rebuild_scan:
        disk_paths = scan_docs_paths()
        # ادغام با ایندکس قبلی
        index_paths = set(index.get("paths") or []) | disk_paths
    else:
        index_paths = set(index.get("paths") or [])
        if not index_paths:
            index_paths = scan_docs_paths()

    companies_map = dict(index.get("companies") or {})
    personnel_map = dict(index.get("personnel") or {})

    comps = list_companies()
    companies_created = 0
    companies_existed = 0
    personnel_created = 0
    personnel_existed = 0
    personnel_skipped_no_nid = 0

    for c in comps:
        c_code = c.get("code")
        c_name = str(c.get("name") or "").strip()
        if not c_code and not c_name:
            continue
        safe = safe_folder_name(
            c_name or f"Company_{c_code}",
            fallback=f"Company_{c_code or 'X'}",
        )
        companies_map[str(c_code)] = safe
        created = ensure_path_from_index(safe, index_paths)
        if created:
            companies_created += 1
        else:
            companies_existed += 1

        try:
            p_res = list_personnel(int(c_code), limit=5000)
            p_list = p_res.get("items", []) if isinstance(p_res, dict) else []
        except Exception:
            p_list = []

        for p in p_list:
            raw_nid = str(p.get("national_id") or "").strip()
            clean_nid = normalize_national_id(raw_nid) if raw_nid else ""
            if not clean_nid or clean_nid == "None":
                personnel_skipped_no_nid += 1
                continue
            rel = f"{safe}/{clean_nid}"
            key = f"{c_code}:{clean_nid}"
            personnel_map[key] = rel
            created = ensure_path_from_index(rel, index_paths)
            if created:
                personnel_created += 1
            else:
                personnel_existed += 1

    index["paths"] = sorted(index_paths)
    index["companies"] = companies_map
    index["personnel"] = personnel_map
    save_folder_index(index)

    return {
        "status": "success",
        "docs_path": root,
        "companies_created": companies_created,
        "companies_existed": companies_existed,
        "personnel_created": personnel_created,
        "personnel_existed": personnel_existed,
        "personnel_skipped_no_nid": personnel_skipped_no_nid,
        "index_entries": len(index_paths),
        "message": (
            f"بروزرسانی انجام شد: "
            f"{companies_created} شرکت جدید، {companies_existed} شرکت موجود؛ "
            f"{personnel_created} فولدر پرسنل جدید، {personnel_existed} موجود"
            + (f"؛ {personnel_skipped_no_nid} بدون کدملی رد شد" if personnel_skipped_no_nid else "")
            + f". (ایندکس: {len(index_paths)} مسیر)"
        ),
    }


def init_db():
    """راه‌اندازی دیتابیس متمرکز: جداول + شرکت‌های نمونه + مهاجرت در صورت نیاز."""
    os.makedirs(DATA_DIR, exist_ok=True)

    # مهاجرت نام فایل دیتابیس: dejban.db → co_db.db
    _old_db = os.path.join(DATA_DIR, "dejban.db")
    if os.path.isfile(_old_db) and not os.path.isfile(MAIN_DB):
        try:
            os.rename(_old_db, MAIN_DB)
        except Exception:
            pass


    # یک اتصال واحد — بدون فراخوانی توابعی که دوباره همان فایل را باز کنند
    with get_main_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                short_name TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                db_file TEXT NOT NULL,
                created_at TEXT,
                description TEXT DEFAULT '',
                parent_code INTEGER DEFAULT NULL
            )
            """
        )
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_companies_code ON companies(code)")

        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(companies)").fetchall()]
            if "parent_code" not in cols:
                conn.execute("ALTER TABLE companies ADD COLUMN parent_code INTEGER DEFAULT NULL")
            if "logo" not in cols:
                conn.execute("ALTER TABLE companies ADD COLUMN logo TEXT DEFAULT ''")
        except Exception:
            pass

        _ensure_settings_table(conn)
        _init_lookup_tables(conn)
        _init_personnel_schema(conn)
        _init_dependents_schema(conn)
        _init_personnel_records_schema(conn)
        _init_cards_schema(conn)
        _init_sys_access_schema(conn)
        _ensure_all_indexes(conn)
        # یکدست‌سازی company_code ذخیره‌شده (عدد → رشته) برای استفاده از ایندکس
        try:
            conn.execute(
                "UPDATE personnel SET company_code = CAST(company_code AS TEXT) "
                "WHERE typeof(company_code) = 'integer'"
            )
        except Exception:
            pass

        count = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        seed_codes = []
        if count == 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # سلسله‌مراتب: 100 ستاد → زیرمجموعه‌ها با parent_code=100
            samples = [
                (100, "تأسیسات دریایی ایران (ستاد)", "IOEC", "co_db.db", "ستاد مرکزی", None),
                (101, "شرکت مهندسی و ساخت تأسیسات دریایی ایران", "IOEC-OPS", "co_db.db", "عملیات دریایی", 100),
                (102, "شرکت خدمات پشتیبانی دریایی", "IOEC-SUP", "co_db.db", "پشتیبانی", 100),
                (103, "پایگاه عملیات خارک", "KHARG", "co_db.db", "پایگاه", 101),
                (104, "پایگاه عملیات عسلویه", "ASSAL", "co_db.db", "پایگاه", 101),
            ]
            for code, name, short, db_file, desc, parent in samples:
                conn.execute(
                    """
                    INSERT INTO companies (code, name, short_name, is_active, db_file, created_at, description, parent_code)
                    VALUES (?, ?, ?, 1, ?, ?, ?, ?)
                    """,
                    (code, name, short, db_file, now, desc, parent),
                )
                seed_codes.append((code, name))

    # seed بعد از بسته شدن اتصال اول
    for code, name in seed_codes:
        try:
            _seed_sample_personnel(code, name)
        except Exception:
            pass

    # فولدر مدارک
    try:
        os.makedirs(get_docs_root(), exist_ok=True)
        for c in list_companies(include_personnel_count=False):
            company_docs_folder(
                company_name=c.get("name") or "",
                company_code=c.get("code"),
                create=True,
            )
    except OSError:
        pass

    # مهاجرت از co_*.db قدیمی (پس از آماده بودن schema)
    try:
        _migrate_legacy_company_dbs()
    except Exception:
        pass

    # رکورد نمونه برای همه فرم‌ها (فقط جداول خالی)
    try:
        ensure_mjz_permits_table()
        migrate_mjz_persian_codes()
        ensure_ctr_employer_column()
        seed_mjz_and_clients_samples(force=False)
        seed_demo_records(force=False)
    except Exception:
        pass

    try:
        with get_main_db() as conn:
            _init_sys_access_schema(conn)
            seed_sys_access_defaults(conn)
            conn.commit()
    except Exception:
        pass


def _seed_sample_personnel(company_code: int, company_name: str):
    """داده نمونه فقط اگر جدول خالی باشد"""
    with get_main_db() as conn:
        n = conn.execute(
            "SELECT COUNT(*) FROM personnel WHERE company_code=?",
            (_norm_company_code(company_code),),
        ).fetchone()[0]
        if n > 0:
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        samples_by_code = {
            100: [
                ("1", "علی", "محمدی", "حسین", "0012345678", "1001", "کارشناس حراست", "حراست", "09121234567"),
                ("2", "رضا", "کریمی", "محمد", "0012345679", "1002", "نگهبان", "انتظامات", "09129876543"),
            ],
            101: [
                ("1", "مریم", "حسینی", "علی", "0012345680", "2001", "کارشناس", "اداری", "09161112233"),
                ("2", "حسین", "رضایی", "احمد", "0012345681", "2002", "راننده", "ترابری", "09163334455"),
            ],
            102: [
                ("1", "سعید", "نوری", "رضا", "0012345682", "3001", "مهندس", "عملیات", "09177778899"),
            ],
            103: [
                ("1", "فاطمه", "احمدی", "محمود", "0012345683", "4001", "مسئول شیفت", "حفاری", "09160001122"),
            ],
        }
        for row in samples_by_code.get(company_code, []):
            row_num, first, last, father, nid, ind, pos, dept, phone = row
            conn.execute(
                """
                INSERT INTO personnel (
                    row_num, first_name, last_name, father_name, national_id,
                    indicator_num, company_code, company, position, department,
                    active_status, phone, created_at, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    row_num, first, last, father, nid, ind,
                    str(company_code), company_name, pos, dept,
                    "فعال", phone, now, now,
                ),
            )


def _next_company_code(conn) -> int:
    row = conn.execute("SELECT MAX(code) FROM companies").fetchone()
    mx = row[0] if row and row[0] is not None else (COMPANY_CODE_START - 1)
    return max(int(mx) + 1, COMPANY_CODE_START)


# ─── شرکت‌ها ───


# کش کوتاه‌مدت فهرست شرکت‌ها (کاهش کوئری تکراری در لیست پرسنل)
_COMPANIES_CACHE = {"ts": 0.0, "active": None, "all": None, "ttl": 8.0}

def _invalidate_companies_cache():
    _COMPANIES_CACHE["ts"] = 0.0
    _COMPANIES_CACHE["active"] = None
    _COMPANIES_CACHE["all"] = None

def list_companies(active_only: bool = False, include_personnel_count: bool = True) -> list:
    """
    فهرست شرکت‌های تابعه از جدول companies در دیتابیس متمرکز.
    include_personnel_count=True شمارش پرسنل هر شرکت را با فیلتر company_code انجام می‌دهد.
    """
    import time as _time
    now = _time.time()
    cache_key = "active" if active_only else "all"
    # فقط وقتی شمارش پرسنل لازم نیست از کش استفاده شود
    if not include_personnel_count:
        cached = _COMPANIES_CACHE.get(cache_key)
        if cached is not None and (now - _COMPANIES_CACHE["ts"]) < _COMPANIES_CACHE["ttl"]:
            return [dict(x) for x in cached]

    with get_companies_db() as conn:
        sql = "SELECT * FROM companies"
        if active_only:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY code ASC"
        rows = conn.execute(sql).fetchall()
        result = []
        for r in rows:
            d = row_to_dict(r)
            d["is_active"] = bool(d.get("is_active"))
            d["db_name"] = "co_db.db"
            if include_personnel_count:
                try:
                    code = d["code"]
                    d["personnel_count"] = conn.execute(
                        "SELECT COUNT(*) FROM personnel WHERE company_code=?",
                        (_norm_company_code(code),),
                    ).fetchone()[0]
                except Exception:
                    d["personnel_count"] = 0
            else:
                d["personnel_count"] = None
            result.append(d)
        if not include_personnel_count:
            import time as _time
            _COMPANIES_CACHE[cache_key] = [dict(x) for x in result]
            _COMPANIES_CACHE["ts"] = _time.time()
        return result


def get_company_by_code(code: int) -> dict | None:
    with get_companies_db() as conn:
        row = conn.execute("SELECT * FROM companies WHERE code=?", (int(code),)).fetchone()
        if not row:
            return None
        d = row_to_dict(row)
        d["is_active"] = bool(d.get("is_active"))
        d["db_name"] = "co_db.db"
        return d


def get_company_by_id(cid: int) -> dict | None:
    with get_companies_db() as conn:
        row = conn.execute("SELECT * FROM companies WHERE id=?", (int(cid),)).fetchone()
        if not row:
            return None
        d = row_to_dict(row)
        d["is_active"] = bool(d.get("is_active"))
        d["db_name"] = "co_db.db"
        return d


def create_company(name: str, short_name: str = "", description: str = "", parent_code=None, logo: str = "") -> dict:
    """
    ثبت شرکت تابعه جدید در جدول companies (دیتابیس متمرکز).
    کد سه‌رقمی یکتا از ۱۰۰ به بعد اختصاص می‌یابد.
    parent_code: کد شرکت سطح بالاتر (ساختار درختی).
    """
    _invalidate_companies_cache()
    name = (name or "").strip()
    if not name:
        raise ValueError("نام شرکت الزامی است")
    pc = None
    if parent_code is not None and str(parent_code).strip() != "":
        try:
            pc = int(parent_code)
        except Exception:
            raise ValueError("کد شرکت والد نامعتبر است")

    with get_companies_db() as conn:
        if pc is not None:
            parent = conn.execute("SELECT code FROM companies WHERE code=?", (pc,)).fetchone()
            if not parent:
                raise ValueError(f"شرکت والد با کد {pc} یافت نشد")
        code = _next_company_code(conn)
        db_file = "co_db.db"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = conn.execute(
            """
            INSERT INTO companies (code, name, short_name, is_active, db_file, created_at, description, parent_code, logo)
            VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?)
            """,
            (code, name, short_name or "", db_file, now, description or "", pc, logo or ""),
        )
        company_id = cur.lastrowid

    ensure_company_database(code)

    # ساخت فولدر شرکت در مسیر ریشه مدارک پرسنل
    try:
        company_docs_folder(company_name=name, company_code=code, create=True)
    except Exception:
        pass

    return get_company_by_id(company_id)


def update_company(code: int, data: dict) -> dict | None:
    """ویرایش مشخصات شرکت."""
    _invalidate_companies_cache()
    allowed = ["name", "short_name", "description", "is_active", "parent_code", "logo"]
    sets, values = [], []
    for k in allowed:
        if k in data:
            sets.append(f"{k}=?")
            val = data[k]
            if k == "is_active":
                val = 1 if val else 0
            if k == "parent_code":
                if val is None or val == "" or val is False:
                    val = None
                else:
                    val = int(val)
                    if val == int(code):
                        raise ValueError("شرکت نمی‌تواند والد خودش باشد")
            values.append(val)
    if not sets:
        return get_company_by_code(code)
    values.append(int(code))
    with get_companies_db() as conn:
        conn.execute(f"UPDATE companies SET {', '.join(sets)} WHERE code=?", values)
    updated = get_company_by_code(code)
    # در صورت تغییر/وجود نام، فولدر شرکت زیر ریشه مدارک ساخته شود
    if updated:
        try:
            company_docs_folder(
                company_name=updated.get("name") or "",
                company_code=code,
                create=True,
            )
        except Exception:
            pass
    return updated


# ─── پرسنل (دیتابیس متمرکز + فیلتر company_code) ───

def _personnel_search_where(q: str | None):
    """ساخت WHERE و پارامترهای جستجوی پرسنل (قابل استفاده مجدد)."""
    conditions, params = [], []
    if not q or not str(q).strip():
        return conditions, params
    raw = str(q).strip()
    q_norm = normalize_for_search(raw)
    digits_only = q_norm.replace(" ", "").replace("-", "")
    if digits_only.isdigit() and len(digits_only) >= 4:
        # پیشوند بدون % اول برای امکان استفاده بهتر از ایندکس در حالت exact-ish
        if len(digits_only) >= 8:
            conditions.append(
                "(national_id = ? OR national_id LIKE ? OR phone LIKE ? OR indicator_num LIKE ?)"
            )
            params.extend([digits_only, f"{digits_only}%", f"%{digits_only}%", f"%{digits_only}%"])
        else:
            like = f"%{digits_only}%"
            conditions.append("(national_id LIKE ? OR phone LIKE ? OR indicator_num LIKE ?)")
            params.extend([like, like, like])
    else:
        # اولویت نام/نام‌خانوادگی؛ LIKE '%x%' ایندکس را کامل استفاده نمی‌کند ولی محدود به ۴ ستون است
        like = f"%{q_norm}%"
        conditions.append(
            "(first_name LIKE ? OR last_name LIKE ? OR position LIKE ? OR department LIKE ?)"
        )
        params.extend([like, like, like, like])
    return conditions, params


def count_personnel(company_code: int, q: str = None) -> int:
    """شمارش سریع پرسنل یک شرکت در دیتابیس متمرکز."""
    company_code = int(company_code)
    ensure_company_database(company_code)
    conditions, params = _personnel_search_where(q)
    cc = _norm_company_code(company_code)
    conditions = ["company_code = ?"] + conditions
    params = [cc] + params
    where = " WHERE " + " AND ".join(conditions)
    with get_main_db() as conn:
        row = conn.execute(f"SELECT COUNT(*) FROM personnel{where}", params).fetchone()
        return int(row[0])



def list_personnel(company_code: int, q: str = None, limit: int = 100, offset: int = 0):
    """
    لیست پرسنل یک شرکت از دیتابیس متمرکز (فیلتر company_code).
    - photo در لیست خوانده نمی‌شود (حجم base64 بالا)
    """
    company_code = int(company_code)
    ensure_company_database(company_code)
    limit = max(1, min(int(limit or 100), 100000))
    offset = max(0, int(offset or 0))

    select_cols = """
        id, row_num, first_name, last_name, previous_last_name, father_name,
        national_id, indicator_num, company_code, company, center, position,
        department, gender, active_status, phone, address,
        CASE WHEN photo IS NOT NULL AND photo != '' THEN 1 ELSE 0 END AS has_photo,
        CASE WHEN signature IS NOT NULL AND signature != '' THEN 1 ELSE 0 END AS has_signature
    """
    conditions, params = _personnel_search_where(q)
    cc = _norm_company_code(company_code)
    conditions = ["company_code = ?"] + conditions
    params = [cc] + params
    where = " WHERE " + " AND ".join(conditions)

    with get_main_db() as conn:
        total = int(
            conn.execute(f"SELECT COUNT(*) FROM personnel{where}", params).fetchone()[0]
        )
        sql = f"""
            SELECT {select_cols}
            FROM personnel
            {where}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(sql, [*params, limit, offset]).fetchall()
        items = []
        for r in rows:
            d = row_to_dict(r)
            d["has_photo"] = bool(int(d.get("has_photo") or 0))
            d["has_signature"] = bool(int(d.get("has_signature") or 0))
            d["photo"] = ""
            d["signature"] = ""
            items.append(d)
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "company_code": company_code,
            "db_name": "co_db.db",
        }


def get_personnel(company_code: int, pid: int):
    ensure_company_database(company_code)
    with get_main_db() as conn:
        row = conn.execute(
            "SELECT * FROM personnel WHERE id=? AND company_code=?",
            (pid, _norm_company_code(company_code)),
        ).fetchone()
        if row is None:
            # سازگاری: اگر company_code قدیمی خالی بود
            row = conn.execute("SELECT * FROM personnel WHERE id=?", (pid,)).fetchone()
        return row_to_dict(row) if row else None


def create_personnel(company_code: int = None, data: dict = None) -> dict:
    data = dict(data or {})
    # تخصیص شرکت می‌تواند بعداً از «تخصیص شرکت به پرسنل» انجام شود
    raw_code = company_code if company_code is not None else data.get("company_code")
    company = None
    if raw_code is not None and str(raw_code).strip() not in ("", "0", "None"):
        try:
            company_code = int(raw_code)
        except Exception:
            raise ValueError("کد شرکت نامعتبر است")
        company = get_company_by_code(company_code)
        if not company:
            raise ValueError(f"شرکت با کد {company_code} یافت نشد")
        if not company.get("is_active"):
            raise ValueError("شرکت غیرفعال است")
        ensure_company_database(company_code)
        data["company_code"] = _norm_company_code(company_code)
        data["company"] = company.get("name", "") or data.get("company") or ""
    else:
        company_code = None
        data["company_code"] = ""
        data["company"] = data.get("company") or "تخصیص‌نشده"
        ensure_company_database(100)  # schema آماده باشد

    fields = [f for f, _ in PERSONAL_FIELDS]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    values = []
    for f in fields:
        val = data.get(f, "")
        if f == "national_id":
            val = normalize_national_id(val)
        values.append(val if val is not None else "")

    with get_main_db() as conn:
        nid = normalize_national_id(data.get("national_id", ""))
        if nid:
            if company_code is not None:
                exists = conn.execute(
                    "SELECT id FROM personnel WHERE national_id=? AND company_code=?",
                    (nid, _norm_company_code(company_code)),
                ).fetchone()
            else:
                exists = conn.execute(
                    "SELECT id FROM personnel WHERE national_id=?", (nid,)
                ).fetchone()
            if exists:
                raise ValueError("کد ملی تکراری است")

        cols = ", ".join(fields + ["created_at", "updated_at"])
        placeholders = ", ".join(["?"] * (len(fields) + 2))
        cur = conn.execute(
            f"INSERT INTO personnel ({cols}) VALUES ({placeholders})",
            (*values, now, now),
        )
        pid = cur.lastrowid
        row = conn.execute("SELECT * FROM personnel WHERE id=?", (pid,)).fetchone()
        result = row_to_dict(row)
        # فولدر: docs_root / نام شرکت / کدملی + ثبت در ایندکس
        if nid and company_code is not None and company:
            try:
                folder = person_docs_folder(
                    nid,
                    company_name=company.get("name", ""),
                    company_code=company_code,
                    create=True,
                )
                # به‌روزرسانی کاتالوگ بدون اسکن کامل
                try:
                    root = get_docs_root()
                    rel = os.path.relpath(folder, root).replace("\\", "/")
                    idx = load_folder_index()
                    paths = set(idx.get("paths") or [])
                    paths.add(rel.split("/")[0])  # شرکت
                    paths.add(rel)
                    idx["paths"] = sorted(paths)
                    idx.setdefault("personnel", {})[f"{company_code}:{nid}"] = rel
                    idx.setdefault("companies", {})[str(company_code)] = rel.split("/")[0]
                    save_folder_index(idx)
                except Exception:
                    pass
            except Exception:
                pass
        return result


def update_personnel(company_code: int, pid: int, data: dict) -> dict | None:
    """ویرایش پرسنل؛ امکان تغییر شرکت/مرکز/واحد برای تخصیص سازمانی."""
    ensure_company_database(company_code if company_code else 100)
    fields = [f for f, _ in PERSONAL_FIELDS]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = dict(data or {})
    # تخصیص شرکت جدید
    if "company_code" in data and data.get("company_code") not in (None, ""):
        try:
            new_code = int(data["company_code"])
            co = get_company_by_code(new_code)
            if co:
                data["company_code"] = _norm_company_code(new_code)
                if not data.get("company"):
                    data["company"] = co.get("name") or ""
        except Exception:
            pass
    sets, values = [], []
    for f in fields:
        if f in data:
            val = data[f]
            if f == "national_id":
                val = normalize_national_id(val)
            sets.append(f"{f}=?")
            values.append(val if val is not None else "")
    if not sets:
        return get_personnel(company_code, pid)
    sets.append("updated_at=?")
    values.append(now)
    values.append(pid)
    with get_main_db() as conn:
        conn.execute(f"UPDATE personnel SET {', '.join(sets)} WHERE id=?", values)
        row = conn.execute("SELECT * FROM personnel WHERE id=?", (pid,)).fetchone()
        return row_to_dict(row) if row else None


def delete_personnel(company_code: int, pid: int) -> bool:
    ensure_company_database(company_code)
    with get_company_db(company_code) as conn:
        cur = conn.execute("DELETE FROM personnel WHERE id=?", (pid,))
        return cur.rowcount > 0


def list_personnel_across_companies(q: str = None, limit: int = 100, offset: int = 0, company_code: int = None) -> dict:
    """
    لیست پرسنل از دیتابیس متمرکز.
    company_code اختیاری است؛ در صورت None همه شرکت‌ها برگردانده می‌شوند.
    """
    ensure_company_database()
    limit = max(1, min(int(limit or 100), 100000))
    offset = max(0, int(offset or 0))

    select_cols = """
        id, row_num, first_name, last_name, previous_last_name, father_name,
        national_id, indicator_num, company_code, company, center, position,
        department, gender, active_status, phone, address,
        CASE WHEN photo IS NOT NULL AND photo != '' THEN 1 ELSE 0 END AS has_photo,
        CASE WHEN signature IS NOT NULL AND signature != '' THEN 1 ELSE 0 END AS has_signature
    """
    conditions, params = _personnel_search_where(q)
    if company_code is not None:
        conditions = ["company_code = ?"] + conditions
        params = [_norm_company_code(company_code)] + params
        scope = "company"
    else:
        scope = "all_companies"
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    registry_map = {}
    try:
        for c in list_companies(active_only=False, include_personnel_count=False):
            try:
                registry_map[int(c.get("code"))] = c.get("name") or c.get("short_name") or ""
            except Exception:
                pass
    except Exception:
        pass

    with get_main_db() as conn:
        # یک اتصال برای COUNT + SELECT (کم‌کردن overhead باز/بسته شدن)
        if not conditions and offset == 0 and limit <= 200:
            # مسیر سریع: بدون WHERE، شمارش با max(id) تقریبی نیست — COUNT(*) روی ایندکس id
            total = int(conn.execute("SELECT COUNT(*) FROM personnel").fetchone()[0])
        else:
            total = int(conn.execute(f"SELECT COUNT(*) FROM personnel{where}", params).fetchone()[0])
        rows = conn.execute(
            f"SELECT {select_cols} FROM personnel{where} ORDER BY id DESC LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()
        items = []
        for r in rows:
            d = row_to_dict(r)
            d["has_photo"] = bool(int(d.get("has_photo") or 0))
            d["has_signature"] = bool(int(d.get("has_signature") or 0))
            d["photo"] = ""
            d["signature"] = ""
            try:
                cc = int(d.get("company_code") or 0)
            except Exception:
                cc = 0
            if cc and not d.get("company"):
                d["company"] = registry_map.get(cc) or d.get("company") or ""
            items.append(d)

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "scope": scope,
        "companies_scanned": sorted(registry_map.keys()) if company_code is None else [int(company_code)],
        "database_errors": [],
        "db_name": "co_db.db",
    }




# ──────────────────────────────────────────────
# جداول پایه (اطلاعات پایه) — در دیتابیس متمرکز co_db.db
# ──────────────────────────────────────────────

def _init_lookup_tables(conn):
    """جداول مرجع مشترک: واحد، رشته تحصیلی، گروه مسئولیت، نوع استخدام"""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT DEFAULT '',
            name TEXT NOT NULL,
            parent_name TEXT DEFAULT '',
            center_name TEXT DEFAULT '',
            company_code INTEGER,
            show_on_guard_board INTEGER DEFAULT 1,
            show_on_internet INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_units_center ON units(center_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_units_name ON units(name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_units_company ON units(company_code)")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS education_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS responsibility_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS employment_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT
        )
        """
    )
    # ستون‌های اضافی واحدها (مهاجرت)
    unit_cols = {r[1] for r in conn.execute("PRAGMA table_info(units)").fetchall()}
    for col, decl in (
        ("image_path", "TEXT DEFAULT ''"),
        ("symbol_path", "TEXT DEFAULT ''"),
    ):
        if col not in unit_cols:
            conn.execute(f"ALTER TABLE units ADD COLUMN {col} {decl}")

    # درب‌های تردد — فیلدهای کامل مطابق دژبان
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS access_doors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT DEFAULT '',
            name TEXT NOT NULL,
            door_type TEXT DEFAULT 'تردد پرسنل و ارباب رجوع',
            direction TEXT DEFAULT 'ورود',
            center_name TEXT DEFAULT '',
            company_code INTEGER,
            ip_address TEXT DEFAULT '',
            road_address TEXT DEFAULT '',
            device_type TEXT DEFAULT '',
            device_name TEXT DEFAULT '',
            terminal_id TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            description TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    # مقصد کالا
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS goods_destinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone1 TEXT DEFAULT '',
            phone2 TEXT DEFAULT '',
            address TEXT DEFAULT '',
            description TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    # مسیر سرویس (ساده)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            created_at TEXT
        )
        """
    )
    # شرکت/مشتری
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS client_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            description TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        )
        """
    )

    # شرکت‌های صدور کارت (نام + لوگو برای چاپ کارت شناسایی)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS card_issue_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            company_code TEXT DEFAULT '',
            logo TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    # نوع ورود و خروج
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS entry_exit_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            is_entry INTEGER DEFAULT 1,
            is_exit INTEGER DEFAULT 1,
            created_at TEXT
        )
        """
    )
    # دسترسی کاربر به درب
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS door_user_access (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            door_name TEXT NOT NULL,
            user_name TEXT DEFAULT '',
            created_at TEXT
        )
        """
    )
    # سازگاری با نام قبلی
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS door_access_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            created_at TEXT
        )
        """
    )
    # —— انتظامات (مرجع شیفت/نگهبانی) ——
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            center_name TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_protection_centers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            center_name TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_protection_places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            place_name TEXT NOT NULL,
            protection_center_name TEXT DEFAULT '',
            center_name TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_shift_hours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            center_name TEXT DEFAULT '',
            start_time TEXT DEFAULT '',
            end_time TEXT DEFAULT '',
            created_at TEXT
        )
    """)

    # migrate shift hours time columns
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(ent_shift_hours)").fetchall()}
        if "start_time" not in cols:
            conn.execute("ALTER TABLE ent_shift_hours ADD COLUMN start_time TEXT DEFAULT ''")
        if "end_time" not in cols:
            conn.execute("ALTER TABLE ent_shift_hours ADD COLUMN end_time TEXT DEFAULT ''")
    except Exception:
        pass
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_shift_leaders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_name TEXT DEFAULT '',
            unit_name TEXT DEFAULT '',
            person_name TEXT DEFAULT '',
            shift_name TEXT DEFAULT '',
            role_type TEXT DEFAULT 'مسئول شیفت',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_work_shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            center_name TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_staff_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_guard_equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_name TEXT DEFAULT '',
            device_name TEXT NOT NULL,
            serial_number TEXT DEFAULT '',
            asset_number TEXT DEFAULT '',
            created_at TEXT
        )
    """)

    # —— انتظامات عملیاتی ——
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_guard_board (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_name TEXT DEFAULT '',
            shift_name TEXT DEFAULT '',
            work_shift TEXT DEFAULT '',
            shift_date TEXT DEFAULT '',
            shift_leader TEXT DEFAULT '',
            shift_deputy TEXT DEFAULT '',
            description TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_shift_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_name TEXT DEFAULT '',
            shift_name TEXT DEFAULT '',
            event_date TEXT DEFAULT '',
            event_text TEXT DEFAULT '',
            reporter TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_shift_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_name TEXT DEFAULT '',
            work_shift TEXT DEFAULT '',
            personnel_name TEXT DEFAULT '',
            date_from TEXT DEFAULT '',
            date_to TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_personnel_electronics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            personnel_name TEXT DEFAULT '',
            device_name TEXT DEFAULT '',
            serial_number TEXT DEFAULT '',
            center_name TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_replacement_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_name TEXT DEFAULT '',
            replacement_name TEXT DEFAULT '',
            shift_name TEXT DEFAULT '',
            request_date TEXT DEFAULT '',
            reason TEXT DEFAULT '',
            status TEXT DEFAULT 'در انتظار',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_permits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            permit_type TEXT DEFAULT '',
            personnel_name TEXT DEFAULT '',
            center_name TEXT DEFAULT '',
            date_from TEXT DEFAULT '',
            date_to TEXT DEFAULT '',
            description TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_monitoring_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_name TEXT DEFAULT '',
            shift_name TEXT DEFAULT '',
            event_date TEXT DEFAULT '',
            event_text TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_monitoring_staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_name TEXT DEFAULT '',
            person_name TEXT DEFAULT '',
            role_name TEXT DEFAULT '',
            shift_name TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_guard_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_name TEXT DEFAULT '',
            report_date TEXT DEFAULT '',
            title TEXT DEFAULT '',
            body TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_guard_referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_name TEXT DEFAULT '',
            report_date TEXT DEFAULT '',
            referred_to TEXT DEFAULT '',
            body TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_roll_call (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_name TEXT DEFAULT '',
            call_date TEXT DEFAULT '',
            personnel_name TEXT DEFAULT '',
            status TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_news_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT DEFAULT '',
            report_date TEXT DEFAULT '',
            body TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_guard_board_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_name TEXT DEFAULT '',
            summary_date TEXT DEFAULT '',
            summary_text TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_guard_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_name TEXT DEFAULT '',
            event_date TEXT DEFAULT '',
            event_text TEXT DEFAULT '',
            officer_name TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_deployment_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT DEFAULT '',
            name TEXT NOT NULL,
            center_name TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ent_officer_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            officer_name TEXT DEFAULT '',
            event_date TEXT DEFAULT '',
            event_text TEXT DEFAULT '',
            center_name TEXT DEFAULT '',
            created_at TEXT
        )
    """)

    # —— صدور کارت (چاپ و گزارش کارت پرسنل / پیمانکار / خودرو) ——
    conn.execute("""
        CREATE TABLE IF NOT EXISTS card_personnel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            personnel_code TEXT DEFAULT '',
            national_id TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            unit_name TEXT DEFAULT '',
            membership_type TEXT DEFAULT '',
            card_status TEXT DEFAULT 'فعال',
            issue_date TEXT DEFAULT '',
            expiry_date TEXT DEFAULT '',
            alphabetical INTEGER DEFAULT 0,
            print_front INTEGER DEFAULT 1,
            print_batch INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS card_contractor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            personnel_code TEXT DEFAULT '',
            national_id TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            company_name TEXT DEFAULT '',
            activity_unit TEXT DEFAULT '',
            card_status TEXT DEFAULT 'فعال',
            issue_date TEXT DEFAULT '',
            expiry_date TEXT DEFAULT '',
            alphabetical INTEGER DEFAULT 0,
            print_front INTEGER DEFAULT 1,
            print_back INTEGER DEFAULT 0,
            print_batch INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS card_vehicle_personnel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT DEFAULT '',
            vehicle_type TEXT DEFAULT '',
            unit_name TEXT DEFAULT '',
            personnel_code TEXT DEFAULT '',
            driver_name TEXT DEFAULT '',
            card_status TEXT DEFAULT 'فعال',
            issue_date TEXT DEFAULT '',
            expiry_date TEXT DEFAULT '',
            alphabetical INTEGER DEFAULT 0,
            print_front INTEGER DEFAULT 1,
            print_batch INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS card_vehicle_contractor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT DEFAULT '',
            vehicle_type TEXT DEFAULT '',
            company_name TEXT DEFAULT '',
            activity_unit TEXT DEFAULT '',
            driver_name TEXT DEFAULT '',
            traffic_area TEXT DEFAULT '',
            card_number TEXT DEFAULT '',
            certificate_number TEXT DEFAULT '',
            card_status TEXT DEFAULT 'فعال',
            issue_date TEXT DEFAULT '',
            expiry_date TEXT DEFAULT '',
            alphabetical INTEGER DEFAULT 0,
            print_front INTEGER DEFAULT 1,
            print_back INTEGER DEFAULT 0,
            print_batch INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)

    # —— پیمانکاران (شرکت / قرارداد / پرسنل / خودرو / راننده) ——
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ctr_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company_code TEXT DEFAULT '',
            parent_company TEXT DEFAULT '',
            employer_company TEXT DEFAULT '',
            register_date TEXT DEFAULT '',
            ceo_mobile TEXT DEFAULT '',
            rep1_mobile TEXT DEFAULT '',
            company_phone TEXT DEFAULT '',
            rep1_name TEXT DEFAULT '',
            supervisor_name TEXT DEFAULT '',
            ceo_name TEXT DEFAULT '',
            supervisor_personnel_code TEXT DEFAULT '',
            ceo_national_id TEXT DEFAULT '',
            company_email TEXT DEFAULT '',
            ceo_education TEXT DEFAULT '',
            company_website TEXT DEFAULT '',
            rep1_national_id TEXT DEFAULT '',
            company_history TEXT DEFAULT '',
            company_address TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ctr_contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            contract_subject TEXT DEFAULT '',
            activity_location TEXT DEFAULT '',
            tender_number TEXT DEFAULT '',
            contract_number TEXT DEFAULT '',
            settlement_date TEXT DEFAULT '',
            start_date TEXT DEFAULT '',
            contract_amount TEXT DEFAULT '',
            credit_duration TEXT DEFAULT '',
            duration_notes TEXT DEFAULT '',
            end_date TEXT DEFAULT '',
            work_location TEXT DEFAULT '',
            supervisor_unit TEXT DEFAULT '',
            contract_status TEXT DEFAULT 'فعال',
            status_description TEXT DEFAULT '',
            is_inactive INTEGER DEFAULT 0,
            description TEXT DEFAULT '',
            transport TEXT DEFAULT '',
            vehicle_count TEXT DEFAULT '',
            vehicle_type TEXT DEFAULT '',
            vehicle_entry_permit INTEGER DEFAULT 0,
            restaurant INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ctr_personnel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            contract_number TEXT DEFAULT '',
            nationality TEXT DEFAULT 'ایرانی',
            personnel_code TEXT DEFAULT '',
            supervisor_name TEXT DEFAULT '',
            job_type TEXT DEFAULT '',
            activity_unit TEXT DEFAULT '',
            end_of_service_date TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            father_name TEXT DEFAULT '',
            national_id TEXT DEFAULT '',
            fixed_phone TEXT DEFAULT '',
            mobile_phone TEXT DEFAULT '',
            emergency_phone TEXT DEFAULT '',
            internal_phone TEXT DEFAULT '',
            has_criminal_record INTEGER DEFAULT 0,
            card_number TEXT DEFAULT '',
            card_status TEXT DEFAULT '',
            card_type TEXT DEFAULT '',
            education_degree TEXT DEFAULT '',
            education_field TEXT DEFAULT '',
            passport_number TEXT DEFAULT '',
            birth_date TEXT DEFAULT '',
            birth_place TEXT DEFAULT '',
            gender TEXT DEFAULT '',
            religion TEXT DEFAULT '',
            sect TEXT DEFAULT '',
            home_address TEXT DEFAULT '',
            job_title TEXT DEFAULT '',
            marital_status TEXT DEFAULT '',
            military_status TEXT DEFAULT '',
            entry_door TEXT DEFAULT '',
            membership_type TEXT DEFAULT '',
            inquiry_number TEXT DEFAULT '',
            id_number TEXT DEFAULT '',
            id_issue_place TEXT DEFAULT '',
            postal_code TEXT DEFAULT '',
            inquiry_date TEXT DEFAULT '',
            blood_type TEXT DEFAULT '',
            is_foreign INTEGER DEFAULT 0,
            retirement_date TEXT DEFAULT '',
            start_work_date TEXT DEFAULT '',
            credit_start_date TEXT DEFAULT '',
            credit_end_date TEXT DEFAULT '',
            is_inactive INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ctr_vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT DEFAULT '',
            company_name TEXT NOT NULL,
            owner_last_name TEXT DEFAULT '',
            owner_first_name TEXT DEFAULT '',
            owner_national_id TEXT DEFAULT '',
            vehicle_class TEXT DEFAULT '',
            vehicle_type TEXT DEFAULT '',
            vehicle_color TEXT DEFAULT '',
            equipment TEXT DEFAULT '',
            usage_purpose TEXT DEFAULT '',
            activity_unit TEXT DEFAULT '',
            chassis_number TEXT DEFAULT '',
            insurance_end_date TEXT DEFAULT '',
            card_status TEXT DEFAULT 'فعال',
            traffic_status TEXT DEFAULT '',
            traffic_area TEXT DEFAULT '',
            credit_end_date TEXT DEFAULT '',
            last_inspection_date TEXT DEFAULT '',
            is_inactive INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ctr_drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            personnel_code TEXT DEFAULT '',
            activity_unit TEXT DEFAULT '',
            position TEXT DEFAULT '',
            driver_name TEXT DEFAULT '',
            father_name TEXT DEFAULT '',
            national_id TEXT DEFAULT '',
            license_type TEXT DEFAULT '',
            license_number TEXT DEFAULT '',
            license_issue_place TEXT DEFAULT '',
            license_end_date TEXT DEFAULT '',
            card_status TEXT DEFAULT 'فعال',
            validity_type TEXT DEFAULT 'دائم',
            is_inactive INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)

    # —— گشت و پایش (دستگاه / رخداد / نقطه بازدید / نگهبان / مسیر) ——
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patrol_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT NOT NULL,
            device_code TEXT DEFAULT '',
            connected_port TEXT DEFAULT '',
            usb_port TEXT DEFAULT '',
            center_name TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patrol_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_code TEXT DEFAULT '',
            event_name TEXT NOT NULL,
            importance TEXT DEFAULT 'عادی',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patrol_checkpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checkpoint_code TEXT DEFAULT '',
            checkpoint_name TEXT NOT NULL,
            center_name TEXT DEFAULT '',
            connected_port TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patrol_guards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guard_id TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            personnel_code TEXT DEFAULT '',
            unit_name TEXT DEFAULT '',
            center_name TEXT DEFAULT '',
            connected_port TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patrol_routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_name TEXT NOT NULL,
            center_name TEXT DEFAULT '',
            start_time TEXT DEFAULT '',
            end_time TEXT DEFAULT '',
            checkpoint_names TEXT DEFAULT '',
            description TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patrol_route_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_name TEXT NOT NULL,
            guard_name TEXT DEFAULT '',
            device_name TEXT DEFAULT '',
            sequence_order TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patrol_shift_times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_name TEXT DEFAULT '',
            route_name TEXT DEFAULT '',
            start_time TEXT DEFAULT '',
            end_time TEXT DEFAULT '',
            shift_name TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)


    # —— حراست (ارزشیابی / منازل / تخلفات / اتباع / سفر) ——
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hr_eval_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT DEFAULT '',
            option1 TEXT DEFAULT '', score1 TEXT DEFAULT '',
            option2 TEXT DEFAULT '', score2 TEXT DEFAULT '',
            option3 TEXT DEFAULT '', score3 TEXT DEFAULT '',
            option4 TEXT DEFAULT '', score4 TEXT DEFAULT '',
            option5 TEXT DEFAULT '', score5 TEXT DEFAULT '',
            option6 TEXT DEFAULT '', score6 TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hr_eval_titles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title_text TEXT NOT NULL,
            score TEXT DEFAULT '',
            answer_type TEXT DEFAULT '',
            option_count TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hr_eval_periods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_title TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hr_eval_monthly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            personnel_name TEXT DEFAULT '',
            unit_name TEXT DEFAULT '',
            period_title TEXT DEFAULT '',
            supervisor_name TEXT DEFAULT '',
            supervisor_opinion TEXT DEFAULT '',
            eval_date TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hr_areas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_name TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hr_houses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            house_name TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hr_house_delivery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_name TEXT DEFAULT '',
            house_name TEXT DEFAULT '',
            personnel_name TEXT DEFAULT '',
            personnel_code TEXT DEFAULT '',
            related_office TEXT DEFAULT '',
            house_number TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            mobile TEXT DEFAULT '',
            delivery_date TEXT DEFAULT '',
            eviction_date TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hr_doc_archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_description TEXT DEFAULT '',
            keyword TEXT DEFAULT '',
            file_name TEXT DEFAULT '',
            file_type TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hr_foreign_nationals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            father_name TEXT DEFAULT '',
            nationality TEXT DEFAULT '',
            passport_number TEXT DEFAULT '',
            gender TEXT DEFAULT '',
            birth_date TEXT DEFAULT '',
            birth_place TEXT DEFAULT '',
            job_title TEXT DEFAULT '',
            mobile TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hr_countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_name TEXT NOT NULL,
            residence_city TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hr_violations_personnel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_type TEXT DEFAULT 'پرسنل شرکتی',
            unit_name TEXT DEFAULT '',
            person_name TEXT DEFAULT '',
            national_id TEXT DEFAULT '',
            violation_code TEXT DEFAULT '',
            violation_subject TEXT DEFAULT '',
            occurrence_time TEXT DEFAULT '',
            register_date TEXT DEFAULT '',
            fine_amount TEXT DEFAULT '',
            description TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hr_violations_vehicle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT DEFAULT '',
            vehicle_type TEXT DEFAULT '',
            driver_name TEXT DEFAULT '',
            unit_name TEXT DEFAULT '',
            violation_code TEXT DEFAULT '',
            violation_subject TEXT DEFAULT '',
            occurrence_time TEXT DEFAULT '',
            register_date TEXT DEFAULT '',
            fine_amount TEXT DEFAULT '',
            description TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hr_incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_datetime TEXT DEFAULT '',
            incident_location TEXT DEFAULT '',
            expert1_name TEXT DEFAULT '',
            expert1_unit TEXT DEFAULT '',
            expert1_opinion TEXT DEFAULT '',
            expert2_name TEXT DEFAULT '',
            expert2_unit TEXT DEFAULT '',
            expert2_opinion TEXT DEFAULT '',
            commission_result TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hr_drug_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_type TEXT DEFAULT 'پرسنل شرکتی',
            unit_name TEXT DEFAULT '',
            person_name TEXT DEFAULT '',
            father_name TEXT DEFAULT '',
            birth_date TEXT DEFAULT '',
            birth_place TEXT DEFAULT '',
            national_id TEXT DEFAULT '',
            mobile TEXT DEFAULT '',
            description TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hr_rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_type TEXT DEFAULT 'پرسنل شرکتی',
            unit_name TEXT DEFAULT '',
            person_name TEXT DEFAULT '',
            reward_code TEXT DEFAULT '',
            reward_subject TEXT DEFAULT '',
            register_date TEXT DEFAULT '',
            description TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hr_travel_abroad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            father_name TEXT DEFAULT '',
            national_id TEXT DEFAULT '',
            passport_number TEXT DEFAULT '',
            destination_country TEXT DEFAULT '',
            travel_from TEXT DEFAULT '',
            travel_to TEXT DEFAULT '',
            purpose TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hr_travel_personal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            national_id TEXT DEFAULT '',
            destination_country TEXT DEFAULT '',
            travel_from TEXT DEFAULT '',
            travel_to TEXT DEFAULT '',
            purpose TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hr_exit_admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_name TEXT DEFAULT '',
            unit_name TEXT DEFAULT '',
            document_type TEXT DEFAULT '',
            request_date TEXT DEFAULT '',
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'در انتظار',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hr_exit_scientific (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_name TEXT DEFAULT '',
            unit_name TEXT DEFAULT '',
            document_type TEXT DEFAULT '',
            request_date TEXT DEFAULT '',
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'در انتظار',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)



    # —— مناقصات و مزایدات ——
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tnd_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            registration_place TEXT DEFAULT '',
            registration_number TEXT DEFAULT '',
            registration_date TEXT DEFAULT '',
            activity_type TEXT DEFAULT '',
            rank_level TEXT DEFAULT '',
            address TEXT DEFAULT '',
            postal_code TEXT DEFAULT '',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            fax TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tnd_tenders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            main_company TEXT DEFAULT '',
            subsidiary_company TEXT DEFAULT '',
            main_organization TEXT DEFAULT '',
            tender_subject TEXT NOT NULL,
            tender_type TEXT DEFAULT '',
            cancellation_reason TEXT DEFAULT '',
            exclusive_method TEXT DEFAULT '',
            security_rep TEXT DEFAULT '',
            inspection_rep TEXT DEFAULT '',
            inspection_rep2 TEXT DEFAULT '',
            packet_open_date TEXT DEFAULT '',
            agreement_amount TEXT DEFAULT '',
            agreement_amount_prev TEXT DEFAULT '',
            expert_amount TEXT DEFAULT '',
            expert_amount_prev TEXT DEFAULT '',
            description TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tnd_auctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            main_company TEXT DEFAULT '',
            subsidiary_company TEXT DEFAULT '',
            main_organization TEXT DEFAULT '',
            auction_subject TEXT NOT NULL,
            auction_type TEXT DEFAULT '',
            cancellation_reason TEXT DEFAULT '',
            exclusive_method TEXT DEFAULT '',
            security_rep TEXT DEFAULT '',
            inspection_rep TEXT DEFAULT '',
            inspection_rep2 TEXT DEFAULT '',
            packet_open_date TEXT DEFAULT '',
            agreement_amount TEXT DEFAULT '',
            agreement_amount_prev TEXT DEFAULT '',
            expert_amount TEXT DEFAULT '',
            expert_amount_prev TEXT DEFAULT '',
            description TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tnd_contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            main_company TEXT DEFAULT '',
            subsidiary_company TEXT DEFAULT '',
            main_organization TEXT DEFAULT '',
            contractor_name TEXT DEFAULT '',
            contract_number TEXT DEFAULT '',
            contract_date TEXT DEFAULT '',
            contract_amount TEXT DEFAULT '',
            execution_place TEXT DEFAULT '',
            contract_subject TEXT DEFAULT '',
            start_date TEXT DEFAULT '',
            end_date TEXT DEFAULT '',
            guarantee_type TEXT DEFAULT '',
            guarantee_amount TEXT DEFAULT '',
            duration TEXT DEFAULT '',
            request_reason TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)



    # —— کارتابل ——
    conn.execute("""
        CREATE TABLE IF NOT EXISTS krt_outgoing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            letter_number TEXT DEFAULT '',
            subject TEXT NOT NULL,
            letter_date TEXT DEFAULT '',
            secretary_number TEXT DEFAULT '',
            secretary_date TEXT DEFAULT '',
            letter_body TEXT DEFAULT '',
            recipients TEXT DEFAULT '',
            file_name TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS krt_inbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            letter_number TEXT DEFAULT '',
            subject TEXT NOT NULL,
            letter_date TEXT DEFAULT '',
            secretary_number TEXT DEFAULT '',
            secretary_date TEXT DEFAULT '',
            letter_body TEXT DEFAULT '',
            sender_name TEXT DEFAULT '',
            status TEXT DEFAULT 'مشاهده نشده',
            folder_name TEXT DEFAULT '',
            file_name TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS krt_management (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_name TEXT DEFAULT '',
            subject TEXT DEFAULT '',
            status TEXT DEFAULT 'مشاهده نشده',
            send_date TEXT DEFAULT '',
            hour_sent TEXT DEFAULT '',
            folder_name TEXT DEFAULT '',
            file_name TEXT DEFAULT '',
            letter_body TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS krt_folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_name TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)



    # —— باسکول ——
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bsk_weighings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT DEFAULT '',
            queue_number TEXT DEFAULT '',
            plate_number TEXT DEFAULT '',
            card_serial TEXT DEFAULT '',
            driver_name TEXT DEFAULT '',
            vehicle_type TEXT DEFAULT '',
            origin_company TEXT DEFAULT '',
            destination_unit TEXT DEFAULT '',
            location_name TEXT DEFAULT '',
            cargo_code TEXT DEFAULT '',
            cargo_title TEXT DEFAULT '',
            first_weight TEXT DEFAULT '',
            first_date TEXT DEFAULT '',
            first_time TEXT DEFAULT '',
            first_operator TEXT DEFAULT '',
            first_status TEXT DEFAULT 'خالی',
            second_weight TEXT DEFAULT '',
            second_date TEXT DEFAULT '',
            second_time TEXT DEFAULT '',
            second_operator TEXT DEFAULT '',
            net_weight TEXT DEFAULT '',
            weigh_type TEXT DEFAULT 'بار ورودی',
            description TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bsk_turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            turn_number TEXT DEFAULT '',
            card_serial TEXT DEFAULT '',
            plate_number TEXT DEFAULT '',
            vehicle_type TEXT DEFAULT '',
            vehicle_weight TEXT DEFAULT '',
            allowed_max_weight TEXT DEFAULT '',
            driver_name TEXT DEFAULT '',
            driver_phone TEXT DEFAULT '',
            license_number TEXT DEFAULT '',
            origin_company TEXT DEFAULT '',
            destination_unit TEXT DEFAULT '',
            cargo_type TEXT DEFAULT '',
            location_name TEXT DEFAULT '',
            description TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bsk_traffic_ban (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT DEFAULT '',
            national_id TEXT DEFAULT '',
            person_name TEXT DEFAULT '',
            issuer_order TEXT DEFAULT '',
            description TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bsk_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_code TEXT DEFAULT '',
            company_name TEXT NOT NULL,
            is_approved INTEGER DEFAULT 1,
            is_origin INTEGER DEFAULT 0,
            is_destination INTEGER DEFAULT 0,
            is_evac INTEGER DEFAULT 0,
            phone TEXT DEFAULT '',
            location_name TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bsk_max_tonnage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT DEFAULT '',
            cargo_name TEXT DEFAULT '',
            destination_unit TEXT DEFAULT '',
            amount TEXT DEFAULT '',
            warning_amount TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bsk_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scale_name TEXT DEFAULT '',
            scale_code TEXT DEFAULT '',
            center_name TEXT DEFAULT '',
            port_name TEXT DEFAULT '',
            baud_rate TEXT DEFAULT '',
            data_bits TEXT DEFAULT '',
            parity_bit TEXT DEFAULT '',
            stop_bit TEXT DEFAULT '',
            region_code TEXT DEFAULT '',
            region_name TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bsk_weigh_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT DEFAULT '',
            plate_number TEXT DEFAULT '',
            vehicle_type TEXT DEFAULT '',
            driver_name TEXT DEFAULT '',
            first_weight TEXT DEFAULT '',
            second_weight TEXT DEFAULT '',
            net_weight TEXT DEFAULT '',
            weigh_date TEXT DEFAULT '',
            origin_company TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)



    # —— پلاک‌خوان ——
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plk_process (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT DEFAULT '',
            camera_name TEXT DEFAULT '',
            process_date TEXT DEFAULT '',
            process_time TEXT DEFAULT '',
            direction TEXT DEFAULT '',
            confidence TEXT DEFAULT '',
            image_path TEXT DEFAULT '',
            status TEXT DEFAULT 'ثبت شده',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plk_traffic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT DEFAULT '',
            camera_name TEXT DEFAULT '',
            entry_date TEXT DEFAULT '',
            entry_time TEXT DEFAULT '',
            exit_date TEXT DEFAULT '',
            exit_time TEXT DEFAULT '',
            vehicle_type TEXT DEFAULT '',
            driver_name TEXT DEFAULT '',
            gate_name TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plk_monitoring (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_name TEXT DEFAULT '',
            location_name TEXT DEFAULT '',
            status TEXT DEFAULT 'فعال',
            last_read_plate TEXT DEFAULT '',
            last_read_time TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plk_traffic_report (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT DEFAULT '',
            report_date TEXT DEFAULT '',
            traffic_count TEXT DEFAULT '',
            gate_name TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plk_full_traffic_report (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT DEFAULT '',
            from_date TEXT DEFAULT '',
            to_date TEXT DEFAULT '',
            total_entries TEXT DEFAULT '',
            total_exits TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plk_access_level_report (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT DEFAULT '',
            access_level TEXT DEFAULT '',
            vehicle_owner TEXT DEFAULT '',
            unit_name TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plk_inside_vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT DEFAULT '',
            entry_time TEXT DEFAULT '',
            camera_name TEXT DEFAULT '',
            duration TEXT DEFAULT '',
            status TEXT DEFAULT 'داخل سازمان',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plk_parking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT DEFAULT '',
            parking_zone TEXT DEFAULT '',
            slot_number TEXT DEFAULT '',
            entry_date TEXT DEFAULT '',
            entry_time TEXT DEFAULT '',
            exit_time TEXT DEFAULT '',
            status TEXT DEFAULT 'پارک شده',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plk_cameras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_name TEXT NOT NULL,
            camera_code TEXT DEFAULT '',
            location_name TEXT DEFAULT '',
            ip_address TEXT DEFAULT '',
            direction TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plk_online_monitor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_name TEXT DEFAULT '',
            live_plate TEXT DEFAULT '',
            event_time TEXT DEFAULT '',
            event_type TEXT DEFAULT 'تشخیص',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)



    # —— کنترل دسترسی (اکسس کنترل) ——
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ac_traffic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_type TEXT DEFAULT 'پرسنل',
            plate_number TEXT DEFAULT '',
            personnel_code TEXT DEFAULT '',
            card_code TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            company_unit TEXT DEFAULT '',
            door_name TEXT DEFAULT '',
            traffic_date TEXT DEFAULT '',
            traffic_time TEXT DEFAULT '',
            vehicle_type TEXT DEFAULT '',
            driver_name TEXT DEFAULT '',
            description TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ac_access_def (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            def_type TEXT DEFAULT 'محدوده زمانی',
            code TEXT DEFAULT '',
            name TEXT NOT NULL,
            time_from TEXT DEFAULT '',
            time_to TEXT DEFAULT '',
            access_hour TEXT DEFAULT '',
            zone_name TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ac_guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            national_id TEXT DEFAULT '',
            host_name TEXT DEFAULT '',
            visit_date TEXT DEFAULT '',
            visit_to_date TEXT DEFAULT '',
            access_group TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ac_guest_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_type TEXT DEFAULT 'مهمان',
            card_code TEXT DEFAULT '',
            card_number TEXT DEFAULT '',
            restriction_type TEXT DEFAULT '',
            access_group TEXT DEFAULT '',
            from_date TEXT DEFAULT '',
            to_date TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ac_guest_traffic_zone (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zone_name TEXT NOT NULL,
            door_name TEXT DEFAULT '',
            device_code TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ac_guest_delivered_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_number TEXT DEFAULT '',
            guest_name TEXT DEFAULT '',
            deliver_date TEXT DEFAULT '',
            deliver_time TEXT DEFAULT '',
            status TEXT DEFAULT 'تحویل شده',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ac_guest_traffic_report (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            card_number TEXT DEFAULT '',
            national_id TEXT DEFAULT '',
            terminal_name TEXT DEFAULT '',
            traffic_date TEXT DEFAULT '',
            entry_time TEXT DEFAULT '',
            exit_time TEXT DEFAULT '',
            unit_name TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ac_assign (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_type TEXT DEFAULT 'پرسنل',
            person_code TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            national_id TEXT DEFAULT '',
            display_name TEXT DEFAULT '',
            access_group TEXT DEFAULT '',
            card_code TEXT DEFAULT '',
            pin_code TEXT DEFAULT '',
            auth_type TEXT DEFAULT '',
            access_level TEXT DEFAULT '',
            issue_date TEXT DEFAULT '',
            expire_date TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ac_terminals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT DEFAULT '',
            ip_address TEXT DEFAULT '',
            mac_address TEXT DEFAULT '',
            serial_number TEXT DEFAULT '',
            group_name TEXT DEFAULT '',
            device_type TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            is_online INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ac_terminal_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT DEFAULT '',
            status TEXT DEFAULT 'آفلاین',
            last_sync TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ac_user_sync (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_code TEXT DEFAULT '',
            user_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            access_level TEXT DEFAULT '',
            person_type TEXT DEFAULT 'پرسنل',
            sync_status TEXT DEFAULT 'در انتظار',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ac_general_report (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_title TEXT DEFAULT '',
            report_date TEXT DEFAULT '',
            person_name TEXT DEFAULT '',
            event_type TEXT DEFAULT '',
            door_name TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)



    # —— جریان کار ——
    conn.execute("""
        CREATE TABLE IF NOT EXISTS wf_request_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_type TEXT NOT NULL,
            approver_count TEXT DEFAULT '1',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS wf_approvers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_type TEXT DEFAULT '',
            approver_name TEXT DEFAULT '',
            approver_username TEXT DEFAULT '',
            user_order TEXT DEFAULT '1',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS wf_delegation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_type TEXT DEFAULT '',
            from_user TEXT DEFAULT '',
            from_username TEXT DEFAULT '',
            to_user TEXT DEFAULT '',
            access_levels TEXT DEFAULT '',
            date_from TEXT DEFAULT '',
            date_to TEXT DEFAULT '',
            description TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS wf_parking_docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_type TEXT DEFAULT '',
            company_name TEXT DEFAULT '',
            personnel_name TEXT DEFAULT '',
            approval_stage TEXT DEFAULT 'مرحله اول',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)


    # —— جداول پشتیبان گزارش‌ها ——
    conn.execute("""
        CREATE TABLE IF NOT EXISTS guest_visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_name TEXT DEFAULT '',
            host_name TEXT DEFAULT '',
            visit_date TEXT DEFAULT '',
            entry_time TEXT DEFAULT '',
            exit_time TEXT DEFAULT '',
            purpose TEXT DEFAULT '',
            center_name TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS personnel_traffic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_name TEXT DEFAULT '',
            person_type TEXT DEFAULT 'پرسنل',
            direction TEXT DEFAULT 'ورود',
            traffic_date TEXT DEFAULT '',
            traffic_time TEXT DEFAULT '',
            door_name TEXT DEFAULT '',
            center_name TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_traffic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT DEFAULT '',
            driver_name TEXT DEFAULT '',
            person_type TEXT DEFAULT 'پرسنل',
            direction TEXT DEFAULT 'ورود',
            traffic_date TEXT DEFAULT '',
            center_name TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS goods_traffic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goods_name TEXT DEFAULT '',
            traffic_type TEXT DEFAULT '',
            direction TEXT DEFAULT 'ورود',
            traffic_date TEXT DEFAULT '',
            company_name TEXT DEFAULT '',
            is_contractor INTEGER DEFAULT 0,
            is_repair INTEGER DEFAULT 0,
            center_name TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS misc_person_traffic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_name TEXT DEFAULT '',
            direction TEXT DEFAULT 'ورود',
            traffic_date TEXT DEFAULT '',
            reason TEXT DEFAULT '',
            center_name TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS traffic_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_name TEXT DEFAULT '',
            request_date TEXT DEFAULT '',
            request_type TEXT DEFAULT '',
            status TEXT DEFAULT 'در انتظار',
            description TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS guest_reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_name TEXT DEFAULT '',
            reserve_date TEXT DEFAULT '',
            host_name TEXT DEFAULT '',
            status TEXT DEFAULT 'رزرو',
            center_name TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS goods_reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goods_name TEXT DEFAULT '',
            reserve_date TEXT DEFAULT '',
            requester TEXT DEFAULT '',
            status TEXT DEFAULT 'رزرو',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT DEFAULT '',
            log_time TEXT DEFAULT '',
            user_name TEXT DEFAULT '',
            action TEXT DEFAULT '',
            details TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    # —— خودروها (اطلاعات پایه) ——
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT DEFAULT '',
            plate_special TEXT DEFAULT '',
            vehicle_type TEXT DEFAULT '',
            color TEXT DEFAULT '',
            ownership TEXT DEFAULT 'ملکی',
            category TEXT DEFAULT 'خودرو',
            chassis_number TEXT DEFAULT '',
            traffic_limit TEXT DEFAULT '',
            card_status TEXT DEFAULT '',
            center_name TEXT DEFAULT '',
            unit_name TEXT DEFAULT '',
            personnel_name TEXT DEFAULT '',
            driver_name TEXT DEFAULT '',
            company_name TEXT DEFAULT '',
            description TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cargo_vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT DEFAULT '',
            plate_special TEXT DEFAULT '',
            vehicle_type TEXT DEFAULT '',
            chassis_number TEXT DEFAULT '',
            driver_name TEXT DEFAULT '',
            driver_phone TEXT DEFAULT '',
            company_name TEXT DEFAULT '',
            vehicle_weight TEXT DEFAULT '',
            max_weight TEXT DEFAULT '',
            description TEXT DEFAULT '',
            is_blocked INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cargo_traffic_reasons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reason TEXT NOT NULL,
            traffic_type TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    # —— کالاها (اطلاعات پایه) ——
    conn.execute("""
        CREATE TABLE IF NOT EXISTS goods_entry_exit_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS goods_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_name TEXT DEFAULT '',
            barcode TEXT DEFAULT '',
            name TEXT NOT NULL,
            goods_type TEXT DEFAULT '',
            count_unit TEXT DEFAULT '',
            serial_number TEXT DEFAULT '',
            product_specs TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_goods_barcode ON goods_products(barcode)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_goods_name ON goods_products(name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_plate ON vehicles(plate_number)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cargo_plate ON cargo_vehicles(plate_number)")
    # seed پیش‌فرض انواع استخدام (اگر خالی باشد)
    cnt = conn.execute("SELECT COUNT(*) FROM employment_types").fetchone()[0]
    if cnt == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for name in ("رسمی", "رسمی-استخدامی", "آزمایشی", "رسمی-انتقالی", "مامور", "پیمانکار", "قراردادی"):
            conn.execute(
                "INSERT INTO employment_types (name, created_at) VALUES (?, ?)",
                (name, now),
            )
    cnt2 = conn.execute("SELECT COUNT(*) FROM education_fields").fetchone()[0]
    if cnt2 == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for name in ("نامشخص", "مهندسی نرم‌افزار", "حقوق", "مهندسی مکانیک", "حسابداری", "مدیریت"):
            conn.execute(
                "INSERT INTO education_fields (name, created_at) VALUES (?, ?)",
                (name, now),
            )
    cnt3 = conn.execute("SELECT COUNT(*) FROM responsibility_groups").fetchone()[0]
    if cnt3 == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO responsibility_groups (name, created_at) VALUES (?, ?)",
            ("گروه ۱", now),
        )


# —— CRUD واحدها ——

def list_units(company_code: int = None, q: str = None) -> list:
    with get_companies_db() as conn:
        _init_lookup_tables(conn)
        sql = "SELECT * FROM units WHERE 1=1"
        params = []
        if company_code is not None:
            sql += " AND (company_code=? OR company_code IS NULL)"
            params.append(int(company_code))
        if q:
            sql += " AND (name LIKE ? OR code LIKE ? OR center_name LIKE ? OR parent_name LIKE ?)"
            like = f"%{q}%"
            params.extend([like, like, like, like])
        sql += " ORDER BY id DESC"
        return [row_to_dict(r) for r in conn.execute(sql, params).fetchall()]


def create_unit(data: dict) -> dict:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_companies_db() as conn:
        _init_lookup_tables(conn)
        cur = conn.execute(
            """
            INSERT INTO units (code, name, parent_name, center_name, company_code,
                               show_on_guard_board, show_on_internet, image_path, symbol_path,
                               created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("code", ""),
                data.get("name", ""),
                data.get("parent_name", ""),
                data.get("center_name", ""),
                data.get("company_code"),
                1 if data.get("show_on_guard_board", True) else 0,
                1 if data.get("show_on_internet", False) else 0,
                data.get("image_path", "") or "",
                data.get("symbol_path", "") or "",
                now, now,
            ),
        )
        row = conn.execute("SELECT * FROM units WHERE id=?", (cur.lastrowid,)).fetchone()
        return row_to_dict(row)


def update_unit(uid: int, data: dict) -> dict | None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fields = ["code", "name", "parent_name", "center_name", "company_code",
              "show_on_guard_board", "show_on_internet", "image_path", "symbol_path"]
    sets, values = [], []
    for f in fields:
        if f in data:
            val = data[f]
            if f in ("show_on_guard_board", "show_on_internet"):
                val = 1 if val else 0
            sets.append(f"{f}=?")
            values.append(val)
    if not sets:
        with get_companies_db() as conn:
            row = conn.execute("SELECT * FROM units WHERE id=?", (uid,)).fetchone()
            return row_to_dict(row) if row else None
    sets.append("updated_at=?")
    values.append(now)
    values.append(uid)
    with get_companies_db() as conn:
        conn.execute(f"UPDATE units SET {', '.join(sets)} WHERE id=?", values)
        row = conn.execute("SELECT * FROM units WHERE id=?", (uid,)).fetchone()
        return row_to_dict(row) if row else None


def delete_unit(uid: int) -> bool:
    with get_companies_db() as conn:
        cur = conn.execute("DELETE FROM units WHERE id=?", (uid,))
        return cur.rowcount > 0


# —— CRUD ساده برای جداول نامی ——

def _list_named(table: str) -> list:
    with get_companies_db() as conn:
        _init_lookup_tables(conn)
        return [row_to_dict(r) for r in conn.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()]


def _create_named(table: str, name: str) -> dict:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    name = (name or "").strip()
    if not name:
        raise ValueError("نام الزامی است")
    with get_companies_db() as conn:
        _init_lookup_tables(conn)
        try:
            cur = conn.execute(
                f"INSERT INTO {table} (name, created_at) VALUES (?, ?)", (name, now)
            )
        except sqlite3.IntegrityError:
            raise ValueError("این نام قبلاً ثبت شده است")
        row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (cur.lastrowid,)).fetchone()
        return row_to_dict(row)


def _update_named(table: str, rid: int, name: str) -> dict | None:
    name = (name or "").strip()
    if not name:
        raise ValueError("نام الزامی است")
    with get_companies_db() as conn:
        try:
            conn.execute(f"UPDATE {table} SET name=? WHERE id=?", (name, rid))
        except sqlite3.IntegrityError:
            raise ValueError("این نام قبلاً ثبت شده است")
        row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (rid,)).fetchone()
        return row_to_dict(row) if row else None


def _delete_named(table: str, rid: int) -> bool:
    with get_companies_db() as conn:
        cur = conn.execute(f"DELETE FROM {table} WHERE id=?", (rid,))
        return cur.rowcount > 0


def list_education_fields():
    return _list_named("education_fields")

def create_education_field(name: str):
    return _create_named("education_fields", name)

def update_education_field(rid: int, name: str):
    return _update_named("education_fields", rid, name)

def delete_education_field(rid: int):
    return _delete_named("education_fields", rid)


def list_responsibility_groups():
    return _list_named("responsibility_groups")

def create_responsibility_group(name: str):
    return _create_named("responsibility_groups", name)

def update_responsibility_group(rid: int, name: str):
    return _update_named("responsibility_groups", rid, name)

def delete_responsibility_group(rid: int):
    return _delete_named("responsibility_groups", rid)


def list_employment_types():
    return _list_named("employment_types")

def create_employment_type(name: str):
    return _create_named("employment_types", name)

def update_employment_type(rid: int, name: str):
    return _update_named("employment_types", rid, name)

def delete_employment_type(rid: int):
    return _delete_named("employment_types", rid)



def seed_demo_records(force: bool = False) -> dict:
    """
    ثبت حداقل یک رکورد نمونه برای همهٔ فرم‌ها/جداول تا مسیر UI قابل تست باشد.
    فقط روی جداول خالی می‌نویسد (مگر force=True).
    """
    ensure_company_database()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {}

    with get_main_db() as conn:
        def empty(table):
            return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0

        # —— اطلاعات پایه: واحد / مرکز ——
        if force or empty("units"):
            units = [
                ("701", "پیام گستر", "", "شرکت پیام گستر", 100, 1, 0),
                ("703", "تست", "پیام گستر", "شرکت پیام گستر", 100, 1, 0),
                ("708", "سیمان", "تست", "شرکت پیام گستر", 100, 1, 0),
                ("801", "حراست ستاد", "", "تأسیسات دریایی ایران (ستاد)", 100, 1, 0),
                ("901", "عملیات جنوب", "", "شرکت ملی مناطق نفت‌خیز جنوب", 101, 1, 0),
            ]
            for code, name, parent, center, ccode, guard, net in units:
                conn.execute(
                    """INSERT INTO units (code, name, parent_name, center_name, company_code,
                       show_on_guard_board, show_on_internet, created_at, updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (code, name, parent, center, ccode, guard, net, now, now),
                )
            report["units"] = len(units)
        else:
            report["units"] = "skip"

        # —— رشته / گروه / استخدام (اگر خالی) ——
        if force or empty("education_fields"):
            for n in ("نامشخص", "مهندسی نرم‌افزار", "مهندسی مکانیک", "حسابداری", "حقوق"):
                conn.execute("INSERT OR IGNORE INTO education_fields (name, created_at) VALUES (?,?)", (n, now))
            report["education_fields"] = 5
        else:
            report["education_fields"] = "skip"

        if force or empty("responsibility_groups"):
            for n in ("گروه ۱", "گروه ۲", "مدیران", "نگهبانی"):
                conn.execute("INSERT OR IGNORE INTO responsibility_groups (name, created_at) VALUES (?,?)", (n, now))
            report["responsibility_groups"] = 4
        else:
            report["responsibility_groups"] = "skip"

        if force or empty("employment_types"):
            for n in ("رسمی", "رسمی استخدامی", "آزمایشی", "پیمانکار", "قراردادی", "مامور"):
                conn.execute("INSERT OR IGNORE INTO employment_types (name, created_at) VALUES (?,?)", (n, now))
            report["employment_types"] = 6
        else:
            report["employment_types"] = "skip"

        # —— درب‌های تردد ——
        if force or empty("access_doors"):
            doors = [
                ("D01", "درب اصلی", "تردد پرسنل و ارباب رجوع", "ورود", "شرکت پیام گستر", "192.168.1.10", "ورودی شمالی", "کارت‌خوان", "دستگاه ۱", "T-100", 1),
                ("D02", "درب خودرویی", "پارکینگ", "ورود", "شرکت پیام گستر", "192.168.1.11", "پارکینگ جنوب", "پلاک‌خوان", "دستگاه ۲", "T-200", 1),
                ("D03", "خروجی سازمان", "خروجی سازمان", "خروج", "تأسیسات دریایی ایران (ستاد)", "10.0.0.5", "خروج شرقی", "کارت‌خوان", "دستگاه ۳", "T-300", 1),
            ]
            for row in doors:
                conn.execute(
                    """INSERT INTO access_doors
                    (code, name, door_type, direction, center_name, ip_address, road_address,
                     device_type, device_name, terminal_id, is_active, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (*row, now, now),
                )
            report["access_doors"] = len(doors)
        else:
            report["access_doors"] = "skip"

        # —— مقصد کالا ——
        if force or empty("goods_destinations"):
            dests = [
                ("انبار مرکزی", "02111111111", "02122222222", "تهران، جاده مخصوص", "مقصد نمونه"),
                ("پالایشگاه جنوب", "06133333333", "", "اهواز", ""),
            ]
            for name, p1, p2, addr, desc in dests:
                conn.execute(
                    """INSERT INTO goods_destinations (name, phone1, phone2, address, description, created_at, updated_at)
                       VALUES (?,?,?,?,?,?,?)""",
                    (name, p1, p2, addr, desc, now, now),
                )
            report["goods_destinations"] = len(dests)
        else:
            report["goods_destinations"] = "skip"

        # —— سرویس ——
        if force or empty("services"):
            for n in ("مسیر سرویس شمال", "مسیر سرویس جنوب", "خط ویژه ستاد"):
                conn.execute("INSERT OR IGNORE INTO services (name, description, created_at) VALUES (?,?,?)", (n, "", now))
            report["services"] = 3
        else:
            report["services"] = "skip"

        # —— شرکت/مشتری ——
        if force or empty("client_companies"):
            clients = [
                ("شرکت الف پیمانکار", "C001", "02144445555", "تهران", "پیمانکار نمونه"),
                ("شرکت ب تأمین", "C002", "02166667777", "اصفهان", ""),
            ]
            for name, code, phone, addr, desc in clients:
                conn.execute(
                    """INSERT INTO client_companies (name, code, phone, address, description, created_at, updated_at)
                       VALUES (?,?,?,?,?,?,?)""",
                    (name, code, phone, addr, desc, now, now),
                )
            report["client_companies"] = len(clients)
        else:
            report["client_companies"] = "skip"

        # —— نوع ورود/خروج ——
        if force or empty("entry_exit_types"):
            types = [
                ("اضافه کار", 1, 1),
                ("تأخیر", 1, 1),
                ("ماموریت روزانه", 1, 1),
                ("مرخصی ساعتی", 1, 1),
                ("عادی", 1, 1),
            ]
            for name, ie, ix in types:
                conn.execute(
                    "INSERT INTO entry_exit_types (name, is_entry, is_exit, created_at) VALUES (?,?,?,?)",
                    (name, ie, ix, now),
                )
            report["entry_exit_types"] = len(types)
        else:
            report["entry_exit_types"] = "skip"

        # —— دسترسی کاربر به درب ——
        if force or empty("door_user_access"):
            for door, user in (("درب اصلی", "اپراتور نگهبانی"), ("درب خودرویی", "اپراتور پارکینگ"), ("درب اصلی", "مدیر حراست")):
                conn.execute(
                    "INSERT INTO door_user_access (door_name, user_name, created_at) VALUES (?,?,?)",
                    (door, user, now),
                )
            report["door_user_access"] = 3
        else:
            report["door_user_access"] = "skip"

        if force or empty("door_access_levels"):
            for n in ("سطح عادی", "سطح مدیریت", "سطح ویژه"):
                conn.execute(
                    "INSERT OR IGNORE INTO door_access_levels (name, description, created_at) VALUES (?,?,?)",
                    (n, "", now),
                )
            report["door_access_levels"] = 3
        else:
            report["door_access_levels"] = "skip"

        # —— پرسنل کامل‌تر (اگر هیچ رکوردی با فیلدهای پایه پر نیست، یک نمونه غنی اضافه کن) ——
        rich = conn.execute(
            "SELECT id FROM personnel WHERE department IS NOT NULL AND department != '' LIMIT 1"
        ).fetchone()
        if force or not rich:
            # یک پرسنل کامل برای تست فرم تعریف پرسنل
            conn.execute(
                """
                INSERT INTO personnel (
                    row_num, indicator_num, first_name, last_name, father_name, national_id,
                    gender, birth_date, birth_place, religion, denomination, blood_type,
                    nationality, marital_status, company_code, company, center, department,
                    position, workplace, responsibility_group, hire_date, employment_type,
                    education_degree, education_field, military_status, phone, email,
                    active_status, card_status, is_native, banned_entry, show_on_internet,
                    created_at, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    "10", "5001", "امیر", "رضایی", "محمد", "0011223344",
                    "مرد", "1368/01/15", "تهران", "اسلام", "شیعه", "O+",
                    "ایرانی", "متاهل", "100", "تأسیسات دریایی ایران (ستاد)",
                    "شرکت پیام گستر", "حراست ستاد", "کارشناس حراست", "ستاد",
                    "گروه ۱", "1395/06/01", "رسمی",
                    "کارشناسی", "مهندسی نرم‌افزار", "پایان خدمت", "09120001122", "amir@example.com",
                    "فعال", "فعال", "خیر", "خیر", "خیر",
                    now, now,
                ),
            )
            report["personnel_rich"] = 1
        else:
            report["personnel_rich"] = "skip"

        # —— وابستگان ——
        pid_row = conn.execute(
            "SELECT id FROM personnel ORDER BY id DESC LIMIT 1"
        ).fetchone()
        pid = int(pid_row[0]) if pid_row else None
        if pid and (force or empty("dependents")):
            deps = [
                (pid, "سارا", "رضایی", "0011223355", "همسر", "1370/03/10", "زن", "09123334455"),
                (pid, "محمد", "رضایی", "0011223366", "فرزند", "1398/07/20", "مرد", ""),
            ]
            for d in deps:
                conn.execute(
                    """INSERT INTO dependents
                    (personnel_id, first_name, last_name, national_id, relation, birth_date, gender, phone, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (*d, now, now),
                )
            report["dependents"] = len(deps)
        else:
            report["dependents"] = "skip"

        # —— کارت ——
        if pid and (force or empty("access_cards")):
            conn.execute(
                """INSERT INTO access_cards
                (personnel_id, card_number, card_type, issue_date, expiry_date, status, printed, description, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (pid, "CARD-5001", "شناسایی", "1403/01/01", "1405/01/01", "فعال", 1, "کارت نمونه", now, now),
            )
            conn.execute(
                "UPDATE personnel SET card_number=? WHERE id=?",
                ("CARD-5001", pid),
            )
            report["access_cards"] = 1
        else:
            report["access_cards"] = "skip"

        # —— سوابق پرسنل (خدمت / سفر / پزشکی) ——
        if pid and (force or empty("personnel_service_history")):
            conn.execute(
                """INSERT INTO personnel_service_history
                (personnel_id, from_date, to_date, organization, position, unit_name, description, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (pid, "1400/01/01", "1404/12/29", "تأسیسات دریایی ایران", "کارشناس حراست", "حراست", "سابقه خدمت نمونه", now, now),
            )
            report["personnel_service_history"] = 1
        else:
            report["personnel_service_history"] = "skip"
        if pid and (force or empty("personnel_travel")):
            conn.execute(
                """INSERT INTO personnel_travel
                (personnel_id, country, from_date, to_date, purpose, visa_no, description, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (pid, "ایران - تهران", "1405/06/01", "1405/06/05", "ماموریت اداری", "", "سفر نمونه", now, now),
            )
            report["personnel_travel"] = 1
        else:
            report["personnel_travel"] = "skip"
        if pid and (force or empty("personnel_medical")):
            conn.execute(
                """INSERT INTO personnel_medical
                (personnel_id, record_date, record_type, diagnosis, physician, description, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                (pid, "1405/05/01", "معاینه دوره‌ای", "سالم", "دکتر نمونه", "پرونده پزشکی نمونه", now, now),
            )
            report["personnel_medical"] = 1
        else:
            report["personnel_medical"] = "skip"

        # —— انتظامات ——
        def _ent_empty(t):
            return conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] == 0

        if force or _ent_empty("ent_groups"):
            for name, center in (("گروه ۱", "شرکت پیام گستر"), ("الف", "شرکت پیام گستر")):
                conn.execute(
                    "INSERT INTO ent_groups (name, center_name, created_at) VALUES (?,?,?)",
                    (name, center, now),
                )
            report["ent_groups"] = 2
        if force or _ent_empty("ent_protection_centers"):
            for name, center in (("مرکز ۱", "شرکت پیام گستر"), ("مرکز یک", "شرکت پیام گستر"), ("مرکز دو", "شرکت پیام گستر")):
                conn.execute(
                    "INSERT INTO ent_protection_centers (name, center_name, created_at) VALUES (?,?,?)",
                    (name, center, now),
                )
            report["ent_protection_centers"] = 3
        if force or _ent_empty("ent_protection_places"):
            conn.execute(
                "INSERT INTO ent_protection_places (place_name, protection_center_name, center_name, created_at) VALUES (?,?,?,?)",
                ("مکان ۱", "مرکز ۱", "شرکت پیام گستر", now),
            )
            report["ent_protection_places"] = 1
        if force or _ent_empty("ent_shift_hours"):
            for name, st, et in (
                ("صبح", "۰۷:۰۰", "۱۵:۰۰"),
                ("عصر", "۱۵:۰۰", "۲۳:۰۰"),
                ("شب", "۲۳:۰۰", "۰۷:۰۰"),
            ):
                conn.execute(
                    "INSERT INTO ent_shift_hours (name, center_name, start_time, end_time, created_at) VALUES (?,?,?,?,?)",
                    (name, "شرکت پیام گستر", st, et, now),
                )
            report["ent_shift_hours"] = 3
        if force or _ent_empty("ent_shift_leaders"):
            for row in (
                ("شرکت پیام گستر", "حراست", "پیام گستر", "صبح", "مسئول شیفت"),
                ("شرکت پیام گستر", "حراست", "Fname1 Lname1", "شب", "مسئول شیفت"),
                ("شرکت پیام گستر", "حراست", "Fname2 Lname2", "شب", "جانشین شیفت"),
            ):
                conn.execute(
                    """INSERT INTO ent_shift_leaders
                    (center_name, unit_name, person_name, shift_name, role_type, created_at)
                    VALUES (?,?,?,?,?,?)""",
                    (*row, now),
                )
            report["ent_shift_leaders"] = 3
        if force or _ent_empty("ent_work_shifts"):
            for name in ("A", "B", "C", "D"):
                conn.execute(
                    "INSERT INTO ent_work_shifts (name, center_name, created_at) VALUES (?,?,?)",
                    (name, "شرکت پیام گستر", now),
                )
            report["ent_work_shifts"] = 4
        if force or _ent_empty("ent_staff_status"):
            for name in ("حاضر", "غایب", "تاخیر", "تعجیل", "جانشین", "مرخصی"):
                conn.execute(
                    "INSERT OR IGNORE INTO ent_staff_status (name, created_at) VALUES (?,?)",
                    (name, now),
                )
            report["ent_staff_status"] = 6
        if force or _ent_empty("ent_guard_equipment"):
            for row in (
                ("شرکت پیام گستر", "باتوم", "545", "A-01"),
                ("شرکت پیام گستر", "اسلحه", "848", ""),
            ):
                conn.execute(
                    """INSERT INTO ent_guard_equipment
                    (center_name, device_name, serial_number, asset_number, created_at)
                    VALUES (?,?,?,?,?)""",
                    (*row, now),
                )
            report["ent_guard_equipment"] = 2

        # —— انتظامات عملیاتی (نمونه تست) ——
        if force or _ent_empty("ent_guard_board"):
            conn.execute(
                """INSERT INTO ent_guard_board
                (center_name, shift_name, work_shift, shift_date, shift_leader, shift_deputy, description, created_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                ("شرکت پیام گستر", "صبح", "A", "1405/07/15", "پیام گستر", "جانشین نمونه", "لوح نمونه تست", now),
            )
            report["ent_guard_board"] = 1
        if force or _ent_empty("ent_shift_events"):
            conn.execute(
                "INSERT INTO ent_shift_events (center_name, shift_name, event_date, event_text, reporter, created_at) VALUES (?,?,?,?,?,?)",
                ("شرکت پیام گستر", "صبح", "1405/07/15", "بازرسی دوره‌ای انجام شد", "مسئول شیفت", now),
            )
            report["ent_shift_events"] = 1
        if force or _ent_empty("ent_shift_schedule"):
            conn.execute(
                "INSERT INTO ent_shift_schedule (center_name, work_shift, personnel_name, date_from, date_to, notes, created_at) VALUES (?,?,?,?,?,?,?)",
                ("شرکت پیام گستر", "A", "امیر رضایی", "1405/07/01", "1405/07/31", "برنامه ماهانه", now),
            )
            report["ent_shift_schedule"] = 1
        if force or _ent_empty("ent_personnel_electronics"):
            conn.execute(
                "INSERT INTO ent_personnel_electronics (personnel_name, device_name, serial_number, center_name, created_at) VALUES (?,?,?,?,?)",
                ("امیر رضایی", "بی‌سیم", "WR-100", "شرکت پیام گستر", now),
            )
            report["ent_personnel_electronics"] = 1
        if force or _ent_empty("ent_replacement_requests"):
            conn.execute(
                "INSERT INTO ent_replacement_requests (requester_name, replacement_name, shift_name, request_date, reason, status, created_at) VALUES (?,?,?,?,?,?,?)",
                ("علی محمدی", "حسین احمدی", "شب", "1405/07/10", "مرخصی اضطراری", "در انتظار", now),
            )
            report["ent_replacement_requests"] = 1
        if force or _ent_empty("ent_permits"):
            conn.execute(
                "INSERT INTO ent_permits (permit_type, personnel_name, center_name, date_from, date_to, description, created_at) VALUES (?,?,?,?,?,?,?)",
                ("تردد ویژه", "امیر رضایی", "شرکت پیام گستر", "1405/07/01", "1405/07/30", "مجوز نمونه", now),
            )
            report["ent_permits"] = 1
        if force or _ent_empty("ent_monitoring_events"):
            conn.execute(
                "INSERT INTO ent_monitoring_events (center_name, shift_name, event_date, event_text, created_at) VALUES (?,?,?,?,?)",
                ("شرکت پیام گستر", "صبح", "1405/07/15", "دوربین ورودی بررسی شد", now),
            )
            report["ent_monitoring_events"] = 1
        if force or _ent_empty("ent_monitoring_staff"):
            conn.execute(
                "INSERT INTO ent_monitoring_staff (center_name, person_name, role_name, shift_name, created_at) VALUES (?,?,?,?,?)",
                ("شرکت پیام گستر", "رضا کریمی", "اپراتور مانیتورینگ", "صبح", now),
            )
            report["ent_monitoring_staff"] = 1
        if force or _ent_empty("ent_guard_reports"):
            conn.execute(
                "INSERT INTO ent_guard_reports (center_name, report_date, title, body, created_at) VALUES (?,?,?,?,?)",
                ("شرکت پیام گستر", "1405/07/15", "گزارش روزانه", "شیفت بدون حادثه خاص پایان یافت.", now),
            )
            report["ent_guard_reports"] = 1
        if force or _ent_empty("ent_guard_referrals"):
            conn.execute(
                "INSERT INTO ent_guard_referrals (center_name, report_date, referred_to, body, created_at) VALUES (?,?,?,?,?)",
                ("شرکت پیام گستر", "1405/07/14", "حراست ستاد", "ارجاع مورد مشکوک برای بررسی", now),
            )
            report["ent_guard_referrals"] = 1
        if force or _ent_empty("ent_roll_call"):
            conn.execute(
                "INSERT INTO ent_roll_call (center_name, call_date, personnel_name, status, notes, created_at) VALUES (?,?,?,?,?,?)",
                ("شرکت پیام گستر", "1405/07/15", "رایان پایمز", "مرخصی", "", now),
            )
            report["ent_roll_call"] = 1
        if force or _ent_empty("ent_news_reports"):
            conn.execute(
                "INSERT INTO ent_news_reports (title, report_date, body, created_at) VALUES (?,?,?,?)",
                ("خبر انتظامات", "1405/07/15", "تمرین مانور آتش‌نشانی برگزار شد.", now),
            )
            report["ent_news_reports"] = 1
        if force or _ent_empty("ent_guard_board_summary"):
            conn.execute(
                "INSERT INTO ent_guard_board_summary (center_name, summary_date, summary_text, created_at) VALUES (?,?,?,?)",
                ("شرکت پیام گستر", "1405/07/15", "خلاصه لوح: شیفت صبح عادی", now),
            )
            report["ent_guard_board_summary"] = 1
        if force or _ent_empty("ent_guard_events"):
            conn.execute(
                "INSERT INTO ent_guard_events (center_name, event_date, event_text, officer_name, created_at) VALUES (?,?,?,?,?)",
                ("شرکت پیام گستر", "1405/07/15", "گشت محوطه انجام شد", "افسر نگهبان", now),
            )
            report["ent_guard_events"] = 1
        if force or _ent_empty("ent_deployment_locations"):
            conn.execute(
                "INSERT INTO ent_deployment_locations (code, name, center_name, created_at) VALUES (?,?,?,?)",
                ("LOC-01", "ورودی اصلی", "شرکت پیام گستر", now),
            )
            report["ent_deployment_locations"] = 1
        if force or _ent_empty("ent_officer_events"):
            conn.execute(
                "INSERT INTO ent_officer_events (officer_name, event_date, event_text, center_name, created_at) VALUES (?,?,?,?,?)",
                ("افسر نگهبان", "1405/07/15", "تحویل شیفت بدون مورد", "شرکت پیام گستر", now),
            )
            report["ent_officer_events"] = 1

        # —— صدور کارت (نمونه تست) ——
        if force or _ent_empty("card_personnel"):
            conn.execute(
                """INSERT INTO card_personnel
                (personnel_code, national_id, first_name, last_name, unit_name, membership_type,
                 card_status, issue_date, expiry_date, alphabetical, print_front, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("2008", "0012345678", "Fname1", "Lname1", "تست", "رسمی",
                 "فعال", "1404/10/17", "1406/10/17", 0, 1, "کارت پرسنل نمونه", now),
            )
            report["card_personnel"] = 1
        if force or _ent_empty("card_contractor"):
            conn.execute(
                """INSERT INTO card_contractor
                (personnel_code, national_id, first_name, last_name, company_name, activity_unit,
                 card_status, issue_date, expiry_date, alphabetical, print_front, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("19751036", "0019751036", "صالح", "رضوانی", "شرکت پیمانکار", "واحد پیمانکار",
                 "فعال", "1404/05/07", "1405/05/07", 0, 1, "کارت پیمانکار نمونه", now),
            )
            report["card_contractor"] = 1
        if force or _ent_empty("card_vehicle_personnel"):
            conn.execute(
                """INSERT INTO card_vehicle_personnel
                (plate_number, vehicle_type, unit_name, personnel_code, driver_name,
                 card_status, issue_date, expiry_date, alphabetical, print_front, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("۱۲ ب ۳۴۵ - ۱۱", "سواری", "تست", "2008", "Fname1 Lname1",
                 "فعال", "1404/06/23", "1406/06/23", 0, 1, "کارت خودروی پرسنل نمونه", now),
            )
            report["card_vehicle_personnel"] = 1
        if force or _ent_empty("card_vehicle_contractor"):
            conn.execute(
                """INSERT INTO card_vehicle_contractor
                (plate_number, vehicle_type, company_name, activity_unit, driver_name, traffic_area,
                 card_number, certificate_number, card_status, issue_date, expiry_date,
                 alphabetical, print_front, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("۹۸ ص ۶۵۴ - ۱۶", "وانت", "شرکت پیمانکار", "واحد پیمانکار", "نام راننده پیمانکار", "محدوده ۱",
                 "VC-001", "CERT-100", "فعال", "1404/06/23", "1405/06/23",
                 0, 1, "کارت خودروی پیمانکار نمونه", now),
            )
            report["card_vehicle_contractor"] = 1

        # —— پیمانکاران (نمونه تست) ——
        if force or _ent_empty("ctr_companies"):
            conn.execute(
                """INSERT INTO ctr_companies
                (name, company_code, parent_company, employer_company, register_date, ceo_mobile, rep1_mobile,
                 company_phone, rep1_name, supervisor_name, ceo_name, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("شرکت پیمانکار نمونه", "666", "", "تأسیسات دریایی ایران (ستاد)", "1405/01/15", "09126666666", "09121111111",
                 "02188888888", "نماینده یک", "ناظر نمونه", "مدیرعامل نمونه", "شرکت پیمانکار نمونه برای تست", now),
            )
            report["ctr_companies"] = 1
        if force or _ent_empty("ctr_contracts"):
            conn.execute(
                """INSERT INTO ctr_contracts
                (company_name, contract_subject, activity_location, tender_number, contract_number,
                 start_date, end_date, contract_amount, contract_status, supervisor_unit, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("شرکت پیمانکار نمونه", "شبکه ای", "محل فعالیت نمونه", "مناقصه-۱", "101010",
                 "1405/01/15", "1406/12/29", "۵۰۰۰۰۰۰۰۰", "فعال", "واحد ناظر", "قرارداد نمونه", now),
            )
            report["ctr_contracts"] = 1
        if force or _ent_empty("ctr_personnel"):
            conn.execute(
                """INSERT INTO ctr_personnel
                (company_name, contract_number, personnel_code, first_name, last_name, father_name,
                 national_id, mobile_phone, card_status, activity_unit, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("شرکت پیمانکار نمونه", "101010", "8", "صالح", "رضوانی", "علیرضا",
                 "0019751036", "09121234567", "فعال", "واحد پیمانکار", "پرسنل پیمانکار نمونه", now),
            )
            report["ctr_personnel"] = 1
        if force or _ent_empty("ctr_vehicles"):
            conn.execute(
                """INSERT INTO ctr_vehicles
                (plate_number, company_name, owner_last_name, owner_first_name, vehicle_type,
                 vehicle_class, vehicle_color, activity_unit, card_status, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                ("۱۱ ب ۱۱۱ - ۱۱", "شرکت پیمانکار نمونه", "مالک", "نمونه", "کامیونتک",
                 "باری", "سفید", "واحد پیمانکار", "فعال", "خودروی پیمانکار نمونه", now),
            )
            report["ctr_vehicles"] = 1
        if force or _ent_empty("ctr_drivers"):
            conn.execute(
                """INSERT INTO ctr_drivers
                (company_name, personnel_code, driver_name, father_name, national_id,
                 license_type, license_number, license_end_date, card_status, position, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("شرکت پیمانکار نمونه", "8", "راننده نمونه", "پدر نمونه", "0012345678",
                 "پایه دو", "LIC-2001", "1406/07/15", "فعال", "راننده", "راننده پیمانکار نمونه", now),
            )
            report["ctr_drivers"] = 1

        # —— گشت و پایش (نمونه تست) ——
        if force or _ent_empty("patrol_devices"):
            for row in (
                ("شرکت پیام گستر", "53791", "تصویری", "پورت USB"),
                ("شرکت پیام گستر", "53561", "احساسی", "پورت USB"),
            ):
                conn.execute(
                    """INSERT INTO patrol_devices
                    (center_name, device_code, device_name, usb_port, connected_port, notes, created_at)
                    VALUES (?,?,?,?,?,?,?)""",
                    (*row, "پورت متصل", "دستگاه نمونه", now),
                )
            report["patrol_devices"] = 2
        if force or _ent_empty("patrol_events"):
            conn.execute(
                """INSERT INTO patrol_events (event_code, event_name, importance, notes, created_at)
                VALUES (?,?,?,?,?)""",
                ("1", "صادق", "مهم", "رخداد نمونه", now),
            )
            report["patrol_events"] = 1
        if force or _ent_empty("patrol_checkpoints"):
            conn.execute(
                """INSERT INTO patrol_checkpoints
                (checkpoint_code, checkpoint_name, center_name, connected_port, notes, created_at)
                VALUES (?,?,?,?,?,?)""",
                ("CP-01", "نقطه ورودی اصلی", "شرکت پیام گستر", "پورت USB", "نقطه بازدید نمونه", now),
            )
            report["patrol_checkpoints"] = 1
        if force or _ent_empty("patrol_guards"):
            conn.execute(
                """INSERT INTO patrol_guards
                (guard_id, first_name, last_name, personnel_code, unit_name, center_name, connected_port, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                ("BA-V2000", "جواد", "رجبی", "2006", "پیام گستر", "شرکت پیام گستر", "پورت USB", "نگهبان نمونه", now),
            )
            report["patrol_guards"] = 1
        if force or _ent_empty("patrol_routes"):
            conn.execute(
                """INSERT INTO patrol_routes
                (route_name, center_name, start_time, end_time, checkpoint_names, description, created_at)
                VALUES (?,?,?,?,?,?,?)""",
                ("مسیر صبح شمالی", "شرکت پیام گستر", "۰۷:۰۰", "۱۵:۰۰", "ورودی اصلی، پارکینگ", "مسیر نمونه", now),
            )
            report["patrol_routes"] = 1
        if force or _ent_empty("patrol_route_config"):
            conn.execute(
                """INSERT INTO patrol_route_config
                (route_name, guard_name, device_name, sequence_order, notes, created_at)
                VALUES (?,?,?,?,?,?)""",
                ("مسیر صبح شمالی", "جواد رجبی", "تصویری", "1", "پیکربندی نمونه", now),
            )
            report["patrol_route_config"] = 1
        if force or _ent_empty("patrol_shift_times"):
            conn.execute(
                """INSERT INTO patrol_shift_times
                (center_name, route_name, start_time, end_time, shift_name, notes, created_at)
                VALUES (?,?,?,?,?,?,?)""",
                ("شرکت پیام گستر", "مسیر صبح شمالی", "۰۷:۰۰", "۱۵:۰۰", "صبح", "ساعت شیفت نمونه", now),
            )
            report["patrol_shift_times"] = 1


        # —— حراست (نمونه تست) ——
        if force or _ent_empty("hr_eval_options"):
            conn.execute(
                """INSERT INTO hr_eval_options
                (group_name, option1, score1, option2, score2, option3, score3, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                ("گروه ۱", "س", "۲", "ش", "۵", "گزینه ۳", "۱", "گزینه ارزشیابی نمونه", now),
            )
            report["hr_eval_options"] = 1
        if force or _ent_empty("hr_eval_titles"):
            conn.execute(
                "INSERT INTO hr_eval_titles (title_text, score, answer_type, option_count, notes, created_at) VALUES (?,?,?,?,?,?)",
                ("تأدیب", "۳", "امتیازی", "۳", "عنوان ارزشیابی نمونه", now),
            )
            report["hr_eval_titles"] = 1
        if force or _ent_empty("hr_eval_periods"):
            conn.execute(
                "INSERT INTO hr_eval_periods (period_title, notes, created_at) VALUES (?,?,?)",
                ("دوره ۱", "دوره ارزشیابی نمونه", now),
            )
            report["hr_eval_periods"] = 1
        if force or _ent_empty("hr_eval_monthly"):
            conn.execute(
                """INSERT INTO hr_eval_monthly
                (personnel_name, unit_name, period_title, supervisor_name, supervisor_opinion, eval_date, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                ("رایان پیله‌ور", "واحد ۱", "دوره ۱", "رایان پیله‌ور", "خوب می باشد", "1405/07/15", "ارزشیابی ماهانه نمونه", now),
            )
            report["hr_eval_monthly"] = 1
        if force or _ent_empty("hr_areas"):
            conn.execute("INSERT INTO hr_areas (area_name, notes, created_at) VALUES (?,?,?)", ("ناحیه شمالی", "ناحیه نمونه", now))
            report["hr_areas"] = 1
        if force or _ent_empty("hr_houses"):
            conn.execute("INSERT INTO hr_houses (house_name, notes, created_at) VALUES (?,?,?)", ("منزل ۱۲۳۴۵۶۷۸", "منزل نمونه", now))
            report["hr_houses"] = 1
        if force or _ent_empty("hr_house_delivery"):
            conn.execute(
                """INSERT INTO hr_house_delivery
                (area_name, house_name, personnel_name, personnel_code, related_office, delivery_date, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                ("ناحیه شمالی", "منزل ۱۲۳۴۵۶۷۸", "امیر رضایی", "1001", "اداره حراست", "1405/07/15", "تحویل منزل نمونه", now),
            )
            report["hr_house_delivery"] = 1
        if force or _ent_empty("hr_doc_archive"):
            conn.execute(
                """INSERT INTO hr_doc_archive (page_description, keyword, file_name, file_type, notes, created_at)
                VALUES (?,?,?,?,?,?)""",
                ("پروپوزال رادیوگرافی", "زمانی", "MyScan.jpg", "jpg", "بایگانی نمونه", now),
            )
            report["hr_doc_archive"] = 1
        if force or _ent_empty("hr_foreign_nationals"):
            conn.execute(
                """INSERT INTO hr_foreign_nationals
                (first_name, last_name, father_name, nationality, passport_number, gender, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                ("John", "Smith", "Robert", "آمریکایی", "P1234567", "مرد", "اتباع خارجی نمونه", now),
            )
            report["hr_foreign_nationals"] = 1
        if force or _ent_empty("hr_countries"):
            for name, city in (("افغانستان", "کابل"), ("ترکیه", "آنکارا"), ("ایران", "تهران")):
                conn.execute("INSERT INTO hr_countries (country_name, residence_city, notes, created_at) VALUES (?,?,?,?)", (name, city, "کشور نمونه", now))
            report["hr_countries"] = 3
        if force or _ent_empty("hr_violations_personnel"):
            conn.execute(
                """INSERT INTO hr_violations_personnel
                (person_type, unit_name, person_name, violation_code, violation_subject, register_date, fine_amount, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                ("پرسنل شرکتی", "پیام گستر", "امیر رضایی", "۶۷", "دزدی", "1405/07/15", "10000", "تخلف پرسنل نمونه", now),
            )
            report["hr_violations_personnel"] = 1
        if force or _ent_empty("hr_violations_vehicle"):
            conn.execute(
                """INSERT INTO hr_violations_vehicle
                (plate_number, vehicle_type, driver_name, unit_name, violation_code, violation_subject, register_date, fine_amount, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                ("۱۲ ب ۳۴۵ - ۱۱", "سواری", "امیر رضایی", "پیام گستر", "۳۹", "پارک ممنوع", "1405/07/15", "50000", "تخلف خودرویی نمونه", now),
            )
            report["hr_violations_vehicle"] = 1
        if force or _ent_empty("hr_incidents"):
            conn.execute(
                """INSERT INTO hr_incidents
                (incident_datetime, incident_location, expert1_name, expert1_unit, expert1_opinion, commission_result, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                ("1405/07/15 10:00", "محوطه شمالی", "کارشناس ۱", "حراست", "بررسی شد", "تأیید", "صورتجلسه نمونه", now),
            )
            report["hr_incidents"] = 1
        if force or _ent_empty("hr_drug_tests"):
            conn.execute(
                """INSERT INTO hr_drug_tests
                (person_type, unit_name, person_name, father_name, national_id, notes, created_at)
                VALUES (?,?,?,?,?,?,?)""",
                ("پرسنل شرکتی", "پیام گستر", "امیر رضایی", "علی", "0012345678", "آزمایش مواد مخدر نمونه", now),
            )
            report["hr_drug_tests"] = 1
        if force or _ent_empty("hr_rewards"):
            conn.execute(
                """INSERT INTO hr_rewards
                (person_type, unit_name, person_name, reward_code, reward_subject, register_date, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                ("پرسنل شرکتی", "پیام گستر", "امیر رضایی", "R-01", "تشویق عملکرد", "1405/07/15", "تقدیر نمونه", now),
            )
            report["hr_rewards"] = 1
        if force or _ent_empty("hr_travel_abroad"):
            conn.execute(
                """INSERT INTO hr_travel_abroad
                (first_name, last_name, national_id, destination_country, travel_from, travel_to, purpose, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                ("امیر", "رضایی", "0012345678", "ترکیه", "1405/08/01", "1405/08/15", "ماموریت", "اعزام خارج نمونه", now),
            )
            report["hr_travel_abroad"] = 1
        if force or _ent_empty("hr_travel_personal"):
            conn.execute(
                """INSERT INTO hr_travel_personal
                (first_name, last_name, national_id, destination_country, travel_from, travel_to, purpose, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                ("امیر", "رضایی", "0012345678", "امارات", "1405/09/01", "1405/09/10", "شخصی", "سفر شخصی نمونه", now),
            )
            report["hr_travel_personal"] = 1
        if force or _ent_empty("hr_exit_admin"):
            conn.execute(
                """INSERT INTO hr_exit_admin
                (requester_name, unit_name, document_type, request_date, description, status, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                ("امیر رضایی", "حراست", "مدارک اداری", "1405/07/15", "درخواست خروج دیپ", "در انتظار", "خروج اداری نمونه", now),
            )
            report["hr_exit_admin"] = 1
        if force or _ent_empty("hr_exit_scientific"):
            conn.execute(
                """INSERT INTO hr_exit_scientific
                (requester_name, unit_name, document_type, request_date, description, status, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                ("امیر رضایی", "حراست", "گزارش علمی", "1405/07/15", "درخواست خروج علمی", "در انتظار", "خروج علمی نمونه", now),
            )
            report["hr_exit_scientific"] = 1


        # —— مناقصات و مزایدات (نمونه تست) ——
        if force or _ent_empty("tnd_companies"):
            conn.execute(
                """INSERT INTO tnd_companies
                (company_name, registration_place, registration_number, registration_date,
                 activity_type, rank_level, address, postal_code, email, phone, fax, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("سایب", "سیاس", "۳۶۶", "۱۳۹۶/۰۵/۰۱", "پیمانکاری", "۴", "تهران", "۷۶۵۴",
                 "a@a.ir", "۴۶۵۶۶", "۵۴۵۶", "شرکت حاضر نمونه", now),
            )
            report["tnd_companies"] = 1
        if force or _ent_empty("tnd_tenders"):
            conn.execute(
                """INSERT INTO tnd_tenders
                (main_company, subsidiary_company, main_organization, tender_subject,
                 tender_type, packet_open_date, agreement_amount, description, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                ("پالایش", "پایت", "پالپ", "پالپ", "مناقصه از نظر فراخوان بررسی",
                 "۱۳۹۶/۰۵/۱۳", "۳۵۶", "مناقصه نمونه", "مناقصه نمونه", now),
            )
            report["tnd_tenders"] = 1
        if force or _ent_empty("tnd_auctions"):
            conn.execute(
                """INSERT INTO tnd_auctions
                (main_company, subsidiary_company, main_organization, auction_subject,
                 auction_type, packet_open_date, agreement_amount, description, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                ("رادر", "پارا", "پالپ", "پالپا", "مزایده از نظر فراخوان بررسی",
                 "۱۳۹۶/۰۶/۱۱", "۶۶۶۶۶۶", "مزایده نمونه", "مزایده نمونه", now),
            )
            report["tnd_auctions"] = 1
        if force or _ent_empty("tnd_contracts"):
            conn.execute(
                """INSERT INTO tnd_contracts
                (main_company, subsidiary_company, contractor_name, contract_number,
                 contract_subject, execution_place, contract_date, contract_amount, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                ("پالایش", "پایت", "مهندسی جنوب خیم", "۲", "تغییرات اساسی", "پالپ",
                 "1405/07/15", "1000000", "قرارداد نمونه", now),
            )
            report["tnd_contracts"] = 1


        # —— کارتابل (نمونه تست) ——
        if force or _ent_empty("krt_outgoing"):
            conn.execute(
                """INSERT INTO krt_outgoing
                (letter_number, subject, letter_date, secretary_number, letter_body, recipients, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                ("1405/100", "درخواست گزارش ماهانه", "1405/07/15", "س-200", "متن نامه نمونه صادره", "پیام گستر", "نامه صادره نمونه", now),
            )
            report["krt_outgoing"] = 1
        if force or _ent_empty("krt_inbox"):
            conn.execute(
                """INSERT INTO krt_inbox
                (letter_number, subject, letter_date, sender_name, status, folder_name, letter_body, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                ("1405/50", "ابلاغ بخشنامه", "1405/07/14", "وزارت ارتباطات", "مشاهده نشده", "عمومی", "متن نامه وارده نمونه", "نامه وارده نمونه", now),
            )
            report["krt_inbox"] = 1
        if force or _ent_empty("krt_management"):
            conn.execute(
                """INSERT INTO krt_management
                (sender_name, subject, status, send_date, hour_sent, folder_name, letter_body, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                ("جواد رجبی", "درخواست بررسی", "مشاهده نشده", "1405/07/15", "۱۰:۳۰", "کارتابل", "متن مدیریت کارتابل", "مدیریت کارتابل نمونه", now),
            )
            report["krt_management"] = 1
        if force or _ent_empty("krt_folders"):
            for name in ("عمومی", "محرمانه", "بایگانی ۱۴۰۵"):
                conn.execute(
                    "INSERT INTO krt_folders (folder_name, notes, created_at) VALUES (?,?,?)",
                    (name, "پوشه بایگانی نمونه", now),
                )
            report["krt_folders"] = 3


        # —— باسکول (نمونه تست) ——
        if force or _ent_empty("bsk_weighings"):
            conn.execute(
                """INSERT INTO bsk_weighings
                (ticket_number, queue_number, plate_number, driver_name, vehicle_type, origin_company,
                 first_weight, first_date, first_time, first_status, net_weight, weigh_type, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("T-1001", "12", "۱۲ ب ۳۴۵ - ۱۱", "امیر رضایی", "باری", "شرکت مبدأ",
                 "8000", "1405/07/15", "۱۰:۱۵", "خالی", "5000", "بار ورودی", "توزین نمونه", now),
            )
            report["bsk_weighings"] = 1
        if force or _ent_empty("bsk_turns"):
            conn.execute(
                """INSERT INTO bsk_turns
                (turn_number, plate_number, vehicle_type, driver_name, origin_company, notes, created_at)
                VALUES (?,?,?,?,?,?,?)""",
                ("N-50", "۱۲ ب ۳۴۵ - ۱۱", "باری", "امیر رضایی", "شرکت مبدأ", "نوبت نمونه", now),
            )
            report["bsk_turns"] = 1
        if force or _ent_empty("bsk_traffic_ban"):
            conn.execute(
                """INSERT INTO bsk_traffic_ban
                (plate_number, national_id, person_name, issuer_order, description, notes, created_at)
                VALUES (?,?,?,?,?,?,?)""",
                ("۱۲ ب ۳۴۵ - ۱۱", "0012345678", "فرد نمونه", "دستور حراست", "ممنوعیت تردد نمونه", "ممنوعیت نمونه", now),
            )
            report["bsk_traffic_ban"] = 1
        if force or _ent_empty("bsk_companies"):
            conn.execute(
                """INSERT INTO bsk_companies
                (company_code, company_name, is_approved, is_origin, phone, notes, created_at)
                VALUES (?,?,?,?,?,?,?)""",
                ("7", "شرکت ۱", 1, 1, "02112345678", "شرکت باسکول نمونه", now),
            )
            report["bsk_companies"] = 1
        if force or _ent_empty("bsk_max_tonnage"):
            conn.execute(
                """INSERT INTO bsk_max_tonnage
                (company_name, cargo_name, destination_unit, amount, warning_amount, notes, created_at)
                VALUES (?,?,?,?,?,?,?)""",
                ("شرکت پیمانکار", "ماسه", "واحد مقصد", "100", "90", "حداکثر تناژ نمونه", now),
            )
            report["bsk_max_tonnage"] = 1
        if force or _ent_empty("bsk_settings"):
            conn.execute(
                """INSERT INTO bsk_settings
                (scale_name, scale_code, center_name, port_name, baud_rate, is_active, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                ("باسکول اصلی", "BSK-01", "شرکت پیام گستر", "COM1", "9600", 1, "تنظیمات نمونه", now),
            )
            report["bsk_settings"] = 1
        if force or _ent_empty("bsk_weigh_reports"):
            conn.execute(
                """INSERT INTO bsk_weigh_reports
                (ticket_number, plate_number, vehicle_type, driver_name, first_weight, second_weight, net_weight, weigh_date, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                ("T-1001", "۱۲ ب ۳۴۵ - ۱۱", "باری", "امیر رضایی", "8000", "13000", "5000", "1405/07/15", "گزارش توزین نمونه", now),
            )
            report["bsk_weigh_reports"] = 1


        # —— پلاک‌خوان (نمونه تست) ——
        if force or _ent_empty("plk_process"):
            conn.execute(
                """INSERT INTO plk_process
                (plate_number, camera_name, process_date, process_time, direction, confidence, status, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                ("۱۲ ب ۳۴۵ - ۱۱", "دوربین ورودی", "1405/07/15", "۱۰:۲۰", "ورود", "۹۸٪", "ثبت شده", "پردازش نمونه", now),
            )
            report["plk_process"] = 1
        if force or _ent_empty("plk_traffic"):
            conn.execute(
                """INSERT INTO plk_traffic
                (plate_number, camera_name, entry_date, entry_time, vehicle_type, gate_name, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                ("۱۲ ب ۳۴۵ - ۱۱", "دوربین ورودی", "1405/07/15", "۱۰:۲۰", "سواری", "درب اصلی", "تردد نمونه", now),
            )
            report["plk_traffic"] = 1
        if force or _ent_empty("plk_monitoring"):
            conn.execute(
                """INSERT INTO plk_monitoring
                (camera_name, location_name, status, last_read_plate, last_read_time, notes, created_at)
                VALUES (?,?,?,?,?,?,?)""",
                ("دوربین ورودی", "درب اصلی", "فعال", "۱۲ ب ۳۴۵ - ۱۱", "۱۰:۲۰", "مانیتورینگ نمونه", now),
            )
            report["plk_monitoring"] = 1
        if force or _ent_empty("plk_traffic_report"):
            conn.execute(
                """INSERT INTO plk_traffic_report
                (plate_number, report_date, traffic_count, gate_name, notes, created_at)
                VALUES (?,?,?,?,?,?)""",
                ("۱۲ ب ۳۴۵ - ۱۱", "1405/07/15", "3", "درب اصلی", "گزارش تردد نمونه", now),
            )
            report["plk_traffic_report"] = 1
        if force or _ent_empty("plk_full_traffic_report"):
            conn.execute(
                """INSERT INTO plk_full_traffic_report
                (plate_number, from_date, to_date, total_entries, total_exits, notes, created_at)
                VALUES (?,?,?,?,?,?,?)""",
                ("۱۲ ب ۳۴۵ - ۱۱", "1405/07/01", "1405/07/15", "12", "11", "گزارش کامل نمونه", now),
            )
            report["plk_full_traffic_report"] = 1
        if force or _ent_empty("plk_access_level_report"):
            conn.execute(
                """INSERT INTO plk_access_level_report
                (plate_number, access_level, vehicle_owner, unit_name, notes, created_at)
                VALUES (?,?,?,?,?,?)""",
                ("۱۲ ب ۳۴۵ - ۱۱", "مجاز", "امیر رضایی", "حراست", "سطح دسترسی نمونه", now),
            )
            report["plk_access_level_report"] = 1
        if force or _ent_empty("plk_inside_vehicles"):
            conn.execute(
                """INSERT INTO plk_inside_vehicles
                (plate_number, entry_time, camera_name, duration, status, notes, created_at)
                VALUES (?,?,?,?,?,?,?)""",
                ("۱۲ ب ۳۴۵ - ۱۱", "۱۰:۲۰", "دوربین ورودی", "۲ ساعت", "داخل سازمان", "خودروی داخل نمونه", now),
            )
            report["plk_inside_vehicles"] = 1
        if force or _ent_empty("plk_parking"):
            conn.execute(
                """INSERT INTO plk_parking
                (plate_number, parking_zone, slot_number, entry_date, entry_time, status, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                ("۱۲ ب ۳۴۵ - ۱۱", "منطقه A", "A-12", "1405/07/15", "۱۰:۳۰", "پارک شده", "پارکینگ نمونه", now),
            )
            report["plk_parking"] = 1
        if force or _ent_empty("plk_cameras"):
            conn.execute(
                """INSERT INTO plk_cameras
                (camera_name, camera_code, location_name, ip_address, direction, is_active, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                ("دوربین ورودی", "CAM-01", "درب اصلی", "192.168.1.100", "ورود", 1, "دوربین نمونه", now),
            )
            report["plk_cameras"] = 1
        if force or _ent_empty("plk_online_monitor"):
            conn.execute(
                """INSERT INTO plk_online_monitor
                (camera_name, live_plate, event_time, event_type, notes, created_at)
                VALUES (?,?,?,?,?,?)""",
                ("دوربین ورودی", "۱۲ ب ۳۴۵ - ۱۱", "۱۰:۲۰", "تشخیص", "مانیتورینگ آنلاین نمونه", now),
            )
            report["plk_online_monitor"] = 1


        # —— کنترل دسترسی (نمونه تست) ——
        if force or _ent_empty("ac_traffic"):
            conn.execute(
                """INSERT INTO ac_traffic
                (person_type, plate_number, personnel_code, card_code, first_name, last_name, company_unit, door_name, traffic_date, traffic_time, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("پرسنل", "۱۲ ب ۳۴۵ - ۱۱", "1001", "C-200", "علی", "محمدی", "حراست", "درب اصلی", "1405/07/15", "۰۸:۳۰", "تردد نمونه", now),
            )
            report["ac_traffic"] = 1
        if force or _ent_empty("ac_access_def"):
            conn.execute(
                """INSERT INTO ac_access_def (def_type, code, name, time_from, time_to, notes, created_at) VALUES (?,?,?,?,?,?,?)""",
                ("محدوده زمانی", "1000", "محدوده زمانی ۱", "۰۷:۰۰", "۱۹:۰۰", "تعریف دسترسی نمونه", now),
            )
            report["ac_access_def"] = 1
        if force or _ent_empty("ac_guests"):
            conn.execute(
                """INSERT INTO ac_guests (first_name, last_name, national_id, host_name, visit_date, access_group, notes, created_at) VALUES (?,?,?,?,?,?,?,?)""",
                ("رضا", "کریمی", "0012345678", "علی محمدی", "1405/07/15", "مهمان", "مهمان نمونه", now),
            )
            report["ac_guests"] = 1
        if force or _ent_empty("ac_guest_cards"):
            conn.execute(
                """INSERT INTO ac_guest_cards (card_type, card_code, card_number, from_date, to_date, access_group, notes, created_at) VALUES (?,?,?,?,?,?,?,?)""",
                ("مهمان", "تقی", "1231231", "1405/07/15", "1405/07/16", "مهمان", "کارت مهمان نمونه", now),
            )
            report["ac_guest_cards"] = 1
        if force or _ent_empty("ac_guest_traffic_zone"):
            conn.execute(
                """INSERT INTO ac_guest_traffic_zone (zone_name, door_name, notes, created_at) VALUES (?,?,?,?)""",
                ("سلسله‌مراتب", "درب اصلی", "محدوده تردد مهمان نمونه", now),
            )
            report["ac_guest_traffic_zone"] = 1
        if force or _ent_empty("ac_guest_delivered_cards"):
            conn.execute(
                """INSERT INTO ac_guest_delivered_cards (card_number, guest_name, deliver_date, status, notes, created_at) VALUES (?,?,?,?,?,?)""",
                ("1231231", "رضا کریمی", "1405/07/15", "تحویل شده", "کارت تحویل‌شده نمونه", now),
            )
            report["ac_guest_delivered_cards"] = 1
        if force or _ent_empty("ac_guest_traffic_report"):
            conn.execute(
                """INSERT INTO ac_guest_traffic_report (guest_name, last_name, card_number, traffic_date, entry_time, terminal_name, notes, created_at) VALUES (?,?,?,?,?,?,?,?)""",
                ("رضا", "کریمی", "1231231", "1405/07/15", "۰۹:۰۰", "ترمینال ورودی", "گزارش تردد مهمان نمونه", now),
            )
            report["ac_guest_traffic_report"] = 1
        if force or _ent_empty("ac_assign"):
            conn.execute(
                """INSERT INTO ac_assign (person_type, person_code, first_name, last_name, national_id, access_group, issue_date, notes, created_at) VALUES (?,?,?,?,?,?,?,?,?)""",
                ("پیمانکار", "9", "نام پیمانکار", "خانوادگی پیمانکار تست", "0019751036", "مجموعه دسترسی ۱", "1405/07/15", "تخصیص نمونه", now),
            )
            report["ac_assign"] = 1
        if force or _ent_empty("ac_terminals"):
            conn.execute(
                """INSERT INTO ac_terminals (device_name, ip_address, mac_address, serial_number, group_name, is_active, notes, created_at) VALUES (?,?,?,?,?,?,?,?)""",
                ("ترمینال ورودی", "192.168.1.50", "AA:BB:CC:DD:EE:FF", "SN-001", "گروه اصلی", 1, "ترمینال نمونه", now),
            )
            report["ac_terminals"] = 1
        if force or _ent_empty("ac_terminal_status"):
            conn.execute(
                """INSERT INTO ac_terminal_status (device_name, status, last_sync, notes, created_at) VALUES (?,?,?,?,?)""",
                ("ترمینال ورودی", "آنلاین", "1405/07/15 ۱۰:۰۰", "وضعیت ترمینال نمونه", now),
            )
            report["ac_terminal_status"] = 1
        if force or _ent_empty("ac_user_sync"):
            conn.execute(
                """INSERT INTO ac_user_sync (user_code, user_name, last_name, access_level, person_type, sync_status, notes, created_at) VALUES (?,?,?,?,?,?,?,?)""",
                ("U-10", "علی", "محمدی", "کامل", "پرسنل", "همسان‌سازی شده", "همسان‌سازی نمونه", now),
            )
            report["ac_user_sync"] = 1
        if force or _ent_empty("ac_general_report"):
            conn.execute(
                """INSERT INTO ac_general_report (report_title, report_date, person_name, event_type, door_name, notes, created_at) VALUES (?,?,?,?,?,?,?)""",
                ("گزارش روزانه", "1405/07/15", "علی محمدی", "ورود", "درب اصلی", "گزارش کلی نمونه", now),
            )
            report["ac_general_report"] = 1


        # —— جریان کار (نمونه تست) ——
        if force or _ent_empty("wf_request_types"):
            samples = [
                ("تاییدات فرم رزرو تردد کارکنان روزمزد و نیروهای جایگزین", "1"),
                ("تایید گزارش نگهبانی", "2"),
                ("تایید رزرو خودرو", "3"),
            ]
            for rt, cnt in samples:
                conn.execute(
                    "INSERT INTO wf_request_types (request_type, approver_count, notes, created_at) VALUES (?,?,?,?)",
                    (rt, cnt, "نوع درخواست نمونه", now),
                )
            report["wf_request_types"] = len(samples)
        if force or _ent_empty("wf_approvers"):
            conn.execute(
                """INSERT INTO wf_approvers (request_type, approver_name, approver_username, user_order, notes, created_at)
                VALUES (?,?,?,?,?,?)""",
                ("درخواست رزرو مهمان", "پیام گستر", "PayamgostarFava", "1", "تاییدکننده نمونه", now),
            )
            report["wf_approvers"] = 1
        if force or _ent_empty("wf_delegation"):
            conn.execute(
                """INSERT INTO wf_delegation
                (request_type, from_user, from_username, to_user, date_from, date_to, description, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                ("درخواست رزرو مهمان", "پیام گستر", "PayamgostarFava", "Admin", "1405/07/01", "1405/07/30", "تفویض موقت", "تفویض نمونه", now),
            )
            report["wf_delegation"] = 1
        if force or _ent_empty("wf_parking_docs"):
            conn.execute(
                """INSERT INTO wf_parking_docs
                (request_type, company_name, personnel_name, approval_stage, notes, created_at)
                VALUES (?,?,?,?,?,?)""",
                ("فرم خروج مدارک اداری", "نفت سپاهان", "پرسنل نمونه", "مرحله اول", "تایید پارکینگ/مدارک نمونه", now),
            )
            report["wf_parking_docs"] = 1

        # —— داده نمونه گزارش‌ها ——
        if force or _ent_empty("guest_visits"):
            conn.execute(
                "INSERT INTO guest_visits (guest_name, host_name, visit_date, entry_time, exit_time, purpose, center_name, created_at) VALUES (?,?,?,?,?,?,?,?)",
                ("مهمان نمونه", "امیر رضایی", "1405/07/15", "۰۹:۳۰", "۱۲:۰۰", "جلسه اداری", "شرکت پیام گستر", now),
            )
            report["guest_visits"] = 1
        if force or _ent_empty("personnel_traffic"):
            for row in (
                ("امیر رضایی", "پرسنل", "ورود", "1405/07/15", "۰۷:۴۵", "درب اصلی", "شرکت پیام گستر"),
                ("علی پیمانکار", "پیمانکار", "ورود", "1405/07/15", "۰۸:۱۰", "درب خودرویی", "شرکت پیام گستر"),
            ):
                conn.execute(
                    "INSERT INTO personnel_traffic (person_name, person_type, direction, traffic_date, traffic_time, door_name, center_name, created_at) VALUES (?,?,?,?,?,?,?,?)",
                    (*row, now),
                )
            report["personnel_traffic"] = 2
        if force or _ent_empty("vehicle_traffic"):
            conn.execute(
                "INSERT INTO vehicle_traffic (plate_number, driver_name, person_type, direction, traffic_date, center_name, created_at) VALUES (?,?,?,?,?,?,?)",
                ("۱۲ ب ۳۴۵ - ۱۱", "امیر رضایی", "پرسنل", "ورود", "1405/07/15", "شرکت پیام گستر", now),
            )
            report["vehicle_traffic"] = 1
        if force or _ent_empty("goods_traffic"):
            for row in (
                ("پرینتر", "امانی", "ورود", "1405/07/14", "شرکت پیام گستر", 0, 0),
                ("قطعه تعمیری", "تعمیری", "ورود", "1405/07/13", "پیمانکار الف", 1, 1),
                ("کالای پیمانکار", "خروجی", "خروج", "1405/07/12", "پیمانکار ب", 1, 0),
            ):
                conn.execute(
                    "INSERT INTO goods_traffic (goods_name, traffic_type, direction, traffic_date, company_name, is_contractor, is_repair, center_name, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                    (row[0], row[1], row[2], row[3], row[4], row[5], row[6], "شرکت پیام گستر", now),
                )
            report["goods_traffic"] = 3
        if force or _ent_empty("misc_person_traffic"):
            conn.execute(
                "INSERT INTO misc_person_traffic (person_name, direction, traffic_date, reason, center_name, created_at) VALUES (?,?,?,?,?,?)",
                ("فرد متفرقه", "ورود", "1405/07/15", "تحویل مرسوله", "شرکت پیام گستر", now),
            )
            report["misc_person_traffic"] = 1
        if force or _ent_empty("traffic_requests"):
            conn.execute(
                "INSERT INTO traffic_requests (requester_name, request_date, request_type, status, description, created_at) VALUES (?,?,?,?,?,?)",
                ("حسین احمدی", "1405/07/10", "تردد خودرو", "تأیید", "درخواست تردد صبح", now),
            )
            report["traffic_requests"] = 1
        if force or _ent_empty("guest_reservations"):
            conn.execute(
                "INSERT INTO guest_reservations (guest_name, reserve_date, host_name, status, center_name, created_at) VALUES (?,?,?,?,?,?)",
                ("مهمان رزرو", "1405/07/20", "امیر رضایی", "رزرو", "شرکت پیام گستر", now),
            )
            report["guest_reservations"] = 1
        if force or _ent_empty("goods_reservations"):
            conn.execute(
                "INSERT INTO goods_reservations (goods_name, reserve_date, requester, status, created_at) VALUES (?,?,?,?,?)",
                ("اسکنر", "1405/07/18", "انبار مرکزی", "رزرو", now),
            )
            report["goods_reservations"] = 1
        if force or _ent_empty("system_logs"):
            for row in (
                ("1405/07/15", "۰۸:۰۰", "admin", "ورود به سیستم", "ورود موفق"),
                ("1405/07/15", "۰۹:۱۲", "admin", "ثبت پرسنل", "ایجاد رکورد نمونه"),
            ):
                conn.execute(
                    "INSERT INTO system_logs (log_date, log_time, user_name, action, details, created_at) VALUES (?,?,?,?,?,?)",
                    (*row, now),
                )
            report["system_logs"] = 2



        # —— خودروها (اطلاعات پایه) ——
        if force or _ent_empty("vehicle_types"):
            for name in ("سواری", "وانت", "اتوبوس", "کامیون", "L90", "PK", "آمبوالانس", "بدون خودرو"):
                conn.execute(
                    "INSERT OR IGNORE INTO vehicle_types (name, created_at) VALUES (?,?)",
                    (name, now),
                )
            report["vehicle_types"] = 8
        if force or _ent_empty("vehicles"):
            conn.execute(
                """INSERT INTO vehicles
                (plate_number, plate_special, vehicle_type, color, ownership, category,
                 chassis_number, center_name, unit_name, personnel_name, driver_name,
                 company_name, description, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("۱۲ ب ۳۴۵ - ۱۱", "", "سواری", "سفید", "ملکی", "خودرو",
                 "CHS-1001", "شرکت پیام گستر", "حراست ستاد", "امیر رضایی", "امیر رضایی",
                 "تأسیسات دریایی ایران (ستاد)", "خودرو نمونه تست", now, now),
            )
            report["vehicles"] = 1
        if force or _ent_empty("cargo_vehicles"):
            conn.execute(
                """INSERT INTO cargo_vehicles
                (plate_number, plate_special, vehicle_type, chassis_number, driver_name,
                 driver_phone, company_name, vehicle_weight, max_weight, description, is_blocked,
                 created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("۹۸ ص ۶۵۴ - ۱۶", "", "تریلی", "CG-200", "موسوی",
                 "09120000000", "شرکت باربری نمونه", "20", "25", "نمونه خودرو باری", 0,
                 now, now),
            )
            report["cargo_vehicles"] = 1
        if force or _ent_empty("cargo_traffic_reasons"):
            for reason, ttype in (
                ("حمل کالا", "ورود"),
                ("تخلیه بار", "خروج"),
                ("علت تردد خودروهای باری", "ورود"),
                ("علت تردد خودروهای باری", "خروج"),
            ):
                conn.execute(
                    "INSERT INTO cargo_traffic_reasons (reason, traffic_type, created_at) VALUES (?,?,?)",
                    (reason, ttype, now),
                )
            report["cargo_traffic_reasons"] = 4

        # —— کالاها ——
        if force or _ent_empty("goods_entry_exit_types"):
            for name in ("امانی", "خدمات", "تعمیری", "تعویضی", "خروجی"):
                conn.execute(
                    "INSERT OR IGNORE INTO goods_entry_exit_types (name, created_at) VALUES (?,?)",
                    (name, now),
                )
            report["goods_entry_exit_types"] = 5
        if force or _ent_empty("goods_products"):
            conn.execute(
                """INSERT INTO goods_products
                (center_name, barcode, name, goods_type, count_unit, serial_number,
                 product_specs, is_active, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                ("شرکت پیام گستر", "1", "پرینتر", "الکترونیکی", "دستگاه", "111",
                 "مشخصات محصول؛ پرینتر", 1, now, now),
            )
            conn.execute(
                """INSERT INTO goods_products
                (center_name, barcode, name, goods_type, count_unit, serial_number,
                 product_specs, is_active, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                ("شرکت پیام گستر", "2", "اسکنر", "الکترونیکی", "دستگاه", "222",
                 "مشخصات محصول؛ اسکنر", 1, now, now),
            )
            report["goods_products"] = 2

    return report


LOOKUP_TABLES = {
    "education_fields": "رشته تحصیلی",
    "responsibility_groups": "گروه مسئولیت",
    "employment_types": "انواع استخدام",
    "services": "مسیر سرویس",
    "door_access_levels": "سطح دسترسی درب (ساده)",
}

# جداول ساختاریافته اطلاعات پایه (فرم کامل دژبان)
BASEINFO_ENTITY_TABLES = {
    "access_doors": "درب‌های تردد",
    "goods_destinations": "مقصد کالا",
    "client_companies": "شرکت/مشتری",
    "card_issue_companies": "نام شرکت صدور کارت",
    "entry_exit_types": "نوع ورود و خروج",
    "door_user_access": "دسترسی کاربر به درب",
    "vehicle_types": "نوع خودروها",
    "vehicles": "تعریف خودروها",
    "cargo_vehicles": "خودروهای باری",
    "cargo_traffic_reasons": "علت تردد خودروهای باری",
    "goods_entry_exit_types": "انواع ورود و خروج کالا",
    "goods_products": "کالا و محصولات",
}

# جداول انتظامات (تعاریف نگهبانی/شیفت)
ENTEZAMAT_ENTITY_TABLES = {
    "ent_groups": "تعریف گروه",
    "ent_protection_centers": "مراکز حفاظتی و نگهبانی",
    "ent_protection_places": "اماکن حفاظتی و نگهبانی",
    "ent_shift_hours": "ساعت‌های شیفت",
    "ent_shift_leaders": "مسئول و جانشین شیفت",
    "ent_work_shifts": "نوبت کار",
    "ent_staff_status": "وضعیت پرسنل انتظامات",
    "ent_guard_equipment": "تجهیزات نگهبانی",
    "ent_guard_board": "لوح نگهبانی",
    "ent_shift_events": "ثبت وقایع شیفت",
    "ent_shift_schedule": "برنامه نوبتکاری",
    "ent_personnel_electronics": "تجهیزات الکترونیک پرسنل",
    "ent_replacement_requests": "درخواست جایگزینی",
    "ent_permits": "صدور مجوز",
    "ent_monitoring_events": "وقایع شیفت اتاق مانیتورینگ",
    "ent_monitoring_staff": "مسئولین اتاق مانیتورینگ",
    "ent_guard_reports": "گزارش نگهبانی",
    "ent_guard_referrals": "گزارش ارجاع نگهبانی",
    "ent_roll_call": "رول‌کال / رونوشت",
    "ent_news_reports": "گزارش خبر",
    "ent_guard_board_summary": "لوح نگهبانی اجمالی",
    "ent_guard_events": "ثبت وقایع نگهبانی",
    "ent_deployment_locations": "شناسه محل استقرار",
    "ent_officer_events": "ثبت وقایع افسر نگهبانی",
}

# جداول صدور کارت (چاپ و گزارش)
CARD_ENTITY_TABLES = {
    "card_personnel": "چاپ کارت پرسنل",
    "card_contractor": "چاپ کارت پیمانکاران",
    "card_vehicle_personnel": "چاپ کارت خودروی پرسنل",
    "card_vehicle_contractor": "چاپ کارت خودروی پیمانکاران",
}

# جداول پیمانکاران
CONTRACTOR_ENTITY_TABLES = {
    "ctr_companies": "شرکت‌های پیمانکار",
    "ctr_contracts": "قرارداد شرکت‌های پیمانکار",
    "ctr_personnel": "پرسنل شرکت‌های پیمانکار",
    "ctr_vehicles": "ثبت خودروهای پیمانکاران",
    "ctr_drivers": "ثبت راننده‌های پیمانکاران",
}

# جداول گشت و پایش
PATROL_ENTITY_TABLES = {
    "patrol_devices": "لیست دستگاه‌ها",
    "patrol_events": "لیست رخدادها",
    "patrol_checkpoints": "لیست نقاط بازدید",
    "patrol_guards": "لیست نگهبانان",
    "patrol_routes": "مسیرها و ساعات شروع",
    "patrol_route_config": "پیکربندی مسیر",
    "patrol_shift_times": "تعیین ساعت شروع و پایان",
}


# جداول حراست
HERASAT_ENTITY_TABLES = {
    "hr_eval_options": "گزینه‌های ارزشیابی",
    "hr_eval_titles": "عناوین ارزشیابی",
    "hr_eval_periods": "تعریف دوره ارزشیابی",
    "hr_eval_monthly": "ارزشیابی ماهانه پرسنل",
    "hr_areas": "تعریف نواحی",
    "hr_houses": "تعریف منازل",
    "hr_house_delivery": "تحویل منازل و اماکن",
    "hr_doc_archive": "بایگانی مدارک",
    "hr_foreign_nationals": "مشخصات اتباع خارجی",
    "hr_countries": "مشخصات کشورها",
    "hr_violations_personnel": "ثبت تخلفات پرسنل و پیمانکاران",
    "hr_violations_vehicle": "ثبت تخلفات خودرویی",
    "hr_incidents": "صورتجلسه حوادث",
    "hr_drug_tests": "ثبت مصرف مواد مخدر",
    "hr_rewards": "تقدیر و تشویق سازمانی",
    "hr_travel_abroad": "پرسشنامه اعزام به خارج",
    "hr_travel_personal": "پرسشنامه سفرهای شخصی",
    "hr_exit_admin": "خروج دیپ و مدارک اداری",
    "hr_exit_scientific": "خروج دیپ و مدارک علمی",
}


# جداول مناقصات و مزایدات
TENDER_ENTITY_TABLES = {
    "tnd_companies": "شرکت‌های حاضر در مناقصه/مزایده",
    "tnd_tenders": "مناقصات",
    "tnd_auctions": "مزایده",
    "tnd_contracts": "قراردادها",
}


# جداول کارتابل
CARTABLE_ENTITY_TABLES = {
    "krt_outgoing": "نامه‌های صادره",
    "krt_inbox": "نامه‌های وارده",
    "krt_management": "مدیریت کارتابل",
    "krt_folders": "پوشه‌های بایگانی",
}


# جداول باسکول
BASKOOL_ENTITY_TABLES = {
    "bsk_weighings": "ثبت توزین",
    "bsk_turns": "سیستم ثبت نوبت",
    "bsk_traffic_ban": "ممنوعیت تردد",
    "bsk_companies": "تعریف شرکت‌ها",
    "bsk_max_tonnage": "حداکثر تناژ پیمانکاران",
    "bsk_settings": "تنظیمات باسکول",
    "bsk_weigh_reports": "گزارش توزین",
}


# جداول پلاک‌خوان
PLATE_READER_ENTITY_TABLES = {
    "plk_process": "فرم پردازش پلاک‌خوان",
    "plk_traffic": "تردد پلاک‌خوان",
    "plk_monitoring": "مانیتورینگ پلاک‌خوان",
    "plk_traffic_report": "گزارش تردد پلاک‌خوان",
    "plk_full_traffic_report": "گزارش تردد کامل پلاک‌خوان",
    "plk_access_level_report": "گزارش سطح دسترسی خودروها",
    "plk_inside_vehicles": "گزارش خودروهای داخل سازمان",
    "plk_parking": "فرم پارکینگ",
    "plk_cameras": "تعریف دوربین‌های پلاک‌خوان",
    "plk_online_monitor": "مانیتورینگ آنلاین پلاک‌خوان",
}


# جداول کنترل دسترسی
ACCESS_ENTITY_TABLES = {
    "ac_traffic": "فرم تردد RFID",
    "ac_access_def": "تعریف دسترسی",
    "ac_guests": "مهمان",
    "ac_guest_cards": "کارت مهمان‌ها",
    "ac_guest_traffic_zone": "محدوده تردد مهمان",
    "ac_guest_delivered_cards": "کارت‌های تحویل‌شده مهمان",
    "ac_guest_traffic_report": "گزارش تردد مهمانان",
    "ac_assign": "فرم تخصیص",
    "ac_terminals": "ترمینال‌ها",
    "ac_terminal_status": "وضعیت ترمینال‌ها",
    "ac_user_sync": "همسان‌سازی کاربران",
    "ac_general_report": "گزارشات کلی",
}


# جداول جریان کار
WORKFLOW_ENTITY_TABLES = {
    "wf_request_types": "انواع درخواست",
    "wf_approvers": "تاییدکننده درخواست",
    "wf_delegation": "تفویض اختیار",
    "wf_parking_docs": "تاییدات پارکینگ و خروج مدارک",
}

ALL_ENTITY_TABLES = {
    **BASEINFO_ENTITY_TABLES,
    **ENTEZAMAT_ENTITY_TABLES,
    **CARD_ENTITY_TABLES,
    **CONTRACTOR_ENTITY_TABLES,
    **PATROL_ENTITY_TABLES,
    **HERASAT_ENTITY_TABLES,
    **TENDER_ENTITY_TABLES,
    **CARTABLE_ENTITY_TABLES,
    **BASKOOL_ENTITY_TABLES,
    **PLATE_READER_ENTITY_TABLES,
    **ACCESS_ENTITY_TABLES,
    **WORKFLOW_ENTITY_TABLES,
}


def list_lookup(table: str) -> list:
    if table not in LOOKUP_TABLES:
        raise ValueError("جدول نامعتبر")
    return _list_named(table)


def create_lookup(table: str, name: str, description: str = "") -> dict:
    if table not in LOOKUP_TABLES:
        raise ValueError("جدول نامعتبر")
    name = (name or "").strip()
    if not name:
        raise ValueError("نام الزامی است")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_companies_db() as conn:
        _init_lookup_tables(conn)
        # اگر جدول description ندارد، فقط name
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        if "description" in cols:
            try:
                cur = conn.execute(
                    f"INSERT INTO {table} (name, description, created_at) VALUES (?, ?, ?)",
                    (name, description or "", now),
                )
            except Exception as e:
                if "UNIQUE" in str(e).upper():
                    raise ValueError("این نام قبلاً ثبت شده است")
                raise
        else:
            try:
                cur = conn.execute(
                    f"INSERT INTO {table} (name, created_at) VALUES (?, ?)",
                    (name, now),
                )
            except Exception as e:
                if "UNIQUE" in str(e).upper():
                    raise ValueError("این نام قبلاً ثبت شده است")
                raise
        row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (cur.lastrowid,)).fetchone()
        return row_to_dict(row)


def update_lookup(table: str, rid: int, name: str, description: str = None) -> dict | None:
    if table not in LOOKUP_TABLES:
        raise ValueError("جدول نامعتبر")
    name = (name or "").strip()
    if not name:
        raise ValueError("نام الزامی است")
    with get_companies_db() as conn:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        if "description" in cols and description is not None:
            conn.execute(
                f"UPDATE {table} SET name=?, description=? WHERE id=?",
                (name, description, rid),
            )
        else:
            conn.execute(f"UPDATE {table} SET name=? WHERE id=?", (name, rid))
        row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (rid,)).fetchone()
        return row_to_dict(row) if row else None


def delete_lookup(table: str, rid: int) -> bool:
    if table not in LOOKUP_TABLES:
        raise ValueError("جدول نامعتبر")
    return _delete_named(table, rid)



def _ensure_baseinfo_ready():
    with get_companies_db() as conn:
        _init_lookup_tables(conn)


def list_baseinfo_entity(table: str) -> list:
    if table not in ALL_ENTITY_TABLES:
        raise ValueError("جدول نامعتبر")
    _ensure_baseinfo_ready()
    with get_companies_db() as conn:
        rows = conn.execute(f"SELECT * FROM {table} ORDER BY id DESC").fetchall()
        return [row_to_dict(r) for r in rows]


def create_baseinfo_entity(table: str, data: dict) -> dict:
    if table not in ALL_ENTITY_TABLES:
        raise ValueError("جدول نامعتبر")
    _ensure_baseinfo_ready()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = dict(data or {})
    # فرمت پلاک ایران برای همه جداول دارای plate_number
    _PLATE_TABLES = (
        "vehicles", "cargo_vehicles",
        "card_vehicle_personnel", "card_vehicle_contractor",
        "ctr_vehicles", "hr_violations_vehicle", "bsk_weighings", "bsk_turns", "bsk_traffic_ban", "bsk_weigh_reports", "plk_process", "plk_traffic", "plk_traffic_report", "plk_full_traffic_report", "plk_access_level_report", "plk_inside_vehicles", "plk_parking", "plk_online_monitor", "ac_traffic",
    )
    if table in _PLATE_TABLES and data.get("plate_number"):
        data["plate_number"] = normalize_iran_plate(data["plate_number"])
    with get_companies_db() as conn:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        cols = [c for c in cols if c != "id"]
        insert_cols, values = [], []
        for c in cols:
            if c in ("created_at", "updated_at"):
                insert_cols.append(c)
                values.append(now)
            elif c in data:
                insert_cols.append(c)
                val = data[c]
                if c in ("is_active", "is_entry", "is_exit", "show_on_guard_board", "show_on_internet"):
                    val = 1 if val in (True, 1, "1", "true", "بلی", "فعال") else 0
                values.append(val if val is not None else "")
        if not insert_cols:
            raise ValueError("داده خالی است")
        placeholders = ", ".join(["?"] * len(insert_cols))
        cur = conn.execute(
            f"INSERT INTO {table} ({', '.join(insert_cols)}) VALUES ({placeholders})",
            values,
        )
        row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (cur.lastrowid,)).fetchone()
        return row_to_dict(row)


def update_baseinfo_entity(table: str, rid: int, data: dict) -> dict | None:
    if table not in ALL_ENTITY_TABLES:
        raise ValueError("جدول نامعتبر")
    _ensure_baseinfo_ready()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = dict(data or {})
    _PLATE_TABLES = (
        "vehicles", "cargo_vehicles",
        "card_vehicle_personnel", "card_vehicle_contractor",
        "ctr_vehicles", "hr_violations_vehicle", "bsk_weighings", "bsk_turns", "bsk_traffic_ban", "bsk_weigh_reports", "plk_process", "plk_traffic", "plk_traffic_report", "plk_full_traffic_report", "plk_access_level_report", "plk_inside_vehicles", "plk_parking", "plk_online_monitor", "ac_traffic",
    )
    if table in _PLATE_TABLES and data.get("plate_number"):
        data["plate_number"] = normalize_iran_plate(data["plate_number"])
    with get_companies_db() as conn:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        sets, values = [], []
        for c in cols:
            if c in ("id", "created_at"):
                continue
            if c == "updated_at":
                sets.append("updated_at=?")
                values.append(now)
            elif c in data:
                val = data[c]
                if c in ("is_active", "is_entry", "is_exit", "show_on_guard_board", "show_on_internet"):
                    val = 1 if val in (True, 1, "1", "true", "بلی", "فعال") else 0
                sets.append(f"{c}=?")
                values.append(val)
        if not sets:
            row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (rid,)).fetchone()
            return row_to_dict(row) if row else None
        values.append(rid)
        conn.execute(f"UPDATE {table} SET {', '.join(sets)} WHERE id=?", values)
        row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (rid,)).fetchone()
        return row_to_dict(row) if row else None


def delete_baseinfo_entity(table: str, rid: int) -> bool:
    if table not in ALL_ENTITY_TABLES:
        raise ValueError("جدول نامعتبر")
    with get_companies_db() as conn:
        cur = conn.execute(f"DELETE FROM {table} WHERE id=?", (rid,))
        return cur.rowcount > 0



_PERSONNEL_RECORD_TABLES = {
    "service": "personnel_service_history",
    "travel": "personnel_travel",
    "medical": "personnel_medical",
}

_PERSONNEL_RECORD_FIELDS = {
    "service": ["from_date", "to_date", "organization", "position", "unit_name", "description"],
    "travel": ["country", "from_date", "to_date", "purpose", "visa_no", "description"],
    "medical": ["record_date", "record_type", "diagnosis", "physician", "description"],
}


def list_personnel_records(company_code: int, kind: str, personnel_id: int = None) -> list:
    table = _PERSONNEL_RECORD_TABLES.get(kind)
    if not table:
        raise ValueError("نوع سابقه نامعتبر است")
    ensure_company_database(company_code)
    with get_company_db(company_code) as conn:
        _init_personnel_records_schema(conn)
        if personnel_id is not None:
            rows = conn.execute(
                f"SELECT * FROM {table} WHERE personnel_id=? ORDER BY id DESC",
                (personnel_id,),
            ).fetchall()
        else:
            rows = conn.execute(f"SELECT * FROM {table} ORDER BY id DESC").fetchall()
        return [row_to_dict(r) for r in rows]


def create_personnel_record(company_code: int, kind: str, data: dict) -> dict:
    table = _PERSONNEL_RECORD_TABLES.get(kind)
    fields = _PERSONNEL_RECORD_FIELDS.get(kind)
    if not table or not fields:
        raise ValueError("نوع سابقه نامعتبر است")
    ensure_company_database(company_code)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pid = int(data.get("personnel_id") or 0)
    if not pid:
        raise ValueError("personnel_id الزامی است")
    with get_company_db(company_code) as conn:
        _init_personnel_records_schema(conn)
        exists = conn.execute("SELECT id FROM personnel WHERE id=?", (pid,)).fetchone()
        if not exists:
            raise ValueError("پرسنل یافت نشد")
        cols = ["personnel_id"] + fields + ["created_at", "updated_at"]
        vals = [pid] + [str(data.get(f) or "") for f in fields] + [now, now]
        placeholders = ", ".join(["?"] * len(cols))
        cur = conn.execute(
            f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})",
            vals,
        )
        row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (cur.lastrowid,)).fetchone()
        return row_to_dict(row)


def update_personnel_record(company_code: int, kind: str, rid: int, data: dict) -> dict:
    table = _PERSONNEL_RECORD_TABLES.get(kind)
    fields = _PERSONNEL_RECORD_FIELDS.get(kind)
    if not table or not fields:
        raise ValueError("نوع سابقه نامعتبر است")
    ensure_company_database(company_code)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_company_db(company_code) as conn:
        _init_personnel_records_schema(conn)
        sets, vals = [], []
        for f in fields:
            if f in data:
                sets.append(f"{f}=?")
                vals.append(str(data.get(f) or ""))
        if not sets:
            row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (rid,)).fetchone()
            return row_to_dict(row) if row else None
        sets.append("updated_at=?")
        vals.append(now)
        vals.append(rid)
        conn.execute(f"UPDATE {table} SET {', '.join(sets)} WHERE id=?", vals)
        row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (rid,)).fetchone()
        return row_to_dict(row) if row else None


def delete_personnel_record(company_code: int, kind: str, rid: int) -> bool:
    table = _PERSONNEL_RECORD_TABLES.get(kind)
    if not table:
        raise ValueError("نوع سابقه نامعتبر است")
    ensure_company_database(company_code)
    with get_company_db(company_code) as conn:
        cur = conn.execute(f"DELETE FROM {table} WHERE id=?", (rid,))
        return cur.rowcount > 0



# ──────────────────────────────────────────────
# وابستگان پرسنل (در دیتابیس متمرکز)
# ──────────────────────────────────────────────

def list_dependents(company_code: int, personnel_id: int = None) -> list:
    ensure_company_database(company_code)
    with get_company_db(company_code) as conn:
        if personnel_id is not None:
            rows = conn.execute(
                "SELECT * FROM dependents WHERE personnel_id=? ORDER BY id DESC",
                (personnel_id,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM dependents ORDER BY id DESC").fetchall()
        return [row_to_dict(r) for r in rows]


def create_dependent(company_code: int, data: dict) -> dict:
    ensure_company_database(company_code)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pid = int(data.get("personnel_id") or 0)
    if not pid:
        raise ValueError("personnel_id الزامی است")
    with get_company_db(company_code) as conn:
        exists = conn.execute("SELECT id FROM personnel WHERE id=?", (pid,)).fetchone()
        if not exists:
            raise ValueError("پرسنل یافت نشد")
        cur = conn.execute(
            """
            INSERT INTO dependents
            (personnel_id, first_name, last_name, national_id, relation,
             birth_date, gender, phone, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pid,
                data.get("first_name", ""),
                data.get("last_name", ""),
                normalize_national_id(data.get("national_id", "")),
                data.get("relation", ""),
                data.get("birth_date", ""),
                data.get("gender", ""),
                data.get("phone", ""),
                data.get("description", ""),
                now, now,
            ),
        )
        row = conn.execute("SELECT * FROM dependents WHERE id=?", (cur.lastrowid,)).fetchone()
        return row_to_dict(row)


def update_dependent(company_code: int, dep_id: int, data: dict) -> dict | None:
    ensure_company_database(company_code)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fields = ["first_name", "last_name", "national_id", "relation",
              "birth_date", "gender", "phone", "description"]
    sets, values = [], []
    for f in fields:
        if f in data:
            val = data[f]
            if f == "national_id":
                val = normalize_national_id(val)
            sets.append(f"{f}=?")
            values.append(val if val is not None else "")
    if not sets:
        return None
    sets.append("updated_at=?")
    values.append(now)
    values.append(dep_id)
    with get_company_db(company_code) as conn:
        conn.execute(f"UPDATE dependents SET {', '.join(sets)} WHERE id=?", values)
        row = conn.execute("SELECT * FROM dependents WHERE id=?", (dep_id,)).fetchone()
        return row_to_dict(row) if row else None


def delete_dependent(company_code: int, dep_id: int) -> bool:
    ensure_company_database(company_code)
    with get_company_db(company_code) as conn:
        cur = conn.execute("DELETE FROM dependents WHERE id=?", (dep_id,))
        return cur.rowcount > 0


# ──────────────────────────────────────────────
# کارت شناسایی پرسنل (در دیتابیس متمرکز)
# ──────────────────────────────────────────────

def list_cards(company_code: int, personnel_id: int = None, status: str = None) -> list:
    ensure_company_database(company_code)
    with get_company_db(company_code) as conn:
        sql = "SELECT * FROM access_cards WHERE 1=1"
        params = []
        if personnel_id is not None:
            sql += " AND personnel_id=?"
            params.append(personnel_id)
        if status:
            sql += " AND status=?"
            params.append(status)
        sql += " ORDER BY id DESC"
        return [row_to_dict(r) for r in conn.execute(sql, params).fetchall()]


def create_card(company_code: int, data: dict) -> dict:
    ensure_company_database(company_code)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pid = int(data.get("personnel_id") or 0)
    if not pid:
        raise ValueError("personnel_id الزامی است")
    with get_company_db(company_code) as conn:
        exists = conn.execute("SELECT id FROM personnel WHERE id=?", (pid,)).fetchone()
        if not exists:
            raise ValueError("پرسنل یافت نشد")
        cur = conn.execute(
            """
            INSERT INTO access_cards
            (personnel_id, card_number, card_type, issue_date, expiry_date,
             status, printed, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pid,
                data.get("card_number", ""),
                data.get("card_type", "شناسایی"),
                data.get("issue_date", ""),
                data.get("expiry_date", ""),
                data.get("status", "فعال"),
                1 if data.get("printed") else 0,
                data.get("description", ""),
                now, now,
            ),
        )
        # همگام‌سازی شماره کارت روی رکورد پرسنل
        card_num = data.get("card_number", "")
        if card_num:
            conn.execute(
                "UPDATE personnel SET card_number=?, card_status=?, validity_start=?, validity_end=?, updated_at=? WHERE id=?",
                (card_num, data.get("status", "فعال"), data.get("issue_date", ""), data.get("expiry_date", ""), now, pid),
            )
        row = conn.execute("SELECT * FROM access_cards WHERE id=?", (cur.lastrowid,)).fetchone()
        return row_to_dict(row)


def update_card(company_code: int, card_id: int, data: dict) -> dict | None:
    ensure_company_database(company_code)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fields = ["card_number", "card_type", "issue_date", "expiry_date", "status", "printed", "description"]
    sets, values = [], []
    for f in fields:
        if f in data:
            val = data[f]
            if f == "printed":
                val = 1 if val else 0
            sets.append(f"{f}=?")
            values.append(val if val is not None else "")
    if not sets:
        return None
    sets.append("updated_at=?")
    values.append(now)
    values.append(card_id)
    with get_company_db(company_code) as conn:
        conn.execute(f"UPDATE access_cards SET {', '.join(sets)} WHERE id=?", values)
        row = conn.execute("SELECT * FROM access_cards WHERE id=?", (card_id,)).fetchone()
        result = row_to_dict(row) if row else None
        if result and result.get("personnel_id"):
            conn.execute(
                "UPDATE personnel SET card_number=?, card_status=?, validity_start=?, validity_end=?, updated_at=? WHERE id=?",
                (
                    result.get("card_number", ""),
                    result.get("status", ""),
                    result.get("issue_date", ""),
                    result.get("expiry_date", ""),
                    now,
                    result["personnel_id"],
                ),
            )
        return result


def delete_card(company_code: int, card_id: int) -> bool:
    ensure_company_database(company_code)
    with get_company_db(company_code) as conn:
        cur = conn.execute("DELETE FROM access_cards WHERE id=?", (card_id,))
        return cur.rowcount > 0


# ──────────────────────────────────────────────
# گزارش‌ها
# ──────────────────────────────────────────────

REPORT_DEFS = {
    "guest": {
        "title": "گزارشات میهمان",
        "sql": "SELECT guest_name AS مهمان, host_name AS میزبان, visit_date AS تاریخ, entry_time AS ورود, exit_time AS خروج, purpose AS هدف, center_name AS مرکز FROM guest_visits ORDER BY id DESC",
    },
    "personnel_traffic": {
        "title": "گزارش تردد پرسنل و پیمانکاران",
        "sql": "SELECT person_name AS نام, person_type AS نوع, direction AS جهت, traffic_date AS تاریخ, traffic_time AS ساعت, door_name AS درب, center_name AS مرکز FROM personnel_traffic ORDER BY id DESC",
    },
    "vehicle_traffic": {
        "title": "گزارش تردد خودروهای پرسنل و پیمانکاران",
        "sql": "SELECT plate_number AS پلاک, driver_name AS راننده, person_type AS نوع, direction AS جهت, traffic_date AS تاریخ, center_name AS مرکز FROM vehicle_traffic ORDER BY id DESC",
    },
    "goods_io": {
        "title": "گزارش ورود و خروج کالا",
        "sql": "SELECT goods_name AS کالا, traffic_type AS نوع, direction AS جهت, traffic_date AS تاریخ, company_name AS شرکت, center_name AS مرکز FROM goods_traffic ORDER BY id DESC",
    },
    "goods_repair": {
        "title": "گزارش کالاهای تعمیری و خدمات",
        "sql": "SELECT goods_name AS کالا, traffic_type AS نوع, direction AS جهت, traffic_date AS تاریخ, company_name AS شرکت FROM goods_traffic WHERE is_repair=1 OR traffic_type IN ('تعمیری','خدمات') ORDER BY id DESC",
    },
    "personnel": {
        "title": "گزارش پرسنل",
        "sql": "SELECT first_name || ' ' || last_name AS نام, national_id AS کدملی, company_code AS شرکت, center AS مرکز, department AS واحد, employment_type AS استخدام FROM personnel ORDER BY id DESC LIMIT 200",
    },
    "contractor_personnel": {
        "title": "گزارش پرسنل پیمانکار",
        "sql": "SELECT person_name AS نام, person_type AS نوع, direction AS جهت, traffic_date AS تاریخ, door_name AS درب FROM personnel_traffic WHERE person_type='پیمانکار' ORDER BY id DESC",
    },
    "cargo_vehicle": {
        "title": "گزارش تردد خودروهای باری",
        "sql": "SELECT plate_number AS پلاک, vehicle_type AS نوع, driver_name AS راننده, company_name AS شرکت, vehicle_weight AS وزن FROM cargo_vehicles ORDER BY id DESC",
    },
    "guard_board": {
        "title": "گزارش لوح نگهبانی",
        "sql": "SELECT center_name AS مرکز, shift_date AS تاریخ, shift_name AS شیفت, work_shift AS نوبت, shift_leader AS مسئول, shift_deputy AS جانشین FROM ent_guard_board ORDER BY id DESC",
    },
    "replacement": {
        "title": "گزارش درخواست جایگزینی",
        "sql": "SELECT request_date AS تاریخ, requester_name AS درخواست‌دهنده, replacement_name AS جایگزین, shift_name AS شیفت, reason AS علت, status AS وضعیت FROM ent_replacement_requests ORDER BY id DESC",
    },
    "misc_traffic": {
        "title": "گزارش تردد افراد متفرقه",
        "sql": "SELECT person_name AS نام, direction AS جهت, traffic_date AS تاریخ, reason AS علت, center_name AS مرکز FROM misc_person_traffic ORDER BY id DESC",
    },
    "system_log": {
        "title": "گزارش لاگ",
        "sql": "SELECT log_date AS تاریخ, log_time AS ساعت, user_name AS کاربر, action AS عملیات, details AS جزئیات FROM system_logs ORDER BY id DESC",
    },
    "contractor_goods": {
        "title": "گزارشات ورود و خروج کالای پیمانکار",
        "sql": "SELECT goods_name AS کالا, traffic_type AS نوع, direction AS جهت, traffic_date AS تاریخ, company_name AS پیمانکار FROM goods_traffic WHERE is_contractor=1 ORDER BY id DESC",
    },
    "traffic_request": {
        "title": "گزارش درخواست تردد",
        "sql": "SELECT request_date AS تاریخ, requester_name AS درخواست‌دهنده, request_type AS نوع, status AS وضعیت, description AS شرح FROM traffic_requests ORDER BY id DESC",
    },
    "guest_reserve": {
        "title": "گزارشات رزرو میهمان",
        "sql": "SELECT guest_name AS مهمان, reserve_date AS تاریخ_رزرو, host_name AS میزبان, status AS وضعیت, center_name AS مرکز FROM guest_reservations ORDER BY id DESC",
    },
    "personnel_history": {
        "title": "گزارشات تاریخچه پرسنل",
        "sql": "SELECT first_name || ' ' || last_name AS نام, national_id AS کدملی, center AS مرکز, department AS واحد, updated_at AS آخرین_بروزرسانی, created_at AS ایجاد FROM personnel ORDER BY COALESCE(updated_at, created_at) DESC LIMIT 200",
    },
    "goods_reserve": {
        "title": "گزارشات رزرو کالا",
        "sql": "SELECT goods_name AS کالا, reserve_date AS تاریخ, requester AS درخواست‌کننده, status AS وضعیت FROM goods_reservations ORDER BY id DESC",
    },
    "ctr_companies": {
        "title": "گزارش شرکت‌های پیمانکار",
        "sql": "SELECT name AS نام_پیمانکار, company_code AS کد_شرکت, employer_company AS کارفرما, parent_company AS شرکت_والد, ceo_name AS مدیرعامل, ceo_mobile AS موبایل_مدیرعامل, rep1_name AS نماینده, company_phone AS تلفن, register_date AS تاریخ_ثبت FROM ctr_companies ORDER BY id DESC",
    },
    "ctr_contracts": {
        "title": "گزارش قرارداد شرکت‌های پیمانکار",
        "sql": "SELECT company_name AS شرکت, contract_number AS شماره_قرارداد, contract_subject AS موضوع, start_date AS شروع, end_date AS پایان, contract_amount AS مبلغ, activity_location AS محل, supervisor_unit AS واحد_ناظر FROM ctr_contracts ORDER BY id DESC",
    },
    "ctr_personnel": {
        "title": "گزارش پرسنل شرکت‌های پیمانکار",
        "sql": "SELECT company_name AS شرکت, first_name AS نام, last_name AS نام_خانوادگی, national_id AS کدملی, personnel_code AS کد_پرسنلی, position AS سمت, mobile_phone AS موبایل, card_status AS وضعیت FROM ctr_personnel ORDER BY id DESC",
    },
    "ctr_vehicles": {
        "title": "گزارش خودروهای پیمانکاران",
        "sql": "SELECT company_name AS شرکت, plate_number AS پلاک, vehicle_type AS نوع, vehicle_class AS کلاس, vehicle_color AS رنگ, owner_first_name || ' ' || owner_last_name AS مالک, card_status AS وضعیت FROM ctr_vehicles ORDER BY id DESC",
    },
    "ctr_drivers": {
        "title": "گزارش راننده‌های پیمانکاران",
        "sql": "SELECT company_name AS شرکت, driver_name AS نام_راننده, national_id AS کدملی, personnel_code AS کد_پرسنلی, license_number AS گواهینامه, license_type AS نوع_گواهینامه, card_status AS وضعیت FROM ctr_drivers ORDER BY id DESC",
    },
}


def list_report_keys():
    return [{"key": k, "title": v["title"]} for k, v in REPORT_DEFS.items()]


def run_report(key: str) -> dict:
    if key not in REPORT_DEFS:
        raise ValueError("گزارش نامعتبر")
    meta = REPORT_DEFS[key]
    with get_main_db() as conn:
        try:
            cur = conn.execute(meta["sql"])
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = [dict(r) for r in cur.fetchall()]
        except Exception as e:
            # fallback empty with message
            cols = ["پیام"]
            rows = [{"پیام": f"خطا در اجرای گزارش: {e}"}]
    return {"key": key, "title": meta["title"], "columns": cols, "rows": rows, "count": len(rows)}


# ═══════════════════════════════════════════════════════════════
# سطوح دسترسی سیستم (تب + گزینه‌های ریبون) و کاربران سیستم
# ═══════════════════════════════════════════════════════════════

def _init_sys_access_schema(conn):
    """جداول سطح دسترسی، مجوزهای تب/ریبون، و کاربران سیستم."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sys_access_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            is_full_admin INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT ''
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sys_access_level_tabs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level_id INTEGER NOT NULL,
            tab_id TEXT NOT NULL,
            UNIQUE(level_id, tab_id),
            FOREIGN KEY (level_id) REFERENCES sys_access_levels(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sys_access_level_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level_id INTEGER NOT NULL,
            action_code TEXT NOT NULL,
            UNIQUE(level_id, action_code),
            FOREIGN KEY (level_id) REFERENCES sys_access_levels(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sys_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL DEFAULT '',
            full_name TEXT DEFAULT '',
            access_level_id INTEGER,
            company_code TEXT DEFAULT '100',
            is_active INTEGER DEFAULT 1,
            can_see_all_companies INTEGER DEFAULT 0,
            created_at TEXT DEFAULT '',
            FOREIGN KEY (access_level_id) REFERENCES sys_access_levels(id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_sys_level_tabs ON sys_access_level_tabs(level_id)"
    )
    # مهاجرت: برگه ترددهای خاص حذف و در صدور مجوز ادغام شد
    try:
        conn.execute(
            "UPDATE sys_access_level_tabs SET tab_id='mojaz' WHERE tab_id='taraddod'"
        )
    except Exception:
        pass
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_sys_level_actions ON sys_access_level_actions(level_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_sys_users_username ON sys_users(username)"
    )


def seed_sys_access_defaults(conn=None):
    """سطح دسترسی پیش‌فرض مدیر کامل + کاربر admin در صورت خالی بودن."""
    own = conn is None
    if own:
        conn = get_main_db().__enter__()
    try:
        n = conn.execute("SELECT COUNT(*) FROM sys_access_levels").fetchone()[0]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if n == 0:
            cur = conn.execute(
                """
                INSERT INTO sys_access_levels (name, description, is_full_admin, is_active, created_at)
                VALUES (?, ?, 1, 1, ?)
                """,
                ("مدیر کامل", "دسترسی کامل به همه برگه‌ها و گزینه‌های ریبون", now),
            )
            full_id = cur.lastrowid
            # سطح نمونه محدود
            cur2 = conn.execute(
                """
                INSERT INTO sys_access_levels (name, description, is_full_admin, is_active, created_at)
                VALUES (?, ?, 0, 1, ?)
                """,
                ("اپراتور حراست", "دسترسی به پرسنل، حراست، انتظامات و گزارشات", now),
            )
            op_id = cur2.lastrowid
            for tab in ("personnel", "herasat", "entezamat", "gozaresh", "sodor_kart"):
                conn.execute(
                    "INSERT OR IGNORE INTO sys_access_level_tabs (level_id, tab_id) VALUES (?, ?)",
                    (op_id, tab),
                )
        else:
            row = conn.execute(
                "SELECT id FROM sys_access_levels WHERE is_full_admin=1 LIMIT 1"
            ).fetchone()
            full_id = row[0] if row else None

        # کاربر admin کلاسیک + AdminUser طبق مشخصات ورود
        for uname, pwd, fname in (
            ("admin", "admin", "مدیر سیستم"),
            ("AdminUser", "AdminUser", "مدیر سیستم"),
        ):
            exists = conn.execute(
                "SELECT id FROM sys_users WHERE username=?", (uname,)
            ).fetchone()
            if not exists and full_id is not None:
                conn.execute(
                    """
                    INSERT INTO sys_users
                    (username, password, full_name, access_level_id, company_code, is_active, can_see_all_companies, created_at)
                    VALUES (?, ?, ?, ?, ?, 1, 1, ?)
                    """,
                    (uname, pwd, fname, full_id, "100", now),
                )
        # همگام‌سازی رمز و سطح کامل AdminUser (حتی اگر از قبل وجود داشته)
        if full_id is not None:
            conn.execute(
                """
                UPDATE sys_users
                SET password=?, full_name=?, access_level_id=?, is_active=1, can_see_all_companies=1
                WHERE lower(username)=lower(?)
                """,
                ("AdminUser", "مدیر سیستم", full_id, "AdminUser"),
            )
            # اگر AdminUser نبود، بساز
            ex = conn.execute(
                "SELECT id FROM sys_users WHERE lower(username)=lower(?)", ("AdminUser",)
            ).fetchone()
            if not ex:
                conn.execute(
                    """
                    INSERT INTO sys_users
                    (username, password, full_name, access_level_id, company_code, is_active, can_see_all_companies, created_at)
                    VALUES (?, ?, ?, ?, ?, 1, 1, ?)
                    """,
                    ("AdminUser", "AdminUser", "مدیر سیستم", full_id, "100", now),
                )
        if own:
            conn.commit()
    finally:
        if own:
            try:
                conn.close()
            except Exception:
                pass


def list_access_levels() -> list:
    with get_main_db() as conn:
        rows = conn.execute(
            """
            SELECT id, name, description, is_full_admin, is_active, created_at
            FROM sys_access_levels ORDER BY id
            """
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["is_full_admin"] = bool(d.get("is_full_admin"))
            d["is_active"] = bool(d.get("is_active"))
            lid = d["id"]
            tabs = [
                x[0]
                for x in conn.execute(
                    "SELECT tab_id FROM sys_access_level_tabs WHERE level_id=?", (lid,)
                ).fetchall()
            ]
            actions = [
                x[0]
                for x in conn.execute(
                    "SELECT action_code FROM sys_access_level_actions WHERE level_id=?",
                    (lid,),
                ).fetchall()
            ]
            d["tabs"] = tabs
            d["actions"] = actions
            d["user_count"] = conn.execute(
                "SELECT COUNT(*) FROM sys_users WHERE access_level_id=?", (lid,)
            ).fetchone()[0]
            result.append(d)
        return result


def get_access_level(level_id: int):
    with get_main_db() as conn:
        row = conn.execute(
            "SELECT * FROM sys_access_levels WHERE id=?", (level_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["is_full_admin"] = bool(d.get("is_full_admin"))
        d["is_active"] = bool(d.get("is_active"))
        d["tabs"] = [
            x[0]
            for x in conn.execute(
                "SELECT tab_id FROM sys_access_level_tabs WHERE level_id=?", (level_id,)
            ).fetchall()
        ]
        d["actions"] = [
            x[0]
            for x in conn.execute(
                "SELECT action_code FROM sys_access_level_actions WHERE level_id=?",
                (level_id,),
            ).fetchall()
        ]
        return d


def create_access_level(
    name: str,
    description: str = "",
    is_full_admin: bool = False,
    tabs=None,
    actions=None,
    is_active: bool = True,
) -> dict:
    name = (name or "").strip()
    if not name:
        raise ValueError("نام سطح دسترسی الزامی است")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_main_db() as conn:
        try:
            cur = conn.execute(
                """
                INSERT INTO sys_access_levels (name, description, is_full_admin, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, description or "", 1 if is_full_admin else 0, 1 if is_active else 0, now),
            )
        except sqlite3.IntegrityError:
            raise ValueError("نام سطح دسترسی تکراری است")
        lid = cur.lastrowid
        if not is_full_admin:
            for t in tabs or []:
                if t:
                    conn.execute(
                        "INSERT OR IGNORE INTO sys_access_level_tabs (level_id, tab_id) VALUES (?, ?)",
                        (lid, str(t)),
                    )
            for a in actions or []:
                if a:
                    conn.execute(
                        "INSERT OR IGNORE INTO sys_access_level_actions (level_id, action_code) VALUES (?, ?)",
                        (lid, str(a)),
                    )
        conn.commit()
    return get_access_level(lid)


def update_access_level(
    level_id: int,
    name=None,
    description=None,
    is_full_admin=None,
    tabs=None,
    actions=None,
    is_active=None,
) -> dict:
    existing = get_access_level(level_id)
    if not existing:
        raise ValueError("سطح دسترسی یافت نشد")
    with get_main_db() as conn:
        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("نام سطح دسترسی الزامی است")
            try:
                conn.execute(
                    "UPDATE sys_access_levels SET name=? WHERE id=?", (name, level_id)
                )
            except sqlite3.IntegrityError:
                raise ValueError("نام سطح دسترسی تکراری است")
        if description is not None:
            conn.execute(
                "UPDATE sys_access_levels SET description=? WHERE id=?",
                (description, level_id),
            )
        if is_full_admin is not None:
            conn.execute(
                "UPDATE sys_access_levels SET is_full_admin=? WHERE id=?",
                (1 if is_full_admin else 0, level_id),
            )
        if is_active is not None:
            conn.execute(
                "UPDATE sys_access_levels SET is_active=? WHERE id=?",
                (1 if is_active else 0, level_id),
            )
        # به‌روزرسانی مجوزها اگر ارسال شده
        full = is_full_admin if is_full_admin is not None else existing["is_full_admin"]
        if tabs is not None or actions is not None or is_full_admin is not None:
            if full:
                conn.execute("DELETE FROM sys_access_level_tabs WHERE level_id=?", (level_id,))
                conn.execute(
                    "DELETE FROM sys_access_level_actions WHERE level_id=?", (level_id,)
                )
            else:
                if tabs is not None:
                    conn.execute(
                        "DELETE FROM sys_access_level_tabs WHERE level_id=?", (level_id,)
                    )
                    for t in tabs:
                        if t:
                            conn.execute(
                                "INSERT OR IGNORE INTO sys_access_level_tabs (level_id, tab_id) VALUES (?, ?)",
                                (level_id, str(t)),
                            )
                if actions is not None:
                    conn.execute(
                        "DELETE FROM sys_access_level_actions WHERE level_id=?",
                        (level_id,),
                    )
                    for a in actions:
                        if a:
                            conn.execute(
                                "INSERT OR IGNORE INTO sys_access_level_actions (level_id, action_code) VALUES (?, ?)",
                                (level_id, str(a)),
                            )
        conn.commit()
    return get_access_level(level_id)


def delete_access_level(level_id: int) -> None:
    with get_main_db() as conn:
        used = conn.execute(
            "SELECT COUNT(*) FROM sys_users WHERE access_level_id=?", (level_id,)
        ).fetchone()[0]
        if used:
            raise ValueError("این سطح به یک یا چند کاربر اختصاص داده شده و قابل حذف نیست")
        conn.execute("DELETE FROM sys_access_level_tabs WHERE level_id=?", (level_id,))
        conn.execute("DELETE FROM sys_access_level_actions WHERE level_id=?", (level_id,))
        cur = conn.execute("DELETE FROM sys_access_levels WHERE id=?", (level_id,))
        if cur.rowcount == 0:
            raise ValueError("سطح دسترسی یافت نشد")
        conn.commit()


def list_sys_users() -> list:
    with get_main_db() as conn:
        rows = conn.execute(
            """
            SELECT u.id, u.username, u.full_name, u.access_level_id, u.company_code,
                   u.is_active, u.can_see_all_companies, u.created_at,
                   l.name AS access_level_name, l.is_full_admin
            FROM sys_users u
            LEFT JOIN sys_access_levels l ON l.id = u.access_level_id
            ORDER BY u.id
            """
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["is_active"] = bool(d.get("is_active"))
            d["can_see_all_companies"] = bool(d.get("can_see_all_companies"))
            d["is_full_admin"] = bool(d.get("is_full_admin"))
            d.pop("password", None)
            result.append(d)
        return result


def get_sys_user(user_id: int):
    with get_main_db() as conn:
        row = conn.execute(
            """
            SELECT u.id, u.username, u.full_name, u.access_level_id, u.company_code,
                   u.is_active, u.can_see_all_companies, u.created_at,
                   l.name AS access_level_name, l.is_full_admin
            FROM sys_users u
            LEFT JOIN sys_access_levels l ON l.id = u.access_level_id
            WHERE u.id=?
            """,
            (user_id,),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["is_active"] = bool(d.get("is_active"))
        d["can_see_all_companies"] = bool(d.get("can_see_all_companies"))
        d["is_full_admin"] = bool(d.get("is_full_admin"))
        return d


def create_sys_user(
    username: str,
    password: str = "",
    full_name: str = "",
    access_level_id=None,
    company_code: str = "100",
    is_active: bool = True,
    can_see_all_companies: bool = False,
) -> dict:
    username = (username or "").strip()
    if not username:
        raise ValueError("نام کاربری الزامی است")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_main_db() as conn:
        try:
            cur = conn.execute(
                """
                INSERT INTO sys_users
                (username, password, full_name, access_level_id, company_code, is_active, can_see_all_companies, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    password or "",
                    full_name or "",
                    access_level_id,
                    str(company_code or "100"),
                    1 if is_active else 0,
                    1 if can_see_all_companies else 0,
                    now,
                ),
            )
        except sqlite3.IntegrityError:
            raise ValueError("نام کاربری تکراری است")
        uid = cur.lastrowid
        conn.commit()
    return get_sys_user(uid)


def update_sys_user(
    user_id: int,
    username=None,
    password=None,
    full_name=None,
    access_level_id=None,
    company_code=None,
    is_active=None,
    can_see_all_companies=None,
    clear_access_level: bool = False,
) -> dict:
    if not get_sys_user(user_id):
        raise ValueError("کاربر یافت نشد")
    with get_main_db() as conn:
        if username is not None:
            username = username.strip()
            if not username:
                raise ValueError("نام کاربری الزامی است")
            try:
                conn.execute(
                    "UPDATE sys_users SET username=? WHERE id=?", (username, user_id)
                )
            except sqlite3.IntegrityError:
                raise ValueError("نام کاربری تکراری است")
        if password is not None and password != "":
            conn.execute("UPDATE sys_users SET password=? WHERE id=?", (password, user_id))
        if full_name is not None:
            conn.execute(
                "UPDATE sys_users SET full_name=? WHERE id=?", (full_name, user_id)
            )
        if clear_access_level:
            conn.execute(
                "UPDATE sys_users SET access_level_id=NULL WHERE id=?", (user_id,)
            )
        elif access_level_id is not None:
            conn.execute(
                "UPDATE sys_users SET access_level_id=? WHERE id=?",
                (access_level_id, user_id),
            )
        if company_code is not None:
            conn.execute(
                "UPDATE sys_users SET company_code=? WHERE id=?",
                (str(company_code), user_id),
            )
        if is_active is not None:
            conn.execute(
                "UPDATE sys_users SET is_active=? WHERE id=?",
                (1 if is_active else 0, user_id),
            )
        if can_see_all_companies is not None:
            conn.execute(
                "UPDATE sys_users SET can_see_all_companies=? WHERE id=?",
                (1 if can_see_all_companies else 0, user_id),
            )
        conn.commit()
    return get_sys_user(user_id)


def delete_sys_user(user_id: int) -> None:
    with get_main_db() as conn:
        row = conn.execute(
            "SELECT username FROM sys_users WHERE id=?", (user_id,)
        ).fetchone()
        if not row:
            raise ValueError("کاربر یافت نشد")
        if row[0] == "admin":
            raise ValueError("کاربر admin قابل حذف نیست")
        conn.execute("DELETE FROM sys_users WHERE id=?", (user_id,))
        conn.commit()



def _normalize_tab_ids(tabs):
    """حذف برگه حذف‌شده ترددهای خاص و ادغام در صدور مجوز تردد."""
    if not tabs:
        return tabs
    out = []
    seen = set()
    for t in tabs:
        tid = "mojaz" if str(t) == "taraddod" else str(t)
        if tid not in seen:
            seen.add(tid)
            out.append(tid)
    return out

def get_user_permissions(user_id=None, username=None):
    """مجوزهای کاربر برای فیلتر UI: tabs + actions + is_full_admin."""
    with get_main_db() as conn:
        if user_id is not None:
            row = conn.execute(
                "SELECT * FROM sys_users WHERE id=?", (user_id,)
            ).fetchone()
        elif username:
            row = conn.execute(
                "SELECT * FROM sys_users WHERE lower(username)=lower(?)", (username,)
            ).fetchone()
        else:
            return {"is_full_admin": True, "tabs": [], "actions": []}
        if not row:
            return {"is_full_admin": False, "tabs": [], "actions": [], "user": None}
        u = dict(row)
        level_id = u.get("access_level_id")
        if not level_id:
            return {
                "is_full_admin": False,
                "tabs": [],
                "actions": [],
                "user": {
                    "id": u["id"],
                    "username": u["username"],
                    "full_name": u.get("full_name"),
                },
            }
        level = conn.execute(
            "SELECT * FROM sys_access_levels WHERE id=?", (level_id,)
        ).fetchone()
        if not level:
            return {"is_full_admin": False, "tabs": [], "actions": []}
        lv = dict(level)
        if lv.get("is_full_admin"):
            return {
                "is_full_admin": True,
                "tabs": [],
                "actions": [],
                "user": {
                    "id": u["id"],
                    "username": u["username"],
                    "full_name": u.get("full_name"),
                    "access_level_id": level_id,
                    "access_level_name": lv.get("name"),
                    "company_code": u.get("company_code"),
                    "can_see_all_companies": bool(u.get("can_see_all_companies")),
                },
            }
        tabs = [
            x[0]
            for x in conn.execute(
                "SELECT tab_id FROM sys_access_level_tabs WHERE level_id=?", (level_id,)
            ).fetchall()
        ]
        actions = [
            x[0]
            for x in conn.execute(
                "SELECT action_code FROM sys_access_level_actions WHERE level_id=?",
                (level_id,),
            ).fetchall()
        ]
        return {
            "is_full_admin": False,
            "tabs": _normalize_tab_ids(tabs),
            "actions": actions,
            "user": {
                "id": u["id"],
                "username": u["username"],
                "full_name": u.get("full_name"),
                "access_level_id": level_id,
                "access_level_name": lv.get("name"),
                "company_code": u.get("company_code"),
                "can_see_all_companies": bool(u.get("can_see_all_companies")),
            },
        }


# ─── مجوزهای تردد (صدور مجوز) ───────────────────────────────────────────


_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_EN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

def to_persian_digits(s) -> str:
    return str(s if s is not None else "").translate(_FA_DIGITS)

def to_english_digits(s) -> str:
    return str(s if s is not None else "").translate(_EN_DIGITS)

def gregorian_to_jalali(gy: int, gm: int, gd: int):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy + 1 if gm > 2 else gy
    days = (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) - 80 + gd + g_d_m[gm - 1]
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + (days % 31)
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + ((days - 186) % 30)
    return jy, jm, jd

def now_jalali_datetime() -> str:
    import datetime as _dt
    n = _dt.datetime.now()
    jy, jm, jd = gregorian_to_jalali(n.year, n.month, n.day)
    s = f"{jy:04d}/{jm:02d}/{jd:02d} {n.hour:02d}:{n.minute:02d}:{n.second:02d}"
    return to_persian_digits(s)

def now_jalali_date_compact() -> str:
    import datetime as _dt
    n = _dt.datetime.now()
    jy, jm, jd = gregorian_to_jalali(n.year, n.month, n.day)
    return to_persian_digits(f"{jy:04d}{jm:02d}{jd:02d}")


def _parse_time_to_minutes(time_str: str):
    """ساعت:دقیقه → دقیقه از نیمه‌شب (ارقام فارسی هم پشتیبانی می‌شود)."""
    s = to_english_digits((time_str or "").strip())
    if not s:
        return None
    import re
    m = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", s)
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


def _parse_jalali_date_parts(date_str: str):
    s = to_english_digits((date_str or "").strip()).replace("-", "/")
    import re
    m = re.search(r"(\d{4})/(\d{1,2})/(\d{1,2})", s)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _jalali_to_approx_days(y, m, d) -> int:
    return y * 365 + (m - 1) * 31 + d


def format_delay_hm(total_minutes: int) -> str:
    """دقیقه → «۲ ساعت و ۱۵ دقیقه» با ارقام فارسی."""
    m = abs(int(total_minutes))
    h, mi = divmod(m, 60)
    parts = []
    if h:
        parts.append(f"{to_persian_digits(h)} ساعت")
    if mi or not h:
        parts.append(f"{to_persian_digits(mi)} دقیقه")
    return " و ".join(parts)


def compute_entry_exit_delay(allowed_date: str, allowed_time: str, actual_jalali_dt: str):
    """
    اختلاف زمان مجاز و زمان واقعی.
    minutes > 0 تأخیر، < 0 تعجیل، 0 به‌موقع
    """
    act_date = _parse_jalali_date_parts(actual_jalali_dt)
    act_min = _parse_time_to_minutes(actual_jalali_dt)
    all_date = _parse_jalali_date_parts(allowed_date) if allowed_date else act_date
    all_min = _parse_time_to_minutes(allowed_time)
    if act_min is None or all_min is None:
        return 0, "—"
    day_diff = 0
    if act_date and all_date:
        day_diff = _jalali_to_approx_days(*act_date) - _jalali_to_approx_days(*all_date)
    total = day_diff * 24 * 60 + (act_min - all_min)
    if total > 0:
        label = f"تأخیر {format_delay_hm(total)}"
    elif total < 0:
        label = f"تعجیل {format_delay_hm(abs(total))}"
    else:
        label = "به‌موقع"
    return total, label


def ensure_mjz_permits_table():
    with get_main_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mjz_permits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                permit_no TEXT UNIQUE NOT NULL,
                permit_type TEXT NOT NULL,
                status TEXT DEFAULT 'issued',
                holder_name TEXT DEFAULT '',
                national_id TEXT DEFAULT '',
                personnel_code TEXT DEFAULT '',
                company_name TEXT DEFAULT '',
                unit_name TEXT DEFAULT '',
                vehicle_plate TEXT DEFAULT '',
                vehicle_type TEXT DEFAULT '',
                driver_name TEXT DEFAULT '',
                goods_desc TEXT DEFAULT '',
                goods_count TEXT DEFAULT '',
                purpose TEXT DEFAULT '',
                destination TEXT DEFAULT '',
                gate_name TEXT DEFAULT '',
                valid_from TEXT DEFAULT '',
                valid_to TEXT DEFAULT '',
                allowed_entry_date TEXT DEFAULT '',
                allowed_entry_time TEXT DEFAULT '',
                allowed_exit_date TEXT DEFAULT '',
                allowed_exit_time TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                issued_by TEXT DEFAULT '',
                entry_at TEXT DEFAULT '',
                entry_delay TEXT DEFAULT '',
                entry_delay_minutes INTEGER DEFAULT 0,
                exit_at TEXT DEFAULT '',
                exit_delay TEXT DEFAULT '',
                exit_delay_minutes INTEGER DEFAULT 0,
                entry_by TEXT DEFAULT '',
                exit_by TEXT DEFAULT '',
                company_code TEXT DEFAULT '100',
                created_at TEXT DEFAULT ''
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mjz_permit_no ON mjz_permits(permit_no)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mjz_status ON mjz_permits(status)")
        for col in ("allowed_entry_date", "allowed_entry_time", "allowed_exit_date", "allowed_exit_time", "entry_delay", "exit_delay", "entry_delay_minutes", "exit_delay_minutes"):
            try:
                cols = [r[1] for r in conn.execute("PRAGMA table_info(mjz_permits)").fetchall()]
                if col not in cols:
                    conn.execute(f"ALTER TABLE mjz_permits ADD COLUMN {col} TEXT DEFAULT ''")
            except Exception:
                pass


def _next_permit_no(conn, permit_type: str = "person") -> str:
    """
    شماره مجوز:
      {تاریخ‌جلالی‌فشرده}_{رقم‌نوع}{سریال۵رقمی}
    مثال: 14050719_100001

    رقم نوع: 1=نفر، 2=خودرو، 3=کالا
    سریال روزانه ۶ رقمی است (با احتساب رقم نوع) و هر روز از اول برای همان نوع شروع می‌شود.
    """
    import datetime as _dt
    n = _dt.datetime.now()
    jy, jm, jd = gregorian_to_jalali(n.year, n.month, n.day)
    day = f"{jy:04d}{jm:02d}{jd:02d}"  # ارقام لاتین مطابق نمونه کاربر

    type_digit = {"person": "1", "vehicle": "2", "goods": "3"}.get(
        (permit_type or "person").strip(), "1"
    )
    # همه مجوزهای همین روز و همین نوع: 14050719_1%%%%%
    like = f"{day}_{type_digit}%"
    rows = conn.execute(
        "SELECT permit_no FROM mjz_permits WHERE permit_no LIKE ? ORDER BY id DESC",
        (like,),
    ).fetchall()
    seq = 1
    for r in rows:
        try:
            tail = to_english_digits(str(r[0]).split("_", 1)[-1])
            # tail مثل 100001 → پنج رقم آخر سریال روزانه
            if len(tail) >= 6 and tail[0] == type_digit:
                seq = max(seq, int(tail[1:]) + 1)
                break
            elif tail.isdigit() and tail.startswith(type_digit):
                seq = max(seq, int(tail[1:] or "0") + 1)
                break
        except Exception:
            continue
    if seq < 1:
        seq = 1
    if seq > 99999:
        seq = 99999
    serial = f"{type_digit}{seq:05d}"  # ۶ رقم: 100001
    return f"{day}_{serial}"



def list_mjz_permits(permit_type=None, status=None, q=None, company_code=None, limit=200):
    ensure_mjz_permits_table()
    with get_main_db() as conn:
        sql = "SELECT * FROM mjz_permits WHERE 1=1"
        args = []
        if permit_type:
            sql += " AND permit_type=?"
            args.append(permit_type)
        if status:
            sql += " AND status=?"
            args.append(status)
        if company_code:
            sql += " AND company_code=?"
            args.append(str(company_code))
        if q:
            sql += """ AND (
                permit_no LIKE ? OR holder_name LIKE ? OR national_id LIKE ?
                OR vehicle_plate LIKE ? OR personnel_code LIKE ? OR driver_name LIKE ?
                OR company_name LIKE ? OR goods_desc LIKE ? OR issued_by LIKE ?
                OR gate_name LIKE ? OR destination LIKE ? OR purpose LIKE ?
                OR unit_name LIKE ?
            )"""
            qq = f"%{q}%"
            args.extend([qq] * 13)
        sql += " ORDER BY id DESC LIMIT ?"
        args.append(int(limit))
        return [dict(r) for r in conn.execute(sql, args).fetchall()]


def get_mjz_permit(permit_id=None, permit_no=None):
    ensure_mjz_permits_table()
    with get_main_db() as conn:
        if permit_id is not None:
            row = conn.execute("SELECT * FROM mjz_permits WHERE id=?", (permit_id,)).fetchone()
        elif permit_no:
            row = conn.execute("SELECT * FROM mjz_permits WHERE permit_no=?", (str(permit_no).strip(),)).fetchone()
        else:
            return None
        return dict(row) if row else None


def create_mjz_permit(data: dict) -> dict:
    ensure_mjz_permits_table()
    import datetime as _dt
    now = now_jalali_datetime()
    with get_main_db() as conn:
        ptype = (data.get("permit_type") or "person").strip()
        permit_no = (data.get("permit_no") or "").strip() or _next_permit_no(conn, ptype)
        cur = conn.execute(
            """
            INSERT INTO mjz_permits (
                permit_no, permit_type, status,
                holder_name, national_id, personnel_code, company_name, unit_name,
                vehicle_plate, vehicle_type, driver_name,
                goods_desc, goods_count, purpose, destination, gate_name,
                valid_from, valid_to,
                allowed_entry_date, allowed_entry_time, allowed_exit_date, allowed_exit_time,
                notes, issued_by, company_code, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                permit_no, ptype, data.get("status") or "issued",
                data.get("holder_name") or "", data.get("national_id") or "",
                data.get("personnel_code") or "", data.get("company_name") or "",
                data.get("unit_name") or "", data.get("vehicle_plate") or "",
                data.get("vehicle_type") or "", data.get("driver_name") or "",
                data.get("goods_desc") or "", data.get("goods_count") or "",
                data.get("purpose") or "", data.get("destination") or "",
                data.get("gate_name") or "", data.get("valid_from") or "",
                data.get("valid_to") or "",
                data.get("allowed_entry_date") or "", data.get("allowed_entry_time") or "",
                data.get("allowed_exit_date") or "", data.get("allowed_exit_time") or "",
                data.get("notes") or "",
                (data.get("issued_by") or "").strip() or "سیستم", str(data.get("company_code") or "100"), now,
            ),
        )
        row = conn.execute("SELECT * FROM mjz_permits WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(row)


def update_mjz_permit(permit_id: int, data: dict) -> dict:
    ensure_mjz_permits_table()
    allowed = [
        "status", "holder_name", "national_id", "personnel_code", "company_name",
        "unit_name", "vehicle_plate", "vehicle_type", "driver_name",
        "goods_desc", "goods_count", "purpose", "destination", "gate_name",
        "valid_from", "valid_to", "allowed_entry_date", "allowed_entry_time", "allowed_exit_date", "allowed_exit_time", "notes", "issued_by",
    ]
    sets, args = [], []
    for k in allowed:
        if k in data:
            sets.append(f"{k}=?")
            args.append(data[k] if data[k] is not None else "")
    if not sets:
        return get_mjz_permit(permit_id=permit_id)
    args.append(permit_id)
    with get_main_db() as conn:
        conn.execute(f"UPDATE mjz_permits SET {', '.join(sets)} WHERE id=?", args)
        row = conn.execute("SELECT * FROM mjz_permits WHERE id=?", (permit_id,)).fetchone()
        return dict(row) if row else None


def confirm_mjz_entry(permit_id: int, guard_name: str = "") -> dict:
    ensure_mjz_permits_table()
    now = now_jalali_datetime()
    with get_main_db() as conn:
        row = conn.execute("SELECT * FROM mjz_permits WHERE id=?", (permit_id,)).fetchone()
        if not row:
            raise ValueError("مجوز یافت نشد")
        d = dict(row)
        if d.get("entry_at"):
            raise ValueError(f"ورود قبلاً در {d['entry_at']} ثبت شده است")
        if d.get("status") == "cancelled":
            raise ValueError("این مجوز لغو شده است")
        delay_min, delay_label = compute_entry_exit_delay(
            d.get("allowed_entry_date") or d.get("valid_from") or "",
            d.get("allowed_entry_time") or "",
            now,
        )
        conn.execute(
            """UPDATE mjz_permits
               SET entry_at=?, entry_by=?, status='entered',
                   entry_delay=?, entry_delay_minutes=?
               WHERE id=?""",
            (now, guard_name or "نگهبان ورودی", delay_label, int(delay_min), permit_id),
        )
        return dict(conn.execute("SELECT * FROM mjz_permits WHERE id=?", (permit_id,)).fetchone())


def confirm_mjz_exit(permit_id: int, guard_name: str = "") -> dict:
    ensure_mjz_permits_table()
    now = now_jalali_datetime()
    with get_main_db() as conn:
        row = conn.execute("SELECT * FROM mjz_permits WHERE id=?", (permit_id,)).fetchone()
        if not row:
            raise ValueError("مجوز یافت نشد")
        d = dict(row)
        if not d.get("entry_at"):
            raise ValueError("ابتدا باید ورود تأیید شود")
        if d.get("exit_at"):
            raise ValueError(f"خروج قبلاً در {d['exit_at']} ثبت شده است")
        if d.get("status") == "cancelled":
            raise ValueError("این مجوز لغو شده است")
        delay_min, delay_label = compute_entry_exit_delay(
            d.get("allowed_exit_date") or d.get("valid_to") or "",
            d.get("allowed_exit_time") or "",
            now,
        )
        conn.execute(
            """UPDATE mjz_permits
               SET exit_at=?, exit_by=?, status='exited',
                   exit_delay=?, exit_delay_minutes=?
               WHERE id=?""",
            (now, guard_name or "نگهبان ورودی", delay_label, int(delay_min), permit_id),
        )
        return dict(conn.execute("SELECT * FROM mjz_permits WHERE id=?", (permit_id,)).fetchone())


def delete_mjz_permit(permit_id: int) -> bool:
    ensure_mjz_permits_table()
    with get_main_db() as conn:
        return conn.execute("DELETE FROM mjz_permits WHERE id=?", (permit_id,)).rowcount > 0


def seed_mjz_and_clients_samples(force: bool = False):
    """رکوردهای نمونه: شرکت‌های پایه، مجوزها با تاریخ جلالی."""
    ensure_mjz_permits_table()
    import datetime as _dt
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_main_db() as conn:
        # شرکت‌ها/مشتری‌ها در اطلاعات پایه
        try:
            n = conn.execute("SELECT COUNT(*) FROM client_companies").fetchone()[0]
        except Exception:
            n = 0
        if force or n == 0:
            samples = [
                ("تأسیسات دریایی ایران (ستاد)", "100", "021-12345678", "تهران", "ستاد"),
                ("شرکت مهندسی و ساخت تأسیسات دریایی ایران", "101", "021-87654321", "تهران", "عملیات"),
                ("شرکت خدمات پشتیبانی دریایی", "102", "077-33445566", "بوشهر", "پشتیبانی"),
                ("پیمانکار نمونه پارس", "P-01", "09121234567", "عسلویه", "پیمانکار"),
            ]
            for name, code, phone, addr, desc in samples:
                exists = conn.execute(
                    "SELECT id FROM client_companies WHERE name=?", (name,)
                ).fetchone()
                if not exists:
                    conn.execute(
                        "INSERT INTO client_companies (name, code, phone, address, description) VALUES (?,?,?,?,?)",
                        (name, code, phone, addr, desc),
                    )
        # مجوزهای نمونه — برای هر نوع یک رکورد (در صورت نبود، درج می‌شود)
        samples_p = [
            (
                "نفر-نمونه-۰۰۰۱", "person",
                "علی محمدی", "0012345678", "P-1001",
                "تأسیسات دریایی ایران (ستاد)", "حراست ستاد",
                "", "", "",
                "", "",
                "ملاقات اداری", "ساختمان ستاد", "دروازه اصلی",
                "1405/07/20", "1405/07/25",
                "1405/07/20", "08:00", "1405/07/20", "17:00",
            ),
            (
                "خودرو-نمونه-۰۰۰۱", "vehicle",
                "رضا کریمی", "0011122233", "P-2002",
                "شرکت خدمات پشتیبانی دریایی", "پشتیبانی ناوگان",
                "12ب345ایران67", "سواری", "رضا کریمی",
                "", "",
                "حمل تجهیزات", "پایگاه خارک", "دروازه خودرو",
                "1405/07/20", "1405/07/22",
                "1405/07/20", "07:30", "1405/07/22", "18:00",
            ),
            (
                "کالا-نمونه-۰۰۰۱", "goods",
                "حسین نوری", "0044455566", "",
                "پیمانکار نمونه پارس", "انبار مرکزی",
                "22ج998ایران11", "باری", "حسین نوری",
                "لوله و اتصالات دریایی", "12 بسته",
                "خروج کالا", "انبار بندر", "دروازه کالا",
                "1405/07/21", "1405/07/21",
                "1405/07/21", "09:00", "1405/07/21", "15:30",
            ),
        ]
        for row in samples_p:
            (pno, ptype, hname, nid, pcode, cname, unit, plate, vtype, driver, gdesc, gcnt,
             purpose, dest, gate, vf, vt, aed, aet, axd, axt) = row
            ex = conn.execute("SELECT id FROM mjz_permits WHERE permit_no=?", (pno,)).fetchone()
            if not ex:
                conn.execute(
                    """
                    INSERT INTO mjz_permits (
                        permit_no, permit_type, status, holder_name, national_id, personnel_code,
                        company_name, unit_name, vehicle_plate, vehicle_type, driver_name, goods_desc, goods_count,
                        purpose, destination, gate_name, valid_from, valid_to,
                        allowed_entry_date, allowed_entry_time, allowed_exit_date, allowed_exit_time,
                        notes, issued_by, company_code, created_at
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (pno, ptype, "issued", hname, nid, pcode, cname, unit, plate, vtype, driver, gdesc, gcnt,
                     purpose, dest, gate, vf, vt, aed, aet, axd, axt, "رکورد نمونه برای تست", "AdminUser", "100", now),
                )

def ensure_ctr_employer_column():
    with get_main_db() as conn:
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(ctr_companies)").fetchall()]
            if "employer_company" not in cols:
                conn.execute("ALTER TABLE ctr_companies ADD COLUMN employer_company TEXT DEFAULT ''")
        except Exception:
            pass


def migrate_mjz_persian_codes():
    """به‌روزرسانی شماره‌های نمونه و زمان‌های میلادی به جلالی/فارسی."""
    ensure_mjz_permits_table()
    mapping = {
        "PRN-SAMPLE-0001": "نفر-نمونه-۰۰۰۱",
        "VEH-SAMPLE-0001": "خودرو-نمونه-۰۰۰۱",
        "GDS-SAMPLE-0001": "کالا-نمونه-۰۰۰۱",
    }
    with get_main_db() as conn:
        for old, new in mapping.items():
            row = conn.execute("SELECT id FROM mjz_permits WHERE permit_no=?", (old,)).fetchone()
            if row:
                exists_new = conn.execute("SELECT id FROM mjz_permits WHERE permit_no=?", (new,)).fetchone()
                if exists_new:
                    conn.execute("DELETE FROM mjz_permits WHERE permit_no=?", (old,))
                else:
                    conn.execute("UPDATE mjz_permits SET permit_no=? WHERE permit_no=?", (new, old))
        # زمان‌های میلادی قدیمی (شامل - و ارقام لاتین سال ۲۰xx) را خالی می‌کنیم تا دوباره با جلالی ثبت شوند
        rows = conn.execute("SELECT id, entry_at, exit_at FROM mjz_permits").fetchall()
        for r in rows:
            rid, ea, xa = r[0], r[1] or "", r[2] or ""
            if ea and ("-" in ea) and any(c.isdigit() and c in "0123456789" for c in ea) and "20" in ea:
                conn.execute("UPDATE mjz_permits SET entry_at='', exit_at='', status='issued' WHERE id=?", (rid,))
