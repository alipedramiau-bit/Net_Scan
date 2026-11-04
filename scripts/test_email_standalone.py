"""Task 39 — ایمیل‌سرور مستقل (بدون جیمیل/یاهو): رفع اشکالات + diagnose + راهنما.

بررسی‌ها:
1) پارسر DNS MX: پاسخ سنتتیک (با pointer فشرده‌سازی + TC flag)؛
2) _system_nameservers / _auto_helo / _effective_helo؛
3) save_config: اعتبارسنجی From/To (مثل «ali pedram» → ValueError)؛
4) send_mail: احترام به فلگ enabled؛ send_direct: ورودی نامعتبر؛
5) diagnose_direct با resolve و socket موک‌شده (open/blocked)؛
6) اندپوینت‌ها با TestClient: GET/PUT config (400 برای From نامعتبر)،
   /api/smtp/diagnose (400 ایمیل بد، 200 با شکل درست)؛
7) سورس فرانت: دکمهٔ «مستقل»، «بررسی امکان ارسال مستقیم»، راهنمای email-guide؛
8) CSS: .email-guide و .email-diag؛
9) بازیابی کامل smtp_config.json اصلی در پایان.
"""
import os, sys, tempfile
from pathlib import Path

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "backend"))

ok = True
def check(label, cond, extra=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label, extra)
    ok = ok and bool(cond)

# ---------- آماده‌سازی: ایزوله‌سازی فایل کانفیگ ----------
import email_manager as em

_cfg_path = em._CONFIG
_orig_bytes = _cfg_path.read_bytes() if _cfg_path.exists() else None
_tmpdir = tempfile.mkdtemp(prefix="smtpcfg39_")
em._CONFIG = Path(_tmpdir) / "smtp_config.json"
_orig_resolve = em.resolve_mx_full
_orig_create_conn = em.socket.create_connection

def cleanup():
    try:
        em._CONFIG = _cfg_path
        mem._CONFIG = _cfg_path
        if _orig_bytes is not None:
            _cfg_path.write_bytes(_orig_bytes)
        elif _cfg_path.exists():
            os.remove(_cfg_path)
        em.resolve_mx_full = _orig_resolve
        mem.resolve_mx_full = _orig_resolve
        em.socket.create_connection = _orig_create_conn
    except Exception as e:
        print("cleanup warn:", e)

# ---------- 1) پارسر DNS ----------
import struct

def _nb(host):
    out = b""
    for l in host.split("."):
        out += bytes([len(l)]) + l.encode()
    return out + b"\x00"

def synth_response(domain, records, tid=0x1234, tc=False, ptr_owner=True):
    qname = _nb(domain)
    flags = 0x8180 | (0x0200 if tc else 0)
    header = struct.pack("!HHHHHH", tid, flags, 1, len(records), 0, 0)
    question = qname + struct.pack("!HH", 15, 1)
    answers = b""
    for pref, host in records:
        rd = struct.pack("!H", pref) + _nb(host)
        owner = b"\xc0\x0c" if ptr_owner else _nb("owner." + domain)
        answers += owner + struct.pack("!HHIH", 15, 1, 300, len(rd)) + rd
    return header + question + answers

recs, tc = em._parse_dns_mx_response(synth_response("example.com", [(10, "mx1.example.com"), (20, "mx2.example.org")]), 0x1234)
check("dns: parse two MX (compressed owner)", recs == [(10, "mx1.example.com"), (20, "mx2.example.org")] and tc is False, str(recs))
recs2, tc2 = em._parse_dns_mx_response(synth_response("example.com", [(5, "a.mx.example.net")], tc=True), 0x1234)
check("dns: TC flag surfaced", tc2 is True and recs2 == [(5, "a.mx.example.net")], f"tc={tc2}")
recs3, _ = em._parse_dns_mx_response(synth_response("example.com", [(15, "b.mx.example.com")], tid=0x9999), 0x1234)
check("dns: tid mismatch -> empty", recs3 == [], str(recs3))
packet, tid2 = em._dns_packet("test.example.ir")
check("dns: packet builder shape", packet.endswith(struct.pack("!HH", 15, 1)) and packet[12:13] == bytes([4]), f"tid={tid2}")

