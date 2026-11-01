"""One-page-per-device PDF route topology report (English, ReportLab).

Mirrors the user's "Detailed Router Path Topology" sample:
header band → router information → IP addresses & interfaces → interfaces →
shortest path diagram → hop-by-hop link verification → routing/adjacency
evidence → footer. Exactly one A4 page per device, so the PDF never overflows.
"""
from __future__ import annotations

import io

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdfcanvas


PAGE_W, PAGE_H = A4  # 595.27 x 841.89
M = 30               # margin
NAVY = (0.122, 0.220, 0.392)
GREEN = (0.086, 0.541, 0.333)
GREEN_BG = (0.909, 0.960, 0.933)
RED = (0.725, 0.109, 0.109)
RED_BG = (0.996, 0.949, 0.949)
AMBER = (0.706, 0.443, 0.043)
AMBER_BG = (1.0, 0.957, 0.878)
INK = (0.058, 0.093, 0.164)
GRAY = (0.415, 0.478, 0.560)
LINE = (0.784, 0.815, 0.862)
THBG = (0.909, 0.929, 0.957)
BOX = (0.200, 0.255, 0.341)

# Task 24: هندسهٔ زنجیرهٔ نمودار Shortest Path — در هر سطر PATH_ROW_BOXES جعبه
# دقیقاً داخل کادر صفحه جا می‌شود و ادامهٔ زنجیره با اتصال Z شکل به سطر بعد
# می‌رود تا روتر مرکزی همیشه داخل کادر قابل رویت باشد (قبلاً gap برای یک جعبه
# کمتر محاسبه می‌شد و جعبه‌های انتهای زنجیره از صفحه بیرون می‌زدند)
PATH_PER_ROW = 3                    # تعداد hop در هر سطر
PATH_ROW_BOXES = PATH_PER_ROW + 1   # تعداد جعبه در هر سطر (دستگاه + hopها)
PATH_BOX_W = 94                     # عرض جعبه‌ها (Task 25: کمی جمع‌تر تا فاصلهٔ
                                    # بین جعبه‌ها عریض‌تر شود و برچسب اینترفیس‌ها
                                    # بدون بریدگی و خوانا جا شوند)
PATH_ROW_GAP = (PAGE_W - 2 * M - PATH_ROW_BOXES * PATH_BOX_W) / (PATH_ROW_BOXES - 1)

# Task 25: برچسب‌های لینک نمودار مسیر باید «قابل خواندن» باشند — به جای یک خط
# ریز 5.8pt به شکل «ether10 <-> ether24» (که در گپ ۳۹٫۸pt همیشه بریده می‌شد)،
# اینترفیسِ دستگاهِ چپ بالای خط اتصال و اینترفیسِ دستگاهِ راست زیر آن با فونت
# درشت‌تر رسم می‌شود و برچسب شاهد (MNDP/CISCO-ROUTE/...) هم بزرگ‌تر است.
PATH_IF_SIZE = 7.0        # نام اینترفیسِ دو سر لینک (قبلاً 5.8 در یک خط)
PATH_TAG_SIZE = 6.0       # برچسب شاهد درون‌سطر (قبلاً 5.2)
PATH_WRAP_LBL_SIZE = 7.2  # برچسب لینک در اتصال شکست سطر (قبلاً 5.8)
PATH_WRAP_TAG_SIZE = 6.4  # برچسب شاهد در اتصال شکست سطر (قبلاً 5.2)

# Task 26: نام دستگاه باید «درشت و خوانا» باشد — هم در نوار بالای صفحه و هم در
# جعبه‌های نمودار مسیر (درخواست کاربر: «فونت نام دستگاه در بالای گزارش مسیریابی
# را بزرگتر کن بهتر دیده شود»). قبلاً نام در جعبه‌ها 6.6pt و در نوار بالا 7.5pt
# بود که در چاپ ناخوانا بود؛ حالا نام‌های بلند در جعبه دورَقمی جا می‌شوند
# (_fit_lines) و برای جبران ارتفاع، فاصلهٔ سطرهای جدول‌ها کمی جمع‌تر شده است.
PATH_NAME_SIZE = 8.5      # نام دستگاه در جعبه‌های زنجیرهٔ اصلی (قبلاً 6.6)
PATH_UP_NAME_SIZE = 8.0   # نام دستگاه در جعبه‌های زنجیرهٔ upstream (قبلاً 6.6)
PATH_BOX_H = 36           # ارتفاع جعبهٔ اصلی (قبلاً 30 — جا برای نام دورَقمی)
PATH_UP_BOX_H = 32        # ارتفاع جعبهٔ upstream (قبلاً 26)
PATH_IP_SIZE = 6.3        # IP زیر نام در جعبهٔ اصلی (قبلاً 6.0)
PATH_UP_IP_SIZE = 6.0     # IP زیر نام در جعبهٔ upstream (قبلاً 5.8)
PATH_ROW_STRIDE = 30      # فاصلهٔ عمودی سطرهای نمودار (قبلاً 34 — جبران ارتفاع جعبه)
HEADER_NAME_SIZE = 11.0   # نام دستگاه در نوار بالای صفحه (قبلاً 7.5)


