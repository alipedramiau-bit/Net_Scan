"""Quick verification test for the updated interface_flaps_csv export."""
import sys
import csv
sys.path.insert(0, "/home/z/my-project/backend")
import smart_reports

# Sample device log with flap events (short flaps < 5 min apart + alternating)
log = """Oct/20 08:00:01 ether1 link up
Oct/20 08:00:03 ether1 link down
Oct/20 08:00:05 ether1 link up
Oct/20 08:00:07 ether1 link down
Oct/20 08:00:09 ether1 link up
Oct/21 09:15:00 ether2 link down
Oct/21 09:15:02 ether2 link up
Oct/21 09:15:04 ether2 link down
Oct/21 09:15:06 ether2 link up"""

device = {
    "device_name": "Shadegan-Jafal1",
    "ip": "10.10.0.5",
    "tags": ["MPLS", "Core"],
    "device_log": log,
}

now = smart_reports.datetime(2026, 10, 23, 12, 0, 0)
report = smart_reports.interface_flap_report([device], days_back=5, threshold_minutes=5, now=now)

print("=== Report event fields ===")
print(sorted(report["events"][0].keys()))
print()
print("=== CSV output ===")
csv_text = smart_reports.interface_flaps_csv(report)
print(csv_text)
print("=== BOM check:", csv_text.startswith("\ufeff"))
print("=== Column count (header):", len(next(csv.reader(csv_text.lstrip("\ufeff").splitlines()))))
print("=== Column count (row 1):", len(next(csv.reader(csv_text.lstrip("\ufeff").splitlines()[1:]))))

# Also verify XLSX builds without error
buf = smart_reports.interface_flaps_xlsx(report)
print("=== XLSX bytes:", len(buf.getvalue()))

# Show the flap_count values that must now appear in CSV
print("\n=== flap_count values in events:", [e["flap_count"] for e in report["events"]])
