import os
import json
import time
import uuid
import threading
import requests
import domains as dm
import storage

TG_TOKEN  = os.environ.get('TG_BOT_TOKEN', '')
TG_CHAT   = os.environ.get('TG_CHAT_ID', '')
ACCS_FILE = 'weynFBCreate.txt'
_lock     = threading.Lock()


# ── Storage helpers ───────────────────────────────────────────────────────────

def _load():
    return storage.load('keys', default={})


def _save(data):
    storage.save('keys', data)


def _count_accounts():
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


def check_key(key, ip=None):
    with _lock:
        data = _load()
        if key not in data:
            return 'invalid', None
        entry = data[key]
        if entry.get('consumed') and entry.get('status') == 'approved':
            # Check expiry even for consumed keys (ongoing session access)
            expires_at = entry.get('expires_at')
            if expires_at and time.time() > expires_at:
                return 'expired', entry
            return 'consumed', entry
        if entry.get('status') == 'approved':
            expires_at = entry.get('expires_at')
            if expires_at and time.time() > expires_at:
                return 'expired', entry
            if ip:
                locked_ip = entry.get('locked_ip')
                if locked_ip and locked_ip != ip:
                    return 'ip_mismatch', entry
        return entry['status'], entry


def verify_and_consume(key, ip):
    """Atomically verify a key and consume it in one lock acquisition.

    Returns (status, entry) where status is one of:
      'approved'     — key was approved and is now consumed (first and only login)
      'already_used' — key was already consumed by a prior login
      'expired'      — key access duration has passed
      'ip_mismatch'  — key is locked to a different IP
      'invalid'      — key not found
      <other>        — key status (e.g. 'pending', 'rejected')
    """
    with _lock:
        data = _load()
        if key not in data:
            return 'invalid', None
        entry = data[key]

        # Already consumed — deny immediately
        if entry.get('consumed') and entry.get('status') == 'approved':
            return 'already_used', entry

        if entry.get('status') != 'approved':
            return entry['status'], entry

        # Expiry check
        expires_at = entry.get('expires_at')
        if expires_at and time.time() > expires_at:
            return 'expired', entry

        # IP lock check
        locked_ip = entry.get('locked_ip')
        if locked_ip and locked_ip != ip:
            return 'ip_mismatch', entry

        # All good — consume atomically in the same lock
        if not locked_ip:
            entry['locked_ip'] = ip
        entry['consumed']   = True
        entry['last_seen']  = time.time()
        data[key] = entry
        _save(data)

        return 'approved', entry


def mark_consumed(key):
    """Mark a key as consumed — no further logins allowed with it."""
    with _lock:
        data = _load()
        if key in data:
            data[key]['consumed'] = True
            _save(data)


def lock_key_to_ip(key, ip):
    """Lock a key to the given IP on first successful login."""
    with _lock:
        data = _load()
        if key in data and not data[key].get('locked_ip'):
            data[key]['locked_ip'] = ip
            _save(data)


def unlock_key_ip(key):
    """Remove the IP lock from a key (admin reset)."""
    with _lock:
        data = _load()
        if key in data and data[key].get('locked_ip'):
            data[key]['locked_ip'] = None
            _save(data)
            return True
    return False


def touch_key(key):
    with _lock:
        data = _load()
        if key in data:
            data[key]['last_seen'] = time.time()
            _save(data)


def approve_key(key, duration_secs=None):
    with _lock:
        data = _load()
        if key not in data:
            return False, 'Key not found'
        data[key]['status']      = 'approved'
        data[key]['approved_at'] = time.time()
        data[key]['expires_at']  = (time.time() + duration_secs) if duration_secs else None
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


def add_user(name, duration_secs=None):
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
            'expires_at':  (time.time() + duration_secs) if duration_secs else None,
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


def _tg_edit_message(chat_id, message_id, text, buttons=None):
    payload = {
        'chat_id':    chat_id,
        'message_id': message_id,
        'text':       text,
        'parse_mode': 'Markdown',
    }
    if buttons is not None:
        payload['reply_markup'] = {'inline_keyboard': buttons}
    _tg_post('editMessageText', payload)


