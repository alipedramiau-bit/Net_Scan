"""Task 27 — دستگاه همسایهٔ متصل به اینترفیس flapشده در گزارش هوشمند.

هر رویداد flap باید «نام دستگاه همسایه» و «IP دستگاه همسایه» داشته باشد:
۱) از ردیف‌های /ip neighbor (LLDP/MNDP) خودِ دستگاه — دقیق و اولویت اول؛
۲) fallback: هم‌سابنتی بودن از روی اینونتوری IP اینترفیس‌ها (Task 25) یا
   متن /ip address ذخیره‌شده.
"""
import csv
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend import smart_reports as sr


def _flap_log(iface="ether2"):
    return (
        f"Oct/20 08:00:01 {iface} link up\n"
        f"Oct/20 08:00:03 {iface} link down\n"
        f"Oct/20 08:00:05 {iface} link up\n"
        f"Oct/20 08:00:07 {iface} link down\n"
        f"Oct/20 08:00:09 {iface} link up"
    )


NOW = sr.datetime(2026, 10, 23, 12, 0, 0)


class ParseNeighborEntriesTests(unittest.TestCase):
    def test_compact_format_from_collect_device_info(self):
        text = ("=== /ip neighbor ===\n"
                "  1  identity=Core-SW  address=10.10.10.2  interface=ether2\n"
                "  2  identity=Repeater-C  address=10.50.0.7  interface=ether4")
        entries = sr.parse_neighbor_entries(text)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["interface"], "ether2")
        self.assertEqual(entries[0]["identity"], "Core-SW")
        self.assertEqual(entries[0]["address"], "10.10.10.2")
        self.assertEqual(entries[1]["interface"], "ether4")

    def test_sentence_format_from_collect_ip_info(self):
        text = ("=== /ip neighbor ===\n"
                "  interface=ether2  mac-address=AA:BB:CC:DD:EE:FF  address=10.10.10.2  "
                "identity=Core-SW  board-name=CCR2004-1G-12S+2XS  uptime=3w1d2h")
        entries = sr.parse_neighbor_entries(text)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["interface"], "ether2")
        self.assertEqual(entries[0]["identity"], "Core-SW")
        self.assertEqual(entries[0]["address"], "10.10.10.2")
        self.assertEqual(entries[0]["mac"], "AA:BB:CC:DD:EE:FF")

    def test_lines_without_interface_are_skipped(self):
        text = "=== /ip route ===\n  1  dst=0.0.0.0/0  gw=10.0.0.254  distance=1"
        self.assertEqual(sr.parse_neighbor_entries(text), [])


