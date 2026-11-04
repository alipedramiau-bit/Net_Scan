"""Task 41 — احراز هویت دامنه: DKIM بدون وابستگی + SPF/DMARC/rDNS + ارسال فقط پورت ۲۵.

A) RSA keygen/parse roundtrip + کنترل متقابل با cryptography؛
B) امضای DKIM → تأیید با dkimpy (درست/دستکاری‌شده/کلید غلط، تک‌بخشی و multipart)؛
C) هدر DKIM verbatim روی سیم (بدون RFC2047)؛
D) پارسر DNS برای TXT/PTR با پاکت مصنوعی؛
E) ارزیاب SPF (ip4/none/fail/include/softfail)؛
F) فیلدهای dkim در save/get config (ماسک/حفظ/پاک‌کردن)؛
G) send_direct فقط پورت ۲۵ + امضا + خطای صریح کلید نبودن؛
H) پیام خطای هدفمند 5.7.26 (و رگرسیون Task40-F)؛
I) dkim_generate + auth_diagnostics + اندپوینت‌های HTTP + هشدار دامنهٔ سرویس‌دهنده؛
J) سورس فرانت و CSS.
"""
import base64, os, smtplib, struct, sys, tempfile, time
from pathlib import Path

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT))          # برای پکیج backend (import main → backend/main.py باید اول باشد)
sys.path.insert(0, os.path.join(ROOT, "backend"))

ok = True
def check(label, cond, extra=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label, extra)
    ok = ok and bool(cond)

import email_manager as em

# ---------- ایزوله‌سازی کانفیگ ----------
_cfg_path = em._CONFIG
_orig_bytes = _cfg_path.read_bytes() if _cfg_path.exists() else None
_tmpdir = tempfile.mkdtemp(prefix="smtpcfg41_")
em._CONFIG = Path(_tmpdir) / "smtp_config.json"
_orig = {}
def _patch(name, val):
    _orig[name] = em.__dict__.get(name)
    setattr(em, name, val)
def _restore():
    for n, v in _orig.items():
        if v is not None:
            setattr(em, n, v)
        elif n in em.__dict__:
            delattr(em, n)

def cleanup():
    try:
        _restore()
        em._CONFIG = _cfg_path
        if _orig_bytes is not None:
            _cfg_path.write_bytes(_orig_bytes)
        elif _cfg_path.exists():
            os.remove(_cfg_path)
    except Exception as e:
        print("cleanup warn:", e)

# ---------- A) RSA keygen/parse + کنترل متقابل cryptography ----------
t0 = time.time()
k = em._generate_rsa_keypair(1024)
gen_s = time.time() - t0
check("A1: keygen 1024 fast & sized", 1024 == k["n"].bit_length() and gen_s < 10, f"{gen_s:.2f}s")
pem8 = em._pem_encode("PRIVATE KEY", em._pkcs8_der(k))
pem1 = em._pem_encode("RSA PRIVATE KEY", em._der_seq(
    em._der_int(0), em._der_int(k["n"]), em._der_int(k["e"]), em._der_int(k["d"]),
    em._der_int(k["p"]), em._der_int(k["q"]), em._der_int(k["dp"]),
    em._der_int(k["dq"]), em._der_int(k["qinv"])))
k8, k1 = em._parse_rsa_private_pem(pem8), em._parse_rsa_private_pem(pem1)
check("A2: PKCS#8 parse roundtrip", (k8["n"], k8["e"], k8["d"]) == (k["n"], k["e"], k["d"]))
check("A3: PKCS#1 parse roundtrip", (k1["n"], k1["e"], k1["d"]) == (k["n"], k["e"], k["d"]))
try:
    from cryptography.hazmat.primitives.serialization import load_pem_private_key, Encoding, PublicFormat
    cpriv = load_pem_private_key(pem8.encode(), password=None)
    cn = cpriv.private_numbers()
    cn_pub = cpriv.public_key().public_numbers()
    check("A4: cryptography cross-check n/e", cn.public_numbers.n == k["n"] and cn.public_numbers.e == 65537
          and cn.d == k["d"] and cn_pub.n == k["n"])
    spki_b64_mine = base64.b64encode(em._spki_der(k["n"], k["e"])).decode()
    spki_b64_ref = base64.b64encode(cpriv.public_key().public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)).decode()
    check("A5: SPKI DER == cryptography", spki_b64_mine == spki_b64_ref)
