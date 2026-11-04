"""SMTP configuration and outbound mail for شبکه‌بان.

Two transport modes:
  - direct : resolve recipient MX and deliver directly — fully standalone,
             no Gmail/Yahoo account, only internet + outbound TCP 25/587
  - relay  : classic SMTP through a provider (host mail, VPS, Gmail, Yahoo, …)

Direct mode DNS strategy: local system resolvers first (resolv.conf), then
public NS, then `nslookup` subprocess, then A-record fallback (RFC 5321 §5.1).
UDP answers with TC flag are retried over TCP.
"""
from __future__ import annotations

import base64
import hashlib
import ipaddress
import json
import math
import os
import random
import re
import secrets
import smtplib
import socket
import ssl
import struct
import time
from concurrent.futures import ThreadPoolExecutor
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
_CONFIG = _ROOT / "smtp_config.json"

DEFAULTS: dict[str, Any] = {
    "enabled": False,
    "mode": "direct",  # "direct" | "relay"
    "host": "smtp.gmail.com",
    "port": 587,
    "use_tls": True,
    "use_ssl": False,
    "username": "",
    "password": "",
    "from_email": "",
    "from_name": "شبکه‌بان",
    "to_email": "",
    "timeout": 30,
    "helo_host": "",  # خالی = تشخیص خودکار (address literal [IP])
    # احراز هویت دامنه (پاسخ خطای 5.7.26 جیمیل): امضای DKIM با کلید دامنهٔ خودتان
    "dkim_enabled": False,
    "dkim_selector": "shabakeban",
    "dkim_domain": "",     # خالی = دامنهٔ فرستنده (From)
    "dkim_private_key": "",  # PKCS#8 PEM — هرگز به سمت کلاینت برنمی‌گردد
}


def _load_raw() -> dict:
    try:
        data = json.loads(_CONFIG.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {}


def _write_config(cfg: dict) -> None:
    """Atomic write (tmp + os.replace) — a crash can't corrupt smtp_config.json."""
    tmp = _CONFIG.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, _CONFIG)


def get_config(mask_password: bool = True) -> dict:
    cfg = {**DEFAULTS, **_load_raw()}
    try:
        cfg["port"] = int(cfg.get("port") or 587)
    except (TypeError, ValueError):
        cfg["port"] = 587
    try:
        cfg["timeout"] = float(cfg.get("timeout") or 30)
    except (TypeError, ValueError):
        cfg["timeout"] = 30.0
    cfg["enabled"] = bool(cfg.get("enabled"))
    cfg["use_tls"] = bool(cfg.get("use_tls", True))
    cfg["use_ssl"] = bool(cfg.get("use_ssl", False))
    mode = str(cfg.get("mode") or "direct").lower().strip()
    cfg["mode"] = mode if mode in ("direct", "relay") else "direct"
    for k in ("host", "username", "password", "from_email", "from_name", "to_email", "helo_host",
              "dkim_selector", "dkim_domain"):
        cfg[k] = str(cfg.get(k) or "")
    cfg["dkim_enabled"] = bool(cfg.get("dkim_enabled"))
    if mask_password and cfg.get("password"):
        cfg["password"] = "********"
        cfg["password_set"] = True
    else:
        cfg["password_set"] = bool(_load_raw().get("password"))
    if mask_password and cfg.get("dkim_private_key"):
        cfg["dkim_private_key"] = "********"
        cfg["dkim_key_set"] = True
    else:
        cfg["dkim_private_key"] = ""
        cfg["dkim_key_set"] = bool(_load_raw().get("dkim_private_key"))
    return cfg


def save_config(body: dict) -> dict:
    current = {**DEFAULTS, **_load_raw()}
    for key in DEFAULTS:
        if key not in body:
            continue
        val = body[key]
        if key == "password":
            if val is None or str(val) == "********":
                continue  # ماسک‌شده → رمز فعلی حفظ می‌شود
            current["password"] = str(val).strip()  # رشتهٔ خالی = پاک کردن رمز
            continue
        if key == "dkim_private_key":
            if val is None or str(val) == "********":
                continue  # ماسک‌شده → کلید فعلی حفظ می‌شود
            current["dkim_private_key"] = str(val).strip()  # خالی = پاک کردن کلید
            continue
        if key == "port":
            try:
                current[key] = int(val)
            except (TypeError, ValueError):
                raise ValueError("پورت نامعتبر است") from None
        elif key == "timeout":
            try:
                current[key] = float(val)
            except (TypeError, ValueError):
                raise ValueError("timeout نامعتبر است") from None
        elif key in ("enabled", "use_tls", "use_ssl", "dkim_enabled"):
            current[key] = bool(val)
        elif key == "mode":
            m = str(val or "direct").lower().strip()
            if m not in ("direct", "relay"):
                raise ValueError("mode باید direct یا relay باشد")
            current[key] = m
        else:
            current[key] = str(val or "").strip()
    if not current.get("from_email") and current.get("username"):
        current["from_email"] = current["username"]
    if current.get("from_email") and not _looks_like_email(current["from_email"]):
        raise ValueError(
            "فرستنده (From) باید ایمیل معتبر باشد — مثال: alerts@your-domain.ir؛ "
            "متن آزاد مثل «ali pedram» قابل قبول نیست"
        )
    if current.get("to_email") and not _looks_like_email(current["to_email"]):
        raise ValueError("گیرندهٔ پیش‌فرض باید ایمیل معتبر باشد")
    _write_config(current)
    return get_config(mask_password=True)


def _plain_config() -> dict:
    return {**DEFAULTS, **_load_raw()}


def _looks_like_email(s: str) -> bool:
    s = (s or "").strip()
    return bool(s) and "@" in s and "." in s.split("@")[-1] and " " not in s


# ---------------------------------------------------------------------------
# Minimal DNS MX lookup (stdlib only — UDP/53 + TCP/53 fallback)
# ---------------------------------------------------------------------------
def _decode_dns_name(buf: bytes, offset: int) -> tuple[str, int]:
    parts: list[str] = []
    jumped = False
    end = offset
    for _ in range(64):
        if offset >= len(buf):
            break
        length = buf[offset]
        if length == 0:
            if not jumped:
                end = offset + 1
            break
        if (length & 0xC0) == 0xC0:
            if offset + 1 >= len(buf):
                break
            pointer = ((length & 0x3F) << 8) | buf[offset + 1]
            if not jumped:
                end = offset + 2
            offset = pointer
            jumped = True
            continue
        offset += 1
        parts.append(buf[offset : offset + length].decode("ascii", "ignore"))
        offset += length
        if not jumped:
            end = offset
    return ".".join(parts), end


def _parse_dns_mx_response(data: bytes, tid: int) -> tuple[list[tuple[int, str]], bool]:
    """Parse a DNS response; returns (mx_records, truncated_flag)."""
    if len(data) < 12:
        return [], False
    rtid, flags, _qd, an, _, _ = struct.unpack("!HHHHHH", data[:12])
    tc = bool(flags & 0x0200)  # truncated
    if rtid != tid or (flags & 0x000F) != 0 or an == 0:
        return [], tc
    pos = 12
    _, pos = _decode_dns_name(data, pos)
    pos += 4  # qtype + qclass
    results: list[tuple[int, str]] = []
    for _ in range(an):
        _, pos = _decode_dns_name(data, pos)
        if pos + 10 > len(data):
            break
        rtype, _rclass, _ttl, rdlen = struct.unpack("!HHIH", data[pos : pos + 10])
        pos += 10
        if pos + rdlen > len(data):
            break
        if rtype == 15 and rdlen >= 3:
            pref = struct.unpack("!H", data[pos : pos + 2])[0]
            name, _ = _decode_dns_name(data, pos + 2)
            if name:
                results.append((pref, name.rstrip(".")))
        pos += rdlen
    results.sort(key=lambda x: x[0])
    return results, tc


