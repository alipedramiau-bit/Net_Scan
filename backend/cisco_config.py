"""Cisco IOS config parser — کانفیگ روتر مرکزی سیسکو.

روتر مرکزی شبکه معمولاً یک Cisco IOS/IOS-XE است و از طریق RouterOS API قابل
خواندن نیست. کاربر خروجی «show running-config» (یا startup-config) این روتر را
به‌صورت یک فایل متنی بارگذاری می‌کند و این ماژول آن را به ساختار داده‌ای
تبدیل می‌کند که route_topology.build_topology بتواند در یافتن مسیر دستگاه‌ها
تا روتر مرکزی استفاده کند:

- hostname
- اینترفیس‌ها (فیزیکی، زیراینترفیس dot1Q، SVI، Loopback، Tunnel، Port-channel)
  با توضیح (description)، آدرس‌های IP (اصلی و secondary)، وضعیت shutdown
- روت‌های استاتیک (ip route) شامل vrf، گیت‌وی (IP یا اینترفیس) و distance
- ساب‌نت‌های connected برای تطبیق اینترفیسِ سمتِ روتر مرکزی روی هر لینک

همهٔ چیز فقط با stdlib پارس می‌شود و هر خط نامفهوم بی‌صدا نادیده گرفته
می‌شود (تا کانفیگ واقعی و ناقص هم قابل استفاده بماند).
"""
from __future__ import annotations

import ipaddress
import re

# حد مجاز حجم فایل کانفیگ (بایت) — ۲ مگابایت برای running-config بسیار کافی است
MAX_CONFIG_BYTES = 2 * 1024 * 1024


# ---------------------------------------------------------------------------
# ابزارهای ماسک و آدرس
# ---------------------------------------------------------------------------
def _mask_to_prefix(mask: str) -> int:
    """'255.255.255.0' -> 24  |  '0.0.0.0' -> 0  |  '24' (پیشوند خام) -> 24"""
    m = (mask or "").strip()
    if not m:
        return -1
    if m.isdigit():
        try:
            v = int(m)
        except ValueError:
            return -1
        return v if 0 <= v <= 32 else -1
    try:
        return ipaddress.ip_network(f"0.0.0.0/{m}", strict=False).prefixlen
    except ValueError:
        return -1


def _prefix_str(ip: str, mask_or_len: str) -> str:
    """('172.19.1.6', '255.255.255.0') -> '172.19.1.0/24' (strict=False)."""
    pl = _mask_to_prefix(mask_or_len)
    if pl < 0:
        return ""
    try:
        net = ipaddress.ip_network(f"{ip}/{pl}", strict=False)
    except ValueError:
        return ""
    return str(net)


_IP_RE = r"\d{1,3}(?:\.\d{1,3}){3}"


