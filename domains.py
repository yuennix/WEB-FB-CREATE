import json
import threading
import time
import storage

_lock = threading.Lock()

WEYN_EMAILS_API = 'https://weyn-emails-production.up.railway.app'

_weyn_cache      = {'domains': set(), 'ts': 0.0}
_weyn_cache_lock = threading.Lock()
_WEYN_CACHE_TTL  = 120   # seconds


def get_weyn_email_domains():
    """Return the set of domains served by the Railway weyn-emails API.
    Result is cached for 2 minutes to avoid hammering the API on every account creation."""
    import requests as _req
    with _weyn_cache_lock:
        if time.time() - _weyn_cache['ts'] < _WEYN_CACHE_TTL and _weyn_cache['domains']:
            return set(_weyn_cache['domains'])
    try:
        r = _req.get(f'{WEYN_EMAILS_API}/api/subdomains', timeout=8)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                names = {e['name'].lower() for e in data if e.get('name')}
                with _weyn_cache_lock:
                    _weyn_cache['domains'] = names
                    _weyn_cache['ts']      = time.time()
                return set(names)
    except Exception:
        pass
    with _weyn_cache_lock:
        return set(_weyn_cache['domains'])


def sync_weyn_email_domains():
    """Fetch all domains from the Railway API and add any new ones to the temp list.
    Safe to call from a background thread."""
    import requests as _req
    try:
        r = _req.get(f'{WEYN_EMAILS_API}/api/subdomains', timeout=8)
        if r.status_code != 200:
            return
        data = r.json()
        if not isinstance(data, list):
            return
        added = []
        for entry in data:
            name = (entry.get('name') or '').strip().lower()
            if not name:
                continue
            ok = add_temp_domain(name)
            if ok:
                added.append(name)
        # Refresh in-memory cache immediately
        with _weyn_cache_lock:
            names = {e['name'].lower() for e in data if e.get('name')}
            _weyn_cache['domains'] = names
            _weyn_cache['ts']      = time.time()
        if added:
            print(f'[domains] synced from weyn-emails API — added: {added}')
    except Exception as e:
        print(f'[domains] sync_weyn_email_domains error: {e}')


_DEFAULT = {
    "domain_password": "yuennix",
    "temp": [
        "1secmail.com", "harakirimail.com",
        "cunt.abrdns.com", "jinbilowg.cloud-ip.cc", "yuennix.work.gd",
        "yuennix.cc.cd",
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
