"""Task 34/36/37 — پشتیبان‌گیری کانفیگ میکروتیک با پسوند rsc در پوشهٔ mik_backup/.

درخواست کاربر: «یک فولدر به نام backup در مسیر برنامه ایجاد کن که با یک دکمهٔ
backup بتواند از طریق API و ورود یوزر/پسورد بک‌آپ دستگاه‌های میکروتیک با پسوند
rsc بگیرد؛ با نام/ای‌دی دستگاه‌ها و ای‌پی دستگاه در فولدر backup ذخیره کند»
+ «فولدر backup را به نام mik_backup تغییر نام بده» (Task 36)
+ «نتونست بک اپ بگیره؛ یک گزینه ثبت لاگ خطا در برگهٔ مدیریت سیستم ایجاد کن؛
خطا را برطرف کن؛ یوزر پسورد ورود مشکلی نداره» (Task 37).

پوشش:
1) نام فایل: «<نام دستگاه>_<IP>.rsc» — دستگاه بی‌نام از ای‌دی ردیف دیتابیس
   (device-<id>)؛ کاراکترهای غیرمجاز پاک می‌شوند؛
2) export_config_via_api — پارس پاسخ /export (هم !done تکی با =ret= و هم
   چند !re تکه‌تکه) + !trap/!fatal با پیام فارسی + عیب‌یابی مرحله‌ای خطا
   (connect/login/read — Task 36) + روش فایل (Task 37): خروجی خالی مستقیم →
   /export =file= + پول اندازه + خواندن contents + حذف فایل موقت؛
3) backup_devices — هر دستگاه فقط یک‌بار (IP یکتا)، ذخیره در پوشهٔ mik_backup،
   پیشرفت/لغو + ثبت خطاها در لاگ (errorlog — Task 37)؛
4) انتقال خودکار پوشهٔ قدیمی backup/ به mik_backup/ (Task 36)؛
5) ورود: روش مستقیم v6.43+ و در شکست، تلاش چالش-پاسخ روی اتصال تازه (Task 37)؛
6) endpointها با TestClient: اعتبارسنجی ورودی، اجرای موفق/ناموفق،
   progress/files + endpointهای لاگ خطا (Task 37).

اتصال واقعی RouterOS با جایگزینی (monkeypatch) کلاینت تست می‌شود — هیچ
دستگاه واقعی‌ای لمس نمی‌شود و پوشهٔ mik_backup واقعی پروژه دست‌نخورده می‌ماند.
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
    """پوشهٔ mik_backup موقت + ریست وضعیت پیشرفت برای هر تست."""
    d = tmp_path / "mik_backup"
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
    """جایگزین RouterOSClient — پاسخ‌های از پیش تعیین‌شده یا خطای اتصال.

    replies می‌تواند اسکریپت مرحله‌به‌مرحله باشد: هر talk یک مرحله مصرف می‌کند و
    آخرین مرحله تکرار می‌شود — تا جریان چندمرحله‌ای روش فایل (Task 37:
    /export → /export =file= → پول /file/print → contents → remove) هم
    شبیه‌سازی شود. تک‌عنصری مثل قبل برای همهٔ talkها همان پاسخ را می‌دهد.
    """
    last_kwargs = {}

    def __init__(self, host, port=8728, timeout=20.0, replies=None, fail=None):
        self.host, self.port, self.timeout = host, port, timeout
        self.replies = list(replies) if replies else []
        self.fail = fail
        self.calls: list[list[str]] = []
        self.closed = False
        type(self).last_kwargs = {"host": host, "port": port, "timeout": timeout}

    def connect(self):
        if self.fail:
            raise backup_rsc._ros.RouterOSError(self.fail)

    def login(self, username, password):
        self.creds = (username, password)  # فقط ثبت — اعتبارگیری در تست جریان API انجام می‌شود

    def talk(self, words, timeout=None):
        self.calls.append(list(words))
        if not self.replies:
            return []
        first = self.replies[0]
        if not (isinstance(first, list) and first and isinstance(first[0], list)):
            # سبک قدیم: خودِ self.replies یک پاسخ است (فهرست جمله‌ها)
            return self.replies
        # اسکریپت Task 37: هر عضو یک پاسخ کامل است؛ آخرین عضو تکرار می‌شود
        return self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]

    def close(self):
        self.closed = True


def _patch_client(monkeypatch, replies=None, fail=None):
    monkeypatch.setattr(backup_rsc, "_ros", local_ros)
    monkeypatch.setattr(local_ros, "RouterOSClient",
                        lambda host, port=8728, timeout=20.0, **kw: _FakeClient(host, port, timeout, replies, fail))


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
    _patch_client(monkeypatch, replies=[[["!done"]], [["!done"]],
                                        [["!done"]], [["!done"]]])
    monkeypatch.setattr(backup_rsc, "_FILE_POLL_INTERVAL", 0)
    with pytest.raises(Exception) as ei:
        backup_rsc.export_config_via_api("10.0.0.2", "u", "p")
    assert "خروجی /export خالی" in str(ei.value)  # روش فایل هم بی‌نتیجه → باز هم خطای واضح


def test_export_trap_message(monkeypatch):
    _patch_client(monkeypatch, replies=[["!trap", "=message=no such command"]])
    with pytest.raises(Exception) as ei:
        backup_rsc.export_config_via_api("10.0.0.2", "u", "p")
    assert "no such command" in str(ei.value)


# ------------------- Task 37: روش فایل (ROS 6 خروجی مستقیم نمی‌دهد) ----------
def _size_rep(n=1234, fid="*1"):
    return [["!re", f"=.id={fid}", "=name=mikbk-x.rsc", f"=size={n}"], ["!done"]]


def test_export_empty_falls_back_to_file_method(monkeypatch):
    cont = [["!re", "=contents=# RouterOS 6 config\n"], ["!done"]]
    _patch_client(monkeypatch, replies=[
        [["!done"]],            # /export مستقیم → فقط !done (ROS 6)
        [["!done"]],            # /export =file= → ok
        _size_rep(), _size_rep(), _size_rep(),   # پول اندازه تا ثبات
        cont,                   # خواندن contents
    ])
    monkeypatch.setattr(backup_rsc, "_FILE_POLL_INTERVAL", 0)
    text = backup_rsc.export_config_via_api("10.0.0.2", "u", "p")
    assert text == "# RouterOS 6 config\n"


def test_export_file_method_removes_temp_file(monkeypatch):
    cont = [["!re", "=contents=# c\n"], ["!done"]]
    replies = [
        [["!done"]], [["!done"]], _size_rep(fid="*7"), _size_rep(fid="*7"),
        _size_rep(fid="*7"), cont,
    ]
    monkeypatch.setattr(backup_rsc, "_FILE_POLL_INTERVAL", 0)

    holder = {"calls": []}

    class _Cap(_FakeClient):
        def talk(self, words, timeout=None):
            holder["calls"].append(list(words))
            return super().talk(words, timeout=timeout)

    monkeypatch.setattr(local_ros, "RouterOSClient",
                        lambda host, port=8728, timeout=20.0, **kw: _Cap(host, port, timeout, replies))
    backup_rsc.export_config_via_api("10.0.0.2", "u", "p")
    calls = holder["calls"]
    assert calls[0] == ["/export"]
    assert calls[1][0] == "/export" and any(w.startswith("=file=") for w in calls[1])
    assert any(c[0] == "/file/print" and any(w.startswith("?name=") for w in c) for c in calls)
    assert calls[-1][0] == "/file/remove" and "=.id=*7" in calls[-1]  # پاک‌سازی فایل موقت


def test_export_file_too_big_reports_4kb_cap(monkeypatch):
    _patch_client(monkeypatch, replies=[
        [["!done"]], [["!done"]],
        _size_rep(n=9000), _size_rep(n=9000), _size_rep(n=9000),
        [["!done"]],           # contents خالی برمی‌گردد (سقف ۴KB RouterOS)
    ])
    monkeypatch.setattr(backup_rsc, "_FILE_POLL_INTERVAL", 0)
    with pytest.raises(Exception) as ei:
        backup_rsc.export_config_via_api("10.0.0.2", "u", "p")
    m = str(ei.value)
    assert "خروجی /export خالی" in m and "۴ کیلوبایت" in m and "9000" in m


def test_export_direct_trap_still_tries_file_method(monkeypatch):
    trap = [["!trap", "=message=bad command name export"]]
    cont = [["!re", "=contents=# cfg6"], ["!done"]]
    _patch_client(monkeypatch, replies=[
        trap, [["!done"]], _size_rep(), _size_rep(), _size_rep(), cont,
    ])
    monkeypatch.setattr(backup_rsc, "_FILE_POLL_INTERVAL", 0)
    text = backup_rsc.export_config_via_api("10.0.0.2", "u", "p")
    assert text == "# cfg6"


def test_export_file_cmd_trap_mentions_write_policy(monkeypatch):
    trap = [["!trap", "=message=failure: permission denied"]]
    _patch_client(monkeypatch, replies=[[["!done"]], trap])
    monkeypatch.setattr(backup_rsc, "_FILE_POLL_INTERVAL", 0)
    with pytest.raises(Exception) as ei:
        backup_rsc.export_config_via_api("10.0.0.2", "u", "p")
    m = str(ei.value)
    assert "read,write,api" in m and "permission denied" in m


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
                        lambda host, port=8728, timeout=20.0, **kw: _FakeClient(host, port, timeout, [["!done", "=ret=# cfg\n"]]))
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


# ------------------------- Task 36: عیب‌یابی + تغییر نام پوشه ---------------
def test_friendly_error_connect_refused():
    msg = backup_rsc._friendly_error(ConnectionRefusedError("connection refused"), "connect")
    assert "سرویس API" in msg and "8728" in msg and "connection refused" in msg
    assert "enable api" in msg  # راهنمای رفع


def test_friendly_error_connect_timeout_firewall():
    msg = backup_rsc._friendly_error(TimeoutError("timed out"), "connect")
    assert "فایروال" in msg and "Winbox" in msg and "timed out" in msg


def test_friendly_error_read_timeout_slow_export():
    msg = backup_rsc._friendly_error(TimeoutError("timed out"), "read")
    assert "export بیش از حد طول کشید" in msg and "timed out" in msg


def test_friendly_error_login_hint():
    msg = backup_rsc._friendly_error(backup_rsc._ros.RouterOSError("cannot log in"), "login")
    assert "ورود API ناموفق" in msg and "policy" in msg


def test_export_failure_classifies_stage(monkeypatch):
    """خطای اتصال باید با علت فارسیِ مرحلهٔ connect بالا بیاید (نه پیام خام)."""
    class _TimeoutClient:
        def __init__(self, host, port=8728, timeout=20.0, **kw):
            self.closed = False

        def connect(self):
            raise TimeoutError("timed out")

        def close(self):
            self.closed = True

    monkeypatch.setattr(backup_rsc, "_ros", local_ros)
    monkeypatch.setattr(local_ros, "RouterOSClient", _TimeoutClient)
    with pytest.raises(Exception) as ei:
        backup_rsc.export_config_via_api("10.0.0.2", "u", "p")
    assert "سرویس api فعال نیست یا فایروال" in str(ei.value)


def test_export_uses_fast_connect_timeout(monkeypatch):
    """اتصال اولیه نباید به اندازهٔ timeout خواندن (≥۹۰s) منتظر بماند — سقف ۱۲ ثانیه."""
    seen = {}

    class _ProbeClient:
        def __init__(self, host, port=8728, timeout=20.0, connect_timeout=None):
            seen["read"], seen["connect"] = timeout, connect_timeout

        def connect(self):
            pass

        def login(self, u, p):
            pass

        def talk(self, words, timeout=None):
            return [["!done", "=ret=# ok\n"]]

        def close(self):
            pass

    monkeypatch.setattr(backup_rsc, "_ros", local_ros)
    monkeypatch.setattr(local_ros, "RouterOSClient", _ProbeClient)
    backup_rsc.export_config_via_api("10.0.0.2", "u", "p", timeout=5)
    assert seen["read"] >= backup_rsc.EXPORT_MIN_TIMEOUT
    assert seen["connect"] == backup_rsc.CONNECT_TIMEOUT_CAP
    assert seen["connect"] < seen["read"]


def test_migrate_old_backup_folder_rename(monkeypatch, tmp_path):
    """backup/ قدیمی → mik_backup/ (تغییر نام یک‌جا وقتی مقصد نیست)."""
    old_root = tmp_path / "app"
    (old_root / "backup").mkdir(parents=True)
    (old_root / "backup" / "A_10.0.0.2.rsc").write_text("# a\n", encoding="utf-8")
    new_dir = old_root / "mik_backup"
    monkeypatch.setattr(backup_rsc, "ROOT_DIR", old_root)
    monkeypatch.setattr(backup_rsc, "BACKUP_DIR", new_dir)
    backup_rsc._migrate_old_backup_folder()
    assert not (old_root / "backup").exists()  # پوشهٔ قدیمی جابه‌جا شد
    assert (new_dir / "A_10.0.0.2.rsc").read_text(encoding="utf-8") == "# a\n"


def test_migrate_old_backup_folder_merge(monkeypatch, tmp_path):
    """اگر هر دو پوشه باشند: فقط rscهای تکراری‌نشدنی منتقل می‌شوند، مقصد دست‌نخورده."""
    old_root = tmp_path / "app"
    (old_root / "backup").mkdir(parents=True)
    (old_root / "backup" / "OLD_1.1.1.1.rsc").write_text("# old\n", encoding="utf-8")
    new_dir = old_root / "mik_backup"
    new_dir.mkdir()
    (new_dir / "NEW_2.2.2.2.rsc").write_text("# new\n", encoding="utf-8")
    monkeypatch.setattr(backup_rsc, "ROOT_DIR", old_root)
    monkeypatch.setattr(backup_rsc, "BACKUP_DIR", new_dir)
    backup_rsc._migrate_old_backup_folder()
    assert (new_dir / "OLD_1.1.1.1.rsc").exists()
    assert (new_dir / "NEW_2.2.2.2.rsc").read_text(encoding="utf-8") == "# new\n"
    assert (old_root / "backup").exists()  # پوشهٔ قدیمی پاک نمی‌شود


def test_default_backup_dir_is_mik_backup():
    """نام جدید پوشه در ریشهٔ برنامه (Task 36) — و اگر backup/ قدیمی بود، منتقل شده."""
    assert backup_rsc.BACKUP_DIR.name == "mik_backup"
    assert backup_rsc.BACKUP_DIR.is_dir()


# ------------------ Task 37: ورود با اتصال تازه + لاگ خطا -------------------
def test_login_fallback_uses_fresh_connection(monkeypatch):
    """ورود مستقیم (6) داد → چالش-پاسخ باید روی اتصال تازه امتحان شود (ROS قدیمی)."""
    cli = local_ros.RouterOSClient("10.0.0.2")
    seq = {"n": 0}
    reconnects = {"n": 0}

    def fake_talk(words, timeout=None):
        seq["n"] += 1
        if seq["n"] == 1:  # ورود مستقیم v6.43+ → رد (6) — حتی با رمز درست
            return [["!trap", "=message=invalid user name or password (6)"]]
        if seq["n"] == 2:  # bare /login روی اتصال تازه → چالش
            return [["!done", "=ret=" + "aa00" * 7]]
        return [["!done"]]  # پاسخ چالش → ok

    monkeypatch.setattr(cli, "talk", fake_talk)
    monkeypatch.setattr(cli, "connect", lambda: reconnects.__setitem__("n", reconnects["n"] + 1))
    monkeypatch.setattr(cli, "close", lambda: None)
    cli.login("garmaf", "secret")  # باید با روش قدیم روی اتصال تازه موفق شود
    assert reconnects["n"] == 1  # تلاش دوم روی اتصالِ تازه — نه همان سوکت مرده


def test_login_failure_reports_router_message(monkeypatch):
    """هر دو روش رد شد → پیام خام روتر (نمونه: (6)) + نتیجهٔ روش دوم حفظ شود."""
    cli = local_ros.RouterOSClient("10.0.0.2")
    calls = {"n": 0}

    def fake_talk(words, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return [["!trap", "=message=invalid user name or password (6)"]]
        return [["!done"]]  # ROS جدید: bare /login بدون =ret=

    monkeypatch.setattr(cli, "talk", fake_talk)
    monkeypatch.setattr(cli, "connect", lambda: None)
    monkeypatch.setattr(cli, "close", lambda: None)
    with pytest.raises(Exception) as ei:
        cli.login("garmaf", "wrong")
    assert "invalid user name or password (6)" in str(ei.value)


def test_backup_failure_logged_to_errorlog(monkeypatch, backup_dir, tmp_path):
    """خطای هر دستگاه + خلاصهٔ پایان کار در mik_log/errorlog.jsonl ثبت می‌شود (Task 37)."""
    import json as _json
    log_file = tmp_path / "errorlog.jsonl"
    cfg_file = tmp_path / "config.json"
    monkeypatch.setattr(backup_rsc._errorlog, "LOG_FILE", log_file)
    monkeypatch.setattr(backup_rsc._errorlog, "CONFIG_FILE", cfg_file)
    _patch_client(monkeypatch, fail="connection refused")
    rows = backup_rsc.backup_devices([_dev("10.9.9.9", "X-MK", 5)], "u", "p")
    assert not rows[0]["ok"]
    entries = [_json.loads(l) for l in log_file.read_text("utf-8").splitlines() if l.strip()]
    per_dev = [e for e in entries if e["ip"] == "10.9.9.9"]
    summary = [e for e in entries if "پایان یافت" in e["message"]]
    assert per_dev and per_dev[0]["source"] == "backup-rsc" and "connection refused" in per_dev[0]["message"]
    assert summary and summary[0]["source"] == "backup-rsc"


def test_errorlog_disabled_skips_logging(monkeypatch, backup_dir, tmp_path):
    import json as _json
    log_file = tmp_path / "errorlog.jsonl"
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(_json.dumps({"enabled": False}), "utf-8")
    monkeypatch.setattr(backup_rsc._errorlog, "LOG_FILE", log_file)
    monkeypatch.setattr(backup_rsc._errorlog, "CONFIG_FILE", cfg_file)
    _patch_client(monkeypatch, fail="connection refused")
    backup_rsc.backup_devices([_dev("10.9.9.9", "X-MK", 5)], "u", "p")
    assert not log_file.exists()  # ثبت خاموش → لاگ نوشته نمی‌شود


# ------------------ Task 37: endpointهای لاگ خطا ----------------------------
def test_errorlog_endpoints_roundtrip(client, monkeypatch, tmp_path):
    import backend.errorlog as _elog
    monkeypatch.setattr(_elog, "LOG_FILE", tmp_path / "errorlog.jsonl")
    monkeypatch.setattr(_elog, "CONFIG_FILE", tmp_path / "config.json")
    r = client.get("/api/errorlog")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["enabled"] is True and d["entries"] == [] and d["count"] == 0
    r = client.post("/api/errorlog/toggle", json={"enabled": False})
    assert r.status_code == 200 and r.json()["enabled"] is False
    assert client.get("/api/errorlog").json()["enabled"] is False
    # ثبت غیرفعال → خطا لاگ نمی‌شود؛ فعال‌سازی → ثبت و خواندن
    _elog.log_error(source="backup-rsc", ip="10.0.0.2", message="خطای آزمایشی")
    assert client.get("/api/errorlog").json()["entries"] == []
    client.post("/api/errorlog/toggle", json={"enabled": True})
    _elog.log_error(source="backup-rsc", ip="10.0.0.2", message="خطای آزمایشی")
    d = client.get("/api/errorlog").json()
    assert d["count"] == 1 and d["entries"][0]["message"] == "خطای آزمایشی"
    r = client.post("/api/errorlog/clear")
    assert r.status_code == 200
    assert client.get("/api/errorlog").json()["count"] == 0
