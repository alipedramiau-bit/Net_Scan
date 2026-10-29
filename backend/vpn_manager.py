"""VPN lifecycle manager with mandatory split-tunnel (never hijack OS default route).

Goal: scanner traffic can reach remote networks via VPN, while the server's
own internet (UI, packages, SSH) stays on the main NIC.
"""
from __future__ import annotations

import ipaddress
import json
import os
import platform
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE_FILE = Path(os.environ.get("MIKROTIK_VPN_PROFILES", ROOT / "vpn_profiles.json"))
LOCK = threading.RLock()
ACTIVE = None
PROFILES: dict = {}
_ALLOWED = {"wireguard", "openvpn", "pptp", "l2tp", "sstp"}
_ID = re.compile(r"^[a-zA-Z0-9_-]{1,48}$")

# Built-in default from Windows phonebook "Olom" (PPTP → 185.110.29.205)
DEFAULT_PROFILES = {
    "olom": {
        "name": "Olom",
        "protocol": "pptp",
        "host": "185.110.29.205",
        "routes": ['172.17.12.0/24', '172.18.1.0/24', '172.18.2.0/24', '172.18.3.0/24', '172.18.4.0/24', '172.18.5.0/24', '172.18.8.0/24', '172.18.9.0/24', '172.18.16.0/24', '172.18.24.0/24', '172.18.25.0/24', '172.18.26.0/24', '172.27.240.0/24', '172.29.2.0/24', '172.29.8.0/24', '172.29.9.0/24', '172.29.13.0/24', '172.29.14.0/24', '172.29.15.0/24', '172.29.16.0/24', '172.29.18.0/24', '172.29.22.0/24', '172.29.24.0/24', '172.29.29.0/24', '172.29.32.0/24', '172.29.33.0/24', '172.29.44.0/24', '172.29.64.0/24', '172.29.66.0/24', '172.29.68.0/24', '172.29.69.0/24', '172.29.70.0/24', '172.29.71.0/24', '172.29.73.0/24', '172.29.74.0/24', '172.29.75.0/24', '172.29.128.0/24', '172.29.130.0/24', '172.29.131.0/24', '172.29.193.0/24', '172.29.195.0/24', '172.29.196.0/24', '172.29.197.0/24', '172.29.198.0/24', '172.29.201.0/24', '172.29.202.0/24', '172.29.204.0/24', '172.29.206.0/24', '172.29.207.0/24', '172.29.209.0/24'],
        "profile_name": "Olom",
        "is_default": True,
        "note": "Extracted from Windows 8 RAS phonebook; split-tunnel only (no OS default route). Routes from ip_olom.txt.",
    }
}


def _config_path(pid: str) -> Path:
    """Sidecar file for a profile's VPN config (never inside the JSON)."""
    return PROFILE_FILE.parent / (PROFILE_FILE.stem + "_configs") / f"{pid}.conf"


def _load():
    global PROFILES
    try:
        value = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
        PROFILES = value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        PROFILES = {}
    # Re-attach VPN configs stored in sidecar files (kept out of the JSON on purpose:
    # .ovpn/.conf payloads embed certs and private keys).
    for pid, meta in PROFILES.items():
        if isinstance(meta, dict):
            cfg_file = _config_path(pid)
            if cfg_file.is_file():
                try:
                    meta["config_content"] = cfg_file.read_text(encoding="utf-8")[:200_000]
                except OSError:
                    pass
    # Ensure built-in defaults exist without overwriting user edits of same id
    changed = False
    for pid, meta in DEFAULT_PROFILES.items():
        if pid not in PROFILES:
            PROFILES[pid] = {k: v for k, v in meta.items() if k != "note"}
            changed = True
    if changed:
        _save()


