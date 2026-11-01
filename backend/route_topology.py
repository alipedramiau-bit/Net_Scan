"""Route topology — مسیر هر دستگاه میکروتیک تا روتر مرکزی.

برای هر دستگاه میکروتیک (از دیتابیس انتخابی یا یک انتخاب صریح) با نام کاربری و
رمز عبوری که کاربر وارد می‌کند از طریق RouterOS API (پورت 8728) وصل می‌شویم،
اینترفیس‌ها / آدرس‌های IP / همسایه‌ها (MNDP) / مسیرهای روتینگ را می‌خوانیم،
گراف لینک‌ها را می‌سازیم (همسایگی MNDP + اشتراک ساب‌نت + گیت‌وی روت)،
کوتاه‌ترین مسیر هر دستگاه تا «روتر مرکزی» (IP آن را کاربر وارد می‌کند) را با
BFS پیدا می‌کنیم و مشخص می‌کنیم در هر گام، کدام اینترفیسِ دستگاه A به کدام
اینترفیسِ دستگاه B وصل است.

خروجی، ورودی ماژول route_pdf.py برای ساخت گزارش PDF یک‌صفحه‌ای به ازای هر
دستگاه است (مشابه نمونهٔ "Detailed Router Path Topology").
"""
from __future__ import annotations

import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event

try:
    from backend import routeros_api as ros
except ImportError:  # direct run from backend/
    import routeros_api as ros

DEFAULT_CENTRAL_IP = "172.19.1.6"

# خواندن جداول بزرگ را محدود می‌کنیم تا PDF/گراف کنترل‌شده بماند
CAPS = {"interfaces": 200, "addresses": 200, "neighbors": 120, "routes": 300, "arp": 200}


# ---------------------------------------------------------------------------
# 1) خواندن ساختاریافتهٔ اطلاعات از RouterOS API
# ---------------------------------------------------------------------------
def collect_topology_info(
    host: str,
    username: str,
    password: str,
    port: int = 8728,
    timeout: float = 12.0,
) -> dict:
    """Read identity / interfaces / addresses / neighbors / routes / arp (structured)."""
    try:
        with ros.RouterOSClient(host, port=port, timeout=timeout) as api:
            api.login(username or "admin", password or "")
            identity = ""
            for row in ros._print_table(api, "/system/identity/print"):
                identity = (row.get("name") or "").strip()
                if identity:
                    break
            resource = {}
            res_rows = ros._print_table(api, "/system/resource/print")
            if res_rows:
                r0 = res_rows[0]
                resource = {
                    "version": (r0.get("version") or "").strip(),
                    "board": (r0.get("board-name") or "").strip(),
                    "uptime": (r0.get("uptime") or "").strip(),
                    "cpu_load": (r0.get("cpu-load") or "").strip(),
                }
            ifaces = []
            for row in ros._print_table(api, "/interface/print")[: CAPS["interfaces"]]:
                ifaces.append({
                    "name": (row.get("name") or "").strip(),
                    "type": (row.get("type") or "").strip(),
                    "running": (row.get("running") or "").strip(),
                    "disabled": (row.get("disabled") or "").strip(),
                    "mac_address": (row.get("mac-address") or "").strip(),
                    "comment": (row.get("comment") or "").strip(),
                })
            addresses = []
            for row in ros._print_table(api, "/ip/address/print")[: CAPS["addresses"]]:
                addresses.append({
                    "address": (row.get("address") or "").strip(),
                    "interface": (row.get("interface") or "").strip(),
                    "network": (row.get("network") or "").strip(),
                })
            neighbors = []
            for row in ros._print_table(api, "/ip/neighbor/print")[: CAPS["neighbors"]]:
                neighbors.append({
                    "identity": (row.get("identity") or "").strip(),
                    "address": (row.get("address") or "").strip(),
                    "interface": (row.get("interface") or "").strip(),
                    "platform": (row.get("platform") or "").strip(),
                    "version": (row.get("version") or "").strip(),
                    "mac_address": (row.get("mac-address") or "").strip(),
                    "uptime": (row.get("uptime") or "").strip(),
                })
            routes = []
            for row in ros._print_table(api, "/ip/route/print")[: CAPS["routes"]]:
                routes.append({
                    "dst_address": (row.get("dst-address") or row.get("dst_address") or "").strip(),
                    "gateway": (row.get("gateway") or "").strip(),
                    "distance": (row.get("distance") or "").strip(),
                    "immediate_gw": (row.get("immediate-gw") or row.get("immediate_gw") or "").strip(),
                })
            arp = []
            for row in ros._print_table(api, "/ip/arp/print")[: CAPS["arp"]]:
                arp.append({
                    "address": (row.get("address") or "").strip(),
                    "mac_address": (row.get("mac-address") or "").strip(),
                    "interface": (row.get("interface") or "").strip(),
                })
        return {
            "ip": host, "ok": True, "error": None,
            "identity": identity or host,
            "resource": resource,
            "interfaces": ifaces,
            "addresses": addresses,
            "neighbors": neighbors,
            "routes": routes,
            "arp": arp,
        }
    except Exception as e:  # اتصال/لاگین/پارس هر شکلی که باشد
        return {
            "ip": host, "ok": False, "error": str(e)[:400],
            "identity": "", "resource": {},
            "interfaces": [], "addresses": [], "neighbors": [], "routes": [], "arp": [],
        }


def collect_topology_info_many(
    ips: list[str],
    username: str,
    password: str,
    port: int = 8728,
    timeout: float = 12.0,
    cancel_event: Event | None = None,
    progress: dict | None = None,
    max_workers: int = 6,
) -> list[dict]:
    """خواندن موازی دستگاه‌ها با حفظ ترتیب و گزارش پیشرفت زنده.

    نکته: مالک فلگ running فراخواننده است (worker گزارش)؛ این تابع فقط
    total/done/ok/failed/current_ip را به‌روز می‌کند تا گزارش قبل از فازهای
    graph/pdf تمام‌شده به نظر نرسد.
    """
    clean = [str(x).strip() for x in (ips or []) if str(x).strip()]
    if progress is not None:
        progress.update({"total": len(clean), "done": 0, "ok": 0, "failed": 0,
                         "current_ip": ""})
    if not clean:
        return []
    workers = max(1, min(int(max_workers or 1), len(clean), 16))
    results: dict[str, dict] = {}

    def _one(ip: str) -> dict:
        if cancel_event is not None and cancel_event.is_set():
            return {"ip": ip, "ok": False, "error": "canceled", "identity": "",
                    "resource": {}, "interfaces": [], "addresses": [],
                    "neighbors": [], "routes": [], "arp": []}
        return collect_topology_info(ip, username, password, port=port, timeout=timeout)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_one, ip): ip for ip in clean}
        for fut in as_completed(futures):
            ip = futures[fut]
            try:
                res = fut.result()
            except Exception as e:  # نباید اتفاق بیفتد؛ محافظت اضافه
                res = {"ip": ip, "ok": False, "error": str(e)[:400], "identity": "",
                       "resource": {}, "interfaces": [], "addresses": [],
                       "neighbors": [], "routes": [], "arp": []}
            results[ip] = res
            if progress is not None:
                progress["done"] = progress.get("done", 0) + 1
                if res.get("ok"):
                    progress["ok"] = progress.get("ok", 0) + 1
                else:
                    progress["failed"] = progress.get("failed", 0) + 1
                progress["current_ip"] = ip
    if progress is not None:
        progress["current_ip"] = ""
    if cancel_event is not None and cancel_event.is_set():
        if progress is not None:
            progress["canceled"] = True
    return [results[ip] for ip in clean if ip in results]


