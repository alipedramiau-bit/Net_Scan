"""E2E checks for post-push verification (Task 20) — fixes the user-reported bug:

«دستگاه‌هایی با اعلام موفق در گزارش کانفیگ، روی آن‌ها اعمال نشده؛
 api/winbox فعال است و یوزر هم درست است»

Root causes covered here:
- /system/script/run returns !done as soon as the job STARTS → script-internal
  errors (user exists, syntax, [find]) were invisible → false success.
  Fix: console scripts are wrapped in :do/on-error writing a status global that
  we read back from /system/script/environment.
- Even a trap-free run says nothing about the EFFECT. Fix: verify_push reads
  back the promised state (user login / identity / snmp / ip service) and
  flips the result to failed with a Persian reason when it does not match.

All device I/O is faked at the RouterOSClient.talk layer — no real device.
Run: python3 scripts/test_push_verification.py
"""
import hashlib
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

from fastapi.testclient import TestClient

import main as appm
import routeros_api as ra

# main.py ممکن است ماژول routeros_api جداگانه‌ای داشته باشد (الگوی AGENTS.md)
ROS_MODULES = [ra]
if getattr(appm, "routeros_api", None) is not None and appm.routeros_api is not ra:
    ROS_MODULES.append(appm.routeros_api)

ok = True


def check(label, cond, extra=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label, extra if not cond else "")
    ok = ok and cond


# ---------------------------------------------------------------------------
# Fake device layer: a stateful talk() replacement keyed by host
# ---------------------------------------------------------------------------
class FakeRouters:
    def __init__(self):
        self.admin = {}            # ip -> (user, pass)
        self.users = {}            # ip -> {name: pass}  (actually created)
        self.user_add_silent = set()  # ip where /user/add returns done but creates NOTHING
        self.silent_sets = set()   # ip where set commands say done but change nothing
        self.identity = {}         # ip -> identity
        self.snmp_enabled = {}     # ip -> "yes"/"no"
        self.services = {}         # ip -> {name: "yes"/"no"(disabled)}
        self.script_status = {}    # ip -> "ok"/"failed"/None
        self.env = {}              # ip -> {var: value}
        self.added_source = {}     # ip -> last script source added
        self.log = {}              # ip -> [sentence,...]
        self._chal = {}            # ip -> challenge hex

    def handle(self, ip: str, words: list[str]) -> list[list[str]]:
        self.log.setdefault(ip, []).append(list(words))
        cmd = words[0]

        if ip not in self.admin:
            # دستگاهی که اصلاً جواب نمی‌دهد (خاموش/فایروال)
            raise ra.RouterOSError("[Errno 111] Connection refused")

        if cmd == "/login":
            if any(w.startswith("=response=") for w in words):
                nm = next((w[6:] for w in words if w.startswith("=name=")), "")
                resp = next((w[10:] for w in words if w.startswith("=response=")), "")
                if self._challenge_valid(ip, nm, resp):
                    return [["!done"]]
                return [["!trap", "=message=cannot log in"]]
            if any(w.startswith("=password=") for w in words):
                nm = next((w[6:] for w in words if w.startswith("=name=")), "")
                pw = next((w[10:] for w in words if w.startswith("=password=")), "")
                if self._valid_login(ip, nm, pw):
                    return [["!done"]]
                return [["!trap", "=message=invalid user name or password"]]
            ret = hashlib.md5(ip.encode()).hexdigest()
            self._chal[ip] = ret
            return [["!done", f"=ret={ret}"]]

        if cmd == "/user/add":
            nm = next((w[6:] for w in words if w.startswith("=name=")), "")
            pw = next((w[10:] for w in words if w.startswith("=password=")), "")
            if ip in self.user_add_silent:
                return [["!done"]]  # the user-reported lie: done but nothing created
            self.users.setdefault(ip, {})[nm] = pw
            return [["!done"]]

        if cmd == "/system/identity/set":
            if ip not in self.silent_sets:
                nm = next((w[6:] for w in words if w.startswith("=name=")), "")
                if nm:
                    self.identity[ip] = nm
            return [["!done"]]
        if cmd == "/snmp/set":
            if ip not in self.silent_sets:
                en = next((w[9:] for w in words if w.startswith("=enabled=")), "")
                if en:
                    self.snmp_enabled[ip] = en
            return [["!done"]]
        if cmd == "/user/set":
            if ip not in self.silent_sets:
                nm = next((w[6:] for w in words if w.startswith("=name=")), "")
                pw = next((w[10:] for w in words if w.startswith("=password=")), "")
                if nm and pw:
                    self.users.setdefault(ip, {})[nm] = pw
            return [["!done"]]

        if cmd == "/system/identity/print":
            return [["!re", f"=name={self.identity.get(ip, 'old-id')}"], ["!done"]]

        if cmd == "/snmp/print":
            return [["!re", f"=enabled={self.snmp_enabled.get(ip, 'no')}"], ["!done"]]

        if cmd == "/ip/service/print":
            rows = [["!re", f"=name={n}", f"=disabled={d}"]
                    for n, d in (self.services.get(ip) or {}).items()]
            return rows + [["!done"]]

        if cmd == "/system/script/add":
            src = next((w[8:] for w in words if w.startswith("=source=")), "")
            self.added_source[ip] = src
            return [["!done"]]
        if cmd == "/system/script/run":
            src = self.added_source.get(ip, "")
            m = re.search(r":global\s+(NetScanPush\w+)", src)
            if m and self.script_status.get(ip) is not None:
                self.env.setdefault(ip, {})[m.group(1)] = self.script_status[ip]
            return [["!done"]]
        if cmd == "/system/script/environment/print":
            rows = [["!re", f"=name={k}", f"=value={v}"]
                    for k, v in (self.env.get(ip) or {}).items()]
            return rows + [["!done"]]
        if cmd == "/system/script/environment/remove":
            rid = next((w[5:] for w in words if w.startswith("=.id=")), "")
            for k in list((self.env.get(ip) or {})):
                if k.startswith(rid) or rid == k:
                    self.env[ip].pop(k, None)
            return [["!done"]]
        if cmd == "/system/script/remove":
            return [["!done"]]

        raise AssertionError("fake: unexpected command " + cmd)

    def _valid_login(self, ip, nm, pw):
        if self.admin.get(ip) == (nm, pw):
            return True
        return (self.users.get(ip) or {}).get(nm) == pw

    def _challenge_valid(self, ip, nm, resp):
        cands = []
        if ip in self.admin:
            cands.append(self.admin[ip])
        for u, p in (self.users.get(ip) or {}).items():
            cands.append((u, p))
        ret = self._chal.get(ip, "")
        for u, p in cands:
            if u != nm:
                continue
            m = hashlib.md5()
            m.update(b"\x00")
            m.update(p.encode())
            m.update(bytes.fromhex(ret))
            if ("00" + m.hexdigest()) == resp:
                return True
        return False