# ---------------------------------------------------------------------------
# پارس کل کانفیگ
# ---------------------------------------------------------------------------
def parse_cisco_config(text: str) -> dict:
    """کانفیگ متنی IOS را به ساختار قابل استفاده تبدیل می‌کند.

    خروجی:
      {
        "hostname": str,
        "interfaces": [ {name, type, description, shutdown, subinterface, vlan,
                         addresses: [{ip, mask, prefix, subnet}], primary_ip, ...} ],
        "static_routes": [ {prefix, destination, mask, next_hops: [..],
                            interface, distance, vrf, name} ],
        "networks": [ {subnet, interface, ip, secondary} ],   # ساب‌نت‌های connected
        "version": str, "warnings": [..],
        "ok": True, "error": None,
      }
    """
    lines = (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    interfaces: list[dict] = []
    static_routes: list[dict] = []
    warnings: list[str] = []
    hostname = ""
    version = ""
    cur: dict | None = None

    def _finish_iface() -> None:
        nonlocal cur
        if cur is not None:
            interfaces.append(cur)
            cur = None

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        s = line.strip()
        if s.startswith("!"):
            continue
        low = s.lower()

        # --- شروع/پایان بلاک اینترفیس -------------------------------------
        m = re.match(r"^interface\s+(\S+)\s*$", s, re.IGNORECASE)
        if m:
            _finish_iface()
            name = m.group(1).strip()
            cur = {
                "name": name,
                "type": _iface_type(name),
                "description": "",
                "shutdown": False,
                "subinterface": "." in name.split()[0] if name else False,
                "vlan": None,
                "addresses": [],
                "primary_ip": "",
                "vrf": "",
            }
            continue

        if cur is not None:
            # خروج از بلاک اینترفیس: هر خطی که در سطح global است (روت، hostname و ...)
            m_ip = re.match(r"^ip\s+address\s+(" + _IP_RE + r")\s+(" + _IP_RE + r"|\d{1,2})"
                            r"(?:\s+secondary)?\s*$", s, re.IGNORECASE)
            if m_ip:
                ip, mask = m_ip.group(1), m_ip.group(2)
                subnet = _prefix_str(ip, mask)
                secondary = bool(re.search(r"\ssecondary\s*$", s, re.IGNORECASE))
                cur["addresses"].append({
                    "ip": ip, "mask": mask, "prefix": subnet.split("/")[-1] if subnet else "",
                    "subnet": subnet, "secondary": secondary,
                })
                if not secondary and not cur["primary_ip"]:
                    cur["primary_ip"] = ip
                continue
            m_desc = re.match(r"^description\s+(.*?)\s*$", s, re.IGNORECASE)
            if m_desc:
                cur["description"] = m_desc.group(1).strip()
                continue
            if re.match(r"^shutdown\s*$", s, re.IGNORECASE):
                cur["shutdown"] = True
                continue
            m_vlan = re.match(r"^encapsulation\s+dot1[qQ]\s+(\d+)", s, re.IGNORECASE)
            if m_vlan:
                cur["vlan"] = int(m_vlan.group(1))
                continue
            m_vrf = re.match(r"^(?:ip\s+)?vrf\s+forwarding\s+(\S+)", s, re.IGNORECASE)
            if m_vrf:
                cur["vrf"] = m_vrf.group(1)
                continue
            m_no_ip = re.match(r"^no\s+ip\s+address\s*$", s, re.IGNORECASE)
            if m_no_ip:
                continue
            # خط global-level داخل بلاک باز؟ → بلاک را ببند و ادامه بده
            if _is_global_line(low):
                _finish_iface()
            else:
                continue

        # --- خطوط global -----------------------------------------------------
        m_hn = re.match(r"^hostname\s+(\S+)\s*$", s, re.IGNORECASE)
        if m_hn:
            hostname = m_hn.group(1)
            continue
        m_ver = re.match(r"^version\s+(\S+)\s*$", s, re.IGNORECASE)
        if m_ver:
            version = m_ver.group(1)
            continue
        m_rt = re.match(
            r"^ip\s+route(?:\s+vrf\s+(\S+))?\s+(" + _IP_RE + r")\s+(" + _IP_RE + r"|\d{1,2})"
            r"\s+(\S+(?:\s+\S+)*?)\s*$", s, re.IGNORECASE)
        if m_rt:
            vrf = (m_rt.group(1) or "").strip()
            dest, mask, rest = m_rt.group(2), m_rt.group(3), m_rt.group(4).strip()
            prefix = _prefix_str(dest, mask)
            toks = rest.split()
            nh: list[str] = []
            iface = ""
            distance = ""
            name_tag = ""
            for tk in toks:
                if re.fullmatch(_IP_RE, tk):
                    nh.append(tk)
                elif re.fullmatch(r"\d{1,3}", tk) and nh and distance == "":
                    # عدد بعد از گیت‌وی = distance (یا name/مقدار آن)
                    distance = tk
                elif tk.lower() == "name":
                    name_tag = "name"
                elif name_tag == "name":
                    name_tag = tk
                elif not iface:
                    iface = tk
            # distance واقعی: آخرین عدد مستقل که نام‌گذاری نباشد؛ ساده نگه می‌داریم
            static_routes.append({
                "prefix": prefix or f"{dest}/{_mask_to_prefix(mask)}",
                "destination": dest,
                "mask": mask,
                "next_hops": nh,
                "interface": iface,
                "distance": distance,
                "vrf": vrf,
                "name": name_tag if name_tag and name_tag != "name" else "",
            })
            continue
        # خطوط دیگر در سطح global نادیده گرفته می‌شوند

    _finish_iface()

    # --- ساب‌نت‌های connected ------------------------------------------------
    networks: list[dict] = []
    seen_net = set()
    for it in interfaces:
        for a in it["addresses"]:
            if not a.get("subnet"):
                continue
            k = (a["subnet"], it["name"])
            if k in seen_net:
                continue
            seen_net.add(k)
            networks.append({
                "subnet": a["subnet"],
                "interface": it["name"],
                "ip": a["ip"],
                "secondary": bool(a.get("secondary")),
                "shutdown": bool(it.get("shutdown")),
            })

    if not hostname:
        warnings.append("hostname در کانفیگ پیدا نشد")
    if not interfaces:
        warnings.append("هیچ اینترفیسی در کانفیگ پیدا نشد")
    if not static_routes:
        warnings.append("روت استاتیکی در کانفیگ پیدا نشد")

    return {
        "hostname": hostname,
        "version": version,
        "interfaces": interfaces,
        "static_routes": static_routes,
        "networks": networks,
        "warnings": warnings,
        "ok": True,
        "error": None,
    }


def _iface_type(name: str) -> str:
    n = (name or "").lower()
    for key, typ in (
        ("gigabitethernet", "GigabitEthernet"), ("gi", "GigabitEthernet"),
        ("tengigabitethernet", "TenGigabitEthernet"), ("te", "TenGigabitEthernet"),
        ("fastethernet", "FastEthernet"), ("fa", "FastEthernet"),
        ("ethernet", "Ethernet"), ("vlan", "VLAN SVI"), ("loopback", "Loopback"),
        ("tunnel", "Tunnel"), ("serial", "Serial"), ("port-channel", "Port-channel"),
        ("po", "Port-channel"), ("mgmt", "Management"),
    ):
        if n.startswith(key):
            return typ
    return "Cisco"


def _is_global_line(low: str) -> bool:
    """تشخیص خط global-level برای بستن بلاک اینترفیس."""
    starts = (
        "hostname", "ip route", "ip dhcp", "ip access-list", "ip prefix-list",
        "router ", "line ", "access-list", "enable", "username", "aaa ",
        "crypto", "banner", "no ip domain", "spanning-tree mode",
        "ip name-server", "ntp ", "snmp-server", "logging ", "clock ",
    )
    return low.startswith(starts)


# ---------------------------------------------------------------------------
# جستجوها روی کانفیگ پارس‌شده
# ---------------------------------------------------------------------------
def find_connected_iface(cisco: dict, ip: str) -> tuple[str, str]:
    """اینترفیسِ سمتِ سیسکو که IP داده‌شده در ساب‌نتِ آن است + IP خودِ سیسکو.

    خروجی: (نام_اینترفیس, ip_سیسکو) — اگر چند ساب‌نت منطبق باشد،
    طولانی‌ترین پیشوند و اینترفیس غیر shutdown ترجیح دارد.
    """
    try:
        tip = ipaddress.ip_address((ip or "").strip())
    except ValueError:
        return ("", "")
    best_key: tuple[int, int] = (-1, 0)  # (prefixlen, primary=1/secondary=0)
    best: tuple[str, str] = ("", "")
    for net in (cisco or {}).get("networks") or []:
        if net.get("shutdown"):
            continue
        try:
            nobj = ipaddress.ip_network(net.get("subnet") or "", strict=False)
        except ValueError:
            continue
        if tip.version != nobj.version or tip not in nobj:
            continue
        key = (nobj.prefixlen, 0 if net.get("secondary") else 1)
        if key > best_key:
            best_key = key
            best = (net.get("interface") or "", net.get("ip") or "")
    return best


def routes_toward(cisco: dict, ip: str) -> list[dict]:
    """روت‌های استاتیک سیسکو که IP داده‌شده را پوشش می‌دهند (طولانی‌ترین پیشوند اول)."""
    try:
        tip = ipaddress.ip_address((ip or "").strip())
    except ValueError:
        return []
    hits: list[tuple[int, dict]] = []
    for rt in (cisco or {}).get("static_routes") or []:
        try:
            net = ipaddress.ip_network(rt.get("prefix") or "", strict=False)
        except ValueError:
            continue
        if tip.version != net.version or tip not in net:
            continue
        hits.append((net.prefixlen, rt))
    hits.sort(key=lambda x: -x[0])
    return [rt for _pl, rt in hits]


def central_ip_known(cisco: dict, ip: str) -> bool:
    """آیا IP روتر مرکزی بین آدرس‌های کانفیگ سیسکو هست؟"""
    ipn = (ip or "").strip()
    for it in (cisco or {}).get("interfaces") or []:
        for a in it.get("addresses") or []:
            if (a.get("ip") or "").strip() == ipn:
                return True
    return False


def summary(cisco: dict) -> dict:
    """خلاصهٔ کانفیگ برای نمایش در UI و هدر گزارش."""
    ifaces = (cisco or {}).get("interfaces") or []
    n_addr = sum(len(i.get("addresses") or []) for i in ifaces)
    n_up = sum(1 for i in ifaces if not i.get("shutdown"))
    return {
        "hostname": (cisco or {}).get("hostname") or "",
        "version": (cisco or {}).get("version") or "",
        "interfaces": len(ifaces),
        "interfaces_up": n_up,
        "addresses": n_addr,
        "static_routes": len((cisco or {}).get("static_routes") or []),
        "networks": len((cisco or {}).get("networks") or []),
        "warnings": list((cisco or {}).get("warnings") or []),
    }


def looks_like_cisco_config(text: str) -> bool:
    """بررسی سرانگشتی اینکه متن، کانفیگ Cisco IOS است (نه فایل تصادفی)."""
    low = (text or "").lower()
    hits = 0
    if re.search(r"^hostname\s+\S+", low, re.MULTILINE):
        hits += 2
    if re.search(r"^interface\s+\S+", low, re.MULTILINE):
        hits += 2
    if re.search(r"^ip\s+route\s+\S+", low, re.MULTILINE):
        hits += 2
    if re.search(r"^ip\s+address\s+" + _IP_RE, low, re.MULTILINE):
        hits += 1
    if re.search(r"^!\s*$", low, re.MULTILINE):
        hits += 1
    if "version" in low.split("\n", 1)[0] or re.search(r"^version\s+\S+", low, re.MULTILINE):
        hits += 1
    return hits >= 4
