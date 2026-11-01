"""Task 24 — نمودار Shortest Path در PDF گزارش مسیر باید داخل کادر صفحه بماند.

باگ قبلی: در _path_diagram هر سطر ۴ جعبه دارد (per_row=3 hop + دستگاه) ولی gap
برای ۳ جعبه محاسبه می‌شد؛ جعبه‌های انتهای زنجیره (از جمله روتر مرکزی) حدود
۲۱۵pt از کادر صفحه بیرون می‌زدند و دیده نمی‌شدند. الان:
- هر سطر دقیقاً داخل کادر جا می‌شود (ثابت‌های PATH_ROW_*)
- ادامهٔ زنجیره با اتصال Z شکل (_row_wrap_connector) به سطر بعد می‌رود
"""
import inspect
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import route_pdf as rpdf


def test_row_geometry_fits_frame():
    """عرض سطر (جعبه‌ها + فاصله‌ها) باید دقیقاً برابر کادر صفحه باشد."""
    row_w = (rpdf.PATH_ROW_BOXES * rpdf.PATH_BOX_W
             + (rpdf.PATH_ROW_BOXES - 1) * rpdf.PATH_ROW_GAP)
    assert abs(row_w - (rpdf.PAGE_W - 2 * rpdf.M)) < 0.01
    assert rpdf.PATH_ROW_BOXES == 4          # ۳ hop + دستگاه مبدأ
    assert rpdf.PATH_ROW_GAP > 0


def test_path_box_slot_wraps_rows():
    """بعد از هر ۴ جعبه، زنجیره به سطر بعد می‌رود."""
    assert rpdf.path_box_slot(0) == (0, 0)
    assert rpdf.path_box_slot(3) == (0, 3)
    assert rpdf.path_box_slot(4) == (1, 0)   # شکست سطر
    assert rpdf.path_box_slot(7) == (1, 3)
    assert rpdf.path_box_slot(8) == (2, 0)


def test_wrap_connector_draws_z_shaped_link():
    """اتصال سطرها: سه پاره‌خط Z شکل + برچسب لینک + برچسب شاهد."""

    class FakeCanvas:
        def __init__(self):
            self.lines, self.texts, self.fonts = [], [], []

        def setStrokeColor(self, *a):
            pass

        def setFillColor(self, *a):
            pass

        def setLineWidth(self, *a):
            pass

        def setFont(self, f, s):
            self.fonts.append((f, s))

        def stringWidth(self, text, font, size):
            return len(str(text)) * size * 0.55

        def line(self, x1, y1, x2, y2):
            self.lines.append((x1, y1, x2, y2))

        def drawCentredString(self, x, y, t):
            self.texts.append((x, y, t))

    fc = FakeCanvas()
    prev_box = (460.0, 100.0, 104.0, 30.0)  # x، پایین جعبه، عرض، ارتفاع
    cur_box = (30.0, 40.0, 104.0, 30.0)     # x، پایین جعبه، عرض، ارتفاع
    rpdf._row_wrap_connector(fc, prev_box, cur_box, "ether1 <-> bridge1", "MNDP")
    assert len(fc.lines) == 3
    x1, x2 = 460.0 + 52.0, 30.0 + 52.0      # مرکز دو جعبه
    mid_y = (100.0 + 40.0 + 30.0) / 2.0     # وسط فاصلهٔ دو سطر
    assert fc.lines[0] == (x1, 100.0, x1, mid_y)    # پایین از جعبهٔ قبل
    assert fc.lines[1] == (x1, mid_y, x2, mid_y)    # رفتن به چپ بین دو سطر
    assert fc.lines[2] == (x2, mid_y, x2, 70.0)     # ورود از بالای جعبهٔ بعد
    labels = [t for _, _, t in fc.texts]
    assert "ether1 <-> bridge1" in labels
    assert "MNDP" in labels


def test_wrap_connector_without_label_still_draws_link():
    class FakeCanvas:
        def __init__(self):
            self.lines, self.texts = [], []

        def setStrokeColor(self, *a):
            pass

        def setFillColor(self, *a):
            pass

        def setLineWidth(self, *a):
            pass

        def setFont(self, *a):
            pass

        def stringWidth(self, text, font, size):
            return len(str(text)) * size * 0.55

        def line(self, x1, y1, x2, y2):
            self.lines.append((x1, y1, x2, y2))

        def drawCentredString(self, x, y, t):
            self.texts.append((x, y, t))

    fc = FakeCanvas()
    rpdf._row_wrap_connector(fc, (0.0, 50.0, 104.0, 26.0), (0.0, 0.0, 104.0, 26.0))
    assert len(fc.lines) == 3 and not fc.texts


def test_path_diagram_uses_wrap_connector_for_both_branches():
    """هم شاخهٔ reachable و هم شاخهٔ upstream باید اتصال سطرها را صدا بزنند."""
    src = inspect.getsource(rpdf._path_diagram)
    assert src.count("_row_wrap_connector") >= 2
    assert "path_box_slot" in src
