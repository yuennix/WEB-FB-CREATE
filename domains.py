import json
import threading
import storage

_lock = threading.Lock()

_DEFAULT = {
    "domain_password": "yuennix",
    "temp": [
        "1secmail.com", "harakirimail.com",
        "cunt.abrdns.com", "jinbilowg.cloud-ip.cc", "yuennix.work.gd",
    ],
    "custom": [
        {"domain": "weyn.store",    "imap_host": "mail.weyn.store",    "imap_user": "admin@weyn.store",    "imap_pass": "yuennix"},
        {"domain": "jhames.shop",   "imap_host": "mail.jhames.shop",   "imap_user": "admin@jhames.shop",   "imap_pass": "yuennix"},
        {"domain": "jakulan.site",  "imap_host": "mail.jakulan.site",  "imap_user": "admin@jakulan.site",  "imap_pass": "yuennix"},
    ]
}

_BAD_PLACEHOLDERS = {"tempmail.io"}


def _load():
    data = storage.load('domains', default=None)
    if data is None:
        return json.loads(json.dumps(_DEFAULT))
    changed = False
    temp = data.get('temp', [])
    temp = [d for d in temp if d not in _BAD_PLACEHOLDERS]
    for dom in _DEFAULT['temp']:
        if dom not in temp:
            temp.append(dom)
            changed = True
    if len(temp) != len(data.get('temp', [])) or changed:
        data['temp'] = temp
        storage.save('domains', data)
    return data


def _save(data):
    storage.save('domains', data)


def get_domain_password():
    with _lock:
        return _load().get('domain_password', 'yuennix')


def set_domain_password(password):
    with _lock:
        data = _load()
        data['domain_password'] = password
        _save(data)


def get_custom_domains():
    with _lock:
        return [e['domain'] for e in _load().get('custom', [])]


def get_temp_domains():
    with _lock:
        return _load().get('temp', ['1secmail.com'])


def get_all_domains():
    return get_temp_domains() + get_custom_domains()


def get_imap_config(domain):
    with _lock:
        for entry in _load().get('custom', []):
            if entry['domain'] == domain:
                return entry
    return None


def add_temp_domain(domain):
    domain = domain.strip().lower()
    with _lock:
        data = _load()
        if domain not in data['temp']:
            data['temp'].append(domain)
            _save(data)
            return True
    return False


def add_custom_domain(domain, imap_pass='', imap_host=None, imap_user=None, domain_type='webhook'):
    domain = domain.strip().lower()
    with _lock:
        data = _load()
        existing = [e['domain'] for e in data.get('custom', [])]
        if domain in existing:
            return False
        entry = {"domain": domain, "type": "webhook"}
        data.setdefault('custom', []).append(entry)
        _save(data)
    return True


def remove_domain(domain):
    domain = domain.strip().lower()
    with _lock:
        data = _load()
        removed = False
        orig_temp = data.get('temp', [])
        data['temp'] = [d for d in orig_temp if d != domain]
        if len(data['temp']) < len(orig_temp):
            removed = True
        orig_custom = data.get('custom', [])
        data['custom'] = [e for e in orig_custom if e['domain'] != domain]
        if len(data['custom']) < len(orig_custom):
            removed = True
        if removed:
            _save(data)
    return removed


def get_all_info():
    with _lock:
        return _load()
