import os
import json
import time
import uuid
import threading
import requests

TG_TOKEN  = os.environ.get('TG_BOT_TOKEN', '')
TG_CHAT   = os.environ.get('TG_CHAT_ID', '')
KEYS_FILE = 'keys.json'
ACCS_FILE = 'weynFBCreate.txt'
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


def _count_accounts():
    """Count total accounts created (lines in weynFBCreate.txt)."""
    try:
        with open(ACCS_FILE) as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0


# ── ID / key generation ───────────────────────────────────────────────────────

def _gen_user_id(data):
    for _ in range(100):
        uid = 'USR-' + uuid.uuid4().hex[:4].upper()
        if not any(v.get('user_id') == uid for v in data.values()):
            return uid
    return 'USR-' + uuid.uuid4().hex[:8].upper()


def _gen_key(data):
    for _ in range(100):
        raw = uuid.uuid4().hex[:16].upper()
        key = f"WEYN-{raw[:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12:]}"
        if key not in data:
            return key
    return f"WEYN-{uuid.uuid4().hex[:16].upper()}"


# ── Public API ────────────────────────────────────────────────────────────────

def generate_key(name, reason=''):
    """Generate a pending key WITHOUT notifying admin yet."""
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
            'notified':    False,
        }
        _save(data)
    return key, user_id


def notify_admin(key):
    """Send Telegram notification with inline approve/decline buttons."""
    with _lock:
        data = _load()
        if key not in data:
            return False
        entry = data[key]
        data[key]['notified'] = True
        _save(data)
    _notify_admin_request(entry['user_id'], key, entry['name'], entry.get('reason', ''))
    return True


def request_access(name, reason=''):
    key, user_id = generate_key(name, reason)
    notify_admin(key)
    return key, user_id


def check_key(key):
    with _lock:
        data = _load()
        if key not in data:
            return 'invalid', None
        entry = data[key]
        return entry['status'], entry


def touch_key(key):
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


# ── Telegram helpers ──────────────────────────────────────────────────────────

def _tg_post(method, payload):
    if not TG_TOKEN:
        return None
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/{method}",
            json=payload,
            timeout=8,
        )
        return r.json()
    except Exception:
        return None


def _tg_send(chat_id, text):
    _tg_post('sendMessage', {
        'chat_id':    chat_id,
        'text':       text,
        'parse_mode': 'Markdown',
    })


def _tg_send_buttons(chat_id, text, buttons):
    """Send a message with inline keyboard buttons.
    buttons: list of list of {text, callback_data}
    """
    _tg_post('sendMessage', {
        'chat_id':      chat_id,
        'text':         text,
        'parse_mode':   'Markdown',
        'reply_markup': {'inline_keyboard': buttons},
    })


def _tg_answer_callback(callback_id, text=''):
    _tg_post('answerCallbackQuery', {
        'callback_query_id': callback_id,
        'text': text,
    })


def _tg_edit_message(chat_id, message_id, text):
    _tg_post('editMessageText', {
        'chat_id':    chat_id,
        'message_id': message_id,
        'text':       text,
        'parse_mode': 'Markdown',
    })


# ── Admin notification with inline buttons ────────────────────────────────────

def _notify_admin_request(user_id, key, name, reason):
    if not TG_TOKEN or not TG_CHAT:
        return
    text = (
        f"🔔 *New Access Request*\n\n"
        f"👤 Name:    `{name}`\n"
        f"🆔 User ID: `{user_id}`\n"
        f"📝 Reason:  `{reason or 'No reason given'}`\n"
        f"🗝 Key:     `{key}`"
    )
    buttons = [[
        {'text': '✅ Approve', 'callback_data': f'approve:{key}'},
        {'text': '❌ Decline', 'callback_data': f'decline:{key}'},
    ]]
    _tg_send_buttons(TG_CHAT, text, buttons)


# ── Callback query handler (button presses) ───────────────────────────────────