def _dns_packet(domain: str) -> tuple[bytes, int]:
    labels = domain.strip(".").split(".")
    qname = b"".join(bytes([len(l)]) + l.encode("ascii", "ignore") for l in labels) + b"\x00"
    tid = random.randint(0, 65535)
    header = struct.pack("!HHHHHH", tid, 0x0100, 1, 0, 0, 0)
    return header + qname + struct.pack("!HH", 15, 1), tid  # MX IN


def _dns_query_mx_udp(domain: str, nameserver: str, timeout: float) -> tuple[list[tuple[int, str]], bool]:
    packet, tid = _dns_packet(domain)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(packet, (nameserver, 53))
        data, _ = sock.recvfrom(4096)
    finally:
        sock.close()
    return _parse_dns_mx_response(data, tid)


def _dns_query_mx_tcp(domain: str, nameserver: str, timeout: float) -> list[tuple[int, str]]:
    packet, tid = _dns_packet(domain)
    with socket.create_connection((nameserver, 53), timeout=timeout) as s:
        s.settimeout(timeout)
        s.sendall(struct.pack("!H", len(packet)) + packet)
        hdr = b""
        while len(hdr) < 2:
            chunk = s.recv(2 - len(hdr))
            if not chunk:
                return []
            hdr += chunk
        (ln,) = struct.unpack("!H", hdr)
        data = b""
        while len(data) < ln:
            chunk = s.recv(min(4096, ln - len(data)))
            if not chunk:
                break
            data += chunk
    recs, _tc = _parse_dns_mx_response(data, tid)
    return recs


def _dns_query_mx(domain: str, nameserver: str, timeout: float = 5.0) -> list[tuple[int, str]]:
    """UDP first; on truncation or network error retry over TCP."""
    try:
        recs, tc = _dns_query_mx_udp(domain, nameserver, timeout)
        if recs or not tc:
            return recs
    except OSError:
        pass
    try:
        return _dns_query_mx_tcp(domain, nameserver, timeout)
    except OSError:
        return []


def _system_nameservers() -> list[str]:
    """Local resolver IPs from /etc/resolv.conf (Linux/macOS); empty elsewhere."""
    ns: list[str] = []
    try:
        text = Path("/etc/resolv.conf").read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("nameserver"):
                parts = line.split()
                if len(parts) >= 2:
                    ns.append(parts[1])
    except OSError:
        pass
    return ns[:4]


def _nslookup_mx(domain: str) -> list[tuple[int, str]]:
    """Last-resort MX lookup via the `nslookup` tool (always present on Windows)."""
    import re
    import shutil
    import subprocess

    if shutil.which("nslookup") is None:
        return []
    try:
        out = subprocess.run(
            ["nslookup", "-type=mx", domain],
            capture_output=True, timeout=10, text=True,
        ).stdout or ""
    except Exception:
        return []
    found: list[tuple[int, str]] = []
    for m in re.finditer(r"mail\s*exchanger\s*=\s*(\d+)\s*([A-Za-z0-9._\-]+)", out):
        found.append((int(m.group(1)), m.group(2).rstrip(".")))
    found.sort(key=lambda x: x[0])
    return found


def resolve_mx_full(domain: str, timeout: float = 5.0) -> list[tuple[int, str]]:
    """Resolve (preference, host) MX pairs; A-record fallback per RFC 5321 §5.1."""
    domain = domain.strip().strip(".").lower()
    if not domain or "." not in domain:
        return []
    ns_list: list[str] = []
    for ns in _system_nameservers() + ["8.8.8.8", "1.1.1.1", "9.9.9.9"]:
        if ns not in ns_list:
            ns_list.append(ns)
    qto = max(1.0, min(timeout, 3.0))  # هر پرس‌وجو حداکثر ۳ ثانیه تا مجموع زنجیرهٔ DNS هنگ نکند
    for ns in ns_list:
        try:
            mx = _dns_query_mx(domain, nameserver=ns, timeout=qto)
            if mx:
                return mx
        except OSError:
            continue
    mx = _nslookup_mx(domain)
    if mx:
        return mx
    try:
        infos = socket.getaddrinfo(domain, 25, socket.AF_INET, socket.SOCK_STREAM)
        if infos:
            return [(0, domain)]
    except socket.gaierror:
        pass
    return []


def resolve_mx(domain: str, timeout: float = 5.0) -> list[str]:
    """Resolve MX hostnames for a domain (empty list if none found)."""
    return [h for _, h in resolve_mx_full(domain, timeout=timeout)]


# ---------------------------------------------------------------------------
# Generic DNS queries: TXT (SPF/DKIM/DMARC), PTR (rDNS), A — stdlib only
# ---------------------------------------------------------------------------
def _dns_packet_q(domain: str, qtype: int) -> tuple[bytes, int]:
    labels = domain.strip(".").split(".")
    qname = b"".join(bytes([len(l)]) + l.encode("ascii", "ignore") for l in labels) + b"\x00"
    tid = random.randint(0, 65535)
    header = struct.pack("!HHHHHH", tid, 0x0100, 1, 0, 0, 0)
    return header + qname + struct.pack("!HH", qtype, 1), tid


def _parse_dns_records(data: bytes, tid: int) -> list[tuple[int, str]]:
    """Parse answers of any supported rtype; returns [(rtype, rdata_text), …]."""
    if len(data) < 12:
        return []
    rtid, flags, _qd, an, _ns, _ar = struct.unpack("!HHHHHH", data[:12])
    if rtid != tid or (flags & 0x000F) != 0 or an == 0:
        return []
    pos = 12
    _, pos = _decode_dns_name(data, pos)
    pos += 4  # qtype + qclass
    out: list[tuple[int, str]] = []
    for _ in range(an):
        _, pos = _decode_dns_name(data, pos)
        if pos + 10 > len(data):
            break
        rtype, _rclass, _ttl, rdlen = struct.unpack("!HHIH", data[pos:pos + 10])
        pos += 10
        rd = data[pos:pos + rdlen]
        try:
            if rtype == 16:  # TXT: رشته‌های طول-پیشوندی که باید به هم بچسبند
                i, chunks = 0, []
                while i < len(rd):
                    ln = rd[i]
                    chunks.append(rd[i + 1:i + 1 + ln])
                    i += 1 + ln
                out.append((16, b"".join(chunks).decode("ascii", "ignore")))
            elif rtype == 12:  # PTR (قابل فشرده‌سازی)
                name, _ = _decode_dns_name(data, pos)
                out.append((12, name.rstrip(".")))
            elif rtype == 1 and len(rd) == 4:  # A
                out.append((1, ".".join(str(b) for b in rd)))
        except Exception:
            pass
        pos += rdlen
    return out


def _dns_query_udp_q(domain: str, qtype: int, nameserver: str, timeout: float) -> list[tuple[int, str]]:
    packet, tid = _dns_packet_q(domain, qtype)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(packet, (nameserver, 53))
        data, _ = sock.recvfrom(8192)
    finally:
        sock.close()
    return _parse_dns_records(data, tid)


def _dns_query_tcp_q(domain: str, qtype: int, nameserver: str, timeout: float) -> list[tuple[int, str]]:
    packet, tid = _dns_packet_q(domain, qtype)
    with socket.create_connection((nameserver, 53), timeout=timeout) as s:
        s.settimeout(timeout)
        s.sendall(struct.pack("!H", len(packet)) + packet)
        hdr = b""
        while len(hdr) < 2:
            chunk = s.recv(2 - len(hdr))
            if not chunk:
                return []
            hdr += chunk
        (ln,) = struct.unpack("!H", hdr)
        data = b""
        while len(data) < ln:
            chunk = s.recv(min(8192, ln - len(data)))
            if not chunk:
                break
            data += chunk
    return _parse_dns_records(data, tid)