# ---------- 2) سیستم‌ریزالور و HELO ----------
ns = em._system_nameservers()
check("dns: system nameservers list", isinstance(ns, list), str(ns))
h = em._auto_helo()
check("helo: auto identity non-empty", isinstance(h, str) and len(h) > 3, h)
check("helo: empty -> auto (not .local)", ".local" not in em._effective_helo("").lower(), em._effective_helo(""))
check("helo: shabakeban.local -> auto", ".local" not in em._effective_helo("shabakeban.local").lower())
check("helo: custom preserved", em._effective_helo("mail.mysite.ir") == "mail.mysite.ir")

# ---------- 3) save_config: اعتبارسنجی ----------
try:
    em.save_config({"from_email": "ali pedram"})
    check("save: invalid From rejected", False)
except ValueError as e:
    check("save: invalid From rejected", True, str(e)[:60])

d = em.save_config({"mode": "direct", "enabled": True, "from_email": "alerts@my-domain.ir",
                    "to_email": "user@example.com", "helo_host": ""})
check("save: valid direct config saved", d.get("mode") == "direct" and d.get("enabled") is True, str(d)[:120])
check("save: password masked/absent", d.get("password") == "" or d.get("password") == "********")
try:
    em.save_config({"to_email": "not an email"})
    check("save: invalid To rejected", False)
except ValueError:
    check("save: invalid To rejected", True)

# ---------- 4) enabled + ورودی‌های نامعتبر ----------
try:
    em.save_config({"enabled": False})
    em.send_mail(subject="x", body="y", to_email="user@example.com")
    check("send_mail: disabled -> error", False)
except ValueError as e:
    check("send_mail: disabled -> error", "غیرفعال" in str(e), str(e)[:70])

try:
    em.send_direct("s", "b", from_email="ali pedram", from_name="x", dest="user@example.com")
    check("send_direct: bad From rejected", False)
except ValueError as e:
    check("send_direct: bad From rejected", True, str(e)[:60])
try:
    em.send_direct("s", "b", from_email="a@b.ir", from_name="x", dest="bad-dest")
    check("send_direct: bad dest rejected", False)
except ValueError:
    check("send_direct: bad dest rejected", True)

# دامنهٔ بی‌MX: باید خطای شفاف بدهد (بدون شبکهٔ واقعی — موک خالی)
em.resolve_mx_full = lambda domain, timeout=5.0: []
try:
    em.send_direct("s", "b", from_email="a@b.ir", from_name="x", dest="u@no-mx.invalid")
    check("send_direct: no-MX -> clear error", False)
except ValueError as e:
    check("send_direct: no-MX -> clear error", "MX" in str(e), str(e)[:80])

# ---------- 5) diagnose_direct موک‌شده ----------
class _FakeSock:
    def __enter__(self): return self
    def __exit__(self, *a): return False

def _mk_diag(open_ports):
    def fake_conn(host_port_pair, timeout=None):
        host, port = host_port_pair
        if (host, port) in open_ports:
            return _FakeSock()
        raise OSError("blocked")
    return fake_conn

em.resolve_mx_full = lambda domain, timeout=8.0: [(10, "mx1.test.ir"), (20, "mx2.test.ir")]

em.socket.create_connection = _mk_diag({("mx1.test.ir", 25)})
d = em.diagnose_direct("user@dest.ir", timeout=3)
check("diag: port25 open detected", d["port25_open"] is True and d["ok"] is True, str(d["checks"]))
check("diag: verdict mentions مستقل", "مستقل" in d["verdict"])
check("diag: helo suggestion present", bool(d["helo_suggestion"]), d["helo_suggestion"])

em.socket.create_connection = _mk_diag(set())
d2 = em.diagnose_direct("user@dest.ir", timeout=3)
check("diag: all blocked -> port25_open false", d2["port25_open"] is False)
check("diag: blocked verdict mentions VPS/رله", "VPS" in d2["verdict"] and "رله" in d2["verdict"])

em.resolve_mx_full = lambda domain, timeout=8.0: []
d3 = em.diagnose_direct("user@unknown.ir", timeout=3)
check("diag: no MX -> verdict explains", not d3["mx"] and "MX" in d3["verdict"])
try:
    em.diagnose_direct("bad-email")
    check("diag: invalid email rejected", False)
