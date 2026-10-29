"""Minimal RouterOS API (TCP 8728) client — no third-party deps.

Pushes terminal-style MikroTik commands to devices via the API service.
"""
from __future__ import annotations

import hashlib
import re
import socket
import time
from typing import Iterable


# ---------------------------------------------------------------------------
# Time helpers: device clock offset → Tehran / Jalali for log display
# ---------------------------------------------------------------------------
_ROS_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    """Convert Gregorian date to Jalali (Persian) calendar."""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy + 1 if gm > 2 else gy
    days = 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400 - 80 + gd + g_d_m[gm - 1]
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return jy, jm, jd


def _to_tehran(dt_utc):
    """Convert aware/naive UTC datetime to Asia/Tehran."""
    from datetime import datetime, timezone, timedelta
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Asia/Tehran")
    except Exception:
        tz = timezone(timedelta(hours=3, minutes=30))
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    return dt_utc.astimezone(tz)


def _fmt_jalali_tehran(dt) -> str:
    """Format datetime as Jalali date + Tehran clock: 1403/07/17 14:05:22"""
    tehran = _to_tehran(dt)
    jy, jm, jd = _gregorian_to_jalali(tehran.year, tehran.month, tehran.day)
    return f"{jy:04d}/{jm:02d}/{jd:02d} {tehran.hour:02d}:{tehran.minute:02d}:{tehran.second:02d}"


def _parse_ros_clock(date_s: str, time_s: str):
    """Parse RouterOS /system/clock date+time → naive datetime (device local)."""
    from datetime import datetime
    date_s = (date_s or "").strip()
    time_s = (time_s or "").strip()
    # date: oct/08/2026  or  2026-10-08
    year = month = day = None
    m = re.match(r"([A-Za-z]{3})/(\d{1,2})/(\d{4})$", date_s)
    if m:
        month = _ROS_MONTHS.get(m.group(1).lower())
        day = int(m.group(2))
        year = int(m.group(3))
    else:
        m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})$", date_s)
        if m:
            year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        else:
            m = re.match(r"([A-Za-z]{3})/(\d{1,2})$", date_s)
            if m:
                from datetime import datetime as _dt
                month = _ROS_MONTHS.get(m.group(1).lower())
                day = int(m.group(2))
                year = _dt.utcnow().year
    tm = re.match(r"(\d{1,2}):(\d{2}):(\d{2})", time_s)
    if not (year and month and day and tm):
        return None
    try:
        return datetime(year, month, day, int(tm.group(1)), int(tm.group(2)), int(tm.group(3)))
    except ValueError:
        return None


def _parse_ros_log_time(time_s: str, device_now, server_now_utc):
    """Parse a single log 'time' field relative to device clock.

    RouterOS formats:
      - jan/02/2024 10:30:45
      - oct/08 12:05:17
      - 12:05:17  (same day as device clock)
    Returns timezone-aware UTC datetime or None.
    """
    from datetime import datetime, timezone, timedelta
    time_s = (time_s or "").strip()
    if not time_s:
        return None

    year = month = day = None
    hour = minute = second = 0

    # full: mon/dd/yyyy hh:mm:ss
    m = re.match(
        r"([A-Za-z]{3})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})",
        time_s,
    )
    if m:
        month = _ROS_MONTHS.get(m.group(1).lower())
        day = int(m.group(2))
        year = int(m.group(3))
        hour, minute, second = int(m.group(4)), int(m.group(5)), int(m.group(6))
    else:
        # mon/dd hh:mm:ss
        m = re.match(
            r"([A-Za-z]{3})/(\d{1,2})\s+(\d{1,2}):(\d{2}):(\d{2})",
            time_s,
        )
        if m:
            month = _ROS_MONTHS.get(m.group(1).lower())
            day = int(m.group(2))
            hour, minute, second = int(m.group(3)), int(m.group(4)), int(m.group(5))
            if device_now:
                year = device_now.year
                # if month/day is in the future vs device, previous year
                try:
                    cand = datetime(year, month, day)
                    if device_now and cand.date() > device_now.date():
                        year -= 1
                except ValueError:
                    pass
            elif server_now_utc:
                year = server_now_utc.year
        else:
            # hh:mm:ss only
            m = re.match(r"(\d{1,2}):(\d{2}):(\d{2})$", time_s)
            if m and device_now:
                year, month, day = device_now.year, device_now.month, device_now.day
                hour, minute, second = int(m.group(1)), int(m.group(2)), int(m.group(3))
            else:
                return None

    if not (year and month and day):
        return None
    try:
        device_local = datetime(year, month, day, hour, minute, second)
    except ValueError:
        return None

    # Apply offset: corrected_utc = device_local_as_if_utc + (server_utc - device_clock_as_utc)
    # device_now is naive local on device; server_now_utc is aware UTC captured at probe time.
    # offset = server_utc_naive - device_now  (how much device is behind/ahead)
    if device_now is not None and server_now_utc is not None:
        server_naive = server_now_utc.replace(tzinfo=None) if server_now_utc.tzinfo else server_now_utc
        # Better: treat device clock reading as "what device thinks now is"
        # real_utc ≈ server_now_utc
        # device_event_utc ≈ server_now_utc - (device_now - device_local)
        delta = device_now - device_local  # positive if event is in the past on device
        from datetime import timezone as _tz
        event_utc = server_now_utc - delta
        return event_utc

    # no offset available — assume device local ≈ Tehran already, just mark as UTC-ish
    return device_local.replace(tzinfo=timezone.utc)


