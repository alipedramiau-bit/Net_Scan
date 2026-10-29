"""Cookie-based admin authentication for the Net_Scan UI.

- Single admin account (default NetAdmin/NetAdmin, overridable via env).
- Session token: base64url(JSON payload) + "." + HMAC-SHA256 signature.
- The signing secret is generated once and persisted next to the database
  catalog, so sessions survive backend restarts.
- Stdlib only — no new dependencies.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
_SECRET_FILE = Path(
    os.environ.get("NETSCAN_AUTH_SECRET_FILE") or (ROOT_DIR / "databases" / ".auth_secret")
)

SESSION_DAYS = int(os.environ.get("NETSCAN_SESSION_DAYS", "7"))
ADMIN_USER = os.environ.get("NETSCAN_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("NETSCAN_ADMIN_PASSWORD", "NetAdmin")
COOKIE_NAME = "net_scan_session"
COOKIE_MAX_AGE = SESSION_DAYS * 86400


def _secret() -> bytes:
    """Load (or create) the persisted signing secret."""
    try:
        data = _SECRET_FILE.read_bytes().strip()
        if len(data) >= 32:
            return data
    except OSError:
        pass
    data = secrets.token_hex(32).encode()
    try:
        _SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
        _SECRET_FILE.write_bytes(data)
        try:
            os.chmod(_SECRET_FILE, 0o600)
        except OSError:
            pass
    except OSError:
        pass  # read-only FS: fall back to an ephemeral secret
    return data


def _sign(payload: bytes) -> str:
    return hmac.new(_secret(), payload, hashlib.sha256).hexdigest()


def create_token(username: str) -> str:
    exp = int((datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)).timestamp())
    payload = json.dumps({"u": username, "exp": exp}, separators=(",", ":")).encode()
    b64 = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    return f"{b64}.{_sign(payload)}"


def verify_token(token: str | None) -> str | None:
    """Return the username for a valid, unexpired token; otherwise None."""
    if not token or "." not in token:
        return None
    b64, sig = token.rsplit(".", 1)
    try:
        payload = base64.urlsafe_b64decode(b64 + "=" * (-len(b64) % 4))
    except Exception:
        return None
    if not hmac.compare_digest(sig, _sign(payload)):
        return None
    try:
        data = json.loads(payload)
    except ValueError:
        return None
    try:
        if int(data.get("exp", 0)) < time.time():
            return None
    except (TypeError, ValueError):
        return None
    return data.get("u") or None


def check_credentials(username: str, password: str) -> bool:
    """Constant-time credential comparison."""
    try:
        return hmac.compare_digest(str(username), ADMIN_USER) and \
               hmac.compare_digest(str(password), ADMIN_PASSWORD)
    except Exception:
        return False