def _san(s) -> str:
    """Keep latin-1 printable characters (Helvetica core font)."""
    if s is None:
        return ""
    return "".join(ch for ch in str(s) if 32 <= ord(ch) < 256).strip()


def _fit(c, text: str, font: str, size: float, max_w: float) -> str:
    if c.stringWidth(text, font, size) <= max_w:
        return text
    while text and c.stringWidth(text + "...", font, size) > max_w:
        text = text[:-1]
    return text + "..."


def _fit_lines(c, text: str, font: str, size: float, max_w: float,
               max_lines: int = 2) -> list[str]:
    """متن را در حداکثر max_lines سطر جا می‌دهد (Task 26).

    نام دستگاه با فونت درشت‌تر معمولاً در یک سطرِ عرض جعبه جا نمی‌شود؛ به جای
    بریدن آن با «...» (ناخوانا)، تا دو سطر شکسته می‌شود و فقط اگر باز هم جا
    نشد سطر آخر با «...» کوتاه می‌شود. هر سطر برگشتی تضمیناً عرضش <= max_w است.
    نام‌های میکروتیک معمولاً «بدون فاصله» و با خط تیره/نقطه‌اند (مثل
    RB-Anbar-daruel-HapLite)؛ پس شکستن فقط در فاصله کافی نیست — در مرز
    خط تیره/نقطه/زیرخط/دو نقطه/اسلش هم شکسته می‌شود.
    """
    text = _san(text)
    if not text:
        return [""]
    if c.stringWidth(text, font, size) <= max_w:
        return [text]
    toks: list[str] = []
    cur = ""
    for ch in text:
        cur += ch
        if ch in " \t-._:/":
            toks.append(cur)
            cur = ""
    if cur:
        toks.append(cur)
    lines: list[str] = []
    cur = ""
    i = 0
    truncated = False
    while i < len(toks):
        tok = toks[i]
        cand = cur + tok
        if cur and c.stringWidth(cand.rstrip(), font, size) > max_w:
            lines.append(cur.rstrip())
            if len(lines) == max_lines:
                truncated = True
                break
            cur = ""
            continue
        cur = cand
        i += 1
    if not truncated and cur.strip():
        lines.append(cur.rstrip())
    if not lines:
        lines = [text]
    out: list[str] = []
    for ln in lines:
        if c.stringWidth(ln, font, size) <= max_w:
            out.append(ln)
            continue
        t = ln
        while t and c.stringWidth(t + "...", font, size) > max_w:
            t = t[:-1]
        out.append(t + "...")
    if truncated and out and not out[-1].endswith("..."):
        t = out[-1]
        while t and c.stringWidth(t + "...", font, size) > max_w:
            t = t[:-1]
        out[-1] = t + "..."
    return out


def _fmt_ip_list(ports) -> str:
    try:
        return ", ".join(str(p) for p in (ports or [])) or "-"
    except Exception:
        return _san(ports) or "-"


def _section(c, y: float, title: str, count: str | None = None) -> float:
    c.setFillColor(GREEN)
    c.rect(M, y - 9, 4, 10, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(M + 9, y - 8, title)
    if count:
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 7.5)
        c.drawString(M + 9 + c.stringWidth(title, "Helvetica-Bold", 9) + 6, y - 8, count)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(M, y - 13, PAGE_W - M, y - 13)
    return y - 22


def _kv_grid(c, y: float, rows: list[tuple[str, str]]) -> float:
    col_w = (PAGE_W - 2 * M) / 2
    line_h = 12.5  # Task 26: 13→12.5 — جبران ارتفاع بیشتر جعبه‌های نمودار
    for i, (k, v) in enumerate(rows):
        cx = M if i % 2 == 0 else M + col_w
        if i % 2 == 0:
            y -= line_h
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(GRAY)
        c.drawString(cx, y, k + ":")
        c.setFont("Helvetica", 7.5)
        c.setFillColor(INK)
        c.drawString(cx + 78, y, _fit(c, _san(v) or "-", "Helvetica", 7.5, col_w - 84))
    return y - 6


