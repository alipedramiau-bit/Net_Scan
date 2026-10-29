"""SQLite persistence for discovered devices (stdlib sqlite3 only).

The database file (devices.db in the project root) is created automatically
when the backend starts. Connections are created per call and guarded by a
module-level lock, so access is thread-safe from FastAPI worker threads.
"""
import csv
import io
import json
import re
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_DB_DIR = _ROOT / "databases"
_CATALOG = _DB_DIR / "catalog.json"
# Legacy single-file DB (migrated into databases/default.db on first init)
_LEGACY_DB = _ROOT / "devices.db"
_LOCK = threading.Lock()


def _read_catalog() -> dict:
    try:
        import json as _json
        data = _json.loads(_CATALOG.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "active" in data:
            return data
    except (OSError, ValueError):
        pass
    return {"active": "default", "databases": ["default"]}


def _write_catalog(data: dict) -> None:
    import json as _json
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    tmp = _CATALOG.with_suffix(".tmp")
    tmp.write_text(_json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(_CATALOG)


def _safe_db_name(name: str) -> str:
    import re
    n = (name or "").strip()
    n = re.sub(r"[^a-zA-Z0-9_\-\u0600-\u06FF]+", "_", n).strip("_")
    if not n or len(n) > 64:
        raise ValueError("نام دیتابیس نامعتبر است (۱ تا ۶۴ کاراکتر، حروف/عدد/خط‌زیر)")
    if n.startswith("_"):
        raise ValueError("نام دیتابیس نباید با _ شروع شود")
    return n


def db_path_for(name: str | None = None) -> Path:
    """Resolve path for a named database (or the active one)."""
    cat = _read_catalog()
    n = name or cat.get("active") or "default"
    n = _safe_db_name(n) if name else (cat.get("active") or "default")
    if n not in cat.get("databases", []) and name is None:
        n = "default"
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    return _DB_DIR / f"{n}.db"


def get_active_db_name() -> str:
    return _read_catalog().get("active") or "default"


def list_databases() -> dict:
    cat = _read_catalog()
    items = []
    for n in cat.get("databases", []):
        p = _DB_DIR / f"{n}.db"
        count = 0
        if p.is_file():
            try:
                with _LOCK:
                    conn = sqlite3.connect(p, timeout=10)
                    try:
                        count = conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
                    except sqlite3.Error:
                        count = 0
                    finally:
                        conn.close()
            except OSError:
                count = 0
        items.append({"name": n, "path": str(p), "exists": p.is_file(), "devices": count, "active": n == cat.get("active")})
    return {"active": cat.get("active"), "databases": items}


def create_database(name: str) -> dict:
    n = _safe_db_name(name)
    cat = _read_catalog()
    dbs = list(cat.get("databases") or [])
    if n not in dbs:
        dbs.append(n)
    cat["databases"] = dbs
    _write_catalog(cat)
    init_db(db_path_for(n))
    return list_databases()


def set_active_database(name: str) -> dict:
    n = _safe_db_name(name)
    cat = _read_catalog()
    if n not in cat.get("databases", []):
        raise KeyError(n)
    cat["active"] = n
    _write_catalog(cat)
    init_db(db_path_for(n))
    return list_databases()


def delete_database(name: str) -> dict:
    n = _safe_db_name(name)
    if n == "default":
        raise ValueError("دیتابیس default قابل حذف نیست")
    cat = _read_catalog()
    if cat.get("active") == n:
        raise ValueError("دیتابیس فعال را نمی‌توان حذف کرد؛ ابتدا دیتابیس دیگری را فعال کنید")
    dbs = [x for x in cat.get("databases", []) if x != n]
    cat["databases"] = dbs
    _write_catalog(cat)
    p = _DB_DIR / f"{n}.db"
    if p.is_file():
        p.unlink()
    return list_databases()


# Back-compat: DB_PATH property-like via function used as default — call sites use DB_PATH
# which we keep as the active path resolved at import; prefer db_path_for() at runtime.
DB_PATH = _LEGACY_DB  # updated in init_db_global

# Stored classification values: mikrotik_candidate | non_mikrotik | special
# Indexes are intentionally NOT in _SCHEMA: older DBs may lack newer columns
# (device_type, wireless_info, …). CREATE TABLE IF NOT EXISTS is a no-op on
# existing tables, so index creation would fail before migration runs.
# Indexes are created after column migration in init_db() / restore path.
_SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
    ip TEXT PRIMARY KEY,
    ping_ok INTEGER NOT NULL DEFAULT 0,
    open_ports TEXT NOT NULL DEFAULT '[]',
    port_states TEXT NOT NULL DEFAULT '{}',
    classification TEXT NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    seen_count INTEGER NOT NULL DEFAULT 1,
    device_name TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '',
    ip_addresses TEXT NOT NULL DEFAULT '',
    ip_neighbors TEXT NOT NULL DEFAULT '',
    interfaces TEXT NOT NULL DEFAULT '',
    device_type TEXT NOT NULL DEFAULT '',
    wireless_info TEXT NOT NULL DEFAULT '',
    device_log TEXT NOT NULL DEFAULT '',
    mac_info TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

_INDEX_DDL = (
    "CREATE INDEX IF NOT EXISTS idx_devices_classification ON devices(classification)",
    "CREATE INDEX IF NOT EXISTS idx_devices_device_type ON devices(device_type)",
    "CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON devices(last_seen)",
    "CREATE INDEX IF NOT EXISTS idx_devices_seen_count ON devices(seen_count)",
    "CREATE INDEX IF NOT EXISTS idx_devices_ping_ok ON devices(ping_ok)",
    "CREATE INDEX IF NOT EXISTS idx_devices_name ON devices(device_name)",
)

_MIGRATE_COLUMNS = [
    ("device_name", "TEXT NOT NULL DEFAULT ''"),
    ("tags", "TEXT NOT NULL DEFAULT ''"),
    ("ip_addresses", "TEXT NOT NULL DEFAULT ''"),
    ("ip_neighbors", "TEXT NOT NULL DEFAULT ''"),
    ("interfaces", "TEXT NOT NULL DEFAULT ''"),
    ("device_type", "TEXT NOT NULL DEFAULT ''"),
    ("wireless_info", "TEXT NOT NULL DEFAULT ''"),
    ("device_log", "TEXT NOT NULL DEFAULT ''"),
    ("mac_info", "TEXT NOT NULL DEFAULT ''"),
]


def _now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def _connect(db_path=None):
    path = str(db_path if db_path is not None else db_path_for())
    with _LOCK:
        conn = sqlite3.connect(path, timeout=60)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA cache_size=-8000")  # ~8MB page cache
            conn.execute("PRAGMA busy_timeout=60000")
            yield conn
            conn.commit()
        finally:
            conn.close()


def init_db(db_path=None):
    path = Path(db_path) if db_path is not None else db_path_for()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        conn = sqlite3.connect(str(path), timeout=30)
        try:
            conn.executescript(_SCHEMA)
            existing = {r[1] for r in conn.execute("PRAGMA table_info(devices)").fetchall()}
            for col, decl in _MIGRATE_COLUMNS:
                if col not in existing:
                    conn.execute(f"ALTER TABLE devices ADD COLUMN {col} {decl}")
            # performance pragmas + indexes (safe to re-run; after migration so columns exist)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            for ddl in _INDEX_DDL:
                conn.execute(ddl)
            conn.commit()
        finally:
            conn.close()
    return path


def init_db_global():
    """Ensure databases/ catalog exists; migrate legacy devices.db into default."""
    global DB_PATH
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    cat = _read_catalog()
    if "default" not in cat.get("databases", []):
        cat["databases"] = ["default"] + [x for x in cat.get("databases", []) if x != "default"]
    if not cat.get("active"):
        cat["active"] = "default"
    _write_catalog(cat)
    default_path = _DB_DIR / "default.db"
    if not default_path.is_file() and _LEGACY_DB.is_file():
        import shutil
        shutil.copy2(_LEGACY_DB, default_path)
    init_db(default_path)
    # init any other registered DBs if missing
    for n in cat.get("databases", []):
        p = _DB_DIR / f"{n}.db"
        if not p.is_file():
            init_db(p)
    DB_PATH = db_path_for()
    return DB_PATH


# Backwards compatibility: legacy Persian labels / old keys map to internal keys.
LEGACY_CLASSIFICATION_LABELS = {
    "نامزد MikroTik": "mikrotik_candidate",
    "دستگاه MikroTik": "mikrotik_candidate",
    "غیر MikroTik": "non_mikrotik",
    "احتمالاً غیر MikroTik": "non_mikrotik",
    "ویژه": "special",
}
# Public display label (new wording).
CLASSIFICATION_LABELS = {
    "mikrotik_candidate": "دستگاه MikroTik",
    "non_mikrotik": "غیر MikroTik",
    "special": "ویژه",
}

def classification_label(value):
    """Persian display label for a classification, tolerating legacy values."""
    if value in LEGACY_CLASSIFICATION_LABELS:
        value = LEGACY_CLASSIFICATION_LABELS[value]
    return CLASSIFICATION_LABELS.get(value, value or "")

def _normalize_classification(classification, ping_ok):
    if classification in LEGACY_CLASSIFICATION_LABELS:
        classification = LEGACY_CLASSIFICATION_LABELS[classification]
    if classification in ("mikrotik_candidate", "non_mikrotik", "special"):
        return classification
    if classification == "no_ping":
        return "non_mikrotik"
    if classification == "winbox_open_api_closed":
        return "special"
    if classification == "potential_non_mikrotik":
        return "non_mikrotik"
    return "mikrotik_candidate" if ping_ok else "non_mikrotik"


def upsert_device(ip, ping_ok, open_ports, port_states=None, classification=None, db_path=None):
    """Insert a new device or merge into the existing row (dedupe by IP).

    - open_ports: iterable of open port numbers; merged as a union.
    - port_states: {port: state}; later (newer) states win.
    - classification is remapped to mikrotik_candidate/non_mikrotik/special.
    - seen_count is incremented on every re-encounter.
    """
    ping_ok = bool(ping_ok)
    open_ports = sorted({int(p) for p in (open_ports or [])})
    port_states = {str(k): str(v) for k, v in (port_states or {}).items()}
    classification = _normalize_classification(classification, ping_ok)
    ts = _now()
    with _connect(db_path) as conn:
        row = conn.execute("SELECT open_ports, port_states, seen_count, ping_ok FROM devices WHERE ip=?", (ip,)).fetchone()
        if row:
            merged_ports = sorted({int(p) for p in json.loads(row["open_ports"])} | set(open_ports))
            merged_states = {**json.loads(row["port_states"]), **port_states}
            if set(merged_ports) & {8291, 8728}:
                classification = "mikrotik_candidate"
            elif row["classification"] == "mikrotik_candidate":
                classification = "mikrotik_candidate"
            elif classification != "special" and row["classification"] == "special":
                classification = "special"
            seen_count = row["seen_count"] + 1
            conn.execute(
                """UPDATE devices SET ping_ok=?, open_ports=?, port_states=?, classification=?,
                   last_seen=?, seen_count=? WHERE ip=?""",
                (1 if ping_ok else row["ping_ok"], json.dumps(merged_ports),
                 json.dumps(merged_states), classification, ts, seen_count, ip),
            )
        else:
            conn.execute(
                """INSERT INTO devices (ip, ping_ok, open_ports, port_states, classification,
                   first_seen, last_seen, seen_count) VALUES (?,?,?,?,?,?,?,?)""",
                (ip, int(ping_ok), json.dumps(open_ports), json.dumps(port_states),
                 classification, ts, ts, 1),
            )
    return {"ip": ip, "ping_ok": ping_ok, "open_ports": open_ports, "classification": classification}


SORT_COLUMNS = {
    "ip": "ip",
    "ping": "ping_ok",
    "ports": "open_ports",
    "ports_count": "json_array_length(open_ports)",
    "classification": "classification",
    "device_type": "device_type",
    "device_name": "device_name",
    "tags": "tags",
    "first_seen": "first_seen",
    "last_seen": "last_seen",
    "seen_count": "seen_count",
}

def _sort_clause(sort, order):
    col = SORT_COLUMNS.get(sort or "ip", "ip")
    direction = "DESC" if (order or "asc").lower() == "desc" else "ASC"
    return f" ORDER BY {col} {direction}, ip ASC"


# Whitelist of fields the free-text search may target. Using a whitelist keeps
# column names out of user input (SQL-injection safe) and lets the UI request a
# narrow scope (faster than scanning every text column).
SEARCH_FIELDS = {
    "ip": "ip",
    "device_name": "IFNULL(device_name,'')",
    "tags": "IFNULL(tags,'')",
    "device_type": "IFNULL(device_type,'')",
    "interfaces": "IFNULL(interfaces,'')",
    "ip_addresses": "IFNULL(ip_addresses,'')",
    "ip_neighbors": "IFNULL(ip_neighbors,'')",
    "wireless_info": "IFNULL(wireless_info,'')",
    "device_log": "IFNULL(device_log,'')",
    "mac_info": "IFNULL(mac_info,'')",
    "classification": "IFNULL(classification,'')",
}


def build_search_clause(q, q_fields=None):
    """Build the WHERE fragment for free-text search.

    - Whitespace-separated terms are AND-ed: every term must match at least
      one of the searched fields (OR across fields).
    - q_fields: comma-separated field ids (see SEARCH_FIELDS). None, empty or
      "all" searches every whitelisted field; unknown ids are ignored.
    Returns (fragment, params); (None, []) when there is nothing to search.
    """
    terms = [t for t in (q or "").split() if t]
    if not terms:
        return None, []
    wanted = (q_fields or "").strip()
    if wanted and wanted.lower() != "all":
        picked = []
        for fid in wanted.split(","):
            expr = SEARCH_FIELDS.get(fid.strip())
            if expr and expr not in picked:
                picked.append(expr)
    else:
        picked = []
    if not picked:
        picked = list(SEARCH_FIELDS.values())
    term_clauses, term_params = [], []
    for term in terms:
        like = f"%{term}%"
        term_clauses.append("(" + " OR ".join(f"{col} LIKE ?" for col in picked) + ")")
        term_params.extend([like] * len(picked))
    return " AND ".join(term_clauses), term_params

def query_devices(classification=None, has_port=None, q=None, limit=500, offset=0, ping_ok=None,
                  new_only=False, sort="ip", order="asc", device_type=None, db_path=None, q_fields=None):
    """Filter devices. has_port filters by open port number.
    q: free-text search; whitespace-separated terms are AND-ed and each term
    matches any of the searched fields.
    q_fields: comma-separated scope (see SEARCH_FIELDS); None/"all" = every field.
    ping_ok: True -> only ping responders, False -> only non-responders, None -> all.
    new_only: only devices first discovered recently (seen_count == 1 or first_seen
    within NEW_DEVICE_WINDOW seconds) — the "دستگاه‌های جدید" report.
    sort: ip | ping | ports | ports_count | classification | first_seen | last_seen | seen_count
    order: asc | desc
    """
    clauses, params = [], []
    if ping_ok is not None:
        clauses.append("ping_ok=?")
        params.append(1 if ping_ok else 0)
    if classification:
        clauses.append("classification=?")
        params.append(classification)
    if device_type:
        clauses.append("IFNULL(device_type,'')=?")
        params.append(device_type)
    if has_port is not None:
        clauses.append("EXISTS (SELECT 1 FROM json_each(devices.open_ports) WHERE json_each.value=?)")
        params.append(int(has_port))
    if q:
        # Free-text search across the whitelisted display / filter fields
        frag, q_params = build_search_clause(q, q_fields)
        if frag:
            clauses.append(frag)
            params.extend(q_params)
    if new_only:
        clauses.append("(seen_count = 1 OR first_seen >= ?)")
        params.append(_now()[:10])  # same UTC day granularity as ISO timestamps
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    limit = max(1, min(int(limit), 200000))
    offset = max(0, int(offset))
    order_clause = _sort_clause(sort, order)
    with _connect(db_path) as conn:
        rows = conn.execute(
            f"SELECT * FROM devices{where}{order_clause} LIMIT ? OFFSET ?", (*params, limit, offset)
        ).fetchall()
        total = conn.execute(f"SELECT COUNT(*) AS c FROM devices{where}", params).fetchone()["c"]
        new_count = conn.execute(
            "SELECT COUNT(*) AS c FROM devices WHERE seen_count = 1 OR first_seen >= ?",
            (_now()[:10],),
        ).fetchone()["c"]
    devices = [
        {"ip": r["ip"], "ping_ok": bool(r["ping_ok"]), "open_ports": json.loads(r["open_ports"]),
         "port_states": json.loads(r["port_states"]), "classification": r["classification"],
         "first_seen": r["first_seen"], "last_seen": r["last_seen"], "seen_count": r["seen_count"],
         "device_name": r["device_name"] if "device_name" in r.keys() else "",
         "tags": r["tags"] if "tags" in r.keys() else "",
         "ip_addresses": r["ip_addresses"] if "ip_addresses" in r.keys() else "",
         "ip_neighbors": r["ip_neighbors"] if "ip_neighbors" in r.keys() else "",
         "interfaces": r["interfaces"] if "interfaces" in r.keys() else "",
         "device_type": r["device_type"] if "device_type" in r.keys() else "",
         "wireless_info": r["wireless_info"] if "wireless_info" in r.keys() else "",
         "device_log": r["device_log"] if "device_log" in r.keys() else "",
         "mac_info": r["mac_info"] if "mac_info" in r.keys() else ""}
        for r in rows
    ]
    devices = enrich_devices_from_ip_info(devices, db_path=db_path)
    return {"total": total, "new_count": new_count, "limit": limit, "offset": offset, "devices": devices}


def add_manual_device(ip, open_ports=None, classification="mikrotik_candidate", db_path=None):
    """Manually register a device (does not bump seen_count if already known)."""
    import ipaddress
    ipaddress.ip_address(ip)  # raises ValueError for invalid input
    ping_ok = True
    open_ports = sorted({int(p) for p in (open_ports or [])})
    classification = _normalize_classification(classification, ping_ok)
    ts = _now()
    with _connect(db_path) as conn:
        row = conn.execute("SELECT open_ports, port_states, classification FROM devices WHERE ip=?", (ip,)).fetchone()
        if row:
            open_ports = sorted({int(p) for p in json.loads(row["open_ports"])} | set(open_ports))
            classification = classification if classification != "mikrotik_candidate" else row["classification"]
            conn.execute("UPDATE devices SET open_ports=?, port_states=?, classification=? WHERE ip=?",
                         (json.dumps(open_ports), json.dumps({}), classification, ip))
        else:
            conn.execute(
                """INSERT INTO devices (ip, ping_ok, open_ports, port_states, classification,
                   first_seen, last_seen, seen_count) VALUES (?,?,?,?,?,?,?,?)""",
                (ip, int(ping_ok), json.dumps(open_ports), "{}", classification, ts, ts, 1),
            )
    return {"ip": ip, "open_ports": open_ports, "classification": classification}

def devices_to_csv(devices):
    devices = enrich_devices_from_ip_info(list(devices or []))
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "ip", "device_name", "tags", "ping_ok", "open_ports", "port_8291", "port_8728",
        "classification", "first_seen", "last_seen", "seen_count", "ip_addresses", "ip_neighbors", "interfaces", "device_type", "wireless_info",
    ])
    for d in devices:
        states = d.get("port_states", {})
        writer.writerow([
            d["ip"], d.get("device_name") or "", d.get("tags") or "",
            "yes" if d["ping_ok"] else "no", " ".join(map(str, d["open_ports"])),
            states.get("8291", ""), states.get("8728", ""), classification_label(d["classification"]),
            d["first_seen"], d["last_seen"], d["seen_count"],
            d.get("ip_addresses") or "", d.get("ip_neighbors") or "", d.get("interfaces") or "",
            d.get("device_type") or "", d.get("wireless_info") or "",
        ])
    return b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8")