def _handle_callback(callback_id, chat_id, message_id, data_str):
    if chat_id != str(TG_CHAT):
        _tg_answer_callback(callback_id, '⛔ Unauthorized')
        return

    parts = data_str.split(':', 1)
    if len(parts) != 2:
        _tg_answer_callback(callback_id, 'Unknown action')
        return

    action, key = parts[0], parts[1].upper()

    if action == 'approve':
        ok, entry = approve_key(key)
        if ok:
            _tg_answer_callback(callback_id, '✅ Approved!')
            _tg_edit_message(chat_id, message_id,
                f"✅ *Approved*\n\n"
                f"👤 Name:    `{entry['name']}`\n"
                f"🆔 User ID: `{entry['user_id']}`\n"
                f"🗝 Key:     `{key}`"
            )
        else:
            _tg_answer_callback(callback_id, '⚠️ Key not found')

    elif action == 'decline':
        ok, entry = reject_key(key)
        if ok:
            _tg_answer_callback(callback_id, '❌ Declined')
            _tg_edit_message(chat_id, message_id,
                f"❌ *Declined*\n\n"
                f"👤 Name:    `{entry['name']}`\n"
                f"🆔 User ID: `{entry['user_id']}`\n"
                f"🗝 Key:     `{key}`"
            )
        else:
            _tg_answer_callback(callback_id, '⚠️ Key not found')

    elif action == 'revoke':
        ok, entry = revoke_by_id(key)  # key here is actually user_id
        if ok:
            _tg_answer_callback(callback_id, '🚫 Revoked')
            _tg_edit_message(chat_id, message_id,
                f"🚫 *Access Revoked*\n\n"
                f"👤 Name:    `{entry['name']}`\n"
                f"🆔 User ID: `{entry['user_id']}`"
            )
        else:
            _tg_answer_callback(callback_id, '⚠️ User not found')


# ── Command handler ───────────────────────────────────────────────────────────