except ImportError:
    print("  (cryptography not available — A4/A5 skipped)")

# ---------- B/C) امضا → تأیید dkimpy + سیم verbatim ----------
import dkim

em.save_config({"mode": "direct", "enabled": True, "from_email": "alerts@my-domain.ir",
                "to_email": "dest@example.com", "dkim_enabled": True, "dkim_selector": "test"})
gen = em.dkim_generate(selector="test", bits=1024)
txt = gen["txt_record"]
check("B0: dkim_generate saves key", em._plain_config().get("dkim_private_key", "").startswith("-----BEGIN PRIVATE KEY-----"))
check("B0b: txt_record shape", txt.startswith("v=DKIM1; k=rsa; p=") and len(txt) > 200, txt[:30])
_stub_ok = lambda n, timeout=5: txt
_stub_bad = lambda n, timeout=5: "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQ=="

msg = em._build_message("[شبکه‌بان] تست DKIM", "سلام\nمتن آزمایشی فارسی.  \nخط بعدی\n",
                        "alerts@my-domain.ir", "شبکه‌بان", "dest@example.com")
info = em._maybe_dkim_sign(msg, "alerts@my-domain.ir")
check("B1: signed info", info.get("signed") is True and info.get("domain") == "my-domain.ir", str(info))
wire = msg.as_bytes(policy=msg.policy.clone(linesep="\r\n"))
check("C1: DKIM header first on wire, verbatim",
      wire.startswith(b"DKIM-Signature: v=1; a=rsa-sha256")
      and b"=?utf-8" not in wire.split(b"\r\n\r\n")[0].split(b"Subject:")[0])
check("C2: single-line signature header", b"\r\n DKIM" not in wire and wire.split(b"\r\n")[0].endswith(b""))
check("B2: dkimpy verify (correct)", dkim.verify(wire, dnsfunc=_stub_ok) is True)
check("B3: dkimpy verify (tampered)", dkim.verify(wire + b"X", dnsfunc=_stub_ok) is False)
check("B4: dkimpy verify (wrong key)", dkim.verify(wire, dnsfunc=_stub_bad) is False)

msg2 = em._build_message("گزارش اسکن", "گزارش پیوست است.\n", "alerts@my-domain.ir",
                         "شبکه‌بان", "dest@example.com",
                         attachments=[("r.pdf", b"%PDF-1.4 x\r\n", "application/pdf")])
em._maybe_dkim_sign(msg2, "alerts@my-domain.ir")
wire2 = msg2.as_bytes(policy=msg2.policy.clone(linesep="\r\n"))
check("B5: dkimpy verify multipart", dkim.verify(wire2, dnsfunc=_stub_ok) is True)

# ---------- D) پارسر DNS TXT/PTR ----------
def _nb(host):
    out = b""
    for l in host.split("."):
        out += bytes([len(l)]) + l.encode()
    return out + b"\x00"

def synth(name, answers, tid=0x2222):
    """answers: list[(rtype, rdata_bytes)]"""
    header = struct.pack("!HHHHHH", tid, 0x8180, 1, len(answers), 0, 0)
    question = _nb(name) + struct.pack("!HH", answers[0][0], 1)
    body = b""
    for rtype, rd in answers:
        body += b"\xc0\x0c" + struct.pack("!HHIH", rtype, 1, 300, len(rd)) + rd
    return header + question + body

recs = em._parse_dns_records(synth("sel._domainkey.my-domain.ir", [(16, b"".join(bytes([len(c)]) + c for c in [b"v=DKIM1; k=rsa; p=AB", b"/CDEFG=="]))]), 0x2222)
check("D1: TXT multi-string joined", recs == [(16, "v=DKIM1; k=rsa; p=AB/CDEFG==")], str(recs))
recs2 = em._parse_dns_records(synth("5.4.3.2.in-addr.arpa", [(12, _nb("mail.my-domain.ir"))]), 0x2222)
check("D2: PTR parsed", recs2 == [(12, "mail.my-domain.ir")], str(recs2))
recs3 = em._parse_dns_records(synth("mx.my-domain.ir", [(1, bytes([1, 2, 3, 4]))]), 0x2222)
check("D3: A parsed", recs3 == [(1, "1.2.3.4")], str(recs3))
check("D4: tid mismatch -> empty", em._parse_dns_records(synth("x.ir", [(16, b"\x01a")], tid=0x3333), 0x2222) == [])