def _format_device_logs(logs: list, device_now, server_now_utc) -> str:
    """Build log text with Jalali/Tehran corrected timestamps."""
    lines = []
    header_bits = ["=== /log (تهران / هجری شمسی) ==="]
    if device_now is not None and server_now_utc is not None:
        try:
            srv = _fmt_jalali_tehran(server_now_utc)
            header_bits.append(f"# زمان سرور هنگام خواندن: {srv}")
            header_bits.append(f"# ساعت دستگاه (خام): {device_now.strftime('%Y-%m-%d %H:%M:%S')}")
            delta = server_now_utc.replace(tzinfo=None) - device_now
            total_sec = int(delta.total_seconds())
            sign = "+" if total_sec >= 0 else "-"
            abs_sec = abs(total_sec)
            h, rem = divmod(abs_sec, 3600)
            m, s = divmod(rem, 60)
            header_bits.append(f"# افست اصلاحی (سرور − دستگاه): {sign}{h:02d}:{m:02d}:{s:02d}")
        except Exception:
            pass
    lines.extend(header_bits)

    slice_logs = logs[-200:] if len(logs) > 200 else logs
    for i, row in enumerate(slice_logs, 1):
        time_s = row.get("time") or ""
        topics = row.get("topics") or row.get("topic") or ""
        msg = row.get("message") or row.get("msg") or ""
        corrected = _parse_ros_log_time(time_s, device_now, server_now_utc)
        if corrected is not None:
            try:
                disp = _fmt_jalali_tehran(corrected)
            except Exception:
                disp = time_s
        else:
            disp = time_s or "-"
        lines.append(f"{i:3d}  {disp}  [{topics}]  {msg}")
    return "\n".join(lines).strip()



class RouterOSError(RuntimeError):
    pass


def _encode_length(length: int) -> bytes:
    if length < 0x80:
        return bytes([length])
    if length < 0x4000:
        length |= 0x8000
        return bytes([(length >> 8) & 0xFF, length & 0xFF])
    if length < 0x200000:
        length |= 0xC00000
        return bytes([(length >> 16) & 0xFF, (length >> 8) & 0xFF, length & 0xFF])
    if length < 0x10000000:
        length |= 0xE0000000
        return bytes([
            (length >> 24) & 0xFF,
            (length >> 16) & 0xFF,
            (length >> 8) & 0xFF,
            length & 0xFF,
        ])
    return bytes([
        0xF0,
        (length >> 24) & 0xFF,
        (length >> 16) & 0xFF,
        (length >> 8) & 0xFF,
        length & 0xFF,
    ])


def _encode_word(word: str) -> bytes:
    data = word.encode("utf-8", errors="surrogateescape")
    return _encode_length(len(data)) + data


def _encode_sentence(words: Iterable[str]) -> bytes:
    return b"".join(_encode_word(w) for w in words) + b"\x00"


def _trap_message(sentence: list[str]) -> str:
    msg = next((w[9:] for w in sentence if w.startswith("=message=")), None)
    cat = next((w[9:] for w in sentence if w.startswith("=category=")), None)
    if msg and cat:
        return f"{msg} (category={cat})"
    return msg or " | ".join(sentence)


