"""Task 26 — نام دستگاه در گزارش مسیر باید درشت و خوانا باشد.

درخواست کاربر: «فونت نام دستگاه در بالای گزارش مسیریابی را بزرگتر کن بهتر دیده
شود». قبلاً نام دستگاه در نوار بالای صفحه 7.5pt و در جعبه‌های نمودار مسیر
6.6pt بود که در چاپ ناخوانا بود. الان:
- نوار بالا: نام با Helvetica-Bold 11 (IP با 8 در ادامه‌اش)
- جعبه‌های نمودار: نام با 8.5 (زنجیرهٔ اصلی) / 8.0 (upstream) و نام‌های بلند
  دورَقمی داخل جعبه جا می‌شوند (_fit_lines) به‌جای بریدن با «...»
- ارتفاع جعبه‌ها 30→36 / 26→32 و برای جبران، فاصلهٔ سطر جدول‌ها کمی جمع‌تر شد
  تا «یک صفحه به ازای هر دستگاه» همچنان برقرار بماند
"""
import inspect
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import route_pdf as rpdf


def test_constants_are_bigger_than_old_sizes():
    """فونت‌های جدید باید از مقادیر قبلی (7.5 / 6.6) بزرگ‌تر باشند."""
    assert rpdf.HEADER_NAME_SIZE >= 11.0          # نوار بالا (قبلاً 7.5)
    assert rpdf.PATH_NAME_SIZE >= 8.5             # جعبهٔ اصلی (قبلاً 6.6)
    assert rpdf.PATH_UP_NAME_SIZE >= 8.0          # جعبهٔ upstream (قبلاً 6.6)
    assert rpdf.PATH_BOX_H == 36 and rpdf.PATH_UP_BOX_H == 32
    assert rpdf.PATH_IP_SIZE > 6.0 and rpdf.PATH_UP_IP_SIZE > 5.8


def test_fit_lines_short_name_single_line():
    class C:
        def stringWidth(self, t, f, s):
            from reportlab.pdfbase.pdfmetrics import stringWidth as sw
            return sw(str(t), f, s)

    c = C()
    assert rpdf._fit_lines(c, "R-Dist-Anbar", "Helvetica-Bold", 8.5, 86) == ["R-Dist-Anbar"]


def test_fit_lines_long_name_wraps_to_two_lines_within_width():
    from reportlab.pdfbase.pdfmetrics import stringWidth
    c = type("C", (), {"stringWidth": staticmethod(
        lambda t, f, s: stringWidth(str(t), f, s))})()
    lines = rpdf._fit_lines(c, "RB-Anbar-daruel-HapLite-Core-Router-Number-One",
                            "Helvetica-Bold", 8.5, 86, 2)
    assert 1 <= len(lines) <= 2
    for ln in lines:
        assert stringWidth(ln, "Helvetica-Bold", 8.5) <= 86, ln
    joined = " ".join(lines)
    assert "RB-Anbar" in joined          # کلمهٔ اول هرگز حذف نمی‌شود


def test_fit_lines_single_long_token_gets_ellipsis():
    from reportlab.pdfbase.pdfmetrics import stringWidth
    c = type("C", (), {"stringWidth": staticmethod(
        lambda t, f, s: stringWidth(str(t), f, s))})()
    token = "X" * 60
    lines = rpdf._fit_lines(c, token, "Helvetica-Bold", 8.5, 86, 2)
    joined = "".join(lines)
    assert joined.endswith("...")
    for ln in lines:
        assert stringWidth(ln, "Helvetica-Bold", 8.5) <= 86, ln


def test_fit_lines_hyphenated_name_wraps_without_truncation():
    """نام میکروتیکیِ بدون فاصله (با خط تیره) باید کامل در دو سطر جا شود.

    RB-Anbar-daruel-HapLite در 6.6pt قدیمی در یک سطر جا می‌شد ولی در 8.5pt
    باید دورَقمی شود — نه اینکه با «...» بریده شود (ناخوانا).
    """
    from reportlab.pdfbase.pdfmetrics import stringWidth
    c = type("C", (), {"stringWidth": staticmethod(
        lambda t, f, s: stringWidth(str(t), f, s))})()
    for nm in ("RB-Anbar-daruel-HapLite", "RB-UMS-SHDGN-CoreRouter",
               "VL-Shadegan-Shabankareh"):
        lines = rpdf._fit_lines(c, nm, "Helvetica-Bold", 8.5, 86, 2)
        assert "".join(lines) == nm, (nm, lines)      # نام کامل، بدون «...»
        for ln in lines:
            assert stringWidth(ln, "Helvetica-Bold", 8.5) <= 86, (nm, ln)
    # نام‌های خط‌تیرهٔ خیلی بلند: دو سطر + «...» در سطر آخر
    lines = rpdf._fit_lines(c, "SW-L2-Far-Very-Long-Identity-Name-Branch",
                            "Helvetica-Bold", 8.5, 86, 2)
    assert len(lines) == 2 and lines[-1].endswith("...")
    assert lines[0].startswith("SW-L2-Far")