# ---------- E) ارزیاب SPF ----------
_dispatch = {
    "my-domain.ir": "v=spf1 ip4:1.2.3.4 -all",
    "fail.ir": "v=spf1 ip4:8.8.8.8 -all",
    "soft.ir": "v=spf1 ip4:8.8.8.8 ~all",
    "incl.ir": "v=spf1 include:_spf.other.com -all",
    "_spf.other.com": "v=spf1 ip4:1.2.3.4 -all",
}
_patch("resolve_txt", lambda name, timeout=3.0: [v] if (v := _dispatch.get(name.strip(".").lower())) else [])
_patch("resolve_a", lambda name, timeout=3.0: ["1.2.3.4"])
_patch("resolve_ptr", lambda ip, timeout=3.0: ["mail.my-domain.ir"])
check("E1: SPF ip4 pass", em._spf_evaluate("my-domain.ir", "1.2.3.4")["status"] == "pass")
check("E2: SPF -all fail", em._spf_evaluate("fail.ir", "1.2.3.4")["status"] == "fail")
check("E3: SPF ~all softfail", em._spf_evaluate("soft.ir", "1.2.3.4")["status"] == "softfail")
check("E4: SPF include pass", em._spf_evaluate("incl.ir", "1.2.3.4")["status"] == "pass")
check("E5: SPF none", em._spf_evaluate("no-spf.ir", "1.2.3.4")["status"] == "none")

# ---------- F) فیلدهای dkim در config ----------
cfgd = em.get_config(mask_password=True)
check("F1: masked key + dkim_key_set", cfgd["dkim_private_key"] == "********" and cfgd["dkim_key_set"] is True)
cfgd2 = em.save_config({"dkim_private_key": "********"})
check("F2: '********' keeps key", em._plain_config().get("dkim_private_key", "").startswith("-----BEGIN"))
cfgd3 = em.save_config({"dkim_enabled": False, "dkim_selector": "sel2"})
check("F3: bool/selector saved", cfgd3["dkim_enabled"] is False and cfgd3["dkim_selector"] == "sel2")
em.save_config({"dkim_private_key": ""})
check("F4: '' clears key", em._plain_config().get("dkim_private_key") == "")
em.dkim_generate(selector="test", bits=1024)  # برای تست‌های بعدی کلید برگردانده می‌شود
check("F5: re-generated", em._plain_config().get("dkim_private_key", "").startswith("-----BEGIN"))

# ---------- G) send_direct: فقط پورت ۲۵ + امضا ----------
_ats = []
def _fake_send(host, port, username, password, msg_, timeout, mode, helo="x"):
    _ats.append((host, port))
    return {}
_patch("resolve_mx_full", lambda domain, timeout=8.0: [(10, "mx1.dest.ir"), (20, "mx2.dest.ir")])
_patch("_smtp_send_once", _fake_send)
em.save_config({"dkim_enabled": True, "dkim_selector": "test", "mode": "direct"})  # F3 غیرفعالش کرده بود
r = em.send_direct("s", "b", from_email="alerts@my-domain.ir", from_name="x", dest="u@dest.ir", timeout=10)
check("G1: direct send ok", r.get("ok") is True and r.get("mx") == "mx1.dest.ir", str(r)[:80])
check("G2: only port 25 attempts", all(p == 25 for _h, p in _ats) and len(_ats) == 1, str(_ats))
check("G3: result says dkim signed", r.get("dkim", {}).get("signed") is True, str(r.get("dkim")))

# DKIM فعال ولی کلید نبود → خطای صریح
em.save_config({"dkim_private_key": ""})
try:
    em.send_direct("s", "b", from_email="alerts@my-domain.ir", from_name="x", dest="u@dest.ir", timeout=10)
    check("G4: missing key -> clear error", False)
except ValueError as e:
    check("G4: missing key -> clear error", "کلید" in str(e) and "DKIM" in str(e), str(e)[:70])