def _page_header(c, idx: int, total: int, name: str, ip: str, central_ip: str,
                 generated: str) -> None:
    band_h = 52
    top = PAGE_H
    c.setFillColor(NAVY)
    c.rect(0, top - band_h, PAGE_W, band_h, fill=1, stroke=0)
    c.setFillColor((1, 1, 1))
    c.setFont("Helvetica-Bold", 13.5)
    c.drawString(M, top - 21, "Detailed Router Path Topology")
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(PAGE_W - M, top - 21, f"Router {idx} of {total}")
    # Task 26: نام دستگاه در بالای گزارش درشت و خوانا — قبلاً کل خط
    # «Target: name (ip)» با 7.5pt رسم می‌شد؛ حالا برچسب «Target:» کوچک می‌ماند
    # ولی خودِ نام Helvetica-Bold 11 می‌شود و IP با 8 در ادامه‌اش می‌آید.
    c.setFont("Helvetica", 7.5)
    c.setFillColor((0.82, 0.87, 0.93))
    c.drawString(M, top - 37, "Target: ")
    lbl_w = c.stringWidth("Target: ", "Helvetica", 7.5)
    core_txt = f"Core Router: {central_ip}"
    core_w = c.stringWidth(core_txt, "Helvetica", 7.5)
    ip_txt = f"({ip})" if ip else ""
    ip_w = (c.stringWidth(ip_txt, "Helvetica", 8) + 5) if ip_txt else 0
    name_x = M + lbl_w + 2
    nm = _fit(c, _san(name) or "-", "Helvetica-Bold", HEADER_NAME_SIZE,
              max(PAGE_W - M - core_w - 10 - name_x - ip_w, 60))
    c.setFillColor((1, 1, 1))
    c.setFont("Helvetica-Bold", HEADER_NAME_SIZE)
    c.drawString(name_x, top - 37, nm)
    if ip_txt:
        c.setFont("Helvetica", 8)
        c.setFillColor((0.82, 0.87, 0.93))
        c.drawString(name_x + c.stringWidth(nm, "Helvetica-Bold", HEADER_NAME_SIZE) + 5,
                     top - 37, ip_txt)
    c.drawRightString(PAGE_W - M, top - 37, core_txt)
    c.setFont("Helvetica", 7)
    c.drawString(M, top - 48, _san(generated)[:110])


def _footer(c, idx: int, total: int, database: str) -> None:
    y = 22
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(M, y + 10, PAGE_W - M, y + 10)
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 6.5)
    c.drawString(M, y, "Net_Scan - Route Topology Report (RouterOS API)" + (f" - database: {database}" if database else ""))
    c.drawRightString(PAGE_W - M, y, f"page {idx}/{total}")


def _addr_table(c, y: float, addresses: list[dict]) -> float:
    rows = [a for a in addresses if a.get("address") or a.get("interface")]
    shown = rows[:12]
    col = [150, 140, PAGE_W - 2 * M - 290]
    y -= 13
    c.setFillColor(THBG)
    c.rect(M, y - 3, PAGE_W - 2 * M, 12, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 7)
    for lbl, w in zip(("Address", "Interface", "Network"), col):
        c.drawString(M + 4 + ([0, col[0], col[0] + col[1]][["Address", "Interface", "Network"].index(lbl)]), y, lbl)
    y -= 12
    c.setFont("Helvetica", 7)
    for a in shown:
        vals = [_san(a.get("address")) or "-", _san(a.get("interface")) or "-", _san(a.get("network")) or "-"]
        for off, v, w in zip((0, col[0], col[0] + col[1]), vals, col):
            c.setFillColor(INK)
            c.drawString(M + 4 + off, y, _fit(c, v, "Helvetica", 7, w - 8))
        y -= 11  # Task 26: 11.5→11 — جبران ارتفاع جعبه‌های نمودار
    if len(rows) > len(shown):
        c.setFillColor(GRAY)
        c.setFont("Helvetica-Oblique", 6.5)
        c.drawString(M + 4, y, f"... and {len(rows) - len(shown)} more address(es)")
        y -= 10
    return y


