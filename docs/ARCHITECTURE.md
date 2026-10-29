# معماری سامانه دژبان (حراست صندوق بازنشستگان نفت)

نسخه مستند: **۵۳** — هم‌تراز با `dejban-project_v48`

---


## UI نوار برگه‌ها (نسخه ۵۳)

به‌خاطر تعداد زیاد تب‌ها، نوار برگه (`tab-bar`) داخل کانتینر `tab-bar-scroll` با `overflow-x: auto` قرار دارد.
با `transform: rotateX(180deg)` روی اسکرولر و معکوس آن روی محتوا، **نوار اسکرول افقی بالای نام برگه‌ها** نمایش داده می‌شود.

## ۱. نمای کلی

| لایه | فناوری |
|------|--------|
| فرانت‌اند | React + Vite، UI ریبون شبیه دژبان |
| بک‌اند | FastAPI (Python) |
| پایگاه داده | **یک فایل متمرکز** `backend/data/dejban.db` (SQLite) |
| چندشرکتی | جدول `companies` + فیلتر منطقی با ستون `company_code` |

اجرای محلی معمول:

- API: از پوشه `backend` با uvicorn
- UI: از پوشه `frontend` با Vite (پروکسی به API)

---

## ۲. اصل محوری: اطلاعات پایه = Source of Truth

برگه **اطلاعات پایه** تنها منبع حقیقت برای داده‌های مرجع است.

**الزام:** هر فیلدی در سایر برگه‌ها (پرسنل، کارت، مجوز، تردد، …) که معادلش در اطلاعات پایه وجود دارد — مانند رشته تحصیلی، واحد/مرکز، گروه مسئولیت، نوع استخدام، نوع خودرو، نوع ورود/خروج کالا — **باید از API اطلاعات پایه به‌صورت select خوانده شود**؛ متن آزاد یا hard-code برای مقادیر مرجع ممنوع است.

### چرا؟

1. یکپارچگی نام‌ها با یک تغییر مرکزی
2. افزودن گزینه بدون تغییر کد فرم‌ها
3. هم‌خوانی با الگوی سامانه دژبان اصلی

### قانون توسعه

1. گزینهٔ لیست‌شدنی جدید → اول در اطلاعات پایه / انتظامات تعریف شود
2. فیلد پرسنل جدید → فقط به `PERSONAL_FIELDS` در `database.py` (migrate خودکار)
3. این سند و مودال «مستندات معماری» داخل برنامه را هم‌زمان به‌روز کنید

---

## ۳. دیتابیس متمرکز

- مسیر: `backend/data/dejban.db` (`MAIN_DB`)
- اتصال: `get_main_db()` / سازگاری قدیمی `get_companies_db()`
- `company_code` همیشه **رشته** (`_norm_company_code`) تا ایندکس ترکیبی کار کند
- مهاجرت یک‌باره از `co_*.db` قدیمی در `init_db` در صورت وجود

### ایندکس‌های مهم پرسنل

| ایندکس | کاربرد |
|--------|--------|
| `idx_pers_company_id (company_code, id)` | لیست و صفحه‌بندی هر شرکت |
| `idx_pers_company_active` | فیلتر فعال/غیرفعال |
| `idx_pers_national_id` / `indicator` / `phone` | جستجو |

سایر: `dependents(personnel_id)`، `access_cards(personnel_id)`، `units(center_name, name)`، پلاک خودرو و بارکد کالا.

داده نمونه: `seed_demo_records()` در `init_db` و `POST /api/admin/seed-demo`

---

## ۴. تب‌های اصلی UI

ترتیب تب‌ها:

پرسنل → شرکت‌های تابعه → **گشت و پایش** → صدور مجوز → پیمانکاران → ترددهای خاص → **انتظامات** → **حراست** → **مناقصات و مزایدات** → **کارتابل** → **صدور کارت** → **اطلاعات پایه** → **گزارشات** → **مدیریت سیستم**

| تب | نقش |
|----|-----|
| **پرسنل** | لیست، ثبت/ویرایش مشخصات، وابستگان، صدور کارت (مستقل از اطلاعات پایه) |
| **صدور کارت** | چاپ و گزارش کارت پرسنل / پیمانکار / خودرو (جداول `card_*`) |
| **اطلاعات پایه** | فقط جداول مرجع |
| **انتظامات** | تعاریف نگهبانی/شیفت (مرجع) |
| **گزارشات** | ۱۷ گزارش عملیاتی با API و نتیجه از DB |
| **مدیریت سیستم** | تنظیمات، مستندات معماری، آرشیو |

اکشن بدون بک‌اند: مجموعه `IMPLEMENTED_ACTIONS`؛ بقیه `notifyComingSoon` → «به زودی فعال می‌شود».

