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


def build_topology(infos: list[dict], devices: list[dict], central_ip: str) -> dict:
    """گراف لینک‌ها + کوتاه‌ترین مسیر هر دستگاه تا روتر مرکزی.

    infos  — خروجی collect_topology_info_many (به ترتیب دستگاه‌ها)
    devices— ردیف‌های دیتابیس (fetch_devices_by_ips / query_devices)
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
    if core_key:
        nodes[core_key]["is_core"] = True
        nodes[core_key]["core_ip"] = central_ip
    else:
        core_key = "core"
        nodes[core_key] = {
            "key": core_key, "name": "Core Router", "ip": central_ip,
            "info": {}, "device": None, "ghost": True, "is_core": True,
            "core_ip": central_ip, "addresses": [], "interfaces": [],
            "neighbors": [], "routes": [],
        }

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
            # اولویت شواهد: mndp > subnet > route > default
            rank = {"mndp": 0, "subnet": 1, "route": 2, "default": 3}
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
    keyed = [k for k in order if nodes[k]["addresses"]]
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

    # 3-ج) یال‌های روتینگ: بهترین next-hop هر دستگاه به سمت روتر مرکزی.
    # روش بهتر (درخواست کاربر): از «روت پیش‌فرض» و hop بالای دستگاه استفاده می‌کنیم —
    #   * طولانی‌ترین پیشوند منطبق با IP مرکزی، وگرنه روت پیش‌فرض با کمترین distance؛
    #   * اگر گیت‌وی خودِ IP مرکزی بود → یال مستقیم به core؛
    #   * اگر گیت‌وی یکی از دستگاه‌های خوانده‌شده بود → یال به همان دستگاه
    #     (زنجیرهٔ بالادست از طریق روترهای میانی تشکیل می‌شود)؛
    #   * وگرنه گرهٔ شبحِ «hop بالادست» ساخته می‌شود تا مسیر تا جایی که شواهد
    #     اجازه می‌دهد نمایش داده شود.
    for key in order:
        if key == core_key:
            continue  # بالادستِ خودِ روتر مرکزی در مسیر «تا مرکز» نقشی ندارد
        node = nodes[key]
        hops, kind = _route_next_hops(node["routes"], central_ip)
        if not hops:
            continue
        ev = "route" if kind == "specific" else "default"
        for gw_ip, gw_if in hops:
            if not gw_ip:
                continue
            a_ip, a_if = _addr_iface_toward(node["addresses"], gw_ip)
            if not a_if:
                a_if = gw_if
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
            # hop بالادست ناشناخته → گرهٔ شبح
            gkey = "g:" + gw_ip
            if gkey not in nodes:
                ghost = _make_node(gkey, gw_ip, gw_ip, None, None, ghost=True)
                ghost["upstream"] = True
                nodes[gkey] = ghost
            _add_edge(key, gkey, a_if, gw_if, a_ip, gw_ip, ev)

    # --- BFS کوتاه‌ترین مسیر تا core -----------------------------------------
    adj: dict[str, list[int]] = {}
    for idx, e in enumerate(edges):
        adj.setdefault(e["a"], []).append(idx)
        adj.setdefault(e["b"], []).append(idx)

    ev_rank = {"mndp": 0, "subnet": 1, "route": 2, "default": 3}

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
    # اگر BFS به core نرسید، از «روت پیش‌فرض / طولانی‌ترین پیشوند» hopهای
    # بالادست را دنبال می‌کنیم تا جایی که شواهد اجازه می‌دهد (حداکثر ۶ گام)
    # تا گزارش به‌جای «هیچ مسیری»، مسیرِ تا سرِ حدِ شواهد را نشان دهد.
    def _upstream_chain(key: str, max_hops: int = 6) -> list[dict]:
        chain: list[dict] = []
        cur = key
        seen = {key}
        while len(chain) < max_hops:
            node = nodes.get(cur)
            if not node:
                break
            hops, kind = _route_next_hops(node.get("routes") or [], central_ip)
            if not hops:
                break
            gw_ip, gw_if = hops[0]
            nxt_key = None
            for k2 in order:
                if k2 == cur:
                    continue
                n2 = nodes[k2]
                if n2["ip"] == gw_ip or any(_ip_of(a.get("address")) == gw_ip for a in (n2["addresses"] or [])):
                    nxt_key = k2
                    break
            if nxt_key is None:
                nxt_key = "g:" + gw_ip
                if nxt_key not in nodes:
                    g = _make_node(nxt_key, gw_ip, gw_ip, None, None, ghost=True)
                    g["upstream"] = True
                    nodes[nxt_key] = g
            a_ip, a_if = _addr_iface_toward(node.get("addresses") or [], gw_ip)
            if not a_if:
                a_if = gw_if
            chain.append({
                "from_key": cur, "to_key": nxt_key,
                "from_name": node["name"], "to_name": nodes[nxt_key]["name"],
                "from_if": a_if, "to_if": ("" if nodes[nxt_key]["ghost"] else gw_if),
                "from_ip": a_ip, "to_ip": gw_ip,
                "ev": ("route" if kind == "specific" else "default"),
            })
            if nxt_key in seen:
                break  # حلقهٔ روتینگ — ادامه نمی‌دهیم
            seen.add(nxt_key)
            cur = nxt_key
            if nodes[nxt_key]["ghost"]:
                break  # از این hop اطلاعات روتینگ نداریم — پایان شواهد
        return chain

    upstream_count = 0
    for key in order:
        p = paths.get(key)
        if not p or p.get("reachable"):
            continue
        up = _upstream_chain(key)
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
        "summary": {
            "devices": len(order),
            "reachable": reachable,
            "unreachable": len(order) - reachable,
            "upstream_only": upstream_count,
            "links": links,
            "central_ip": central_ip,
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
