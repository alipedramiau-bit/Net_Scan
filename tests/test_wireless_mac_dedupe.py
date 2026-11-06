"""Task 44 — حذف رکوردهای تکراریِ یک MAC از گزارش «قطع و وصل شدن آنتن‌ها».

رکوردهایی که MAC ایستگاه یکسانی دارند فقط یک بار در گزارش بیایند:
۱) از هر MAC فقط جدیدترین رکورد نگه داشته می‌شود (گزارش جدیدترین‌اول است)؛
۲) تکرارِ همان MAC روی آنتن دیگر هم حذف می‌شود (تطبیق سراسری روی MAC)؛
۳) رکوردهای بدون MAC سر جایشان می‌مانند؛
۴) duplicate_mac_count تعداد رکوردهای حذف‌شده را می‌دهد؛
۵) CSV هم فقط یک ردیف برای هر MAC دارد.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend import smart_reports as sr

NOW = sr.datetime(2026, 11, 6, 12, 0, 0)

DUP_MAC = "78:9A:18:B0:43:EC"
OTHER_MAC = "AA:BB:CC:00:11:22"


def _devices():
    return [
        {"ip": "172.172.177.46", "device_name": "ParsaRasanerh-Man-K1", "device_log": (
            f"Nov/06 09:00:00 wlan1: {DUP_MAC}@wlan1 disconnected, extensive data loss, signal strength -67\n"
            f"Nov/06 10:00:00 wlan1: {DUP_MAC}@wlan1 disconnected, extensive data loss, signal strength -66\n"
            "Nov/06 10:05:00 wlan1: weak signal detected\n"
            "Nov/06 10:06:00 wlan1: weak signal detected\n"
        ), "mac_info": "", "wireless_info": "", "ip_neighbors": "", "interfaces": "", "ip_addresses": ""},
        {"ip": "172.172.171.6", "device_name": "PR-Choobdeh5", "device_log": (
            f"Nov/06 08:00:00 wlan2: {DUP_MAC}@wlan2 lost connection\n"
            f"Nov/06 11:00:00 wlan1: {OTHER_MAC}@wlan1 disconnected, not responding\n"
        ), "mac_info": "", "wireless_info": "", "ip_neighbors": "", "interfaces": "", "ip_addresses": ""},
    ]


def _report():
    return sr.wireless_antenna_report(_devices(), days_back=5, now=NOW)


class MacDedupeTests(unittest.TestCase):
    def test_only_latest_record_per_mac_kept(self):
        report = _report()
        dup_events = [e for e in report["events"] if e["station_mac"] == DUP_MAC]
        self.assertEqual(len(dup_events), 1)
        # جدیدترین رکورد (۱۰:۰۰) نگه داشته شده، نه ۰۹:۰۰ و نه ۰۸:۰۰ آنتن دیگر.
        self.assertIn("10:00:00", dup_events[0]["datetime"])
        self.assertIn("signal strength -66", dup_events[0]["event"])

    def test_duplicate_across_antennas_removed(self):
        report = _report()
        macs = [e["station_mac"] for e in report["events"]]
        self.assertEqual(macs.count(DUP_MAC), 1)
        self.assertEqual(macs.count(OTHER_MAC), 1)

    def test_macless_events_are_kept(self):
        report = _report()
        macless = [e for e in report["events"] if not e["station_mac"]]
        self.assertEqual(len(macless), 2)

    def test_duplicate_mac_count_reported(self):
        self.assertEqual(_report()["duplicate_mac_count"], 2)
        self.assertEqual(_report()["event_count"], 4)

    def test_rows_renumbered_and_order_desc(self):
        report = _report()
        rows = [e["row"] for e in report["events"]]
        self.assertEqual(rows, list(range(1, len(rows) + 1)))
        times = [e["datetime"] for e in report["events"]]
        self.assertEqual(times, sorted(times, reverse=True))

    def test_csv_has_single_row_per_mac(self):
        csv_text = sr.wireless_antenna_csv(_report())
        # هر MAC فقط در «یک ردیف» CSV بیاید (در همان ردیف داخل متن رویداد هم هست).
        dup_rows = [l for l in csv_text.splitlines() if DUP_MAC in l]
        other_rows = [l for l in csv_text.splitlines() if OTHER_MAC in l]
        self.assertEqual(len(dup_rows), 1)
        self.assertEqual(len(other_rows), 1)


if __name__ == "__main__":
    unittest.main()