---

## ۵. اطلاعات پایه — فریم‌های ریبون

### ساختار سازمانی

| فرم | جدول / API |
|-----|------------|
| تعریف واحدها (مرکز + واحد) | `units` → `/api/units` |

**مرکز** = `units.center_name` و **واحد** = `units.name`؛ فقط از همین تعریف.

### جداول پرسنلی (lookup)

| فرم | جدول | API |
|-----|------|-----|
| رشته تحصیلی | `education_fields` | `/api/lookups/education_fields` |
| گروه مسئولیت | `responsibility_groups` | `/api/lookups/responsibility_groups` |
| انواع استخدام | `employment_types` | `/api/lookups/employment_types` |

### تردد و دسترسی

| فرم | جدول | API |
|-----|------|-----|
| درب‌های تردد | `access_doors` | `/api/baseinfo/access_doors` |
| دسترسی درب | `door_user_access` | `/api/baseinfo/door_user_access` |
| نوع ورود و خروج | `entry_exit_types` | `/api/baseinfo/entry_exit_types` |

### کالا و سرویس

| فرم | جدول | API |
|-----|------|-----|
| مقصد کالا | `goods_destinations` | `/api/baseinfo/goods_destinations` |
| سرویس | `services` | `/api/lookups/services` |
| شرکت/مشتری | `client_companies` | `/api/baseinfo/client_companies` |

### کالاها

| فرم | جدول | فیلدها | نمونه |
|-----|------|--------|-------|
| انواع ورود و خروج کالا | `goods_entry_exit_types` | نام | امانی، خدمات، تعمیری، تعویضی، خروجی |
| تعریف کالا و محصولات | `goods_products` | مرکز، بارکد، نام، نوع، واحد شمارش، سریال، مشخصات، فعال | پرینتر، اسکنر |

### خودروها

| فرم | جدول | فیلدهای اصلی | نمونه |
|-----|------|----------------|-------|
| نوع خودروها | `vehicle_types` | نام | سواری، وانت، … |
| تعریف خودروها | `vehicles` | پلاک ایران، نوع، رنگ، مرکز، راننده، مالکیت | `۱۲ ب ۳۴۵ - ۱۱` |
| خودروهای باری | `cargo_vehicles` | پلاک، نوع، راننده، وزن | `۹۸ ص ۶۵۴ - ۱۶` |
| علت تردد باری | `cargo_traffic_reasons` | علت، ورود/خروج | حمل کالا |

CRUD عمومی موجودیت‌ها:

`GET/POST /api/baseinfo/{table}` ، `PUT/DELETE /api/baseinfo/{table}/{id}`

جداول در `BASEINFO_ENTITY_TABLES` و `ALL_ENTITY_TABLES`.

---

## ۶. پلاک ملی ایران

فرمت ذخیره: **`۱۲ ب ۳۴۵ - ۱۱`** (دو رقم + حرف + سه رقم + کد منطقه)

- UI: کامپوننت `IranPlateInput` (بخش‌های جدا + لیست حروف فارسی + SVG ایران)
- بک‌اند: `normalize_iran_plate()` روی POST/PUT جداول `vehicles` و `cargo_vehicles`
- حروف: الف، ب، پ، … ی (`IRAN_PLATE_LETTERS`)

---



## انتظامات عملیاتی (نسخه ۳۹)

علاوه بر تعاریف پایه، فرم‌های عملیاتی PDF دژبان-انتظامات:

| فرم | جدول | نمونه تست |
|-----|------|-----------|
| لوح نگهبانی | `ent_guard_board` | شیفت صبح ۱۴۰۵/۰۷/۱۵ |
| ثبت وقایع شیفت | `ent_shift_events` | بازرسی دوره‌ای |
| برنامه نوبتکاری | `ent_shift_schedule` | امیر رضایی / نوبت A |
| تجهیزات الکترونیک پرسنل | `ent_personnel_electronics` | بی‌سیم WR-100 |
| درخواست جایگزینی | `ent_replacement_requests` | در انتظار |
| صدور مجوز | `ent_permits` | تردد ویژه |
| وقایع/مسئولین مانیتورینگ | `ent_monitoring_*` | اپراتور |
| گزارش نگهبانی / ارجاع / خبر | `ent_guard_reports` و … | گزارش روزانه |
| رول‌کال | `ent_roll_call` | مرخصی |
| لوح اجمالی / وقایع نگهبانی | `ent_guard_board_summary` و … | خلاصه شیفت |
| محل استقرار | `ent_deployment_locations` | LOC-01 ورودی اصلی |
| وقایع افسر | `ent_officer_events` | تحویل شیفت |

