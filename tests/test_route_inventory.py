"""Task 25 — اینونتوری IP اینترفیس‌ها + ای‌دی دستگاه در دیتابیس و پردازش گزارش مسیر از روی دیتابیس.

پوشش:
1) جدول device_interface_ips ساخته می‌شود؛ replace/load رفتار «جایگزینی در سطح
   هر دستگاه» دارد (دستگاهی که ردیف تازه ندارد، ردیف‌های قبلی‌اش می‌ماند)
2) inventory_rows_from_infos — device_id/identity/interface/ip-بدون-ماسک/network
   و صرف‌نظر از دستگاه خوانده‌نشده یا بی‌آدرس (تا دادهٔ قبلی پاک نشود)
3) build_topology(inventory=...) — مالکیت گیت‌وی برای دستگاهِ خوانده‌نشدهٔ همین
   اجرا از دیتابیس درمی‌آید (یال به دستگاه واقعی به‌جای گرهٔ شبح) و گره‌های شبح
   با identity ثبت‌شده در دیتابیس نام‌گذاری می‌شوند
4) delete_devices ردیف‌های اینونتوری دستگاه حذف‌شده را هم پاک می‌کند
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import db as dbm
import route_topology as rt


def _tmp_db(tmp_path):
    p = str(tmp_path / "inv_test.db")
    dbm.init_db(p)
    return p


def _info(ip, identity, addresses, routes=(), ifaces=(), ok_=True, error=None):
    return {"ip": ip, "ok": ok_, "error": (error if error is not None else (None if ok_ else "timeout")),
            "identity": identity, "resource": {"version": "7.14"} if ok_ else {},
            "interfaces": list(ifaces), "addresses": list(addresses),
            "neighbors": [], "routes": list(routes), "arp": []}


def _dev(ip, name, dev_id):
    return {"id": dev_id, "ip": ip, "device_name": name, "tags": "t", "ping_ok": True,
            "open_ports": [8728], "device_type": "Router"}


def _if(n, run="true", dis="false"):
    return {"name": n, "type": "ether", "running": run, "disabled": dis, "mac_address": "", "comment": ""}


# ---------------------------------------------------------------------------
def test_table_created_and_roundtrip(tmp_path):
    p = _tmp_db(tmp_path)
    rows = [
        {"device_ip": "10.0.0.2", "device_id": 11, "identity": "A-MK",
         "interface": "ether1", "address": "10.0.0.2/24", "ip": "10.0.0.2", "network": "10.0.0.0"},
        {"device_ip": "10.0.0.2", "device_id": 11, "identity": "A-MK",
         "interface": "ether2", "address": "10.9.0.1/24", "ip": "10.9.0.1", "network": "10.9.0.0"},
        {"device_ip": "10.0.0.3", "device_id": 12, "identity": "B-MK",
         "interface": "ether5", "address": "10.8.0.1/30", "ip": "10.8.0.1", "network": "10.8.0.0"},
    ]
    saved = dbm.replace_interface_inventory(rows, db_path=p)
    assert saved == {"devices": 2, "rows": 3}, saved
    loaded = dbm.load_interface_inventory(p)
    assert len(loaded) == 3
    a1 = [r for r in loaded if r["ip"] == "10.9.0.1"][0]
    assert a1["device_ip"] == "10.0.0.2" and a1["device_id"] == 11
    assert a1["identity"] == "A-MK" and a1["interface"] == "ether2"
    assert a1["address"] == "10.0.0.2/24".replace("10.0.0.2", "10.9.0.1")  # address با ماسک
    assert a1["address"] == "10.9.0.1/24" and a1["network"] == "10.9.0.0"
    assert a1["updated_at"]  # مهر زمانی ذخیره


def test_replace_is_per_device(tmp_path):
    """جایگزینی فقط در سطح device_ip است — دستگاه بدون ردیف تازه، دادهٔ قبلی دارد."""
    p = _tmp_db(tmp_path)
    dbm.replace_interface_inventory([
        {"device_ip": "10.0.0.2", "device_id": 11, "identity": "A-MK", "interface": "e1",
         "address": "10.0.0.2/24", "ip": "10.0.0.2", "network": "10.0.0.0"},
        {"device_ip": "10.0.0.3", "device_id": 12, "identity": "B-MK", "interface": "e5",
         "address": "10.8.0.1/30", "ip": "10.8.0.1", "network": "10.8.0.0"},
    ], db_path=p)
    # اجرای بعدی: فقط A تازه خوانده شده؛ B نبوده است
    dbm.replace_interface_inventory([
        {"device_ip": "10.0.0.2", "device_id": 11, "identity": "A-MK", "interface": "e9",
         "address": "10.7.0.2/24", "ip": "10.7.0.2", "network": "10.7.0.0"},
    ], db_path=p)
    loaded = {r["device_ip"]: r for r in dbm.load_interface_inventory(p)}
    assert loaded["10.0.0.2"]["ip"] == "10.7.0.2"          # A جایگزین شد
    assert loaded["10.0.0.3"]["ip"] == "10.8.0.1"          # B دست‌نخورده ماند
    assert len(loaded) == 2


def test_rows_from_infos_mapping():
    infos = [
        _info("10.0.0.2", "A-MK", [
            {"address": "10.0.0.2/24", "interface": "ether1", "network": "10.0.0.0"},
            {"address": "10.9.0.1/24", "interface": "ether2", "network": "10.9.0.0"}]),
        _info("10.0.0.3", "", [], ok_=False, error="timeout"),   # خوانده نشد
        _info("10.0.0.4", "C-MK", []),                            # خوانده شد ولی بی‌آدرس
    ]
    devices = [_dev("10.0.0.2", "A-MK", 21), _dev("10.0.0.3", "B-MK", 22), _dev("10.0.0.4", "C-MK", 23)]
    rows = rt.inventory_rows_from_infos(infos, devices)
    assert len(rows) == 2, rows  # فقط دستگاه سالمِ دارای آدرس
    r1, r2 = rows
    assert (r1["device_ip"], r1["device_id"], r1["identity"]) == ("10.0.0.2", 21, "A-MK")
    assert r1["interface"] == "ether1" and r1["address"] == "10.0.0.2/24"
    assert r1["ip"] == "10.0.0.2" and r1["network"] == "10.0.0.0"
    assert r2["ip"] == "10.9.0.1" and r2["interface"] == "ether2"
    assert rt.inventory_rows_from_infos([], devices) == []
    assert rt.inventory_rows_from_infos(infos, []) [0]["device_id"] is None


def test_ownership_of_failed_device_comes_from_inventory():
    """دستگاه B در اجرای جاری خوانده نشده؛ مالکیت گیت‌وی A از اینونتوری دیتابیس درمی‌آید."""
    info_a = _info("10.40.1.10", "A-MK",
                   [{"address": "10.40.1.10/24", "interface": "ether1", "network": "10.40.1.0"}],
                   routes=[{"dst_address": "0.0.0.0/0", "gateway": "10.40.4.254", "distance": "1"}])
    info_b = _info("10.40.2.1", "", [], ok_=False, error="timeout")
    info_d = _info("10.40.4.10", "D-MK",
                   [{"address": "10.40.4.10/24", "interface": "ether1", "network": "10.40.4.0"}],
                   routes=[{"dst_address": "0.0.0.0/0", "gateway": "10.40.4.254", "distance": "1"}])
    devices = [_dev("10.40.1.10", "A-MK", 1), _dev("10.40.2.1", "B-MK", 2), _dev("10.40.4.10", "D-MK", 4)]
    inventory = [
        # B خوانده‌نشده — اینونتوری قبلی‌اش در دیتابیس است: IP گیت‌ویِ D مالِ B است
        {"device_ip": "10.40.2.1", "device_id": 2, "identity": "B-MK", "interface": "ether5",
         "address": "10.40.4.254/24", "ip": "10.40.4.254", "network": "10.40.4.0"},
    ]
    topo = rt.build_topology([info_a, info_b, info_d], devices, "172.19.1.6", inventory=inventory)
    # یال D→B از طریق مالکیت دیتابیسی ساخته شده (نه گرهٔ شبح)
    ab = [(e["a"], e["b"]) for e in topo["edges"]]
    assert ("d:10.40.4.10", "d:10.40.2.1") in ab or ("d:10.40.2.1", "d:10.40.4.10") in ab, ab
    assert ("g:10.40.4.254") not in topo["nodes"], "با اینونتوری، گیت‌وی نباید شبح بماند"
    # مسیر A: گیت‌وی‌اش (10.40.4.254) هم مالِ B است → یال A→B
    assert ("d:10.40.1.10", "d:10.40.2.1") in ab or ("d:10.40.2.1", "d:10.40.1.10") in ab, ab
    # بدون اینونتوری همان سناریو شبح می‌سازد (رفتار قبلی)
    topo0 = rt.build_topology([info_a, info_b, info_d], devices, "172.19.1.6")
    assert "g:10.40.4.254" in topo0["nodes"]


def test_ghost_named_from_inventory_identity():
    info_a = _info("10.40.1.10", "A-MK",
                   [{"address": "10.40.1.10/24", "interface": "ether1", "network": "10.40.1.0"}],
                   routes=[{"dst_address": "0.0.0.0/0", "gateway": "10.40.1.254", "distance": "1"}],
                   ifaces=[_if("ether1")])
    devices = [_dev("10.40.1.10", "A-MK", 1)]
    inventory = [
        # دستگاهی خارج از انتخاب این اجرا؛ IP گیت‌ویِ A قبلاً برایش ثبت شده
        {"device_ip": "9.9.9.77", "device_id": 321, "identity": "Up-Core-MK", "interface": "ether1",
         "address": "10.40.1.254/24", "ip": "10.40.1.254", "network": "10.40.1.0"},
    ]
    topo = rt.build_topology([info_a], devices, "172.19.1.6", inventory=inventory)
    g = topo["nodes"]["g:10.40.1.254"]
    assert g["name"] == "Up-Core-MK", g
    assert g.get("from_inventory") is True and g.get("inventory_dev_id") == 321
    # بدون اینونتوری: نام شبح همان IP است
    topo0 = rt.build_topology([info_a], devices, "172.19.1.6")
    assert topo0["nodes"]["g:10.40.1.254"]["name"] == "10.40.1.254"
    # دلیل نرسیدن A به شبحِ نام‌دار اشاره می‌کند
    rows = {r["ip"]: r for r in rt.unreachable_reason_rows(topo)}
    assert "10.40.1.254" in rows["10.40.1.10"]["reason"]


def test_delete_devices_cleans_inventory(tmp_path):
    p = _tmp_db(tmp_path)
    dbm.replace_interface_inventory([
        {"device_ip": "10.0.0.2", "device_id": 11, "identity": "A-MK", "interface": "e1",
         "address": "10.0.0.2/24", "ip": "10.0.0.2", "network": "10.0.0.0"},
        {"device_ip": "10.0.0.3", "device_id": 12, "identity": "B-MK", "interface": "e5",
         "address": "10.8.0.1/30", "ip": "10.8.0.1", "network": "10.8.0.0"},
    ], db_path=p)
    with sqlite3.connect(p):
        pass
    dbm.delete_devices(["10.0.0.2"], db_path=p)
    loaded = dbm.load_interface_inventory(p)
    assert [r["device_ip"] for r in loaded] == ["10.0.0.3"], loaded


def test_inventory_does_not_break_graph_without_rows(tmp_path):
    """inventory خالی/None → رفتار کاملاً مثل قبل (سازگاری رو به عقب)."""
    info_a = _info("10.0.0.2", "A-MK",
                   [{"address": "10.0.0.2/24", "interface": "ether1", "network": "10.0.0.0"}],
                   routes=[{"dst_address": "0.0.0.0/0", "gateway": "10.0.0.1", "distance": "1"}])
    topo = rt.build_topology([info_a], [_dev("10.0.0.2", "A-MK", 1)], "172.19.1.6", inventory=[])
    assert "g:10.0.0.1" in topo["nodes"]
    assert topo["summary"]["devices"] == 1