def fetch_devices_by_ips(ips, db_path=None):
    """Return device rows for the given IP list (order preserved when possible)."""
    ips = [str(x).strip() for x in (ips or []) if str(x).strip()]
    if not ips:
        return []
    found = {}
    with _connect(db_path) as conn:
        # chunk to avoid SQLite variable limits
        for i in range(0, len(ips), 400):
            chunk = ips[i : i + 400]
            q = ",".join("?" * len(chunk))
            rows = conn.execute(f"SELECT * FROM devices WHERE ip IN ({q})", chunk).fetchall()
            for r in rows:
                found[r["ip"]] = {
                    "ip": r["ip"],
                    "ping_ok": bool(r["ping_ok"]),
                    "open_ports": json.loads(r["open_ports"]),
                    "port_states": json.loads(r["port_states"]),
                    "classification": r["classification"],
                    "first_seen": r["first_seen"],
                    "last_seen": r["last_seen"],
                    "seen_count": r["seen_count"],
                    "device_name": r["device_name"] if "device_name" in r.keys() else "",
                    "tags": r["tags"] if "tags" in r.keys() else "",
                    "ip_addresses": r["ip_addresses"] if "ip_addresses" in r.keys() else "",
                    "ip_neighbors": r["ip_neighbors"] if "ip_neighbors" in r.keys() else "",
                    "interfaces": r["interfaces"] if "interfaces" in r.keys() else "",
                    "device_type": r["device_type"] if "device_type" in r.keys() else "",
                    "wireless_info": r["wireless_info"] if "wireless_info" in r.keys() else "",
                    "device_log": r["device_log"] if "device_log" in r.keys() else "",
                    "mac_info": r["mac_info"] if "mac_info" in r.keys() else "",
                }
    return enrich_devices_from_ip_info([found[ip] for ip in ips if ip in found], db_path=db_path)