def _parse_terminal_line(line: str) -> list[str] | None:
    """Convert a simple terminal command into an API sentence.

    Examples:
      /user add name=olom1 password="x" group=full
        → ['/user/add', '=name=olom1', '=password=x', '=group=full']
      /snmp set enabled=yes trap-version=2
        → ['/snmp/set', '=enabled=yes', '=trap-version=2']
      /ip service enable api
        → ['/ip/service/enable', '=numbers=api']  (best-effort)
    """
    line = line.strip()
    if not line or line.startswith("#") or line.startswith(";"):
        return None
    # Already API-style
    if line.startswith("/") and ("=" in line.split()[0] if line.split() else False):
        return None

    # Match: /path/parts command attr=val ...
    m = re.match(
        r"^(/(?:[A-Za-z0-9\-]+(?:\s+[A-Za-z0-9\-]+)*))\s+(add|set|remove|enable|disable|print|run)\b(.*)$",
        line,
        re.I,
    )
    if not m:
        return None

    path_raw, cmd, rest = m.group(1), m.group(2).lower(), m.group(3).strip()
    # "/ip service" or "/user" or "/snmp community" → /ip/service , /user , /snmp/community
    parts = path_raw.replace("/", " ").split()
    path = "/" + "/".join(parts)
    api_cmd = f"{path}/{cmd}"

    attrs: list[str] = []
    # find query: [ find ... ] → ?key=val (remove from rest before attr parse)
    find_m = re.search(r"\[\s*find\s+([^\]]+)\]", rest, re.I)
    rest_for_attrs = rest
    if find_m:
        query = find_m.group(1).strip()
        rest_for_attrs = (rest[:find_m.start()] + " " + rest[find_m.end():]).strip()
        for part in re.findall(
            r"""([A-Za-z0-9\-\.]+)=("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^\s]+)""",
            query,
        ):
            k, v = part
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            attrs.append(f"?{k}={v}")

    # Tokenize attr=value with optional quotes
    for am in re.finditer(
        r"""([A-Za-z0-9\-\.]+)=("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^\s]+)""",
        rest_for_attrs,
    ):
        key = am.group(1)
        val = am.group(2)
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        val = val.replace('\\"', '"').replace("\\'", "'")
        attrs.append(f"={key}={val}")

    # enable/disable with bare name: /ip service enable api
    if cmd in ("enable", "disable", "remove", "run") and not attrs:
        leftover = re.sub(r"\[\s*find[^\]]*\]", "", rest, flags=re.I).strip()
        if leftover and "=" not in leftover:
            num = leftover.strip().strip('"').strip("'")
            attrs.append(f"=numbers={num}")

    return [api_cmd, *attrs]


