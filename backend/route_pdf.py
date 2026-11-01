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
    line_h = 13
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
    c.drawString(M, top - 22, "Detailed Router Path Topology")
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(PAGE_W - M, top - 21, f"Router {idx} of {total}")
    c.setFont("Helvetica", 7.5)
    c.setFillColor((0.82, 0.87, 0.93))
    c.drawString(M, top - 36, _fit(c, f"Target: {_san(name)}  ({ip})", "Helvetica", 7.5, 300))
    c.drawRightString(PAGE_W - M, top - 36, f"Core Router: {central_ip}")
    c.drawString(M, top - 47, _san(generated)[:110])


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
        y -= 11.5
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
        ry = y - 11 * (idx % per_col) - 11
        run = (it.get("running") or "").lower() == "true" and (it.get("disabled") or "").lower() != "true"
        state = "up" if run else ("off" if (it.get("disabled") or "").lower() == "true" else "down")
        c.setFillColor(GREEN if run else GRAY)
        c.rect(cx, ry - 1, 3, 7, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont("Helvetica", 6.8)
        c.drawString(cx + 6, ry, _fit(c, f"{_san(it.get('name'))} ({_san(it.get('type')) or '-'}) {state}",
                                      "Helvetica", 6.8, col_w - 10))
    # tallest column = min(n, per_col) rows (column-major layout)
    y -= 11 * min(len(shown), per_col) + 2
    if len(rows) > len(shown):
        c.setFillColor(GRAY)
        c.setFont("Helvetica-Oblique", 6.5)
        c.drawString(M, y, f"... and {len(rows) - len(shown)} more interface(s)")
        y -= 10
    return y


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
            per_row = 3
            bw = 104
            gap = (PAGE_W - 2 * M - per_row * bw) / max(1, (per_row - 1))
            bh = 26
            shown_up = up[: 2 * per_row]
            node_seq = [up[0]["from_key"]] + [h["to_key"] for h in shown_up]
            y_start = y - 2
            row = 0
            col = 0
            for bi, nkey in enumerate(node_seq):
                nd = nodes.get(nkey) or {}
                x = M + col * (bw + gap)
                by = y_start - row * (bh + 30) - bh
                if bi > 0:
                    h = shown_up[bi - 1]
                    if col > 0:
                        c.setStrokeColor(BOX)
                        c.setLineWidth(1)
                        c.line(x - gap, by + bh / 2, x, by + bh / 2)
                        lbl = f"{_san(h.get('from_if')) or '?'} -> {_san(h.get('to_if')) or _san(h.get('to_ip')) or '?'}"
                        c.setFillColor(INK)
                        c.setFont("Helvetica-Bold", 5.8)
                        c.drawCentredString(x - gap / 2, by + bh / 2 + 4, _fit(c, lbl, "Helvetica-Bold", 5.8, gap - 4))
                        c.setFillColor(AMBER)
                        c.setFont("Helvetica-Oblique", 5.2)
                        c.drawCentredString(x - gap / 2, by + bh / 2 - 9, "DEFAULT-ROUTE" if h.get("ev") == "default" else "ROUTE")
                ghost = bool(nd.get("ghost"))
                c.setStrokeColor(BOX)
                c.setLineWidth(0.9)
                c.setFillColor((0.996, 0.929, 0.780) if ghost else (0.973, 0.980, 0.988))
                c.roundRect(x, by, bw, bh, 4, fill=1, stroke=1)
                c.setFillColor(INK)
                c.setFont("Helvetica-Bold", 6.6)
                nm = (_san(nd.get("name")) or nkey)
                if ghost:
                    nm = nm + " (?)"
                c.drawCentredString(x + bw / 2, by + bh - 11, _fit(c, nm, "Helvetica-Bold", 6.6, bw - 8))
                c.setFillColor(GRAY)
                c.setFont("Helvetica", 5.8)
                c.drawCentredString(x + bw / 2, by + 6, _fit(c, _san(nd.get("ip")) or "", "Helvetica", 5.8, bw - 8))
                col += 1
                if col >= per_row + 1:
                    col = 0
                    row += 1
            y = y_start - (row + 1) * (bh + 30) + 8
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
    per_row = 3  # 3 hops = 4 boxes
    bw = 104
    gap = (PAGE_W - 2 * M - per_row * bw) / max(1, (per_row - 1))
    bh = 30
    shown = hops[: 2 * per_row]
    node_seq = [ (hops[0]["from_key"] if hops else None) ]
    for h in shown:
        node_seq.append(h["to_key"])
    y_start = y - 4
    row = 0
    col = 0
    for bi, nkey in enumerate(node_seq):
        nd = nodes.get(nkey) or {}
        is_core = (nkey == core_key)
        x = M + col * (bw + gap)
        by = y_start - row * (bh + 34) - bh
        # connector from previous box
        if bi > 0:
            h = shown[bi - 1]
            px = M + (col - 1) * (bw + gap) if col > 0 else None
            if col > 0:
                c.setStrokeColor(BOX)
                c.setLineWidth(1)
                c.line(x - gap, by + bh / 2, x, by + bh / 2)
                lbl = f"{_san(h.get('from_if')) or '?'} <-> {_san(h.get('to_if')) or '?'}"
                c.setFillColor(INK)
                c.setFont("Helvetica-Bold", 5.8)
                c.drawCentredString(x - gap / 2, by + bh / 2 + 4, _fit(c, lbl, "Helvetica-Bold", 5.8, gap - 4))
                c.setFillColor(GRAY)
                c.setFont("Helvetica-Oblique", 5.2)
                c.drawCentredString(x - gap / 2, by + bh / 2 - 9, {"mndp": "MNDP", "subnet": "SUBNET", "route": "ROUTE", "default": "DEFAULT-ROUTE"}.get(h.get("ev"), ""))
        c.setStrokeColor(BOX)
        c.setLineWidth(0.9)
        if is_core:
            c.setFillColor(GREEN)
        else:
            c.setFillColor((0.973, 0.980, 0.988))
        c.roundRect(x, by, bw, bh, 4, fill=1, stroke=1)
        c.setFillColor((1, 1, 1) if is_core else INK)
        c.setFont("Helvetica-Bold", 6.6)
        c.drawCentredString(x + bw / 2, by + bh - 12, _fit(c, _san(nd.get("name")) or nkey, "Helvetica-Bold", 6.6, bw - 8))
        c.setFont("Helvetica", 6)
        ip_txt = _san(nd.get("ip")) or _san(nd.get("core_ip")) or ""
        c.setFillColor((0.92, 0.97, 0.94) if is_core else GRAY)
        c.drawCentredString(x + bw / 2, by + 7, _fit(c, ip_txt, "Helvetica", 6, bw - 8))
        col += 1
        if col >= per_row + 1:
            col = 0
            row += 1
    y = y_start - (row + 1) * (bh + 34) + 10
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
              "default": "Default-route gateway"}.get(h.get("ev"), "-")
        c.setFillColor(INK)
        c.drawString(M + 4, y, str(i))
        c.drawString(M + 18, y, _fit(c, left, "Helvetica", 6.8, 226))
        c.drawString(M + 250, y, _fit(c, right, "Helvetica", 6.8, 216))
        c.setFillColor(GREEN)
        c.drawString(M + 470, y, _fit(c, ev + "  VERIFIED", "Helvetica", 6.8, 95))
        y -= 12
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
        y -= 11
    if not shown:
        c.setFillColor(GRAY)
        txt = "No direct routing/adjacency evidence collected for this device."
        if not reachable:
            txt = f"No direct adjacency evidence to core router {central_ip}."
        c.drawString(M + 4, y, txt)
        y -= 11
    return y


def build_route_topology_pdf(topology: dict, devices: list[dict], central_ip: str = "",
                             database: str = "", generated: str = "") -> bytes:
    from datetime import datetime, timezone

    generated = generated or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    central_ip = central_ip or topology.get("central_ip") or "0.0.0.0"
    nodes: dict = topology["nodes"]
    paths: dict = topology["paths"]
    order: list[str] = topology["order"]
    core_key = topology["core_key"]
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
                     central_ip, generated)
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
        y = _section(c, y, "Routing & Adjacency Evidence", f"toward core {central_ip}")
        _evidence_lines(c, y, ev_lines, bool(path.get("reachable")), central_ip)

        _footer(c, idx, total, database)
        c.showPage()

    c.save()
    return buf.getvalue()
