"""Interface link flap detection and Excel report helpers."""
from __future__ import annotations
from datetime import datetime, timedelta
import ipaddress
import re
from io import BytesIO, StringIO
import csv

_LINE = re.compile(
    r"^\s*(?:\d+\s+)?(?P<stamp>(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|"
    r"[A-Za-z]{3}/\d{1,2})\s+\d{2}:\d{2}:\d{2}|"
    r"\d{2}:\d{2}:\d{2})\s+(?P<message>.*)$", re.I)
# Topics may be single ("info") or comma-separated ("interface,info,debug").
# Interface names may include /, ., @, :, <>, e.g. sfp-sfpplus1, <pppoe-out1>, ether1.
_LINK_EVENT = re.compile(
    r"^\s*(?:\[[^]]*\]\s*)?"
    r"(?:(?P<topics>[\w-]+(?:,[\w-]+)*)\s+)?"
    r"(?P<interface>[\w./@<>:+-]+?)\s*:?\s+link\s+(?P<status>up|down)\b",
    re.I,
)
_MONTHS = {name.lower(): number for number, name in enumerate(
    ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"), 1)}
_GREGORIAN_YEAR = 1600

def jalali_to_gregorian(jy, jm, jd):
    """Convert Jalali calendar date to Gregorian (integer arithmetic)."""
    jy += 1595
    days = -355668 + 365 * jy + (jy // 33) * 8 + ((jy % 33 + 3) // 4) + jd
    if jm < 7: days += (jm - 1) * 31
    else: days += (jm - 7) * 30 + 186
    gy = 400 * (days // 146097)
    days %= 146097
    if days > 36524:
        gy += 100 * ((days - 1) // 36524); days = (days - 1) % 36524
        if days >= 365: days += 1
    gy += 4 * (days // 1461); days %= 1461
    if days > 365:
        gy += (days - 1) // 365; days = (days - 1) % 365
    gd = days + 1
    leap = (gy % 4 == 0 and gy % 100 != 0) or gy % 400 == 0
    month_days = [0,31,29 if leap else 28,31,30,31,30,31,31,30,31,30,31]
    gm = 1
    while gm <= 12 and gd > month_days[gm]:
        gd -= month_days[gm]; gm += 1
    return gy, gm, gd

def gregorian_to_jalali(gy, gm, gd):
    """Convert Gregorian date to Jalali using integer day arithmetic."""
    g_days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    j_days_in_month = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]
    gy -= 1600
    g_day_no = (365 * gy + (gy + 3) // 4 - (gy + 99) // 100 + (gy + 399) // 400)
    for month in range(1, gm):
        g_day_no += g_days_in_month[month - 1]
    if gm > 2 and ((gy % 4 == 0 and gy % 100 != 0) or gy % 400 == 0):
        g_day_no += 1
    g_day_no += gd - 1

    j_day_no = g_day_no - 79
    j_np = j_day_no // 12053
    j_day_no %= 12053
    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)
    j_day_no %= 1461
    if j_day_no >= 366:
        jy += (j_day_no - 1) // 365
        j_day_no = (j_day_no - 1) % 365
    jm = 1
    while jm <= 12 and j_day_no >= j_days_in_month[jm - 1]:
        j_day_no -= j_days_in_month[jm - 1]
        jm += 1
    return jy, jm, j_day_no + 1


def jalali_datetime_string(value):
    """Format a datetime as Jalali YYYY/MM/DD HH:MM:SS."""
    jy, jm, jd = gregorian_to_jalali(value.year, value.month, value.day)
    return f"{jy:04d}/{jm:02d}/{jd:02d} {value:%H:%M:%S}"


def parse_log_datetime(value, reference=None):
    """Parse Gregorian, legacy Jalali, abbreviated-month, and time-only dates.

    Yearless dates are assigned the year nearest the supplied reference (or
    today), which naturally handles logs spanning a year boundary.
    """
    reference = reference or datetime.now()
    value = value.strip()
    if re.fullmatch(r"\d{2}:\d{2}:\d{2}", value):
        return datetime.combine(reference.date(), datetime.strptime(value, "%H:%M:%S").time())
    month_match = re.fullmatch(r"([A-Za-z]{3})/(\d{1,2})\s+(\d{2}:\d{2}:\d{2})", value)
    if month_match:
        month = _MONTHS.get(month_match.group(1).lower())
        if not month:
            raise ValueError("Unknown month abbreviation")
        day, clock = int(month_match.group(2)), datetime.strptime(month_match.group(3), "%H:%M:%S").time()
        candidates = []
        for year in (reference.year - 1, reference.year, reference.year + 1):
            try:
                candidates.append(datetime(year, month, day, clock.hour, clock.minute, clock.second))
            except ValueError:
                pass
        if not candidates:
            raise ValueError("Invalid yearless date")
        return min(candidates, key=lambda item: abs((item - reference).total_seconds()))
    normalized = value.replace("-", "/")
    dt = datetime.strptime(normalized, "%Y/%m/%d %H:%M:%S")
    if dt.year < _GREGORIAN_YEAR:
        gy, gm, gd = jalali_to_gregorian(dt.year, dt.month, dt.day)
        return dt.replace(year=gy, month=gm, day=gd)
    return dt

def parse_device_log(device, now=None, days_back=5, threshold_minutes=5):
    """Return latest flap per interface.

    In addition to the existing short-interval detection, report an interface
    from the third event onward in a consecutive alternating sequence (at
    least two transitions), provided each adjacent event is less than one hour
    apart.
    """
    now = now or datetime.now()
    cutoff = now - timedelta(days=max(0, int(days_back)))
    grouped = {}
    for line in (device.get("device_log") or "").splitlines():
        match = _LINE.match(line)
        if not match: continue
        event = _LINK_EVENT.match(match.group("message"))
        if not event: continue
        try: when = parse_log_datetime(match.group("stamp"), reference=now)
        except (ValueError, OverflowError): continue
        if when < cutoff or when > now + timedelta(minutes=1): continue
        iface = event.group("interface").strip().rstrip(":").strip()
        # Drop accidental topic words captured as interface when topics group missed.
        if iface.lower() in {"info", "debug", "warning", "error", "critical", "system", "interface", "link", "wireless"}:
            continue
        status = event.group("status").title()
        if iface:
            grouped.setdefault(iface, []).append((when, status))
    found=[]
    threshold=timedelta(minutes=max(0, int(threshold_minutes)))
    one_hour=timedelta(hours=1)
    for iface, events in grouped.items():
        events.sort(key=lambda item:item[0])
        flaps=[]
        alternating_transitions=0
        for prev, cur in zip(events, events[1:]):
            gap=cur[0]-prev[0]
            if prev[1] != cur[1]:
                if timedelta(0) <= gap <= threshold:
                    flaps.append(cur)  # Preserve the existing short-flap rule.
                if timedelta(0) <= gap < one_hour:
                    alternating_transitions += 1
                    if alternating_transitions >= 2:
                        flaps.append(cur)
                else:
                    alternating_transitions=0
            else:
                alternating_transitions=0
        # A record can satisfy both rules; count unique event records once.
        flaps=list(dict.fromkeys(flaps))
        if flaps:
            latest=max(flaps,key=lambda item:item[0])
            raw_tags = device.get('tags') or device.get('device_tag') or device.get('tag') or ''
            if isinstance(raw_tags, list):
                tag_str = ', '.join(str(t).strip() for t in raw_tags if str(t).strip())
            else:
                tag_str = str(raw_tags).strip()
            found.append({"datetime":latest[0].isoformat(sep=" "),
                          "datetime_jalali":jalali_datetime_string(latest[0]),
                          "device_name":device.get("device_name") or "",
                          "tags":tag_str, "device_tag": tag_str,
                          "ip":device.get("ip") or "", "interface":iface, "last_status":latest[1],
                          "flap_count":len(flaps)})
    return found

# ---------------- Smart report: neighbor device on the flapping interface ----------------
# Both stored shapes of /ip neighbor (and /ip address) are whitespace-separated
# "key=value" tokens:
#   compact:  "  1  identity=Core-SW  address=10.0.0.2  interface=ether2"
#   sentence: "  interface=ether2  mac-address=AA:BB..  address=10.0.0.2  identity=Core-SW"
# The value ends at the next "<key>=" token, so unknown keys that follow (like
# board-name/uptime) cannot be swallowed into the previous value.
_KV_RE = re.compile(r"(?P<key>[A-Za-z][\w.-]*)=(?P<val>.*?)(?=\s+[A-Za-z][\w.-]*=|$)")

def _ip4(value):
    """Return a clean IPv4 string (mask stripped) or empty string."""
    raw = str(value or "").split("/")[0].strip()
    try:
        return str(ipaddress.IPv4Address(raw))
    except ValueError:
        return ""

def _kv_of_line(line):
    """Extract known key=value pairs from one stored RouterOS print line."""
    if "=" not in line:
        return {}
    return {m.group("key").lower(): m.group("val").strip() for m in _KV_RE.finditer(line)}

def parse_neighbor_entries(text):
    """Parse a stored /ip neighbor text block into entries.

    Accepts both persisted shapes (compact collect_device_info lines and the
    API sentence dump of collect_ip_info). Entries without a local interface
    are useless for this report and skipped.
    """
    entries = []
    for line in (text or "").splitlines():
        kv = _kv_of_line(line)
        iface = (kv.get("interface") or kv.get("interface-name") or "").strip()
        if not iface:
            continue
        entries.append({
            "interface": iface,
            "identity": (kv.get("identity") or "").strip(),
            "address": (kv.get("address") or "").strip(),
            "mac": (kv.get("mac-address") or "").strip(),
        })
    return entries

def parse_self_addresses(text):
    """Parse a stored /ip address text block into {iface_lower: [(ipv4, prefix_bits)]}."""
    out = {}
    for line in (text or "").splitlines():
        kv = _kv_of_line(line)
        iface = (kv.get("interface") or kv.get("interface-name") or "").strip().lower()
        raw = (kv.get("address") or "").strip()
        if not iface or not raw:
            continue
        if "/" in raw:
            ip_raw, bits_raw = raw.split("/", 1)
            try:
                bits = max(0, min(32, int(bits_raw.strip())))
            except ValueError:
                continue
        else:
            ip_raw, bits = raw, 32
        ip = _ip4(ip_raw)
        if not ip:
            continue
        bucket = out.setdefault(iface, [])
        if (ip, bits) not in bucket:
            bucket.append((ip, bits))
    return out

def build_neighbor_context(devices, inventory_rows=None):
    """Build the lookup structures used to resolve interface neighbors.

    Sources, in priority order:
    1. the device's own /ip neighbor rows (LLDP/MNDP) — precise per-interface;
    2. subnet overlap over the interface-IP inventory (device_interface_ips
       table, Task 25) and each device's stored /ip address text.
    """
    devices = [d for d in (devices or []) if isinstance(d, dict)]
    info_by_ip = {}
    for d in devices:
        ip = _ip4(d.get("ip"))
        if ip and ip not in info_by_ip:
            info_by_ip[ip] = {"name": (d.get("device_name") or "").strip(), "ip": ip}

    known_by_ip = {ip: {"name": info["name"], "ip": ip} for ip, info in info_by_ip.items()}
    known_by_identity = {}
    for ip, info in info_by_ip.items():
        ident = info["name"].strip().lower()
        if ident and ident not in known_by_identity:
            known_by_identity[ident] = {"name": info["name"], "ip": ip}

    self_addrs = {}
    # Interface-IP inventory persisted in the database (Task 25).
    for row in (inventory_rows or []):
        if not isinstance(row, dict):
            continue
        ip = _ip4(row.get("ip") or row.get("address"))
        owner = _ip4(row.get("device_ip"))
        iface = str(row.get("interface") or "").strip().lower()
        if not ip or not owner or not iface:
            continue
        raw = str(row.get("address") or "")
        try:
            bits = int(raw.split("/", 1)[1]) if "/" in raw else 32
            bits = max(0, min(32, bits))
        except (TypeError, ValueError):
            bits = 32
        bucket = self_addrs.setdefault(owner, {}).setdefault(iface, [])
        if (ip, bits) not in bucket:
            bucket.append((ip, bits))
        if ip not in known_by_ip:
            owner_info = info_by_ip.get(owner)
            known_by_ip[ip] = {
                "name": (owner_info["name"] if owner_info else str(row.get("identity") or "").strip()),
                "ip": owner,
            }
        ident = str(row.get("identity") or "").strip().lower()
        if ident and ident not in known_by_identity:
            owner_info = info_by_ip.get(owner)
            known_by_identity[ident] = {
                "name": (owner_info["name"] if owner_info else str(row.get("identity")).strip()),
                "ip": owner,
            }
    # Stored /ip address text as a fallback source of the device's own IPs.
    for d in devices:
        owner = _ip4(d.get("ip"))
        if not owner:
            continue
        parsed = parse_self_addresses(d.get("ip_addresses"))
        owner_info = info_by_ip.get(owner)
        for iface, pairs in parsed.items():
            bucket = self_addrs.setdefault(owner, {}).setdefault(iface, [])
            for pair in pairs:
                if pair not in bucket:
                    bucket.append(pair)
                if pair[0] not in known_by_ip:
                    known_by_ip[pair[0]] = {"name": owner_info["name"] if owner_info else "", "ip": owner}

    lldp = {}
    # Task 30: نقشهٔ «قفل‌شدگی» همسایه‌ها به اینترفیس‌های خودِ هر دستگاه — اگر LLDP/MNDP
    # یک همسایه را روی اینترفیسی مشخص دیده باشد، آن همسایه فقط همسایهٔ همان اینترفیس است
    # و نباید در fallback ساب‌نتِ اینترفیس‌های دیگرِ همان دستگاه ظاهر شود.
    # مقدار interface در /ip neighbor می‌تواند فهرستِ جدا-با-کاما باشد (مثل wlan1,bridge1)
    # — ردیف به تک‌تک آن اینترفیس‌ها قفل می‌شود.
    pinned = {}
    for d in devices:
        owner = _ip4(d.get("ip"))
        if not owner:
            continue
        for entry in parse_neighbor_entries(d.get("ip_neighbors")):
            ifaces = [p.strip().lower() for p in str(entry["interface"]).split(",") if p.strip()]
            if not ifaces:
                continue
            slot = pinned.setdefault(owner, {})
            addr = _ip4(entry.get("address"))
            ident = (entry.get("identity") or "").strip().lower()
            for iface in ifaces:
                lldp.setdefault(owner, {}).setdefault(iface, []).append(entry)
                if addr:
                    slot.setdefault(addr, set()).add(iface)
                if ident:
                    slot.setdefault(ident, set()).add(iface)

    return {"known_by_ip": known_by_ip, "known_by_identity": known_by_identity,
            "self_addrs": self_addrs, "lldp": lldp, "pinned": pinned}

def _resolve_neighbor(context, owner_ip, interface):
    """Resolve the neighbor device connected to one interface of one device.

    Returns (neighbor_name, neighbor_ip, via) — via is "lldp" when the
    neighbor came from /ip neighbor rows and "subnet" when it was inferred
    from inventory subnet overlap; empty strings mean unknown.
    """
    owner_ip = _ip4(owner_ip)
    if not owner_ip:
        return "", "", ""
    iface = str(interface or "").strip().lower()
    own_ips = {ip for pairs in context["self_addrs"].get(owner_ip, {}).values() for ip, _ in pairs}
    own_ips.add(owner_ip)

    # 1) LLDP/MNDP neighbors reported by this device for this interface.
    resolved = []
    for entry in context["lldp"].get(owner_ip, {}).get(iface, []):
        addr = _ip4(entry.get("address"))
        ident = (entry.get("identity") or "").strip()
        hit = context["known_by_ip"].get(addr) if addr else None
        if not hit and ident:
            hit = context["known_by_identity"].get(ident.lower())
        if hit and hit["ip"] == owner_ip:
            continue  # the device seeing itself — not a neighbor
        if hit:
            resolved.append((hit["name"], hit["ip"]))
        elif ident or addr:
            resolved.append((ident, addr))
    resolved = list(dict.fromkeys(resolved))
    if resolved:
        names = " ، ".join(n for n, _ in resolved if n)
        ips = " ، ".join(i for _, i in resolved if i)
        return names, ips, "lldp"

    # 2) Fallback: another known device sharing the interface's IP subnet.
    # Task 30: همسایهٔ گزارش‌شده فقط باید مربوط به همین اینترفیسِ flapدار باشد —
    # کاندیدایی که LLDP/MNDP خودِ همان دستگاه آن را روی اینترفیس دیگری دیده است
    # (به‌جز خودِ این اینترفیس) حذف می‌شود و به این ردیف سرریز نمی‌کند.
    pinned = context.get("pinned", {}).get(owner_ip, {})
    for ip, bits in context["self_addrs"].get(owner_ip, {}).get(iface, []):
        try:
            net = ipaddress.ip_network(f"{ip}/{bits}", strict=False)
        except ValueError:
            continue
        candidates = []
        for cand_ip, info in context["known_by_ip"].items():
            if cand_ip in own_ips:
                continue
            try:
                if ipaddress.IPv4Address(cand_ip) not in net:
                    continue
            except ValueError:
                continue
            cand_name = str(info.get("name") or "").strip().lower()
            pinned_ifaces = set(pinned.get(cand_ip, set()))
            if cand_name:
                pinned_ifaces |= pinned.get(cand_name, set())
            if pinned_ifaces and iface not in pinned_ifaces:
                continue  # این همسایه به اینترفیس دیگری از همین دستگاه قفل شده است
            candidates.append((info["name"], cand_ip))
        if candidates:
            candidates = sorted(set(candidates))
            names = " ، ".join(n for n, _ in candidates if n)
            ips = " ، ".join(i for _, i in candidates if i)
            return names, ips, "subnet"
    return "", "", ""

def interface_flap_report(devices, days_back=5, threshold_minutes=5, now=None, inventory_rows=None):
    now = now or datetime.now()
    devices=list(devices or [])
    events=[]
    devices_with_logs=0
    newest_log=None
    neighbor_context=build_neighbor_context(devices, inventory_rows)
    for device in devices:
        log_text=device.get("device_log") or ""
        if log_text.strip(): devices_with_logs+=1
        # Track the newest link event in the logs regardless of the requested
        # window, so an empty result can be explained (stale logs vs. none).
        for line in log_text.splitlines():
            match=_LINE.match(line)
            if not match: continue
            if not _LINK_EVENT.match(match.group("message")): continue
            try: when=parse_log_datetime(match.group("stamp"), reference=now)
            except (ValueError, OverflowError): continue
            if newest_log is None or when>newest_log: newest_log=when
        events.extend(parse_device_log(device, now=now, days_back=days_back, threshold_minutes=threshold_minutes))
    events.sort(key=lambda e:(e["datetime"],e["device_name"],e["interface"]),reverse=True)
    for index,event in enumerate(events,1):
        event["row"] = index
        name, nip, via = _resolve_neighbor(neighbor_context, event.get("ip"), event.get("interface"))
        event["neighbor_name"] = name
        event["neighbor_ip"] = nip
        event["neighbor_via"] = via
    report={"events":events,"device_count":len({e["ip"] for e in events}),"event_count":len(events),
            "days":int(days_back),"threshold_minutes":int(threshold_minutes),
            "devices_scanned":len(devices),"devices_with_logs":devices_with_logs}
    if newest_log is not None:
        report["newest_log_at"]=newest_log.isoformat(sep=" ")
        report["newest_log_at_jalali"]=jalali_datetime_string(newest_log)
        if not events:
            cutoff=now-timedelta(days=max(0,int(days_back)))
            if newest_log<cutoff:
                report["stale_logs"]=True
                suggested=max(int(days_back)+1, min(90, int((now-newest_log).days)+2))
                report["suggested_days"]=suggested
    return report

def interface_flaps_csv(report):
    """Return a UTF-8-BOM CSV for Excel, populated from a flap report.

    The CSV mirrors every field shown in the on-screen report table,
    using the same column names and order as the UI.
    """
    output = StringIO(newline="")
    writer = csv.writer(output)
    # Task 30: چیدمان قرینه — همهٔ ستون‌ها از راست به چپ چیده می‌شوند؛ در نمایش
    # راست‌به‌چپ (جدول UI، شیت RTL اکسل و CSV در اکسل فارسی) ستون اولِ آرایه راست‌ترین
    # ستون است، پس آرایه دقیقاً همان ترتیب خواسته‌شدهٔ کاربر است:
    #   نام دستگاه ، آی‌پی دستگاه ، اینترفیس ، تعداد تکرار لاگ ، نوع رویداد ،
    #   تاریخ و زمان (شمسی) ، نام دستگاه همسایه ، IP دستگاه همسایه
    writer.writerow(["نام دستگاه", "آی‌پی دستگاه", "اینترفیس", "تعداد تکرار لاگ",
                     "نوع رویداد", "تاریخ و زمان (شمسی)",
                     "نام دستگاه همسایه", "IP دستگاه همسایه"])
    for event in report.get("events", []):
        writer.writerow([event.get("device_name", ""), event.get("ip", ""),
                         event.get("interface", ""), event.get("flap_count", 1),
                         event.get("last_status", ""), event.get("datetime_jalali", ""),
                         event.get("neighbor_name", ""), event.get("neighbor_ip", "")])
    return "\ufeff" + output.getvalue()

def interface_flaps_xlsx(report):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
    wb=Workbook(); ws=wb.active; ws.title="قطع وصل اینترفیس"; ws.sheet_view.rightToLeft=True
    # Task 30: چیدمان قرینه — شیت rightToLeft است و ستون اولِ آرایه راست‌ترین ستون
    # می‌شود؛ ترتیب آرایه = ترتیب راست‌به‌چپ خواسته‌شدهٔ کاربر (همان ترتیب CSV):
    # نام دستگاه، آی‌پی دستگاه، اینترفیس، تعداد تکرار لاگ، نوع رویداد،
    # تاریخ و زمان (شمسی)، نام دستگاه همسایه، IP دستگاه همسایه
    headers=["نام دستگاه","آی‌پی دستگاه","اینترفیس","تعداد تکرار لاگ","نوع رویداد","تاریخ و زمان (شمسی)","نام دستگاه همسایه","IP دستگاه همسایه"]
    ws.append(headers)
    for event in report.get("events",[]):
        ws.append([event.get("device_name",""),event.get("ip",""),event["interface"],event.get("flap_count",1),event["last_status"],event["datetime_jalali"],event.get("neighbor_name",""),event.get("neighbor_ip","")])
    fill=PatternFill("solid",fgColor="1F4E78"); white=Font(name="Arial",bold=True,color="FFFFFF",size=11)
    thin=Side(style="thin",color="D9E2F3")
    for cell in ws[1]:
        cell.fill=fill;cell.font=white;cell.alignment=Alignment(horizontal="center",vertical="center",wrap_text=True);cell.border=Border(bottom=Side(style="medium",color="17365D"))
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.font=Font(name="Arial",size=10);cell.alignment=Alignment(horizontal="center",vertical="center");cell.border=Border(bottom=thin)
    ws.freeze_panes="A2";ws.auto_filter.ref=ws.dimensions;ws.row_dimensions[1].height=32
    for col in ws.columns:
        letter=col[0].column_letter; width=max((len(str(c.value or "")) for c in col),default=10)
        ws.column_dimensions[letter].width=min(max(width+3,12),42)
    out=BytesIO();wb.save(out);out.seek(0);return out


# ---------------- Smart report: wireless antenna / station disconnects ----------------
_MAC_ADDRESS = re.compile(r"(?i)\b(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}\b")
_WIRELESS_ISSUE = re.compile(
    r"(?:"
    r"extensive\s+data\s+loss|"
    r"lost\s+connection|connection\s+lost|"
    r"disassoc(?:iated|iation)?|"
    r"deauth(?:enticated|entication)?|"
    r"station\s+leaving|"
    r"not\s+responding|no\s+response|"
    r"no\s+beacons?\s+received|"
    r"failed\s+to\s+connect|"
    r"registration\s+timeout|authentication\s+timeout|"
    r"removing\s+from\s+registration\s+table|"
    r"(?:weak|low|poor)\s+(?:wireless\s+)?signal|"
    r"signal\s+(?:is\s+)?(?:weak|low|lost|too\s+weak|below)"
    r")",
    re.I,
)

def _mac_key(value):
    return re.sub(r"[^0-9a-f]", "", str(value or "").lower())

def wireless_antenna_report(devices, days_back=5, now=None):
    """Find wireless station/link issues in saved RouterOS logs and resolve MACs against DB fields."""
    now = now or datetime.now()
    cutoff = now - timedelta(days=max(1, int(days_back)))
    devices = list(devices or [])
    # Index MACs found in saved inventory fields to their known device identity/IP.
    mac_index = {}
    mac_fields = ("mac_info", "wireless_info", "ip_neighbors", "interfaces", "ip_addresses")
    for device in devices:
        for field in mac_fields:
            text_value = device.get(field) or ""
            for mac in _MAC_ADDRESS.findall(text_value):
                key = _mac_key(mac)
                if key and key not in mac_index:
                    mac_index[key] = {
                        "matched_device_ip": device.get("ip") or "",
                        "matched_device_name": device.get("device_name") or "",
                    }

    events = []
    seen = set()
    for device in devices:
        raw_log = device.get("device_log") or ""
        for line in raw_log.splitlines():
            match = _LINE.match(line)
            if not match:
                continue
            message = match.group("message").strip()
            if not _WIRELESS_ISSUE.search(message):
                continue
            try:
                when = parse_log_datetime(match.group("stamp"), reference=now)
            except (ValueError, OverflowError):
                continue
            if when < cutoff or when > now + timedelta(minutes=1):
                continue
            macs = _MAC_ADDRESS.findall(message)
            # Signal-strength-only records without a station MAC are still useful,
            # but the report cannot claim a client identity without one.
            station_mac = macs[0].upper().replace("-", ":") if macs else ""
            resolved = mac_index.get(_mac_key(station_mac), {}) if station_mac else {}
            key = (device.get("ip") or "", when.isoformat(), message)
            if key in seen:
                continue
            seen.add(key)
            # Task 43: نام دستگاهِ مالکِ MAC (تطبیق‌شده از فیلدهای اینونتوری) به
            # انتهای متن رویداد اضافه می‌شود تا در ستون «رویداد» هم معلوم باشد.
            owner = (str(resolved.get("matched_device_name") or "").strip()
                     or str(resolved.get("matched_device_ip") or "").strip())
            event_text = f"{message} — دستگاه متعلق به MAC: {owner}" if owner else message
            events.append({
                "datetime": when.isoformat(sep=" "),
                "datetime_jalali": jalali_datetime_string(when),
                "antenna_ip": device.get("ip") or "",
                "antenna_name": device.get("device_name") or "",
                "station_mac": station_mac,
                "matched_device_ip": resolved.get("matched_device_ip", ""),
                "matched_device_name": resolved.get("matched_device_name", ""),
                "event": event_text,
                "raw_line": line.strip(),
            })
    events.sort(key=lambda item: (item["datetime"], item["antenna_ip"], item["station_mac"]), reverse=True)
    # Task 44: هر MAC فقط یک بار در گزارش بیاید — لیست جدیدترین‌اول است، پس
    # از هر MAC تنها جدیدترین رکورد نگه داشته می‌شود و تکراری‌ها حذف می‌شوند.
    # رکوردهای بدون MAC هویتی برای ادغام ندارند و سر جایشان می‌مانند.
    seen_mac = set()
    deduped = []
    duplicate_mac_count = 0
    for event in events:
        mac_key = _mac_key(event["station_mac"]) if event["station_mac"] else ""
        if mac_key:
            if mac_key in seen_mac:
                duplicate_mac_count += 1
                continue
            seen_mac.add(mac_key)
        deduped.append(event)
    events = deduped
    for index, event in enumerate(events, 1):
        event["row"] = index
    return {
        "items": events,
        "events": events,
        "event_count": len(events),
        "days": int(days_back),
        "duplicate_mac_count": duplicate_mac_count,
        "unmatched_mac_count": len({e["station_mac"] for e in events if e["station_mac"] and not e["matched_device_ip"]}),
    }

def wireless_antenna_csv(report):
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["ردیف", "تاریخ و زمان (میلادی)", "تاریخ و زمان (شمسی)",
                     "نام آنتن/روتر لاگ‌دهنده", "IP آنتن/روتر", "MAC ایستگاه",
                     "نام دستگاه متناظر با MAC", "IP دستگاه متناظر با MAC", "رویداد/علت"])
    for event in report.get("items", []):
        writer.writerow([
            event.get("row", ""), event.get("datetime", ""), event.get("datetime_jalali", ""),
            event.get("antenna_name", ""), event.get("antenna_ip", ""), event.get("station_mac", ""),
            event.get("matched_device_name", ""), event.get("matched_device_ip", ""), event.get("event", ""),
        ])
    return "\ufeff" + output.getvalue()