def _dns_query_any(domain: str, qtype: int, timeout: float = 3.0) -> list[tuple[int, str]]:
    """NS chain (system + public) with UDP→TCP fallback per nameserver."""
    domain = domain.strip().strip(".").lower()
    if not domain or "." not in domain:
        return []
    qto = max(1.0, min(timeout, 3.0))  # سقف هر پرس‌وجو تا زنجیره هنگ نکند
    ns_list: list[str] = []
    for ns in _system_nameservers() + ["8.8.8.8", "1.1.1.1", "9.9.9.9"]:
        if ns not in ns_list:
            ns_list.append(ns)
    for ns in ns_list:
        try:
            recs = _dns_query_udp_q(domain, qtype, ns, qto)
            if recs:
                return recs
        except OSError:
            pass
        try:
            recs = _dns_query_tcp_q(domain, qtype, ns, qto)
            if recs:
                return recs
        except OSError:
            continue
    return []


def resolve_txt(name: str, timeout: float = 3.0) -> list[str]:
    """TXT records of a DNS name (SPF / DKIM / DMARC)."""
    return [v for t, v in _dns_query_any(name, 16, timeout) if t == 16 and v]


def resolve_ptr(ip: str, timeout: float = 3.0) -> list[str]:
    """Reverse-DNS (PTR) names for an IPv4 address."""
    name = ".".join(reversed(ip.split("."))) + ".in-addr.arpa"
    return [v for t, v in _dns_query_any(name, 12, timeout) if t == 12 and v]


def resolve_a(name: str, timeout: float = 3.0) -> list[str]:
    """IPv4 addresses of a DNS name."""
    return [v for t, v in _dns_query_any(name, 1, timeout) if t == 1 and v]


def _looks_like_ipv4(s: str) -> bool:
    parts = (s or "").split(".")
    return len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)


def _public_ip(timeout: float = 5.0) -> tuple[str | None, str]:
    """Public egress IPv4 via HTTPS echo services; returns (ip, provider) or (None, '')."""
    import urllib.request
    for url in ("https://api.ipify.org", "https://ifconfig.me/ip", "https://checkip.amazonaws.com"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "shabakeban-mailcheck/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                ip = resp.read(64).decode("ascii", "ignore").strip()
            if _looks_like_ipv4(ip):
                return ip, url
        except Exception:
            continue
    return None, ""


# ---------------------------------------------------------------------------
# DKIM (RFC 6376) — fully stdlib: ASN.1/DER + RSA keygen + RSA-SHA256 signing
# هیچ وابستگی جدیدی لازم نیست؛ با هر verifier سازگار است (تست با dkimpy انجام شده)
# ---------------------------------------------------------------------------
_RSA_OID_BYTES = bytes.fromhex("06092a864886f70d010101")  # 1.2.840.113549.1.1.1
_SHA256_DIGESTINFO = bytes.fromhex("3031300d060960864801650304020105000420")


def _der_len(n: int) -> bytes:
    if n < 0x80:
        return bytes([n])
    b = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(b)]) + b


def _der_tlv(tag: int, payload: bytes) -> bytes:
    return bytes([tag]) + _der_len(len(payload)) + payload