def _ip_info_dir(db_path=None):
    """Directory of per-device ip_info files next to the given database.

    `db_path` may be a filesystem path (str/Path, as taken by query_devices)
    or a database NAME; None means the active database.
    """
    from pathlib import Path as _P
    if db_path:
        p = _P(str(db_path))
        # A real filesystem path: has a suffix (.db) or spans several parts.
        # Database names can never contain dots or path separators (they are
        # sanitized), so this check cannot misclassify a plain name.
        if p.suffix == ".db" or len(p.parts) > 1:
            return p.parent / "ip_info"
        return db_path_for(str(db_path)).parent / "ip_info"
    return db_path_for().parent / "ip_info"


def _parse_ip_info_file(text: str) -> dict:
    """Parse backend/ip_info/{ip}.txt sections into field dict."""
    out = {"interfaces": "", "ip_addresses": "", "ip_neighbors": "", "wireless_info": "", "device_log": "", "mac_info": "", "device_name": "", "device_type": ""}
    if not text:
        return out
    # identity / device_type lines
    for line in text.splitlines():
        low = line.strip()
        if low.lower().startswith("identity:"):
            out["device_name"] = low.split(":", 1)[1].strip().strip("-")
        elif low.lower().startswith("device_type:"):
            out["device_type"] = low.split(":", 1)[1].strip().strip("-")
    sections = {
        "interfaces": ("----- interfaces -----",),
        "wireless_info": ("----- wireless -----", "----- wireless_info -----"),
        "ip_addresses": ("----- ip_addresses -----", "----- ip_addresses / routes -----"),
        "ip_neighbors": ("----- neighbors -----", "----- ip_neighbors -----"),
    }
    # split by section headers
    parts = re.split(r"(?m)^----- .+ -----\s*$", text)
    headers = re.findall(r"(?m)^----- (.+?) -----\s*$", text)
    # headers list aligns with parts[1:]
    body_map = {}
    for h, body in zip(headers, parts[1:]):
        body_map[h.strip().lower()] = body.strip()
    def _body(*names):
        for n in names:
            for k, v in body_map.items():
                if n.lower() in k or k in n.lower():
                    if v and v.strip() not in ("(empty)", "-"):
                        return v.strip()
        return ""
    out["interfaces"] = _body("interfaces")
    out["wireless_info"] = _body("wireless", "wireless_info")
    out["device_log"] = _body("log", "device_log", "logs")
    out["mac_info"] = _body("mac", "mac_info", "arp")
    out["ip_addresses"] = _body("ip_addresses", "ip_addresses / routes", "routes")
    out["ip_neighbors"] = _body("neighbors", "ip_neighbors")
    return out


