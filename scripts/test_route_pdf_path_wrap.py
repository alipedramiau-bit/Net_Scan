"""E2E verification (Task 24): نمودار Shortest Path باید داخل کادر صفحه بماند.

باگ گزارش کاربر (تصویر PDF صفحهٔ RB-Anbar-daruel-HapLite): هر سطر نمودار ۴ جعبه
دارد ولی gap برای ۳ جعبه محاسبه می‌شد؛ جعبه‌های انتهای زنجیره از کادر صفحه بیرون
می‌زدند و روتر مرکزی دیده نمی‌شد. این اسکریپت:
1) PDF یک زنجیرهٔ ۵ hop (شبیه شبکهٔ واقعی کاربر) و یک دستگاه unreachable با
   زنجیرهٔ upstream ۵ hop را می‌سازد؛
2) با بوم ضبط‌کنندهٔ ReportLab مختصات «همهٔ» جعبه‌ها و خطوط را می‌گیرد و ثابت
   می‌کند هیچ جعبه‌ای از کادر صفحه بیرون نمی‌زند و روتر مرکزی داخل کادر است؛
3) اتصال Z شکل ادامهٔ زنجیره به سطر بعد (خط افقی راست‌به‌چپ بین دو سطر) را
   روی هر دو صفحه تأیید می‌کند؛
4) نمونهٔ PDF را برای بازبینی بصری در /tmp/render/route_wrap_sample.pdf می‌نویسد.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import route_pdf as rpdf
from reportlab.pdfgen import canvas as pdfcanvas

ok = True


def check(label, cond, extra=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label, extra)
    ok = ok and cond


W, HGT = rpdf.PAGE_W, rpdf.PAGE_H
M = rpdf.M
BW, GAP = rpdf.PATH_BOX_W, rpdf.PATH_ROW_GAP

# ---------- topology شبیه شبکهٔ واقعی کاربر (تصویر پیوست) ----------
NAMES = [
    ("n0", "RB-Anbar-daruel-HapLite", "172.29.196.68"),
    ("n1", "Router.Orzhans", "172.18.24.132"),
    ("n2", "RB-UMS-SHDGN-CoreRouter", "172.18.1.241"),
    ("n3", "VL-Shadegan-Shabankareh", "172.18.1.71"),
    ("n4", "R-Dist-Anbar", "172.19.1.9"),
    ("core", "SW-Wireless1", "172.19.1.6"),
]
HOP_IFS = [("ether1", "bridge1", "mndp"), ("ether2-input", "ether2", "mndp"),
           ("ether1", "ether3", "route"), ("ether5", "ether1", "default"),
           ("ether9", "ether9", "mndp")]

nodes = {}
for key, name, ip in NAMES:
    nodes[key] = {"name": name, "ip": ip,
                  "info": {"ok": True, "error": None,
                           "resource": {"version": "6.49.7", "board": "hAP lite", "uptime": "3w6d"},
                           "interfaces": [], "addresses": []},
                  "device": {"device_type": "ST", "ping_ok": True, "open_ports": [22, 8291, 8728],
                             "tags": "Core" if key == "core" else ""},
                  "addresses": []}

hops = []
for i in range(5):
    fk, tk = NAMES[i][0], NAMES[i + 1][0]
    fif, tif, ev = HOP_IFS[i]
    hops.append({"from_key": fk, "to_key": tk, "from_if": fif, "to_if": tif,
                 "from_ip": NAMES[i][2], "to_ip": NAMES[i + 1][2], "ev": ev})

paths = {"core": {"is_core": True, "reachable": True, "hops": [], "upstream": [],
                  "main_ip": "172.19.1.6"},
         "n0": {"is_core": False, "reachable": True, "hops": hops, "upstream": [],
                "main_ip": "172.29.196.68"}}

# دستگاه unreachable با زنجیرهٔ upstream ۵ hop (۶ جعبه → شکست سطر)
for i in range(4):
    gk = f"g{i}"
    nodes[gk] = {"name": f"GW-{i + 1}", "ip": f"172.29.200.{i + 1}", "ghost": True}
paths["n5"] = {"is_core": False, "reachable": False, "hops": [],
               "upstream": [{"from_key": "n5", "to_key": "g0", "from_if": "ether1",
                             "to_ip": "172.29.200.1", "ev": "default"}]
                           + [{"from_key": f"g{i - 1}", "to_key": f"g{i}",
                               "from_if": "ether1", "to_ip": f"172.30.{i}.1", "ev": "default"}
                              for i in range(1, 5)],
               "main_ip": "172.29.200.5"}
nodes["n5"] = {"name": "SW-L2-Far", "ip": "172.29.200.5",
               "info": {"ok": True, "error": None, "resource": {}, "interfaces": [],
                        "addresses": []},
               "device": {"device_type": "ST", "ping_ok": True, "open_ports": [8728], "tags": ""},
               "addresses": []}

topology = {"nodes": nodes, "paths": paths, "order": ["n0", "n5", "core"],
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

    def showPage(self):
        r = super().showPage()
        self.page += 1
        return r


_original_canvas = rpdf.pdfcanvas.Canvas
RecordCanvas.instances.clear()
rpdf.pdfcanvas.Canvas = RecordCanvas
try:
    pdf = rpdf.build_route_topology_pdf(topology, [], central_ip="172.19.1.6",
                                        database="zz_wrap_test", generated="2026-11-01 13:30 UTC")
    rc = RecordCanvas.instances[-1]
finally:
    rpdf.pdfcanvas.Canvas = _original_canvas

check("pdf magic", pdf[:5] == b"%PDF-", str(len(pdf)) + " bytes")
ops = rc.ops


def page_boxes(p):
    return [op for op in ops if op[0] == p and op[1] == "box"]


def page_lines(p):
    return [op for op in ops if op[0] == p and op[1] == "line"]


# ---------- 1) هیچ جعبه‌ای از کادر صفحه بیرون نمی‌زند (رفع باگ اصلی) ----------
all_boxes = [op for op in ops if op[1] == "box"]
outside = [b for b in all_boxes if b[2] < M - 0.5 or b[2] + b[4] > W - M + 0.5]
check("no box outside page frame (all pages)", not outside,
      f"{len(outside)} outside, worst x+w={max((b[2] + b[4] for b in all_boxes), default=0):.1f} <= {W - M:.1f}")

# ---------- 2) صفحهٔ reachable: ۶ جعبه در ۲ سطر + اتصال Z شکل ----------
pb = [b for b in page_boxes(0) if abs(b[5] - rpdf.PATH_BOX_H) < 0.1]
check("reachable page: 6 path boxes", len(pb) == 6, str(len(pb)))
rows_y = sorted({round(b[3], 1) for b in pb}, reverse=True)
check("reachable page: boxes on 2 rows (wrap happened)", len(rows_y) == 2, str(rows_y))
row0 = [b for b in pb if abs(b[3] - rows_y[0]) < 0.1]
row1 = [b for b in pb if abs(b[3] - rows_y[1]) < 0.1]
check("row0 has 4 boxes / row1 has 2 boxes", len(row0) == 4 and len(row1) == 2,
      f"{len(row0)}/{len(row1)}")
xs0 = sorted(round(b[2], 1) for b in row0)
xs1 = sorted(round(b[2], 1) for b in row1)
check("row0 x positions inside frame", xs0[0] >= M - 0.5 and xs0[-1] + BW <= W - M + 0.5, str(xs0))
check("row1 starts at left margin (continuation row)", abs(xs1[0] - M) < 0.5, str(xs1))
# آخرین جعبهٔ سطر ۱ = روتر مرکزی (سبز) — باید داخل کادر باشد
core_box = max(pb, key=lambda b: (b[3], b[2]))
check("core router box inside frame", core_box[2] >= M - 0.5 and core_box[2] + core_box[4] <= W - M + 0.5,
      f"x={core_box[2]:.1f} w={core_box[4]:.1f}")
# اتصال Z شکل: خط افقی راست‌به‌چپ بین دو سطر (یگانه امضای _row_wrap_connector)
wrap_lines = [l for l in page_lines(0) if l[3] == l[5] and l[2] > l[4] and (l[2] - l[4]) > 300]
check("reachable page: Z-shaped row-wrap connector present", len(wrap_lines) >= 1, str(wrap_lines[:1]))
gutter_top, gutter_bottom = rows_y[1] + rpdf.PATH_BOX_H, rows_y[0]
check("wrap connector lies in the gutter between rows",
      all(gutter_bottom > l[3] > gutter_top for l in wrap_lines),
      f"gutter {gutter_top:.1f}..{gutter_bottom:.1f}, y={wrap_lines[0][3]:.1f}" if wrap_lines else "")

# ---------- 3) صفحهٔ unreachable: زنجیرهٔ upstream هم wrap می‌شود ----------
ub = [b for b in page_boxes(1) if abs(b[5] - rpdf.PATH_UP_BOX_H) < 0.1]
check("unreachable page: 6 upstream boxes", len(ub) == 6, str(len(ub)))
urows_y = sorted({round(b[3], 1) for b in ub}, reverse=True)
check("unreachable page: 2 rows", len(urows_y) == 2, str(urows_y))
uwrap = [l for l in page_lines(1) if l[3] == l[5] and l[2] > l[4] and (l[2] - l[4]) > 300]
check("unreachable page: Z-shaped row-wrap connector present", len(uwrap) >= 1)

# ---------- 4) زنجیره‌های بلندتر از ۶ hop همچنان سرریز نمی‌کنند ----------
hops9 = []
N9 = [(f"k{i}", f"R-Hop-{i}", f"10.9.0.{i}") for i in range(8)] + [("core9", "R-Core9", "10.9.0.99")]
nodes9 = {k: {"name": n, "ip": ip, "info": {"ok": True, "error": None, "resource": {},
                                            "interfaces": [], "addresses": []},
              "device": {"device_type": "ST", "ping_ok": True, "open_ports": [], "tags": ""},
              "addresses": []} for k, n, ip in N9}
for i in range(8):
    hops9.append({"from_key": f"k{i}", "to_key": (N9[i + 1][0]), "from_if": "ether1",
                  "to_if": "ether2", "from_ip": N9[i][2], "to_ip": N9[i + 1][2], "ev": "mndp"})
topo9 = {"nodes": nodes9, "paths": {"k0": {"is_core": False, "reachable": True, "hops": hops9,
                                           "upstream": [], "main_ip": "10.9.0.0"},
                                    "core9": {"is_core": True, "reachable": True, "hops": [],
                                              "upstream": [], "main_ip": "10.9.0.99"}},
         "order": ["k0", "core9"], "core_key": "core9", "central_ip": "10.9.0.99",
         "cisco": {}, "cisco_data": None}
_Cap = RecordCanvas
RecordCanvas.instances.clear()
rpdf.pdfcanvas.Canvas = _Cap
try:
    rpdf.build_route_topology_pdf(topo9, [], central_ip="10.9.0.99", database="zz_wrap_test",
                                  generated="2026-11-01 13:30 UTC")
    rc9 = _Cap.instances[-1]
finally:
    rpdf.pdfcanvas.Canvas = _original_canvas
boxes9 = [op for op in rc9.ops if op[1] == "box" and abs(op[5] - rpdf.PATH_BOX_H) < 0.1]
outside9 = [b for b in boxes9 if b[2] < M - 0.5 or b[2] + b[4] > W - M + 0.5]
check("9-hop chain: all shown boxes inside frame", not outside9, f"{len(boxes9)} boxes")
check("9-hop chain: still capped at 2 rows (one page per device)", len({round(b[3], 1) for b in boxes9}) == 2)

# ---------- 5) خروجی نمونه برای بازبینی بصری ----------
out_dir = "/tmp/render"
os.makedirs(out_dir, exist_ok=True)
out_pdf = os.path.join(out_dir, "route_wrap_sample.pdf")
with open(out_pdf, "wb") as f:
    f.write(pdf)
print("sample pdf:", out_pdf)

print("\nALL OK" if ok else "\nFAILURES PRESENT")
sys.exit(0 if ok else 1)