def _der_int(v: int) -> bytes:
    if v == 0:
        return _der_tlv(0x02, b"\x00")
    b = v.to_bytes((v.bit_length() + 7) // 8, "big")
    if b[0] & 0x80:
        b = b"\x00" + b
    return _der_tlv(0x02, b)


def _der_seq(*parts: bytes) -> bytes:
    return _der_tlv(0x30, b"".join(parts))


def _der_bitstring(data: bytes) -> bytes:
    return _der_tlv(0x03, b"\x00" + data)


def _der_read_tlv(data: bytes, pos: int) -> tuple[int, bytes, int]:
    tag = data[pos]
    pos += 1
    ln = data[pos]
    pos += 1
    if ln & 0x80:
        nbytes = ln & 0x7F
        ln = int.from_bytes(data[pos:pos + nbytes], "big")
        pos += nbytes
    return tag, data[pos:pos + ln], pos + ln


def _modinv(a: int, m: int) -> int:
    r0, r1, s0, s1 = a % m, m, 1, 0
    while r1:
        q = r0 // r1
        r0, r1 = r1, r0 - q * r1
        s0, s1 = s1, s0 - q * s1
    if r0 != 1:
        raise ValueError("وارون پودولار پیدا نشد")
    return s0 % m


def _is_probable_prime(n: int, rounds: int = 40) -> bool:
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for _ in range(rounds):
        a = 2 + secrets.randbelow(n - 3)
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True


def _gen_prime(bits: int) -> int:
    while True:
        c = secrets.randbits(bits) | (1 << (bits - 1)) | (1 << (bits - 2)) | 1
        if _is_probable_prime(c):
            return c


def _generate_rsa_keypair(bits: int = 2048) -> dict:
    """RSA keypair via Miller-Rabin — چند ثانیه طول می‌کشد (فقط هنگام تولید کلید)."""
    e = 65537
    half = bits // 2
    for _ in range(1000):
        p, q = _gen_prime(half), _gen_prime(half)
        if p == q:
            continue
        n = p * q
        if n.bit_length() != bits:
            continue
        phi = (p - 1) * (q - 1)
        if math.gcd(e, phi) != 1:
            continue
        d = _modinv(e, phi)
        return {
            "n": n, "e": e, "d": d, "p": p, "q": q,
            "dp": d % (p - 1), "dq": d % (q - 1),
            "qinv": _modinv(q, p),
        }
    raise RuntimeError("تولید کلید RSA ناموفق بود")


def _pem_encode(label: str, der: bytes) -> str:
    b64 = base64.b64encode(der).decode("ascii")
    lines = "\n".join(b64[i:i + 64] for i in range(0, len(b64), 64))
    return f"-----BEGIN {label}-----\n{lines}\n-----END {label}-----\n"


def _pem_decode(pem: str) -> bytes:
    body = [l.strip() for l in (pem or "").strip().splitlines()
            if l.strip() and not l.strip().startswith("-----")]
    return base64.b64decode("".join(body).replace(" ", ""))


def _parse_pkcs1(der: bytes) -> dict:
    tag, body, _ = _der_read_tlv(der, 0)
    if tag != 0x30:
        raise ValueError("ساختار PKCS#1 نامعتبر است")
    t, _ver, pos = _der_read_tlv(body, 0)
    if t != 0x02:
        raise ValueError("ساختار PKCS#1 نامعتبر است")
    vals: list[int] = []
    for _ in range(8):
        t, v, pos = _der_read_tlv(body, pos)
        if t != 0x02:
            raise ValueError("ساختار PKCS#1 نامعتبر است")
        vals.append(int.from_bytes(v, "big"))
    return {"n": vals[0], "e": vals[1], "d": vals[2]}


def _parse_rsa_private_pem(pem: str) -> dict:
    """PKCS#8 («PRIVATE KEY») یا PKCS#1 («RSA PRIVATE KEY») → {n, e, d}."""
    der = _pem_decode(pem)
    tag, body, _ = _der_read_tlv(der, 0)
    if tag != 0x30:
        raise ValueError("کلید خصوصی قابل خواندن نیست")
    t_ver, _v, pos = _der_read_tlv(body, 0)
    if t_ver != 0x02:
        raise ValueError("کلید خصوصی قابل خواندن نیست")
    t_next, _, _ = _der_read_tlv(body, pos)  # peek: PKCS#8 → AlgorithmIdentifier(SEQUENCE)
    if t_next == 0x30:
        _t, _alg, pos2 = _der_read_tlv(body, pos)
        t3, inner, _ = _der_read_tlv(body, pos2)
        if t3 != 0x04:
            raise ValueError("ساختار PKCS#8 نامعتبر است")
        return _parse_pkcs1(inner)
    return _parse_pkcs1(der)


def _spki_der(n: int, e: int) -> bytes:
    """SubjectPublicKeyInfo DER — همان مقداری که در تگ p= رکورد DKIM می‌رود."""
    algid = _der_tlv(0x30, _RSA_OID_BYTES + _der_tlv(0x05, b""))
    return _der_seq(algid, _der_bitstring(_der_seq(_der_int(n), _der_int(e))))


def _pkcs8_der(k: dict) -> bytes:
    pkcs1 = _der_seq(
        _der_int(0), _der_int(k["n"]), _der_int(k["e"]), _der_int(k["d"]),
        _der_int(k["p"]), _der_int(k["q"]), _der_int(k["dp"]), _der_int(k["dq"]),
        _der_int(k["qinv"]),
    )
    algid = _der_tlv(0x30, _RSA_OID_BYTES + _der_tlv(0x05, b""))
    return _der_seq(_der_int(0), algid, _der_tlv(0x04, pkcs1))


def _rsa_sign_pkcs1v15_sha256(k: dict, data: bytes) -> bytes:
    digest = hashlib.sha256(data).digest()
    klen = (k["n"].bit_length() + 7) // 8
    t = _SHA256_DIGESTINFO + digest
    if klen < len(t) + 11:
        raise ValueError("کلید برای امضا کوچک است")
    em = b"\x00\x01" + b"\xff" * (klen - len(t) - 3) + b"\x00" + t
    s = pow(int.from_bytes(em, "big"), k["d"], k["n"])
    return s.to_bytes(klen, "big")


_DKIM_HEADERS = ("from", "to", "subject", "date", "message-id",
                 "mime-version", "content-type", "content-transfer-encoding",
                 "reply-to", "return-path", "list-unsubscribe")


def _canon_body_relaxed(body: bytes) -> bytes:
    lines = [re.sub(rb"[ \t]+", b" ", ln).rstrip(b" \t") for ln in body.split(b"\r\n")]
    while lines and lines[-1] == b"":
        lines.pop()
    if not lines:
        return b""
    return b"\r\n".join(lines) + b"\r\n"


def _canon_header_relaxed(name_b: bytes, value_b: bytes) -> bytes:
    v = re.sub(rb"[\r\n\t ]+", b" ", value_b).strip(b" \t")
    return name_b.strip(b" \t").lower() + b":" + v


def _dkim_sign_message(msg: EmailMessage, domain: str, selector: str, key: dict) -> str:
    """DKIM-Signature value (relaxed/relaxed, rsa-sha256) over the exact wire bytes.

    سیمِ بایت‌ها باید دقیقاً همان باشد که smtplib می‌فرستد؛ SMTP.send_message با
    linesep='\r\n' فلت می‌کند (منبع smtplib) — همین‌جا هم همان policy استفاده می‌شود.
    """
    wire = msg.as_bytes(policy=msg.policy.clone(linesep="\r\n"))
    sep = wire.find(b"\r\n\r\n")
    header_block, body = (wire, b"") if sep == -1 else (wire[:sep], wire[sep + 4:])
    headers: list[tuple[bytes, bytes]] = []
    for line in header_block.split(b"\r\n"):
        if line[:1] in (b" ", b"\t") and headers:
            n, v = headers[-1]
            headers[-1] = (n, v + b"\r\n" + line)  # حفظ فولدینگ برای کنونیکال‌سازی دقیق
        elif b":" in line:
            n, v = line.split(b":", 1)
            headers.append((n, v))
    allow = set(_DKIM_HEADERS)
    selected: list[tuple[bytes, bytes]] = []
    sel_names: list[str] = []
    for n, v in headers:  # به ترتیبِ ظاهر شدن در پیام (الزام RFC برای هر verifier)
        name = n.strip(b" \t").lower().decode("ascii", "ignore")
        if name in allow:
            selected.append((n, v))
            sel_names.append(name)
    if "from" not in sel_names:
        raise ValueError("هدر From برای امضای DKIM پیدا نشد")
    bh = base64.b64encode(hashlib.sha256(_canon_body_relaxed(body)).digest()).decode("ascii")
    sig_core = (
        f"v=1; a=rsa-sha256; c=relaxed/relaxed; d={domain}; s={selector}; "
        f"t={int(time.time())}; h={':'.join(sel_names)}; bh={bh}; b="
    )
    sig_canon = _canon_header_relaxed(b"DKIM-Signature", sig_core.encode("ascii"))
    data = b"".join(_canon_header_relaxed(n, v) + b"\r\n" for n, v in selected) + sig_canon
    sig = base64.b64encode(_rsa_sign_pkcs1v15_sha256(key, data)).decode("ascii")
    return sig_core + sig


class _RawHeader(str):
    """هدر خام: هنگام فلت کردن verbatim نوشته می‌شود — policy پایتون نباید
    مقدار بلند b= را با encoded-word برش بزند (باعث خرابی verifier می‌شد).
    ویژگی name باعث می‌شود EmailPolicy._fold مستقیماً fold() همین شیء را صدا بزند
    (پروتکل BaseHeader: fold(*, policy) که نام هدر را خودش در خروجی می‌نویسد)."""

    name = "raw"  # noqa: A003 — سیگنالِ policy برای استفاده از fold خودِ شیء

    def __new__(cls, value: str, hdr_name: str = "DKIM-Signature"):
        obj = str.__new__(cls, value)
        obj.header_name = hdr_name
        return obj

    def fold(self, *, policy):  # noqa: N802 — API Generator/BaseHeader
        return f"{self.header_name}: {str(self)}\r\n" if self else f"{self.header_name}:\r\n"


def _inject_dkim_header(msg: EmailMessage, sig: str) -> None:
    """DKIM-Signature را در بالای بلوک هدرها به‌صورت خام می‌گذارد (بدون بازنویسی policy)."""
    try:
        msg._headers.insert(0, ("DKIM-Signature", _RawHeader(sig)))  # type: ignore[attr-defined]
        return
    except Exception:
        pass
    msg["DKIM-Signature"] = sig  # fallback استاندارد


def _maybe_dkim_sign(msg: EmailMessage, from_email: str) -> dict:
    """اگر dkim_enabled و کلید موجود باشد پیام را امضا می‌کند؛ تنظیم ناقص را صریح خطا می‌دهد."""
    cfg = _plain_config()
    if not cfg.get("dkim_enabled"):
        return {"signed": False, "reason": "امضای DKIM غیرفعال است"}
    key_pem = str(cfg.get("dkim_private_key") or "").strip()
    if not key_pem:
        raise ValueError(
            "امضای DKIM فعال است ولی کلید خصوصی ذخیره نشده — در کارت «سرور ایمیل» دکمهٔ "
            "«تولید کلید DKIM» را بزنید و «ذخیره تنظیمات» کنید (یا تیک امضای DKIM را بردارید)"
        )
    from_dom = from_email.split("@")[-1].lower().strip()
    domain = str(cfg.get("dkim_domain") or "").strip().lower() or from_dom
    if domain != from_dom:
        raise ValueError(
            f"دامنهٔ DKIM ({domain}) با دامنهٔ فرستنده ({from_dom}) هم‌خوان نیست — تگ d= باید "
            "همان دامنهٔ From باشد؛ دکمهٔ «تولید کلید DKIM» را دوباره بزنید"
        )
    selector = str(cfg.get("dkim_selector") or "").strip().lower() or "shabakeban"
    try:
        key = _parse_rsa_private_pem(key_pem)
    except Exception as e:
        raise ValueError(f"کلید خصوصی DKIM قابل خواندن نیست: {e}") from e
    try:
        sig = _dkim_sign_message(msg, domain, selector, key)
    except Exception as e:
        raise ValueError(f"امضای DKIM ناموفق بود: {e}") from e
    _inject_dkim_header(msg, sig)
    return {"signed": True, "domain": domain, "selector": selector}


def dkim_generate(selector: str | None = None, bits: int = 2048) -> dict:
    """کلید RSA بساز، در smtp_config.json نگه‌دار و رکورد TXT قابل انتشار برگردان."""
    sel = str(selector or "").strip().lower() or "shabakeban"
    if not re.fullmatch(r"[a-z0-9]([a-z0-9_-]{0,61}[a-z0-9])?", sel):
        raise ValueError("selector فقط حروف/رقم/خط تیره و تا ۶۳ نویسه باشد — مثال: shabakeban")
    if bits not in (1024, 2048, 3072):
        bits = 2048
    cfg = _plain_config()
    from_email = str(cfg.get("from_email") or "").strip()
    domain = str(cfg.get("dkim_domain") or "").strip().lower()
    if (not domain or "." not in domain or "@" in domain) and "@" in from_email:
        domain = from_email.split("@")[-1].lower()
    if not domain or "." not in domain or "@" in domain:
        raise ValueError(
            "دامنهٔ فرستنده مشخص نیست — ابتدا «فرستنده (From)» را روی دامنهٔ خودتان "
            "(مثلاً alerts@your-domain.ir) بگذارید، «ذخیره تنظیمات» را بزنید و بعد کلید بسازید"
        )
    key = _generate_rsa_keypair(bits)
    cfg["dkim_private_key"] = _pem_encode("PRIVATE KEY", _pkcs8_der(key))
    cfg["dkim_selector"] = sel
    cfg["dkim_domain"] = domain
    _write_config(cfg)
    pub_b64 = base64.b64encode(_spki_der(key["n"], key["e"])).decode("ascii")
    return {
        "ok": True,
        "selector": sel,
        "domain": domain,
        "dkim_host": f"{sel}._domainkey.{domain}",
        "txt_record": f"v=DKIM1; k=rsa; p={pub_b64}",
        "bits": bits,
        "dkim_key_set": True,
    }


# ---------------------------------------------------------------------------
# SPF evaluation + DNS authentication diagnostics (SPF / DKIM / DMARC / rDNS)
# ---------------------------------------------------------------------------
def _ip_in_net(ip: str, net: str) -> bool:
    try:
        return ipaddress.ip_address(ip) in ipaddress.ip_network(net, strict=False)
    except ValueError:
        return False


def _spf_evaluate(domain: str, ip: str, timeout: float = 3.0, depth: int = 10) -> dict:
    """SPF check — status: pass / fail / softfail / neutral / none / temperror."""
    try:
        txts = resolve_txt(domain, timeout)
    except Exception:
        txts = []
    spf = next((t.strip() for t in txts if t.strip().lower().startswith("v=spf1")), None)
    if spf is None:
        return {"status": "none", "record": None, "matched": ""}
    if depth <= 0:
        return {"status": "temperror", "record": spf, "matched": "include/redirect خیلی عمیق"}
    res = {"status": "neutral", "record": spf, "matched": "all"}
    for term in spf.split()[1:]:
        q, t = "+", term
        if term[:1] in "+-~?":
            q, t = term[:1], term[1:]
        low = t.lower()
        hit = False
        try:
            if low.startswith("ip4:"):
                hit = _ip_in_net(ip, t[4:])
            elif low.startswith("ip6:"):
                hit = False  # ارسال‌کنندهٔ این نرم‌افزار IPv4 است
            elif low == "a":
                hit = ip in resolve_a(domain, timeout)
            elif low.startswith("a:"):
                hit = ip in resolve_a(t[2:], timeout)
            elif low == "mx" or low.startswith("mx:"):
                host = domain if low == "mx" else t[3:]
                hit = any(ip in resolve_a(h, timeout) for h in resolve_mx(host, timeout))
            elif low.startswith("include:"):
                hit = _spf_evaluate(t[8:], ip, timeout, depth - 1)["status"] == "pass"
            elif low.startswith("redirect="):
                sub = _spf_evaluate(t[9:], ip, timeout, depth - 1)
                return {"status": sub["status"], "record": f"{spf} → {sub['record']}", "matched": sub["matched"]}
            elif low.startswith("exists:"):
                hit = bool(resolve_a(t[7:], timeout))
        except Exception:
            hit = False
        if hit or low == "all":
            res["status"] = {"+": "pass", "-": "fail", "~": "softfail", "?": "neutral"}[q]
            res["matched"] = term
            break
    return res


_KNOWN_PROVIDER_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.jp", "outlook.com",
    "hotmail.com", "live.com", "msn.com", "icloud.com", "me.com", "aol.com",
    "mailfa.com", "yandex.ru", "yandex.com", "mail.ru", "proton.me", "protonmail.com",
}