class RouterOSClient:
    def __init__(self, host: str, port: int = 8728, timeout: float = 15.0):
        self.host = host
        self.port = int(port)
        self.timeout = float(timeout)
        self.sock: socket.socket | None = None

    def connect(self) -> None:
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.sock.settimeout(self.timeout)

    def close(self) -> None:
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *exc):
        self.close()

    def _read_exact(self, n: int) -> bytes:
        assert self.sock is not None
        buf = bytearray()
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise RouterOSError("اتصال API قطع شد")
            buf.extend(chunk)
        return bytes(buf)

    def _read_length(self) -> int:
        b = self._read_exact(1)[0]
        if b & 0x80 == 0:
            return b
        if b & 0xC0 == 0x80:
            return ((b & 0x7F) << 8) + self._read_exact(1)[0]
        if b & 0xE0 == 0xC0:
            o = self._read_exact(2)
            return ((b & 0x1F) << 16) + (o[0] << 8) + o[1]
        if b & 0xF0 == 0xE0:
            o = self._read_exact(3)
            return ((b & 0x0F) << 24) + (o[0] << 16) + (o[1] << 8) + o[2]
        if b == 0xF0:
            o = self._read_exact(4)
            return (o[0] << 24) + (o[1] << 16) + (o[2] << 8) + o[3]
        raise RouterOSError("طول word نامعتبر در پاسخ API")

    def _read_word(self) -> str | None:
        length = self._read_length()
        if length == 0:
            return None
        data = self._read_exact(length)
        return data.decode("utf-8", errors="replace")

    def read_sentence(self) -> list[str]:
        words: list[str] = []
        while True:
            w = self._read_word()
            if w is None:
                break
            words.append(w)
        return words

    def write_sentence(self, words: Iterable[str]) -> None:
        assert self.sock is not None
        self.sock.sendall(_encode_sentence(words))

    def talk(self, words: Iterable[str], timeout: float | None = None) -> list[list[str]]:
        words = list(words)
        self.write_sentence(words)
        old_timeout = None
        if timeout is not None and self.sock:
            old_timeout = self.sock.gettimeout()
            self.sock.settimeout(timeout)
        replies: list[list[str]] = []
        try:
            while True:
                sentence = self.read_sentence()
                if not sentence:
                    continue
                replies.append(sentence)
                tag = sentence[0]
                if tag in ("!done", "!fatal"):
                    break
                # !trap may be followed by !done
                if tag == "!trap":
                    # continue until !done
                    continue
        finally:
            if old_timeout is not None and self.sock:
                self.sock.settimeout(old_timeout)
        return replies

    def _assert_ok(self, replies: list[list[str]], context: str = "") -> None:
        traps = [s for s in replies if s and s[0] == "!trap"]
        fatals = [s for s in replies if s and s[0] == "!fatal"]
        if fatals:
            raise RouterOSError(_trap_message(fatals[0]) or (context + " ناموفق"))
        if traps:
            raise RouterOSError(_trap_message(traps[0]) or (context + " ناموفق"))
        if not any(s and s[0] == "!done" for s in replies):
            raise RouterOSError(context + " بدون پاسخ !done" if context else "پاسخ API نامعتبر")

    def login(self, username: str, password: str) -> None:
        username = username or ""
        password = password or ""
        # ROS 6.43+ plaintext login
        replies = self.talk(["/login", f"=name={username}", f"=password={password}"])
        traps = [s for s in replies if s and s[0] == "!trap"]
        if not traps and any(s and s[0] == "!done" for s in replies):
            return

        # Older challenge-response login
        replies = self.talk(["/login"])
        chal = None
        for s in replies:
            for w in s:
                if w.startswith("=ret="):
                    chal = w[5:]
        if not chal:
            # first login may have already reported error
            if traps:
                raise RouterOSError(_trap_message(traps[0]) or "ورود API ناموفق")
            raise RouterOSError("ورود API ناموفق (challenge دریافت نشد)")
        md = hashlib.md5()
        md.update(b"\x00")
        md.update(password.encode("utf-8", errors="surrogateescape"))
        md.update(bytes.fromhex(chal))
        replies = self.talk(["/login", f"=name={username}", f"=response=00{md.hexdigest()}"])
        self._assert_ok(replies, "ورود API")

    def run_api_sentence(self, sentence: list[str]) -> list[list[str]]:
        replies = self.talk(sentence)
        self._assert_ok(replies, sentence[0] if sentence else "دستور")
        return replies

    def run_script(self, script: str) -> list[list[str]]:
        script = (script or "").strip()
        if not script:
            raise RouterOSError("اسکریپت خالی است")

        errors: list[str] = []
        lines = [ln.strip() for ln in script.replace("\r\n", "\n").split("\n")]
        lines = [ln for ln in lines if ln and not ln.startswith("#")]

        # 1) Try converting each terminal line to native API sentences
        api_sentences: list[list[str]] = []
        unparsed: list[str] = []
        for ln in lines:
            parsed = _parse_terminal_line(ln)
            if parsed:
                api_sentences.append(parsed)
            else:
                unparsed.append(ln)

        if api_sentences and not unparsed:
            all_replies: list[list[str]] = []
            for sent in api_sentences:
                try:
                    all_replies.extend(self.run_api_sentence(sent))
                except RouterOSError as e:
                    errors.append(f"{sent[0]}: {e}")
            if errors:
                raise RouterOSError("؛ ".join(errors))
            return all_replies

        # 2) /execute (works on many ROS versions for multi-line scripts)
        try:
            replies = self.talk(["/execute", f"=script={script}"])
            self._assert_ok(replies, "اجرای اسکریپت")
            return replies
        except RouterOSError as e:
            errors.append(f"/execute: {e}")

        # 3) Temporary system script add → run → remove
        name = f"push-{int(time.time()) % 100000}"
        try:
            # ignore remove errors if not exists
            try:
                self.talk(["/system/script/remove", f"=numbers={name}"])
            except Exception:
                pass
            replies = self.talk([
                "/system/script/add",
                f"=name={name}",
                f"=source={script}",
                "=dont-require-permissions=yes",
            ])
            self._assert_ok(replies, "ثبت اسکریپت")
            replies = self.talk(["/system/script/run", f"=number={name}"])
            self._assert_ok(replies, "اجرای اسکریپت")
            try:
                self.talk(["/system/script/remove", f"=numbers={name}"])
            except Exception:
                pass
            return replies
        except RouterOSError as e:
            errors.append(f"/system/script: {e}")
            try:
                self.talk(["/system/script/remove", f"=numbers={name}"])
            except Exception:
                pass

        # 4) Mixed: run parsed lines, then remaining via execute
        if api_sentences:
            for sent in api_sentences:
                try:
                    self.run_api_sentence(sent)
                except RouterOSError as e:
                    errors.append(f"{sent[0]}: {e}")
            if unparsed:
                remaining = "\n".join(unparsed)
                try:
                    replies = self.talk(["/execute", f"=script={remaining}"])
                    self._assert_ok(replies, "اجرای باقی‌مانده")
                except RouterOSError as e:
                    errors.append(str(e))
            if not errors:
                return []

        raise RouterOSError("؛ ".join(errors) if errors else "اجرای اسکریپت ناموفق")