def enrich_devices_from_ip_info(devices, db_path=None):
    """Fill empty interfaces/ip_addresses/neighbors/wireless from ip_info/{ip}.txt if present."""
    if not devices:
        return devices
    info_dir = _ip_info_dir(db_path)
    if not info_dir.is_dir():
        return devices
    for d in devices:
        ip = (d.get("ip") or "").strip()
        if not ip:
            continue
        need = not (d.get("interfaces") or d.get("ip_addresses") or d.get("ip_neighbors") or d.get("wireless_info"))
        if not need:
            # still fill individual empties
            pass
        safe = ip.replace(":", "_").replace("/", "_")
        fpath = info_dir / f"{safe}.txt"
        if not fpath.is_file():
            continue
        try:
            parsed = _parse_ip_info_file(fpath.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        for key in ("interfaces", "ip_addresses", "ip_neighbors", "wireless_info", "device_log", "mac_info"):
            if not (d.get(key) or "").strip() and (parsed.get(key) or "").strip():
                d[key] = parsed[key]
        if not (d.get("device_name") or "").strip() and (parsed.get("device_name") or "").strip():
            d["device_name"] = parsed["device_name"]
        if not (d.get("device_type") or "").strip() and (parsed.get("device_type") or "").strip():
            d["device_type"] = parsed["device_type"]
    return devices



def _xlsx_safe(val) -> str:
    """Strip characters illegal in Excel XML cells (openpyxl)."""
    if val is None:
        return ""
    s = str(val)
    # Excel forbids most C0 controls except tab/lf/cr
    return "".join(ch for ch in s if ord(ch) >= 32 or ch in "\t\n\r")



def _xlsx_compact(text: str, max_len: int = 800) -> str:
    """Make multi-line probe text visible in a single Excel row height."""
    if not text:
        return ""
    s = _xlsx_safe(text)
    lines = []
    for ln in s.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("==="):
            continue
        parts = ln.split(None, 1)
        if parts and parts[0].isdigit() and len(parts) > 1:
            ln = parts[1]
        lines.append(ln)
    if not lines:
        collapsed = " | ".join(x.strip() for x in s.splitlines() if x.strip())
        return collapsed[:max_len]
    joined = " | ".join(lines)
    if len(joined) > max_len:
        return joined[: max_len - 1] + "…"
    return joined


def _parse_kv_line(line: str) -> dict:
    """Parse 'key=value key2=value2' style lines from RouterOS dumps."""
    out = {}
    line = (line or "").strip()
    if not line:
        return out
    parts = line.split(None, 1)
    if parts and parts[0].isdigit() and len(parts) > 1:
        line = parts[1]
    for m in re.finditer(r"([A-Za-z_][\w\-.]*)=([^\s]+)", line):
        out[m.group(1)] = m.group(2).strip()
    return out


def _section_lines(text: str) -> list:
    if not text:
        return []
    lines = []
    for ln in str(text).splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("==="):
            continue
        lines.append(ln)
    return lines


def devices_to_xlsx(devices) -> bytes:
    """Build Excel workbook with visible main sheet + structured detail sheets."""
    devices = enrich_devices_from_ip_info(list(devices or []))
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    import io as _io

    wb = Workbook()
    ws = wb.active
    ws.title = "devices"
    header_labels = [
        "IP", "نام دستگاه", "نوع دستگاه", "تگ", "پینگ", "پورت‌های باز",
        "8291", "8728", "دسته‌بندی", "اولین مشاهده", "آخرین مشاهده",
        "تعداد مشاهده", "آدرس‌های IP", "همسایه‌ها", "اینترفیس‌ها", "وایرلس",
    ]
    ws.append(header_labels)
    header_fill = PatternFill("solid", fgColor="123B5D")
    header_font = Font(bold=True, color="FFFFFF")
    thin = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1"),
    )

    def style_header(sheet, ncols):
        for col in range(1, ncols + 1):
            cell = sheet.cell(1, col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin
        sheet.row_dimensions[1].height = 22
        sheet.freeze_panes = "A2"

    style_header(ws, len(header_labels))

    sh_if = wb.create_sheet("اینترفیس‌ها")
    sh_if.append(["IP", "نام دستگاه", "name", "type", "running"])
    style_header(sh_if, 5)

    sh_ip = wb.create_sheet("آدرس‌های IP")
    sh_ip.append(["IP", "نام دستگاه", "address", "interface", "network", "نوع", "متن"])
    style_header(sh_ip, 7)

    sh_nb = wb.create_sheet("همسایه‌ها")
    sh_nb.append(["IP", "نام دستگاه", "identity", "address", "interface"])
    style_header(sh_nb, 5)

    sh_wl = wb.create_sheet("وایرلس")
    sh_wl.append(["IP", "نام دستگاه", "name", "mode", "ssid", "band", "frequency"])
    style_header(sh_wl, 7)

    for d in devices:
        states = d.get("port_states") or {}
        if not isinstance(states, dict):
            states = {}
        states_s = {str(k): str(v) for k, v in states.items()}

        ip_addresses = d.get("ip_addresses") or ""
        ip_neighbors = d.get("ip_neighbors") or ""
        interfaces = d.get("interfaces") or ""
        wireless_info = d.get("wireless_info") or ""
        ip = d.get("ip") or ""
        name = _xlsx_safe(d.get("device_name") or "")

        ws.append([
            ip,
            name,
            _xlsx_safe(d.get("device_type") or ""),
            _xlsx_safe(d.get("tags") or ""),
            "yes" if d.get("ping_ok") else "no",
            " ".join(map(str, d.get("open_ports") or [])),
            states_s.get("8291", ""),
            states_s.get("8728", ""),
            classification_label(d.get("classification") or ""),
            d.get("first_seen") or "",
            d.get("last_seen") or "",
            d.get("seen_count") if d.get("seen_count") is not None else "",
            _xlsx_compact(ip_addresses),
            _xlsx_compact(ip_neighbors),
            _xlsx_compact(interfaces),
            _xlsx_compact(wireless_info),
        ])

        for ln in _section_lines(interfaces):
            kv = _parse_kv_line(ln)
            sh_if.append([ip, name, kv.get("name") or "", kv.get("type") or "", kv.get("running") or kv.get("disabled") or ""])

        in_routes = False
        for ln in str(ip_addresses).splitlines():
            raw = ln.strip()
            if not raw:
                continue
            if raw.startswith("==="):
                in_routes = "route" in raw.lower()
                continue
            kv = _parse_kv_line(raw)
            if in_routes or raw.startswith("dst=") or " dst=" in raw:
                sh_ip.append([ip, name, kv.get("dst") or kv.get("dst-address") or "", kv.get("gw") or kv.get("gateway") or "", "", "route", _xlsx_safe(raw)])
            else:
                sh_ip.append([ip, name, kv.get("address") or "", kv.get("interface") or "", kv.get("network") or "", "address", _xlsx_safe(raw)])

        for ln in _section_lines(ip_neighbors):
            kv = _parse_kv_line(ln)
            sh_nb.append([ip, name, kv.get("identity") or "", kv.get("address") or "", kv.get("interface") or ""])

        for ln in _section_lines(wireless_info):
            kv = _parse_kv_line(ln)
            sh_wl.append([ip, name, kv.get("name") or "", kv.get("mode") or "", kv.get("ssid") or "", kv.get("band") or "", kv.get("frequency") or ""])

    widths = [16, 24, 12, 18, 8, 18, 8, 8, 16, 20, 20, 12, 48, 48, 48, 40]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=len(header_labels)):
        for cell in row:
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            cell.border = thin

    def finish_sheet(sheet, col_widths):
        for i, w in enumerate(col_widths, 1):
            sheet.column_dimensions[get_column_letter(i)].width = w
        for row in sheet.iter_rows(min_row=2, max_row=max(2, sheet.max_row), max_col=len(col_widths)):
            for cell in row:
                cell.alignment = Alignment(vertical="center", wrap_text=True)
                cell.border = thin
        if sheet.max_row >= 1:
            sheet.auto_filter.ref = f"A1:{get_column_letter(len(col_widths))}{sheet.max_row}"

    finish_sheet(sh_if, [16, 24, 18, 12, 12])
    finish_sheet(sh_ip, [16, 24, 22, 18, 18, 10, 40])
    finish_sheet(sh_nb, [16, 24, 28, 18, 24])
    finish_sheet(sh_wl, [16, 24, 16, 16, 22, 12, 12])
    ws.auto_filter.ref = f"A1:{get_column_letter(len(header_labels))}{max(1, ws.max_row)}"

    buf = _io.BytesIO()
    wb.save(buf)
    return buf.getvalue()