def auth_diagnostics(from_email: str = "", selector: str | None = None, timeout: float = 4.0) -> dict:
    """وضعیت SPF/DKIM/DMARC/rDNS برای دامنهٔ فرستنده + رکوردهای دقیقی که باید ثبت شود."""
    cfg = _plain_config()
    from_email = (from_email or str(cfg.get("from_email") or "")).strip()
    if not _looks_like_email(from_email):
        raise ValueError(
            "ابتدا «فرستنده (From)» را با یک ایمیل معتبر روی دامنهٔ خودتان ذخیره کنید — مثلاً alerts@your-domain.ir"
        )
    domain = from_email.split("@")[-1].lower()
    sel = (str(selector or "").strip().lower()
           or str(cfg.get("dkim_selector") or "").strip().lower()
           or "shabakeban")
    ip, ip_src = _public_ip(timeout=timeout)

    def _ptr():
        if not ip:
            return None
        try:
            recs = resolve_ptr(ip, timeout)
            return recs[0] if recs else None
        except Exception:
            return None

    def _spf():
        if not ip:
            return {"status": "none", "record": None, "matched": ""}
        try:
            return _spf_evaluate(domain, ip, timeout)
        except Exception as e:
            return {"status": "temperror", "record": None, "matched": str(e)}

    def _dkim():
        host = f"{sel}._domainkey.{domain}"
        try:
            recs = [r for r in resolve_txt(host, timeout) if "p=" in r]
        except Exception:
            recs = []
        rec = recs[0] if recs else None
        match = None
        priv = str(cfg.get("dkim_private_key") or "").strip()
        if priv:
            try:
                k = _parse_rsa_private_pem(priv)
                mine = base64.b64encode(_spki_der(k["n"], k["e"])).decode("ascii")
                pub_in_rec = ""
                if rec:
                    for part in rec.replace(" ", "").split(";"):
                        if part.lower().startswith("p="):
                            pub_in_rec = part[2:]
                if pub_in_rec:
                    match = "match" if pub_in_rec == mine else "mismatch"
            except Exception:
                match = None
        return {"host": host, "found": rec is not None, "record": rec,
                "match": match, "selector": sel, "key_saved": bool(priv)}

    def _dmarc():
        host = f"_dmarc.{domain}"
        try:
            recs = [r for r in resolve_txt(host, timeout) if r.strip().lower().startswith("v=dmarc1")]
        except Exception:
            recs = []
        return {"host": host, "found": bool(recs), "record": recs[0] if recs else None}

    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {k: ex.submit(f) for k, f in (("ptr", _ptr), ("spf", _spf), ("dkim", _dkim), ("dmarc", _dmarc))}
        ptr = futs["ptr"].result()
        spf = futs["spf"].result()
        dkim = futs["dkim"].result()
        dmarc = futs["dmarc"].result()

    records: dict[str, dict] = {
        "spf": {"host": f"@ ({domain})", "type": "TXT",
                "value": f"v=spf1 ip4:{ip} ~all" if ip else "v=spf1 ~all"},
        "dmarc": {"host": f"_dmarc.{domain}", "type": "TXT",
                  "value": f"v=DMARC1; p=none; rua=mailto:postmaster@{domain}"},
    }
    priv = str(cfg.get("dkim_private_key") or "").strip()
    if priv:
        try:
            k = _parse_rsa_private_pem(priv)
            records["dkim"] = {"host": f"{sel}._domainkey.{domain}", "type": "TXT",
                               "value": "v=DKIM1; k=rsa; p=" + base64.b64encode(_spki_der(k["n"], k["e"])).decode("ascii")}
        except Exception:
            pass

    steps: list[str] = []
    warnings: list[str] = []
    is_provider = domain in _KNOWN_PROVIDER_DOMAINS
    if is_provider:
        warnings.append(
            f"دامنهٔ فرستنده ({domain}) به سرویس‌دهنده تعلق دارد نه به شما — برای آن هیچ‌وقت نمی‌توانید SPF/DKIM تعریف "
            "کنید و گیرنده‌های بزرگ (Gmail و…) نامه را با خطای 5.7.26 رد می‌کنند. فرستنده (From) را روی دامنهٔ خودتان "
            "تنظیم کنید (خرید یک دامنهٔ ارزان کافی است) و بعد کلید DKIM بسازید."
        )
    if not ip:
        warnings.append("IP عمومی خروجی تشخیص داده نشد (اینترنت/فیلتر) — SPF را بعداً با IP واقعی به‌روز کنید.")
    else:
        steps.append(f"IP خروجی این سرور: {ip} — این IP باید در رکورد SPF دامنه مجاز شود.")
    if ptr:
        steps.append(f"rDNS (PTR) فعلی IP: {ptr} — اگر نام دامنهٔ شما نیست، با ISP/ارائه‌دهنده تنظیم کنید (اختیاری ولی مؤثر).")
    else:
        steps.append("rDNS (PTR) برای IP خروجی پیدا نشد — با ISP/ارائه‌دهنده تنظیم کنید (اختیاری ولی مؤثر).")
    if spf["status"] == "pass":
        steps.append("SPF: رکورد هست و IP خروجی مجاز است ✓")
    elif spf["status"] in ("fail", "softfail", "neutral"):
        steps.append(f"SPF: رکورد هست ولی IP خروجی مجاز نیست (مکانیزم: {spf.get('matched')}) — رکورد زیر را جایگزین کنید.")
    elif spf["status"] == "none":
        steps.append("SPF: هیچ رکورد SPF روی دامنه نیست — رکورد زیر را ثبت کنید.")
    else:
        steps.append("SPF: رکورد خوانده نشد (خطای DNS) — دوباره تلاش کنید.")
    if dkim.get("match") == "match":
        steps.append(f"DKIM: رکورد DNS با کلید همین نرم‌افزار یکی است ✓ (selector: {sel})")
    elif dkim.get("match") == "mismatch":
        steps.append(f"DKIM: رکورد هست ولی با کلید نرم‌افزار نمی‌خواند — رکورد زیر را جایگزین کنید (selector: {sel}).")
    elif dkim.get("found"):
        steps.append(f"DKIM: رکورد هست؛ کلید محلی برای مقایسه ذخیره نشده — اگر همین کلید است که ثبت کرده‌اید درست است (selector: {sel}).")
    elif dkim.get("key_saved"):
        steps.append(f"DKIM: کلید در نرم‌افزار ساخته شده ولی در DNS ثبت نشده — رکورد زیر را در پنل دامنه ثبت کنید (selector: {sel}).")
    else:
        steps.append("DKIM: کلید هنوز ساخته نشده — دکمهٔ «تولید کلید DKIM» را بزنید و رکورد زیر را ثبت کنید.")
    if dmarc.get("found"):
        steps.append("DMARC: رکورد هست ✓")
    else:
        steps.append("DMARC: رکورد ثبت نشده — رکورد زیر را ثبت کنید (اجباری نیست ولی تحویل بهتر می‌شود).")

    ok_all = (dkim.get("match") == "match" and dmarc.get("found") and not is_provider
              and (spf["status"] == "pass" or spf["status"] == "softfail" or not ip))
    if ok_all:
        verdict = ("احراز هویت دامنه کامل است (SPF/DKIM/DMARC) — «ارسال ایمیل آزمایشی» را بزنید؛ "
                   "اگر گیرندهٔ بزرگی باز هم رد کرد، معمولاً اعتبار IP/بلاک‌لیست است نه تنظیمات.")
    elif is_provider:
        verdict = "قدم اول: فرستنده باید روی دامنهٔ خودتان باشد — با @gmail.com/@yahoo.com احراز هویت ممکن نیست."
    else:
        verdict = ("رکوردهای DNS زیر را در پنل دامنه ثبت کنید (انتشار DNS چند دقیقه تا چند ساعت طول می‌کشد) "
                   "و بعد دوباره «بررسی احراز هویت دامنه» را بزنید.")

    return {
        "ok": True,
        "from": from_email,
        "domain": domain,
        "egress_ip": ip,
        "egress_source": ip_src,
        "ptr": {"ip": ip, "record": ptr},
        "spf": spf,
        "dkim": dkim,
        "dmarc": dmarc,
        "records": records,
        "steps": steps,
        "warnings": warnings,
        "verdict": verdict,
        "selector": sel,
    }


