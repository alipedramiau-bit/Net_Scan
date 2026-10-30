"""Route report (tracert) for the MikroTik devices of the current report.

Runs the traceroute command the user asked for — `tracert -d <ip_device>` on
Windows, `traceroute -n <ip>` on Linux (the `-n` flag is the Linux equivalent
of `-d`: show addresses, never resolve host names) — against every MikroTik
device that matches the report's current search filter and returns the hops
as CSV rows with Persian headers.

The «گزارش روت» dialog asks the user for a source IP and a destination IP
(both defaulting to 172.19.1.6):
- the route to EACH device IP is always traced separately (the command the
  user asked for: `tracert -d ip_device`);
- the user-provided source IP is recorded in the report's «IP مبدأ» column
  (the traces themselves run from the server hosting the app — neither
  Windows tracert nor Linux traceroute allows spoofing an arbitrary source);
- when the user-entered destination differs from the source, the route
  مبدأ→مقصد is additionally traced and placed at the top of the report.

Persian UI strings live here so both the API layer and tests share them.
"""
from __future__ import annotations

import csv
import io
import os
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor

DEFAULT_SOURCE_IP = "172.19.1.6"
DEFAULT_DEST_IP = "172.19.1.6"
DEFAULT_MAX_HOPS = 15
DEFAULT_TIMEOUT_MS = 800

# hop rows always start with the hop number (" 1 ", " 2:", " 3:")
_HOP_RE = re.compile(r"^\s*(\d{1,3})[:\s]")
_IPV4_RE = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b")
_MS_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*ms", re.IGNORECASE)

BASE_ROUTE_LABEL = "مسیر مبدأ تا مقصد"

CSV_HEADERS = ["IP مبدأ", "IP مقصد", "نام دستگاه", "شماره مرحله", "IP مرحله", "تاخیر (ms)", "وضعیت"]

NO_TOOL_ERROR = "ابزار tracert/traceroute روی سرور یافت نشد"
TIMEOUT_ERROR = "مهلت اجرای دستور ردیابی مسیر تمام شد"


def which_tracer_tool() -> str:
    """Name of the traceroute tool available on this host ("" when none)."""
    if os.name == "nt":
        return "tracert"
    for tool in ("traceroute", "tracepath"):
        if shutil.which(tool):
            return tool
    return ""


def build_command(tool: str, target: str, max_hops: int, timeout_ms: int) -> list:
    """Build the traceroute command line for the given tool.

    `-d` on Windows tracert == `-n` on Linux traceroute (no DNS resolution).
    """
    if tool == "tracert":
        return ["tracert", "-d", "-h", str(int(max_hops)), "-w", str(int(timeout_ms)), target]
    if tool == "traceroute":
        # 1 probe per hop (-q 1) keeps large reports reasonably fast
        return ["traceroute", "-n", "-m", str(int(max_hops)),
                "-w", str(max(1, int(round(timeout_ms / 1000.0)))), "-q", "1", target]
    return ["tracepath", "-n", "-m", str(int(max_hops)), target]


def parse_trace_output(text: str) -> list:
    """Tolerant parser for tracert / traceroute / tracepath output.

    Returns a list of hop dicts: {"hop", "ip", "latency_ms", "status"}.
    Lines that do not start with a hop number (headers, footers) are skipped.
    """
    hops = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        m = _HOP_RE.match(line)
        if not m:
            continue
        hop = int(m.group(1))
        ips = _IPV4_RE.findall(line)
        ip = ips[-1] if ips else "*"
        ms = _MS_RE.search(line)
        latency = str(ms.group(1)).replace(",", ".") if ms else ""
        low = line.lower()
        if "unreachable" in low or "!h" in low or "!n" in low or "!x" in low or "!a" in low:
            status = "مقصد/مسیر غیرقابل‌دسترس"
        elif ip == "*":
            status = "بدون پاسخ (timeout)"
        else:
            status = "پاسخ داد"
        hops.append({"hop": hop, "ip": ip, "latency_ms": latency, "status": status})
    return hops


def trace_route(target: str, max_hops: int = DEFAULT_MAX_HOPS,
                timeout_ms: int = DEFAULT_TIMEOUT_MS, tool: str = None) -> dict:
    """Run one traceroute and return {"ok", "tool", "hops", "error"}."""
    target = str(target or "").strip()
    tool = tool or which_tracer_tool()
    if not tool:
        return {"ok": False, "tool": "", "hops": [], "error": NO_TOOL_ERROR}
    cmd = build_command(tool, target, max_hops, timeout_ms)
    # tracert sends 3 probes per hop; give the subprocess a generous ceiling
    timeout_s = max(20.0, int(max_hops) * 3 * (int(timeout_ms) / 1000.0) + 15.0)
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return {"ok": False, "tool": tool, "hops": [], "error": TIMEOUT_ERROR}
    except OSError as e:
        return {"ok": False, "tool": tool, "hops": [], "error": f"خطا در اجرای دستور: {e}"}
    out = (proc.stdout or b"").decode("utf-8", errors="replace")
    if os.name != "nt":
        # traceroute prints its header (and some errors) on stderr
        out += "\n" + (proc.stderr or b"").decode("utf-8", errors="replace")
    hops = parse_trace_output(out)
    if not hops:
        err_lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
        return {"ok": False, "tool": tool, "hops": [],
                "error": err_lines[-1] if err_lines else f"خروجی قابل‌تفسیری از {tool} دریافت نشد"}
    return {"ok": True, "tool": tool, "hops": hops, "error": ""}


def trace_many(targets: list, max_workers: int = 6, **kwargs) -> list:
    """Trace several targets concurrently (input order preserved).

    Returns [{"ip": <target>, "trace": <trace_route result>}, ...].
    """
    targets = list(dict.fromkeys(str(t).strip() for t in (targets or []) if str(t).strip()))
    results = [None] * len(targets)

    def _one(i: int, ip: str):
        results[i] = trace_route(ip, **kwargs)

    workers = max(1, min(int(max_workers or 1), len(targets)))
    if workers == 1:
        for i, ip in enumerate(targets):
            _one(i, ip)
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(_one, i, ip): i for i, ip in enumerate(targets)}
            for f in futures:
                f.result()
    return [{"ip": ip, "trace": results[i]} for i, ip in enumerate(targets)]


def build_route_report_csv(entries: list, source_ip: str, dest_ip: str,
                           base_trace: dict = None) -> bytes:
    """Build the CSV report bytes (UTF-8 BOM, 7 Persian columns).

    entries: [{"ip", "device_name", "trace"}] — one trace per MikroTik device.
    base_trace: optional trace of مبدأ→مقصد placed at the top of the report.
    """
    source_ip = (source_ip or "").strip() or DEFAULT_SOURCE_IP
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(CSV_HEADERS)

    def emit(dest: str, name: str, trace: dict):
        if not trace or not trace.get("ok"):
            writer.writerow([source_ip, dest, name, "", "-", "",
                             "خطا: " + ((trace or {}).get("error") or "ردیابی ناموفق")])
            return
        for h in trace.get("hops") or []:
            writer.writerow([source_ip, dest, name, h.get("hop", ""),
                             h.get("ip", ""), h.get("latency_ms") or "", h.get("status") or ""])

    if base_trace is not None:
        emit(dest_ip, BASE_ROUTE_LABEL, base_trace)
    for e in entries or []:
        emit(e.get("ip") or "", e.get("device_name") or "",
             e.get("trace") or {"ok": False, "error": "بدون نتیجه"})
    return b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8")
