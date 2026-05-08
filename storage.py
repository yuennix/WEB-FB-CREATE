import os
import json
import threading

_lock = threading.Lock()
_DB_URL = os.environ.get('DATABASE_URL', '')

# ── PostgreSQL backend ────────────────────────────────────────────────────────

def _get_conn():
    import psycopg2
    url = _DB_URL
    # Railway sometimes gives postgres:// but psycopg2 needs postgresql://
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
        _db_ready = True


def _db_load(name):
    _init_db()
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


def _db_save(name, data):
    _init_db()
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


# ── File backend ──────────────────────────────────────────────────────────────

def _file_path(name):
    return f'{name}.json'


def _file_load(name):
    try:
        with open(_file_path(name)) as f:
            return json.load(f)
    except Exception:
        return None


def _file_save(name, data):
    try:
        with open(_file_path(name), 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f'[storage] File save error ({name}): {e}')
    return False


# ── Public API ────────────────────────────────────────────────────────────────

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
