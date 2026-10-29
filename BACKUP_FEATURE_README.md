# قابلیت Backup (.rsc)

## بازیابی فوری backend/routeros_api.py

این فایل به‌اشتباه با محتوای placeholder جایگزین شده بود.
از تاریخچه Git بازیابی کنید:

```bash
git checkout 40c23821673292a6569f59df5cba10654511ae95 -- backend/routeros_api.py
```

سپس فایل‌های اصلاح‌شده را از پکیج patch جایگزین کنید:
- backend/routeros_api.py
- backend/db.py
- backend/main.py
- frontend/src.jsx
- frontend/style.css

## رفتار جدید

با «خواندن با API»، پیکربندی کامل دستگاه با `/export` گرفته می‌شود و در فیلد `device_backup` ذخیره می‌شود.
دکمه **Backup** کنار **Log** متن `.rsc` را نشان می‌دهد و دکمه «دانلود .rsc» فایل را ذخیره می‌کند.
