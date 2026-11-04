"""Task 37 (ادامه) — دلتای ماژول errorlog: سطح (warn/info)، فیلتر جستجوی آزاد
سرورساید و خروجی CSV لاگ.

مبنا: پیاده‌سازی errorlog (mik_log/errorlog.jsonl با کلید فعال/خاموش و چرخش) —
این تست‌ها فقط افزودنی‌های بعدی را پوشش می‌دهند:
1) log_warn/log_info + فیلد level (پیش‌فرض error برای فراخوانی‌های قدیمی)؛
2) read_errors با فیلتر level و q (جستجوی case-insensitive در پیام/raw/ip/منبع)؛
3) GET /api/errorlog با level/q؛
4) GET /api/errorlog/csv — BOM + مهر زمانی در نام فایل + ستون‌های فارسی.
"""
import csv
import io
import re
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend import errorlog  # noqa: E402
from backend.main import app  # noqa: E402


@pytest.fixture()
def client():
    c = TestClient(app)
    assert c.post("/api/login", json={"username": "admin", "password": "NetAdmin"}).status_code == 200
    return c


@pytest.fixture(autouse=True)
def isolated_log(monkeypatch, tmp_path):
    log_dir = tmp_path / "mik_log"
    monkeypatch.setattr(errorlog, "LOG_DIR", log_dir)
    monkeypatch.setattr(errorlog, "LOG_FILE", log_dir / "errorlog.jsonl")
    monkeypatch.setattr(errorlog, "CONFIG_FILE", log_dir / "config.json")


def test_levels_and_default_error():
    errorlog.log_error("backup-rsc", "خطا")
    errorlog.log_warn("backup-rsc", "خلاصهٔ با خطا")
    errorlog.log_info("backup-rsc", "خلاصهٔ موفق")
    errorlog.log_error("system", "سطح نامعتبر", level="weird")  # → error
    entries = errorlog.read_errors(limit=10)
    assert [e["level"] for e in entries] == ["error", "info", "warn", "error"]  # جدیدترین اول


def test_read_errors_level_filter():
    errorlog.log_error("backup-rsc", "خطای ورود")
    errorlog.log_info("backup-rsc", "خلاصهٔ موفق")
    e = errorlog.read_errors(level="error")
    assert len(e) == 1 and "خطای ورود" in e[0]["message"]
    e = errorlog.read_errors(level="info")
    assert len(e) == 1
    e = errorlog.read_errors(level="warn")
    assert e == []
    # ردیف‌های قدیمی بدون level → error فرض می‌شوند
    errorlog.LOG_FILE.write_text('{"time":"2026-11-04 10:00:00","source":"x","ip":"","stage":"","message":"قدیمی","raw":""}\n',
                                 encoding="utf-8")
    e = errorlog.read_errors(level="error")
    assert any("قدیمی" in x["message"] for x in e)


def test_read_errors_free_text_search():
    errorlog.log_error("backup-rsc", "ورود API رد شد", ip="172.17.12.34", raw="invalid user name or password (6)")
    errorlog.log_info("system", "پشتیبان‌گیری تمام شد")
    assert len(errorlog.read_errors(q="(6)")) == 1            # در raw
    assert len(errorlog.read_errors(q="172.17.12.34")) == 1   # در ip
    assert len(errorlog.read_errors(q="تمام شد")) == 1        # در پیام
    assert errorlog.read_errors(q="چیز-دیگر") == []
    assert len(errorlog.read_errors(source="backup-rsc", q="ورود")) == 1


def test_api_errorlog_filters(client):
    errorlog.log_error("backup-rsc", "ورود API از سمت روتر رد شد (invalid user name or password (6))", ip="172.17.12.34")
    errorlog.log_info("system", "خلاصهٔ موفق")
    d = client.get("/api/errorlog").json()
    assert d["count"] == 2 and len(d["entries"]) == 2
    d = client.get("/api/errorlog", params={"level": "error", "q": "(6)"}).json()
    assert len(d["entries"]) == 1 and d["entries"][0]["ip"] == "172.17.12.34"
    d = client.get("/api/errorlog", params={"level": "info"}).json()
    assert len(d["entries"]) == 1 and "خلاصهٔ موفق" in d["entries"][0]["message"]


def test_api_errorlog_csv(client):
    errorlog.log_error("backup-rsc", "ورود رد شد", ip="10.0.0.9", stage="login", raw="raw-text")
    errorlog.log_info("system", "خلاصهٔ موفق")
    r = client.get("/api/errorlog/csv")
    assert r.status_code == 200
    assert re.search(r"error_log_\d{8}_\d{6}\.csv", r.headers.get("content-disposition", ""))
    assert r.content.startswith(b"\xef\xbb\xbf")  # BOM
    rows = list(csv.reader(io.StringIO(r.content.decode("utf-8-sig"))))
    assert rows[0] == ["زمان", "سطح", "منبع", "IP دستگاه", "مرحله", "پیام", "جزئیات خام"]
    body = {tuple(row[2:5]) for row in rows[1:]}
    assert ("backup-rsc", "10.0.0.9", "login") in body
    # فیلتر در CSV هم اعمال می‌شود
    r = client.get("/api/errorlog/csv", params={"level": "info"})
    rows = list(csv.reader(io.StringIO(r.content.decode("utf-8-sig"))))
    assert len(rows) == 2 and "خلاصهٔ موفق" in rows[1][5]


def test_api_errorlog_csv_requires_auth():
    c = TestClient(app)
    assert c.get("/api/errorlog/csv").status_code == 401