# ---------------------------------------------------------------------------
# 2) ابزارهای IP
# ---------------------------------------------------------------------------
def _ip_of(addr: str) -> str:
    """'172.18.2.217/29' -> '172.18.2.217' (ورودی بدون ماسک هم قبول است)."""
    return (addr or "").split("/")[0].strip()


def _iface_of(addresses: list[dict], ip: str) -> str:
    for a in addresses:
        if _ip_of(a.get("address")) == ip:
            return a.get("interface") or ""
    return ""


def _iface_ip_in_network(addresses: list[dict], net: str) -> tuple[str, str]:
    """(ip, interface) اولین آدرسی که در شبکهٔ net است."""
    try:
        net_obj = ipaddress.ip_network(net, strict=False)
    except ValueError:
        return ("", "")
    for a in addresses:
        try:
            ifo = ipaddress.ip_interface(a.get("address") or "")
        except ValueError:
            continue
        if ifo.network == net_obj:
            return (str(ifo.ip), a.get("interface") or "")
    return ("", "")


def _same_subnet(a: str, b: str) -> bool:
    """دو رشتهٔ آدرس (با ماسک) در یک ساب‌نت هستند؟"""
    try:
        ia = ipaddress.ip_interface(a)
        ib = ipaddress.ip_interface(b)
        return ia.network == ib.network
    except ValueError:
        return False


