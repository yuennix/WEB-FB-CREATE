import os
import json
import time
import uuid
import threading
import requests

TG_TOKEN  = os.environ.get('TG_BOT_TOKEN', '')
TG_CHAT   = os.environ.get('TG_CHAT_ID', '')
KEYS_FILE = 'keys.json'
_lock     = threading.Lock()


# ── Storage helpers ───────────────────────────────────────────────────────────

def _load():
    try:
        with open(KEYS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data):
    with open(KEYS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


# ── ID / key generation ───────────────────────────────────────────────────────

def _gen_user_id(data):
    """Generate a short unique user ID like USR-4F2A."""
    for _ in range(100):
        uid = 'USR-' + uuid.uuid4().hex[:4].upper()
        if not any(v.get('user_id') == uid for v in data.values()):
            return uid
    return 'USR-' + uuid.uuid4().hex[:8].upper()


def _gen_key(data):
    """Generate a unique access key like WEYN-XXXX-XXXX-XXXX-XXXX."""
    for _ in range(100):
        raw = uuid.uuid4().hex[:16].upper()
        key = f"WEYN-{raw[:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12:]}"
        if key not in data:
            return key
    return f"WEYN-{uuid.uuid4().hex[:16].upper()}"


# ── Public API ────────────────────────────────────────────────────────────────

def request_access(name, reason=''):
    """User requests access — creates a pending entry and pings admin."""
    with _lock:
        data    = _load()
        user_id = _gen_user_id(data)
        key     = _gen_key(data)
        data[key] = {
            'user_id':     user_id,
            'key':         key,
            'name':        name,
            'reason':      reason or 'No reason given',
            'status':      'pending',
            'created_at':  time.time(),
            'approved_at': None,
            'last_seen':   None,
        }
        _save(data)

    _notify_admin_request(user_id, key, name, reason)
    return key, user_id


def check_key(key):
    """Returns (status, entry) — status: approved|pending|rejected|revoked|invalid"""
    with _lock:
        data = _load()
        if key not in data:
            return 'invalid', None
        entry = data[key]
        return entry['status'], entry


def touch_key(key):
    """Update last_seen timestamp."""
    with _lock:
        data = _load()
        if key in data:
            data[key]['last_seen'] = time.time()
            _save(data)


def approve_key(key):
    with _lock:
        data = _load()
        if key not in data:
            return False, 'Key not found'
        data[key]['status']      = 'approved'
        data[key]['approved_at'] = time.time()
        _save(data)
    return True, data[key]


def reject_key(key):
    with _lock:
        data = _load()
        if key not in data:
            return False, 'Key not found'
        data[key]['status'] = 'rejected'
        _save(data)
    return True, data[key]


def revoke_by_id(user_id):
    with _lock:
        data = _load()
        for k, v in data.items():
            if v.get('user_id') == user_id:
                data[k]['status'] = 'revoked'
                _save(data)
                return True, v
    return False, None


def remove_by_id(user_id):
    with _lock:
        data = _load()
        for k, v in list(data.items()):
            if v.get('user_id') == user_id:
                del data[k]
                _save(data)
                return True, v
    return False, None


def add_user(name):
    """Admin adds a user directly — creates an approved key and returns it."""
    with _lock:
        data    = _load()
        user_id = _gen_user_id(data)
        key     = _gen_key(data)
        data[key] = {
            'user_id':     user_id,
            'key':         key,
            'name':        name,
            'reason':      'Added by admin',
            'status':      'approved',
            'created_at':  time.time(),
            'approved_at': time.time(),
            'last_seen':   None,
        }
        _save(data)
    return key, user_id


def get_stats():
    with _lock:
        data = _load()
    counts = {'approved': 0, 'pending': 0, 'rejected': 0, 'revoked': 0, 'total': len(data)}
    for v in data.values():
        s = v.get('status', 'unknown')
        if s in counts:
            counts[s] += 1
    return counts, data


def list_users():
    with _lock:
        return _load()


def find_key_by_user_id(user_id):
    with _lock:
        data = _load()
        for k, v in data.items():
            if v.get('user_id') == user_id:
                return k, v
    return None, None


# ── Telegram notifications ────────────────────────────────────────────────────

def _notify_admin_request(user_id, key, name, reason):
    if not TG_TOKEN or not TG_CHAT:
        return
    text = (
        f"🔔 *New Access Request*\n\n"
        f"👤 Name:    `{name}`\n"
        f"🆔 User ID: `{user_id}`\n"
        f"📝 Reason:  `{reason or 'No reason given'}`\n"
        f"🗝 Key:     `{key}`\n\n"
        f"✅ Approve: `/approve {key}`\n"
        f"❌ Reject:  `/reject {key}`"
    )
    _tg_send(TG_CHAT, text)


def _tg_send(chat_id, text):
    if not TG_TOKEN:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'},
            timeout=8,
        )
    except Exception:
        pass


# ── Telegram bot polling ──────────────────────────────────────────────────────

_last_update_id = 0