همه از `/api/baseinfo/{table}` و `ENTEZAMAT_ENTITY_TABLES`؛ حداقل یک رکورد نمونه در seed.

## صدور کارت (نسخه ۴۳)

برگه مستقل **صدور کارت** بر اساس PDF دژبان-صدور کارت:

| فرم | جدول | نمونه تست |
|-----|------|-----------|
| چاپ کارت پرسنل | `card_personnel` | Fname1 / Lname1 / کد ۲۰۰۸ |
| چاپ کارت پیمانکاران | `card_contractor` | صالح رضوانی / شرکت پیمانکار |
| گزارش کارت‌های صادر شده | همان `card_personnel` (فقط‌خواندنی) | — |
| چاپ کارت خودروی پرسنل | `card_vehicle_personnel` | ۱۲ ب ۳۴۵ - ۱۱ |
| چاپ کارت خودروی پیمانکاران | `card_vehicle_contractor` | ۹۸ ص ۶۵۴ - ۱۶ |
| گزارش کارت‌های خودروی صادر شده | همان `card_vehicle_personnel` (فقط‌خواندنی) | — |

جداول در `CARD_ENTITY_TABLES` و `ALL_ENTITY_TABLES`؛ CRUD از `/api/baseinfo/{table}`؛ seed نمونه در `seed_demo_records`.


## کارتابل (نسخه ۴۸)

برگه **کارتابل** بر اساس PDF دژبان-کارتابل:

| فرم | جدول | توضیح |
|-----|------|------|
| نامه‌های صادره | `krt_outgoing` | شماره، موضوع، تاریخ، دبیرخانه، متن، گیرندگان |
| نامه‌های وارده | `krt_inbox` | + فرستنده، وضعیت، پوشه |
| مدیریت کارتابل | `krt_management` | وضعیت مشاهده/ارسال/بایگانی |
| پوشه‌های بایگانی | `krt_folders` | تعریف پوشه |

## مناقصات و مزایدات (نسخه ۴۷)

| فرم | جدول |
|-----|------|
| شرکت‌های حاضر | `tnd_companies` |
| مناقصات | `tnd_tenders` |
| مزایده | `tnd_auctions` |
| قراردادها | `tnd_contracts` |


## جریان کار (نسخه ۵۲)

| فرم | جدول |
|-----|------|
| انواع درخواست | `wf_request_types` |
| تاییدکننده درخواست | `wf_approvers` |
| تفویض اختیار | `wf_delegation` |
| تاییدات پارکینگ و خروج مدارک | `wf_parking_docs` |

## پشتیبان‌گیری (نسخه ۵۲)

- `POST /api/admin/backup` — ایجاد کپی از `dejban.db` در `data/backups/`
- `GET /api/admin/backups` — فهرست
- `POST /api/admin/restore?name=` — بازیابی از فایل سرور
- `POST /api/admin/restore-upload` — بازیابی از آپلود کاربر
- قبل از هر بازیابی یک فایل `pre_restore_*` ذخیره می‌شود

## ۷. انتظامات

فقط تعاریف مرجع:

| فرم | جدول |
|-----|------|
| تعریف گروه | `ent_groups` |
| مراکز حفاظتی و نگهبانی | `ent_protection_centers` |
| اماکن حفاظتی و نگهبانی | `ent_protection_places` |
| ساعت‌های شیفت | `ent_shift_hours` (نام + **ساعت شروع/پایان** فارسی مثل ۰۷:۰۰) |
| مسئول و جانشین شیفت | `ent_shift_leaders` |
| نوبت کار | `ent_work_shifts` |
| وضعیت پرسنل انتظامات | `ent_staff_status` |
| تجهیزات نگهبانی | `ent_guard_equipment` |

جداول در `ENTEZAMAT_ENTITY_TABLES`. بارگذاری UI: `loadLookup(view, 'entezamat')`.

---

## ۸. پرسنل

- تب مستقل؛ «تعریف پرسنل» داخل اطلاعات پایه **نیست**
- فیلدها: `PERSONAL_FIELDS` + migrate با `ALTER`
- عکس/امضا: پایدار در DB + پوشه مدارک؛ ویرایش با GET کامل و PUT با `exclude_unset`
- وابستگان: `dependents` — `/api/dependents`
- کارت: `access_cards` — `/api/cards`
- مرکز/واحد/رشته/گروه/استخدام از select اطلاعات پایه

---

## ۹. نقشه وابستگی فیلدها (خلاصه)