class LldpNeighborResolutionTests(unittest.TestCase):
    def _devices(self):
        return [
            {"ip": "10.10.10.1", "device_name": "Shadegan-Jafal1", "device_log": _flap_log("ether2"),
             "ip_neighbors": "=== /ip neighbor ===\n"
                             "  1  identity=SW-Core-MK  address=10.10.10.2  interface=ether2",
             "ip_addresses": "=== /ip address ===\n"
                             "  1  address=10.10.10.1/24  interface=ether2  network=10.10.10.0"},
            {"ip": "10.10.10.2", "device_name": "SW-Core-MK", "device_log": "", "ip_neighbors": "", "ip_addresses": ""},
        ]

    def test_known_lldp_neighbor_resolved(self):
        report = sr.interface_flap_report(self._devices(), days_back=5, now=NOW)
        event = report["events"][0]
        self.assertEqual(event["neighbor_name"], "SW-Core-MK")
        self.assertEqual(event["neighbor_ip"], "10.10.10.2")
        self.assertEqual(event["neighbor_via"], "lldp")

    def test_unknown_lldp_neighbor_shows_raw_values(self):
        devices = self._devices()
        devices[0]["ip_neighbors"] = ("=== /ip neighbor ===\n"
                                      "  1  identity=Mystery-Box  address=172.16.5.9  interface=ether2")
        report = sr.interface_flap_report(devices, days_back=5, now=NOW)
        event = report["events"][0]
        self.assertEqual(event["neighbor_name"], "Mystery-Box")
        self.assertEqual(event["neighbor_ip"], "172.16.5.9")
        self.assertEqual(event["neighbor_via"], "lldp")

    def test_identity_match_without_address(self):
        devices = self._devices()
        devices[0]["ip_neighbors"] = ("=== /ip neighbor ===\n"
                                      "  1  identity=SW-Core-MK  interface=ether2")
        report = sr.interface_flap_report(devices, days_back=5, now=NOW)
        event = report["events"][0]
        self.assertEqual(event["neighbor_name"], "SW-Core-MK")
        self.assertEqual(event["neighbor_ip"], "10.10.10.2")

    def test_self_entries_are_skipped(self):
        devices = self._devices()
        devices[0]["ip_neighbors"] = ("=== /ip neighbor ===\n"
                                      "  1  identity=Shadegan-Jafal1  address=10.10.10.1  interface=ether2")
        report = sr.interface_flap_report(devices, days_back=5, now=NOW)
        event = report["events"][0]
        # خودِ دستگاه نباید به‌عنوان همسایه گزارش شود؛ همسایهٔ واقعی همان ساب‌نت
        # (SW-Core-MK با 10.10.10.2) از fallback اینونتوری پیدا می‌شود.
        self.assertNotEqual(event["neighbor_name"], "Shadegan-Jafal1")
        self.assertEqual(event["neighbor_name"], "SW-Core-MK")
        self.assertEqual(event["neighbor_ip"], "10.10.10.2")
        self.assertEqual(event["neighbor_via"], "subnet")


class SubnetFallbackTests(unittest.TestCase):
    def test_inventory_subnet_overlap_resolves_neighbor(self):
        devices = [
            {"ip": "10.10.10.1", "device_name": "Shadegan-Jafal1", "device_log": _flap_log("ether4"),
             "ip_neighbors": "", "ip_addresses": ""},
            {"ip": "10.50.0.7", "device_name": "Repeater-C", "device_log": "", "ip_neighbors": "",
             "ip_addresses": ""},
        ]
        inventory = [
            {"device_ip": "10.10.10.1", "device_id": 1, "identity": "Shadegan-Jafal1",
             "interface": "ether4", "address": "10.50.0.1/24", "ip": "10.50.0.1", "network": "10.50.0.0"},
            {"device_ip": "10.50.0.7", "device_id": 2, "identity": "Repeater-C",
             "interface": "wlan1", "address": "10.50.0.7/24", "ip": "10.50.0.7", "network": "10.50.0.0"},
        ]
        report = sr.interface_flap_report(devices, days_back=5, now=NOW, inventory_rows=inventory)
        event = report["events"][0]
        self.assertEqual(event["neighbor_name"], "Repeater-C")
        self.assertEqual(event["neighbor_ip"], "10.50.0.7")
        self.assertEqual(event["neighbor_via"], "subnet")

    def test_ip_address_text_is_a_fallback_source(self):
        devices = [
            {"ip": "10.10.10.1", "device_name": "Shadegan-Jafal1", "device_log": _flap_log("ether4"),
             "ip_neighbors": "",
             "ip_addresses": "=== /ip address ===\n"
                             "  2  address=10.50.0.1/24  interface=ether4  network=10.50.0.0"},
            {"ip": "10.50.0.7", "device_name": "Repeater-C", "device_log": "", "ip_neighbors": "",
             "ip_addresses": "=== /ip address ===\n"
                             "  1  address=10.50.0.7/24  interface=wlan1  network=10.50.0.0"},
        ]
        report = sr.interface_flap_report(devices, days_back=5, now=NOW, inventory_rows=[])
        event = report["events"][0]
        self.assertEqual(event["neighbor_name"], "Repeater-C")
        self.assertEqual(event["neighbor_ip"], "10.50.0.7")
        self.assertEqual(event["neighbor_via"], "subnet")

    def test_no_neighbor_anywhere(self):
        devices = [
            {"ip": "10.99.0.1", "device_name": "Lonely-RTR", "device_log": _flap_log("ether5"),
             "ip_neighbors": "", "ip_addresses": ""},
        ]
        report = sr.interface_flap_report(devices, days_back=5, now=NOW, inventory_rows=[])
        event = report["events"][0]
        self.assertEqual(event["neighbor_name"], "")
        self.assertEqual(event["neighbor_ip"], "")
        self.assertEqual(event["neighbor_via"], "")


