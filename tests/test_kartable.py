"""Task 32 — تست بک‌اند کارتابل اداری.

- بذر خودکار: برای «هر بخش» یک رکورد نمونه (۷ پوشهٔ منو + اطلاعیه + رویداد تقویم)؛
- CRUD آیتم‌ها (ذخیره‌سازی/خوانده‌شدن/انتقال/حذف) با TestClient روی اپ واقعی؛
- آمار کارت «گزارش مکاتبات اداری» و بج‌های منو؛
- اعتبارسنجی پوشه/زیرپوشه و قالب تاریخ رویداد؛ مسیر /template.docx قالب Word.
همهٔ تست‌ها روی دیتابیس موقت کار می‌کنند؛ databases/kartable.db واقعی دست‌نخورده می‌ماند.
"""
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import auth
from backend import kartable as kb
from backend.main import app


@pytest.fixture()
def kb_tmp(monkeypatch, tmp_path):
    """دیتابیس کارتابل موقت + بذرگیری از نو برای هر تست."""
    dbf = tmp_path / "kartable_test.db"
    monkeypatch.setattr(kb, "KARTABLE_DB", dbf)
    monkeypatch.setattr(kb, "_READY", False)
    yield dbf


@pytest.fixture()
def client(kb_tmp):
    c = TestClient(app)
    c.cookies.set(auth.COOKIE_NAME, auth.create_token(auth.ADMIN_USER))
    return c


def _summary(client):
    r = client.get("/api/kartable/summary")
    assert r.status_code == 200
    return r.json()


def test_seed_one_sample_per_section(client, kb_tmp):
    """برای هر بخشِ منوی کارتابل (و اطلاعیه/رویداد) حداقل یک رکورد نمونه ساخته شده باشد."""
    s = _summary(client)
    assert s["items_total"] >= 7
    for folder in kb.FOLDERS:  # هر ۷ بخش منو یک نمونه دارد
        assert s["folders"][folder] >= 1, folder
    assert s["unread"] >= 1          # صندوق ورودی خوانده‌نشده
    assert s["drafts"] >= 1          # پیش‌نویس
    assert s["total_inbox"] >= 1     # کل وارده
    assert s["confidential"] >= 1    # محرمانه (نمونهٔ پوشه محرمانه)
    assert s["announcements"] >= 1
    assert s["events"] >= 1


