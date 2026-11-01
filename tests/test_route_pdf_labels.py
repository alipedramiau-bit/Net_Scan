"""Task 25 — برچسب‌های اینترفیس در نمودار Shortest Path باید خوانا باشند.

درخواست کاربر: «اینترفیس‌های دستگاه‌های سمت راست مشخص نیست؛ اندازهٔ برچسب‌ها را
طوری تغییر بده که قابل خواندن باشند». قبلاً هر دو اینترفیس در یک خط 5.8pt درون
گپِ ~۳۹٫۸pt رسم می‌شد و همیشه بریده می‌شد ("ether10 <-> ether24" عرضش ۵۳٫۲pt).
الان: اینترفیسِ چپ بالای خط، اینترفیسِ راست زیر خط (هرکدام 7.0pt) و برچسب شاهد
6.0pt؛ جعبه‌ها کمی جمع‌تر شده‌اند (۱۰۴→۹۴) تا گپ ~۵۳٫۱pt شود و چیزی بریده نشود.
"""
import inspect
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import route_pdf as rpdf


def test_row_geometry_still_fits_frame():
    """با جعبهٔ ۹۴ هم عرض سطر باید دقیقاً برابر کادر صفحه باشد (Task 24 حفظ می‌شود)."""
    row_w = (rpdf.PATH_ROW_BOXES * rpdf.PATH_BOX_W
             + (rpdf.PATH_ROW_BOXES - 1) * rpdf.PATH_ROW_GAP)
    assert abs(row_w - (rpdf.PAGE_W - 2 * rpdf.M)) < 0.01
    assert rpdf.PATH_ROW_BOXES == 4
    assert rpdf.PATH_BOX_W == 94          # جمع‌تر شده تا گپ عریض‌تر شود
    assert rpdf.PATH_ROW_GAP >= 50        # جای کافی برای برچسب‌های درشت‌تر


def test_label_sizes_are_readable():
    """فونت برچسب‌ها نسبت به نسخهٔ ناخوانا (5.8/5.2) درشت‌تر شده است."""
    assert rpdf.PATH_IF_SIZE >= 7.0        # نام اینترفیس دو سر لینک
    assert rpdf.PATH_TAG_SIZE >= 6.0       # برچسب شاهد درون‌سطر
    assert rpdf.PATH_WRAP_LBL_SIZE >= 7.0  # برچسب اتصال شکست سطر
    assert rpdf.PATH_WRAP_TAG_SIZE >= 6.0


def test_long_labels_fit_the_gap_without_truncation():
    """طولانی‌ترین برچسب‌های رایج باید کامل درون گپ جا شوند (بدون ...)."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    gap = rpdf.PATH_ROW_GAP
    for name in ("ether10", "ether24", "bridge1", "sfp-plus1", "ether10-slave"):
        assert stringWidth(name, "Helvetica-Bold", rpdf.PATH_IF_SIZE) <= gap - 6, name
    for tag in ("MNDP", "SUBNET", "ROUTE", "CISCO-ROUTE", "DEFAULT-ROUTE"):
        assert stringWidth(tag, "Helvetica-Oblique", rpdf.PATH_TAG_SIZE) <= gap - 2, tag


class FakeCanvas:
    def __init__(self):
        self.texts, self.fonts = [], []

    def setFillColor(self, *a):
        pass

    def setFont(self, f, s):
        self.fonts.append((f, s))

    def stringWidth(self, text, font, size):
        from reportlab.pdfbase.pdfmetrics import stringWidth as sw
        return sw(str(text), font, size)

    def drawCentredString(self, x, y, t):
        self.texts.append((x, y, t))


def test_inrow_labels_split_into_two_readable_lines():
    """اینترفیس چپ بالای خط، اینترفیس راست زیر خط — هر دو کامل و درشت."""
    fc = FakeCanvas()
    rpdf._inrow_link_labels(fc, 100.0, 50.0, "ether10", "ether24", "CISCO-ROUTE")
    texts = [(t, y) for _x, y, t in fc.texts]
    assert texts[0] == ("ether10", 55.0)     # بالای خط اتصال (mid + 5)
    assert texts[1] == ("ether24", 41.5)     # زیر خط اتصال (mid - 8.5)
    assert texts[2] == ("CISCO-ROUTE", 33.5)  # برچسب شاهد (mid - 16.5)
    sizes = [(f, s) for f, s in fc.fonts]
    # دو setFont: نام‌های اینترفیس با یک فونت مشترک درشت، برچسب شاهد کوچک‌تر
    assert sizes == [("Helvetica-Bold", rpdf.PATH_IF_SIZE),
                     ("Helvetica-Oblique", rpdf.PATH_TAG_SIZE)]
    assert rpdf.PATH_IF_SIZE > 5.8 and rpdf.PATH_TAG_SIZE > 5.2


def test_inrow_labels_without_evidence_tag():
    fc = FakeCanvas()
    rpdf._inrow_link_labels(fc, 100.0, 50.0, "ether1", "bridge1", "")
    assert [t for _x, _y, t in fc.texts] == ["ether1", "bridge1"]


def test_wrap_connector_labels_are_larger():
    """اتصال شکست سطر هم برچسب درشت‌تر دارد (Task 24 + Task 25)."""
    src = inspect.getsource(rpdf._row_wrap_connector)
    assert "PATH_WRAP_LBL_SIZE" in src and "PATH_WRAP_TAG_SIZE" in src
    assert "5.8" not in src and "5.2" not in src


def test_both_branches_use_the_readable_label_helper():
    """هم زنجیرهٔ reachable و هم upstream از helper خوانا استفاده می‌کنند."""
    src = inspect.getsource(rpdf._path_diagram)
    assert src.count("_inrow_link_labels") == 2
    assert "PATH_IF_SIZE" in inspect.getsource(rpdf._inrow_link_labels)