FAKE = FakeRouters()


def make_talk(state):
    def talk(self, words, timeout=None):
        return state.handle(getattr(self, "host", "?"), list(words))
    return talk


orig_talks = []
for m in ROS_MODULES:
    orig_talks.append((m.RouterOSClient, m.RouterOSClient.talk,
                       m.RouterOSClient.connect, m.RouterOSClient.close))
    m.RouterOSClient.talk = make_talk(FAKE)
    m.RouterOSClient.connect = lambda self: None  # بدون سوکت واقعی
    m.RouterOSClient.close = lambda self: None

SCRIPT_USER = '/user add name=olom1 password="Olom@2026$" group=full'

try:
    # ------------------------------------------------------------------
    # 0) unit: parser + intents
    # ------------------------------------------------------------------
    sent, pdef = ra._parse_terminal_line(SCRIPT_USER)
    check("unit: quotes stripped from password", "=password=Olom@2026$" in sent, str(sent))
    check("unit: sentence path", sent[0] == "/user/add", str(sent))
    sent2, _ = ra._parse_terminal_line("set enabled=yes", "/snmp")
    check("unit: continuation uses cur_path", sent2 == ["/snmp/set", "=enabled=yes"], str(sent2))
    po, pd = ra._parse_terminal_line("/snmp community")
    check("unit: path-only line", po is None and pd == "/snmp/community", str((po, pd)))
    fs, _ = ra._parse_terminal_line('/snmp community remove [ find name="public" ]')
    check("unit: [find] on remove goes to console path", fs is None, str(fs))
    pr, _ = ra._parse_terminal_line("/ip route print where dst-address=10.0.0.0/8")
    check("unit: print passthrough", pr is not None and pr[0] == "/ip/route/print", str(pr))
    it = ra._extract_verify_intents(SCRIPT_USER)
    check("unit: intents extract quoted creds", it["users"] == [("olom1", "Olom@2026$")], str(it))
    it2 = ra._extract_verify_intents("/system identity set name=R1\n/ip service enable api")
    check("unit: intents identity+service",
          it2["identity"] == "R1" and it2["services"] == [("api", True)], str(it2))
    check("classify: user-exists hint",
          "از قبل" in ra.classify_push_error("failure: already have such user"),
          ra.classify_push_error("failure: already have such user"))

    # ------------------------------------------------------------------
    # 1) THE USER'S BUG: device says done, user NOT actually created
    # ------------------------------------------------------------------
    ip = "10.77.0.1"
    FAKE.admin[ip] = ("admin", "pw")
    FAKE.user_add_silent.add(ip)
    res = ra.push_config(ip, "admin", "pw", SCRIPT_USER, timeout=5)
    check("silent-fail: reported FAILED (not ok)", res.get("ok") is False, str(res))
    check("silent-fail: verified=False", res.get("verified") is False, str(res))
    check("silent-fail: Persian reason mentions verify",
          "تأیید اعمال نشد" in (res.get("reason") or ""), str(res.get("reason")))
    check("silent-fail: reason mentions the user",
          "olom1" in (res.get("reason") or ""), str(res.get("reason")))

    # ------------------------------------------------------------------
    # 2) user actually created → ok + verified
    # ------------------------------------------------------------------
    ip2 = "10.77.0.2"
    FAKE.admin[ip2] = ("admin", "pw")
    res = ra.push_config(ip2, "admin", "pw", SCRIPT_USER, timeout=5)
    check("applied: ok=True", res.get("ok") is True, str(res))
    check("applied: verified=True", res.get("verified") is True, str(res))
    check("applied: user really stored",
          FAKE.users.get(ip2, {}).get("olom1") == "Olom@2026$")

    # ------------------------------------------------------------------
    # 3) identity verify
    # ------------------------------------------------------------------
    ip3 = "10.77.0.3"
    FAKE.admin[ip3] = ("admin", "pw")
    FAKE.identity[ip3] = "old-id"
    FAKE.silent_sets.add(ip3)
    res = ra.push_config(ip3, "admin", "pw", "/system identity set name=NEW-ID", timeout=5)
    check("identity-fail: FAILED with identity detail",
          res.get("ok") is False and "identity" in (res.get("reason") or "")
          and "NEW-ID" in (res.get("reason") or ""), str(res))
    ip4 = "10.77.0.4"
    FAKE.admin[ip4] = ("admin", "pw")
    # شبیه‌سازی اعمال واقعی: اولین خواندن identity بعد از push مقدار جدید را بدهد
    FAKE.identity[ip4] = "NEW-ID"
    res = ra.push_config(ip4, "admin", "pw", "/system identity set name=NEW-ID", timeout=5)
    check("identity-ok: verified", res.get("ok") is True and res.get("verified") is True, str(res))

    # ------------------------------------------------------------------
    # 4) snmp verify
    # ------------------------------------------------------------------
    ip5 = "10.77.0.5"
    FAKE.admin[ip5] = ("admin", "pw")
    FAKE.snmp_enabled[ip5] = "no"
    FAKE.silent_sets.add(ip5)
    res = ra.push_config(ip5, "admin", "pw", "/snmp set enabled=yes trap-version=2", timeout=5)
    check("snmp-fail: FAILED mentioning SNMP",
          res.get("ok") is False and "SNMP" in (res.get("reason") or ""), str(res))
    ip6 = "10.77.0.6"
    FAKE.admin[ip6] = ("admin", "pw")
    FAKE.snmp_enabled[ip6] = "yes"
    res = ra.push_config(ip6, "admin", "pw", "/snmp set enabled=yes trap-version=2", timeout=5)
    check("snmp-ok: verified", res.get("ok") is True and res.get("verified") is True, str(res))

    # ------------------------------------------------------------------
    # 5) console fallback: wrapped script + self-reported status
    # ------------------------------------------------------------------
    ip7 = "10.77.0.7"
    FAKE.admin[ip7] = ("admin", "pw")
    FAKE.script_status[ip7] = "ok"
    console_script = ':put "hello"\n/log info "netscan test"'
    res = ra.push_config(ip7, "admin", "pw", console_script, timeout=5)
    check("console-ok: ok=True", res.get("ok") is True, str(res))
    check("console-ok: no verifiable intent → verified None", res.get("verified") is None, str(res))
    src = FAKE.added_source.get(ip7, "")
    check("console-ok: script wrapped in :do/on-error",
          ":do {" in src and "on-error={" in src and 'set NetScanPush' in src, src[:120])
    check("console-ok: original script inside wrapper", ':put "hello"' in src, src[:120])
    check("console-ok: temp script cleaned (remove called)",
          any(w[0] == "/system/script/remove" for w in FAKE.log[ip7]))

    ip8 = "10.77.0.8"
    FAKE.admin[ip8] = ("admin", "pw")
    FAKE.script_status[ip8] = "failed"
    res = ra.push_config(ip8, "admin", "pw", console_script, timeout=5)
    check("console-fail: FAILED with on-error reason",
          res.get("ok") is False and "خطا داد" in (res.get("reason") or ""), str(res))

    # status never appears → timeout (shortened for the test)
    ip9 = "10.77.0.9"
    FAKE.admin[ip9] = ("admin", "pw")
    FAKE.script_status[ip9] = None
    for m in ROS_MODULES:
        m.RouterOSClient.PUSH_STATUS_TIMEOUT = 0.8
    t0 = time.time()
    res = ra.push_config(ip9, "admin", "pw", console_script, timeout=5)
    dt = time.time() - t0
    check("console-timeout: FAILED with unknown-status reason",
          res.get("ok") is False and "خوانده نشد" in (res.get("reason") or ""), str(res))
    check("console-timeout: waited ~timeout not 30s", 0.5 < dt < 6, str(round(dt, 2)))

    # ------------------------------------------------------------------
    # 6) parallel E2E via the API + failed-csv (Task 19) integration
    # ------------------------------------------------------------------
    client = TestClient(appm.app)
    r = client.post("/api/login", json={"username": "admin", "password": "NetAdmin"})
    check("login", r.status_code == 200, str(r.status_code))

    FAKE.admin["10.77.1.1"] = ("admin", "pw")
    FAKE.user_add_silent.add("10.77.1.1")   # the lying device
    FAKE.admin["10.77.1.2"] = ("admin", "pw")  # honest ok
    FAKE.script_status["10.77.1.2"] = "ok"
    # 10.77.1.3 unknown → connection refused
    ips = ["10.77.1.1", "10.77.1.2", "10.77.1.3"]
    r = client.post("/api/devices/push-config/start",
                    json={"ips": ips, "username": "admin", "password": "pw",
                          "script": SCRIPT_USER, "port": 8728})
    check("parallel: started", r.status_code == 200 and r.json().get("total") == 3, r.text[:120])
    p = {}
    for _ in range(200):
        p = client.get("/api/devices/push-config/progress").json()
        if p.get("ready") or p.get("error"):
            break
        time.sleep(0.05)
    check("parallel: failed=2 (silent-fail + refused)",
          p.get("ok") == 1 and p.get("failed") == 2, str(p))
    resmap = {x["ip"]: x for x in (p.get("results") or [])}
    check("parallel: silent device reason Persian",
          "تأیید اعمال نشد" in (resmap.get("10.77.1.1", {}).get("reason") or ""),
          str(resmap.get("10.77.1.1")))
    check("parallel: refused device classified",
          "اتصال رد شد" in (resmap.get("10.77.1.3", {}).get("reason") or ""),
          str(resmap.get("10.77.1.3")))

    r = client.get("/api/devices/push-config/failed-csv")
    check("failed-csv: includes the lying device", r.status_code == 200, str(r.status_code))
    body = r.content.decode("utf-8-sig")
    check("failed-csv: reason row has verify text", "تأیید اعمال نشد" in body, body[:200])

    # no-verifiable-intent push → ok with verified None (still success)
    r2 = client.post("/api/devices/push-config/start",
                     json={"ips": ["10.77.1.2"], "username": "admin", "password": "pw",
                           "script": ':put "nothing to verify"', "port": 8728})
    check("second run started", r2.status_code == 200, r2.text[:120])
    for _ in range(200):
        p = client.get("/api/devices/push-config/progress").json()
        if p.get("ready") or p.get("error"):
            break
        time.sleep(0.05)
    check("no-intent: ok", p.get("failed") == 0 and p.get("ok") == 1, str(p))
finally:
    for cls, fn_talk, fn_conn, fn_close in orig_talks:
        cls.talk = fn_talk
        cls.connect = fn_conn
        cls.close = fn_close
    for m in ROS_MODULES:
        m.RouterOSClient.PUSH_STATUS_TIMEOUT = 30.0

print("\n" + ("ALL TESTS PASSED ✔" if ok else "SOME TESTS FAILED ✘"))
sys.exit(0 if ok else 1)