def _iface_grid(c, y: float, interfaces: list[dict]) -> float:
    rows = [i for i in interfaces if i.get("name")]
    shown = rows[:24]
    col_w = (PAGE_W - 2 * M) / 3
    per_col = 8
    c.setFont("Helvetica", 6.8)
    for idx, it in enumerate(shown):
        cx = M + (idx // per_col) * col_w
        ry = y - 10.6 * (idx % per_col) - 10.6  # Task 26: 11→10.6
        run = (it.get("running") or "").lower() == "true" and (it.get("disabled") or "").lower() != "true"
        state = "up" if run else ("off" if (it.get("disabled") or "").lower() == "true" else "down")
        c.setFillColor(GREEN if run else GRAY)
        c.rect(cx, ry - 1, 3, 7, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont("Helvetica", 6.8)
        c.drawString(cx + 6, ry, _fit(c, f"{_san(it.get('name'))} ({_san(it.get('type')) or '-'}) {state}",
                                      "Helvetica", 6.8, col_w - 10))
    # tallest column = min(n, per_col) rows (column-major layout)
    y -= 10.6 * min(len(shown), per_col) + 2  # Task 26: 11→10.6 — جبران ارتفاع جعبه‌ها
    if len(rows) > len(shown):
        c.setFillColor(GRAY)
        c.setFont("Helvetica-Oblique", 6.5)
        c.drawString(M, y, f"... and {len(rows) - len(shown)} more interface(s)")
        y -= 10
    return y


def path_box_slot(i: int) -> tuple[int, int]:
    """موقعیت (سطر، ستون) جعبهٔ i-ام زنجیرهٔ مسیر (Task 24).

    بعد از هر PATH_ROW_BOXES جعبه، زنجیره به سطر بعد می‌رود تا همیشه داخل
    کادر صفحه بماند و روتر مرکزی در انتهای زنجیره دیده شود.
    """
    return (i // PATH_ROW_BOXES, i % PATH_ROW_BOXES)


def _row_wrap_connector(c, prev_box, cur_box, label: str = "", tag: str = "",
                        tag_color=GRAY) -> None:
    """اتصال انتهای یک سطر به ابتدای سطر بعد در نمودار مسیر (Task 24).

    زنجیرهٔ مسیر وقتی از عرض کادر بلندتر شود به سطر بعد می‌رود؛ این helper
    ادامهٔ مسیر را با اتصال Z شکل رسم می‌کند: از پایین جعبهٔ آخر سطر قبل پایین
    می‌آید، در فاصلهٔ بین دو سطر به چپ می‌رود و از بالای جعبهٔ اول سطر بعد وارد
    آن می‌شود — تا زنجیره در سطر بعد هم پیوسته دیده شود و روتر مرکزی داخل
    کادر قابل رویت باشد. (Task 25: فونت برچسب‌ها درشت‌تر شد تا خوانا بماند.)
    """
    px, pby, pw, _ph = prev_box
    cx, cby, cw, ch = cur_box
    x1, x2 = px + pw / 2.0, cx + cw / 2.0
    mid_y = (pby + cby + ch) / 2.0
    c.setStrokeColor(BOX)
    c.setLineWidth(1)
    c.line(x1, pby, x1, mid_y)
    c.line(x1, mid_y, x2, mid_y)
    c.line(x2, mid_y, x2, cby + ch)
    mid_x = (x1 + x2) / 2.0
    if label:
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", PATH_WRAP_LBL_SIZE)
        c.drawCentredString(mid_x, mid_y + 3,
                            _fit(c, label, "Helvetica-Bold", PATH_WRAP_LBL_SIZE,
                                 PAGE_W - 2 * M - 16))
    if tag:
        c.setFillColor(tag_color)
        c.setFont("Helvetica-Oblique", PATH_WRAP_TAG_SIZE)
        c.drawCentredString(mid_x, mid_y - 9, tag)


def _inrow_link_labels(c, mid_x: float, mid: float, from_if: str, to_if: str,
                       ev_tag: str, tag_color=GRAY) -> None:
    """برچسب خوانای لینکِ درون‌سطر در نمودار مسیر (Task 25).

    درخواست کاربر: «اینترفیس‌های دستگاه‌های سمت راست مشخص نیست؛ اندازهٔ برچسب‌ها
    را طوری تغییر بده که قابل خواندن باشند». قبلاً هر دو اینترفیس در «یک خط»
    ریز 5.8pt رسم می‌شد و چون عرض گپ فقط ۳۹٫۸pt بود همیشه بریده می‌شد
    ("ether10 <-> ether24" عرضش ۵۳٫۲pt است). حالا:
      * اینترفیسِ دستگاهِ چپ  بالای خط اتصال (Helvetica-Bold 7.0)
      * اینترفیسِ دستگاهِ راست زیر خط اتصال (Helvetica-Bold 7.0)
      * برچسب شاهد (MNDP/CISCO-ROUTE/...) زیر آن (Helvetica-Oblique 6.0)
    و با جمع‌ترشدن جعبه‌ها (۱۰۴→۹۴) عرض گپ به ~۵۳pt رسیده تا بدون بریدگی جا شود.
    """
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", PATH_IF_SIZE)
    c.drawCentredString(mid_x, mid + 5,
                        _fit(c, from_if, "Helvetica-Bold", PATH_IF_SIZE, PATH_ROW_GAP - 6))
    c.drawCentredString(mid_x, mid - 8.5,
                        _fit(c, to_if, "Helvetica-Bold", PATH_IF_SIZE, PATH_ROW_GAP - 6))
    if ev_tag:
        c.setFillColor(tag_color)
        c.setFont("Helvetica-Oblique", PATH_TAG_SIZE)
        c.drawCentredString(mid_x, mid - 16.5,
                            _fit(c, ev_tag, "Helvetica-Oblique", PATH_TAG_SIZE,
                                 PATH_ROW_GAP - 2))


def _path_diagram(c, y: float, path: dict, nodes: dict, core_key: str, central_ip: str) -> float:
    if path.get("is_core"):
        c.setFillColor(GREEN_BG)
        c.roundRect(M, y - 26, PAGE_W - 2 * M, 22, 4, fill=1, stroke=0)
        c.setFillColor(GREEN)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(M + 10, y - 19, "This device is the core router itself.")
        return y - 40
    hops = path.get("hops") or []
    if not path.get("reachable") or not hops:
        c.setFillColor(RED_BG)
        c.roundRect(M, y - 26, PAGE_W - 2 * M, 22, 4, fill=1, stroke=0)
        c.setFillColor(RED)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(M + 10, y - 19, f"No path to core router {central_ip} discovered from this device.")
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 6.8)
        c.drawString(M + 10, y - 40, "No direct adjacency evidence (check MNDP neighbors, subnets and routes).")
        y = y - 50
        # best-effort upstream chain (default route / longest-prefix next-hops)
        up = path.get("upstream") or []
        if up:
            c.setFillColor(AMBER_BG)
            c.roundRect(M, y - 13, PAGE_W - 2 * M, 15, 3, fill=1, stroke=0)
            c.setFillColor(AMBER)
            c.setFont("Helvetica-Bold", 7)
            c.drawString(M + 10, y - 9, "Best-effort upstream path (via default route / longest prefix) - core not reached:")
            y -= 22
            per_row = PATH_PER_ROW
            bw = PATH_BOX_W
            gap = PATH_ROW_GAP
            bh = PATH_UP_BOX_H  # Task 26: 26→32 — جا برای نام درشت دورَقمی
            shown_up = up[: 2 * per_row]
            node_seq = [up[0]["from_key"]] + [h["to_key"] for h in shown_up]
            y_start = y - 2
            prev_box = None
            for bi, nkey in enumerate(node_seq):
                row, col = path_box_slot(bi)
                nd = nodes.get(nkey) or {}
                x = M + col * (bw + gap)
                by = y_start - row * (bh + PATH_ROW_STRIDE) - bh
                if bi > 0:
                    h = shown_up[bi - 1]
                    from_if = _san(h.get("from_if")) or "?"
                    to_if = _san(h.get("to_if")) or _san(h.get("to_ip")) or "?"
                    ev_tag = "DEFAULT-ROUTE" if h.get("ev") == "default" else "ROUTE"
                    if col > 0:
                        c.setStrokeColor(BOX)
                        c.setLineWidth(1)
                        c.line(x - gap, by + bh / 2, x, by + bh / 2)
                        # Task 25: برچسب خوانا — اینترفیس چپ/راست دو سطر + شاهد
                        _inrow_link_labels(c, x - gap / 2, by + bh / 2, from_if, to_if,
                                           ev_tag, tag_color=AMBER)
                    elif prev_box:
                        # Task 24: شکست سطر — ادامهٔ زنجیرهٔ upstream در سطر بعد
                        _row_wrap_connector(c, prev_box, (x, by, bw, bh),
                                            f"{from_if} <-> {to_if}", ev_tag, tag_color=AMBER)
                ghost = bool(nd.get("ghost"))
                c.setStrokeColor(BOX)
                c.setLineWidth(0.9)
                c.setFillColor((0.996, 0.929, 0.780) if ghost else (0.973, 0.980, 0.988))
                c.roundRect(x, by, bw, bh, 4, fill=1, stroke=1)
                c.setFillColor(INK)
                # Task 26: نام دستگاه درشت (8pt) و در صورت بلند بودن دورَقمی
                nm = (_san(nd.get("name")) or nkey)
                if ghost:
                    nm = nm + " (?)"
                nm_lines = _fit_lines(c, nm, "Helvetica-Bold", PATH_UP_NAME_SIZE, bw - 8, 2)
                c.setFont("Helvetica-Bold", PATH_UP_NAME_SIZE)
                if len(nm_lines) == 1:
                    c.drawCentredString(x + bw / 2, by + bh - 14, nm_lines[0])
                else:
                    c.drawCentredString(x + bw / 2, by + bh - 12, nm_lines[0])
                    c.drawCentredString(x + bw / 2, by + bh - 21, nm_lines[1])
                c.setFillColor(GRAY)
                c.setFont("Helvetica", PATH_UP_IP_SIZE)
                c.drawCentredString(x + bw / 2, by + 4, _fit(c, _san(nd.get("ip")) or "", "Helvetica", PATH_UP_IP_SIZE, bw - 8))
                prev_box = (x, by, bw, bh)
            last_row = path_box_slot(len(node_seq) - 1)[0]
            y = y_start - (last_row + 1) * (bh + PATH_ROW_STRIDE) + 8
            if len(up) > len(shown_up):
                c.setFillColor(GRAY)
                c.setFont("Helvetica-Oblique", 6.5)
                c.drawString(M, y, f"... and {len(up) - len(shown_up)} more upstream hop(s)")
                y -= 10
            last_to = nodes.get(shown_up[-1]["to_key"]) or {}
            c.setFillColor(GRAY)
            c.setFont("Helvetica-Oblique", 6.5)
            c.drawString(M, y, f"Evidence ends at {(_san(last_to.get('ip')) or '?')} - no routing data beyond this hop (add it to the scan to extend the path).")
            y -= 10
        return y
    # chain of node boxes: device -> hop1 -> ... -> core
    # Task 24: هر سطر PATH_ROW_BOXES جعبه دارد و gap برای همان تعداد جعبه محاسبه
    # می‌شود تا سطر دقیقاً داخل کادر صفحه بماند؛ ادامهٔ زنجیره با اتصال Z شکل
    # (_row_wrap_connector) به سطر بعد می‌رود و روتر مرکزی داخل کادر دیده می‌شود
    per_row = PATH_PER_ROW
    bw = PATH_BOX_W
    gap = PATH_ROW_GAP
    bh = PATH_BOX_H  # Task 26: 30→36 — جا برای نام درشت دورَقمی
    shown = hops[: 2 * per_row]
    node_seq = [ (hops[0]["from_key"] if hops else None) ]
    for h in shown:
        node_seq.append(h["to_key"])
    y_start = y - 4
    prev_box = None
    for bi, nkey in enumerate(node_seq):
        row, col = path_box_slot(bi)
        nd = nodes.get(nkey) or {}
        is_core = (nkey == core_key)
        x = M + col * (bw + gap)
        by = y_start - row * (bh + PATH_ROW_STRIDE) - bh
        # connector from previous box
        if bi > 0:
            h = shown[bi - 1]
            from_if = _san(h.get("from_if")) or "?"
            to_if = _san(h.get("to_if")) or "?"
            ev_tag = {"mndp": "MNDP", "subnet": "SUBNET", "route": "ROUTE",
                      "default": "DEFAULT-ROUTE", "cisco": "CISCO-ROUTE"}.get(h.get("ev"), "")
            if col > 0:
                c.setStrokeColor(BOX)
                c.setLineWidth(1)
                c.line(x - gap, by + bh / 2, x, by + bh / 2)
                # Task 25: برچسب خوانا — اینترفیسِ دستگاه چپ بالای خط،
                # اینترفیسِ دستگاه راست زیر خط و برچسب شاهد زیر آن
                _inrow_link_labels(c, x - gap / 2, by + bh / 2, from_if, to_if, ev_tag)
            elif prev_box:
                # Task 24: شکست سطر — ادامهٔ زنجیره در سطر بعد تا روتر مرکزی
                _row_wrap_connector(c, prev_box, (x, by, bw, bh),
                                    f"{from_if} <-> {to_if}", ev_tag)
        c.setStrokeColor(BOX)
        c.setLineWidth(0.9)
        if is_core:
            c.setFillColor(GREEN)
        else:
            c.setFillColor((0.973, 0.980, 0.988))
        c.roundRect(x, by, bw, bh, 4, fill=1, stroke=1)
        c.setFillColor((1, 1, 1) if is_core else INK)
        # Task 26: نام دستگاه درشت (8.5pt) و در صورت بلند بودن دورَقمی داخل جعبه
        nm = _san(nd.get("name")) or nkey
        nm_lines = _fit_lines(c, nm, "Helvetica-Bold", PATH_NAME_SIZE, bw - 8, 2)
        c.setFont("Helvetica-Bold", PATH_NAME_SIZE)
        if len(nm_lines) == 1:
            c.drawCentredString(x + bw / 2, by + bh - 16, nm_lines[0])
        else:
            c.drawCentredString(x + bw / 2, by + bh - 13, nm_lines[0])
            c.drawCentredString(x + bw / 2, by + bh - 22, nm_lines[1])
        c.setFont("Helvetica", PATH_IP_SIZE)
        ip_txt = _san(nd.get("ip")) or _san(nd.get("core_ip")) or ""
        c.setFillColor((0.92, 0.97, 0.94) if is_core else GRAY)
        c.drawCentredString(x + bw / 2, by + 6, _fit(c, ip_txt, "Helvetica", PATH_IP_SIZE, bw - 8))
        prev_box = (x, by, bw, bh)
    last_row = path_box_slot(len(node_seq) - 1)[0]
    y = y_start - (last_row + 1) * (bh + PATH_ROW_STRIDE) + 10
    if len(hops) > len(shown):
        c.setFillColor(GRAY)
        c.setFont("Helvetica-Oblique", 6.5)
        c.drawString(M, y, f"... and {len(hops) - len(shown)} more link(s) to the core")
        y -= 10
    return y


def _hops_table(c, y: float, path: dict, nodes: dict) -> float:
    hops = (path.get("hops") or [])[:8]
    y -= 13
    c.setFillColor(THBG)
    c.rect(M, y - 3, PAGE_W - 2 * M, 12, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(M + 4, y, "#")
    c.drawString(M + 18, y, "From device [interface  IP]")
    c.drawString(M + 250, y, "To device [interface  IP]")
    c.drawString(M + 470, y, "Evidence / Status")
    y -= 12
    c.setFont("Helvetica", 6.8)
    for i, h in enumerate(hops, 1):
        fn = _san((nodes.get(h["from_key"]) or {}).get("name")) or h["from_key"]
        tn = _san((nodes.get(h["to_key"]) or {}).get("name")) or h["to_key"]
        left = f"{fn} [{_san(h.get('from_if')) or '?'}  {_san(h.get('from_ip')) or '-'}]"
        right = f"{tn} [{_san(h.get('to_if')) or '?'}  {_san(h.get('to_ip')) or '-'}]"
        ev = {"mndp": "MNDP neighbor", "subnet": "Shared subnet", "route": "Route gateway",
              "default": "Default-route gateway", "cisco": "Cisco static route"}.get(h.get("ev"), "-")
        c.setFillColor(INK)
        c.drawString(M + 4, y, str(i))
        c.drawString(M + 18, y, _fit(c, left, "Helvetica", 6.8, 226))
        c.drawString(M + 250, y, _fit(c, right, "Helvetica", 6.8, 216))
        c.setFillColor(GREEN)
        c.drawString(M + 470, y, _fit(c, ev + "  VERIFIED", "Helvetica", 6.8, 95))
        y -= 11.2  # Task 26: 12→11.2 — جبران ارتفاع جعبه‌های نمودار
    total = len(path.get("hops") or [])
    if total > len(hops):
        c.setFillColor(GRAY)
        c.setFont("Helvetica-Oblique", 6.5)
        c.drawString(M + 4, y, f"... and {total - len(hops)} more hop(s)")
        y -= 10
    return y


def _evidence_lines(c, y: float, lines: list[str], reachable: bool, central_ip: str) -> float:
    shown = lines[:6]
    c.setFont("Helvetica", 6.8)
    for ln in shown:
        c.setFillColor(INK)
        c.drawString(M + 4, y, _fit(c, _san(ln), "Helvetica", 6.8, PAGE_W - 2 * M - 8))
        y -= 10  # Task 26: 11→10 — جبران ارتفاع جعبه‌های نمودار
    if not shown:
        c.setFillColor(GRAY)
        txt = "No direct routing/adjacency evidence collected for this device."
        if not reachable:
            txt = f"No direct adjacency evidence to core router {central_ip}."
        c.drawString(M + 4, y, txt)
        y -= 10
    return y


def _cisco_evidence_lines(cisco_data: dict, addresses, core_name: str = "",
                          main_ip: str = "", max_lines: int = 3) -> list[str]:
    """خطوط شاهد از روت‌های استاتیک کانفیگ سیسکو برای این دستگاه.

    نشان می‌دهد روتر مرکزی سیسکو چگونه به ساب‌نت این دستگاه مسیر دارد —
    شاهد مکمل قوی از سمتِ مرکز (کانفیگ بارگذاری‌شدهٔ کاربر). همهٔ آدرس‌های
    دستگاه بررسی می‌شوند (IP LAN + IP مدیریتی) و طولانی‌ترین پیشوند اول می‌آید.
    """
    if not cisco_data:
        return []
    try:
        from backend.cisco_config import routes_toward
    except ImportError:
        from cisco_config import routes_toward
    cands: list[str] = []
    for a in addresses or []:
        ip = ((a.get("address") or "").split("/")[0] or "").strip()
        if ip and ip not in cands:
            cands.append(ip)
    mip = (main_ip or "").strip()
    if mip and mip not in cands:
        cands.append(mip)
    seen: set = set()
    out: list[str] = []
    for ip in cands:
        try:
            hits = routes_toward(cisco_data, ip)
        except Exception:
            continue
        for rt in hits:
            key = (rt.get("prefix") or "", tuple(rt.get("next_hops") or []), rt.get("vrf") or "")
            if key in seen:
                continue
            seen.add(key)
            gws = ", ".join(rt.get("next_hops") or []) or (rt.get("interface") or "?")
            out.append(f"cisco {core_name or 'core'}: route {rt.get('prefix') or '?'} via {gws}"
                       + (f" (distance {rt['distance']})" if rt.get("distance") else "")
                       + (f" [vrf {rt['vrf']}]" if rt.get("vrf") else ""))
            if len(out) >= max_lines:
                return out
    return out


def build_route_topology_pdf(topology: dict, devices: list[dict], central_ip: str = "",
                             database: str = "", generated: str = "") -> bytes:
    from datetime import datetime, timezone

    generated = generated or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    central_ip = central_ip or topology.get("central_ip") or "0.0.0.0"
    nodes: dict = topology["nodes"]
    paths: dict = topology["paths"]
    order: list[str] = topology["order"]
    core_key = topology["core_key"]
    cisco_meta = topology.get("cisco") or {}
    cisco_data = topology.get("cisco_data") or None
    core_label = central_ip
    if cisco_meta.get("hostname"):
        core_label = f"{cisco_meta['hostname']} ({central_ip})"
    total = len(order)
    if not total:
        raise ValueError("no devices for PDF")

    buf = io.BytesIO()
    c = pdfcanvas.Canvas(buf, pagesize=A4)
    c.setTitle("Detailed Router Path Topology")
    c.setAuthor("Net_Scan")
    w = PAGE_W - 2 * M

    for idx, key in enumerate(order, 1):
        node = nodes.get(key) or {}
        info = node.get("info") or {}
        dev = node.get("device") or {}
        path = paths.get(key) or {}
        ok_api = bool(info.get("ok"))
        _page_header(c, idx, total, node.get("name") or key, node.get("ip") or "",
                     core_label, generated)
        y = PAGE_H - 66

        # -- connection failure banner --------------------------------------
        if not ok_api:
            c.setFillColor(RED_BG)
            c.roundRect(M, y - 34, w, 30, 4, fill=1, stroke=0)
            c.setFillColor(RED)
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(M + 10, y - 14, "CONNECTION FAILED (RouterOS API)")
            c.setFont("Helvetica", 7)
            c.drawString(M + 10, y - 26, _fit(c, _san(info.get("error")) or "unknown error", "Helvetica", 7, w - 20))
            y -= 44

        # -- router information ----------------------------------------------
        res = info.get("resource") or {}
        ifaces = info.get("interfaces") or []
        y = _section(c, y, "Router Information", f"main IP: {path.get('main_ip') or node.get('ip')}")
        rows = [
            ("Router Name", node.get("name") or dev.get("device_name") or "-"),
            ("Main IP", path.get("main_ip") or node.get("ip") or "-"),
            ("Type", _san(dev.get("device_type")) or "Router"),
            ("Ping", "OK" if dev.get("ping_ok") else "Failed"),
            ("Open Ports", _fmt_ip_list(dev.get("open_ports"))),
            ("Tags", _san(dev.get("tags")) or "-"),
            ("RouterOS", _san(res.get("version")) or "-"),
            ("Board", _san(res.get("board")) or "-"),
            ("Uptime", _san(res.get("uptime")) or "-"),
            ("Interfaces", f"{len(ifaces)} discovered" if ok_api else "-"),
        ]
        y = _kv_grid(c, y, rows)

        # -- IP addresses & interfaces ---------------------------------------
        y = _section(c, y, "IP Addresses & Interfaces", f"({len(info.get('addresses') or [])} found)")
        y = _addr_table(c, y, info.get("addresses") or [])

        # -- interfaces --------------------------------------------------------
        y = _section(c, y, "Interfaces", f"({len(ifaces)} discovered)")
        y = _iface_grid(c, y, ifaces)

        # -- shortest path -----------------------------------------------------
        nh = len(path.get("hops") or [])
        if path.get("is_core"):
            sp_count = "(this device is the core router)"
        elif path.get("reachable"):
            sp_count = f"({nh} link{'s' if nh != 1 else ''} to core, verified)"
        elif path.get("upstream"):
            sp_count = "(unreachable - best-effort upstream path shown)"
        else:
            sp_count = "(unreachable)"
        y = _section(c, y, "Shortest Path", sp_count)
        y = _path_diagram(c, y, path, nodes, core_key, central_ip)

        # -- hop by hop ----------------------------------------------------------
        if path.get("reachable") and (path.get("hops") or []):
            y = _section(c, y, "Hop-by-Hop Link Verification")
            y = _hops_table(c, y, path, nodes)

        # -- evidence ------------------------------------------------------------
        try:
            from route_topology import next_hop_evidence
        except ImportError:
            from backend.route_topology import next_hop_evidence
        next_ip = (path.get("hops") or [{}])[0].get("to_ip", "")
        if not next_ip:
            next_ip = (path.get("upstream") or [{}])[0].get("to_ip", "")
        ev_lines = next_hop_evidence(info, next_ip) if ok_api else []
        cev = _cisco_evidence_lines(cisco_data, node.get("addresses") or [],
                                    (cisco_meta.get("hostname") or "core"),
                                    main_ip=path.get("main_ip") or node.get("ip") or "")
        if cev:
            ev_lines = cev + ev_lines[: max(0, 6 - len(cev))]
        y = _section(c, y, "Routing & Adjacency Evidence", f"toward core {central_ip}")
        _evidence_lines(c, y, ev_lines, bool(path.get("reachable")), central_ip)

        _footer(c, idx, total, database)
        c.showPage()

    c.save()
    return buf.getvalue()
