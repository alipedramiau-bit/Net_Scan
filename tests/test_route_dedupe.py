"""Task 33 — حذف گزارش تکراری دستگاه‌ها در «ایجاد گزارش مسیر (PDF)».

درخواست کاربر: «دستگاه‌هایی که گزارش آن‌ها تولید شده با در نظر گرفتن نام یا
ای‌دی دستگاه‌ها در گزارش به‌صورت تکراری تولید نکن» — یعنی در انتخاب هدف‌های
گزارش مسیر، هر دستگاه فقط یک‌بار بیاید؛ کلیدهای تکراریت:
  * IP اتصال (رفتار قبلی)؛
  * ای‌دی ردیف دیتابیس (device_id)؛
  * نام دستگاه (device_name — بدون تفاوت حروف بزرگ/کوچک)؛ ردیف بی‌نام از
    identity ثبت‌شدهٔ اینونتوری اینترفیس‌ها (Task 25) نام می‌گیرد.
نخستین ردیفِ هر دستگاه گزارش می‌شود و تعداد ردیف‌های تکراریِ حذف‌شده
برگردانده می‌شود (برای نمایش در پیام شروع گزارش).

لایهٔ دیتابیس با monkeypatch جایگزین شده — هیچ دیتابیس واقعی‌ای لمس نمی‌شود.
"""
import pytest

from backend import db as dbm
from backend.main import _select_topology_targets


def _dev(ip, name, dev_id, mk=True):
    return {"id": dev_id, "ip": ip, "device_name": name, "tags": "",
            "ping_ok": True, "device_type": "Router",
            "classification": "mikrotik_candidate" if mk else "non_mikrotik",
            "open_ports": [8291, 8728] if mk else []}


def _inv(device_ip, identity):
    return {"device_ip": device_ip, "identity": identity}


@pytest.fixture()
def patch_db(monkeypatch):
    """دیتابیس ساختگی: ردیف‌ها/اینونتوری از متغیرهای تست خوانده می‌شود."""
    state = {"rows": [], "inventory": []}

    def fake_fetch(ips, db_path=None):
        want = {str(x).strip() for x in ips or []}
        return [d for d in state["rows"] if d["ip"] in want]

    def fake_query(limit=500, db_path=None, **kw):
        return {"devices": list(state["rows"]), "count": len(state["rows"])}

    def fake_inventory(db_path=None):
        return list(state["inventory"])

    monkeypatch.setattr(dbm, "fetch_devices_by_ips", fake_fetch)
    monkeypatch.setattr(dbm, "query_devices", fake_query)
    monkeypatch.setattr(dbm, "load_interface_inventory", fake_inventory)
    return state


# ---------------------------------------------------------------------------
def test_same_name_two_ips_reported_once(patch_db):
    """یک دستگاه با دو IP (دو ردیف هم‌نام) → فقط نخستین ردیف گزارش می‌شود."""
    patch_db["rows"] = [
        _dev("10.0.0.2", "CORE-SW", 1),
        _dev("10.0.0.9", "CORE-SW", 2),   # همان دستگاه، IP دوم
    ]
    targets, skipped = _select_topology_targets("", [], 80)
    assert [t["ip"] for t in targets] == ["10.0.0.2"]
    assert skipped == 1


def test_same_device_id_reported_once(patch_db):
    """کلید «ای‌دی دستگاه»: دو ردیف با ای‌دی یکسان → فقط نخستین ردیف."""
    patch_db["rows"] = [
        _dev("10.0.0.2", "A-MK", 7),
        _dev("10.0.1.2", "B-MK", 7),      # همان ردیف دیتابیس با IP دیگر
    ]
    targets, skipped = _select_topology_targets("", [], 80)
    assert [t["ip"] for t in targets] == ["10.0.0.2"]
    assert skipped == 1


def test_same_ip_reported_once_regression(patch_db):
    """رفتار قبلی حفظ می‌شود: IP تکراری حذف می‌شود."""
    patch_db["rows"] = [
        _dev("10.0.0.2", "A-MK", 1),
        _dev("10.0.0.2", "A-MK", 1),
    ]
    targets, skipped = _select_topology_targets("", [], 80)
    assert [t["ip"] for t in targets] == ["10.0.0.2"]
    assert skipped == 1


def test_name_case_insensitive(patch_db):
    """نام بدون تفاوت حروف بزرگ/کوچک یکسان است (core-sw == Core-SW)."""
    patch_db["rows"] = [
        _dev("10.0.0.2", "core-sw", 1),
        _dev("10.0.0.3", "Core-SW", 2),
    ]
    targets, skipped = _select_topology_targets("", [], 80)
    assert [t["ip"] for t in targets] == ["10.0.0.2"]
    assert skipped == 1