def push_config(
    host: str,
    username: str,
    password: str,
    script: str,
    port: int = 8728,
    timeout: float = 15.0,
) -> dict:
    try:
        with RouterOSClient(host, port=port, timeout=timeout) as api:
            api.login(username, password)
            api.run_script(script)
        return {"ip": host, "ok": True, "error": None}
    except Exception as e:
        return {"ip": host, "ok": False, "error": str(e)[:400]}


def push_config_many(
    ips: list[str],
    username: str,
    password: str,
    script: str,
    port: int = 8728,
    timeout: float = 15.0,
) -> list[dict]:
    results = []
    for ip in ips:
        ip = str(ip).strip()
        if not ip:
            continue
        results.append(
            push_config(ip, username, password, script, port=port, timeout=timeout)
        )
    return results


def _sentences_to_text(replies: list[list[str]]) -> str:
    """Convert API reply sentences into a readable multi-line text block."""
    lines = []
    for sent in replies:
        if not sent:
            continue
        if sent[0] == "!re":
            attrs = []
            for w in sent[1:]:
                if w.startswith("="):
                    attrs.append(w[1:])
                elif w.startswith(".tag="):
                    continue
                else:
                    attrs.append(w)
            if attrs:
                lines.append("  " + "  ".join(attrs))
        elif sent[0] == "!done":
            continue
        elif sent[0] == "!trap":
            lines.append("TRAP: " + " ".join(sent[1:]))
        else:
            lines.append(" ".join(sent))
    return "\n".join(lines).strip()


def collect_ip_info(
    host: str,
    username: str,
    password: str,
    port: int = 8728,
    timeout: float = 15.0,
) -> dict:
    """Fetch /ip address, /ip route, /ip neighbor via API.

    Returns two text fields:
      ip_addresses  — combined /ip address + /ip route print
      ip_neighbors  — /ip neighbor print
    """
    try:
        with RouterOSClient(host, port=port, timeout=timeout) as api:
            api.login(username, password)
            addr_replies = api.talk(["/ip/address/print"])
            route_replies = api.talk(["/ip/route/print"])
            neigh_replies = api.talk(["/ip/neighbor/print"])
        addr_txt = _sentences_to_text(addr_replies)
        route_txt = _sentences_to_text(route_replies)
        neigh_txt = _sentences_to_text(neigh_replies)
        combined = ""
        if addr_txt:
            combined += "=== /ip address ===\n" + addr_txt + "\n"
        if route_txt:
            combined += "=== /ip route ===\n" + route_txt + "\n"
        return {
            "ip": host,
            "ok": True,
            "error": None,
            "ip_addresses": combined.strip(),
            "ip_neighbors": (("=== /ip neighbor ===\n" + neigh_txt) if neigh_txt else "").strip(),
        }
    except Exception as e:
        return {
            "ip": host,
            "ok": False,
            "error": str(e)[:400],
            "ip_addresses": "",
            "ip_neighbors": "",
        }


def collect_ip_info_many(
    ips: list[str],
    username: str,
    password: str,
    port: int = 8728,
    timeout: float = 15.0,
) -> list[dict]:
    results = []
    for ip in ips:
        ip = str(ip).strip()
        if not ip:
            continue
        results.append(
            collect_ip_info(ip, username, password, port=port, timeout=timeout)
        )
    return results