def test_items_filter_by_folder_and_subfolder(client, kb_tmp):
    r = client.get("/api/kartable/items", params={"folder": "بایگانی شخصی"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert {i["subfolder"] for i in items} >= {"پوشه محرمانه", "پوشه عمومی"}
    conf = [i for i in items if i["subfolder"] == "پوشه محرمانه"]
    assert len(conf) == 1 and conf[0]["confidentiality"] == "محرمانه"
    # فیلتر زیرپوشه
    r2 = client.get("/api/kartable/items", params={"folder": "بایگانی شخصی", "subfolder": "پوشه محرمانه"})
    items2 = r2.json()["items"]
    assert items2 and all(i["subfolder"] == "پوشه محرمانه" for i in items2)


def test_item_storage_roundtrip(client, kb_tmp):
    """تست ذخیره‌سازی: ایجاد → دیده‌شدن در لیست → خوانده‌شدن → حذف."""
    body = {"folder": "نامه‌های اقدامی", "subfolder": "جهت امضا",
            "subject": "نامهٔ تست ذخیره‌سازی", "sender": "واحد تست", "letter_no": "۱۴۰۵/۹۹۹"}
    r = client.post("/api/kartable/items", json=body)
    assert r.status_code == 201
    item_id = r.json()["id"]
    assert r.json()["item"]["status"] == "خوانده‌نشده"

    r = client.get("/api/kartable/items", params={"folder": "نامه‌های اقدامی", "subfolder": "جهت امضا"})
    assert any(i["id"] == item_id for i in r.json()["items"])

    r = client.put(f"/api/kartable/items/{item_id}", json={"status": "خوانده‌شده"})
    assert r.status_code == 200 and r.json()["item"]["status"] == "خوانده‌شده"

    r = client.delete(f"/api/kartable/items/{item_id}")
    assert r.status_code == 200
    assert client.delete(f"/api/kartable/items/{item_id}").status_code == 404
    assert client.put(f"/api/kartable/items/{item_id}", json={"status": "خوانده‌شده"}).status_code == 404


def test_summary_reflects_mark_read(client, kb_tmp):
    before = _summary(client)
    r = client.post("/api/kartable/items", json={"folder": "صندوق ورودی", "subfolder": "جهت استحضار",
                                                 "subject": "نامهٔ جدید ورودی"})
    assert r.status_code == 201
    mid = _summary(client)
    assert mid["unread"] == before["unread"] + 1
    assert mid["total_inbox"] == before["total_inbox"] + 1
    item_id = r.json()["id"]
    client.put(f"/api/kartable/items/{item_id}", json={"status": "خوانده‌شده"})
    after = _summary(client)
    assert after["unread"] == before["unread"]


def test_move_item_between_folders(client, kb_tmp):
    r = client.post("/api/kartable/items", json={"folder": "پیش‌نویس‌ها", "subfolder": "پیش‌نویس‌های من",
                                                 "subject": "پیش‌نویس برای ارسال"})
    item_id = r.json()["id"]
    before = _summary(client)
    r2 = client.put(f"/api/kartable/items/{item_id}", json={"folder": "ارسال شده ها", "status": "ارسال‌شده"})
    assert r2.status_code == 200
    after = _summary(client)
    assert after["drafts"] == before["drafts"] - 1
    items = client.get("/api/kartable/items", params={"folder": "ارسال شده ها"}).json()["items"]
    assert any(i["id"] == item_id and i["status"] == "ارسال‌شده" for i in items)


def test_invalid_folder_and_event_date_rejected(client, kb_tmp):
    assert client.post("/api/kartable/items", json={"folder": "پوشهٔ ناموجود", "subject": "x"}).status_code == 422
    assert client.post("/api/kartable/items", json={"folder": "صندوق ورودی", "subfolder": "زیرپوشهٔ دروغ",
                                                    "subject": "x"}).status_code == 422
    assert client.post("/api/kartable/events", json={"event_date": "۱۴۰۵/۸/۱۵", "title": "بد"}).status_code == 422
    assert client.post("/api/kartable/events", json={"event_date": "1405/08/15", "title": "خوب"}).status_code == 201


def test_announcements_endpoints(client, kb_tmp):
    anns = client.get("/api/kartable/announcements").json()["announcements"]
    assert anns and anns[0]["title"] == "اطلاعیه مهم اداری"
    assert "help.pdf" in anns[0]["attachment"]
    r = client.post("/api/kartable/announcements", json={"title": "اطلاعیه تست", "body": "متن", "attachment": "a.pdf"})
    assert r.status_code == 201
    anns2 = client.get("/api/kartable/announcements").json()["announcements"]
    assert anns2[0]["title"] == "اطلاعیه تست"  # جدیدترین اول


def test_events_seeded_on_current_week(client, kb_tmp):
    """رویداد نمونهٔ «جلسه اداری» با تاریخ امروز شمسی درج شده باشد."""
    evts = client.get("/api/kartable/events").json()["events"]
    assert any(e["title"] == "جلسه اداری" and e["event_date"] == kb.today_jalali() for e in evts)


def test_kartable_requires_auth(kb_tmp):
    c = TestClient(app)
    assert c.get("/api/kartable/summary").status_code == 401
    assert c.post("/api/kartable/items", json={"folder": "صندوق ورودی", "subject": "x"}).status_code == 401


def test_template_docx_served(client, kb_tmp):
    r = client.get("/template.docx")
    assert r.status_code == 200
    assert r.content[:2] == b"PK"  # امضای فایل docx (zip)


def test_module_create_rejects_unknown_folder(kb_tmp):
    with pytest.raises(ValueError):
        kb.create_item("پوشهٔ ناموجود", "x")