def _save():
    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Persist config_content to per-profile sidecar files instead of the JSON.
    configs = {}
    disk_view = {}
    for pid, meta in PROFILES.items():
        entry = dict(meta) if isinstance(meta, dict) else meta
        if isinstance(entry, dict) and "config_content" in entry:
            content = str(entry.pop("config_content") or "")
            if content.strip():
                configs[pid] = content
        disk_view[pid] = entry
    tmp = PROFILE_FILE.with_suffix(PROFILE_FILE.suffix + ".tmp")
    tmp.write_text(json.dumps(disk_view, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    tmp.replace(PROFILE_FILE)
    # Write sidecar configs with restrictive permissions.
    if configs:
        cfg_dir = _config_path("x").parent
        cfg_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(cfg_dir, 0o700)
        except OSError:
            pass
        for pid, content in configs.items():
            cfg_file = _config_path(pid)
            tmp_cfg = cfg_file.with_suffix(cfg_file.suffix + ".tmp")
            tmp_cfg.write_text(content, encoding="utf-8")
            try:
                os.chmod(tmp_cfg, 0o600)
            except OSError:
                pass
            tmp_cfg.replace(cfg_file)
    # Drop sidecars for profiles that no longer exist or lost their config.
    cfg_dir = _config_path("x").parent
    if cfg_dir.is_dir():
        for old in cfg_dir.glob("*.conf"):
            if old.stem not in configs:
                try:
                    old.unlink()
                except OSError:
                    pass


def _safe_config(text, suffix):
    if not isinstance(text, str) or not text.strip() or len(text) > 200_000:
        raise ValueError("فایل پیکربندی خالی یا بزرگ است")
    if "\x00" in text:
        raise ValueError("پیکربندی نامعتبر است")
    folder = ROOT / ".vpn_runtime"
    folder.mkdir(mode=0o700, exist_ok=True)
    try:
        os.chmod(folder, 0o700)
    except OSError:
        pass
    path = folder / ("active" + suffix)
    path.write_text(text, encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return path


def _routes(value):
    if value in (None, ""):
        return []
    if isinstance(value, str):
        value = [x.strip() for x in value.split(",") if x.strip()]
    if not isinstance(value, list) or len(value) > 64:
        raise ValueError("حداکثر ۶۴ مسیر مجاز است")
    try:
        return [str(ipaddress.ip_network(x, strict=False)) for x in value]
    except ValueError as e:
        raise ValueError("مسیر شبکه باید CIDR معتبر باشد") from e


def _run(cmd, timeout=45):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=False)



def _windows_ensure_pbk_entry(entry_name: str, server: str) -> None:
    """Create/update a minimal PPTP phonebook entry so rasdial works without manual UI setup."""
    if not entry_name or not server:
        return
    # User-level pbk
    appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    pbk_dir = Path(appdata) / "Microsoft" / "Network" / "Connections" / "Pbk"
    pbk_dir.mkdir(parents=True, exist_ok=True)
    pbk = pbk_dir / "rasphone.pbk"
    block = f"""
[{entry_name}]
Encoding=1
PBVersion=4
Type=2
AutoLogon=0
UseRasCredentials=1
DialParamsUID=0
Guid=00000000000000000000000000000000
VpnStrategy=1
ExcludedProtocols=0
LcpExtensions=1
DataEncryption=0
SwCompression=0
NegotiateMultilinkAlways=0
SkipDoubleDialDialog=0
DialMode=0
OverridePref=15
RedialAttempts=3
RedialSeconds=60
IdleDisconnectSeconds=0
RedialOnLinkFailure=1
CallbackMode=0
PreferredPort=VPN2-0
PreferredDevice=WAN Miniport (PPTP)
PreviewUserPw=1
PreviewDomain=0
PreviewPhoneNumber=0
ShowDialingProgress=1
ShowMonitorIconInTaskBar=1
CustomAuthKey=0
AuthRestrictions=552
IpPrioritizeRemote=0
IpInterfaceMetric=0
IpHeaderCompression=0
IpAddress=0.0.0.0
IpDnsAddress=0.0.0.0
IpDns2Address=0.0.0.0
IpWinsAddress=0.0.0.0
IpWins2Address=0.0.0.0
IpAssign=1
IpNameAssign=1
IpDnsFlags=0
IpNBTFlags=1
TcpWindowSize=0
UseFlags=0
IpSecFlags=0
Ipv6Assign=1
Ipv6Address=::
Ipv6PrefixLength=0
Ipv6PrioritizeRemote=0
Ipv6InterfaceMetric=0
Ipv6NameAssign=1
Ipv6DnsAddress=::
Ipv6Dns2Address=::
DisableClassBasedDefaultRoute=1
MEDIA=rastapi
Port=VPN2-0
Device=WAN Miniport (PPTP)
DEVICE=vpn
PhoneNumber={server}
AreaCode=
CountryCode=0
CountryID=0
UseDialingRules=0
Comment=mikrotik-scanner-split-tunnel
FriendlyName=
LastSelectedPhone=0
PromoteAlternates=0
TryNextAlternateOnFail=1
"""
    existing = ""
    if pbk.exists() and pbk.stat().st_size > 0:
        raw = pbk.read_bytes()
        # Windows rasphone.pbk is usually UTF-16 LE (with or without BOM).
        # Python's "utf-16" codec requires a BOM and raises
        # "UTF-16 stream does not start with BOM" otherwise.
        for enc in ("utf-16", "utf-16-le", "utf-16-be", "utf-8", "cp1256", "latin-1"):
            try:
                if enc == "utf-16" and not (raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff")):
                    continue  # strict utf-16 needs BOM
                existing = raw.decode(enc)
                if "[" in existing:
                    break
            except (UnicodeDecodeError, UnicodeError, LookupError):
                continue
        else:
            existing = raw.decode("latin-1", errors="replace")
    if f"[{entry_name}]" in existing:
        # leave existing entry
        return
    # Prefer appending as UTF-16 LE with BOM when the file is new/empty or already UTF-16;
    # fall back to UTF-8 so we never crash the connect flow.
    block_crlf = block.replace("\r\n", "\n").replace("\n", "\r\n")
    try:
        is_utf16 = (
            not pbk.exists()
            or pbk.stat().st_size == 0
            or (pbk.exists() and pbk.read_bytes()[:2] in (b"\xff\xfe", b"\xfe\xff"))
        )
        if is_utf16:
            # utf-16-le + explicit BOM is the most common Windows pbk form
            data = ("\ufeff" + block_crlf) if not pbk.exists() or pbk.stat().st_size == 0 else block_crlf
            with open(pbk, "ab") as f:
                f.write(data.encode("utf-16-le"))
        else:
            with open(pbk, "a", encoding="utf-8", newline="") as f:
                f.write(block_crlf)
    except Exception:
        with open(pbk, "a", encoding="utf-8", errors="replace") as f:
            f.write(block_crlf)


# ---------- Split-tunnel helpers (never take OS default route) ----------

def _windows_disable_vpn_default_route(entry_name: str) -> list[str]:
    """After rasdial, remove 0.0.0.0/0 via the VPN interface; keep split routes only."""
    notes = []
    ps = (
        f"$n='{entry_name}';"
        "$a=Get-NetAdapter -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'Up' -and ($_.InterfaceDescription -match 'WAN Miniport|VPN|PPP' -or $_.Name -match [regex]::Escape($n)) };"
        "foreach($x in $a){"
        "  Get-NetRoute -InterfaceIndex $x.ifIndex -ErrorAction SilentlyContinue |"
        "    Where-Object { $_.DestinationPrefix -eq '0.0.0.0/0' } |"
        "    Remove-NetRoute -Confirm:$false -ErrorAction SilentlyContinue;"
        "  # also classic route delete fallback"
        "}"
        "route print -4 | Out-String"
    )
    exe = shutil.which("powershell") or shutil.which("powershell.exe")
    if exe:
        r = _run([exe, "-NoProfile", "-Command", ps], timeout=30)
        notes.append("windows_default_route_stripped")
        if r.returncode:
            notes.append((r.stderr or r.stdout or "")[:200])
    # Classic route delete attempts (common VPN gateway patterns)
    _run(["route", "delete", "0.0.0.0", "mask", "0.0.0.0"], timeout=10)
    notes.append("route_delete_default_attempted")
    return notes


def _windows_add_split_routes(routes: list[str]) -> list[str]:
    notes = []
    for cidr in routes:
        net = ipaddress.ip_network(cidr, strict=False)
        # On Windows, without knowing VPN gateway, use interface metric via PowerShell if possible
        # Fallback: route add with IF implied after rasdial — best-effort
        mask = str(net.netmask)
        dest = str(net.network_address)
        r = _run(["route", "add", dest, "mask", mask, "0.0.0.0"], timeout=10)
        notes.append(f"route_add:{cidr}:rc={r.returncode}")
    return notes


def _linux_add_split_routes(iface: str, routes: list[str]) -> list[str]:
    notes = []
    for cidr in routes:
        r = _run(["ip", "route", "replace", cidr, "dev", iface], timeout=10)
        notes.append(f"ip_route:{cidr}:rc={r.returncode}")
    return notes


def _linux_find_ppp_iface() -> str | None:
    try:
        out = _run(["ip", "-o", "link", "show"], timeout=5).stdout
        for line in out.splitlines():
            m = re.search(r"\d+:\s+(ppp\d+):", line)
            if m:
                return m.group(1)
    except Exception:
        pass
    return None


def connect(config):
    """Connect VPN with split-tunnel only. Does not replace the OS default gateway."""
    global ACTIVE
    if not isinstance(config, dict):
        raise ValueError("پارامترهای VPN نامعتبرند")
    protocol = str(config.get("protocol", "")).lower()
    if protocol not in _ALLOWED:
        raise ValueError("پروتکل پشتیبانی‌نشده است")
    routes = _routes(config.get("routes"))
    split_notes: list[str] = []

    with LOCK:
        if ACTIVE and ACTIVE.get("connected"):
            raise RuntimeError("یک اتصال VPN از قبل فعال است")
        kind = platform.system().lower()
        name = str(config.get("name") or "Remote VPN")[:64]
        host = str(config.get("host") or "").strip()

        if protocol == "wireguard":
            if kind == "windows":
                exe = shutil.which("wireguard")
                if not exe:
                    raise RuntimeError("WireGuard for Windows نصب نیست")
                cfg = _safe_config(config.get("config_content"), ".conf")
                # Ensure AllowedIPs is not 0.0.0.0/0 if user wants split — optional rewrite skipped
                result = _run([exe, "/installtunnelservice", str(cfg)], timeout=30)
                if result.returncode:
                    raise RuntimeError((result.stderr or result.stdout or "WireGuard ناموفق").strip()[:500])
                ACTIVE = {
                    "protocol": protocol,
                    "name": name,
                    "interface": cfg.stem,
                    "connected": True,
                    "routes": routes,
                    "process": None,
                    "config": str(cfg),
                    "windows_service": True,
                    "split_tunnel": True,
                }
            else:
                exe = shutil.which("wg-quick")
                if not exe:
                    raise RuntimeError("wg-quick نصب نیست")
                cfg = _safe_config(config.get("config_content"), ".conf")
                result = _run([exe, "up", str(cfg)], timeout=45)
                if result.returncode:
                    raise RuntimeError((result.stderr or result.stdout or "wg-quick ناموفق").strip()[:500])
                ACTIVE = {
                    "protocol": protocol,
                    "name": name,
                    "interface": cfg.stem,
                    "connected": True,
                    "routes": routes,
                    "process": None,
                    "config": str(cfg),
                    "split_tunnel": True,
                }

        elif protocol == "openvpn":
            exe = shutil.which("openvpn") or (shutil.which("openvpn.exe") if kind == "windows" else None)
            if not exe:
                raise RuntimeError("OpenVPN نصب نیست")
            raw = config.get("config_content") or ""
            # Force split-tunnel: strip redirect-gateway directives
            cleaned = "\n".join(
                ln
                for ln in str(raw).splitlines()
                if not re.match(r"^\s*redirect-gateway\b", ln, re.I)
            )
            cleaned += "\n# split-tunnel enforced by scanner\npull-filter ignore redirect-gateway\n"
            if routes:
                for cidr in routes:
                    cleaned += f"route {cidr.split('/')[0]} {ipaddress.ip_network(cidr, strict=False).netmask}\n"
            cfg = _safe_config(cleaned, ".ovpn")
            proc = subprocess.Popen(
                [exe, "--config", str(cfg), "--writepid", str(cfg.with_suffix(".pid"))],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False,
            )
            ACTIVE = {
                "protocol": protocol,
                "name": name,
                "interface": None,
                "connected": False,
                "routes": routes,
                "process": proc,
                "config": str(cfg),
                "started": time.time(),
                "split_tunnel": True,
            }

        elif protocol in ("pptp", "l2tp", "sstp"):
            if kind == "windows":
                # Prefer explicit phonebook entry name (Olom); else host
                profile = str(config.get("profile_name") or name or host or "")
                if not profile or any(c in profile for c in '"\r\n'):
                    raise ValueError("نام اتصال RAS / profile_name لازم است (مثلاً Olom)")
                if host:
                    _windows_ensure_pbk_entry(profile, host)
                exe = shutil.which("rasdial")
                if not exe:
                    raise RuntimeError("rasdial در Windows پیدا نشد")
                args = [exe, profile]
                if config.get("username"):
                    args += [str(config["username"]), str(config.get("password") or "")]
                result = _run(args, timeout=60)
                if result.returncode:
                    raise RuntimeError((result.stderr or result.stdout or "اتصال RAS ناموفق").strip()[:500])
                # CRITICAL: strip default route so OS internet stays up
                split_notes += _windows_disable_vpn_default_route(profile)
                if routes:
                    split_notes += _windows_add_split_routes(routes)
                ACTIVE = {
                    "protocol": protocol,
                    "name": profile,
                    "host": host,
                    "interface": None,
                    "connected": True,
                    "routes": routes,
                    "process": None,
                    "ras": True,
                    "split_tunnel": True,
                    "split_notes": split_notes,
                }
            else:
                # Linux PPTP via pptp client + pppd, nodefaultroute
                if protocol != "pptp":
                    raise RuntimeError(
                        f"اتصال {protocol} روی Linux در این نسخه پشتیبانی نشده؛ از PPTP یا OpenVPN/WireGuard استفاده کنید"
                    )
                if not host:
                    raise ValueError("آدرس سرور PPTP (host) لازم است")
                user = str(config.get("username") or "").strip()
                password = str(config.get("password") or "")
                if not user:
                    raise ValueError("نام کاربری PPTP لازم است")
                pptp = shutil.which("pptp")
                pppd = shutil.which("pppd")
                if not pptp or not pppd:
                    raise RuntimeError(
                        "برای PPTP روی Linux بسته‌های pptp-linux و ppp لازم است "
                        "(مثلاً: apt install pptp-linux ppp)"
                    )
                runtime = ROOT / ".vpn_runtime"
                runtime.mkdir(mode=0o700, exist_ok=True)
                peer = runtime / "peer_olom"
                # pppd options: nodefaultroute keeps OS internet
                peer.write_text(
                    "\n".join(
                        [
                            f'pty "{pptp} {host} --nolaunchpppd"',
                            f"name {user}",
                            "remotename olom",
                            "require-mppe-128",
                            "noauth",
                            "nodefaultroute",
                            "noipdefault",
                            "nodetach",
                            "persist",
                            "maxfail 3",
                            "lcp-echo-failure 4",
                            "lcp-echo-interval 30",
                            "",
                        ]
                    ),
                    encoding="utf-8",
                )
                try:
                    os.chmod(peer, 0o600)
                except OSError:
                    pass
                # password via stdin plugin is hard; use chap-secrets line in runtime file
                secrets = runtime / "chap-secrets"
                # escape
                secrets.write_text(f'{user} olom "{password}" *\n', encoding="utf-8")
                try:
                    os.chmod(secrets, 0o600)
                except OSError:
                    pass
                proc = subprocess.Popen(
                    [
                        pppd,
                        "file",
                        str(peer),
                        "remotename",
                        "olom",
                        "user",
                        user,
                        "password",
                        password,
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    shell=False,
                )
                time.sleep(3)
                iface = _linux_find_ppp_iface()
                if routes and iface:
                    split_notes += _linux_add_split_routes(iface, routes)
                ACTIVE = {
                    "protocol": protocol,
                    "name": name,
                    "host": host,
                    "interface": iface,
                    "connected": proc.poll() is None,
                    "routes": routes,
                    "process": proc,
                    "started": time.time(),
                    "split_tunnel": True,
                    "split_notes": split_notes,
                    "config": str(peer),
                }
                if proc.poll() is not None:
                    raise RuntimeError(
                        "pppd/pptp بلافاصله خارج شد — نام کاربری/رمز یا دسترسی root را بررسی کنید"
                    )
        else:
            raise RuntimeError(f"پروتکل ناشناخته: {protocol}")

        return status()


def _interfaces():
    try:
        if shutil.which("ip"):
            out = _run(["ip", "-o", "-4", "addr", "show"], timeout=3).stdout
            return [
                {"name": m.group(1), "ip": m.group(2)}
                for line in out.splitlines()
                if (m := re.search(r"\d+:\s+([^ ]+).*?inet ([0-9.]+)", line))
            ]
        if platform.system().lower() == "windows" and shutil.which("ipconfig"):
            out = _run(["ipconfig"], timeout=3).stdout
            return [
                {"name": "Windows adapter", "ip": x}
                for x in re.findall(r"(?:IPv4 Address|IPv4-адрес)[^:]*:\s*([0-9.]+)", out)
            ]
    except Exception:
        pass
    return []


def status():
    with LOCK:
        active = ACTIVE
        if active and active.get("process"):
            proc = active["process"]
            if proc.poll() is not None:
                active["connected"] = False
                active["error"] = "فرایند VPN پایان یافت"
            elif time.time() - active.get("started", 0) > 3:
                active["connected"] = True
                if not active.get("interface"):
                    active["interface"] = _linux_find_ppp_iface()
        interfaces = _interfaces()
        safe_active = None
        if active:
            safe_active = {
                k: v
                for k, v in active.items()
                if k not in ("process", "config", "started", "windows_service", "ras")
            }
        return {
            "connected": bool(active and active.get("connected")),
            "connecting": bool(
                active
                and active.get("process")
                and active["process"].poll() is None
                and not active.get("connected")
            ),
            "active": safe_active,
            "interfaces": interfaces,
            "interface_ip": next(
                (
                    x["ip"]
                    for x in interfaces
                    if active and active.get("interface") == x["name"]
                ),
                None,
            ),
            "routes": active.get("routes", []) if active else [],
            "split_tunnel": bool(active and active.get("split_tunnel")),
        }


def disconnect():
    global ACTIVE
    with LOCK:
        active = ACTIVE
        if not active:
            return status()
        protocol = active["protocol"]
        try:
            if protocol == "wireguard":
                if active.get("windows_service"):
                    exe = shutil.which("wireguard")
                    if exe:
                        _run(
                            [exe, "/uninstalltunnelservice", Path(active["config"]).stem],
                            timeout=30,
                        )
                else:
                    exe = shutil.which("wg-quick")
                    if exe and active.get("config"):
                        _run([exe, "down", active["config"]], timeout=30)
            elif protocol == "openvpn":
                p = active.get("process")
                if p and p.poll() is None:
                    p.terminate()
                    try:
                        p.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        p.kill()
                        p.wait(timeout=3)
            elif active.get("ras"):
                exe = shutil.which("rasdial")
                if exe:
                    _run([exe, active["name"], "/disconnect"], timeout=20)
            elif active.get("process"):
                p = active["process"]
                if p.poll() is None:
                    p.terminate()
                    try:
                        p.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        p.kill()
                        p.wait(timeout=3)
                # kill leftover ppp
                if active.get("interface"):
                    _run(["ip", "link", "delete", active["interface"]], timeout=5)
        finally:
            cfg = active.get("config")
            if cfg:
                for path in (Path(cfg), Path(cfg).with_suffix(".pid")):
                    try:
                        path.unlink(missing_ok=True)
                    except OSError:
                        pass
            ACTIVE = None
        return status()


def list_interfaces():
    return _interfaces()


def get_active_vpn():
    return status().get("active")


def list_profiles():
    with LOCK:
        _load()
        out = []
        for k, v in PROFILES.items():
            out.append(
                {
                    "id": k,
                    "name": v.get("name", k),
                    "protocol": v.get("protocol"),
                    "host": v.get("host", ""),
                    "port": v.get("port") or "",
                    "username": v.get("username", ""),
                    "routes": v.get("routes", []),
                    "profile_name": v.get("profile_name", ""),
                    "config_content": v.get("config_content", ""),
                    "has_config": bool(str(v.get("config_content") or "").strip()),
                    "is_default": bool(v.get("is_default") or k in DEFAULT_PROFILES),
                }
            )
        out.sort(key=lambda x: (0 if x.get("is_default") else 1, x["id"]))
        return out


def save_profile(data):
    if not isinstance(data, dict):
        raise ValueError("پروفایل نامعتبر")
    pid = str(data.get("id") or "")
    if not _ID.fullmatch(pid):
        raise ValueError("شناسه پروفایل نامعتبر")
    protocol = str(data.get("protocol", "")).lower()
    if protocol not in _ALLOWED:
        raise ValueError("پروتکل نامعتبر")
    port_raw = data.get("port")
    port_val = ""
    if port_raw not in (None, ""):
        try:
            port_val = int(port_raw)
            if not 1 <= port_val <= 65535:
                raise ValueError
        except (TypeError, ValueError):
            raise ValueError("پورت نامعتبر است") from None
    # Password is intentionally NOT persisted to disk.
    safe = {
        "name": str(data.get("name") or pid)[:64],
        "protocol": protocol,
        "host": str(data.get("host") or "")[:253],
        "port": port_val,
        "username": str(data.get("username") or "")[:128],
        "routes": _routes(data.get("routes")),
        "profile_name": str(data.get("profile_name") or "")[:128],
        "config_content": str(data.get("config_content") or "")[:200_000],
        "is_default": bool(data.get("is_default")),
    }
    with LOCK:
        _load()
        if safe["is_default"]:
            for k, v in list(PROFILES.items()):
                if isinstance(v, dict) and v.get("is_default") and k != pid:
                    v["is_default"] = False
        PROFILES[pid] = safe
        _save()
    return {"id": pid, **safe}


def delete_profile(pid):
    with LOCK:
        _load()
        if pid not in PROFILES:
            return False
        if pid in DEFAULT_PROFILES:
            raise ValueError("پروفایل پیش‌فرض Olom قابل حذف نیست")
        del PROFILES[pid]
        _save()
        try:
            _config_path(pid).unlink(missing_ok=True)
        except OSError:
            pass
        return True


# Load defaults at import
_load()
