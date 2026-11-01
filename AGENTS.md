# AGENTS.md — راهنمای عامل‌های هوش مصنوعی برای مخزن Net_Scan

این فایل راهنمای کار برای عامل‌های کدنویسی (AI Coding Agents) در این مخزن است.
هدف: هر عامل/دستیار بتواند بدون حدس‌زدن، پروژه را بسازد، تست کند و تغییرات را
مطابق قراردادهای موجود کامیت کند.

## ۱) شناسنامه پروژه

- **نام:** Net_Scan (اسکنر مجاز IPv4 و مدیریت دستگاه‌های MikroTik شبکه)
- **معماری:** بک‌اند FastAPI (پورت 8001) + فرانت‌اند React/Vite (توسعه: پورت 5001)
- **زبان رابط کاربری:** فارسی، راست‌به‌چپ (RTL) — همه متن‌های UI، پیام‌های خطا و
  سرستون‌های خروجی‌ها باید فارسی باشند.
- **دیتابیس:** SQLite استاندارد پایتون (بدون ORM) — کاتالوگ چنددیتابیسی در
  `databases/catalog.json`، فایل‌های دیتابیس در `databases/*.db` و فایل‌های
  جزئیات هر دستگاه در `databases/ip_info/{ip}.txt`.

## ۲) نقشه مسیرهای کلیدی

| مسیر | نقش |
| --- | --- |
| `backend/main.py` | همه endpointها (FastAPI)، احراز هویت کوکی HMAC، مدیریت jobها |
| `backend/db.py` | لایه دیتابیس: کاتالوگ، جدول devices، خروجی‌ها، backup، enrich از ip_info |
| `backend/routeros_api.py` | خواندن مستقیم از RouterOS API (probe موازی، collect، push-config) |
| `backend/route_topology.py` | توپولوژی مسیر: خواندن ساختاریافته API + گراف لینک‌ها + BFS تا روتر مرکزی |
| `backend/route_pdf.py` | تولید PDF «Detailed Router Path Topology» (یک صفحه به ازای هر دستگاه) |
| `backend/snmp_manager.py` | خواندن identity از طریق SNMP |
| `frontend/src.jsx` | کل رابط کاربری در «یک فایل» (React + JSX، بدون فایل‌های کامپوننت جدا) |
| `frontend/style.css` | استایل‌ها (RTL، تم تیره) |
| `frontend/dist/` | build تولیدی — **کامیت می‌شود** و FastAPI آن را روی `/` سرو می‌کند |
| `tests/` | تست‌های واحد بدون شبکه (`python -m unittest discover -s tests`) |
| `scripts/` | اسکریپت‌های تست E2E — **در .gitignore است**؛ برای کامیت: `git add -f scripts/<file>.py` |
| `worklog.md` | دفتر کار: برای هر تغییر یک `Task ID` جدید (عدد ترتیبی) اضافه کنید |
| `Lib/`, `lib/`, `Scripts/` | venv کامیت‌شده در مخزن — **به آن دست نزنید** (بدهی تاریخی مخزن) |

## ۳) اجرا، تست و build

```sh
# بک‌اند (از ریشه، با پایتون محیط مجازی):
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001
# ورود پیش‌فرض UI: admin / NetAdmin (تغییرش دهید!)

# تست‌های واحد:
python -m unittest discover -s tests

# تست‌های E2E در scripts/ (نمونه):
python scripts/test_export_mikrotik_csv.py
python scripts/test_api_probe_progress.py
python scripts/test_json_export_route_report.py
python scripts/test_route_topology_unit.py
python scripts/test_route_topology_pdf.py
python scripts/test_device_picker.py

# build فرانت‌اند — بعد از هر تغییر در src.jsx یا style.css الزامی است:
cd frontend && npm install && npm run build
```

- تست E2E الگوی ثابت دارد: `FastAPI TestClient` + دیتابیس موقت با
  `db.create_database()`/`delete_database()` + ورود با `POST /api/login`.
- خروجی CSV همیشه با BOM (`\xef\xbb\xbf`) ساخته می‌شود تا در اکسل فارسی درست باز شود.

## ۴) قراردادهای کامیت و کار

1. **worklog.md:** پایان هر کار، یک بخش `Task ID: N` (ادامه عدد قبلی) با عنوان،
   شرح تغییرات و «Stage Summary» بنویسید.
