import os
import json
import threading
import datetime

_lock = threading.Lock()
_DB_URL = os.environ.get('DATABASE_URL', '')

# ── PostgreSQL backend ────────────────────────────────────────────────────────

def _get_conn():
    import psycopg2
    url = _DB_URL
    if url.startswith('postgres://'):
        url = 'postgresql://' + url[len('postgres://'):]
    return psycopg2.connect(url)


def _ensure_table():
    try:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kv_store (
                name TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                started_at TIMESTAMP DEFAULT NOW(),
                count      INTEGER,
                domain     TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id         SERIAL PRIMARY KEY,
                session_id TEXT REFERENCES sessions(session_id) ON DELETE CASCADE,
                uid        TEXT NOT NULL,
                password   TEXT NOT NULL,
                name       TEXT DEFAULT '',
                email      TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            ALTER TABLE accounts
                ADD COLUMN IF NOT EXISTS name  TEXT DEFAULT '',
                ADD COLUMN IF NOT EXISTS email TEXT DEFAULT ''
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f'[storage] DB init error: {e}')


_db_ready = False

def _init_db():
    global _db_ready
    if not _db_ready and _DB_URL:
        _ensure_table()
        _migrate_json_to_db()
        _db_ready = True


def _migrate_json_to_db():
    """On first startup with DB, copy any existing JSON files into the database."""
    for name in ('keys', 'domains'):
        existing = _db_load_raw(name)
        if existing is not None:
            continue
        try:
            with open(f'{name}.json') as f:
                data = json.load(f)
            if data:
                _db_save_raw(name, data)
                print(f'[storage] Migrated {name}.json → database ✓')
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f'[storage] Migration error ({name}): {e}')


def _db_load_raw(name):
    try:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT data FROM kv_store WHERE name = %s", (name,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return json.loads(row[0])
    except Exception as e:
        print(f'[storage] DB load error ({name}): {e}')
    return None


def _db_save_raw(name, data):
    try:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO kv_store (name, data) VALUES (%s, %s)
            ON CONFLICT (name) DO UPDATE SET data = EXCLUDED.data
        """, (name, json.dumps(data)))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f'[storage] DB save error ({name}): {e}')
    return False


def _db_load(name):
    _init_db()
    return _db_load_raw(name)


def _db_save(name, data):
    _init_db()
    return _db_save_raw(name, data)


# ── File backend ──────────────────────────────────────────────────────────────

def _file_load(name):
    try:
        with open(f'{name}.json') as f:
            return json.load(f)
    except Exception:
        return None


def _file_save(name, data):
    try:
        with open(f'{name}.json', 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f'[storage] File save error ({name}): {e}')
    return False


# ── Public KV API ─────────────────────────────────────────────────────────────

def load(name, default=None):
    with _lock:
        if _DB_URL:
            result = _db_load(name)
        else:
            result = _file_load(name)
        return result if result is not None else (default if default is not None else {})


def save(name, data):
    with _lock:
        if _DB_URL:
            return _db_save(name, data)
        else:
            return _file_save(name, data)


# ── Accounts / Sessions API ───────────────────────────────────────────────────

def save_session(session_id, count, domain):
    """Record the start of a creation session."""
    if _DB_URL:
        _init_db()
        try:
            conn = _get_conn()
            cur  = conn.cursor()
            cur.execute(
                "INSERT INTO sessions (session_id, count, domain) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                (session_id, count, domain)
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f'[storage] save_session error: {e}')
    else:
        try:
            with open('weynFBCreate.txt', 'a') as f:
                ts  = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                sep = f"\n{'='*60}\n SESSION {ts} | {count} account(s) | {domain}\n{'='*60}\n"
                f.write(sep)
        except Exception as e:
            print(f'[storage] save_session file error: {e}')


def save_account(session_id, uid, password, name='', email=''):
    """Persist a created account to DB or file."""
    if _DB_URL:
        _init_db()
        try:
            conn = _get_conn()
            cur  = conn.cursor()
            cur.execute(
                "INSERT INTO accounts (session_id, uid, password, name, email) VALUES (%s, %s, %s, %s, %s)",
                (session_id, uid, password, name, email)
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f'[storage] save_account error: {e}')
    else:
        try:
            with open('weynFBCreate.txt', 'a') as f:
                f.write(f"{uid}|{password}\n")
        except Exception as e:
            print(f'[storage] save_account file error: {e}')


def get_accounts_text():
    """Return all accounts formatted for download, grouped by session."""
    if _DB_URL:
        _init_db()
        try:
            conn = _get_conn()
            cur  = conn.cursor()
            cur.execute("""
                SELECT s.session_id, s.started_at, s.count, s.domain,
                       a.uid, a.password, a.name, a.email
                FROM   sessions s
                JOIN   accounts a ON a.session_id = s.session_id
                ORDER  BY s.started_at ASC, a.id ASC
            """)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            if not rows:
                return None

            lines         = []
            current_sid   = None
            for sid, started_at, count, domain, uid, password, name, email in rows:
                if sid != current_sid:
                    current_sid = sid
                    ts = started_at.strftime('%Y-%m-%d %H:%M:%S') if started_at else '—'
                    lines.append(f"\n{'='*60}")
                    lines.append(f" SESSION {ts} | {count} account(s) | {domain}")
                    lines.append('='*60)
                lines.append(f"{uid}|{password}")
            return '\n'.join(lines)
        except Exception as e:
            print(f'[storage] get_accounts_text error: {e}')
            return None
    else:
        try:
            with open('weynFBCreate.txt') as f:
                return f.read()
        except Exception:
            return None


def get_accounts_list():
    """Return all accounts as a list of 'uid|password' strings (no session headers)."""
    if _DB_URL:
        _init_db()
        try:
            conn = _get_conn()
            cur  = conn.cursor()
            cur.execute("SELECT uid, password, name, email FROM accounts ORDER BY id ASC")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return [f"{uid}|{password}" for uid, password, name, email in rows]
        except Exception as e:
            print(f'[storage] get_accounts_list error: {e}')
            return []
    else:
        try:
            with open('weynFBCreate.txt') as f:
                return [
                    l.strip() for l in f
                    if l.strip() and not l.startswith('=') and not l.startswith(' SESSION')
                ]
        except Exception:
            return []


def count_accounts():
    """Return total number of created accounts."""
    if _DB_URL:
        _init_db()
        try:
            conn = _get_conn()
            cur  = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM accounts")
            row = cur.fetchone()
            cur.close()
            conn.close()
            return row[0] if row else 0
        except Exception as e:
            print(f'[storage] count_accounts error: {e}')
            return 0
    else:
        try:
            with open('weynFBCreate.txt') as f:
                return sum(
                    1 for l in f
                    if l.strip() and not l.startswith('=') and not l.startswith(' SESSION')
                )
        except Exception:
            return 0