def test_inventory_identity_fallback_for_unnamed_rows(patch_db):
    """ردیف بی‌نام: identity ثبت‌شدهٔ اینونتوری به‌عنوان نام استفاده می‌شود."""
    patch_db["rows"] = [
        _dev("10.0.0.2", "", 1),
        _dev("10.0.0.3", "", 2),          # اینونتوری: هر دو MK-UP هستند
        _dev("10.0.0.4", "", 3),          # اینونتوری: MK-DOWN — جدا می‌ماند
    ]
    patch_db["inventory"] = [
        _inv("10.0.0.2", "MK-UP"),
        _inv("10.0.0.3", "MK-UP"),
        _inv("10.0.0.4", "MK-DOWN"),
    ]
    targets, skipped = _select_topology_targets("", [], 80)
    assert [t["ip"] for t in targets] == ["10.0.0.2", "10.0.0.4"]
    assert skipped == 1


def test_device_name_wins_over_inventory_identity(patch_db):
    """وقتی ردیف نام دارد، نام ردیف ملاک است (نه identity اینونتوری)."""
    patch_db["rows"] = [
        _dev("10.0.0.2", "X-MK", 1),
        _dev("10.0.0.3", "", 2),
    ]
    patch_db["inventory"] = [_inv("10.0.0.3", "X-MK")]
    targets, skipped = _select_topology_targets("", [], 80)
    assert [t["ip"] for t in targets] == ["10.0.0.2"]
    assert skipped == 1


def test_unnamed_rows_without_inventory_stay(patch_db):
    """ردیف بی‌نام بدون اینونتوری: کلید مشترکی نیست → حذف نمی‌شود."""
    patch_db["rows"] = [_dev("10.0.0.2", "", 1), _dev("10.0.0.3", "", 2)]
    targets, skipped = _select_topology_targets("", [], 80)
    assert [t["ip"] for t in targets] == ["10.0.0.2", "10.0.0.3"]
    assert skipped == 0


def test_non_mikrotik_excluded_and_not_counted_as_duplicate(patch_db):
    """دستگاه غیرمیکروتیک همان‌نام، تکراری حساب نمی‌شود (خودش حذف می‌شود)."""
    patch_db["rows"] = [
        _dev("10.0.0.2", "PRN-1", 1),
        _dev("10.0.0.3", "PRN-1", 2, mk=False),  # پرینتر هم‌نام
    ]
    targets, skipped = _select_topology_targets("", [], 80)
    assert [t["ip"] for t in targets] == ["10.0.0.2"]
    assert skipped == 0


def test_empty_ip_dropped_without_counting(patch_db):
    patch_db["rows"] = [_dev("", "NO-IP", 1), _dev("10.0.0.2", "A-MK", 2)]
    targets, skipped = _select_topology_targets("", [], 80)
    assert [t["ip"] for t in targets] == ["10.0.0.2"]
    assert skipped == 0


def test_max_devices_counts_unique_devices_only(patch_db):
    """سقف تعداد روی دستگاه‌های یکتا اعمال می‌شود؛ تکراری‌ها جا نمی‌گیرند."""
    patch_db["rows"] = [
        _dev("10.0.0.2", "A-MK", 1),
        _dev("10.0.0.9", "A-MK", 2),   # تکراری — حتی قبل از سقف هم حذف می‌شود
        _dev("10.0.0.3", "B-MK", 3),
        _dev("10.0.0.4", "C-MK", 4),
    ]
    targets, skipped = _select_topology_targets("", [], 2)
    assert [t["ip"] for t in targets] == ["10.0.0.2", "10.0.0.3"]
    assert skipped == 1


def test_explicit_ips_selection_dedupes(patch_db):
    """انتخاب دستی (ips) هم همان حذف تکراری را دارد."""
    patch_db["rows"] = [
        _dev("10.0.0.2", "CORE-SW", 1),
        _dev("10.0.0.9", "CORE-SW", 2),
        _dev("10.0.0.3", "EDGE-MK", 3),
    ]
    targets, skipped = _select_topology_targets("", ["10.0.0.9", "10.0.0.2", "10.0.0.3"], 80)
    assert [t["ip"] for t in targets] == ["10.0.0.2", "10.0.0.3"]  # ترتیب ردیف‌های دیتابیس
    assert skipped == 1


def test_distinct_devices_all_kept(patch_db):
    """دستگاه‌های واقعاً متفاوت (نام/ای‌دی/IP متمایز) همگی گزارش می‌شوند."""
    patch_db["rows"] = [
        _dev("10.0.0.2", "A-MK", 1),
        _dev("10.0.0.3", "B-MK", 2),
        _dev("10.0.0.4", "C-MK", 3),
    ]
    targets, skipped = _select_topology_targets("", [], 80)
    assert [t["ip"] for t in targets] == ["10.0.0.2", "10.0.0.3", "10.0.0.4"]
    assert skipped == 0