def fetch_wireless_info(
    host: str,
    username: str,
    password: str = "",
    port: int = 8728,
    timeout: float = 12.0,
) -> dict:
    """Read wireless interface modes via RouterOS API.

    Returns {"ok", "error", "text", "modes": [{"name","mode"}, ...], "device_type_hint"}.
    mode values include: ap-bridge, station, station-bridge, station-wds, ...
    """
    modes = []
    lines = []
    try:
        with RouterOSClient(host, port=port, timeout=timeout) as api:
            api.login(username, password or "")
            for path_cmd in ("/interface/wireless/print", "/interface/wifi/print"):
                try:
                    replies = api.talk([path_cmd])
                except Exception:
                    continue
                current = {}
                for sent in replies:
                    if not sent:
                        continue
                    if sent[0] == "!re":
                        current = {}
                        for w in sent[1:]:
                            if w.startswith("=") and "=" in w[1:]:
                                k, v = w[1:].split("=", 1)
                                current[k] = v
                        name = current.get("name") or current.get(".id") or ""
                        mode = (current.get("mode") or "").strip()
                        if name or mode:
                            modes.append({"name": name, "mode": mode})
                            lines.append(f"name={name}  mode={mode or '-'}")
                    elif sent[0] == "!done":
                        break
        text = ""
        if lines:
            text = "=== /interface wireless (API) ===\n" + "\n".join(lines)
        # classify hint from modes
        modes_l = " ".join((m.get("mode") or "").lower() for m in modes)
        hint = ""
        if any(x in modes_l for x in ("station-bridge", "station bridge", "station-wds", "station", "alignment-only")):
            # station* takes priority over ap
            if "station" in modes_l:
                hint = "ST"
        if not hint and any(x in modes_l for x in ("ap-bridge", "ap", "bridge")):
            # plain "bridge" alone is weak; prefer ap-bridge
            if "ap-bridge" in modes_l or " ap" in f" {modes_l}":
                hint = "AP"
        if not hint and modes:
            # any wireless present without clear mode
            if "station" in modes_l:
                hint = "ST"
            elif modes_l.strip():
                hint = "AP"
        return {"ok": True, "error": None, "text": text, "modes": modes, "device_type_hint": hint}
    except Exception as e:
        return {"ok": False, "error": str(e)[:400], "text": "", "modes": [], "device_type_hint": ""}


def _re_attrs(sentence: list[str]) -> dict:
    out = {}
    for w in sentence[1:]:
        if w.startswith("=") and "=" in w[1:]:
            k, v = w[1:].split("=", 1)
            out[k] = v
    return out


def _print_table(api: "RouterOSClient", path: str) -> list[dict]:
    rows = []
    try:
        replies = api.talk([path])
    except Exception:
        return rows
    for sent in replies:
        if not sent:
            continue
        if sent[0] == "!re":
            rows.append(_re_attrs(sent))
        elif sent[0] == "!done":
            break
    return rows