def _tg_edit_remove_buttons(chat_id, message_id, text):
    _tg_post('editMessageText', {
        'chat_id':      chat_id,
        'message_id':   message_id,
        'text':         text,
        'parse_mode':   'Markdown',
        'reply_markup': {'inline_keyboard': []},
    })


# ── Register bot menu commands ────────────────────────────────────────────────

def _register_commands():
    _tg_post('setMyCommands', {
        'commands': [
            {'command': 'start',       'description': '👋 Welcome message'},
            {'command': 'stats',       'description': '📊 Total users & accounts created'},
            {'command': 'users',       'description': '👥 View all users with revoke buttons'},
            {'command': 'remove',      'description': '🗑 Remove user — /remove USR-XXXX'},
            {'command': 'domains',     'description': '🌐 List & manage email domains'},
            {'command': 'adddomain',   'description': '➕ Add temp domain — /adddomain domain.com'},
            {'command': 'addcustom',   'description': '➕ Add custom domain — /addcustom domain.com pass'},
            {'command': 'setdmpass',   'description': '🔑 Set domain password — /setdmpass newpass'},
        ]
    })
    for payload in [
        {'chat_id': TG_CHAT, 'menu_button': {'type': 'commands'}},
        {'menu_button': {'type': 'commands'}},
    ]:
        _tg_post('setChatMenuButton', payload)


# ── Admin notification with Approve / Decline buttons ────────────────────────

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


# ── Callback query handler (inline button presses) ────────────────────────────

def _handle_callback(callback_id, chat_id, message_id, data_str):
    if chat_id != str(TG_CHAT):
        _tg_answer_callback(callback_id, '⛔ Unauthorized')
        return

    parts = data_str.split(':', 1)
    if len(parts) != 2:
        _tg_answer_callback(callback_id, 'Unknown action')
        return

    action, value = parts[0], parts[1]

    if action == 'approve':
        key = value.upper()
        ok, entry = approve_key(key)
        if ok:
            _tg_answer_callback(callback_id, '✅ Approved!')
            _tg_edit_remove_buttons(chat_id, message_id,
                f"✅ *Approved*\n\n"
                f"👤 Name:    `{entry['name']}`\n"
                f"🆔 User ID: `{entry['user_id']}`\n"
                f"🗝 Key:     `{key}`"
            )
        else:
            _tg_answer_callback(callback_id, '⚠️ Key not found')

    elif action == 'decline':
        key = value.upper()
        ok, entry = reject_key(key)
        if ok:
            _tg_answer_callback(callback_id, '❌ Declined')
            _tg_edit_remove_buttons(chat_id, message_id,
                f"❌ *Declined*\n\n"
                f"👤 Name:    `{entry['name']}`\n"
                f"🆔 User ID: `{entry['user_id']}`\n"
                f"🗝 Key:     `{key}`"
            )
        else:
            _tg_answer_callback(callback_id, '⚠️ Key not found')

    elif action == 'revoke':
        uid = value.upper()
        ok, entry = revoke_by_id(uid)
        if ok:
            _tg_answer_callback(callback_id, '🚫 Access revoked')
            _tg_edit_remove_buttons(chat_id, message_id,
                f"🚫 *Access Revoked*\n\n"
                f"👤 Name:    `{entry['name']}`\n"
                f"🆔 User ID: `{entry['user_id']}`\n"
                f"_User can no longer log in._"
            )
        else:
            _tg_answer_callback(callback_id, '⚠️ User not found')

    elif action == 'domain_remove':
        domain = value.lower()
        ok = dm.remove_domain(domain)
        if ok:
            _tg_answer_callback(callback_id, f'🗑 Removed {domain}')
            _tg_edit_remove_buttons(chat_id, message_id,
                f"🗑 *Domain Removed*\n\n`{domain}` has been deleted.\nUsers will no longer see it in the web UI."
            )
        else:
            _tg_answer_callback(callback_id, f'⚠️ Domain not found')


# ── Command handler ───────────────────────────────────────────────────────────