class ExportColumnsTests(unittest.TestCase):
    def _report(self):
        devices = [
            {"ip": "10.10.10.1", "device_name": "Shadegan-Jafal1", "tags": "MPLS",
             "device_log": _flap_log("ether2"),
             "ip_neighbors": "=== /ip neighbor ===\n"
                             "  1  identity=SW-Core-MK  address=10.10.10.2  interface=ether2",
             "ip_addresses": ""},
        ]
        return sr.interface_flap_report(devices, days_back=5, now=NOW)

    def test_csv_contains_neighbor_columns_in_order(self):
        text = sr.interface_flaps_csv(self._report())
        self.assertTrue(text.startswith("\ufeff"))
        rows = list(csv.reader(io.StringIO(text.lstrip("\ufeff"))))
        header = rows[0]
        # Task 30: چیدمان قرینه — ستون‌ها از راست به چپ؛ در نمایش RTL ستون اول آرایه
        # راست‌ترین ستون است، پس آرایه همان ترتیب خواندن راست‌به‌چپ کاربر است:
        # نام دستگاه، آی‌پی دستگاه، اینترفیس، تعداد تکرار لاگ، نوع رویداد،
        # تاریخ و زمان (شمسی)، نام دستگاه همسایه، IP دستگاه همسایه
        self.assertEqual(header[0], "نام دستگاه")
        self.assertEqual(header[1], "آی‌پی دستگاه")
        self.assertEqual(header[2], "اینترفیس")
        self.assertEqual(header[3], "تعداد تکرار لاگ")
        self.assertEqual(header[4], "نوع رویداد")
        self.assertEqual(header[5], "تاریخ و زمان (شمسی)")
        self.assertEqual(header[6], "نام دستگاه همسایه")
        self.assertEqual(header[7], "IP دستگاه همسایه")
        self.assertEqual(len(header), 8)
        data = rows[1]
        self.assertEqual(data[0], "Shadegan-Jafal1")
        self.assertEqual(data[1], "10.10.10.1")
        self.assertEqual(data[2], "ether2")
        self.assertEqual(int(data[3]), 4)  # تعداد تکرار لاگ
        self.assertEqual(data[4], "Up")  # نوع رویداد
        self.assertRegex(data[5], r"^\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}$")  # شمسی
        self.assertEqual(data[6], "SW-Core-MK")
        self.assertEqual(data[7], "10.10.10.2")
        self.assertEqual(len(data), len(header))
        # ستون‌های حذف‌شده نباید باشند
        self.assertNotIn("ردیف", header)
        self.assertNotIn("تگ دستگاه", header)
        self.assertTrue(all("میلادی" not in col for col in header))

    def test_xlsx_contains_neighbor_columns(self):
        from openpyxl import load_workbook
        buf = sr.interface_flaps_xlsx(self._report())
        buf.seek(0)
        ws = load_workbook(buf).active
        header = [c.value for c in ws[1]]
        # Task 30: در شیت RTL اکسل هم همان ۸ ستون با همان ترتیب راست‌به‌چپ CSV
        self.assertEqual(header[0], "نام دستگاه")
        self.assertEqual(header[1], "آی‌پی دستگاه")
        self.assertEqual(header[2], "اینترفیس")
        self.assertEqual(header[3], "تعداد تکرار لاگ")
        self.assertEqual(header[4], "نوع رویداد")
        self.assertEqual(header[5], "تاریخ و زمان (شمسی)")
        self.assertEqual(header[6], "نام دستگاه همسایه")
        self.assertEqual(header[7], "IP دستگاه همسایه")
        self.assertEqual(len(header), 8)
        row2 = [c.value for c in ws[2]]
        self.assertEqual(row2[0], "Shadegan-Jafal1")
        self.assertEqual(row2[1], "10.10.10.1")
        self.assertEqual(row2[2], "ether2")
        self.assertEqual(row2[6], "SW-Core-MK")
        self.assertEqual(row2[7], "10.10.10.2")