def update_device_fields(ip: str, device_name=None, tags=None, ip_addresses=None, ip_neighbors=None, interfaces=None, device_type=None, wireless_info=None, device_log=None, mac_info=None, db_path=None):
    """Update manually-editable metadata without touching scan data."""
    if not ip:
        raise ValueError("IP لازم است")
    sets, params = [], []
    if device_name is not None:
        sets.append("device_name=?")
        params.append(str(device_name)[:128])
    if tags is not None:
        if isinstance(tags, (list, tuple)):
            tags = ", ".join(str(t).strip() for t in tags if str(t).strip())
        sets.append("tags=?")
        params.append(str(tags)[:4000])
    if ip_addresses is not None:
        sets.append("ip_addresses=?")
        params.append(str(ip_addresses)[:100000])
    if ip_neighbors is not None:
        sets.append("ip_neighbors=?")
        params.append(str(ip_neighbors)[:100000])
    if interfaces is not None:
        sets.append("interfaces=?")
        params.append(str(interfaces)[:100000])
    if device_type is not None:
        dt = str(device_type).strip()
        if dt and dt not in ("AP", "ST", "Router", ""):
            # normalize common variants
            low = dt.lower()
            if low in ("ap", "access-point", "accesspoint", "cap"):
                dt = "AP"
            elif low in ("st", "station", "sta", "cpe"):
                dt = "ST"
            elif low in ("router", "rtr", "rb"):
                dt = "Router"
        sets.append("device_type=?")
        params.append(dt[:32])
    if wireless_info is not None:
        sets.append("wireless_info=?")
        params.append(str(wireless_info)[:100000])
    if device_log is not None:
        sets.append("device_log=?")
        params.append(str(device_log)[:200000])
    if mac_info is not None:
        sets.append("mac_info=?")
        params.append(str(mac_info)[:100000])
    if not sets:
        raise ValueError("فیلدی برای به‌روزرسانی ارسال نشده")
    params.append(ip)
    with _connect(db_path) as conn:
        cur = conn.execute(f"UPDATE devices SET {', '.join(sets)} WHERE ip=?", params)
        if cur.rowcount == 0:
            raise KeyError(ip)
    return {"ip": ip, "device_name": device_name, "tags": tags, "ip_addresses": ip_addresses, "ip_neighbors": ip_neighbors, "interfaces": interfaces, "device_type": device_type, "wireless_info": wireless_info, "device_log": device_log, "mac_info": mac_info}