def _split_gateway(gw: str) -> list[tuple[str, str]]:
    """'10.0.0.1%ether2,10.0.0.2' -> [('10.0.0.1','ether2'), ('10.0.0.2','')]"""
    out = []
    for part in (gw or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "%" in part:
            ip, ifc = part.split("%", 1)
            out.append((ip.strip(), ifc.strip()))
        else:
            out.append((part, ""))
    return out


def _arp_iface_toward(arp: list[dict], ip: str) -> str:
    """اینترفیسِ دستگاه برای رساندن به ip از جدول ARP (وقتی گیت‌وی on-link نیست)."""
    ipn = (ip or "").strip()
    if not ipn:
        return ""
    for a in arp or []:
        if _ip_of(a.get("address")) == ipn:
            return a.get("interface") or ""
    return ""


def _addr_iface_toward(addresses: list[dict], ip: str) -> tuple[str, str]:
    """(ip_خودِ_دستگاه, اینترفیس) اولین آدرسی که شبکه‌اش شامل ip است.

    برای یافتن اینترفیسِ سمتِ گیت‌وی به کار می‌رود؛ مثلاً اگر دستگاه
    172.18.1.68/28 داشته باشد و گیت‌وی 172.18.1.71 باشد، برمی‌گرداند
    ('172.18.1.68', نامِ اینترفیس).
    """
    try:
        tip = ipaddress.ip_address(ip)
    except ValueError:
        return ("", "")
    for a in addresses or []:
        try:
            ifo = ipaddress.ip_interface((a.get("address") or "").strip())
        except ValueError:
            continue
        if tip in ifo.network:
            return (str(ifo.ip), a.get("interface") or "")
    return ("", "")


def _route_next_hops(routes: list[dict], central_ip: str) -> tuple[list[tuple[str, str]], str]:
    """بهترین next-hopهای یک گره به سمت روتر مرکزی (روش بهترِ یافتن مسیر).

    ۱) طولانی‌ترین پیشوند مسیری که central_ip را پوشش می‌دهد (route specific) —
       در همان طولِ پیشوند، کم‌ترین distance و سپس همهٔ گیت‌وی‌های ECMP؛
    ۲) وگرنه «روت پیش‌فرض» (0.0.0.0/0) با کمترین distance — یعنی hop بالای
       دستگاه (بالادست)؛ در حالت ECMP همهٔ گیت‌وی‌های هم‌distance برمی‌گردند.

    خروجی: ([(gw_ip, gw_if), ...], "specific" | "default" | "")
    """
    tip_raw = (central_ip or "").strip()
    if not tip_raw:
        return ([], "")
    try:
        caddr = ipaddress.ip_address(tip_raw)
    except ValueError:
        return ([], "")

    def _dist(rt: dict) -> int:
        try:
            return int(str(rt.get("distance") or "0").strip() or 0)
        except (TypeError, ValueError):
            return 0

    cands: dict[int, dict] = {}   # prefixlen (>0) -> {"dist", "gws"}
    defaults: list[tuple[int, list[tuple[str, str]]]] = []
    for rt in routes or []:
        dst = (rt.get("dst_address") or "").strip()
        gws = _split_gateway(rt.get("gateway") or "") + _split_gateway(rt.get("immediate_gw") or "")
        if not gws:
            continue
        try:
            net = ipaddress.ip_network(dst or "0.0.0.0/0", strict=False)
        except ValueError:
            continue
        if caddr not in net:
            continue
        if net.prefixlen == 0:
            defaults.append((_dist(rt), gws))
            continue
        c = cands.get(net.prefixlen)
        d = _dist(rt)
        if c is None:
            cands[net.prefixlen] = {"dist": d, "gws": list(gws)}
        elif d < c["dist"]:
            cands[net.prefixlen] = {"dist": d, "gws": list(gws)}
        elif d == c["dist"]:
            for x in gws:
                if x not in c["gws"]:
                    c["gws"].append(x)
    if cands:
        best_pl = max(cands)
        return (cands[best_pl]["gws"], "specific")
    if defaults:
        min_d = min(d for d, _g in defaults)
        merged: list[tuple[str, str]] = []
        for d, g in defaults:
            if d == min_d:
                for x in g:
                    if x not in merged:
                        merged.append(x)
        return (merged, "default")
    return ([], "")


def _route_distance(rt: dict) -> int:
    try:
        return int(str(rt.get("distance") or "0").strip() or 0)
    except (TypeError, ValueError):
        return 0


def _route_all_next_hops(routes: list[dict], central_ip: str) -> list[dict]:
    """همهٔ next-hopهای ممکن به سمت روتر مرکزی از «همهٔ» روت‌های پوشش‌دهنده.

    برخلاف _route_next_hops (فقط بهترین روت)، برای درخواست کاربر مبنی بر اینکه
    «هر روتر چند IP روی اینترفیس‌های مختلف دارد و تمام اینترفیس‌ها و IPهای آن
    برای مسیریابی باید چک شوند»، گیت‌وی‌های همهٔ روت‌های پوشش‌دهندهٔ central_ip
    (روت خاص هر اینترفیس، روت‌های جایگزین با distance بدتر و روت پیش‌فرض) را
    به‌ترتیب برتری (پیشوند بلندتر ← distance کمتر ← ترتیب جدول) برمی‌گرداند.

    خروجی: [{"gw","gw_if","kind","dst","prefixlen","distance"}] بدون تکرار؛
    گیت‌وی اینترفیسی (نام اینترفیس به‌جای IP) قابل دنبال‌کردن نیست و حذف می‌شود.
    """
    tip_raw = (central_ip or "").strip()
    if not tip_raw:
        return []
    try:
        caddr = ipaddress.ip_address(tip_raw)
    except ValueError:
        return []
    cands: list[dict] = []
    for pos, rt in enumerate(routes or []):
        dst = (rt.get("dst_address") or "").strip()
        try:
            net = ipaddress.ip_network(dst or "0.0.0.0/0", strict=False)
        except ValueError:
            continue
        if caddr not in net:
            continue
        for g, gif in _split_gateway(rt.get("gateway") or "") + _split_gateway(rt.get("immediate_gw") or ""):
            g = (g or "").strip()
            if not g:
                continue
            try:
                ipaddress.ip_address(g)
            except ValueError:
                continue  # گیت‌وی اینترفیسی مثل "ether5" — قابل دنبال‌کردن نیست
            cands.append({
                "gw": g, "gw_if": (gif or "").strip(),
                "kind": "specific" if net.prefixlen else "default",
                "dst": str(net), "prefixlen": net.prefixlen,
                "distance": _route_distance(rt), "pos": pos,
            })
    cands.sort(key=lambda c: (-c["prefixlen"], c["distance"], c["pos"]))
    out: list[dict] = []
    seen: set = set()
    for c in cands:
        k = (c["gw"], c["gw_if"])
        if k in seen:
            continue
        seen.add(k)
        out.append(c)
    return out


# برچسب فارسی نتیجهٔ بررسی هر اینترفیس برای مسیر به روتر مرکزی (CSV Task 21)
_VERDICT_FA = {
    "direct": "مستقیم متصل — روتر مرکزی در ساب‌نتِ همین IP است",
    "route": "روت به مرکز از طریق گیت‌وی {gw} (پوشش {dst})",
    "default": "فقط روت پیش‌فرض از طریق گیت‌وی {gw}",
    "none": "مسیری به روتر مرکزی از این اینترفیس نیست",
}
_STATE_SUFFIX_FA = {
    "disabled": " — اینترفیس غیرفعال است (disabled)",
    "down": " — اینترفیس اتصال فیزیکی ندارد (no link)",
}


def interface_route_verdicts(info: dict, central_ip: str) -> list[dict]:
    """بررسی تک‌تک اینترفیس‌ها و آدرس‌های IP دستگاه برای رسیدن به روتر مرکزی.

    برای «هر» آدرس IP روی هر اینترفیس مشخص می‌شود:
      direct  — روتر مرکزی در ساب‌نتِ همین IP است (اتصال مستقیم L2)
      route   — روتِ پوشش‌دهندهٔ مرکز که گیت‌وی‌اش در ساب‌نتِ همین IP است
      default — فقط روت پیش‌فرض با گیت‌ویِ در ساب‌نتِ همین IP
      none    — هیچ مسیری از این اینترفیس به سمت مرکز دیده نمی‌شود
    به‌همراه وضعیت اینترفیس (disabled / no link) و دیده‌شدن گیت‌وی در ARP.
    """
    tip_raw = (central_ip or "").strip()
    try:
        caddr = ipaddress.ip_address(tip_raw)
    except ValueError:
        return []
    addresses = info.get("addresses") or []
    routes = info.get("routes") or []
    ifaces = {(i.get("name") or "").strip(): i for i in (info.get("interfaces") or [])}
    arp_ips = {_ip_of(a.get("address")) for a in (info.get("arp") or [])}
    out: list[dict] = []
    for a in addresses:
        raw = (a.get("address") or "").strip()
        try:
            ifo = ipaddress.ip_interface(raw)
        except ValueError:
            continue
        ifc = (a.get("interface") or "").strip()
        verdict, gw, rdst = "none", "", ""
        if caddr in ifo.network:
            verdict, rdst = "direct", str(ifo.network)
        else:
            best_key = None
            for rt in routes:
                dst = (rt.get("dst_address") or "").strip()
                try:
                    net = ipaddress.ip_network(dst or "0.0.0.0/0", strict=False)
                except ValueError:
                    continue
                if caddr not in net:
                    continue
                for g, _gif in _split_gateway(rt.get("gateway") or "") + _split_gateway(rt.get("immediate_gw") or ""):
                    g = (g or "").strip()
                    if not g:
                        continue
                    try:
                        gip = ipaddress.ip_address(g)
                    except ValueError:
                        continue
                    if gip in ifo.network:
                        key = (net.prefixlen, -_route_distance(rt))
                        if best_key is None or key > best_key:
                            best_key = key
                            verdict = "route" if net.prefixlen else "default"
                            gw, rdst = g, str(net)
        it = ifaces.get(ifc) or {}
        dis = (it.get("disabled") or "").strip().lower() == "true"
        run = (it.get("running") or "").strip().lower() == "true"
        state = "disabled" if dis else ("down" if not run else "up")
        label = _VERDICT_FA.get(verdict, verdict)
        if verdict in ("route", "default"):
            label = label.format(gw=gw, dst=rdst)
        label += _STATE_SUFFIX_FA.get(state, "")
        out.append({
            "interface": ifc, "ip": str(ifo.ip), "address": raw, "network": str(ifo.network),
            "verdict": verdict, "gateway": gw, "route_dst": rdst, "state": state,
            "gw_in_arp": (gw in arp_ips) if gw else None, "label": label,
        })
    return out


# ---------------------------------------------------------------------------
# 2-ب) تحلیل دلیل نرسیدن هر دستگاه به روتر مرکزی (گزارش CSV — درخواست کاربر)
# ---------------------------------------------------------------------------
def unreachable_reason_rows(topo: dict) -> list[dict]:
    """برای هر دستگاهی که در گراف به روتر مرکزی نمی‌رسد، «دلیل» را تحلیل می‌کند.

    ورودی خروجی build_topology است؛ خروجی فهرست ردیف‌های CSV با فیلدهای فارسی:
    IP، نام، وضعیت، تعداد اینترفیس/IP، فهرست اینترفیس‌ها و آدرس‌ها، نتیجهٔ
    بررسی هر اینترفیس برای مسیر، دلیل اصلی و جزئیات.
    """
    nodes = topo.get("nodes") or {}
    order = topo.get("order") or []
    paths = topo.get("paths") or {}
    central = (topo.get("central_ip") or "").strip()
    core_node = nodes.get(topo.get("core_key") or "") or {}
    cisco_meta = topo.get("cisco") or {}
    core_unknown = bool(core_node.get("ghost")) and not cisco_meta.get("used")

    rows: list[dict] = []
    for key in order:
        path = paths.get(key) or {}
        if path.get("reachable"):
            continue
        node = nodes.get(key) or {}
        info = node.get("info") or {}
        dev = node.get("device") or {}
        addresses = node.get("addresses") or []
        routes = node.get("routes") or []
        ifaces = node.get("interfaces") or []
        details: list[str] = []
        status = "نمی‌رسد به روتر مرکزی"
        reason = ""

        ip_txt = (node.get("ip") or "").strip()
        name = (info.get("identity") or dev.get("device_name") or ip_txt or "—")
        addrs_txt = "؛ ".join(
            f"{(a.get('interface') or '?')}: {(a.get('address') or '?')}"
            for a in addresses
        )
        n_if = len({(a.get("interface") or "?") for a in addresses}) if addresses else 0

        if info and info.get("ok") is False:
            # دستگاه اصلاً از API خوانده نشده — مسیر اصلاً قابل بررسی نبوده
            err = str(info.get("error") or "").strip()
            if err.lower() == "canceled":
                status = "بررسی متوقف شد"
                reason = "خواندن دستگاه پیش از بررسی مسیر متوقف شد (توقف گزارش توسط کاربر)"
            else:
                status = "خوانده نشد"
                cause = ""
                try:
                    cause = ros.classify_push_error(err)
                except Exception:
                    cause = ""
                reason = ("دستگاه اصلاً از RouterOS API خوانده نشد؛ بدون خواندن "
                          "اینترفیس‌ها و جدول روتینگ، مسیر قابل بررسی نیست"
                          + (f" — {cause}" if cause else ""))
                details.append(f"خطای اتصال: {err[:180]}")
        else:
            verdicts = interface_route_verdicts(info, central)
            viable = [v for v in verdicts if v["verdict"] in ("direct", "route", "default")]
            good = [v for v in viable if v["state"] == "up"]
            bad = [v for v in viable if v["state"] != "up"]
            if core_unknown:
                details.append(
                    f"روتر مرکزی {central} بین دستگاه‌های خوانده‌شده یافت نشد و کانفیگ "
                    "Cisco روتر مرکزی بارگذاری نشده است؛ مسیر تا مرکز قابل اتصال نیست"
                )
            if verdicts:
                n_vif = len({v["interface"] or "?" for v in verdicts})
                details.insert(
                    0,
                    f"تمام {len(verdicts)} آدرس IP روی {n_vif} اینترفیس دستگاه برای "
                    "مسیر به روتر مرکزی بررسی شد",
                )
            if not addresses:
                reason = "هیچ آدرس IP روی دستگاه خوانده نشد؛ مسیری برای رسیدن به مرکز قابل تشخیص نیست"
            elif not routes:
                reason = "جدول روتینگ دستگاه خالی است (/ip route) — هیچ مسیری به سمت مرکز وجود ندارد"
            elif not viable:
                hops_any = _route_all_next_hops(routes, central)
                if hops_any:
                    gws = "، ".join(dict.fromkeys(h["gw"] for h in hops_any))
                    reason = (
                        f"روت به سمت مرکز وجود دارد (گیت‌وی: {gws}) اما گیت‌وی در "
                        "ساب‌نت هیچ‌کدام از اینترفیس‌های دستگاه نیست — یا گیت‌وی اشتباه "
                        "است یا مسیر بازگشتی (recursive) بدون اینترفیس خروجی مشخص"
                    )
                else:
                    reason = ("هیچ روت پیش‌فرض یا مسیر خاصی به سمت روتر مرکزی "
                              f"({central}) در جدول روتینگ دستگاه نیست")
            else:
                # دستگاه مسیری به مرکز «دارد» — چرا در گراف نرسید؟
                if bad and not good:
                    names = "، ".join(
                        f"{v['interface']} ({'غیرفعال' if v['state'] == 'disabled' else 'بدون اتصال فیزیکی'})"
                        for v in bad
                    )
                    reason = f"اینترفیس خروجی مسیر غیرفعال یا قطع است: {names}"
                else:
                    end = path.get("upstream_end") or {}
                    kind = (end.get("kind") or "").strip()
                    if kind == "ghost":
                        reason = (
                            f"مسیر تا گیت‌وی {end.get('ip') or '?'} پیش می‌رود اما دستگاه "
                            "بعدی در دستگاه‌های بررسی‌شده نیست — یا API آن در دسترس نیست "
                            "یا خارج از محدودهٔ انتخاب گزارش است"
                        )
                    elif kind == "loop":
                        reason = (
                            f"زنجیرهٔ گیت‌وی‌ها در حلقه گیر می‌کند (دستگاه "
                            f"{end.get('name') or '?'} — {end.get('ip') or '?'} دوباره تکرار می‌شود)"
                        )
                    elif kind == "max":
                        reason = ("زنجیرهٔ بالادست بیش از ۶ گام ادامه دارد و در محدودهٔ "
                                  "بررسی به روتر مرکزی ختم نمی‌شود")
                    elif kind == "no-route" and end.get("to_key") != key:
                        reason = (
                            f"مسیر به دستگاه بعدی ({end.get('name') or '?'} — "
                            f"{end.get('ip') or '?'}) می‌رسد اما آن دستگاه نیز هیچ روت "
                            "به سمت روتر مرکزی ندارد"
                        )
                    elif kind == "no-route":
                        reason = ("روت پوشش‌دهندهٔ مرکز در جدول روتینگ دیده شد اما "
                                  "next-hop قابل تعیین نیست (گیت‌وی نامعتبر)")
                    else:
                        reason = ("مسیر تا روتر مرکزی از شواهد دستگاه‌ها قابل ساخت نیست "
                                  "(حلقهٔ واسط گم‌شده یا شواهد ناکافی)")
                if bad and good:
                    for v in bad:
                        details.append(
                            f"اینترفیس {v['interface']} (خروجی مسیر به گیت‌وی {v['gateway']}) "
                            + ("غیرفعال است" if v["state"] == "disabled" else "اتصال فیزیکی ندارد (no link)")
                        )
            # گیت‌ویِ مسیرِ سالم در ARP دیده نشده؟
            first_good = good[0] if good else (viable[0] if viable else None)
            if first_good and first_good.get("gateway") and first_good.get("gw_in_arp") is False:
                details.append(
                    f"گیت‌وی {first_good['gateway']} در جدول ARP دستگاه دیده نشد "
                    "(هنوز پاسخ نداده یا فیلتر شده است)"
                )

        verdicts_txt = " | ".join(
            f"{v['interface']} ({v['ip']}): {v['label']}"
            for v in (interface_route_verdicts(info, central) if (info and info.get("ok") is not False) else [])
        ) if (addresses and routes) else ""

        rows.append({
            "ip": ip_txt,
            "name": name,
            "device_name": dev.get("device_name") or "",
            "device_type": dev.get("device_type") or "",
            "tags": dev.get("tags") or "",
            "status": status,
            "ifaces_count": (f"{n_if} اینترفیس / {len(addresses)} آدرس IP"
                             if addresses else "—"),
            "addresses_txt": addrs_txt,
            "verdicts_txt": verdicts_txt,
            "reason": reason,
            "details": " | ".join(d for d in details if d),
        })
    return rows


# ---------------------------------------------------------------------------
# 3) ساخت گراف و محاسبهٔ مسیر
# ---------------------------------------------------------------------------
def _make_node(key: str, name: str, ip: str, info: dict | None, device: dict | None,
               ghost: bool) -> dict:
    info = info or {}
    return {
        "key": key, "name": name or ip, "ip": ip,
        "info": info, "device": device, "ghost": ghost, "is_core": False,
        "addresses": info.get("addresses") or [],
        "interfaces": info.get("interfaces") or [],
        "neighbors": info.get("neighbors") or [],
        "routes": info.get("routes") or [],
    }


def _cisco_addresses(cisco: dict) -> list[dict]:
    """آدرس‌های کانفیگ سیسکو در شکلِ آدرس‌های RouterOS (برای گرهٔ core)."""
    out: list[dict] = []
    for it in (cisco or {}).get("interfaces") or []:
        for a in it.get("addresses") or []:
            if not a.get("ip"):
                continue
            out.append({
                "address": f"{a['ip']}/{a.get('prefix') or '32'}",
                "interface": it.get("name") or "",
                "network": a.get("subnet") or "",
                "secondary": bool(a.get("secondary")),
            })
    return out


def _cisco_interfaces(cisco: dict) -> list[dict]:
    """اینترفیس‌های کانفیگ سیسکو در شکلِ اینترفیس‌های RouterOS (برای گرهٔ core)."""
    out: list[dict] = []
    for it in (cisco or {}).get("interfaces") or []:
        shutdown = bool(it.get("shutdown"))
        out.append({
            "name": it.get("name") or "",
            "type": it.get("type") or "Cisco",
            "running": "false" if shutdown else "true",
            "disabled": "true" if shutdown else "false",
            "mac_address": "",
            "comment": it.get("description") or "",
        })
    return out


def _core_iface_toward(core_addrs: list[dict], ip: str) -> tuple[str, str]:
    """(ip_سیسکو، اینترفیس) برای گیت‌ویِ داده‌شده: اول تطبیق دقیق، بعد ساب‌نت."""
    ifc = _iface_of(core_addrs, ip)
    if ifc:
        return (ip, ifc)
    return _addr_iface_toward(core_addrs, ip)


def build_topology(infos: list[dict], devices: list[dict], central_ip: str,
                   cisco: dict | None = None) -> dict:
    """گراف لینک‌ها + کوتاه‌ترین مسیر هر دستگاه تا روتر مرکزی.

    infos  — خروجی collect_topology_info_many (به ترتیب دستگاه‌ها)
    devices— ردیف‌های دیتابیس (fetch_devices_by_ips / query_devices)
    cisco  — کانفیگ پارس‌شدهٔ روتر مرکزی سیسکو (cisco_config.parse_cisco_config)؛
             وقتی روتر مرکزی سیسکو است و از RouterOS API خوانده نمی‌شود، گرهٔ core
             از روی این کانفیغ غنی‌سازی می‌شود (آدرس‌ها/اینترفیس‌ها) و روت‌های
             استاتیک سیسکو به‌عنوان شواهد یال core→دستگاه استفاده می‌شوند.
    """
    central_ip = (central_ip or "").strip() or DEFAULT_CENTRAL_IP
    dev_by_ip = {str(d.get("ip") or "").strip(): d for d in (devices or []) if d.get("ip")}

    nodes: dict[str, dict] = {}
    order: list[str] = []
    for info in infos or []:
        ip = (info.get("ip") or "").strip()
        if not ip:
            continue
        key = "d:" + ip
        dev = dev_by_ip.get(ip) or {}
        name = (info.get("identity") or dev.get("device_name") or ip)
        node = _make_node(key, name, ip, info, dev, ghost=False)
        nodes[key] = node
        order.append(key)

    # روتر مرکزی: اگر یکی از دستگاه‌های خوانده‌شده خودش IP مرکزی را دارد
    core_key = None
    for key in order:
        for a in nodes[key]["addresses"]:
            if _ip_of(a.get("address")) == central_ip:
                core_key = key
                break
        if core_key:
            break
    cisco_info = None
    if cisco and isinstance(cisco, dict) and (cisco.get("interfaces") or cisco.get("static_routes")):
        cisco_info = cisco
    if core_key:
        nodes[core_key]["is_core"] = True
        nodes[core_key]["core_ip"] = central_ip
        try:
            from backend import cisco_config as cc
        except ImportError:
            import cisco_config as cc
        central_in_cisco = cc.central_ip_known(cisco_info or {}, central_ip)
    else:
        core_key = "core"
        try:
            from backend import cisco_config as cc
        except ImportError:
            import cisco_config as cc
        central_in_cisco = cc.central_ip_known(cisco_info or {}, central_ip)
        if cisco_info:
            core_name = (cisco_info.get("hostname") or "Core Router (Cisco)")
            core_addrs = _cisco_addresses(cisco_info)
            core_ifaces = _cisco_interfaces(cisco_info)
        else:
            core_name = "Core Router"
            core_addrs = []
            core_ifaces = []
        nodes[core_key] = {
            "key": core_key, "name": core_name, "ip": central_ip,
            "info": {}, "device": None, "ghost": True, "is_core": True,
            "core_ip": central_ip, "addresses": core_addrs, "interfaces": core_ifaces,
            "neighbors": [], "routes": [],
        }
        if cisco_info:
            nodes[core_key]["platform"] = "Cisco IOS"
            nodes[core_key]["cisco"] = True
    cisco_used = bool(nodes[core_key].get("cisco"))
    core_addrs_live = nodes[core_key]["addresses"]

    # --- یال‌ها -------------------------------------------------------------
    edges: list[dict] = []
    edge_seen: set = set()

    def _add_edge(a_key: str, b_key: str, a_if: str, b_if: str, a_ip: str, b_ip: str,
                  ev: str) -> None:
        if a_key == b_key:
            return
        if (a_key, b_key) > (b_key, a_key):
            a_key, b_key, a_if, b_if, a_ip, b_ip = b_key, a_key, b_if, a_if, b_ip, a_ip
        k = (a_key, b_key, a_if, b_if)
        if k in edge_seen:
            # اولویت شواهد: mndp > cisco > subnet > route > default
            rank = {"mndp": 0, "cisco": 1, "subnet": 2, "route": 3, "default": 4}
            for e in edges:
                if (e["a"], e["b"], e["a_if"], e["b_if"]) == k:
                    if rank.get(ev, 9) < rank.get(e["ev"], 9):
                        e["ev"] = ev
                    break
            return
        edge_seen.add(k)
        edges.append({"a": a_key, "b": b_key, "a_if": a_if, "b_if": b_if,
                      "a_ip": a_ip, "b_ip": b_ip, "ev": ev})

    # 3-الف) همسایگی MNDP — اینترفیسِ سمت مقابل از آدرسِ همسایه استخراج می‌شود
    for key in order:
        node = nodes[key]
        for nb in node["neighbors"]:
            nb_ips = [_ip_of(x) for x in (nb.get("address") or "").split(",") if x.strip()]
            if not nb_ips:
                continue
            a_if = nb.get("interface") or ""
            a_ip = ""
            # IP سمت خودِ دستگاه روی همان اینترفیس (ترجیحاً هم‌ساب‌نت با همسایه)
            if a_if:
                cand = [a for a in node["addresses"] if a.get("interface") == a_if]
                for c in cand:
                    for nip in nb_ips:
                        if nip and _same_subnet(c.get("address"), nip + "/32"):
                            a_ip = _ip_of(c.get("address"))
                            break
                    if a_ip:
                        break
                if not a_ip and cand:
                    a_ip = _ip_of(cand[0].get("address"))
            for nip in nb_ips:
                if not nip:
                    continue
                if nip == central_ip:
                    _add_edge(key, core_key, a_if, "", a_ip, nip, "mndp")
                    continue
                peer_key = None
                # تطبیق با دستگاه خوانده‌شده: IP اتصال، آدرس‌ها یا identity
                for k2 in order:
                    n2 = nodes[k2]
                    if k2 == key:
                        continue
                    if n2["ip"] == nip or nip == central_ip:
                        peer_key = k2
                        break
                    if any(_ip_of(a.get("address")) == nip for a in n2["addresses"]):
                        peer_key = k2
                        break
                    if nb.get("identity") and n2["name"] == nb["identity"]:
                        peer_key = k2
                        break
                if peer_key is None:
                    # گرهٔ شبح: دستگاهی که آن را نخوانده‌ایم ولی در MNDP دیده شده
                    nm = (nb.get("identity") or "").strip()
                    ghost = _make_node("g:" + nip, nm or nip, nip, None, None, ghost=True)
                    if nb.get("platform"):
                        ghost["platform"] = nb["platform"]
                    nodes[ghost["key"]] = ghost
                    peer_key = ghost["key"]
                peer = nodes[peer_key]
                b_if = _iface_of(peer["addresses"], nip)
                if not b_if and peer["addresses"]:
                    # fallback: ساب‌نت مشترک با IP سمت این دستگاه
                    if a_ip:
                        for c in peer["addresses"]:
                            if a_ip and _same_subnet(c.get("address"), a_ip + "/32"):
                                b_if = c.get("interface") or ""
                                break
                _add_edge(key, peer_key, a_if, b_if, a_ip, nip, "mndp")

    # 3-ب) اشتراک ساب‌نت بین گره‌های دارای آدرس
    # روتر مرکزیِ سیسکو (با آدرس‌های کانفیگ) هم در مقایسهٔ ساب‌نت شرکت می‌کند
    keyed = [k for k in order if nodes[k]["addresses"]]
    if cisco_used and core_key not in keyed and nodes[core_key]["addresses"]:
        keyed.append(core_key)
    for i in range(len(keyed)):
        for j in range(i + 1, len(keyed)):
            ka, kb = keyed[i], keyed[j]
            na, nb_ = nodes[ka], nodes[kb]
            done = False
            for aa in na["addresses"]:
                for ab in nb_["addresses"]:
                    if aa.get("address") and ab.get("address") and _same_subnet(aa["address"], ab["address"]):
                        _add_edge(ka, kb, aa.get("interface") or "", ab.get("interface") or "",
                                  _ip_of(aa["address"]), _ip_of(ab["address"]), "subnet")
                        done = True
                        break
                if done:
                    break

    # 3-ج) یال‌های روتینگ: همهٔ next-hopهای هر دستگاه به سمت روتر مرکزی.
    # روش بهتر (درخواست کاربر) و Task 21: هر روتر چند IP روی اینترفیس‌های مختلف
    # دارد؛ «تمام» اینترفیس‌ها و IPها برای مسیریابی چک می‌شوند — گیت‌وی‌های
    # همهٔ روت‌های پوشش‌دهندهٔ central_ip (روت خاص هر اینترفیس، روت‌های جایگزین
    # با distance بدتر و روت پیش‌فرض) همه یال می‌گیرند:
    #   * طولانی‌ترین پیشوند منطبق با IP مرکزی اول، وگرنه/بعد روت پیش‌فرض؛
    #   * اگر گیت‌وی خودِ IP مرکزی بود → یال مستقیم به core؛
    #   * اگر گیت‌وی یکی از دستگاه‌های خوانده‌شده بود → یال به همان دستگاه
    #     (زنجیرهٔ بالادست از طریق روترهای میانی تشکیل می‌شود)؛
    #   * وگرنه گرهٔ شبحِ «hop بالادست» ساخته می‌شود تا مسیر تا جایی که شواهد
    #     اجازه می‌دهد نمایش داده شود.
    for key in order:
        if key == core_key:
            continue  # بالادستِ خودِ روتر مرکزی در مسیر «تا مرکز» نقشی ندارد
        node = nodes[key]
        for cand in _route_all_next_hops(node["routes"], central_ip):
            gw_ip, gw_if = cand["gw"], cand["gw_if"]
            ev = "route" if cand["kind"] == "specific" else "default"
            a_ip, a_if = _addr_iface_toward(node["addresses"], gw_ip)
            if not a_if:
                a_if = _arp_iface_toward(node.get("arp") or [], gw_ip) or gw_if
            if gw_ip == central_ip:
                _add_edge(key, core_key, a_if, "", a_ip, gw_ip, ev)
                continue
            # گیت‌وی متعلق به کدام دستگاه خوانده‌شده است؟
            peer_key = None
            for k2 in order:
                if k2 == key:
                    continue
                n2 = nodes[k2]
                if n2["ip"] == gw_ip or any(_ip_of(a.get("address")) == gw_ip for a in n2["addresses"]):
                    peer_key = k2
                    break
            if peer_key is not None:
                peer = nodes[peer_key]
                b_if = _iface_of(peer["addresses"], gw_ip)
                _add_edge(key, peer_key, a_if, b_if, a_ip, gw_ip, ev)
                continue
            # گیت‌وی روی خودِ روتر مرکزی سیسکو؟ (IP دقیق یا داخل ساب‌نت‌های کانفیگ)
            if cisco_used and core_addrs_live:
                c_ip, c_if = _core_iface_toward(core_addrs_live, gw_ip)
                if c_if:
                    _add_edge(key, core_key, a_if, c_if, a_ip, c_ip or gw_ip, ev)
                    continue
            # hop بالادست ناشناخته → گرهٔ شبح
            gkey = "g:" + gw_ip
            if gkey not in nodes:
                ghost = _make_node(gkey, gw_ip, gw_ip, None, None, ghost=True)
                ghost["upstream"] = True
                nodes[gkey] = ghost
            _add_edge(key, gkey, a_if, gw_if, a_ip, gw_ip, ev)

    # 3-د) روت‌های استاتیک کانفیگ سیسکو — یال‌های core→دستگاه (اولین روتر بعد از
    # مرکز). گیت‌ویِ هر روتِ استاتیک سیسکو، روتر میکروتیکی است که آن ساب‌نت را
    # سرو می‌کند؛ این قوی‌ترین شواهد از سمت روتر مرکزی است.
    if cisco_used:
        for rt in (cisco_info.get("static_routes") or []):
            prefix = rt.get("prefix") or ""
            if not prefix or "/" not in prefix:
                continue
            for gw_ip in (rt.get("next_hops") or []):
                if not gw_ip or gw_ip == central_ip:
                    continue
                c_ip, c_if = _core_iface_toward(core_addrs_live, gw_ip)
                peer_key = None
                peer_aip, peer_aif = "", ""
                for k2 in order:
                    n2 = nodes[k2]
                    if n2["ip"] == gw_ip:
                        peer_key, peer_aip, peer_aif = k2, gw_ip, _iface_of(n2["addresses"], gw_ip)
                        break
                    t_ip, t_if = _addr_iface_toward(n2["addresses"], gw_ip)
                    if t_if:
                        peer_key, peer_aip, peer_aif = k2, t_ip, t_if
                        break
                if peer_key is not None:
                    _add_edge(core_key, peer_key, c_if, peer_aif, c_ip or gw_ip, peer_aip or gw_ip, "cisco")
                    continue
                gkey = "g:" + gw_ip
                if gkey not in nodes:
                    g = _make_node(gkey, gw_ip, gw_ip, None, None, ghost=True)
                    g["upstream"] = True
                    nodes[gkey] = g
                _add_edge(core_key, gkey, c_if, "", c_ip or gw_ip, gw_ip, "cisco")

    # --- BFS کوتاه‌ترین مسیر تا core -----------------------------------------
    adj: dict[str, list[int]] = {}
    for idx, e in enumerate(edges):
        adj.setdefault(e["a"], []).append(idx)
        adj.setdefault(e["b"], []).append(idx)

    ev_rank = {"mndp": 0, "cisco": 1, "subnet": 2, "route": 3, "default": 4}

    def _hop_from_edge(e: dict, src: str) -> dict:
        if e["a"] == src:
            return {"from": e["a"], "to": e["b"], "from_if": e["a_if"], "to_if": e["b_if"],
                    "from_ip": e["a_ip"], "to_ip": e["b_ip"], "ev": e["ev"]}
        return {"from": e["b"], "to": e["a"], "from_if": e["b_if"], "to_if": e["a_if"],
                "from_ip": e["b_ip"], "to_ip": e["a_ip"], "ev": e["ev"]}

    paths: dict[str, dict] = {}
    for key in order + ([core_key] if not nodes[core_key]["ghost"] else []):
        if key == core_key:
            paths[key] = {"reachable": True, "hops": [], "main_ip": nodes[key]["ip"],
                          "is_core": True}
            continue
        # BFS
        parent: dict[str, tuple[str, dict]] = {}
        visited = {key}
        queue = [key]
        found = False
        while queue and not found:
            cur = queue.pop(0)
            for idx in sorted(adj.get(cur, []), key=lambda i: ev_rank.get(edges[i]["ev"], 9)):
                e = edges[idx]
                nxt = e["b"] if e["a"] == cur else e["a"]
                if nxt in visited:
                    continue
                visited.add(nxt)
                parent[nxt] = (cur, e)
                if nxt == core_key:
                    found = True
                    break
                queue.append(nxt)
        if not found:
            paths[key] = {"reachable": False, "hops": [], "main_ip": nodes[key]["ip"],
                          "is_core": False}
            continue
        # بازسازی مسیر از core به عقب
        chain = []
        cur = core_key
        while cur != key:
            prev, e = parent[cur]
            hop = _hop_from_edge(e, src=prev)
            hop["from_key"], hop["to_key"] = hop["from"], hop["to"]
            hop["from_name"] = nodes[hop["from"]]["name"]
            hop["to_name"] = nodes[hop["to"]]["name"]
            chain.append(hop)
            cur = prev
        chain.reverse()  # از دستگاه به سمت core
        main_ip = chain[0]["from_ip"] or nodes[key]["ip"] if chain else nodes[key]["ip"]
        paths[key] = {"reachable": True, "hops": chain, "main_ip": main_ip,
                      "is_core": False}

    # --- زنجیرهٔ بالادست (best-effort) برای دستگاه‌های بدون مسیر کامل ---------
    # اگر BFS به core نرسید، hopهای بالادست را از «همهٔ» روت‌های پوشش‌دهنده
    # (روت خاص هر اینترفیس + روت‌های جایگزین + روت پیش‌فرض) دنبال می‌کنیم؛
    # اولین گیت‌وی‌ای که به دستگاه شناخته‌شده یا خودِ core برسد انتخاب می‌شود تا
    # همهٔ اینترفیس‌ها/IPها واقعاً برای مسیریابی چک شده باشند (Task 21).
    # خروجی: (زنجیرهٔ hopها، اطلاعات پایان زنجیره برای تحلیل دلیل نرسیدن)
    def _upstream_chain(key: str, max_hops: int = 6) -> tuple[list[dict], dict]:
        chain: list[dict] = []
        cur = key
        seen = {key}
        end: dict = {"kind": "none", "to_key": key, "ip": nodes.get(key, {}).get("ip") or "",
                     "name": nodes.get(key, {}).get("name") or ""}
        while len(chain) < max_hops:
            node = nodes.get(cur)
            if not node:
                end = {"kind": "unknown-node", "to_key": cur, "ip": "", "name": ""}
                break
            cands = _route_all_next_hops(node.get("routes") or [], central_ip)
            if not cands:
                end = {"kind": "no-route", "to_key": cur, "ip": node.get("ip") or "",
                       "name": node.get("name") or ""}
                break
            # ترجیح: اولین گیت‌وی که به دستگاه شناخته‌شده یا خودِ core می‌رسد؛
            # وگرنه اولین گیت‌وی (گرهٔ شبح) به‌عنوان انتهای شواهد
            chosen = None
            for cand in cands:
                gw_ip = cand["gw"]
                nxt_key = None
                if gw_ip == central_ip:
                    nxt_key = core_key  # گیت‌وی خودِ روتر مرکزی است
                else:
                    for k2 in order:
                        if k2 == cur:
                            continue
                        n2 = nodes[k2]
                        if n2["ip"] == gw_ip or any(_ip_of(a.get("address")) == gw_ip for a in (n2["addresses"] or [])):
                            nxt_key = k2
                            break
                    if nxt_key is None and cisco_used and core_addrs_live and _core_iface_toward(core_addrs_live, gw_ip)[1]:
                        nxt_key = core_key  # گیت‌وی روی خودِ روتر مرکزی سیسکو است
                if nxt_key is not None and not str(nxt_key).startswith("g:"):
                    chosen = (cand, nxt_key)
                    break
                if chosen is None:
                    chosen = (cand, "g:" + gw_ip)
            if chosen is None:
                end = {"kind": "no-route", "to_key": cur, "ip": node.get("ip") or "",
                       "name": node.get("name") or ""}
                break
            cand, nxt_key = chosen
            gw_ip, gw_if = cand["gw"], cand["gw_if"]
            kind = cand["kind"]
            if nxt_key.startswith("g:") and nxt_key not in nodes:
                g = _make_node(nxt_key, gw_ip, gw_ip, None, None, ghost=True)
                g["upstream"] = True
                nodes[nxt_key] = g
            a_ip, a_if = _addr_iface_toward(node.get("addresses") or [], gw_ip)
            if not a_if:
                a_if = _arp_iface_toward(node.get("arp") or [], gw_ip) or gw_if
            to_node = nodes[nxt_key]
            chain.append({
                "from_key": cur, "to_key": nxt_key,
                "from_name": node["name"], "to_name": to_node["name"],
                "from_if": a_if, "to_if": ("" if to_node["ghost"] else gw_if),
                "from_ip": a_ip, "to_ip": gw_ip,
                "ev": ("route" if kind == "specific" else "default"),
            })
            if nxt_key == core_key:
                end = {"kind": "core", "to_key": core_key, "ip": central,
                       "name": to_node["name"]}
                break  # زنجیرهٔ بالادست به روتر مرکزی رسید
            if nxt_key in seen:
                end = {"kind": "loop", "to_key": nxt_key, "ip": gw_ip,
                       "name": to_node["name"]}
                break  # حلقهٔ روتینگ — ادامه نمی‌دهیم
            seen.add(nxt_key)
            cur = nxt_key
            if nodes[nxt_key]["ghost"]:
                end = {"kind": "ghost", "to_key": nxt_key, "ip": gw_ip,
                       "name": to_node["name"]}
                break  # از این hop اطلاعات روتینگ نداریم — پایان شواهد
        if len(chain) >= max_hops and end.get("kind") == "none":
            end = {"kind": "max", "to_key": chain[-1]["to_key"] if chain else key,
                   "ip": chain[-1]["to_ip"] if chain else "", "name": ""}
        return chain, end

    upstream_count = 0
    for key in order:
        p = paths.get(key)
        if not p or p.get("reachable"):
            continue
        up, up_end = _upstream_chain(key)
        p["upstream_end"] = up_end
        if up:
            p["upstream"] = up
            p["upstream_partial"] = True
            upstream_count += 1

    reachable = sum(1 for k in order if paths.get(k, {}).get("reachable"))
    links = sum(len(paths.get(k, {}).get("hops") or []) for k in order)
    return {
        "nodes": nodes,
        "edges": edges,
        "paths": paths,
        "core_key": core_key,
        "central_ip": central_ip,
        "order": order,
        "cisco": ({
            "used": cisco_used,
            "hostname": (cisco_info or {}).get("hostname") or "",
            "static_routes": len((cisco_info or {}).get("static_routes") or []),
            "addresses": len(nodes[core_key]["addresses"]),
            "interfaces": len(nodes[core_key]["interfaces"]),
            "central_ip_found": central_in_cisco,
        } if (cisco_info or cisco) else None),
        "cisco_data": (cisco_info if cisco_used else None),
        "summary": {
            "devices": len(order),
            "reachable": reachable,
            "unreachable": len(order) - reachable,
            "upstream_only": upstream_count,
            "links": links,
            "central_ip": central_ip,
            "cisco_loaded": cisco_used,
            "cisco_hostname": (nodes[core_key].get("platform") == "Cisco IOS" and nodes[core_key]["name"]) or "",
        },
    }


def next_hop_evidence(info: dict, next_ip: str, max_lines: int = 6) -> list[str]:
    """خطوط شاهد روتینگ/همسایگی برای صفحهٔ PDF هر دستگاه."""
    lines: list[str] = []
    next_ip = (next_ip or "").strip()
    for rt in (info.get("routes") or []):
        gws = _split_gateway(rt.get("gateway") or "") + _split_gateway(rt.get("immediate_gw") or "")
        gw_txt = ", ".join((g + (("%" + i) if i else "")) for g, i in gws)
        if not gw_txt:
            continue
        mark = ""
        if next_ip and any(g == next_ip for g, _i in gws):
            mark = "  << next-hop"
        lines.append(f"route {rt.get('dst_address') or '-'} via {gw_txt}"
                     + (f" (distance {rt['distance']})" if rt.get("distance") else "") + mark)
        if len(lines) >= max_lines:
            break
    for nb in (info.get("neighbors") or []):
        if next_ip and next_ip in [ _ip_of(x) for x in (nb.get("address") or "").split(",") ]:
            lines.append(f"neighbor {nb.get('identity') or '-'} {nb.get('address')} on {nb.get('interface') or '-'}"
                         + (f" ({nb.get('platform')} {nb.get('version')})" if nb.get("platform") else ""))
            if len(lines) >= max_lines + 2:
                break
    return lines[: max_lines + 2]
