"""E2E verification (Task 26): نام دستگاه در گزارش مسیر باید درشت و خوانا باشد.

درخواست کاربر: «فونت نام دستگاه در بالای گزارش مسیریابی را بزرگتر کن بهتر دیده
شود». این اسکریپت:
1) PDF را با بوم ضبط‌کنندهٔ ReportLab روی توپولوژی شبیه شبکهٔ واقعی کاربر
   (نام‌های بلند مثل RB-Anbar-daruel-HapLite) می‌سازد؛
2) ثابت می‌کند نام هر دستگاه در نوار بالای صفحه با Helvetica-Bold 11 رسم شده؛
3) ثابت می‌کند نام هر جعبهٔ نمودار با 8.5pt (زنجیرهٔ اصلی) / 8.0pt (upstream)
   رسم شده و هیچ سطر نامی از عرض جعبه بیرون نمی‌زند (دورَقمی یا «...»)؛
4) جعبه‌ها 36/32pt ارتفاع دارند و هیچ جعبه‌ای از کادر صفحه بیرون نمی‌زند
   (رگرسیون Task 24/25) و ارتفاع کل صفحه برای «یک صفحه به ازای هر دستگاه» کافی است؛
5) نمونهٔ PDF را برای بازبینی بصری در /tmp/render/route_name_sample.pdf می‌نویسد.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import route_pdf as rpdf
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas as pdfcanvas

ok = True


def check(label, cond, extra=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label, extra)
    ok = ok and cond


BW, GAP = rpdf.PATH_BOX_W, rpdf.PATH_ROW_GAP
MAX_NM_W = BW - 8

# ---------- topology شبیه شبکهٔ واقعی کاربر + یک نام خیلی بلند ----------
NAMES = [
    ("n0", "RB-Anbar-daruel-HapLite", "172.29.196.68"),
    ("n1", "Router.Orzhans", "172.18.24.132"),
    ("n2", "RB-UMS-SHDGN-CoreRouter", "172.18.1.241"),
    ("n3", "VL-Shadegan-Shabankareh", "172.18.1.71"),
    ("n4", "R-Dist-Anbar", "172.19.1.9"),
    ("n5", "R-Core-Bakhtar", "172.19.1.11"),
    ("n6", "SW-Karkheh-Branch", "172.19.1.12"),
    ("n7", "R-Dezfool-Edge", "172.19.1.13"),
    ("core", "SW-Wireless1", "172.19.1.6"),
]
HOP_IFS = [("ether1", "bridge1", "mndp"), ("ether2-input", "ether2", "mndp"),
           ("ether1", "ether3", "route"), ("ether5", "ether1", "default"),
           ("ether9", "ether9", "mndp"), ("ether3", "ether1", "mndp"),
           ("ether2", "ether4", "route"), ("ether1", "ether8", "mndp")]

nodes = {}
for key, name, ip in NAMES:
    nodes[key] = {"name": name, "ip": ip,
                  "info": {"ok": True, "error": None,
                           "resource": {"version": "6.49.7", "board": "hAP lite", "uptime": "3w6d"},
                           "interfaces": [{"name": f"ether{i}", "type": "ether",
                                           "running": "true", "disabled": "false"} for i in range(24)],
                           "addresses": [{"address": f"10.0.{i}.1/24", "interface": f"ether{i}",
                                          "network": f"10.0.{i}.0"} for i in range(12)]},
                  "device": {"device_type": "ST", "ping_ok": True, "open_ports": [22, 8291, 8728],
                             "tags": "Core" if key == "core" else ""},
                  "addresses": []}

hops = []
for i in range(8):
    fk, tk = NAMES[i][0], NAMES[i + 1][0]
    fif, tif, ev = HOP_IFS[i]
    hops.append({"from_key": fk, "to_key": tk, "from_if": fif, "to_if": tif,
                 "from_ip": NAMES[i][2], "to_ip": NAMES[i + 1][2], "ev": ev})

paths = {"core": {"is_core": True, "reachable": True, "hops": [], "upstream": [],
                  "main_ip": "172.19.1.6"},
         "n0": {"is_core": False, "reachable": True, "hops": hops, "upstream": [],
                "main_ip": "172.29.196.68"}}

# دستگاه unreachable با نام خیلی بلند + زنجیرهٔ upstream ۵ hop (۶ جعبه → شکست سطر)
for i in range(4):
    gk = f"g{i}"
    nodes[gk] = {"name": f"GW-Upstream-Unknown-{i + 1}", "ip": f"172.29.200.{i + 1}", "ghost": True}
paths["far"] = {"is_core": False, "reachable": False, "hops": [],
                "upstream": [{"from_key": "far", "to_key": "g0", "from_if": "ether1",
                              "to_ip": "172.29.200.1", "ev": "default"}]
                            + [{"from_key": f"g{i - 1}", "to_key": f"g{i}",
                                "from_if": "ether1", "to_ip": f"172.30.{i}.1", "ev": "default"}
                               for i in range(1, 5)],
                "main_ip": "172.29.200.5"}
nodes["far"] = {"name": "SW-L2-Far-Very-Long-Identity-Name-Branch", "ip": "172.29.200.5",
                "info": {"ok": True, "error": None, "resource": {}, "interfaces": [],
                         "addresses": []},
                "device": {"device_type": "ST", "ping_ok": True, "open_ports": [8728], "tags": ""},
                "addresses": []}

topology = {"nodes": nodes, "paths": paths, "order": ["n0", "far", "core"],
            "core_key": "core", "central_ip": "172.19.1.6", "cisco": {}, "cisco_data": None}


# ---------- بوم ضبط‌کننده ----------
class RecordCanvas(pdfcanvas.Canvas):
    instances = []

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.ops = []
        self.page = 0
        RecordCanvas.instances.append(self)

    def roundRect(self, x, y, w, h, *a, **kw):
        self.ops.append((self.page, "box", float(x), float(y), float(w), float(h)))
        return super().roundRect(x, y, w, h, *a, **kw)

    def line(self, x1, y1, x2, y2):
        self.ops.append((self.page, "line", float(x1), float(y1), float(x2), float(y2)))
        return super().line(x1, y1, x2, y2)

    def setFont(self, f, s):
        self.ops.append((self.page, "font", f, float(s)))
        return super().setFont(f, s)

    def drawString(self, x, y, t, *a, **kw):
        self.ops.append((self.page, "text", float(x), float(y), str(t)))
        return super().drawString(x, y, t, *a, **kw)

    def drawCentredString(self, x, y, t, *a, **kw):
        self.ops.append((self.page, "ctext", float(x), float(y), str(t)))
        return super().drawCentredString(x, y, t, *a, **kw)

    def showPage(self):
        r = super().showPage()
        self.page += 1
        return r


_original_canvas = rpdf.pdfcanvas.Canvas
RecordCanvas.instances.clear()
rpdf.pdfcanvas.Canvas = RecordCanvas
try:
    pdf = rpdf.build_route_topology_pdf(topology, [], central_ip="172.19.1.6",
                                        database="zz_name_font_test", generated="2026-11-01 13:30 UTC")
    rc = RecordCanvas.instances[-1]
finally:
    rpdf.pdfcanvas.Canvas = _original_canvas

check("pdf magic", pdf[:5] == b"%PDF-", str(len(pdf)) + " bytes")
ops = rc.ops
W, M = rpdf.PAGE_W, rpdf.M


def page(p):
    return [op for op in ops if op[0] == p]


def page_boxes(p):
    return [op for op in ops if op[0] == p and op[1] == "box"]


# ---------- 1) نوار بالا: نام دستگاه با Helvetica-Bold 11 ----------
hdr_fonts = [(op[2], op[3]) for op in page(0) if op[1] == "font"]
check("header: device name drawn in Helvetica-Bold 11",
      ("Helvetica-Bold", rpdf.HEADER_NAME_SIZE) in hdr_fonts,
      str(sorted({s for f, s in hdr_fonts})))
hdr_texts = [op[4] for op in page(0) if op[1] == "text"]
check("header: full device name without truncation",
      "RB-Anbar-daruel-HapLite" in hdr_texts)
check("header: ip shown after name", "(172.29.196.68)" in hdr_texts)
# نام در نوار از کادر صفحه بیرون نمی‌زند
hdr_name_ops = [op for op in page(0) if op[1] == "text" and op[4] == "RB-Anbar-daruel-HapLite"]
check("header: name inside page frame",
      hdr_name_ops and hdr_name_ops[0][2] + stringWidth("RB-Anbar-daruel-HapLite",
                                                        "Helvetica-Bold", rpdf.HEADER_NAME_SIZE)
      <= W - M + 0.5)


# ---------- 2) جعبه‌های نمودار: نام درشت و داخل جعبه ----------
def box_name_texts(p, box_h):
    """متن‌های وسط‌چینِ داخل جعبه‌های با ارتفاع box_h + جعبه‌های همان سطر."""
    boxes = [b for b in page_boxes(p) if abs(b[5] - box_h) < 0.1]
    texts = []
    for op in page(p):
        if op[1] != "ctext":
            continue
        _p, _k, x, y, t = op
        for b in boxes:
            if b[2] - 1 <= x <= b[2] + b[4] + 1 and b[3] <= y <= b[3] + b[5] + 1:
                texts.append((x, y, t, b))
                break
    return boxes, texts


for p, box_h, name_size in ((0, rpdf.PATH_BOX_H, rpdf.PATH_NAME_SIZE),
                            (1, rpdf.PATH_UP_BOX_H, rpdf.PATH_UP_NAME_SIZE)):
    boxes, texts = box_name_texts(p, box_h)
    check(f"page {p}: path boxes have new height {box_h}", len(boxes) >= 6, str(len(boxes)))
    big = [op for op in page(p) if op[1] == "font" and op[2] == "Helvetica-Bold"
           and abs(op[3] - name_size) < 0.01]
    check(f"page {p}: box names drawn in Helvetica-Bold {name_size}", len(big) >= 6, str(len(big)))
    # هیچ نام/سطرِ اینترفیسِ داخل جعبه از عرض جعبه بیرون نمی‌زند
    overflow = []
    for x, y, t, b in texts:
        w = max(stringWidth(t, "Helvetica-Bold", name_size),
                stringWidth(t, "Helvetica", name_size),
                stringWidth(t, "Helvetica-Bold", rpdf.PATH_IP_SIZE if p == 0 else rpdf.PATH_UP_IP_SIZE),
                stringWidth(t, "Helvetica", rpdf.PATH_IP_SIZE if p == 0 else rpdf.PATH_UP_IP_SIZE))
        if w > b[4] - 6 + 0.6:
            overflow.append((t, w))
    check(f"page {p}: no box text wider than its box", not overflow, str(overflow[:3]))
    # جعبه‌ها داخل کادر صفحه‌اند (رگرسیون Task 24)
    outside = [b for b in boxes if b[2] < M - 0.5 or b[2] + b[4] > W - M + 0.5]
    check(f"page {p}: all boxes inside page frame", not outside, str(len(outside)))

# نام دورَقمی: دستگاه با نام خیلی بلند روی صفحهٔ unreachable باید در ۲ سطر داخل جعبه باشد
_u_boxes, u_texts = box_name_texts(1, rpdf.PATH_UP_BOX_H)
long_lines = [(x, y, t) for x, y, t, b in u_texts
              if t.startswith("SW-L2-Far") or t.startswith("Branch")]
check("long name wrapped into box (2 lines or ellipsized inside)",
      long_lines and all(stringWidth(t, "Helvetica-Bold", rpdf.PATH_UP_NAME_SIZE)
                         <= MAX_NM_W + 0.6 for _x, _y, t in long_lines),
      str([t for _x, _y, t in long_lines]))

# ---------- 3) یک صفحه به ازای هر دستگاه: ارتفاع محتوا بالای فوتر تمام می‌شود ----------
# آخرین متن بدنهٔ هر صفحه باید با فاصلهٔ تمیز بالای خط فوتر (y=32) تمام شود
for p in (0, 1):
    body_texts = [op for op in page(p) if op[1] in ("text", "ctext") and op[3] > 26]
    min_y = min((op[3] for op in body_texts), default=0)
    check(f"page {p}: body stays clear of the footer line", min_y >= 34, f"min text y={min_y:.1f}")
check("8-hop worst case reaches the table cap", len(hops) == 8, str(len(hops)))

# ---------- 4) خروجی نمونه برای بازبینی بصری ----------
out_dir = "/tmp/render"
os.makedirs(out_dir, exist_ok=True)
out_pdf = os.path.join(out_dir, "route_name_sample.pdf")
with open(out_pdf, "wb") as f:
    f.write(pdf)
print("sample pdf:", out_pdf)

print("\nALL OK" if ok else "\nFAILURES PRESENT")
sys.exit(0 if ok else 1)
