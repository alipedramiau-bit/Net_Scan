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

import json
import random
import smtplib
import socket
import ssl
import struct
import time
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
}


def _load_raw() -> dict:
    try:
        data = json.loads(_CONFIG.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {}


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
    for k in ("host", "username", "password", "from_email", "from_name", "to_email", "helo_host"):
        cfg[k] = str(cfg.get(k) or "")
    if mask_password and cfg.get("password"):
        cfg["password"] = "********"
        cfg["password_set"] = True
    else:
        cfg["password_set"] = bool(_load_raw().get("password"))
    return cfg


def save_config(body: dict) -> dict:
    current = {**DEFAULTS, **_load_raw()}
    for key in DEFAULTS:
        if key not in body:
            continue
        val = body[key]
        if key == "password":
            if val is None or str(val).strip() in ("", "********"):
                continue
            current["password"] = str(val)
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
        elif key in ("enabled", "use_tls", "use_ssl"):
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
    _CONFIG.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
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
    for ns in ns_list:
        try:
            mx = _dns_query_mx(domain, nameserver=ns, timeout=timeout)
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


def diagnose_direct(to_email: str, timeout: float = 8.0) -> dict:
    """Check whether standalone (direct MX) delivery is possible on this network."""
    if not _looks_like_email(to_email):
        raise ValueError("گیرنده باید یک ایمیل معتبر باشد")
    domain = to_email.split("@", 1)[1].lower()
    mx = resolve_mx_full(domain, timeout=timeout)
    checks: list[dict] = []
    port25_open = False
    for host in [h for _, h in mx][:3]:
        for port in (25, 587):
            status, detail = "blocked", ""
            try:
                with socket.create_connection((host, port), timeout=timeout):
                    status = "open"
            except ConnectionRefusedError:
                status, detail = "refused", "اتصال رد شد"
            except OSError as e:
                status, detail = "blocked", type(e).__name__
            checks.append({"host": host, "port": port, "status": status, "detail": detail})
            if port == 25 and status == "open":
                port25_open = True
    if not mx:
        verdict = (
            f"برای دامنهٔ {domain} رکورد MX پیدا نشد — دامنه ممکن است غلط باشد "
            "یا DNS این شبکه محدود است. آدرس گیرنده یا DNS را چک کنید."
        )
    elif port25_open:
        verdict = (
            "پورت خروجی ۲۵ باز است — این شبکه می‌تواند بدون جیمیل/یاهو و کاملاً مستقل ایمیل بفرستد. "
            "حالا در تنظیمات، حالت «مستقیم به MX گیرنده» را ذخیره کنید و «ارسال ایمیل آزمایشی» را بزنید."
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
    # Port 25 (MX standard) first, then 587; bounded so UI never hangs minutes
    attempts: list[tuple[str, int, str]] = []
    for h in mx_hosts[:4]:
        attempts.append((h, 25, "plain"))
        attempts.append((h, 587, "starttls"))

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
            err_s = str(e)
            server_rejected = True
            errors.append(f"{host}:{port} سرور نامه را نپذیرفت ({err_s.split(':')[0]})")
        except smtplib.SMTPHeloError:
            errors.append(f"{host}:{port} HELO رد شد")
        except (smtplib.SMTPException, OSError, TimeoutError, ConnectionError) as e:
            errors.append(f"{host}:{port} {type(e).__name__}")
            continue

    if server_rejected:
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
    body = message or (
        "این یک پیام آزمایشی از نرم‌افزار شبکه‌بان است.\n"
        f"حالت ارسال: {mode}\n"
        f"زمان ارسال (تهران): {stamp}\n"
        "اگر این ایمیل را دریافت کردید، مسیر ارسال درست کار می‌کند."
    )
    return send_mail(subject="[شبکه‌بان] تست ارسال", body=body, to_email=to_email or None)