def upsert_devices_batch(hosts, db_path=None):
    """Upsert many hosts in ONE transaction (single commit) for speed.

    hosts: iterable of dicts with keys ip, ping_ok, open_ports, port_states,
    classification (same shapes as upsert_device accepts).
    Merging semantics match upsert_device: open ports union, port states merged
    (newer win), seen_count incremented, classification remapped. Merging also
    happens between rows in the batch itself (dedupe by IP).
    """
    merged = {}  # ip -> row dict
    for host in hosts:
        ip = host["ip"]
        ping_ok = bool(host.get("ping_ok"))
        open_ports = sorted({int(p) for p in (host.get("open_ports") or [])})
        port_states = {str(k): str(v) for k, v in (host.get("port_states") or {}).items()}
        classification = _normalize_classification(host.get("classification"), ping_ok)
        row = merged.get(ip)
        if row is None:
            merged[ip] = {"ping_ok": ping_ok, "open_ports": set(open_ports),
                          "port_states": dict(port_states), "classification": classification,
                          "seen": 1}
        else:
            row["open_ports"] |= set(open_ports)
            row["port_states"].update(port_states)
            row["ping_ok"] = row["ping_ok"] or ping_ok
            if set(open_ports) & {8291, 8728}:
                row["classification"] = "mikrotik_candidate"
            elif row["classification"] == "mikrotik_candidate":
                pass
            elif classification == "special" or row["classification"] == "special":
                row["classification"] = "special" if classification == "special" else row["classification"]
            row["seen"] += 1
    if not merged:
        return []
    ts = _now()
    results = []
    with _connect(db_path) as conn:
        conn.execute("PRAGMA synchronous=NORMAL")
        existing = {}
        ips = list(merged)
        for i in range(0, len(ips), 500):
            chunk = ips[i:i + 500]
            rows = conn.execute(
                f"SELECT ip, open_ports, port_states, seen_count, ping_ok, classification FROM devices WHERE ip IN ({','.join('?' * len(chunk))})",
                chunk,
            ).fetchall()
            existing.update({r["ip"]: r for r in rows})
        updates, inserts = [], []
        for ip, row in merged.items():
            old = existing.get(ip)
            if old:
                open_ports = sorted(row["open_ports"] | {int(p) for p in json.loads(old["open_ports"])})
                port_states = {**json.loads(old["port_states"]), **row["port_states"]}
                classification = row["classification"]
                if set(open_ports) & {8291, 8728}:
                    classification = "mikrotik_candidate"
                elif old["classification"] == "mikrotik_candidate":
                    classification = "mikrotik_candidate"
                elif classification != "special" and old["classification"] == "special":
                    classification = "special"
                updates.append((1 if row["ping_ok"] else old["ping_ok"], json.dumps(open_ports),
                                json.dumps(port_states), classification, ts,
                                old["seen_count"] + row["seen"], ip))
            else:
                open_ports = sorted(row["open_ports"])
                inserts.append((ip, int(row["ping_ok"]), json.dumps(open_ports),
                                json.dumps(row["port_states"]), row["classification"], ts, ts, row["seen"]))
        if updates:
            conn.executemany(
                """UPDATE devices SET ping_ok=?, open_ports=?, port_states=?, classification=?,
                   last_seen=?, seen_count=? WHERE ip=?""", updates)
        if inserts:
            conn.executemany(
                """INSERT INTO devices (ip, ping_ok, open_ports, port_states, classification,
                   first_seen, last_seen, seen_count) VALUES (?,?,?,?,?,?,?,?)""", inserts)
    for ip, row in merged.items():
        results.append({"ip": ip, "ping_ok": row["ping_ok"],
                        "open_ports": sorted(row["open_ports"]),
                        "classification": row["classification"]})
    return results



def dedupe_devices(by: str = "device_name", db_path=None) -> dict:
    """Remove duplicate rows.

    by=device_name: keep one row per non-empty identity name (latest last_seen wins).
    by=ip: no-op (ip is primary key).
    Returns counts of removed / kept.
    """
    path = db_path if db_path is not None else db_path_for()
    if by not in ("device_name", "name", "identity"):
        raise ValueError("معیار حذف تکراری نامعتبر است (device_name)")
    removed = 0
    kept = 0
    with _connect(path) as conn:
        rows = conn.execute(
            """SELECT ip, device_name, last_seen, seen_count, open_ports FROM devices
               WHERE IFNULL(device_name,'') != ''
               ORDER BY device_name COLLATE NOCASE, last_seen DESC, seen_count DESC"""
        ).fetchall()
        seen_names = set()
        to_delete = []
        for r in rows:
            key = (r["device_name"] or "").strip().lower()
            if not key:
                continue
            if key in seen_names:
                to_delete.append(r["ip"])
            else:
                seen_names.add(key)
                kept += 1
        if to_delete:
            for i in range(0, len(to_delete), 400):
                chunk = to_delete[i:i+400]
                conn.execute(
                    f"DELETE FROM devices WHERE ip IN ({','.join('?'*len(chunk))})",
                    chunk,
                )
            removed = len(to_delete)
        total = conn.execute("SELECT COUNT(*) AS c FROM devices").fetchone()["c"]
    return {"removed": removed, "kept_unique_names": kept, "total_remaining": total}


def delete_devices(ips: list, db_path=None) -> dict:
    path = db_path if db_path is not None else db_path_for()
    ips = [str(x).strip() for x in (ips or []) if str(x).strip()]
    if not ips:
        return {"deleted": 0}
    with _connect(path) as conn:
        deleted = 0
        for i in range(0, len(ips), 400):
            chunk = ips[i:i+400]
            cur = conn.execute(
                f"DELETE FROM devices WHERE ip IN ({','.join('?'*len(chunk))})",
                chunk,
            )
            deleted += cur.rowcount
    return {"deleted": deleted}


def transfer_hosts_to_db(hosts: list, target_db: str) -> dict:
    """Upsert scan host dicts into a named database (not necessarily active)."""
    n = _safe_db_name(target_db)
    cat = _read_catalog()
    if n not in cat.get("databases", []):
        cat.setdefault("databases", []).append(n)
        _write_catalog(cat)
    path = db_path_for(n)
    init_db(path)
    results = upsert_devices_batch(hosts, db_path=path)
    return {"database": n, "upserted": len(results), "path": str(path)}

# ---------------- settings (key/value) ----------------