def _auto_helo() -> str:
    """Best HELO identity: RFC 5321 address literal [local-ip], else fqdn."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 53))
            ip = s.getsockname()[0]
        finally:
            s.close()
        if ip and not ip.startswith("127."):
            return f"[{ip}]"
    except OSError:
        pass
    try:
        fqdn = socket.getfqdn()
        if fqdn and fqdn != "localhost" and "." in fqdn:
            return fqdn
    except Exception:
        pass
    return "localhost"


def _effective_helo(helo: str) -> str:
    h = (helo or "").strip()
    if not h or ".local" in h.lower():
        return _auto_helo()
    return h


def _check_tcp_port(host: str, port: int, timeout: float) -> dict:
    """One IPv4 TCP connect probe — thread-safe, بدون معطلی IPv6."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect((host, port))
            return {"host": host, "port": port, "status": "open", "detail": ""}
        finally:
            s.close()
    except ConnectionRefusedError:
        return {"host": host, "port": port, "status": "refused", "detail": "اتصال رد شد"}
    except socket.timeout:
        return {"host": host, "port": port, "status": "blocked", "detail": "Timeout"}
    except OSError as e:
        return {"host": host, "port": port, "status": "blocked", "detail": type(e).__name__}


def diagnose_direct(to_email: str, timeout: float = 8.0) -> dict:
    """Check whether standalone (direct MX) delivery is possible on this network.

    بررسی پورت‌ها موازی اجرا می‌شود (حداکثر ~۶ ثانیه) تا UI هنگ نکند.
    """
    if not _looks_like_email(to_email):
        raise ValueError("گیرنده باید یک ایمیل معتبر باشد")
    domain = to_email.split("@", 1)[1].lower()
    mx = resolve_mx_full(domain, timeout=timeout)
    probe_to = max(2.0, min(timeout, 6.0))
    targets: list[tuple[str, int]] = []
    for host in [h for _, h in mx][:3]:
        targets.append((host, 25))
        targets.append((host, 587))
    if targets:
        with ThreadPoolExecutor(max_workers=min(6, len(targets))) as ex:
            checks = list(ex.map(lambda t: _check_tcp_port(t[0], t[1], probe_to), targets))
    else:
        checks = []
    port25_open = any(c["port"] == 25 and c["status"] == "open" for c in checks)
    port587_open = any(c["port"] == 587 and c["status"] == "open" for c in checks)
    if not mx:
        verdict = (
            f"برای دامنهٔ {domain} رکورد MX پیدا نشد — دامنه ممکن است غلط باشد "
            "یا DNS این شبکه محدود است. آدرس گیرنده یا DNS را چک کنید."
        )
    elif port25_open:
        verdict = (
            "پورت خروجی ۲۵ باز است — این شبکه می‌تواند بدون جیمیل/یاهو و کاملاً مستقل ایمیل بفرستد. "
            "حالا در تنظیمات، حالت «مستقیم به MX گیرنده» را ذخیره کنید و «ارسال ایمیل آزمایشی» را بزنید. "
            "توجه: برای تحویل به Gmail/Outlook علاوه بر این، دامنهٔ فرستنده باید SPF/DKIM داشته باشد — "
            "بخش «احراز هویت دامنه» را ببینید."
        )
    elif port587_open:
        verdict = (
            "پورت ۲۵ بسته است ولی ۵۸۷ روی بعضی سرورهای MX باز است؛ اکثر سرورهای ایمیل نامهٔ "
            "بدون احراز هویت را فقط از پورت ۲۵ می‌پذیرند، پس شانس موفقیت کم است — "
            "بهتر است شبکه‌ای با پورت خروجی ۲۵ باز (مثل اینترنت دیگر یا VPS) یا حالت «رله SMTP» استفاده شود."
        )
    else:
        verdict = (
            "پورت خروجی ۲۵ روی این شبکه باز نیست (ISP/فایروال آن را مسدود کرده). "
            "ارسال مستقل از اینجا ممکن نیست: یا نرم‌افزار را روی سرور/VPS با پورت ۲۵ باز اجرا کنید "
            "یا از حالت «رله SMTP» استفاده کنید."
        )
    return {
        "ok": True,
        "domain": domain,
        "mx": [{"pref": p, "host": h} for p, h in mx],
        "checks": checks,
        "port25_open": port25_open,
        "verdict": verdict,
        "helo_suggestion": _auto_helo(),
    }