except ValueError:
    check("diag: invalid email rejected", True)

em.resolve_mx_full = _orig_resolve
em.socket.create_connection = _orig_create_conn

# ---------- 6) اندپوینت‌ها ----------
from fastapi.testclient import TestClient
import main as appm
mem = appm.email_manager  # نمونهٔ واقعی استفاده‌شده در main (ممکن است backend.email_manager باشد)
mem._CONFIG = Path(_tmpdir) / "smtp_config.json"  # ایزوله‌سازی همان فایل موقت
client = TestClient(appm.app)
_r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
assert _r.status_code == 200, f"login failed: {_r.status_code}"

r = client.get("/api/smtp/config")
check("ep: GET config 200", r.status_code == 200, r.text[:100])
check("ep: config shape", r.json().get("mode") in ("direct", "relay") and "enabled" in r.json())

r = client.put("/api/smtp/config", json={"from_email": "ali pedram"})
check("ep: PUT invalid From -> 400", r.status_code == 400, r.text[:120])

r = client.put("/api/smtp/config", json={"mode": "direct", "enabled": True,
                                         "from_email": "alerts@net.local", "to_email": "dest@example.com",
                                         "helo_host": "", "port": 587, "timeout": 30})
check("ep: PUT valid direct -> 200", r.status_code == 200, r.text[:150])
check("ep: PUT returns direct mode", r.json().get("mode") == "direct")

r = client.post("/api/smtp/diagnose", json={"to_email": "not-an-email"})
check("ep: diagnose bad email -> 400", r.status_code == 400, r.text[:120])

em.resolve_mx_full = lambda domain, timeout=8.0: [(10, "mx1.test.ir")]
mem.resolve_mx_full = em.resolve_mx_full
mem.socket.create_connection = _mk_diag(set())
r = client.post("/api/smtp/diagnose", json={"to_email": "user@dest.ir"})
check("ep: diagnose valid -> 200", r.status_code == 200, r.text[:150])
dj = r.json()
check("ep: diagnose shape", all(k in dj for k in ("domain", "mx", "checks", "port25_open", "verdict")))
check("ep: diagnose domain parsed", dj.get("domain") == "dest.ir")
check("ep: mocked mx used", (dj.get("mx") or [{}])[0].get("host") == "mx1.test.ir", str(dj.get("mx")))
em.resolve_mx_full = _orig_resolve
mem.resolve_mx_full = _orig_resolve
em.socket.create_connection = _orig_create_conn

# ---------- 7) سورس فرانت ----------
src = open(os.path.join(ROOT, "frontend", "src.jsx"), encoding="utf-8").read()
check("src: standalone preset button", "مستقل — بدون جیمیل/یاهو" in src and "applyStandalone" in src)
check("src: applyStandalone sets direct+enabled", 'mode:"direct",enabled:true' in src)
check("src: diagnose button", "بررسی امکان ارسال مستقیم" in src and "/api/smtp/diagnose" in src)
check("src: diag result box", 'className={"email-diag"' in src and "port25_open" in src)
check("src: guide section", "email-guide" in src and "راهنمای استفاده — ارسال مستقل بدون جیمیل/یاهو" in src)
check("src: guide covers how-it-works", "رکورد MX دامنهٔ گیرنده" in src and "پورت خروجی ۲۵" in src)
check("src: guide troubleshooting", "اسپم" in src and "5.7.1" in src and "VPS" in src)
check("src: load no longer overrides tls flags", "use_tls:port!==465" not in src)

# ---------- 8) CSS ----------
css = open(os.path.join(ROOT, "frontend", "style.css"), encoding="utf-8").read()
check("css: .email-guide styled", ".email-guide{" in css and ".email-guide summary{" in css)
check("css: .email-diag styled", ".email-diag{" in css and ".email-diag.ok{" in css and ".email-diag.bad{" in css)

# ---------- 9) بازیابی ----------
cleanup()
check("cleanup: original smtp_config.json restored",
      (_orig_bytes is None and not os.path.exists(str(_cfg_path))) or _cfg_path.read_bytes() == _orig_bytes)

print("\nALL OK" if ok else "\nFAILURES PRESENT")
sys.exit(0 if ok else 1)