def _handle_command(chat_id, text):
    global _last_update_id

    parts = text.strip().split()
    cmd   = parts[0].lower()

    # /help
    if cmd == '/help':
        _tg_send(chat_id, (
            "📋 *WEYN Bot Commands*\n\n"
            "`/stats`              — user statistics\n"
            "`/list`               — list all users\n"
            "`/adduser <name>`     — add approved user\n"
            "`/removeuser <ID>`    — permanently delete user\n"
            "`/approve <KEY>`      — approve pending request\n"
            "`/reject <KEY>`       — reject pending request\n"
            "`/revoke <ID>`        — revoke access by user ID\n"
            "`/help`               — show this message"
        ))

    # /stats
    elif cmd == '/stats':
        counts, data = get_stats()
        lines = [
            "📊 *User Statistics*\n",
            f"👥 Total:    *{counts['total']}*",
            f"✅ Approved: *{counts['approved']}*",
            f"⏳ Pending:  *{counts['pending']}*",
            f"❌ Rejected: *{counts['rejected']}*",
            f"🚫 Revoked:  *{counts['revoked']}*",
        ]
        # recent logins
        recent = [(k, v) for k, v in data.items() if v.get('last_seen')]
        recent.sort(key=lambda x: x[1]['last_seen'], reverse=True)
        if recent:
            lines.append("\n🕐 *Recent Activity*")
            for k, v in recent[:5]:
                ago = int((time.time() - v['last_seen']) / 60)
                lines.append(f"  • `{v['user_id']}` {v['name']} — {ago}m ago")
        _tg_send(chat_id, "\n".join(lines))

    # /list
    elif cmd == '/list':
        data = list_users()
        if not data:
            _tg_send(chat_id, "No users yet.")
            return
        emoji_map = {'approved': '✅', 'pending': '⏳', 'rejected': '❌', 'revoked': '🚫'}
        lines = ["👥 *All Users*\n"]
        for k, v in sorted(data.items(), key=lambda x: x[1].get('created_at', 0), reverse=True):
            e = emoji_map.get(v['status'], '❓')
            lines.append(f"{e} `{v['user_id']}` — *{v['name']}*  _{v['status']}_")
        _tg_send(chat_id, "\n".join(lines))

    # /adduser <name>
    elif cmd == '/adduser':
        if len(parts) < 2:
            _tg_send(chat_id, "Usage: `/adduser <name>`")
            return
        name = ' '.join(parts[1:])
        key, user_id = add_user(name)
        _tg_send(chat_id, (
            f"✅ *User Added*\n\n"
            f"👤 Name:    `{name}`\n"
            f"🆔 User ID: `{user_id}`\n"
            f"🗝 Key:     `{key}`\n\n"
            f"_Send this key to the user so they can log in._"
        ))

    # /approve <key>
    elif cmd == '/approve':
        if len(parts) < 2:
            _tg_send(chat_id, "Usage: `/approve <KEY>`")
            return
        key = parts[1].upper()
        ok, entry = approve_key(key)
        if ok:
            _tg_send(chat_id, (
                f"✅ *Approved*\n\n"
                f"👤 Name:    `{entry['name']}`\n"
                f"🆔 User ID: `{entry['user_id']}`\n"
                f"🗝 Key:     `{key}`"
            ))
        else:
            _tg_send(chat_id, f"⚠️ Key not found: `{key}`")

    # /reject <key>
    elif cmd == '/reject':
        if len(parts) < 2:
            _tg_send(chat_id, "Usage: `/reject <KEY>`")
            return
        key = parts[1].upper()
        ok, entry = reject_key(key)
        if ok:
            _tg_send(chat_id, f"❌ Rejected key for `{entry['name']}` (`{entry['user_id']}`)")
        else:
            _tg_send(chat_id, f"⚠️ Key not found: `{key}`")

    # /revoke <user_id>
    elif cmd == '/revoke':
        if len(parts) < 2:
            _tg_send(chat_id, "Usage: `/revoke <USR-XXXX>`")
            return
        uid = parts[1].upper()
        ok, entry = revoke_by_id(uid)
        if ok:
            _tg_send(chat_id, f"🚫 Revoked access for `{entry['name']}` (`{uid}`)")
        else:
            _tg_send(chat_id, f"⚠️ User ID not found: `{uid}`")

    # /removeuser <user_id>
    elif cmd == '/removeuser':
        if len(parts) < 2:
            _tg_send(chat_id, "Usage: `/removeuser <USR-XXXX>`")
            return
        uid = parts[1].upper()
        ok, entry = remove_by_id(uid)
        if ok:
            _tg_send(chat_id, f"🗑 Removed user `{entry['name']}` (`{uid}`) permanently.")
        else:
            _tg_send(chat_id, f"⚠️ User ID not found: `{uid}`")

    else:
        _tg_send(chat_id, "Unknown command. Send /help for a list of commands.")


def _poll_telegram():
    global _last_update_id
    if not TG_TOKEN:
        return
    while True:
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates",
                params={'offset': _last_update_id + 1, 'timeout': 30},
                timeout=40,
            )
            updates = r.json().get('result', [])
            for upd in updates:
                _last_update_id = upd['update_id']
                msg     = upd.get('message', {})
                chat_id = str(msg.get('chat', {}).get('id', ''))
                text    = msg.get('text', '').strip()
                if not text or not chat_id:
                    continue
                if chat_id != str(TG_CHAT):
                    _tg_send(chat_id, "⛔ Unauthorized.")
                    continue
                _handle_command(chat_id, text)
        except Exception:
            time.sleep(5)


def start_bot():
    t = threading.Thread(target=_poll_telegram, daemon=True)
    t.start()