class InterfaceSpecificNeighborTests(unittest.TestCase):
    """Task 30 — نام/IP دستگاه همسایه فقط مختص همین اینترفیس flapدار."""

    def _devices(self, extra_iface_addr=""):
        lldp = ("=== /ip neighbor ===\n"
                "  1  identity=SW-Core-MK  address=10.10.10.2  interface=ether2")
        ip_addresses = ("=== /ip address ===\n"
                        "  1  address=10.10.10.1/24  interface=ether2  network=10.10.10.0\n"
                        + extra_iface_addr)
        return [
            {"ip": "10.10.10.1", "device_name": "Shadegan-Jafal1", "device_log": _flap_log("ether5"),
             "ip_neighbors": lldp, "ip_addresses": ip_addresses},
            {"ip": "10.10.10.2", "device_name": "SW-Core-MK", "device_log": "",
             "ip_neighbors": "", "ip_addresses": ""},
        ]

    def test_neighbor_pinned_to_other_interface_does_not_leak(self):
        # ether5 هم‌سابنتِ ether2 است (10.10.10.5/25 ← شبکهٔ 10.10.10.0/25 که
        # 10.10.10.2 هم داخلش است) ولی LLDP خودِ دستگاه، SW-Core-MK را فقط به
        # ether2 قفل کرده — پس نباید همسایهٔ ether5 گزارش شود.
        devices = self._devices("  2  address=10.10.10.5/25  interface=ether5  network=10.10.10.0")
        report = sr.interface_flap_report(devices, days_back=5, now=NOW, inventory_rows=[])
        event = report["events"][0]
        self.assertEqual(event["interface"], "ether5")
        self.assertEqual(event["neighbor_name"], "")
        self.assertEqual(event["neighbor_ip"], "")
        self.assertEqual(event["neighbor_via"], "")

    def test_control_neighbor_on_its_own_interface_still_resolves(self):
        # کنترل: همان LLDP برای خودِ ether2 همچنان همسایه می‌دهد (قفل‌شدگی
        # نباید همسایهٔ واقعیِ همان اینترفیس را حذف کند).
        devices = self._devices()
        devices[0]["device_log"] = _flap_log("ether2")
        report = sr.interface_flap_report(devices, days_back=5, now=NOW, inventory_rows=[])
        event = report["events"][0]
        self.assertEqual(event["neighbor_name"], "SW-Core-MK")
        self.assertEqual(event["neighbor_ip"], "10.10.10.2")
        self.assertEqual(event["neighbor_via"], "lldp")

    def test_multi_interface_neighbor_value_is_pinned_to_each_part(self):
        # مقدار interface در /ip neighbor می‌تواند «wlan1,bridge1» باشد —
        # flap روی wlan1 باید همان همسایه را از مسیر LLDP ببیند.
        devices = [
            {"ip": "10.30.0.1", "device_name": "R-Edge", "device_log": _flap_log("wlan1"),
             "ip_neighbors": "=== /ip neighbor ===\n"
                             "  1  identity=R2SH  address=10.30.0.9  interface=wlan1,bridge1",
             "ip_addresses": "=== /ip address ===\n"
                             "  1  address=10.30.0.1/24  interface=wlan1  network=10.30.0.0"},
            {"ip": "10.30.0.9", "device_name": "R2SH", "device_log": "",
             "ip_neighbors": "", "ip_addresses": ""},
        ]
        report = sr.interface_flap_report(devices, days_back=5, now=NOW, inventory_rows=[])
        event = report["events"][0]
        self.assertEqual(event["neighbor_name"], "R2SH")
        self.assertEqual(event["neighbor_ip"], "10.30.0.9")
        self.assertEqual(event["neighbor_via"], "lldp")


if __name__ == "__main__":
    unittest.main()