em.dkim_generate(selector="test", bits=1024)

# امضا در حالت رله هم انجام می‌شود
_ats.clear()
_patch("_smtp_send_once", _fake_send)
em.save_config({"mode": "relay", "host": "smtp.my-host.ir", "port": 587,
                "username": "alerts@my-domain.ir", "password": "secret"})
r2 = em.send_relay("s", "b", to_email="u@dest.ir")
check("G5: relay send ok + signed", r2.get("ok") is True and r2.get("dkim", {}).get("signed") is True, str(r2)[:90])
em.save_config({"mode": "direct", "host": "", "username": "", "password": ""})

# ---------- H) پیام خطای هدفمند 5.7.26 ----------
def _fake_reject(*a, **k):
    raise smtplib.SMTPDataError(550, b"5.7.26 Your email has been blocked because the sender is unauthenticated.\n5.7.26 Gmail requires all senders to authenticate with either SPF or DKIM.")
_patch("_smtp_send_once", _fake_reject)
try:
    em.send_direct("s", "b", from_email="alerts@my-domain.ir", from_name="x", dest="u@dest.ir", timeout=10)
    check("H1: 5.7.26 targeted hint", False)
except ValueError as e:
    s = str(e)
    check("H1: 5.7.26 targeted hint", "5.7.26" in s and "تولید کلید DKIM" in s and "احرازنشده" in s, s[:100])
def _fake_reject2(*a, **k):
    raise smtplib.SMTPDataError(550, b"5.7.1 spam rejected")
_patch("_smtp_send_once", _fake_reject2)
try:
    em.send_direct("s", "b", from_email="alerts@my-domain.ir", from_name="x", dest="u@dest.ir", timeout=10)
    check("H2: Task40-F regression (code+text present)", False)
except ValueError as e:
    s = str(e)
    check("H2: Task40-F regression (code+text present)", "550" in s and "5.7.1" in s and "تولید کلید DKIM" not in s, s[:100])
_restore()  # موک‌های send بازگردانده می‌شوند؛ پارسر SPF/DNS هم

# ---------- I) auth_diagnostics + اندپوینت‌ها ----------
em.save_config({"from_email": "alerts@my-domain.ir", "mode": "direct", "enabled": True,
                "dkim_enabled": True, "dkim_selector": "test", "dkim_private_key": "********"})
gen = em.dkim_generate(selector="test", bits=1024)
_txts = {
    "my-domain.ir": "v=spf1 ip4:1.2.3.4 -all",
    "test._domainkey.my-domain.ir": gen["txt_record"],
    "_dmarc.my-domain.ir": "v=DMARC1; p=none; rua=mailto:postmaster@my-domain.ir",
}
_patch("resolve_txt", lambda name, timeout=3.0: [_txts[name.strip(".").lower()]] if name.strip(".").lower() in _txts else [])
_patch("resolve_ptr", lambda ip, timeout=3.0: ["mail.my-domain.ir"])
_patch("_public_ip", lambda timeout=5.0: ("1.2.3.4", "test"))
d = em.auth_diagnostics("alerts@my-domain.ir")
check("I1: auth diag shape", all(kk in d for kk in ("domain", "egress_ip", "spf", "dkim", "dmarc", "records", "steps", "verdict")))
check("I2: SPF pass", d["spf"]["status"] == "pass")
check("I3: DKIM match", d["dkim"]["match"] == "match", str(d["dkim"])[:90])
check("I4: DMARC found", d["dmarc"]["found"] is True)
check("I5: verdict all-ok", "کامل است" in d["verdict"], d["verdict"][:60])
check("I6: records include spf/dkim/dmarc", set(d["records"]) == {"spf", "dkim", "dmarc"}, str(list(d["records"])))
check("I7: rDNS surfaced", d["ptr"]["record"] == "mail.my-domain.ir")

d2 = em.auth_diagnostics("user@gmail.com")
check("I8: provider-domain warning", any("دامنهٔ فرستنده" in w for w in d2["warnings"]) and "دامنهٔ خودتان" in d2["verdict"], d2["verdict"][:60])

try:
    em.auth_diagnostics("not-an-email")
    check("I9: invalid from rejected", False)