def _build_message(
    subject: str,
    body: str,
    from_email: str,
    from_name: str,
    dest: str,
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject or "شبکه‌بان"
    msg["From"] = f"{from_name} <{from_email}>" if from_name else from_email
    msg["To"] = dest
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=from_email.split("@")[-1] if "@" in from_email else "shabakeban.local")
    msg.set_content(body or "")
    for att in attachments or []:
        fname, data, mime = att[0], att[1], (att[2] if len(att) > 2 else "application/octet-stream")
        maintype, _, subtype = mime.partition("/")
        if not subtype:
            maintype, subtype = "application", "octet-stream"
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=fname)
    return msg


def _smtp_send_once(host, port, username, password, msg, timeout, mode: str, helo: str = "shabakeban.local"):
    if mode == "ssl":
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, timeout=timeout, context=context) as server:
            if helo:
                try:
                    server.ehlo(helo)
                except Exception:
                    pass
            if username and password:
                server.login(username, password)
            server.send_message(msg)
    elif mode == "starttls":
        with smtplib.SMTP(host, port, timeout=timeout, local_hostname=helo or None) as server:
            server.ehlo(helo or None)
            context = ssl.create_default_context()
            server.starttls(context=context)
            server.ehlo(helo or None)
            if username and password:
                server.login(username, password)
            server.send_message(msg)
    else:  # plain (port 25 typical for MX)
        with smtplib.SMTP(host, port, timeout=timeout, local_hostname=helo or None) as server:
            server.ehlo(helo or None)
            if username and password:
                server.login(username, password)
            server.send_message(msg)


