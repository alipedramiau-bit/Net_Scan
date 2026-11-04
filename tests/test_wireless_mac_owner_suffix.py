"""Task 43 — نام دستگاهِ مالکِ MAC در انتهای متن رویداد گزارش آنتن‌ها.

در گزارش «قطع و وصل شدن آنتن‌ها» متنِ رخداد یک MAC دارد (مثل
E4:8D:8C:61:6E:4F@wlan1 "disconnected, ..."). باید نام دستگاهِ متناظر با
همان MAC (از فیلدهای اینونتوری) به انتهای متن رویداد اضافه شود:
۱) MAC تطبیق‌شده با نام → پسوند «— دستگاه متعلق به MAC: <نام>»؛
۲) MAC ناشناخته → متن رویداد دست‌نخورده می‌ماند؛
۳) نام خالی ولی IP موجود → پسوند با IP ساخته می‌شود؛
۴) پسوند در CSV هم باید بیاید.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend import smart_reports as sr

NOW = sr.datetime(2026, 11, 4, 12, 0, 0)

KNOWN_MAC = "E4:8D:8C:61:6E:4F"
UNKNOWN_MAC = "AA:BB:CC:DD:EE:01"
IP_ONLY_MAC = "11:22:33:44:55:66"

SUFFIX_KNOWN = f"دستگاه متعلق به MAC: RB-Jafal1-Link"
SUFFIX_IP = f"دستگاه متعلق به MAC: 172.18.9.9"


def _log():
    return (
        f"Nov/03 09:15:00 wlan1: {KNOWN_MAC}@wlan1 disconnected, extensive data loss, signal strength -73\n"
        f"Nov/03 09:20:00 wlan1: {UNKNOWN_MAC}@wlan1 failed to connect, not responding\n"
        f"Nov/03 09:25:00 wlan1: {IP_ONLY_MAC}@wlan1 lost connection"
    )


def _devices():
    return [
        {"ip": "172.18.4.1", "device_name": "RB-UMS-SHDGN-CoreRouter", "device_log": _log(),
         "mac_info": "", "wireless_info": "", "ip_neighbors": "", "interfaces": "", "ip_addresses": ""},
        {"ip": "172.18.4.7", "device_name": "RB-Jafal1-Link", "device_log": "",
         "mac_info": f"MAC={KNOWN_MAC}", "wireless_info": "", "ip_neighbors": "", "interfaces": "",
         "ip_addresses": ""},
        {"ip": "172.18.9.9", "device_name": "", "device_log": "",
         "mac_info": f"MAC={IP_ONLY_MAC}", "wireless_info": "", "ip_neighbors": "", "interfaces": "",
         "ip_addresses": ""},
    ]


def _report():
    return sr.wireless_antenna_report(_devices(), days_back=5, now=NOW)


def _event_for_mac(report, mac):
    return [e for e in report["events"] if e["station_mac"] == mac][0]


class OwnerSuffixTests(unittest.TestCase):
    def test_matched_mac_appends_owner_name(self):
        event = _event_for_mac(_report(), KNOWN_MAC)
        base = f"wlan1: {KNOWN_MAC}@wlan1 disconnected, extensive data loss, signal strength -73"
        self.assertEqual(event["event"], f"{base} — {SUFFIX_KNOWN}")
        self.assertEqual(event["matched_device_name"], "RB-Jafal1-Link")

    def test_unmatched_mac_keeps_event_text_untouched(self):
        event = _event_for_mac(_report(), UNKNOWN_MAC)
        self.assertEqual(
            event["event"],
            f"wlan1: {UNKNOWN_MAC}@wlan1 failed to connect, not responding")
        self.assertNotIn("دستگاه متعلق به MAC", event["event"])

    def test_name_missing_falls_back_to_ip(self):
        event = _event_for_mac(_report(), IP_ONLY_MAC)
        self.assertTrue(event["event"].endswith(f" — {SUFFIX_IP}"))

    def test_suffix_reaches_csv(self):
        csv_text = sr.wireless_antenna_csv(_report())
        self.assertIn(SUFFIX_KNOWN, csv_text)
        self.assertIn(SUFFIX_IP, csv_text)

    def test_other_fields_still_intact(self):
        report = _report()
        self.assertEqual(report["event_count"], 3)
        event = _event_for_mac(report, KNOWN_MAC)
        self.assertEqual(event["antenna_name"], "RB-UMS-SHDGN-CoreRouter")
        self.assertEqual(event["matched_device_ip"], "172.18.4.7")
        # raw_line بدون پسوند می‌ماند (متن خام لاگ).
        self.assertNotIn("دستگاه متعلق به MAC", event["raw_line"])


if __name__ == "__main__":
    unittest.main()