def _handle_command(chat_id, text):
    parts = text.strip().split()
    cmd   = parts[0].lower()

    # /start
    if cmd == '/start':
        _tg_send(chat_id, (
            "👋 *Welcome to KYBX Bot*\n\n"
            "Send /help to see all commands."
        ))

    # /help
    elif cmd == '/help':
        _tg_send(chat_id, (
            "📋 *KYBX Bot Commands*\n\n"
            "`/stats`              — total users & accounts created\n"
            "`/users`              — list all users with remove buttons\n"
            "`/adduser <name>`     — add an approved user directly\n"
            "`/approve <KEY>`      — approve a pending key\n"
            "`/decline <KEY>`      — decline a pending key\n"
            "`/revoke <USR-ID>`    — revoke access\n"
            "`/remove <USR-ID>`    — permanently remove user\n"
            "`/help`               — show this message"
        ))

    # /stats
    elif cmd == '/stats':
        counts, data   = get_stats()
        total_accounts = _count_accounts()
        recent = [(k, v) for k, v in data.items() if v.get('last_seen')]
        recent.sort(key=lambda x: x[1]['last_seen'], reverse=True)

        lines = [
            "📊 *KYBX Statistics*\n",
            f"👥 Total Users:       *{counts['total']}*",
            f"✅ Approved:          *{counts['approved']}*",
            f"⏳ Pending:           *{counts['pending']}*",
            f"❌ Rejected/Revoked:  *{counts['rejected'] + counts['revoked']}*",
            f"\n🤖 Total Accounts Created: *{total_accounts}*",
        ]
        if recent:
            lines.append("\n🕐 *Recent Logins*")
            for k, v in recent[:5]:
                ago = int((time.time() - v['last_seen']) / 60)
                lines.append(f"  • `{v['user_id']}` {v['name']} — {ago}m ago")
        _tg_send(chat_id, "\n".join(lines))

    # /users
    elif cmd == '/users':
        data = list_users()
        if not data:
            _tg_send(chat_id, "No users yet.")
            return
        emoji_map = {'approved': '✅', 'pending': '⏳', 'rejected': '❌', 'revoked': '🚫'}
        approved = [(k, v) for k, v in data.items() if v.get('status') == 'approved']
        pending  = [(k, v) for k, v in data.items() if v.get('status') == 'pending']
        others   = [(k, v) for k, v in data.items() if v.get('status') not in ('approved', 'pending')]

        lines = [f"👥 *All Users* ({len(data)} total)\n"]
        for section, items in [('✅ Approved', approved), ('⏳ Pending', pending), ('Others', others)]:
            if items:
                lines.append(f"\n*{section}*")
                for k, v in sorted(items, key=lambda x: x[1].get('created_at', 0), reverse=True):
                    e = emoji_map.get(v['status'], '❓')
                    lines.append(f"{e} `{v['user_id']}` — *{v['name']}*")
                    if v.get('status') == 'approved':
                        lines.append(f"   ↳ `/revoke {v['user_id']}`  or  `/remove {v['user_id']}`")

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
            f"_Send this key to the user._"
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

    # /decline <key>
    elif cmd == '/decline':
        if len(parts) < 2:
            _tg_send(chat_id, "Usage: `/decline <KEY>`")
            return
        key = parts[1].upper()
        ok, entry = reject_key(key)
        if ok:
            _tg_send(chat_id, f"❌ Declined key for `{entry['name']}` (`{entry['user_id']}`)")
        else:
            _tg_send(chat_id, f"⚠️ Key not found: `{key}`")

    # /reject (alias for /decline)
    elif cmd == '/reject':
        if len(parts) < 2:
            _tg_send(chat_id, "Usage: `/decline <KEY>`")
            return
        key = parts[1].upper()
        ok, entry = reject_key(key)
        if ok:
            _tg_send(chat_id, f"❌ Declined key for `{entry['name']}` (`{entry['user_id']}`)")
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
            _tg_send(chat_id, f"🚫 Revoked access for *{entry['name']}* (`{uid}`)")
        else:
            _tg_send(chat_id, f"⚠️ User ID not found: `{uid}`")

    # /remove <user_id>
    elif cmd == '/remove' or cmd == '/removeuser':
        if len(parts) < 2:
            _tg_send(chat_id, "Usage: `/remove <USR-XXXX>`")
            return
        uid = parts[1].upper()
        ok, entry = remove_by_id(uid)
        if ok:
            _tg_send(chat_id, f"🗑 Removed *{entry['name']}* (`{uid}`) permanently.")
        else:
            _tg_send(chat_id, f"⚠️ User ID not found: `{uid}`")

    else:
        _tg_send(chat_id, "Unknown command. Send /help for a list of commands.")


# ── Telegram bot polling ──────────────────────────────────────────────────────

_last_update_id = 0


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

                # ── Handle inline button presses ──
                if 'callback_query' in upd:
                    cb      = upd['callback_query']
                    cb_id   = cb['id']
                    cb_data = cb.get('data', '')
                    cb_chat = str(cb['message']['chat']['id'])
                    cb_msg  = cb['message']['message_id']
                    threading.Thread(
                        target=_handle_callback,
                        args=(cb_id, cb_chat, cb_msg, cb_data),
                        daemon=True,
                    ).start()
                    continue

                # ── Handle text commands ──
                msg     = upd.get('message', {})
                chat_id = str(msg.get('chat', {}).get('id', ''))
                text    = msg.get('text', '').strip()
                if not text or not chat_id:
                    continue
                if chat_id != str(TG_CHAT):
                    _tg_send(chat_id, "⛔ Unauthorized.")
                    continue
                threading.Thread(
                    target=_handle_command,
                    args=(chat_id, text),
                    daemon=True,
                ).start()

        except Exception:
            time.sleep(5)


def start_bot():
    t = threading.Thread(target=_poll_telegram, daemon=True)
    t.start()