def test_fit_lines_empty_text():
    c = type("C", (), {"stringWidth": staticmethod(lambda t, f, s: 0)})()
    assert rpdf._fit_lines(c, "", "Helvetica-Bold", 8.5, 86) == [""]


def test_header_draws_big_bold_device_name():
    """نوار بالای صفحه: نام دستگاه با Helvetica-Bold 11 رسم می‌شود."""

    class C:
        def __init__(self):
            self.fonts, self.strings = [], []

        def setFillColor(self, *a):
            pass

        def setFont(self, f, s):
            self.fonts.append((f, s))

        def stringWidth(self, t, f, s):
            from reportlab.pdfbase.pdfmetrics import stringWidth as sw
            return sw(str(t), f, s)

        def rect(self, *a, **k):
            pass

        def drawString(self, x, y, t):
            self.strings.append((x, y, t))

        def drawRightString(self, x, y, t):
            self.strings.append((x, y, t))

    c = C()
    rpdf._page_header(c, 1, 3, "RB-Anbar-daruel-HapLite", "172.29.196.68",
                      "SW-Wireless1 (172.19.1.6)", "2026-11-01 13:30 UTC")
    assert ("Helvetica-Bold", rpdf.HEADER_NAME_SIZE) in c.fonts
    texts = [t for _x, _y, t in c.strings]
    assert "RB-Anbar-daruel-HapLite" in texts          # نام کامل، بدون بریدگی
    assert "(172.29.196.68)" in texts                  # IP در ادامهٔ نام
    assert "Core Router: SW-Wireless1 (172.19.1.6)" in texts
    # نام دستگاه با درشت‌ترین فونت بعد از تیتر صفحه رسم می‌شود
    bold_sizes = [s for f, s in c.fonts if f == "Helvetica-Bold"]
    assert rpdf.HEADER_NAME_SIZE in bold_sizes
    assert max(bold_sizes) == 13.5                     # فقط تیتر «Detailed Router...»


def test_header_long_name_is_fitted_inside_band():
    """نام خیلی بلند در نوار بالا با «...» کوتاه می‌شود ولی از نوار بیرون نمی‌زند."""
    from reportlab.pdfbase.pdfmetrics import stringWidth

    class C:
        def __init__(self):
            self.strings = []

        def setFillColor(self, *a):
            pass

        def setFont(self, *a):
            pass

        def stringWidth(self, t, f, s):
            return stringWidth(str(t), f, s)

        def rect(self, *a, **k):
            pass

        def drawString(self, x, y, t):
            self.strings.append((x, t))

        def drawRightString(self, x, y, t):
            self.right = t

    c = C()
    long_name = "Very-Long-Router-Identity-Name-" * 4
    rpdf._page_header(c, 1, 1, long_name, "10.0.0.1", "10.0.0.99", "gen")
    # رشتهٔ ساخته‌شده از نام بلند باید «...» داشته باشد و داخل کادر بماند
    name_lines = [t for _x, t in c.strings if "Very-Long" in t or t.endswith("...")]
    assert name_lines, [t for _x, t in c.strings]
    fitted = name_lines[0]
    assert fitted.endswith("...")
    assert all(x + stringWidth(t, "Helvetica-Bold", rpdf.HEADER_NAME_SIZE) <= rpdf.PAGE_W - rpdf.M
               for x, t in c.strings if t == fitted)


def test_path_diagram_box_names_use_big_font():
    src = inspect.getsource(rpdf._path_diagram)
    assert "PATH_NAME_SIZE" in src and "PATH_UP_NAME_SIZE" in src
    assert "PATH_BOX_H" in src and "PATH_UP_BOX_H" in src
    assert "_fit_lines" in src
    assert "6.6" not in src          # فونت قدیمی ناخوانا حذف شده باشد
    assert "_san(nd.get(\"name\")) or nkey" in src


def test_page_budget_still_fits_one_page_per_device():
    """بدترین حالت (۱۲ آدرس + ۲۴ اینترفیس + ۸ hop + ۶ شاهد) باید بالای فوتر تمام شود.

    جمع کاهش فاصلهٔ سطر جدول‌ها (Task 26) باید >= افزایش ارتفاع جعبه‌های نمودار باشد.
    """
    # افزایش: جعبهٔ اصلی 30→36 و فاصلهٔ سطر 34→30 → هر سطر نمودار +2pt
    # (دو سطر = +4) و upstream 26→32 با فاصلهٔ 30 → هر سطر +2 (دو سطر = +4)
    box_growth_per_row = (rpdf.PATH_BOX_H + rpdf.PATH_ROW_STRIDE) - (30 + 34)
    assert box_growth_per_row == 2
    # جبران: kv 5×0.5 + addr 12×0.5 + iface 8×0.4 + hops 8×0.8 + evidence 6×1 = 18.7pt
    saved = (5 * (13 - 12.5) + 12 * (11.5 - 11.0) + 8 * (11 - 10.6)
             + 8 * (12 - 11.2) + 6 * (11 - 10.0))
    assert saved >= 2 * box_growth_per_row