def get_setting(key: str, default=None, db_path=None):
    with _connect(db_path) as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str, db_path=None):
    ts = _now()
    with _connect(db_path) as conn:
        conn.execute(
            """INSERT INTO settings (key, value, updated_at) VALUES (?,?,?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
            (key, str(value), ts),
        )
    return {"key": key, "value": str(value), "updated_at": ts}


def list_settings(db_path=None):
    with _connect(db_path) as conn:
        rows = conn.execute("SELECT key, value, updated_at FROM settings ORDER BY key").fetchall()
        return [dict(r) for r in rows]


def get_all_settings(db_path=None) -> dict:
    """Return all settings as a plain {key: value} mapping."""
    with _connect(db_path) as conn:
        rows = conn.execute("SELECT key, value FROM settings ORDER BY key").fetchall()
        return {r["key"]: r["value"] for r in rows}


# ---------------- backup / restore ----------------

def backup_db_bytes(db_path=None) -> bytes:
    """Return a consistent snapshot of the SQLite database as bytes."""
    path = Path(db_path) if db_path is not None else db_path_for()
    if not path.is_file():
        raise FileNotFoundError(f"دیتابیس یافت نشد: {path}")
    # Use SQLite backup API for a consistent copy even while writers are active.
    import tempfile
    with _LOCK:
        src = sqlite3.connect(str(path), timeout=30)
        try:
            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                dst = sqlite3.connect(tmp_path)
                try:
                    src.backup(dst)
                finally:
                    dst.close()
                return Path(tmp_path).read_bytes()
            finally:
                try:
                    Path(tmp_path).unlink(missing_ok=True)
                except OSError:
                    pass
        finally:
            src.close()


def restore_db_bytes(data: bytes, db_path=None) -> dict:
    """Replace devices.db with uploaded bytes after validating it is a SQLite DB with devices table."""
    if not data or len(data) < 100:
        raise ValueError("فایل پشتیبان خالی یا خیلی کوچک است")
    if data[:16] != b"SQLite format 3\x00":
        raise ValueError("فایل پشتیبان یک دیتابیس SQLite معتبر نیست")
    import tempfile
    # Validate schema on a temp copy first
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        conn = sqlite3.connect(tmp_path, timeout=10)
        try:
            tables = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
            if "devices" not in tables:
                raise ValueError("جدول devices در فایل پشتیبان وجود ندارد")
            count = conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
        finally:
            conn.close()
        path = Path(db_path) if db_path is not None else db_path_for()
        path.parent.mkdir(parents=True, exist_ok=True)
        # Atomic-ish replace under lock
        with _LOCK:
            bak = path.with_suffix(path.suffix + ".pre_restore")
            if path.exists():
                try:
                    if bak.exists():
                        bak.unlink()
                    path.replace(bak)
                except OSError:
                    pass
            # copy validated temp over target (replace may fail across volumes)
            import shutil
            shutil.copy2(tmp_path, path)
            conn2 = sqlite3.connect(str(path), timeout=30)
            try:
                conn2.executescript(_SCHEMA)
                # migrations then indexes (indexes need migrated columns)
                existing = {r[1] for r in conn2.execute("PRAGMA table_info(devices)").fetchall()}
                for col, decl in _MIGRATE_COLUMNS:
                    if col not in existing:
                        conn2.execute(f"ALTER TABLE devices ADD COLUMN {col} {decl}")
                for ddl in _INDEX_DDL:
                    conn2.execute(ddl)
                conn2.commit()
            finally:
                conn2.close()
        return {
            "ok": True,
            "devices": count,
            "path": str(path),
            "database": get_active_db_name() if db_path is None else Path(path).stem,
        }
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except OSError:
            pass


def export_backup_bytes(db_path=None) -> bytes:
    """Export devices and settings as a validated, portable JSON backup."""
    with _connect(db_path) as conn:
        device_rows = conn.execute("SELECT * FROM devices ORDER BY ip").fetchall()
        settings_rows = conn.execute("SELECT key, value FROM settings ORDER BY key").fetchall()
    devices = []
    for row in device_rows:
        item = dict(row)
        for key in ("ping_ok",):
            item[key] = bool(item.get(key))
        for key in ("open_ports", "port_states"):
            try:
                item[key] = json.loads(item.get(key) or ("[]" if key == "open_ports" else "{}"))
            except (TypeError, ValueError):
                item[key] = [] if key == "open_ports" else {}
        devices.append(item)
    payload = {
        "app": "mikrotik_scanner",
        "version": 1,
        "created_at": _now(),
        "devices": devices,
        "settings": {row["key"]: row["value"] for row in settings_rows},
    }
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def restore_backup_bytes(data: bytes, db_path=None) -> dict:
    """Restore a portable JSON backup after validating its complete structure."""
    if not isinstance(data, (bytes, bytearray)) or not data:
        raise ValueError("فایل پشتیبان خالی یا نامعتبر است")
    try:
        payload = json.loads(bytes(data).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("ساختار JSON فایل پشتیبان معتبر نیست") from exc
    if not isinstance(payload, dict) or payload.get("app") != "mikrotik_scanner":
        raise ValueError("نوع فایل پشتیبان معتبر نیست")
    devices = payload.get("devices")
    settings = payload.get("settings")
    if not isinstance(devices, list) or not isinstance(settings, dict):
        raise ValueError("فایل پشتیبان باید شامل devices و settings معتبر باشد")
    for item in devices:
        if not isinstance(item, dict) or not isinstance(item.get("ip"), str) or not item["ip"].strip():
            raise ValueError("رکورد دستگاه در فایل پشتیبان نامعتبر است")
    if any(not isinstance(k, str) or not isinstance(v, (str, int, float, bool)) for k, v in settings.items()):
        raise ValueError("تنظیمات فایل پشتیبان نامعتبر است")

    path = Path(db_path) if db_path is not None else db_path_for()
    init_db(path)
    with _connect(path) as conn:
        # Restore atomically from the validated payload.
        conn.execute("DELETE FROM devices")
        conn.execute("DELETE FROM settings")
        columns = {r[1] for r in conn.execute("PRAGMA table_info(devices)").fetchall()}
        device_count = 0
        for item in devices:
            record = dict(item)
            record["ip"] = record["ip"].strip()
            record["ping_ok"] = int(bool(record.get("ping_ok", False)))
            record["open_ports"] = json.dumps(record.get("open_ports") or [], ensure_ascii=False)
            record["port_states"] = json.dumps(record.get("port_states") or {}, ensure_ascii=False)
            record.setdefault("classification", _normalize_classification("", bool(record["ping_ok"])))
            record.setdefault("first_seen", _now())
            record.setdefault("last_seen", record["first_seen"])
            record.setdefault("seen_count", 1)
            record.setdefault("device_name", "")
            record.setdefault("tags", "")
            record.setdefault("ip_addresses", "")
            record.setdefault("ip_neighbors", "")
            record.setdefault("interfaces", "")
            record.setdefault("device_type", "")
            record.setdefault("wireless_info", "")
            record.setdefault("device_log", "")
            record.setdefault("mac_info", "")
            names = [key for key in record if key in columns]
            conn.execute(
                f"INSERT INTO devices ({','.join(names)}) VALUES ({','.join('?' for _ in names)})",
                [record[key] for key in names],
            )
            device_count += 1
        for key, value in settings.items():
            conn.execute(
                "INSERT INTO settings (key, value, updated_at) VALUES (?,?,?)",
                (key, str(value), _now()),
            )
    return {
        "ok": True,
        "devices_restored": device_count,
        "devices_total": device_count,
        "settings_restored": len(settings),
        "settings_total": len(settings),
        "path": str(path),
    }


# ---------------- tag import + full project backup/restore ----------------

def apply_tags_by_ip(rows: list, db_path=None) -> dict:
    """Apply tags from a list of {ip, tags} dicts onto matching devices.

    Returns counts: updated, missing (IP not in DB), skipped (empty).
    """
    updated = 0
    missing = []
    skipped = 0
    path = Path(db_path) if db_path is not None else db_path_for()
    with _connect(path) as conn:
        for item in rows:
            ip = str(item.get("ip") or "").strip()
            tag = item.get("tags")
            if tag is None:
                tag = item.get("tag") or item.get("TAG") or ""
            tag = str(tag).strip()
            if not ip:
                skipped += 1
                continue
            # normalize trivial IP
            try:
                import ipaddress
                ip = str(ipaddress.IPv4Address(ip))
            except Exception:
                pass
            row = conn.execute("SELECT ip, tags FROM devices WHERE ip=?", (ip,)).fetchone()
            if not row:
                missing.append(ip)
                continue
            # Append new tag to existing text with a single space (no replace).
            existing = (row["tags"] if "tags" in row.keys() else "") or ""
            existing = str(existing).strip()
            if not tag:
                skipped += 1
                continue
            if existing:
                # avoid exact duplicate token if already present as whole suffix/segment
                if tag in existing.split():
                    # already present as a whitespace-separated token — leave unchanged
                    continue
                merged = f"{existing} {tag}"
            else:
                merged = tag
            conn.execute("UPDATE devices SET tags=? WHERE ip=?", (merged[:512], ip))
            updated += 1
    return {
        "ok": True,
        "updated": updated,
        "missing": missing,
        "missing_count": len(missing),
        "skipped": skipped,
        "total_rows": len(rows),
        "database": get_active_db_name() if db_path is None else Path(path).stem,
    }


def full_backup_zip_bytes() -> bytes:
    """Zip all project databases + config JSON files into one archive."""
    import io
    import zipfile
    import shutil

    buf = io.BytesIO()
    meta = {
        "format": "mikrotik_scanner_full_backup_v1",
        "created_at": _now(),
        "active": _read_catalog().get("active", "default"),
        "databases": list(_read_catalog().get("databases", ["default"])),
    }
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("meta.json", json.dumps(meta, ensure_ascii=False, indent=2))
        # catalog
        if _CATALOG.is_file():
            zf.write(_CATALOG, "databases/catalog.json")
        else:
            zf.writestr("databases/catalog.json", json.dumps(_read_catalog(), ensure_ascii=False, indent=2))
        # each named database (consistent snapshot via backup API)
        cat = _read_catalog()
        for name in cat.get("databases", ["default"]):
            try:
                p = db_path_for(name)
            except Exception:
                p = _DB_DIR / f"{name}.db"
            if not p.is_file():
                continue
            try:
                data = backup_db_bytes(p)
                zf.writestr(f"databases/{name}.db", data)
            except Exception:
                # fall back to raw copy
                zf.write(p, f"databases/{name}.db")
        # config files at project root
        for fname in ("snmp_profiles.json", "vpn_profiles.json", "smtp_config.json", "ip_olom.txt"):
            fp = _ROOT / fname
            if fp.is_file():
                zf.write(fp, fname)
        # optional ip_info folder next to databases
        info_dir = _DB_DIR / "ip_info"
        if info_dir.is_dir():
            for f in info_dir.glob("*.txt"):
                zf.write(f, f"ip_info/{f.name}")
        # also project-root ip_info if present
        root_info = _ROOT / "ip_info"
        if root_info.is_dir():
            for f in root_info.glob("*.txt"):
                arc = f"ip_info/{f.name}"
                # avoid overwrite if already written from databases/ip_info
                try:
                    zf.getinfo(arc)
                except KeyError:
                    zf.write(f, arc)
    return buf.getvalue()


def full_restore_from_zip(data: bytes) -> dict:
    """Restore databases + config files from a full-backup ZIP."""
    import io
    import zipfile
    import shutil
    import tempfile

    if not data or len(data) < 50:
        raise ValueError("فایل پشتیبان خالی یا خیلی کوچک است")
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as e:
        raise ValueError("فایل ZIP معتبر نیست") from e

    names = zf.namelist()
    # Accept either full backup format or a zip that at least contains *.db
    db_members = [n for n in names if n.replace("\\", "/").endswith(".db")]
    if not db_members:
        raise ValueError("در فایل ZIP هیچ دیتابیس (.db) یافت نشد")

    restored_dbs = []
    restored_files = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        zf.extractall(tmp_path)
        # normalize paths
        def find(rel: str):
            p = tmp_path / rel
            if p.is_file():
                return p
            # case-insensitive walk
            for f in tmp_path.rglob("*"):
                if f.is_file() and f.name.lower() == Path(rel).name.lower():
                    return f
            return None

        # catalog
        cat_file = find("databases/catalog.json") or find("catalog.json")
        if cat_file and cat_file.is_file():
            try:
                cat_data = json.loads(cat_file.read_text(encoding="utf-8"))
                if isinstance(cat_data, dict) and "databases" in cat_data:
                    _DB_DIR.mkdir(parents=True, exist_ok=True)
                    _write_catalog(cat_data)
                    restored_files.append("databases/catalog.json")
            except (OSError, ValueError):
                pass

        # restore each .db via validated restore_db_bytes
        for member in db_members:
            member = member.replace("\\", "/")
            src = tmp_path / member
            if not src.is_file():
                continue
            name = Path(member).stem
            # skip catalog-looking names
            if name.lower() in ("catalog",):
                continue
            try:
                raw = src.read_bytes()
                # target path under databases/
                target = _DB_DIR / f"{name}.db"
                result = restore_db_bytes(raw, db_path=target)
                # ensure name is in catalog
                cat = _read_catalog()
                if name not in cat.get("databases", []):
                    cat.setdefault("databases", []).append(name)
                    _write_catalog(cat)
                restored_dbs.append({"name": name, "devices": result.get("devices", 0)})
            except Exception as e:
                restored_dbs.append({"name": name, "error": str(e)})

        # config files
        for fname in ("snmp_profiles.json", "vpn_profiles.json", "smtp_config.json", "ip_olom.txt"):
            src = find(fname)
            if src and src.is_file():
                dest = _ROOT / fname
                shutil.copy2(src, dest)
                restored_files.append(fname)

        # ip_info
        info_src = tmp_path / "ip_info"
        if info_src.is_dir():
            dest_info = _DB_DIR / "ip_info"
            dest_info.mkdir(parents=True, exist_ok=True)
            for f in info_src.glob("*.txt"):
                shutil.copy2(f, dest_info / f.name)
                restored_files.append(f"ip_info/{f.name}")

    return {
        "ok": True,
        "format": "mikrotik_scanner_full_backup_v1",
        "databases": restored_dbs,
        "files": restored_files,
        "active": get_active_db_name(),
    }
