import json
import sys
import tempfile
import unittest
from pathlib import Path

# Make project root importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend import db


class SettingsAndBackupTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "test_devices.db"
        db.init_db(self.db_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_settings_crud(self):
        # Default when key does not exist
        self.assertIsNone(db.get_setting("theme", db_path=self.db_path))
        self.assertEqual(db.get_setting("theme", "dark", db_path=self.db_path), "dark")

        # Set and get (set_setting also returns an updated_at timestamp)
        res = db.set_setting("theme", "emerald", db_path=self.db_path)
        self.assertEqual(res["key"], "theme")
        self.assertEqual(res["value"], "emerald")
        self.assertIn("updated_at", res)
        self.assertEqual(db.get_setting("theme", db_path=self.db_path), "emerald")

        # Update existing
        db.set_setting("theme", "indigo", db_path=self.db_path)
        self.assertEqual(db.get_setting("theme", db_path=self.db_path), "indigo")

        # Multiple settings
        db.set_setting("timeout", "500", db_path=self.db_path)
        all_s = db.get_all_settings(db_path=self.db_path)
        self.assertEqual(all_s, {"theme": "indigo", "timeout": "500"})

    def test_export_and_restore_backup(self):
        # Insert initial devices and settings
        db.upsert_device("192.168.1.1", True, [8291], {"8291": "open"}, "mikrotik_candidate", db_path=self.db_path)
        db.upsert_device("192.168.1.2", True, [80], {"80": "open"}, "non_mikrotik", db_path=self.db_path)
        db.set_setting("site_name", "Headquarters", db_path=self.db_path)
        db.set_setting("scan_workers", "32", db_path=self.db_path)

        # Export backup bytes
        raw_bytes = db.export_backup_bytes(db_path=self.db_path)
        self.assertIsInstance(raw_bytes, bytes)
        payload = json.loads(raw_bytes.decode("utf-8"))
        self.assertEqual(payload["app"], "mikrotik_scanner")
        self.assertEqual(len(payload["devices"]), 2)
        self.assertEqual(payload["settings"]["site_name"], "Headquarters")

        # Restore into a fresh database
        new_db_path = Path(self.tmpdir.name) / "restored_devices.db"
        summary = db.restore_backup_bytes(raw_bytes, db_path=new_db_path)
        self.assertEqual(summary["devices_restored"], 2)
        self.assertEqual(summary["devices_total"], 2)
        self.assertEqual(summary["settings_restored"], 2)
        self.assertEqual(summary["settings_total"], 2)

        # Verify restored data
        q = db.query_devices(db_path=new_db_path)
        self.assertEqual(q["total"], 2)
        ips = {d["ip"] for d in q["devices"]}
        self.assertEqual(ips, {"192.168.1.1", "192.168.1.2"})
        self.assertEqual(db.get_setting("site_name", db_path=new_db_path), "Headquarters")
        self.assertEqual(db.get_setting("scan_workers", db_path=new_db_path), "32")

    def test_restore_invalid_payload_raises(self):
        with self.assertRaises(ValueError):
            db.restore_backup_bytes(b"invalid json format", db_path=self.db_path)

        with self.assertRaises(ValueError):
            db.restore_backup_bytes(json.dumps({"app": "mikrotik_scanner"}).encode("utf-8"), db_path=self.db_path)


if __name__ == "__main__":
    unittest.main()