2. **scripts/ گیت‌ایگنورد است:** فایل‌های تست جدید را با `git add -f` اضافه کنید.
3. **frontend/dist را همیشه همراه تغییر frontend کامیت کنید** (کاربر مستقیم dist را سرو می‌کند).
4. تغییرات venv (`Lib/`, `lib/`, `Scripts/`) را در کامیت‌های منطقی خودتان نقطه‌گذاری نکنید؛
   در صورت ظاهرشدن در `git status` آنها را کنار بگذارید مگر اینکه کامیت هدفش باشد.
5. پیام کامیت: قالب `type(scope): خلاصه انگلیسی` (مثل `feat(devices): ...`، `fix(api): ...`).
6. قبل از کامیت: تست‌ها سبز باشند؛ `git status` را برای فایل‌های ناخواسته چک کنید.

## ۵) نقشه قابلیت‌ها (تا Task 15)

- **اسکن شبکه:** `POST /scans/start` (قابل لغو با `/scans/{id}/cancel`)، ورودی IP/CIDR/بازه،
  پورت‌های 8291 و 8728 همیشه اضافه می‌شوند.
- **دیتابیس چندگانه:** CRUD کاتالوگ، دیتابیس «فعال»، انتقال/ادغام/حذف تکراری‌ها، backup/restore.
- **خواندن اطلاعات دستگاه‌ها:**
  - `POST /api/snmp/probe` — identity از SNMP؛ پیشرفت: `/api/snmp/probe/progress`؛ توقف: `/cancel`.
  - `POST /api/devices/probe-api` — خواندن کامل با RouterOS API (identity، اینترفیس‌ها،
    آدرس‌های IP، همسایه‌ها، وایرلس، لاگ، MAC) **موازی با Thread Pool** (`max_workers`،
    پیش‌فرض 6)؛ پیشرفت زنده: `GET /api/devices/probe-api/progress` (ok/failed/remaining)؛
    توقف مشارکتی با `Event`.
  - ذخیره‌سازی مشترک در `_persist_api_probe_results()` → دیتابیس + `databases/ip_info/{ip}.txt`.
- **خروجی CSV میکروتیک:** `POST /devices/export-mikrotik.csv` — فقط دستگاه‌های میکروتیکِ
  انتخاب‌شده، ۱۹ ستون فارسی، با `read_missing=true` دستگاه‌های بدونِ اطلاعاتِ کامل قبل از
  خروجی زنده خوانده می‌شوند (با همان نمودار پیشرفت) و ستون «وضعیت خواندن» completeness
  هر ردیف را نشان می‌دهد (کامل / ناقص).
- **خروجی JSON میکروتیک:** `POST /devices/export-mikrotik.json` — دقیقاً همان دستگاه‌ها و
  همان ۱۹ فیلد فارسی (کلیدها = سرستون‌های CSV، مرجع مشترک: `db.MIKROTIK_EXPORT_FIELDS` و
  `db.mikrotik_selected_rows()`) + متادیتا (exported_at/database/count/fields)؛
  خواندن خودکارِ مواردِ ناقص مشترک با CSV در `_live_read_missing_devices()`.
- **گزارش روت:** `POST /devices/route-report.csv` (ماژول `backend/route_report.py`) —
  اجرای `tracert -d <IP>` برای تمام دستگاه‌های میکروتیکِ درخواست (لینوکس: `traceroute -n`،
  معادلِ `-d`)، موازی با ThreadPool؛ مبدأ/مقصد از کاربر (پیش‌فرض هر دو 172.19.1.6)؛
  اگر مبدأ≠مقصد مسیر مبدأ→مقصد هم ردیابی و به ابتدای گزارش می‌آید؛ خروجی CSV با
  BOM و ۷ ستون فارسی (IP مبدأ، IP مقصد، نام دستگاه، شماره مرحله، IP مرحله، تاخیر، وضعیت).
- **انتخاب دستگاه‌ها از دیتابیس (Device Picker):** مودال جستجو/فیلتر/انتخاب چندگانه در
  بخش «گزارش مسیر تا روتر مرکزی» تب گزارش هوشمند (`DevicePickerModal` در src.jsx +
  CSS `device-picker-*` در style.css). فهرست دستگاه‌ها از `GET /devices?database=<name>`
  (پارامتر جدید؛ نام اعتبارسنجی و ۴۰۴ برای نام ناشناخته) می‌آید؛ فیلترهای کلاینت‌ساید:
  جستجوی آزاد (IP/نام/تگ/نوع/دسته)، «فقط میکروتیک» (همان قاعدهٔ `_is_mikrotik_device`)،
  «فقط پینگ‌خورده»؛ نمایش حداکثر ۳۰۰ ردیف با شمارنده، سقف انتخاب ۲۰۰ دستگاه
  (سپس `max_devices=Math.min(200,max(80,len))` به start ارسال می‌شود)؛ بدون انتخاب =
  رفتار قبلی (کل میکروتیک‌های دیتابیس، حداکثر ۸۰). تغییر دیتابیس، انتخاب را پاک می‌کند.