| فیلد در فرم‌ها | منبع | API نمونه |
|----------------|------|-----------|
| مرکز / واحد | تعریف واحدها | `/api/units` |
| رشته تحصیلی | رشته تحصیلی | `/api/lookups/education_fields` |
| گروه مسئولیت | گروه مسئولیت | `/api/lookups/responsibility_groups` |
| نوع استخدام | انواع استخدام | `/api/lookups/employment_types` |
| نوع خودرو | نوع خودروها | `/api/baseinfo/vehicle_types` |
| نوع ورود/خروج کالا | انواع ورود و خروج کالا | `/api/baseinfo/goods_entry_exit_types` |
| درب / مقصد کالا / مشتری / … | همان فرم اطلاعات پایه | `/api/baseinfo/...` |

---

## ۱۰. فایل‌های کلیدی

| مسیر | نقش |
|------|-----|
| `backend/database.py` | schema، seed، ایندکس، CRUD |
| `backend/main.py` | مسیرهای FastAPI |
| `frontend/src/App.jsx` | ریبون، فرم‌ها، IMPLEMENTED_ACTIONS |
| `docs/ARCHITECTURE.md` | این سند |
| `README.md` | راهنمای اجرا و تاریخچه نسخه‌ها |

---

## ۱۱. تاریخچه مختصر نسخه‌ها

| نسخه | خلاصه |
|------|--------|
| ۲۶ | دیتابیس متمرکز |
| ۲۷–۲۸ | seed همه فرم‌ها + ایندکس بهینه |
| ۲۹ | پرسنل فقط در تب مستقل |
| ۳۰–۳۲ | انتظامات + بارگذاری UI |
| ۳۳–۳۶ | خودروها + پلاک ایران ترکیبی |
| ۳۷ | فریم کالاها |
| ۳۸ | یکدست‌سازی مستندات |


## گزارشات (نسخه ۴۱)

`GET /api/reports` — فهرست کلیدها  
`GET /api/reports/{key}` — اجرای گزارش → `{ title, columns, rows, count }`

| کلید | عنوان | منبع داده |
|------|--------|-----------|
| guest | گزارشات میهمان | `guest_visits` |
| personnel_traffic | تردد پرسنل و پیمانکاران | `personnel_traffic` |
| vehicle_traffic | تردد خودرو پرسنل/پیمانکار | `vehicle_traffic` |
| goods_io | ورود و خروج کالا | `goods_traffic` |
| goods_repair | کالای تعمیری و خدمات | `goods_traffic` (تعمیری) |
| personnel | گزارش پرسنل | `personnel` |
| contractor_personnel | پرسنل پیمانکار | `personnel_traffic` |
| cargo_vehicle | تردد خودرو باری | `cargo_vehicles` |
| guard_board | لوح نگهبانی | `ent_guard_board` |
| replacement | درخواست جایگزینی | `ent_replacement_requests` |
| misc_traffic | تردد افراد متفرقه | `misc_person_traffic` |
| system_log | گزارش لاگ | `system_logs` |
| contractor_goods | کالای پیمانکار | `goods_traffic` |
| traffic_request | درخواست تردد | `traffic_requests` |
| guest_reserve | رزرو میهمان | `guest_reservations` |
| personnel_history | تاریخچه پرسنل | `personnel` |
| goods_reserve | رزرو کالا | `goods_reservations` |

تعاریف در `REPORT_DEFS` / `run_report()` در `database.py`.



## فیلدهای مرجع مشترک در همه فرم‌ها (نسخه ۴۲)

در تمام فرم‌های اطلاعات پایه و انتظامات، این سه فیلد **فقط از select** پر می‌شوند:

| فیلد | منبع | API |
|------|------|-----|
| `center_name` (مرکز) | تعریف واحدها → نام‌های مرکز یکتا | `/api/units` |
| `shift_name` (نام شیفت) | تعریف ساعت‌های شیفت | `/api/baseinfo/ent_shift_hours` |
| `work_shift` (نوبت کار) | تعریف نوبت کار | `/api/baseinfo/ent_work_shifts` |

پیاده‌سازی UI: `optionsForField` / `loadShiftRefs` در `App.jsx`.



## سطوح دسترسی سیستم (نسخه ۵۵)

| جدول | نقش |
|------|-----|
| `sys_access_levels` | نام سطح، توضیحات، `is_full_admin` |
| `sys_access_level_tabs` | برگه‌های مجاز هر سطح |
| `sys_access_level_actions` | کدهای ریبون مجاز هر سطح |
| `sys_users` | کاربران سیستم + `access_level_id` |

API:
- `GET/POST /api/admin/access-levels` ، `PUT/DELETE /api/admin/access-levels/{id}`
- `GET/POST /api/admin/users` ، `PUT/DELETE /api/admin/users/{id}`
- `GET /api/admin/users/{id}/permissions`

در UI: مدیریت سیستم → تعریف سطح دسترسی / تعریف کاربران
