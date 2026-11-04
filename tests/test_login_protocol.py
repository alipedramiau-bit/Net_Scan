"""Task 37 — تست پروتکل ورود RouterOS با «سرور API تقلبی» روی سوکت واقعی.

چرا؟ خطای کاربر «ورود API ناموفق (invalid user name or password (6))» پیام خام
خودِ روتر است؛ باید مطمئن شویم کلاینتِ پروژه:
1) ورود plaintext (ROS 6.43+) را درست انجام می‌دهد؛
2) با روترهای قدیمی (چالش-پاسخ MD5) هم کار می‌کند — تلاش دوم؛
3) تلاش دوم روی «اتصال تازه» انجام می‌شود (رفتار قدیم: روی همان اتصالِ بعد از
   trap تلاش می‌کرد و نسخه‌هایی که نشست را می‌بندند از کار می‌افتادند)؛
4) وقتی روتر پیام صریح می‌دهد (invalid user name or password (6))، همان پیام
   بدون قلم‌شدن به بالا می‌آید تا عیب‌یابی ممکن باشد.

هیچ دستگاه واقعی‌ای لمس نمی‌شود — سرور تقلبی روی 127.0.0.1 با پروتکل صحیح
(کلمات با پیشوند طول، جمله با word صفر-طول) پاسخ می‌دهد.
"""
import hashlib
import os
import socket
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.routeros_api import RouterOSClient, RouterOSError

USER, PASS = "garnaf", "1234"


# ------------------------- کدگذاری پروتکل ----------------------------------
def _enc_len(n: int) -> bytes:
    if n < 0x80:
        return bytes([n])
    if n < 0x4000:
        return bytes([0x80 | (n >> 8), n & 0xFF])
    if n < 0x200000:
        return bytes([0xC0 | (n >> 16), (n >> 8) & 0xFF, n & 0xFF])
    return bytes([0xE0 | (n >> 24), (n >> 16) & 0xFF, (n >> 8) & 0xFF, n & 0xFF])


def _enc_word(w: str) -> bytes:
    data = w.encode("utf-8")
    return _enc_len(len(data)) + data


def _enc_sentence(words) -> bytes:
    return b"".join(_enc_word(w) for w in words) + b"\x00"


