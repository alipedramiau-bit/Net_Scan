"""Task 34 — پشتیبان‌گیری کانفیگ میکروتیک با پسوند rsc در پوشهٔ backup/.

درخواست کاربر: «یک فولدر به نام backup در مسیر برنامه ایجاد کن که با یک دکمهٔ
backup بتواند از طریق API و ورود یوزر/پسورد بک‌آپ دستگاه‌های میکروتیک با پسوند
rsc بگیرد؛ با نام/ای‌دی دستگاه‌ها و ای‌پی دستگاه در فولدر backup ذخیره کند».

پوشش:
1) نام فایل: «<نام دستگاه>_<IP>.rsc» — دستگاه بی‌نام از ای‌دی ردیف دیتابیس
   (device-<id>)؛ کاراکترهای غیرمجاز پاک می‌شوند؛
2) export_config_via_api — پارس پاسخ /export (هم !done تکی با =ret= و هم
   چند !re تکه‌تکه) + !trap/!fatal با پیام فارسی؛
3) backup_devices — هر دستگاه فقط یک‌بار (IP یکتا)، ذخیره در پوشهٔ backup،
   پیشرفت/لغو؛
4) endpointها با TestClient: اعتبارسنجی ورودی، اجرای موفق/ناموفق،
   progress/files.

اتصال واقعی RouterOS با جایگزینی (monkeypatch) کلاینت تست می‌شود — هیچ
دستگاه واقعی‌ای لمس نمی‌شود و پوشهٔ backup واقعی پروژه دست‌نخورده می‌ماند.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import backup_rsc
from backend import routeros_api as local_ros  # همان ماژولی که backup_rsc استفاده می‌کند
from backend.main import app


@pytest.fixture()
def backup_dir(monkeypatch, tmp_path):
    """پوشهٔ backup موقت + ریست وضعیت پیشرفت برای هر تست."""
    d = tmp_path / "backup"
    d.mkdir()
    monkeypatch.setattr(backup_rsc, "BACKUP_DIR", d)
    backup_rsc.BACKUP_PROGRESS.update({"total": 0, "done": 0, "ok": 0, "failed": 0,
                                       "current_ip": "", "percent": 0,
                                       "running": False, "canceled": False, "error": None})
    backup_rsc.BACKUP_CANCEL.clear()
    return d


@pytest.fixture()
def client():
    c = TestClient(app)
    r = c.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
    assert r.status_code == 200, f"login failed: {r.status_code}"
    return c


# ------------------------- نام فایل ---------------------------------------
def test_filename_name_and_ip():
    assert backup_rsc.backup_filename("CORE-SW", "172.18.1.105", 12) == "CORE-SW_172.18.1.105.rsc"


def test_filename_unnamed_uses_db_id():
    """دستگاه بی‌نام از ای‌دی ردیف دیتابیس نام می‌گیرد (device-<id>)."""
    assert backup_rsc.backup_filename("", "10.0.0.2", 34) == "device-34_10.0.0.2.rsc"
    assert backup_rsc.backup_filename(None, "10.0.0.2", None) == "device_10.0.0.2.rsc"


def test_filename_sanitizes_unsafe_chars():
    """کاراکترهای غیرمجاز نام فایل (ویندوز/لینوکس) پاک می‌شوند."""
    assert backup_rsc.backup_filename('a/b\\c:d*e?f"g<h>i|j', "10.0.0.2", 1) == \
        "a-b-c-d-e-f-g-h-i-j_10.0.0.2.rsc"
    assert backup_rsc.safe_stem("  **  ") == "router"  # fallback


# ------------------------- پارس /export ------------------------------------
class _FakeClient:
    """جایگزین RouterOSClient: پاسخ از پیش تعیین‌شده یا خطای اتصال."""
    last_kwargs = {}

    def __init__(self, host, port=8728, timeout=20.0, replies=None, fail=None):
        self.host, self.port, self.timeout = host, port, timeout
        self.replies, self.fail = replies, fail
        self.closed = False
        type(self).last_kwargs = {"host": host, "port": port, "timeout": timeout}

    def connect(self):
        if self.fail:
            raise backup_rsc._ros.RouterOSError(self.fail)

    def login(self, username, password):
        self.creds = (username, password)  # فقط ثبت — اعتبارگیری در تست جریان API انجام می‌شود

    def talk(self, words, timeout=None):
        assert words == ["/export"], words
        return self.replies or []

    def close(self):
        self.closed = True


def _patch_client(monkeypatch, replies=None, fail=None):
    monkeypatch.setattr(backup_rsc, "_ros", local_ros)
    monkeypatch.setattr(local_ros, "RouterOSClient",
                        lambda host, port=8728, timeout=20.0: _FakeClient(host, port, timeout, replies, fail))


def test_export_parses_single_done_ret(monkeypatch):
    replies = [["!done", "=ret=# RouterOS 7.14\n/interface print"]]
    _patch_client(monkeypatch, replies=replies)
    text = backup_rsc.export_config_via_api("10.0.0.2", "netadmin", "secret", timeout=5)
    assert text.startswith("# RouterOS 7.14")
    assert _FakeClient.last_kwargs["timeout"] >= backup_rsc.EXPORT_MIN_TIMEOUT


def test_export_concatenates_chunked_replies(monkeypatch):
    # چند !re تکه‌تکه + !done — تکه‌ها به‌ترتیب چسبانده می‌شوند
    replies = [["!re", "=ret=# part1\n"], ["!re", "=ret=# part2\n"], ["!done", "=ret=# part3\n"]]
    _patch_client(monkeypatch, replies=replies)
    text = backup_rsc.export_config_via_api("10.0.0.2", "u", "p")
    assert text == "# part1\n# part2\n# part3\n"


def test_export_empty_output_is_error(monkeypatch):
    _patch_client(monkeypatch, replies=[["!done"]])
    with pytest.raises(Exception) as ei:
        backup_rsc.export_config_via_api("10.0.0.2", "u", "p")
    assert "خروجی /export خالی" in str(ei.value)


def test_export_trap_message(monkeypatch):
    _patch_client(monkeypatch, replies=[["!trap", "=message=no such command"]])
    with pytest.raises(Exception) as ei:
        backup_rsc.export_config_via_api("10.0.0.2", "u", "p")
    assert "no such command" in str(ei.value)


# ------------------------- backup_devices ----------------------------------
def _dev(ip, name, dev_id):
    return {"id": dev_id, "ip": ip, "device_name": name}


def test_backup_devices_writes_files_and_progress(monkeypatch, backup_dir):
    replies = [["!done", "=ret=# config for router\n"]]
    _patch_client(monkeypatch, replies=replies)
    devices = [_dev("10.0.0.2", "CORE-SW", 1), _dev("10.0.0.3", "", 2), _dev("10.0.0.2", "CORE-SW", 9)]
    rows = backup_rsc.backup_devices(devices, "netadmin", "secret", max_workers=2)
    assert len(rows) == 2  # IP تکراری حذف شد
    r1, r2 = rows
    assert r1["ok"] and r1["file"] == "CORE-SW_10.0.0.2.rsc"
    assert (backup_dir / "CORE-SW_10.0.0.2.rsc").read_text(encoding="utf-8") == "# config for router\n"
    assert r2["ok"] and r2["file"] == "device-2_10.0.0.3.rsc"
    p = backup_rsc.BACKUP_PROGRESS
    assert p["done"] == 2 and p["ok"] == 2 and p["failed"] == 0 and not p["running"]


def test_backup_devices_failure_row(monkeypatch, backup_dir):
    _patch_client(monkeypatch, fail="connection refused")
    rows = backup_rsc.backup_devices([_dev("10.9.9.9", "X-MK", 5)], "u", "p")
    assert not rows[0]["ok"] and "connection refused" in rows[0]["error"]
    assert backup_rsc.BACKUP_PROGRESS["failed"] == 1
    assert not list(backup_dir.glob("*.rsc"))


def test_backup_devices_respects_cancel(monkeypatch, backup_dir):
    """پس از ست‌شدن رویداد لغو (وسط کار)، دستگاه‌های باقی‌مانده پردازش نمی‌شوند."""
    _patch_client(monkeypatch, replies=[["!done", "=ret=# c\n"]])
    cancel = __import__("threading").Event()
    real_export = backup_rsc.export_config_via_api

    def export_then_cancel(host, *a, **kw):
        cancel.set()  # بعد از نخستین دستگاه، بقیه لغو می‌شود
        return real_export(host, *a, **kw)

    monkeypatch.setattr(backup_rsc, "export_config_via_api", export_then_cancel)
    rows = backup_rsc.backup_devices(
        [_dev("10.0.0.2", "A", 1), _dev("10.0.0.3", "B", 2), _dev("10.0.0.4", "C", 3)],
        "u", "p", max_workers=1, cancel=cancel)
    assert [r["ip"] for r in rows] == ["10.0.0.2"], rows
    assert backup_rsc.BACKUP_PROGRESS["canceled"] is True
    assert backup_rsc.BACKUP_PROGRESS["done"] == 1


# ------------------------- endpointها --------------------------------------
def test_api_backup_requires_credentials_and_ips(client):
    r = client.post("/api/devices/backup-rsc", json={"ips": [], "username": "u"})
    assert r.status_code == 422, r.text  # ips حداقل یکی
    r = client.post("/api/devices/backup-rsc", json={"ips": ["10.0.0.2"], "username": ""})
    assert r.status_code == 422, r.text


def test_api_backup_flow(client, monkeypatch, backup_dir):
    monkeypatch.setattr(backup_rsc, "_ros", local_ros)
    monkeypatch.setattr(local_ros, "RouterOSClient",
                        lambda host, port=8728, timeout=20.0: _FakeClient(host, port, timeout, [["!done", "=ret=# cfg\n"]]))
    import backend.db as dbm
    monkeypatch.setattr(dbm, "fetch_devices_by_ips",
                        lambda ips, db_path=None: [_dev("10.0.0.2", "CORE-SW", 1), _dev("10.0.0.3", "EDGE", 2)])
    r = client.post("/api/devices/backup-rsc", json={"ips": ["10.0.0.2", "10.0.0.3"],
                                                     "username": "netadmin", "password": "secret"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["total"] == 2 and d["ok"] == 2 and d["failed"] == 0
    assert d["folder"] == str(backup_dir)
    assert {x["file"] for x in d["results"]} == {"CORE-SW_10.0.0.2.rsc", "EDGE_10.0.0.3.rsc"}
    assert (backup_dir / "CORE-SW_10.0.0.2.rsc").exists()
    # پیشرفت پس از پایان: running=False
    pr = client.get("/api/devices/backup-rsc/progress").json()
    assert pr["running"] is False and pr["done"] == 2


def test_api_backup_unknown_devices_404(client, monkeypatch):
    import backend.db as dbm
    monkeypatch.setattr(dbm, "fetch_devices_by_ips", lambda ips, db_path=None: [])
    r = client.post("/api/devices/backup-rsc", json={"ips": ["10.99.99.99"], "username": "u"})
    assert r.status_code == 404, r.text


def test_api_backup_files_list(client, backup_dir):
    (backup_dir / "A_10.0.0.2.rsc").write_text("# a\n", encoding="utf-8")
    (backup_dir / "B_10.0.0.3.rsc").write_text("# b\n", encoding="utf-8")
    (backup_dir / "ignored.txt").write_text("x", encoding="utf-8")
    r = client.get("/api/devices/backup-rsc/files")
    assert r.status_code == 200
    d = r.json()
    assert d["count"] == 2 and d["folder"] == str(backup_dir)
    names = {f["file"] for f in d["files"]}
    assert names == {"A_10.0.0.2.rsc", "B_10.0.0.3.rsc"}  # فقط rsc
