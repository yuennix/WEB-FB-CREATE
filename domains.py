import json
import threading

DOMAINS_FILE = 'domains.json'
_lock = threading.Lock()

_DEFAULT = {
    "domain_password": "yuennix",
    "temp": ["1secmail.com"],
    "custom": [
        {"domain": "weyn.store",    "imap_host": "mail.weyn.store",    "imap_user": "admin@weyn.store",    "imap_pass": "yuennix"},
        {"domain": "jhames.shop",   "imap_host": "mail.jhames.shop",   "imap_user": "admin@jhames.shop",   "imap_pass": "yuennix"},
        {"domain": "jakulan.site",  "imap_host": "mail.jakulan.site",  "imap_user": "admin@jakulan.site",  "imap_pass": "yuennix"},
    ]
}


def _load():
    try:
        with open(DOMAINS_FILE) as f:
            return json.load(f)
    except Exception:
        return json.loads(json.dumps(_DEFAULT))


def _save(data):
    with open(DOMAINS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


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


def add_custom_domain(domain, imap_pass, imap_host=None, imap_user=None):
    domain = domain.strip().lower()
    if not imap_host:
        imap_host = f"mail.{domain}"
    if not imap_user:
        imap_user = f"admin@{domain}"
    with _lock:
        data = _load()
        existing = [e['domain'] for e in data.get('custom', [])]
        if domain in existing:
            return False
        data.setdefault('custom', []).append({
            "domain":    domain,
            "imap_host": imap_host,
            "imap_user": imap_user,
            "imap_pass": imap_pass,
        })
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