def send_direct(
    subject: str,
    body: str,
    from_email: str,
    from_name: str,
    dest: str,
    timeout: float = 30,
    helo_host: str = "",
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> dict:
    """Deliver directly to recipient domain MX — no Gmail/relay account needed."""
    if not _looks_like_email(dest):
        raise ValueError("آدرس گیرنده معتبر نیست")
    if not _looks_like_email(from_email):
        raise ValueError(
            "فرستنده (From) باید یک ایمیل معتبر باشد، مثال: alerts@your-domain.ir "
            "(لازم نیست حساب واقعی باشد، فقط شکل ایمیل داشته باشد)"
        )

    domain = dest.split("@", 1)[1].lower()
    mx_hosts = resolve_mx(domain, timeout=min(timeout, 8))
    if not mx_hosts:
        raise ValueError(
            f"برای دامنهٔ {domain} رکورد MX یا A پیدا نشد — آدرس گیرنده غلط است "
            "یا DNS این شبکه اجازهٔ پرس‌وجو نمی‌دهد (اینترنت را چک کنید)"
        )

    helo = _effective_helo(helo_host)
    msg = _build_message(subject, body, from_email, from_name, dest, attachments)
    dkim_info = _maybe_dkim_sign(msg, from_email)
    # تحویل MX فقط روی پورت ۲۵ تعریف شده (RFC 5321) — تلاش روی ۵۸۷ فقط Timeout بی‌فایده می‌سازد
    attempts: list[tuple[str, int, str]] = [(h, 25, "plain") for h in mx_hosts[:4]]

    deadline = time.monotonic() + max(timeout * 2, 60)
    per_try = max(10.0, min(timeout, 20.0))
    errors: list[str] = []
    tried = 0
    server_rejected = False
    for host, port, mode in attempts:
        if time.monotonic() > deadline:
            errors.append("مهلت کل ارسال تمام شد (تلاش‌های بعدی حذف شدند)")
            break
        tried += 1
        try:
            _smtp_send_once(host, port, "", "", msg, per_try, mode, helo=helo)
            return {
                "ok": True,
                "mode": "direct",
                "to": dest,
                "from": from_email,
                "mx": host,
                "port": port,
                "transport": mode,
                "helo": helo,
                "dkim": dkim_info,
                "subject": subject,
            }
        except smtplib.SMTPRecipientsRefused as e:
            server_rejected = True
            codes = ",".join(str(v[0]) for v in (e.recipients or {}).values()) if hasattr(e, "recipients") else ""
            errors.append(f"{host}:{port} گیرنده رد شد {codes}")
        except smtplib.SMTPSenderRefused as e:
            server_rejected = True
            errors.append(f"{host}:{port} فرستنده رد شد ({getattr(e, 'smtp_code', '')})")
        except smtplib.SMTPDataError as e:
            code = getattr(e, "smtp_code", "")
            err = getattr(e, "smtp_error", "")
            if isinstance(err, bytes):
                err = err.decode("ascii", "replace")
            server_rejected = True
            errors.append(f"{host}:{port} سرور نامه را نپذیرفت ({code} {err})".strip())
        except smtplib.SMTPHeloError:
            errors.append(f"{host}:{port} HELO رد شد")
        except (smtplib.SMTPException, OSError, TimeoutError, ConnectionError) as e:
            errors.append(f"{host}:{port} {type(e).__name__}")
            continue

    if server_rejected:
        if any(_is_unauth_error(x) for x in errors):
            hint = (
                "سرور گیرنده فرستنده را «احرازنشده» رد کرد (معروف‌ترین نمونه: خطای 5.7.26 جیمیل). راه‌حل در سه قدم: "
                "۱) فرستنده (From) روی دامنهٔ خودتان باشد — نه @gmail.com/@yahoo.com، چون دامنهٔ دیگران قابل احراز نیست؛ "
                "۲) دکمهٔ «تولید کلید DKIM» را بزنید و رکورد TXT داده‌شده را در پنل DNS دامنه ثبت کنید؛ "
                "۳) رکوردهای SPF و DMARC پیشنهادی را هم ثبت کنید — دکمهٔ «بررسی احراز هویت دامنه» هر سه را چک می‌کند. "
                "نامه ممکن است در Spam هم باشد."
            )
        else:
            hint = (
                "سرور گیرنده نامه را نپذیرفت — Gmail/Yahoo و اکثر سرویس‌های بزرگ ارسال مستقیم از "
                "IP خانگی/آلوده را رد می‌کنند (بدون SPF/DKIM). از یک سرور/VPS با IP تمیز ارسال کنید، "
                "یا از حالت «رله SMTP» استفاده کنید. نامه ممکن است در Spam هم باشد."
            )
    elif tried and not server_rejected:
        hint = (
            "اتصال به هیچ سرور MX ممکن نشد — معمولاً پورت خروجی ۲۵ توسط ISP/فایروال مسدود است "
            "یا اینترنت قطع است. با دکمهٔ «بررسی امکان ارسال مستقیم» وضعیت پورت ۲۵ را ببینید؛ "
            "در صورت مسدود بودن، نرم‌افزار را روی سرور/VPS اجرا کنید یا از حالت «رله SMTP» استفاده کنید."
        )
    else:
        hint = "جزئیات بیشتر در لاگ سرور."
    raise ValueError("ارسال مستقیم ناموفق. " + " | ".join(errors[:6]) + " — " + hint)


def _is_unauth_error(text: str) -> bool:
    """رف فرستندهٔ احرازنشده (5.7.26 جیمیل و مشابه‌ها) از خطاهای عمومی تفکیک می‌شود."""
    t = (text or "").lower()
    keys = ("unauthenticated", "5.7.26", "spf", "dkim", "dmarc",
            "authentication required", "policy reasons", "access denied",
            "blocked using", "bad reputation")
    return any(k in t for k in keys)


def send_relay(
    subject: str,
    body: str,
    to_email: str | None = None,
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> dict:
    cfg = _plain_config()
    host = (cfg.get("host") or "").strip()
    try:
        port = int(cfg.get("port") or 587)
    except (TypeError, ValueError):
        port = 587
    username = (cfg.get("username") or "").strip()
    password = "".join(str(cfg.get("password") or "").split())
    from_email = (cfg.get("from_email") or "").strip()
    from_name = (cfg.get("from_name") or "شبکه‌بان").strip()
    dest = (to_email or cfg.get("to_email") or "").strip()
    helo = (cfg.get("helo_host") or "shabakeban.local").strip()
    timeout = float(cfg.get("timeout") or 30)

    if not host:
        raise ValueError("آدرس SMTP رله مشخص نشده است")
    if not _looks_like_email(dest):
        raise ValueError("آدرس گیرنده معتبر نیست")
    if not username or not password:
        raise ValueError("برای حالت رله، نام کاربری و رمز SMTP لازم است")
    if not _looks_like_email(from_email):
        if _looks_like_email(username):
            from_email = username
        else:
            raise ValueError("فرستنده باید ایمیل معتبر باشد")

    msg = _build_message(subject, body, from_email, from_name, dest, attachments)
    dkim_info = _maybe_dkim_sign(msg, from_email)

    if port == 465:
        attempts = [(465, "ssl")]
    elif port == 587:
        attempts = [(587, "starttls")]
    else:
        attempts = [(port, "ssl" if cfg.get("use_ssl") else "starttls")]

    host_l = host.lower()
    if "gmail" in host_l or "google" in host_l or "yahoo" in host_l or "mailfa" in host_l:
        if port == 587:
            attempts.append((465, "ssl"))
        elif port == 465:
            attempts.append((587, "starttls"))

    last_err: Exception | None = None
    used_port, used_mode = attempts[0]
    for try_port, mode in attempts:
        try:
            _smtp_send_once(host, try_port, username, password, msg, timeout, mode, helo=helo)
            used_port, used_mode = try_port, mode
            last_err = None
            break
        except smtplib.SMTPAuthenticationError as e:
            raise ValueError(
                "احراز هویت SMTP رد شد. برای Gmail از App Password استفاده کنید. "
                f"جزئیات: {e}"
            ) from e
        except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError, ConnectionError, OSError, TimeoutError) as e:
            last_err = e
            continue
        except smtplib.SMTPException as e:
            last_err = e
            continue

    if last_err is not None:
        raise ValueError(f"اتصال SMTP رله برقرار نشد ({host}:{port}): {last_err}") from last_err

    return {
        "ok": True,
        "mode": "relay",
        "to": dest,
        "from": from_email,
        "host": host,
        "port": used_port,
        "transport": used_mode,
        "dkim": dkim_info,
        "subject": subject,
    }


def send_mail(
    subject: str,
    body: str,
    to_email: str | None = None,
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> dict:
    cfg = _plain_config()
    if not cfg.get("enabled"):
        raise ValueError(
            "ارسال ایمیل غیرفعال است — در کارت «سرور ایمیل» گزینهٔ «فعال‌سازی ارسال ایمیل» را "
            "تیک بزنید و «ذخیره تنظیمات» را بزنید"
        )
    mode = str(cfg.get("mode") or "direct").lower()
    dest = (to_email or cfg.get("to_email") or "").strip()
    from_email = (cfg.get("from_email") or cfg.get("username") or "").strip()
    from_name = (cfg.get("from_name") or "شبکه‌بان").strip()
    timeout = float(cfg.get("timeout") or 30)
    helo = (cfg.get("helo_host") or "").strip()

    if mode == "direct":
        if not _looks_like_email(from_email):
            raise ValueError(
                "در حالت ارسال مستقیم، فیلد From را با یک ایمیل پر کنید "
                "(مثلاً alert@yourdomain.com یا هر آدرس شناسایی‌کننده)"
            )
        return send_direct(
            subject=subject,
            body=body,
            from_email=from_email,
            from_name=from_name,
            dest=dest,
            timeout=timeout,
            helo_host=helo,
            attachments=attachments,
        )
    return send_relay(subject, body, to_email=to_email, attachments=attachments)


def send_test(to_email: str | None = None, message: str | None = None) -> dict:
    from datetime import datetime, timezone, timedelta
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Asia/Tehran"))
    except Exception:
        now = datetime.now(timezone(timedelta(hours=3, minutes=30)))
    stamp = now.strftime("%Y-%m-%d %H:%M:%S %Z")
    cfg = get_config(mask_password=True)
    mode = cfg.get("mode") or "direct"
    dkim_on = bool(cfg.get("dkim_enabled"))
    body = message or (
        "این یک پیام آزمایشی از نرم‌افزار شبکه‌بان است.\n"
        f"حالت ارسال: {mode}\n"
        f"امضای DKIM: {'فعال' if dkim_on else 'غیرفعال'}\n"
        f"زمان ارسال (تهران): {stamp}\n"
        "اگر این ایمیل را دریافت کردید، مسیر ارسال درست کار می‌کند."
    )
    return send_mail(subject="[شبکه‌بان] تست ارسال", body=body, to_email=to_email or None)
