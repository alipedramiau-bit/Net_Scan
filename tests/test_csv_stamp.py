import sys
import re
import inspect
import unittest
from datetime import datetime
from pathlib import Path

# Make the project root importable when this test file is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.main import file_stamp


class FileStampTests(unittest.TestCase):
    """Task 22: نام همهٔ فایل‌های CSV باید تاریخ/ساعت جاری سیستم را داشته باشد."""

    def test_file_stamp_format_and_freshness(self):
        stamp = file_stamp()
        self.assertRegex(stamp, r"^\d{8}_\d{6}$")
        parsed = datetime.strptime(stamp, "%Y%m%d_%H%M%S")
        self.assertLess(abs((datetime.now() - parsed).total_seconds()), 5)

    def test_every_csv_route_uses_file_stamp(self):
        # هر مسیری که CSV برمی‌گرداند باید file_stamp() را در نام فایل به‌کار ببرد
        from backend import main as appm
        csv_routes = [r for r in appm.app.routes
                      if getattr(r, "path", "").endswith("csv")]
        self.assertGreaterEqual(len(csv_routes), 7)
        for route in csv_routes:
            src = inspect.getsource(route.endpoint)
            self.assertIn("file_stamp", src,
                          f"route {route.path} does not stamp its CSV filename")


if __name__ == "__main__":
    unittest.main()