- **گزارش مسیر تا روتر مرکزی (توپولوژی PDF):** `POST /api/reports/route-topology/start`
  + `/progress` + `/cancel` + `/result.pdf` (ماژول‌های `backend/route_topology.py` و
  `backend/route_pdf.py`) — با نام کاربری/رمز RouterOS API که کاربر وارد می‌کند به تمام
  دستگاه‌های میکروتیک دیتابیس انتخابی (یا انتخاب صریح `ips`) وصل می‌شود، اینترفیس‌ها /
  آدرس‌های IP / همسایه‌ها (MNDP) / روت‌ها را می‌خواند، گراف لینک‌ها را می‌سازد
  (همسایگی MNDP + اشتراک ساب‌نت + گیت‌وی روت به IP مرکزی)، کوتاه‌ترین مسیر هر دستگاه تا
  «روتر مرکزی» (پیش‌فرض 172.19.1.6، ورودی کاربر) را با BFS حساب می‌کند و در هر گام
  مشخص می‌کند کدام اینترفیس دستگاه A به کدام اینترفیس دستگاه B وصل است؛ خروجی یک PDF
  انگلیسی‌زبان (مثل نمونه Detailed Router Path Topology) با یک صفحه به ازای هر دستگاه؛
  دستگاه‌های قطع هم صفحهٔ «CONNECTION FAILED» با اطلاعات دیتابیس دارند. الگوی اجرا
  مثل probe: Thread پس‌زمینه + progress زنده + توقف مشارکتی؛ هم‌زمان فقط یک گزارش.
  **مالک فلگ `running` فقط worker گزارش است** — `collect_topology_info_many` نباید
  `running` را بنویسد (باگ Task 15: گزارش در فاز graph/pdf «تمام‌شده» دیده می‌شد و
  فرانت‌اند polling را زودتر قطع می‌کرد).
- **سایر:** گزارش‌های هوشمند، Winbox tools، مدیریت VPN، ایمیل/اطلاع‌رسانی.

## ۶) نکات دام‌دار (Gotchas)

- `frontend/src.jsx` فایل بزرگِ تک‌فایلی است — برای ویرایش، بخش مربوطه را با grep پیدا کنید،
  کل فایل را بازنویسی نکنید.
- شماره ستون‌های خروجی CSV ممکن است تغییر کند؛ تست‌ها با `csv.reader` پارس کنید نه
  `splitlines` (فیلدهای چندخطی مثل لاگ می‌شکنند).
- `delete_database` فقط فایل `.db` را حذف می‌کند؛ فایل‌های `databases/ip_info/*.txt` مشترک
  بین دیتابیس‌ها هستند و باقی می‌مانند — در تست‌ها این را در نظر بگیرید.
- `enrich_devices_from_ip_info` فقط فیلدهای «خالی» را از txt پر می‌کند و هرگز مقدار
  دیتابیس را بازنویسی نمی‌کند.
- اعتبارنامه‌های RouterOS (user/pass) هرگز در کد/کامیت هاردکد نشوند؛ از ورودی کاربر یا
  تنظیمات بگیرید.
- `reportlab` برای PDF لازم است (در requirements.txt)؛ متن PDF با فونت core Helvetica است
  پس فقط نویسه‌های Latin-1 — متن فارسی/عربی قبل از رسم باید پاکسازی شود (`route_pdf._san`).
- شمارش صفحات PDF در تست‌ها: `len(re.findall(rb"/Type\\s*/Page[^s]", content))` —
  شمارش سادهٔ `/Type /Page` گرهٔ `/Pages` را هم می‌شمارد.

## ۷) امنیت

- مخزن عمومی است: هر داده‌ای با IP/تگ/نام واقعی شبکه (مثل فایل‌های runtime
  `databases/`، `ip_info/`، `.vpn_runtime/`) نباید به کامیت‌های جدید اضافه شود.
- توکن/رمز در URL ریموت، لاگ یا خروجی تست قرار نگیرد.
- این ابزار فقط برای شبکه‌هایی با مجوز صریح است؛ اسکن بدون اجازه ممنوع.