def _recv_exact(sock, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("closed")
        buf += chunk
    return buf


def _recv_len(sock) -> int:
    b = _recv_exact(sock, 1)[0]
    if b & 0x80 == 0:
        return b
    if b & 0xC0 == 0x80:
        return ((b & 0x7F) << 8) + _recv_exact(sock, 1)[0]
    if b & 0xE0 == 0xC0:
        o = _recv_exact(sock, 2)
        return ((b & 0x1F) << 16) + (o[0] << 8) + o[1]
    if b & 0xF0 == 0xE0:
        o = _recv_exact(sock, 3)
        return ((b & 0x0F) << 24) + (o[0] << 16) + (o[1] << 8) + o[2]
    o = _recv_exact(sock, 4)
    return (o[0] << 24) + (o[1] << 16) + (o[2] << 8) + o[3]


def _recv_sentence(sock) -> list[str]:
    words: list[str] = []
    while True:
        ln = _recv_len(sock)
        if ln == 0:
            return words
        words.append(_recv_exact(sock, ln).decode("utf-8", errors="replace"))


def _get(sentence: list[str], key: str) -> str:
    for w in sentence:
        if w.startswith(key + "="):
            return w[len(key) + 1:]
    return ""


# ------------------------- سرور تقلبی --------------------------------------
class FakeRosServer:
    """سرور RouterOS API تقلبی با حالت‌های رفتاری مختلف.

    - mode="v7": ورود plaintext استاندارد؛ رمز غلط → trap «invalid user name or password (6)».
    - mode="v6old": plaintext با =password= پذیرفته نمی‌شود؛ فقط چالش-پاسخ MD5.
    - mode="reject-close": هر plaintext login رد می‌شود و بلافاصله اتصال بسته
      می‌شود (شبیه نسخه‌هایی که بعد از ورود ناموفق نشست را می‌بندند) — چالش-پاسخ
      روی اتصال بعدی درست جواب می‌دهد.
    - mode="no-challenge": plaintext رد می‌شود و bare /login هم چالش نمی‌دهد
      (فقط trap) — کلاینت باید پیام trap اول را حفظ کند.
    """

    def __init__(self, mode: str):
        self.mode = mode
        self._srv = socket.socket()
        self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._srv.bind(("127.0.0.1", 0))
        self._srv.listen(8)
        self.port = self._srv.getsockname()[1]
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def close(self):
        self._stop.set()
        try:
            self._srv.close()
        except OSError:
            pass

    def _serve(self):
        while not self._stop.is_set():
            try:
                conn, _ = self._srv.accept()
            except OSError:
                return
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _send(self, conn, *sentences):
        for s in sentences:
            conn.sendall(_enc_sentence(s))

    def _handle(self, conn):
        try:
            challenge = os.urandom(16).hex()
            conn.settimeout(5)
            while True:
                try:
                    sentence = _recv_sentence(conn)
                except (ConnectionError, OSError, IndexError):
                    return
                if not sentence:
                    return
                cmd = sentence[0]
                if cmd != "/login":
                    self._send(conn, ["!trap", "=message=no such command"], ["!done"])
                    continue
                name = _get(sentence, "=name")
                password = _get(sentence, "=password")
                response = _get(sentence, "=response")
                mode = self.mode

                if mode == "v7":
                    if "=password=" in str(sentence):
                        if name == USER and password == PASS:
                            self._send(conn, ["!done"])
                        else:
                            self._send(conn, ["!trap", "=message=invalid user name or password (6)"],
                                       ["!done"])
                        continue
                    if response:
                        # پس از چالش — باید همان حساب درست باشد
                        md5 = hashlib.md5(b"\x00" + PASS.encode() + bytes.fromhex(challenge)).hexdigest()
                        if response == "00" + md5:
                            self._send(conn, ["!done"])
                        else:
                            self._send(conn, ["!trap", "=message=invalid user name or password (6)"],
                                       ["!done"])
                        continue
                    self._send(conn, ["!done", f"=ret={challenge}"])
                    continue

                if mode == "v6old":
                    if "=password=" in str(sentence):
                        self._send(conn, ["!trap", "=message=no such command or parameter (password)"],
                                   ["!done"])
                        continue
                    if response:
                        md5 = hashlib.md5(b"\x00" + PASS.encode() + bytes.fromhex(challenge)).hexdigest()
                        if name == USER and response == "00" + md5:
                            self._send(conn, ["!done"])
                        else:
                            self._send(conn, ["!trap", "=message=invalid user name or password (6)"],
                                       ["!done"])
                        continue
                    self._send(conn, ["!done", f"=ret={challenge}"])
                    continue

                if mode == "reject-close":
                    if "=password=" in str(sentence):
                        # فقط ورود plaintext رد می‌شود و نشست بسته می‌شود؛
                        # درخواست چالش در اتصال بعدی سالم پاسخ داده می‌شود
                        self._send(conn, ["!trap", "=message=invalid user name or password (6)"], ["!done"])
                        return
                    if response:
                        md5 = hashlib.md5(b"\x00" + PASS.encode() + bytes.fromhex(challenge)).hexdigest()
                        if response == "00" + md5:
                            self._send(conn, ["!done"])
                        else:
                            self._send(conn, ["!trap", "=message=invalid user name or password (6)"], ["!done"])
                        continue
                    self._send(conn, ["!done", f"=ret={challenge}"])
                    continue

                if mode == "no-challenge":
                    self._send(conn, ["!trap", "=message=invalid user name or password (6)"], ["!done"])
                    continue
        except (OSError, ValueError):
            return
        finally:
            try:
                conn.close()
            except OSError:
                pass


def _client(port: int) -> RouterOSClient:
    return RouterOSClient("127.0.0.1", port=port, timeout=5.0, connect_timeout=5.0)


# ------------------------- تست‌ها ------------------------------------------
def test_login_plaintext_ok_v7():
    srv = FakeRosServer("v7")
    try:
        cli = _client(srv.port)
        cli.connect()
        cli.login(USER, PASS)  # نباید exception بدهد
        cli.close()
    finally:
        srv.close()


def test_login_wrong_creds_reports_raw_router_message():
    srv = FakeRosServer("v7")
    try:
        cli = _client(srv.port)
        cli.connect()
        with pytest.raises(RouterOSError) as ei:
            cli.login(USER, "wrong-pass")
        # پیام خام روتر حفظ شود — همان چیزی که کاربر در اسکرین‌شات دید («(6)»)
        assert "invalid user name or password (6)" in str(ei.value)
        cli.close()
    finally:
        srv.close()


def test_login_old_router_challenge_fallback_ok():
    """روتر قدیمی: plaintext پذیرفته نیست؛ روش چالش-پاسخ باید جواب دهد."""
    srv = FakeRosServer("v6old")
    try:
        cli = _client(srv.port)
        cli.connect()
        cli.login(USER, PASS)  # از مسیر چالش-پاسخ
        cli.close()
    finally:
        srv.close()


def test_login_fallback_runs_on_fresh_connection():
    """رفع باگ Task 37: برخی روترها بعد از ورود ناموفق نشست را می‌بندند —
    تلاش دوم باید روی اتصال تازه انجام شود و موفق شود."""
    srv = FakeRosServer("reject-close")
    try:
        cli = _client(srv.port)
        cli.connect()
        cli.login(USER, PASS)  # plaintext رد و اتصال بسته می‌شود؛ fallback روی اتصال تازه
        cli.close()
    finally:
        srv.close()


def test_login_no_challenge_keeps_first_trap_message():
    """اگر چالش هم داده نشد، پیام trap اول (علت واقعی) گم نشود."""
    srv = FakeRosServer("no-challenge")
    try:
        cli = _client(srv.port)
        cli.connect()
        with pytest.raises(RouterOSError) as ei:
            cli.login(USER, PASS)
        assert "invalid user name or password (6)" in str(ei.value)
        assert "challenge دریافت نشد" not in str(ei.value)
        cli.close()
    finally:
        srv.close()


def test_login_reconnect_failure_still_reports_first_trap():
    """اگر اتصال دوم ممکن نشد، همان پیام trap اول بالا بیاید (نه خطای اتصال دوم)."""
    srv = FakeRosServer("reject-close")
    try:
        cli = _client(srv.port)
        cli.connect()
        srv.close()  # سرور دیگر اتصال تازه نمی‌پذیرد
        with pytest.raises(RouterOSError) as ei:
            cli.login(USER, PASS)
        assert "invalid user name or password (6)" in str(ei.value)
        cli.close()
    finally:
        srv.close()
