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
| `backend/cisco_config.py` | پارس کانفیگ متنی روتر مرکزی سیسکو (اینترفیس‌ها/آدرس‌ها/روت استاتیک) برای گزارش مسیر |
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
python scripts/test_push_config_progress.py
python scripts/test_push_config_failed_csv.py
python scripts/test_push_verification.py
python scripts/test_cisco_config.py
python scripts/test_route_unreachable_csv.py

# build فرانت‌اند — بعد از هر تغییر در src.jsx یا style.css الزامی است:
cd frontend && npm install && npm run build
```

- تست E2E الگوی ثابت دارد: `FastAPI TestClient` + دیتابیس موقت با
  `db.create_database()`/`delete_database()` + ورود با `POST /api/login`.
- خروجی CSV همیشه با BOM (`\xef\xbb\xbf`) ساخته می‌شود تا در اکسل فارسی درست باز شود.
- نام همهٔ فایل‌های CSV خروجی با مهر تاریخ/ساعت جاری سیستم پایان می‌یابد — `file_stamp()`
  در `backend/main.py` با الگوی `{name}_YYYYMMDD_HHMMSS.csv` (Task 22)؛ فرانت نام را از
  `Content-Disposition` می‌خواند و fallback آن هم `csvStamp()` با همان الگو است.
  تست نام/تازگی مهر: `scripts/test_csv_filename_stamp.py` و `tests/test_csv_stamp.py`.

## ۴) قراردادهای کامیت و کار

1. **worklog.md:** پایان هر کار، یک بخش `Task ID: N` (ادامه عدد قبلی) با عنوان،
   شرح تغییرات و «Stage Summary» بنویسید.
2. **scripts/ گیت‌ایگنورد است:** فایل‌های تست جدید را با `git add -f` اضافه کنید.
3. **frontend/dist را همیشه همراه تغییر frontend کامیت کنید** (کاربر مستقیم dist را سرو می‌کند).
4. تغییرات venv (`Lib/`, `lib/`, `Scripts/`) را در کامیت‌های منطقی خودتان نقطه‌گذاری نکنید؛
   در صورت ظاهرشدن در `git status` آنها را کنار بگذارید مگر اینکه کامیت هدفش باشد.
5. پیام کامیت: قالب `type(scope): خلاصه انگلیسی` (مثل `feat(devices): ...`، `fix(api): ...`).
6. قبل از کامیت: تست‌ها سبز باشند؛ `git status` را برای فایل‌های ناخواسته چک کنید.

## ۵) نقشه قابلیت‌ها (تا Task 28)

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
- **انتخاب همه فیلترشده‌ها:** دکمهٔ «انتخاب همه فیلترشده‌ها (N)» در نوار ابزار برگهٔ مدیریت دستگاه‌ها
  (`selectAllFiltered` در src.jsx) — با همان فیلترهای جاری (`params` بدون offset و
  `limit=100000`) همهٔ نتایج را می‌گیرد و در `selected` علامت می‌زند؛ یعنی انتخاب بین
  صفحات (چک‌باکس هدر جدول فقط ردیف‌های صفحهٔ جاری را انتخاب می‌کند). کاربردها: کانفیگ
  گروهی، خروجی‌ها، حذف گروهی.
- **انتقال کانفیگ گروهی با نمودار پیشرفت زنده:** `POST /api/devices/push-config/start`
  + `/progress` + `/cancel` + `GET /api/devices/push-config/failed-csv` (موازی با
  `push_config_many_parallel`، پیش‌فرض ۶ رشته تا ۱۶،
  توقف مشارکتی با `CFG_PUSH_CANCEL`؛ مالک فلگ running فقط worker است). دو مسیر UI:
  «انتقال کانفیگ» (کانفیگ کادر SNMP + prompt یوزر/رمز) و «کانفیگ گروهی» (پنل با متن
  دستورات). نمودار (`cfgProg` در src.jsx + CSS `cfg-*`): نوار درصد سه‌بخشی سبز/قرمز/خاکستری،
  شمارنده‌ها، IP جاری، شبکهٔ خانه‌های per-device و جدول «جزئیات نتایج» با علتِ فارسیِ هر خطا
  (`classify_push_error` در routeros_api.py — timeout/refused/credentials/…). دکمهٔ
  «تلاش مجدد فقط ناموفق‌ها» با `cfgLast` (آخرین ips/user/pass/script) دوباره اجرا می‌کند.
  **گزارش CSV ناموفق‌ها (Task 19):** دکمهٔ «گزارش CSV ناموفق‌ها» در سرستون نمودار پس از
  پایان اجرا (فقط وقتی خطا > 0) فایل `config_failed_{زمان}.csv` را از
  `GET /api/devices/push-config/failed-csv` می‌دهد — از `CFG_PUSH_STATE["results"]` آخرین
  اجرا فقط ردیف‌های ناموفق (شامل متوقف‌شده‌ها با برچسب «متوقف شد») با غنی‌سازی نام/نوع/تگ
  از دیتابیس فعال، ستون علت فارسی، جزئیات خطای خام و ستون «زمان پایان اجرا»
  (خوانده‌شده از `CFG_PUSH_STATE["finished_at"]` که worker در `finally` پر می‌کند)؛
  CSV با BOM؛ بدون مورد ناموفق یا بدون اجرا → 404 با پیام فارسی.
  **تأیید پس از اعمال (Task 20 — رفع موفقِ کاذب):** «موفق» فقط با تأییدِ نتیجه است.
  اسکریپت‌های کنسولی داخل `:do {...} on-error={:set NetScanPushXXXX "failed"}` پیچیده و
  وضعیت از `/system/script/environment` خوانده می‌شود (خطای داخل اسکریپت دیگر نامرئی نیست؛
  `/system/script/run` به‌محض شروع job برمی‌گردد — همان منبع قبلیِ موفقِ کاذب؛ سقف انتظار:
  `RouterOSClient.PUSH_STATUS_TIMEOUT=30s`). سپس `verify_push` تغییر وعده‌داده‌شده را
  دوباره می‌خواند: کاربر (login دوباره با نام/رمز)، identity، snmp enabled، سرویس IP؛
  عدمِ تطبیق → نتیجهٔ «ناموفق» با علت «کانفیگ اجرا شد اما تأیید اعمال نشد: …» و فیلد
  `verified=False` (ستون «تأیید اعمال» در جدول نتایج با نشان سبز/قرمز). `_parse_terminal_line`
  خروجی `(sentence, path_def)` دارد (خطوط ادامه‌دار مثل `/snmp community` + `set …`) و
  «[find …]» روی فعل‌های تغییردهنده را به مسیر کنسول می‌فرستد (در API فقط روی print مجاز است).
  تست: `scripts/test_push_verification.py` (فیکِ talk/connect/close + چالش MD5).
- **گزارش مسیر تا روتر مرکزی (توپولوژی PDF):** `POST /api/reports/route-topology/start`
  + `/progress` + `/cancel` + `/result.pdf` (ماژول‌های `backend/route_topology.py` و
  `backend/route_pdf.py`) — با نام کاربری/رمز RouterOS API که کاربر وارد می‌کند به تمام
  دستگاه‌های میکروتیک دیتابیس انتخابی (یا انتخاب صریح `ips`) وصل می‌شود، اینترفیس‌ها /
  آدرس‌های IP / همسایه‌ها (MNDP) / روت‌ها را می‌خواند، گراف لینک‌ها را می‌سازد
  (همسایگی MNDP + اشتراک ساب‌نت + یال‌های روتینگ «طولانی‌ترین پیشوند/روت پیش‌فرض»)،
  کوتاه‌ترین مسیر هر دستگاه تا
  «روتر مرکزی» (پیش‌فرض 172.19.1.6، ورودی کاربر) را با BFS حساب می‌کند و در هر گام
  مشخص می‌کند کدام اینترفیس دستگاه A به کدام اینترفیس دستگاه B وصل است؛ خروجی یک PDF
  انگلیسی‌زبان (مثل نمونه Detailed Router Path Topology) با یک صفحه به ازای هر دستگاه؛
  دستگاه‌های قطع هم صفحهٔ «CONNECTION FAILED» با اطلاعات دیتابیس دارند. الگوی اجرا
  مثل probe: Thread پس‌زمینه + progress زنده + توقف مشارکتی؛ هم‌زمان فقط یک گزارش.
  **مالک فلگ `running` فقط worker گزارش است** — `collect_topology_info_many` نباید
  `running` را بنویسد (باگ Task 15: گزارش در فاز graph/pdf «تمام‌شده» دیده می‌شد و
  فرانت‌اند polling را زودتر قطع می‌کرد).
- **یافتن مسیر با روت پیش‌فرض (Task 17):** `_route_next_hops()` — اول طولانی‌ترین
  پیشوندِ منطبق با IP مرکزی (در همان طول، کم‌ترین distance + ECMP)، وگرنه روت پیش‌فرض
  0.0.0.0/0 با کم‌ترین distance (hop بالای دستگاه). یال‌های روتینگ (بخش 3-ج در
  `build_topology`) حتی وقتی روتر مرکزی خودش خوانده شده هم ساخته می‌شوند؛ گیت‌وی
  می‌تواند به core (یال مستقیم)، به دستگاه خوانده‌شدهٔ دیگر (زنجیرهٔ بالادست) یا به
  گرهٔ شبحِ `g:<ip>` با فلگ `upstream` (hop ناشناخته) برسد. اولویت شواهد
  (از Task 18): mndp > cisco > subnet > route > default. دستگاه‌های unreachable یک «زنجیرهٔ بالادست
  best-effort» (حداکثر ۶ گام، مقاوم به حلقه) در `path["upstream"]` می‌گیرند که PDF
  آن را با باکس‌های کهربایی ترسیم می‌کند؛ آمار `summary["upstream_only"]` شمارش می‌شود.
  روتر مرکزی خودش در بخش 3-ج پردازش نمی‌شود (بالادستِ آن در مسیر «تا مرکز» بی‌اثر است).
- **بارگذاری کانفیگ روتر مرکزی سیسکو (Task 18):** چون روتر مرکزی شبکه سیسکو است و از
  RouterOS API خوانده نمی‌شود، کاربر خروجی `show running-config` آن را به‌صورت فایل متنی
  در تب گزارش هوشمند بارگذاری می‌کند: `POST /api/reports/route-topology/cisco-config`
  (multipart با فیلد `file` یا JSON با فیلد `text`؛ حداکثر ۲MB؛ با `looks_like_cisco_config`
  اعتبارسنجی و خطای ۴۰۰ فارسی) + `GET` (خلاصهٔ پارس‌شده) + `DELETE`. فایل در
  `databases/cisco_central_config.txt` ذخیره می‌شود (دایمی، بین اجراها).
  ماژول `backend/cisco_config.py` کانفیگ IOS را پارس می‌کند: اینترفیس‌ها (فیزیکی/
  زیراینترفیس dot1Q/SVI/Loopback با description و shutdown)، آدرس‌های IP اصلی و
  secondary، روت‌های استاتیک (vrf/گیت‌وی IP یا اینترفیس/distance/name) و ساب‌نت‌های
  connected. در `build_topology(..., cisco=پارس‌شده)`: گرهٔ core (وقتی روتر مرکزی بین
  دستگاه‌ها نباشد) با hostname/آدرس‌ها/اینترفیس‌های سیسکو غنی‌سازی می‌شود، یال‌های
  روت استاتیک سیسکو (گیت‌ویِ هر روت → دستگاه دارای آن IP یا گرهٔ شبح) با شاهد `cisco`
  ساخته می‌شوند و گیت‌وی دستگاه‌ها اگر روی خودِ سیسکو باشد به core وصل می‌شود.
  اولویت شواهد جدید: mndp > cisco > subnet > route > default. در PDF: هدر
  «Core Router: <hostname> (<ip>)»، برچسب CISCO-ROUTE، ستون «Cisco static route» و
  خطوط شواهد `cisco <hostname>: route <prefix> via <nh>` (از `_cisco_evidence_lines`،
  همهٔ آدرس‌های دستگاه بررسی می‌شوند). هدر `X-Topology-Cisco` در result.pdf نام
  hostname را برمی‌گرداند. اینترفیسِ سمتِ دستگاه برای گیت‌وی‌های off-link از ARP خوانده
  می‌شود (`_arp_iface_toward`).
- **بررسی همهٔ اینترفیس‌ها/IPها + گزارش CSV دلایل نرسیدن (Task 21):** هر روتر چند IP روی
  اینترفیس‌های مختلف دارد؛ در یافتن مسیر «تمام» روت‌های پوشش‌دهندهٔ IP مرکزی چک می‌شوند:
  `_route_all_next_hops()` گیت‌وی‌های همهٔ روت‌های پوشش‌دهنده (روت خاص هر اینترفیس،
  روت‌های جایگزین با distance بدتر، روت پیش‌فرض) را مرتب‌شده (پیشوند بلندتر ← distance
  کمتر) و بدون تکرار برمی‌گرداند و بخش 3-ج و `_upstream_chain` همه را امتحان می‌کنند
  (اولین گیت‌وی که به دستگاه شناخته‌شده یا core برسد انتخاب می‌شود؛ گیت‌وی اینترفیسی مثل
  "ether5" قابل دنبال‌کردن نیست و حذف می‌شود). زنجیرهٔ بالادست در `path["upstream_end"]`
  دلیلِ پایان را ثبت می‌کند (core/ghost/loop/max/no-route). تحلیل دلیل هر دستگاه
  unreachable: `route_topology.unreachable_reason_rows(topo)` — وضعیت (نمی‌رسد/خوانده
  نشد/متوقف شد)، بررسی تک‌تک IPها با `interface_route_verdicts()` (verdict
  direct/route/default/none + وضعیت اینترفیس disabled/no-link + دیده‌شدن گیت‌وی در ARP)
  و دلیل اصلی فارسی: جدول روتینگ خالی، بدون روت پوشش‌دهنده، گیت‌وی خارج از ساب‌نتِ همهٔ
  اینترفیس‌ها، اینترفیس خروجی قطع/غیرفعال، پایان زنجیره در گیت‌وی ناشناخته، حلقهٔ
  روتینگ، دستگاه بعدی بدون روت، خوانده‌نشدنِ دستگاه (classify_push_error). خروجی در
  `TOPOLOGY_STATE["unreachable_rows"]` ذخیره و با `GET
  /api/reports/route-topology/unreachable-csv` (۱۲ ستون فارسی، BOM،
  filename=`route_unreachable_{زمان}.csv`، 404/409 فارسی) downloadable است؛ دکمهٔ
  «گزارش CSV دلایل نرسیدن به مرکز» در UI گزارش مسیر + شمارش `unreachable` در
  progress. `_route_next_hops` قدیمی برای سازگاری تست‌ها باقی است.
- **مهر تاریخ/ساعت در نام همهٔ فایل‌های CSV (Task 22):** هر ۸ نقطهٔ تولید CSV
  (`devices/export.csv`، `export-mikrotik.csv`، `route-report.csv`،
  `scans/{id}/reports/{key}`، flaps، wireless، `unreachable-csv`، `failed-csv`)
  نام فایل را با `file_stamp()` (ساعت لوکال سیستم، الگوی `YYYYMMDD_HHMMSS`) می‌سازند تا
  دانلودهای چندباره یکدیگر را بازنویسی نکنند؛ چهار مسیرِ بدون مهر (`devices.csv`،
  `{key}.csv`، `interface_flaps_report.csv`، `wireless_antenna_issues.csv`) مهردار شدند و
  مهر CSVهای قبلاً مهردار از UTC به ساعت سیستم منتقل شد (خروجی‌های غیر CSV مثل
  xlsx/json/pdf/zip/db تغییری نکردند). دانلودرهای فرانتِ flaps و wireless که نام را
  هاردکد بازنویسی می‌کردند حالا از `Content-Disposition` می‌خوانند؛ fallbackهای
  `config_failed`/`mikrotik_selected`/`route_report`/`route_unreachable` هم با
  `csvStamp()` مهر می‌گیرند.
- **کشف hop بالاسری با default روت (Task 23):** روش مسیریابی طبق درخواست کاربر —
  قبل از مسیریابی، نقشهٔ مالکیت IP (فاز صفر در `build_topology`): IP اتصال + همهٔ
  آدرس‌های اینترفیسی هر دستگاه (+ آدرس‌های سیسکوی مرکز) → کلید گره؛ گره‌ها `dev_id`
  (شناسهٔ دیتابیس) دارند. کاندیدهای next-hop در `_route_all_next_hops` حالا
  **default-اول**‌اند: اول default روت‌ها (0.0.0.0/0؛ distance کمتر ← ترتیب جدول) بعد
  روت‌های خاص؛ helper جدید `_route_default_next_hops` فقط defaultها را می‌دهد. BFS
  «آگاه از default روت» است: در هر گره یال سمت گیت‌وی default (`pref_edges`/
  `ordered_adj`) قبل از بقیهٔ یال‌ها امتحان می‌شود تا مسیر گزارش‌شده سلسله‌مراتب
  default را دنبال کند نه میان‌بر ساب‌نت/روت خاص. `_upstream_chain` هم از نقشهٔ
  مالکیت IP استفاده می‌کند. `_route_next_hops` قدیمی (specific-اول) برای سازگاری باقی است.
- **نمودار مسیر داخل کادر صفحه (Task 24):** در PDF گزارش مسیر، هر سطرِ نمودار
  «Shortest Path» ۴ جعبه دارد (۳ hop + دستگاه مبدأ) ولی gap برای ۳ جعبه محاسبه
  می‌شد؛ جعبه‌های انتهای زنجیره (از جمله روتر مرکزی) از صفحه بیرون می‌زدند. حالا
  هندسهٔ سطر با ثابت‌های `PATH_PER_ROW`/`PATH_ROW_BOXES`/`PATH_BOX_W`/
  `PATH_ROW_GAP` در `route_pdf.py` طوری است که هر سطر دقیقاً داخل کادر جا
  می‌شود؛ موقعیت جعبه‌ها با `path_box_slot` (سطر، ستون) داده می‌شود و ادامهٔ
  زنجیره با اتصال Z شکلِ `_row_wrap_connector` (از پایین جعبهٔ آخر سطر، در فاصلهٔ
  بین دو سطر به چپ با برچسب لینک/شاهد، و از بالای جعبهٔ اول سطر بعد) به سطر بعد
  می‌رود — هم در شاخهٔ reachable و هم در زنجیرهٔ upstream دستگاه‌های نارس.
- **اینونتوری IP اینترفیس‌ها در دیتابیس + برچسب خوانا (Task 25):** (الف) جدول
  `device_interface_ips` در هر دیتابیس (`db.py`: `replace_interface_inventory`
  — جایگزینی در سطح هر device_ip؛ `load_interface_inventory`) — worker گزارش
  مسیر بعد از خواندن دستگاه‌ها (فاز جدید `inventory`) ردیف‌های `inventory_rows_from_infos`
  (IP همهٔ اینترفیس‌ها + `device_id` = rowid ردیف devices که حالا در
  `query_devices`/`fetch_devices_by_ips` هم برگردانده می‌شود + identity) را ذخیره
  و سپس «همان دیتابیس» را به `build_topology(inventory=...)` می‌دهد: دستگاه‌های
  خوانده‌نشده (خطای API/بی‌آدرس — که ردیف تازه نمی‌گیرند و دادهٔ قبلی‌شان می‌ماند)
  مالکیت IPهای اینترفیس‌های‌شان را از دیتابیس می‌گیرند (یال به دستگاه واقعی به‌جای
  شبح) و گره‌های شبح با identity ثبت‌شده نام‌گذاری می‌شوند (`from_inventory`/
  `inventory_dev_id`)؛ `delete_devices` ردیف‌های اینونتوری را هم پاک می‌کند.
  (ب) برچسب‌های لینک نمودار مسیر خوانا شدند: به‌جای یک خط 5.8pt («ether10 <->
  ether24» که در گپ ۳۹٫۸pt بریده می‌شد)، `_inrow_link_labels` اینترفیسِ چپ را
  بالای خط اتصال و اینترفیسِ راست را زیر آن با فونت ۷pt (`PATH_IF_SIZE`) و
  برچسب شاهد را با ۶pt (`PATH_TAG_SIZE`) رسم می‌کند؛ `PATH_BOX_W` ۱۰۴→۹۴ تا گپ
  ~۵۳pt شود و طولانی‌ترین برچسب‌ها (تا `DEFAULT-ROUTE` و `ether10-slave`) کامل
  جا شوند؛ اتصال شکست سطر هم با فونت‌های `PATH_WRAP_LBL_SIZE`/`PATH_WRAP_TAG_SIZE`
  درشت‌تر شده. بررسی عددی عرض رشته‌ها با `reportlab.pdfbase.pdfmetrics.stringWidth`.
- **نام دستگاه درشت و خوانا (Task 26):** درخواست «فونت نام دستگاه در بالای گزارش
  مسیریابی بزرگ‌تر شود» — در `route_pdf.py`: (الف) نوار بالای صفحه: نام با
  `Helvetica-Bold 11` (`HEADER_NAME_SIZE`) و IP با 8 در ادامه‌اش (قبلاً کل خط
  7.5pt)؛ (ب) جعبه‌های نمودار: نام با 8.5 (`PATH_NAME_SIZE`) و 8.0 در شاخهٔ
  upstream (`PATH_UP_NAME_SIZE`) — قبلاً 6.6؛ نام‌های بلند با `_fit_lines`
  دورَقمی داخل جعبه جا می‌شوند و شکستن در مرز خط تیره/نقطه/زیرخط/دو نقطه/اسلش
  هم انجام می‌شود چون نام‌های میکروتیک معمولاً بدون فاصله‌اند (مثل
  RB-Anbar-daruel-HapLite) و فقط اگر باز جا نشد با «...» کوتاه می‌شود؛
  (پ) ارتفاع جعبه‌ها 30→36 / 26→32 (`PATH_BOX_H`/`PATH_UP_BOX_H`) و فاصلهٔ
  سطرهای نمودار 34→30 (`PATH_ROW_STRIDE`)؛ برای جبران، فاصلهٔ سطر جدول‌ها کمی
  جمع شده (kv 13→12.5، آدرس 11.5→11، اینترفیس 11→10.6، hop 12→11.2، شواهد
  11→10) تا «یک صفحه به ازای هر دستگاه» و پایان‌نگرفتن محتوا روی فوتر در
  بدترین حالت (۸ hop + ۱۲ آدرس + ۲۴ اینترفیس + ۶ شاهد) همچنان برقرار بماند —
  اندازه‌گیری‌شده با بوم ضبط‌کننده در `scripts/test_route_name_font_e2e.py`.
- **دستگاه همسایهٔ اینترفیس flapشده در گزارش هوشمند (Task 27):** درخواست «در گزارش
  هوشمند، دستگاه همسایهٔ متصل به اینترفیس گزارش‌شده شامل IP و نام دستگاه همسایه به
  گزارش اضافه شود» — `smart_reports.py` یک موتور تشخیص همسایه دارد:
  `parse_neighbor_entries` (هر دو شکل ذخیره‌شدهٔ /ip neighbor — خطوط جمع‌شدهٔ
  `collect_device_info` و dump جمله‌ای `collect_ip_info` — با regex عمومی
  `_KV_RE` که مقدار هر کلید در توکن `کلید=` بعدی تمام می‌شود تا کلیدهای ناشناخته
  مثل board-name مقدار قبلی را نبلعند)، `parse_self_addresses` (IP/ماسک هر
  اینترفیس از متن /ip address ذخیره‌شده)، `build_neighbor_context` (ایندکس
  IP→دستگاه و identity→دستگاه از لیست دستگاه‌ها + اینونتوری دیتابیس
  `device_interface_ips` + متن ip_addresses؛ ایندکس LLDP و IPهای خودِ هر دستگاه)
  و `_resolve_neighbor` با اولویت: (۱) ردیف‌های LLDP/MNDP خودِ دستگاه برای همان
  اینترفیس — تطبیق آدرس و بعد identity با دستگاه‌های شناخته‌شده؛ اگر شناخته شد
  نام/IP واقعی دستگاه برمی‌گردد وگرنه مقادیر خام LLDP؛ ردیف «خودبینی» (آدرسِ
  خود دستگاه) حذف می‌شود؛ (۲) fallback: دستگاهِ دیگری که IPاش در ساب‌نتِ IPِ
  همان اینترفیس باشد (از اینونتوری یا متن ip_addresses) — چند همسایه با «،»
  می‌آیند. خروجی در هر رویداد flap: `neighbor_name`/`neighbor_ip`/`neighbor_via`
  (lldp/subnet). هر سه اندپوینت flap در `main.py` اینونتوری دیتابیس را با
  `db.load_interface_inventory(db_path)` می‌خوانند و پاس می‌دهند (خطا → لیست
  خالی). دو ستون جدید «نام دستگاه همسایه» و «IP دستگاه همسایه» بعد از
  «اینترفیس» در جدول UI، CSV (۱۱ ستون، BOM) و xlsx اضافه شدند. ضمناً باگ
  پیش‌مخفی اندپوینت `export.xlsx` رفع شد (BytesIO خام به Response پاس داده می‌شد
  و همیشه ۵۰۰ می‌داد — حالا `data.getvalue()`). تست‌ها:
  `tests/test_flap_neighbor.py` (۱۲ تست) و `scripts/test_flap_neighbor_e2e.py`
  (۲۸ بررسی: JSON/CSV/XLSX با اینونتوری واقعی دیتابیس موقت). تست قدیمی
  `test_ip_info_path_fix.py` که مهر تاریخ ثابت لاگ داشت و بعد از چند روز کهنه
  می‌شد، مهر پویا گرفت و بررسی «دیتابیس واقعی» به‌دلیل وابستگی محیطی گیت شد.
- **انتقال ستون‌های نام/IP دستگاه به لبهٔ چپ گزارش flap + پهنای مشخص فیلدها (Task 28):**
  درخواست «ستون‌های نام دستگاه و ای پی دستگاه به ستون سمت چپ گزارش منتقل شود؛ پهنای
  فیلدها اصلاح/adjust شود» — در جدول RTL انتهای آرایهٔ ستون‌ها چپ‌ترین ستون است؛ ترتیب
  جدید هر سه خروجی یکی شد: ردیف، تگ دستگاه، اینترفیس، نام دستگاه همسایه، IP دستگاه
  همسایه، تعداد تکرار لاگ، تاریخ میلادی، تاریخ شمسی، نوع رویداد، آی‌پی دستگاه، نام
  دستگاه — یعنی «نام دستگاه» چپ‌ترین و «آی‌پی دستگاه» کنارش. در `frontend/src.jsx`
  جدول به پیکربندی ستون‌محور `FLAP_COLS` تبدیل شد با `table-layout:fixed`,
  `box-sizing:border-box` و عرض مشخص هر ستون (ردیف 56، تگ 100، اینترفیس 120،
  نام همسایه 150، IP همسایه 130، تعداد 80، میلادی 170، شمسی 175، رویداد 110،
  آی‌پی 130، نام 175 — مجموع 1396، min-width جدول 1400)؛ سرستون وسط‌چین و قابل
  شکستن دوخطی، ستون‌های متنی با `overflow-wrap:break-word` داخل سلول می‌شکنند و
  ستون‌های عددی/IP/تاریخ nowrap یک‌خطی می‌مانند. نکتهٔ دام‌دار: بدون
  `box-sizing:border-box` پدینگ 24px هر سلول به عرض ستون اضافه می‌شود و جمع ستون‌ها
  (~1607px) از کادر بیرون می‌زند و دو ستون راست در اسکرول گم می‌شوند. همین ترتیب در
  `interface_flaps_csv` و `interface_flaps_xlsx` هم اعمال شد (شیت اکسل rightToLeft
  است پس آنجا هم نام/IP چپ‌ترین‌اند) — ترتیب ستون‌های CSV/xlsx عوض شد؛ هر تستی که
  اندیس ستون flap را چک می‌کند باید اندیس‌های جدید (همسایه 3/4، نام/IP دستگاه 9/10)
  را داشته باشد. تست‌ها: `tests/test_flap_neighbor.py` و
  `scripts/test_flap_neighbor_e2e.py` (+۴ بررسی جایگاه چپ). بازبینی بصری رندر جدول
  با Playwright در دو عرض 1440/900 انجام شد.
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
- پچ کردن توابع شبکه در تست‌ها باید روی **هر دو شیء ماژول** انجام شود: `main.py`
  با `from backend import routeros_api` ایمپورت می‌کند ولی تست با `import routeros_api`
  — این دو می‌توانند شیءهای متفاوتی باشند (الگوی `ROS_MODULES` در
  `test_push_config_progress.py` و پچ دوگانهٔ collector در `test_device_picker.py`).
  در غیر این صورت تست، اتصال واقعی به شبکه می‌زند.
- فایل کانفیگ سیسکو (`databases/cisco_central_config.txt`) وضعیت سراسری و دایمی است —
  تست‌ها باید قبل و بعد از اجرا از آن backup بگیرند/پاک کنند (الگوی `restore_cfg` در
  `test_cisco_config.py`) تا کانفیگ واقعی کاربر از بین نرود.
- `TOPOLOGY_STATE["unreachable_rows"]` وضعیت سراسری از آخرین گزارش است — reset_state
  تست‌ها باید آن (و `unreachable_error`) را هم None کند وگرنه CSV تست قبلی در همان
  پروسه نشت می‌کند (الگوی `reset_state` در `test_route_unreachable_csv.py`).
- متن PDF را در تست‌ها مستقیم از بایت‌های خام جستجو نکنید (استریم‌ها ASCII85+Flate
  فشرده‌اند) — با `pypdf.extract_text` یا `pdftotext -layout` متن را دربیاورید
  (الگوی `pdf_text` در `test_cisco_config.py`).

## ۷) امنیت

- مخزن عمومی است: هر داده‌ای با IP/تگ/نام واقعی شبکه (مثل فایل‌های runtime
  `databases/`، `ip_info/`، `.vpn_runtime/`) نباید به کامیت‌های جدید اضافه شود.
- توکن/رمز در URL ریموت، لاگ یا خروجی تست قرار نگیرد.
- این ابزار فقط برای شبکه‌هایی با مجوز صریح است؛ اسکن بدون اجازه ممنوع.