def export_device_rsc(
    host: str,
    username: str,
    password: str = "",
    port: int = 8728,
    timeout: float = 20.0,
) -> dict:
    """Run /export and return its text file using the RouterOS API."""
    import uuid as _uuid

    remote_base = "olom_export_" + _uuid.uuid4().hex[:12]
    remote_file = remote_base + ".rsc"
    identity = host
    payload = b""
    file_id = None
    with RouterOSClient(host, port=port, timeout=timeout) as api:
        api.login(username, password or "")
        identities = _print_table(api, "/system/identity/print")
        if identities and identities[0].get("name"):
            identity = identities[0]["name"].strip() or host
        api.run_api_sentence(["/export", f"=file={remote_base}"])
        try:
            replies = api.talk([
                "/file/print",
                "=.proplist=.id,name,size,contents",
                f"?name={remote_file}",
            ])
            api._assert_ok(replies, "خواندن فایل Export")
            rows = [_re_attrs(sent) for sent in replies if sent and sent[0] == "!re"]
            if not rows:
                raise RouterOSError("فایل Export ساخته نشد یا محتوای آن قابل خواندن نیست")
            row = rows[0]
            file_id = row.get(".id")
            contents = row.get("contents") or ""
            try:
                expected_size = int(row.get("size") or 0)
            except (TypeError, ValueError):
                expected_size = 0
            if contents:
                payload = contents.encode("utf-8")
            # RouterOS versions exposing /file/read can return large files in chunks.
            if not payload or (expected_size and len(payload) < expected_size):
                chunks = []
                offset = 0
                max_chunks = max(1, min(4096, (max(expected_size, 1) // 32768) + 2))
                for _ in range(max_chunks):
                    try:
                        chunk_replies = api.talk([
                            "/file/read",
                            f"=file={remote_file}",
                            f"=offset={offset}",
                            "=chunk-size=32768",
                        ])
                        api._assert_ok(chunk_replies, "خواندن بخش فایل Export")
                    except Exception:
                        break
                    data = ""
                    for sent in chunk_replies:
                        if sent and sent[0] == "!re":
                            data = _re_attrs(sent).get("data", "")
                            break
                    if not data:
                        break
                    encoded = data.encode("utf-8")
                    chunks.append(encoded)
                    offset += len(encoded)
                    if len(encoded) < 32768:
                        break
                if chunks:
                    payload = b"".join(chunks)
            if not payload:
                raise RouterOSError(
                    "فایل Export خالی است یا نسخه RouterOS اجازه خواندن محتوای فایل را نداد"
                )
            return {"ip": host, "identity": identity, "content": payload}
        finally:
            # Only remove the uniquely named temporary file created by this request.
            try:
                if file_id:
                    api.run_api_sentence(["/file/remove", f"=numbers={file_id}"])
                else:
                    for item in _print_table(api, "/file/print"):
                        if item.get("name") == remote_file and item.get(".id"):
                            api.run_api_sentence(["/file/remove", f"=numbers={item['.id']}"])
                            break
            except Exception:
                pass


def probe_device_via_api(
    host: str,
    username: str,
    password: str = "",
    port: int = 8728,
    timeout: float = 15.0,
) -> dict:
    """Full device read via RouterOS API for DB update.

    Collects identity, interfaces, wireless modes, IP addresses, routes, neighbors.
    """
    device_log = ""
    mac_info = ""
    try:
        with RouterOSClient(host, port=port, timeout=timeout) as api:
            api.login(username, password or "")

            # identity
            identity = ""
            for row in _print_table(api, "/system/identity/print"):
                identity = (row.get("name") or "").strip()
                if identity:
                    break

            # interfaces (+ MAC)
            ifaces = _print_table(api, "/interface/print")
            iface_lines = []
            mac_lines = []
            for i, row in enumerate(ifaces, 1):
                n = row.get("name") or ""
                typ = row.get("type") or ""
                run = row.get("running") or row.get("disabled") or ""
                mac = (row.get("mac-address") or row.get("mac-address") or "").strip()
                iface_lines.append(f"{i:3d}  name={n}  type={typ}  running={run}  mac={mac or '-'}")
                if mac and mac.upper() not in ("00:00:00:00:00:00", ""):
                    mac_lines.append(f"{n}  {mac}  ({typ})")
            interfaces_text = ("=== /interface ===\n" + "\n".join(iface_lines)).strip() if iface_lines else ""
            # also ARP for additional MACs
            try:
                arps = _print_table(api, "/ip/arp/print")
                arp_extra = []
                for j, row in enumerate(arps[:100], 1):
                    am = (row.get("mac-address") or "").strip()
                    aip = row.get("address") or ""
                    aif = row.get("interface") or ""
                    if am:
                        arp_extra.append(f"{aif or '-'}  {am}  (arp {aip})")
                if arp_extra:
                    mac_lines.append("--- /ip arp ---")
                    mac_lines.extend(arp_extra)
            except Exception:
                pass
            mac_info = ("=== MAC addresses ===\n" + "\n".join(mac_lines)).strip() if mac_lines else ""

            # wireless (legacy + wifiwave2)
            wl_lines = []
            modes = []
            for path_cmd in ("/interface/wireless/print", "/interface/wifi/print"):
                for row in _print_table(api, path_cmd):
                    n = row.get("name") or ""
                    mode = (row.get("mode") or "").strip()
                    ssid = row.get("ssid") or row.get("configuration.ssid") or ""
                    band = row.get("band") or ""
                    freq = row.get("frequency") or ""
                    modes.append({"name": n, "mode": mode})
                    wl_lines.append(
                        f"name={n}  mode={mode or '-'}  ssid={ssid or '-'}  band={band or '-'}  frequency={freq or '-'}"
                    )
            wireless_text = ("=== /interface wireless ===\n" + "\n".join(wl_lines)).strip() if wl_lines else ""

            # IP addresses
            addrs = _print_table(api, "/ip/address/print")
            addr_lines = []
            for i, row in enumerate(addrs, 1):
                addr_lines.append(
                    f"{i:3d}  address={row.get('address') or '-'}  interface={row.get('interface') or '-'}  network={row.get('network') or '-'}"
                )
            ip_addresses = ("=== /ip address ===\n" + "\n".join(addr_lines)).strip() if addr_lines else ""

            # routes (compact)
            routes = _print_table(api, "/ip/route/print")
            route_lines = []
            for i, row in enumerate(routes[:80], 1):
                route_lines.append(
                    f"{i:3d}  dst={row.get('dst-address') or '-'}  gw={row.get('gateway') or '-'}  distance={row.get('distance') or '-'}"
                )
            if route_lines:
                ip_addresses = (ip_addresses + "\n\n=== /ip route ===\n" + "\n".join(route_lines)).strip()

            # neighbors
            neigh = _print_table(api, "/ip/neighbor/print")
            neigh_lines = []
            for i, row in enumerate(neigh[:80], 1):
                neigh_lines.append(
                    f"{i:3d}  identity={row.get('identity') or '-'}  address={row.get('address') or '-'}  interface={row.get('interface') or '-'}"
                )
            ip_neighbors = ("=== /ip neighbor ===\n" + "\n".join(neigh_lines)).strip() if neigh_lines else ""

            # system clock (for log time offset correction)
            from datetime import datetime, timezone as _tz
            server_now_utc = datetime.now(_tz.utc)
            device_now = None
            try:
                clock_rows = _print_table(api, "/system/clock/print")
                if clock_rows:
                    cr = clock_rows[0]
                    device_now = _parse_ros_clock(cr.get("date") or "", cr.get("time") or "")
            except Exception:
                device_now = None

            # system log (last entries) — times corrected to Tehran / Jalali
            try:
                logs = _print_table(api, "/log/print")
                device_log = _format_device_logs(logs, device_now, server_now_utc) if logs else ""
            except Exception:
                device_log = ""

        # device type from wireless modes
        modes_l = " ".join((m.get("mode") or "").lower() for m in modes)
        if any(x in modes_l for x in ("station-bridge", "station bridge", "station-wds", "station")):
            device_type = "ST"
        elif any(x in modes_l for x in ("ap-bridge", "ap bridge", "ap_bridge")) or (
            modes and "ap" in modes_l
        ):
            device_type = "AP"
        elif modes:
            device_type = "AP"
        else:
            # no wireless interfaces in wireless tables — router
            device_type = "Router"
            # still check interface types for wireless-like names
            for line in iface_lines:
                low = line.lower()
                if any(k in low for k in ("wlan", "wifi", "wireless")):
                    device_type = "AP"
                    break

        return {
            "ip": host,
            "ok": True,
            "error": None,
            "device_name": identity,
            "interfaces": interfaces_text,
            "wireless_info": wireless_text,
            "ip_addresses": ip_addresses,
            "ip_neighbors": ip_neighbors,
            "device_type": device_type,
            "device_log": device_log,
            "mac_info": mac_info,
            "modes": modes,
        }
    except Exception as e:
        return {
            "ip": host,
            "ok": False,
            "error": str(e)[:400],
            "device_name": "",
            "interfaces": "",
            "wireless_info": "",
            "ip_addresses": "",
            "ip_neighbors": "",
            "device_type": "",
            "device_log": "",
            "mac_info": "",
            "modes": [],
        }


def probe_devices_via_api_many(
    ips: list[str],
    username: str,
    password: str = "",
    port: int = 8728,
    timeout: float = 15.0,
    cancel_event=None,
    progress: dict | None = None,
) -> list[dict]:
    results = []
    clean = [str(x).strip() for x in ips if str(x).strip()]
    if progress is not None:
        progress.update({"total": len(clean), "done": 0, "current_ip": "", "running": True, "canceled": False})
    try:
        for ip in clean:
            if cancel_event is not None and cancel_event.is_set():
                if progress is not None:
                    progress["canceled"] = True
                break
            if progress is not None:
                progress["current_ip"] = ip
            results.append(
                probe_device_via_api(ip, username, password, port=port, timeout=timeout)
            )
            if progress is not None:
                progress["done"] = len(results)
    finally:
        if progress is not None:
            progress["running"] = False
            progress["current_ip"] = ""
    return results