except ValueError:
    check("I9: invalid from rejected", True)
_restore()  # موک‌های DNS/IP بازگردانده می‌شوند

from fastapi.testclient import TestClient
import main as appm
mem = appm.email_manager
if mem is not em:  # یکسان‌سازی ایزوله‌سازی
    mem._CONFIG = em._CONFIG
client = TestClient(appm.app)
_r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
assert _r.status_code == 200, f"login failed: {_r.status_code}"

rg = client.post("/api/smtp/dkim/generate", json={"selector": "apitest", "bits": 1024})
check("I10: dkim/generate 200", rg.status_code == 200 and rg.json().get("txt_record", "").startswith("v=DKIM1"), rg.text[:90])
check("I11: dkim/generate host", rg.json().get("dkim_host") == "apitest._domainkey.my-domain.ir", rg.text[:120])
rb = client.post("/api/smtp/dkim/generate", json={"selector": "بد!!"})
check("I12: bad selector -> 400", rb.status_code == 400, rb.text[:80])

_patch_mem = {}
if mem is not em:
    _patch_mem = dict(_orig)

rr = client.post("/api/smtp/auth-check", json={"from_email": "user@gmail.com"})
check("I13: auth-check 200 (gmail warning path)", rr.status_code == 200 and rr.json().get("domain") == "gmail.com", rr.text[:90])
check("I14: auth-check warnings present", bool(rr.json().get("warnings")), rr.text[:150])
rbad = client.post("/api/smtp/auth-check", json={"from_email": "bad"})
check("I15: auth-check invalid -> 400", rbad.status_code == 400, rbad.text[:80])

rc = client.get("/api/smtp/config")
jc = rc.json()
check("I16: GET config has dkim fields", all(kk in jc for kk in ("dkim_enabled", "dkim_selector", "dkim_key_set")) and jc.get("dkim_private_key") in ("", "********"), str({k: jc.get(k) for k in ("dkim_enabled", "dkim_selector", "dkim_key_set")}))
rk = client.put("/api/smtp/config", json={"dkim_enabled": True, "dkim_selector": "web"})
check("I17: PUT dkim fields -> 200", rk.status_code == 200 and rk.json().get("dkim_enabled") is True, rk.text[:80])
rt = client.post("/api/smtp/dkim/generate", json={"selector": "web", "bits": 1024})
check("I18: generate with web selector", rt.status_code == 200 and rt.json().get("dkim_host", "").startswith("web._domainkey"), rt.text[:100])

# ---------- J) سورس فرانت و CSS ----------
src = open(os.path.join(ROOT, "frontend", "src.jsx"), encoding="utf-8").read()
check("J1: auth section present", "احراز هویت دامنه (SPF / DKIM / DMARC)" in src and "genDkim" in src and "authCheck" in src)
check("J2: endpoints wired", "/api/smtp/dkim/generate" in src and "/api/smtp/auth-check" in src)
check("J3: buttons labeled", "تولید کلید DKIM" in src and "بررسی احراز هویت دامنه" in src)
check("J4: dns-record boxes", 'className="dns-record"' in src and "dkim_host" in src and "txt_record" in src)
check("J5: guide explains 5.7.26", "5.7.26" in src and "SPF یا DKIM" in src and "_dmarc" in src)
check("J6: guide covers records", "v=spf1 ip4" in src and "v=DMARC1" in src and "_domainkey" in src)  # رکورد DKIM پویاست
check("J7: from-domain warning", "دامنهٔ دیگران قابل احراز نیست" in src)
check("J8: standalone msg updated", "برای تحویل مطمئن بخش «احراز هویت دامنه»" in src)
css = open(os.path.join(ROOT, "frontend", "style.css"), encoding="utf-8").read()
check("J9: .dns-record styled", ".dns-record{" in css)
check("J10: .email-diag ol styled", ".email-diag ol{" in css)

# ---------- بازیابی ----------
cleanup()
check("cleanup: original smtp_config.json restored",
      (_orig_bytes is None and not os.path.exists(str(_cfg_path))) or _cfg_path.read_bytes() == _orig_bytes)

print("\nALL OK" if ok else "\nFAILURES PRESENT")
sys.exit(0 if ok else 1)