def _handle_command(chat_id, text):
    parts = text.strip().split()
    cmd   = parts[0].lower().split('@')[0]   # strip @botname suffix

    # /start
    if cmd == '/start':
        _tg_send(chat_id, (
            "👋 *Welcome to WEYN Admin Bot*\n\n"
            "Use the *Menu* button to see all commands.\n\n"
            "📌 *Quick guide:*\n"
            "• New requests arrive with ✅ Approve / ❌ Decline buttons\n"
            "• `/stats` — see totals\n"
            "• `/users` — manage users with revoke buttons\n"
            "• `/remove USR\\-XXXX` — permanently delete a user\n"
            "• `/domains` — list & manage email domains\n"
            "• `/adddomain domain.com` — add a temp domain\n"
            "• `/addcustom domain.com pass` — add a custom domain\n"
            "• `/setdmpass newpass` — change domain password"
        ))

    # /stats
    elif cmd == '/stats':
        counts, data   = get_stats()
        total_accounts = _count_accounts()
        recent = [(k, v) for k, v in data.items() if v.get('last_seen')]
        recent.sort(key=lambda x: x[1]['last_seen'], reverse=True)

        lines = [
            "📊 *WEYN Statistics*\n",
            f"👥 Total Users:          *{counts['total']}*",
            f"✅ Approved:             *{counts['approved']}*",
            f"⏳ Pending:              *{counts['pending']}*",
            f"❌ Rejected / Revoked:   *{counts['rejected'] + counts['revoked']}*",
            f"\n🤖 *Total FB Accounts Created:  {total_accounts}*",
        ]
        if recent:
            lines.append("\n🕐 *Recent Logins*")
            for k, v in recent[:5]:
                ago = int((time.time() - v['last_seen']) / 60)
                lines.append(f"  • `{v['user_id']}` {v['name']} — {ago}m ago")
        _tg_send(chat_id, "\n".join(lines))

    # /users — send each user as its own message with action buttons
    elif cmd == '/users':
        data = list_users()
        if not data:
            _tg_send(chat_id, "👥 No users registered yet.")
            return

        counts, _ = get_stats()
        _tg_send(chat_id,
            f"👥 *User List*  —  {counts['total']} total\n"
            f"✅ {counts['approved']} approved  •  "
            f"⏳ {counts['pending']} pending  •  "
            f"🚫 {counts['revoked']} revoked"
        )

        emoji_map = {'approved': '✅', 'pending': '⏳', 'rejected': '❌', 'revoked': '🚫'}

        # Sort: approved first, then pending, then rest
        order = {'approved': 0, 'pending': 1, 'rejected': 2, 'revoked': 3}
        sorted_users = sorted(
            data.values(),
            key=lambda v: (order.get(v.get('status', ''), 9), -v.get('created_at', 0))
        )

        for v in sorted_users:
            status  = v.get('status', 'unknown')
            emoji   = emoji_map.get(status, '❓')
            uid     = v['user_id']
            name    = v['name']
            reason  = v.get('reason', '')

            last = ''
            if v.get('last_seen'):
                ago  = int((time.time() - v['last_seen']) / 60)
                last = f"\n🕐 Last seen: {ago}m ago"

            text = (
                f"{emoji} *{name}*\n"
                f"🆔 `{uid}`  •  _{status}_\n"
                f"📝 {reason}{last}"
            )

            if status == 'approved':
                buttons = [[{'text': '🚫 Revoke Access', 'callback_data': f'revoke:{uid}'}]]
                _tg_send_buttons(chat_id, text, buttons)
            elif status == 'pending':
                key = v.get('key', '')
                buttons = [[
                    {'text': '✅ Approve', 'callback_data': f'approve:{key}'},
                    {'text': '❌ Decline', 'callback_data': f'decline:{key}'},
                ]]
                _tg_send_buttons(chat_id, text, buttons)
            else:
                _tg_send(chat_id, text)

            time.sleep(0.05)   # slight delay to avoid Telegram flood limits

    # /remove <user_id>
    elif cmd == '/remove':
        if len(parts) < 2:
            _tg_send(chat_id, "Usage: `/remove USR-XXXX`")
            return
        uid = parts[1].upper()
        ok, entry = remove_by_id(uid)
        if ok:
            _tg_send(chat_id, f"🗑 Permanently removed *{entry['name']}* (`{uid}`).")
        else:
            _tg_send(chat_id, f"⚠️ User ID not found: `{uid}`")

    # /domains
    elif cmd == '/domains':
        info = dm.get_all_info()
        temp_list   = info.get('temp', [])
        custom_list = info.get('custom', [])
        pw          = info.get('domain_password', '—')

        lines = ["🌐 *Email Domains*\n", f"🔑 Password: `{pw}`\n"]

        if temp_list:
            lines.append("📦 *Temp (API)*")
            for d in temp_list:
                lines.append(f"  • `{d}`")
        else:
            lines.append("📦 *Temp:* _(none)_")

        lines.append("")
        if custom_list:
            lines.append("🔧 *Custom (IMAP)*")
            for e in custom_list:
                lines.append(f"  • `{e['domain']}`")
        else:
            lines.append("🔧 *Custom:* _(none)_")

        lines.append("\n_Tap ❌ below to remove a domain_")
        msg_text = "\n".join(lines)

        all_domains = [(d, 'temp') for d in temp_list] + [(e['domain'], 'custom') for e in custom_list]
        if all_domains:
            buttons = [[{'text': f'❌ {d}', 'callback_data': f'domain_remove:{d}'}] for d, _ in all_domains]
            _tg_send_buttons(chat_id, msg_text, buttons)
        else:
            _tg_send(chat_id, msg_text + "\n\n_(No domains configured yet)_")

    # /adddomain <domain>
    elif cmd == '/adddomain':
        if len(parts) < 2:
            _tg_send(chat_id, "Usage: `/adddomain domain.com`")
            return
        domain = parts[1].lower()
        ok = dm.add_temp_domain(domain)
        if ok:
            _tg_send(chat_id, f"✅ Temp domain added: `{domain}`\nUsers will see it in the web UI immediately.")
        else:
            _tg_send(chat_id, f"⚠️ `{domain}` is already in the list.")

    # /addcustom <domain> <password>
    elif cmd == '/addcustom':
        if len(parts) < 3:
            _tg_send(chat_id, "Usage: `/addcustom domain.com mailpassword`\n\nThis uses standard IMAP: `mail.domain.com` / `admin@domain.com`.\nContact me if you need custom IMAP settings.")
            return
        domain   = parts[1].lower()
        imap_pass = parts[2]
        ok = dm.add_custom_domain(domain, imap_pass)
        if ok:
            _tg_send(chat_id,
                f"✅ Custom domain added: `{domain}`\n"
                f"📬 IMAP: `mail.{domain}` → `admin@{domain}`\n"
                f"🔑 Pass: `{imap_pass}`\n\n"
                f"Users will see it immediately in the web UI."
            )
        else:
            _tg_send(chat_id, f"⚠️ `{domain}` is already in the custom domain list.")

    # /setdmpass <newpass>
    elif cmd == '/setdmpass':
        if len(parts) < 2:
            _tg_send(chat_id, "Usage: `/setdmpass newpassword`")
            return
        new_pw = parts[1]
        dm.set_domain_password(new_pw)
        _tg_send(chat_id, f"🔑 Domain password updated to: `{new_pw}`\n\nUsers must enter this password when selecting a custom domain.")

    else:
        _tg_send(chat_id, "Use the *Menu* button or send /start for help.")


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

                # Inline button presses
                if 'callback_query' in upd:
                    cb = upd['callback_query']
                    threading.Thread(
                        target=_handle_callback,
                        args=(
                            cb['id'],
                            str(cb['message']['chat']['id']),
                            cb['message']['message_id'],
                            cb.get('data', ''),
                        ),
                        daemon=True,
                    ).start()
                    continue

                # Text commands
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
    _register_commands()
    t = threading.Thread(target=_poll_telegram, daemon=True)
    t.start()
