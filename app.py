import os
import sys
import json
import time
import queue
import secrets as _secrets
import threading
import re as _re
import random as _random
import concurrent.futures as _cfi
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote as _uq

from flask import Flask, render_template, request, jsonify, Response, send_file, session

sys.path.insert(0, '.')
import main as m
import auth
import domains as dm

app = Flask(__name__)

# ── Stable secret key (persisted in DB so sessions survive restarts) ──────────
import datetime as _dt
import storage as _sto

def _get_stable_secret():
    rec = _sto.load('flask_secret', None)
    if rec and isinstance(rec, dict) and rec.get('key'):
        return rec['key']
    key = os.urandom(32).hex()
    _sto.save('flask_secret', {'key': key})
    return key

app.secret_key = _get_stable_secret()

# ── Start Telegram bot when running under gunicorn ────────────────────────────
auth.start_bot()

# ── Webhook secret ────────────────────────────────────────────────────────────

def _get_webhook_secret():
    rec = _sto.load('webhook_secret', None)
    if rec and isinstance(rec, dict) and rec.get('token'):
        return rec['token']
    token = _secrets.token_urlsafe(32)
    _sto.save('webhook_secret', {'token': token})
    return token

# ── Per-job state registry ────────────────────────────────────────────────────
_jobs      = {}          # job_id -> job state dict
_jobs_lock = threading.Lock()

def _new_job_state():
    return {
        'task_queue':   queue.Queue(),
        'result_store': [],
        'running':      True,
        'lock':         threading.Lock(),
        'done_count':   [0],
        'cp_count':     [0],
    }

# ── Session store for retry-confirm ──────────────────────────────────────────
_session_store = {}   # uid -> {'ses': requests.Session, 'email': str, 'password': str, 'job_id': str}
_session_lock  = threading.Lock()

WORKERS = 50   # 50 parallel workers

# ── Auth routes ───────────────────────────────────────────────────────────────

@app.route('/')
def index():
    key = request.cookies.get('access_key', '')
    if key:
        status, entry = auth.check_key(key)
        if status in ('approved', 'consumed'):
            auth.touch_key(key)
            return render_template('index.html', user_name=entry.get('name', ''))
        if status == 'expired':
            resp = render_template('login.html')
            from flask import make_response
            r = make_response(resp)
            r.delete_cookie('access_key')
            return r
    return render_template('login.html')


@app.route('/generate-key', methods=['POST'])
def generate_key():
    data   = request.json or {}
    name   = (data.get('name') or '').strip()
    reason = (data.get('reason') or '').strip()
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    key, user_id = auth.generate_key(name, reason)
    return jsonify({'key': key, 'user_id': user_id})


@app.route('/notify-admin', methods=['POST'])
def notify_admin():
    data = request.json or {}
    key  = (data.get('key') or '').strip().upper()
    if not key:
        return jsonify({'error': 'Key is required'}), 400
    ok = auth.notify_admin(key)
    if ok:
        return jsonify({'status': 'sent'})
    return jsonify({'error': 'Key not found'}), 404


@app.route('/request-access', methods=['POST'])
def request_access():
    data   = request.json or {}
    name   = (data.get('name') or '').strip()
    reason = (data.get('reason') or '').strip()
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    key, user_id = auth.request_access(name, reason)
    return jsonify({'key': key, 'user_id': user_id})


def _get_client_ip():
    xff = request.headers.get('X-Forwarded-For', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.remote_addr


@app.route('/verify-key', methods=['POST'])
def verify_key():
    data   = request.json or {}
    key    = (data.get('key') or '').strip().upper()
    ip     = _get_client_ip()
    # Atomic check + consume — prevents two simultaneous logins with the same key
    status, entry = auth.verify_and_consume(key, ip)
    if status == 'approved':
        resp = jsonify({
            'status': 'approved',
            'name':    entry['name'],
            'user_id': entry['user_id'],
        })
        resp.set_cookie('access_key', key, max_age=60*60*24*30, httponly=True, samesite='Lax', path='/')
        return resp
    if status == 'already_used':
        return jsonify({'status': 'already_used'})
    if status == 'expired':
        return jsonify({'status': 'expired'})
    if status == 'ip_mismatch':
        return jsonify({'status': 'ip_mismatch'})
    return jsonify({'status': status})


@app.route('/logout', methods=['POST'])
def logout():
    resp = jsonify({'status': 'ok'})
    resp.delete_cookie('access_key')
    return resp


@app.route('/key-status', methods=['POST'])
def key_status():
    data = request.json or {}
    key  = (data.get('key') or '').strip().upper()
    status, entry = auth.check_key(key)
    return jsonify({'status': status})


# ── Auth guard ────────────────────────────────────────────────────────────────

def _require_auth():
    if session.get('is_admin'):
        return True
    key = request.cookies.get('access_key', '')
    if not key:
        return False
    ip = _get_client_ip()
    status, _ = auth.check_key(key, ip=ip)
    if status == 'expired':
        return False
    return status in ('approved', 'consumed')


# ── Main routes ───────────────────────────────────────────────────────────────

@app.route('/start', methods=['POST'])
def start():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    import uuid as _uuid
    data            = request.json
    name_type       = data.get('name_type', '1')
    email_domain    = data.get('email_domain', '1secmail.com')
    domain_password = data.get('domain_password', '')
    count           = max(1, min(int(data.get('count', 1)), 200))
    password_type   = data.get('password_type', 'auto')
    custom_password = data.get('custom_password', '')
    gender          = data.get('gender', '3')

    if email_domain in dm.get_custom_domains():
        if domain_password != dm.get_domain_password():
            return jsonify({'error': 'Wrong domain password'}), 403

    job_id = _uuid.uuid4().hex
    job    = _new_job_state()
    with _jobs_lock:
        _jobs[job_id] = job

    threading.Thread(
        target=run_creation,
        args=(name_type, email_domain, count, password_type, custom_password, gender, job_id, job),
        daemon=True,
    ).start()

    return jsonify({'status': 'started', 'job_id': job_id})


# ── Worker ────────────────────────────────────────────────────────────────────

def _create_one(name_type, gender, password_type, custom_password, num, session_id, email_domain, job):
    jq   = job['task_queue']
    jlk  = job['lock']
    jdc  = job['done_count']
    jcp  = job['cp_count']
    jrs  = job['result_store']

    while True:
        with jlk:
            if jdc[0] >= num or not job['running']:
                return

        try:
            ses      = m.requests.Session()
            response = ses.get("https://m.facebook.com/reg/", timeout=15)
            form     = m.extractor(response.text)

            if not form.get("lsd") and not form.get("fb_dtsg"):
                jq.put({'type': 'log', 'level': 'warn',
                        'msg': 'Could not load reg page, retrying…'})
                continue

            if name_type == '2':
                firstname, lastname = m.get_rpw_name()
            else:
                base_first, base_last = m.get_bd_name()
                if gender == '1':
                    firstname = m.random.choice(m.first_names_male)
                elif gender == '2':
                    firstname = m.random.choice(m.first_names_female)
                else:
                    firstname = m.random.choice(m.first_names_male + m.first_names_female)
                lastname = base_last

            if gender == '1':
                fb_sex = "2"
            elif gender == '2':
                fb_sex = "1"
            else:
                fb_sex = m.random.choice(["1", "2"])

            m.EMAIL_DOMAIN = email_domain
            phone = m.get_email_for_registration(firstname, lastname)
            pww   = m.get_pass() if password_type == 'auto' else custom_password

            _pt = form.get('privacy_mutation_token', '')
            if _pt:
                _reg_url = (f"https://m.facebook.com/reg/submit/"
                            f"?privacy_mutation_token={_uq(_pt)}&multi_step_form=1&skip_suma=0")
            else:
                _reg_url = "https://m.facebook.com/reg/submit/?multi_step_form=1&skip_suma=0"

            payload = {
                'ccp': "2",
                'reg_instance':       form.get("reg_instance", ""),
                'submission_request': "true",
                'reg_impression_id':  form.get("reg_impression_id", ""),
                'ns':                 "1",
                'logger_id':          form.get("logger_id", ""),
                'firstname':          firstname,
                'lastname':           lastname,
                'birthday_day':       str(m.random.randint(1, 28)),
                'birthday_month':     str(m.random.randint(1, 12)),
                'birthday_year':      str(m.random.randint(1985, 2005)),
                'reg_email__':        phone,
                'reg_passwd__':       pww,
                'sex':                fb_sex,
                'encpass':            f'#PWD_BROWSER:0:{int(time.time())}:{pww}',
                'submit':             "Sign Up",
                'privacy_mutation_token': _pt,
                'fb_dtsg':   form.get("fb_dtsg", ""),
                'jazoest':   form.get("jazoest", ""),
                'lsd':       form.get("lsd", ""),
                '__dyn': '', '__csr': '', '__req': 'q', '__a': '', '__user': '0',
            }

            merged_headers = {
                'User-Agent':    m.FB_LITE_UA,
                'Accept':        ('text/html,application/xhtml+xml,application/xml;q=0.9,'
                                  'image/avif,image/webp,image/apng,*/*;q=0.8,'
                                  'application/signed-exchange;v=b3;q=0.7'),
                'Accept-Encoding':   'gzip, deflate, br',
                'Accept-Language':   'en-US,en;q=0.9',
                'Cache-Control':     'max-age=0',
                'Origin':            'https://m.facebook.com',
                'Referer':           'https://m.facebook.com/reg/',
                'sec-ch-prefers-color-scheme': 'light',
                'sec-ch-ua':         '"Android WebView";v="109", "Chromium";v="109", "Not_A Brand";v="24"',
                'sec-ch-ua-mobile':  '?1',
                'sec-ch-ua-platform':'"Android"',
                'sec-fetch-dest':    'document',
                'sec-fetch-mode':    'navigate',
                'sec-fetch-site':    'same-origin',
                'sec-fetch-user':    '?1',
                'upgrade-insecure-requests': '1',
                'x-requested-with':  'com.facebook.lite',
                'viewport-width':    '980',
            }

            ses.post(_reg_url, data=payload, headers=merged_headers, timeout=20)
            login_coki = ses.cookies.get_dict()

            if "c_user" in login_coki:
                uid = login_coki["c_user"]

                with jlk:
                    if jdc[0] >= num or not job['running']:
                        return
                    jdc[0] += 1
                    current = jdc[0]
                    if jdc[0] >= num:
                        job['running'] = False

                result = {
                    'num':      current,
                    'name':     f'{firstname} {lastname}',
                    'email':    phone,
                    'password': pww,
                    'uid':      uid,
                    'status':   'success',
                }
                jrs.append(result)

                _tmail_tok = ''
                _phone_dom = phone.split('@')[1].lower() if '@' in phone else ''
                if _phone_dom in m._TEMPMAIL_IO_DOMAIN_SET:
                    with m._TEMPMAIL_IO_TOKEN_LOCK:
                        _tmail_tok = m._TEMPMAIL_IO_TOKEN_STORE.get(phone, '')
                with _session_lock:
                    _session_store[uid] = {
                        'ses': ses, 'email': phone, 'password': pww,
                        'tmail_token': _tmail_tok,
                        'job_id': job.get('job_id', ''),
                    }

                _sto.save_account(session_id, uid, pww,
                                  name=f'{firstname} {lastname}', email=phone)

                jq.put({'type': 'account', 'data': result,
                        'created': current, 'target': num})
                jq.put({'type': 'log', 'level': 'success',
                        'msg': (f'[{current}/{num}] ✓ '
                                f'{firstname} {lastname} | {phone} | UID:{uid}')})

                _instant_urls = [
                    'https://m.facebook.com/confirmemail.php?send=1',
                    'https://m.facebook.com/confirmemail.php?soft=hjk&send=1',
                    'https://m.facebook.com/confirmemail.php?soft=hjk&resend=1',
                    'https://m.facebook.com/confirmemail.php?soft=1&send=1',
                    'https://www.facebook.com/confirmemail.php?send=1',
                ]
                _ih = {
                    'User-Agent':       m.FB_LITE_UA,
                    'Accept':           'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language':  'en-US,en;q=0.9',
                    'Accept-Encoding':  'gzip, deflate, br',
                    'Referer':          'https://m.facebook.com/confirmemail.php',
                    'x-requested-with': 'com.facebook.lite',
                }
                def _ifire(u):
                    try:
                        ses.get(u, headers=_ih, timeout=6, allow_redirects=True)
                    except Exception:
                        pass
                with _cfi.ThreadPoolExecutor(max_workers=len(_instant_urls)) as _ipool:
                    _ipool.map(_ifire, _instant_urls)

                threading.Thread(
                    target=m._full_email_confirm,
                    args=(ses, phone, uid, pww, jq),
                    daemon=False,
                ).start()

            elif "checkpoint" in login_coki:
                with jlk:
                    jcp[0] += 1
                jq.put({'type': 'log', 'level': 'warn',
                        'msg': f'⚠ Checkpoint — {firstname} {lastname} | {phone}'})

        except Exception as e:
            jq.put({'type': 'log', 'level': 'error', 'msg': str(e)})


# ── Orchestrator ──────────────────────────────────────────────────────────────

def run_creation(name_type, email_domain, count, password_type, custom_password, gender, job_id, job):
    import uuid
    session_id = str(uuid.uuid4())

    job['job_id'] = job_id
    jq = job['task_queue']

    _sto.save_session(session_id, count, email_domain)

    jq.put({'type': 'log', 'level': 'info',
            'msg': f'Starting {count} account(s) with {WORKERS} workers on {email_domain}…'})

    try:
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futures = [
                pool.submit(_create_one, name_type, gender, password_type, custom_password, count, session_id, email_domain, job)
                for _ in range(WORKERS)
            ]
            for f in as_completed(futures):
                try:
                    f.result()
                except Exception as e:
                    jq.put({'type': 'log', 'level': 'error', 'msg': str(e)})
    finally:
        job['running'] = False
        jq.put({
            'type':       'done',
            'total':      count,
            'created':    job['done_count'][0],
            'checkpoint': job['cp_count'][0],
            'msg':        (f'Done — {job["done_count"][0]}/{count} created'
                           + (f', {job["cp_count"][0]} checkpointed' if job['cp_count'][0] else '') + '.'),
        })
        with _jobs_lock:
            _jobs.pop(job_id, None)


# ── SSE stream ────────────────────────────────────────────────────────────────

@app.route('/stream')
def stream():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    job_id = request.args.get('job_id', '')
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Invalid job_id'}), 404

    jq = job['task_queue']

    def generate():
        yield 'retry: 3000\n\n'
        empty = 0
        while empty < 38:
            try:
                item = jq.get(timeout=8)
                empty = 0
                yield f'data: {json.dumps(item)}\n\n'
            except queue.Empty:
                empty += 1
                yield f'data: {json.dumps({"type": "ping"})}\n\n'

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


@app.route('/stop', methods=['POST'])
def stop():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    job_id = (request.json or {}).get('job_id', '')
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job:
        job['running'] = False
    return jsonify({'status': 'stopped'})


@app.route('/api/accounts/all')
def api_accounts_all():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'accounts': _sto.get_accounts_list()})


@app.route('/api/domains')
def api_domains():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    info = dm.get_all_info()
    return jsonify({
        'temp':   info.get('temp', []),
        'custom': [e['domain'] for e in info.get('custom', [])],
    })


@app.route('/download')
def download():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    text = _sto.get_accounts_text()
    if text:
        import io
        buf = io.BytesIO(text.encode('utf-8'))
        buf.seek(0)
        return send_file(buf, as_attachment=True, download_name='weynFBCreate.txt',
                         mimetype='text/plain')
    return jsonify({'error': 'No results yet'}), 404


@app.route('/retry-confirm', methods=['POST'])
def retry_confirm():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    uid  = (data.get('uid') or '').strip()
    if not uid:
        return jsonify({'error': 'uid required'}), 400
    with _session_lock:
        entry = _session_store.get(uid)
    if not entry:
        return jsonify({'error': 'Session expired — cannot retry'}), 404
    ses      = entry['ses']
    email    = entry['email']
    password = entry['password']
    job_id   = entry.get('job_id', '')
    with _jobs_lock:
        job = _jobs.get(job_id)
    jq = job['task_queue'] if job else queue.Queue()
    threading.Thread(
        target=m._full_email_confirm,
        args=(ses, email, uid, password, jq),
        daemon=False,
    ).start()
    return jsonify({'status': 'retrying'})


def _extract_code_from_body(body):
    """Extract FB confirmation code from an email body string. Returns code string or None."""
    from bs4 import BeautifulSoup as _BS
    plain = _BS(body, 'html.parser').get_text(separator=' ') if body else ''
    clean = _re.sub(r'https?://\S+', ' ', plain)
    pats  = [
        # "confirmation code is 847291" / "confirmation code: 847291"
        r'(?:confirmation|verification)\s*code[\s\w]*?[:\s\-]+(\d{5,6})',
        # "your confirmation code is 847291" / "your code is 847291"
        r'(?:your|the)\s+(?:\w+\s+)*?(?:confirmation\s+)?code[\s\w]*?[:\-]?\s*(\d{5,6})',
        # "code: 847291" or "code — 847291"
        r'code[:\s\-]+(\d{5,6})',
        # "847291 is your code" / "847291 to confirm"
        r'\b(\d{5,6})\s+(?:is\s+your|to\s+confirm)',
        # "enter code: 847291"
        r'enter\s+(?:the\s+)?(?:code|number)[:\s\-]+(\d{5,6})',
        # standalone 6-digit number (most permissive — number followed by non-digit or end)
        r'(?<!\d)(\d{6})(?!\d)',
        # standalone 5-digit number
        r'(?<!\d)(\d{5})(?!\d)',
    ]
    for pat in pats:
        match = _re.search(pat, clean, _re.IGNORECASE | _re.MULTILINE)
        if match:
            code = match.group(1)
            if not (1900 <= int(code) <= 2100):
                return code
    return None


@app.route('/fetch-code-now', methods=['POST'])
def fetch_code_now():
    """Poll any supported inbox and return the FB confirmation code.
    Supports: harakirimail.com, 1secmail.com, all tempmail.io domains,
    any custom IMAP domain, and webhook domains (checks stored payload)."""
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    data  = request.json or {}
    uid   = (data.get('uid')   or '').strip()
    email = (data.get('email') or '').strip()
    if not uid or not email:
        return jsonify({'error': 'uid and email required'}), 400

    domain = email.split('@')[1].lower() if '@' in email else ''
    login  = email.split('@')[0]

    with _session_lock:
        _fcn_ses_entry = _session_store.get(uid, {})
    _fcn_job_id = _fcn_ses_entry.get('job_id', '')
    with _jobs_lock:
        _fcn_job = _jobs.get(_fcn_job_id)
    _fcn_jq = _fcn_job['task_queue'] if _fcn_job else None

    base_hdrs = {
        'User-Agent':     ('Mozilla/5.0 (Linux; Android 11; Redmi Note 8) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/109.0.5414.118 Mobile Safari/537.36'),
        'Accept':         'application/json',
        'Accept-Language':'en-US,en;q=0.9',
    }

    deadline = time.time() + 30
    seen_ids = set()

    # ── harakirimail ──────────────────────────────────────────────────────────
    if 'harakirimail' in domain:
        hdrs = {**base_hdrs, 'Referer': f'https://harakirimail.com/inbox/{login}'}
        while time.time() < deadline:
            try:
                r = m.requests.get(
                    f'https://harakirimail.com/api/v1/inbox/{login}',
                    headers=hdrs, timeout=10
                )
                if r.status_code == 200:
                    for msg in (r.json().get('emails') or []):
                        mid    = str(msg.get('_id') or '')
                        if not mid or mid in seen_ids:
                            continue
                        from_t = str(msg.get('from', '')).lower()
                        subj_t = str(msg.get('subject', '')).lower()
                        is_fb  = ('facebook' in from_t or 'facebookmail' in from_t
                                   or 'confirm' in subj_t or 'code' in subj_t
                                   or 'verification' in subj_t)
                        seen_ids.add(mid)
                        if not is_fb:
                            continue
                        try:
                            er = m.requests.get(
                                f'https://harakirimail.com/api/v1/email/{mid}',
                                headers=hdrs, timeout=10
                            )
                            if er.status_code == 200:
                                try:
                                    ed   = er.json()
                                    body = str(ed.get('bodyhtml') or ed.get('bodytext') or
                                               ed.get('html') or ed.get('body') or
                                               ed.get('text') or '')
                                except Exception:
                                    body = er.text
                                code = _extract_code_from_body(body)
                                if code:
                                    if _fcn_jq: _fcn_jq.put({'type': 'confirm_code', 'uid': uid, 'code': code})
                                    return jsonify({'code': code})
                        except Exception:
                            pass
            except Exception:
                pass
            time.sleep(3)
        return jsonify({'status': 'not_found'})

    # ── temp-mail.io (with hyphen) — all 8 domains ───────────────────────────
    if domain in m._TEMPMAIL_IO_DOMAIN_SET:
        _TMAIL_API = m._TEMPMAIL_IO_API
        _tmail_hdrs = dict(m._TEMPMAIL_IO_HDRS)

        # 1) Look up token stored per-uid in session store (survives beyond creation thread)
        _token = ''
        with _session_lock:
            _sess_entry = _session_store.get(uid) or {}
        _token = _sess_entry.get('tmail_token', '')

        # 2) Fallback: look up by email in the global token store
        if not _token:
            with m._TEMPMAIL_IO_TOKEN_LOCK:
                _token = m._TEMPMAIL_IO_TOKEN_STORE.get(email, '')

        if not _token:
            return jsonify({'status': 'not_found', 'error': 'Token not found — account may have been created before this session'})

        _msg_url = f'{_TMAIL_API}/v3/email/{_token}/messages'

        while time.time() < deadline:
            try:
                r = m.requests.get(_msg_url, headers=_tmail_hdrs, timeout=10)
                msgs = []
                if r.status_code == 200:
                    d = r.json()
                    msgs = d if isinstance(d, list) else (
                        d.get('messages') or d.get('mails') or
                        d.get('emails') or d.get('data') or [])

                for msg in msgs:
                    mid    = str(msg.get('id') or msg.get('_id') or '')
                    if not mid or mid in seen_ids:
                        continue
                    from_t = str(msg.get('from', '')).lower()
                    subj_t = str(msg.get('subject', '')).lower()
                    is_fb  = ('facebook' in from_t or 'facebookmail' in from_t
                               or 'meta' in from_t
                               or 'confirm' in subj_t or 'code' in subj_t
                               or 'verification' in subj_t or 'registration' in subj_t)
                    seen_ids.add(mid)
                    if not is_fb:
                        continue

                    body = str(msg.get('body_html') or msg.get('html') or
                               msg.get('body') or msg.get('text') or
                               msg.get('bodyhtml') or msg.get('bodytext') or '')
                    if not body:
                        try:
                            er = m.requests.get(
                                f'{_TMAIL_API}/v3/email/{_token}/messages/{mid}',
                                headers=_tmail_hdrs, timeout=10)
                            if er.status_code == 200:
                                try:
                                    ed   = er.json()
                                    body = str(ed.get('body_html') or ed.get('html') or
                                               ed.get('body') or ed.get('text') or
                                               ed.get('bodyhtml') or ed.get('bodytext') or '')
                                except Exception:
                                    body = er.text
                        except Exception:
                            pass

                    code = _extract_code_from_body(body)
                    if code:
                        if _fcn_jq: _fcn_jq.put({'type': 'confirm_code', 'uid': uid, 'code': code})
                        return jsonify({'code': code})
            except Exception:
                pass
            time.sleep(3)
        return jsonify({'status': 'not_found'})

    # ── weyn-emails (cunt.abrdns.com, jinbilowg.cloud-ip.cc, yuennix.work.gd) ─
    _WEYN_EMAILS_API     = 'https://weyn-emails-production.up.railway.app'
    _WEYN_EMAILS_DOMAINS = {'cunt.abrdns.com', 'jinbilowg.cloud-ip.cc', 'yuennix.work.gd'}
    if domain in _WEYN_EMAILS_DOMAINS:
        while time.time() < deadline:
            try:
                r = m.requests.get(f'{_WEYN_EMAILS_API}/api/emails', timeout=10)
                if r.status_code == 200:
                    msgs = r.json() if isinstance(r.json(), list) else []
                    for msg in msgs:
                        if str(msg.get('toAddress', '')).lower() != email.lower():
                            continue
                        mid = str(msg.get('id', ''))
                        if mid in seen_ids:
                            continue
                        from_t = str(msg.get('fromAddress', '')).lower()
                        subj_t = str(msg.get('subject', '')).lower()
                        is_fb  = ('facebook' in from_t or 'facebookmail' in from_t
                                   or 'meta' in from_t
                                   or 'confirm' in subj_t or 'code' in subj_t
                                   or 'verification' in subj_t or 'registration' in subj_t)
                        seen_ids.add(mid)
                        if not is_fb:
                            continue
                        body     = str(msg.get('bodyHtml') or msg.get('bodyText') or '')
                        combined = str(msg.get('subject', '')) + ' ' + body
                        code = _extract_code_from_body(combined)
                        if code:
                            if _fcn_jq: _fcn_jq.put({'type': 'confirm_code', 'uid': uid, 'code': code})
                            return jsonify({'code': code})
            except Exception:
                pass
            time.sleep(3)
        return jsonify({'status': 'not_found'})

    # ── Custom IMAP / Webhook domains ────────────────────────────────────────
    cfg = dm.get_imap_config(domain)
    if cfg:
        dtype = cfg.get('type', 'imap')
        if dtype == 'webhook':
            # Webhook domains receive email via HTTP POST — nothing to poll.
            # Check by uid first, then fall back to email (handles session-restart case).
            stored = _sto.load(f'webhook_code_{uid}', None)
            if not (stored and isinstance(stored, dict) and stored.get('code')):
                stored = _sto.load(f'webhook_code_email_{email}', None)
            if stored and isinstance(stored, dict) and stored.get('code'):
                code = stored['code']
                if _fcn_jq: _fcn_jq.put({'type': 'confirm_code', 'uid': uid, 'code': code})
                # Persist by uid too for future fast lookups
                _sto.save(f'webhook_code_{uid}', {'code': code})
                return jsonify({'code': code})
            return jsonify({'status': 'waiting_webhook',
                            'msg': 'Waiting for email via webhook — check your mail server is forwarding correctly.'})
        # IMAP domain
        imap_host = cfg.get('imap_host', f'mail.{domain}')
        imap_user = cfg.get('imap_user', f'admin@{domain}')
        imap_pass = cfg.get('imap_pass', '')
        try:
            body = m._poll_imap_inbox(
                to_addr=email,
                imap_host=imap_host,
                imap_user=imap_user,
                imap_pass=imap_pass,
                timeout_secs=28,
            )
            if body:
                code = _extract_code_from_body(body)
                if code:
                    if _fcn_jq: _fcn_jq.put({'type': 'confirm_code', 'uid': uid, 'code': code})
                    return jsonify({'code': code})
        except Exception:
            pass
        return jsonify({'status': 'not_found'})

    return jsonify({'status': 'unsupported_domain',
                    'msg': f'No inbox handler configured for {domain}'}), 400


@app.route('/status')
def status():
    job_id = request.args.get('job_id', '')
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        return jsonify({'running': False, 'count': 0})
    return jsonify({'running': job['running'], 'count': len(job['result_store'])})


# ── Admin auth ────────────────────────────────────────────────────────────────

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'yuennix')

def _require_admin():
    return session.get('is_admin') is True

@app.route('/admin')
def admin_panel():
    if not _require_admin():
        return render_template('admin_login.html')
    counts, users = auth.get_stats()
    return render_template('admin.html', counts=counts)

@app.route('/admin/login', methods=['POST'])
def admin_login():
    pw = (request.json or {}).get('password', '')
    if pw == ADMIN_PASSWORD:
        session.permanent = True
        session['is_admin'] = True
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'Wrong password'}), 401

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('is_admin', None)
    return jsonify({'status': 'ok'})

@app.route('/admin/api/stats')
def admin_stats():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    counts, users = auth.get_stats()
    total_accounts = _sto.count_accounts()
    return jsonify({'counts': counts, 'total_accounts': total_accounts})

@app.route('/admin/api/users')
def admin_users():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    users = auth.list_users()
    result = []
    for key, v in users.items():
        result.append({
            'key':         key,
            'user_id':     v.get('user_id', ''),
            'name':        v.get('name', ''),
            'reason':      v.get('reason', ''),
            'status':      v.get('status', ''),
            'created_at':  v.get('created_at'),
            'approved_at': v.get('approved_at'),
            'last_seen':   v.get('last_seen'),
            'locked_ip':   v.get('locked_ip'),
            'expires_at':  v.get('expires_at'),
        })
    result.sort(key=lambda x: x.get('created_at') or 0, reverse=True)
    return jsonify(result)

def _parse_duration(data):
    """Parse duration_value + duration_unit from request body → seconds or None."""
    try:
        val = int(data.get('duration_value') or 0)
    except (ValueError, TypeError):
        val = 0
    if val <= 0:
        return None
    unit = (data.get('duration_unit') or 'hours').lower()
    multipliers = {'mins': 60, 'hours': 3600, 'days': 86400}
    return val * multipliers.get(unit, 3600)

@app.route('/admin/api/approve/<key>', methods=['POST'])
def admin_approve(key):
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    duration_secs = _parse_duration(data)
    ok, entry = auth.approve_key(key.upper(), duration_secs=duration_secs)
    if ok:
        return jsonify({'status': 'approved', 'name': entry['name'], 'expires_at': entry.get('expires_at')})
    return jsonify({'error': 'Key not found'}), 404

@app.route('/admin/api/reject/<key>', methods=['POST'])
def admin_reject(key):
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    ok, entry = auth.reject_key(key.upper())
    if ok:
        return jsonify({'status': 'rejected'})
    return jsonify({'error': 'Key not found'}), 404

@app.route('/admin/api/revoke/<uid>', methods=['POST'])
def admin_revoke(uid):
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    ok, entry = auth.revoke_by_id(uid.upper())
    if ok:
        return jsonify({'status': 'revoked'})
    return jsonify({'error': 'User not found'}), 404

@app.route('/admin/api/reset-ip/<uid>', methods=['POST'])
def admin_reset_ip(uid):
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    ok = auth.unlock_key_ip(uid.upper())
    if ok:
        return jsonify({'status': 'reset'})
    return jsonify({'error': 'User not found or no IP lock set'}), 404

@app.route('/admin/api/remove/<uid>', methods=['POST'])
def admin_remove(uid):
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    ok, entry = auth.remove_by_id(uid.upper())
    if ok:
        return jsonify({'status': 'removed'})
    return jsonify({'error': 'User not found'}), 404

@app.route('/admin/api/add-user', methods=['POST'])
def admin_add_user():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    duration_secs = _parse_duration(data)
    key, uid = auth.add_user(name, duration_secs=duration_secs)
    return jsonify({'key': key, 'user_id': uid, 'name': name})

@app.route('/admin/api/domains')
def admin_domains():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(dm.get_all_info())

@app.route('/admin/api/domains/add-temp', methods=['POST'])
def admin_add_temp():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    domain = ((request.json or {}).get('domain') or '').strip().lower()
    if not domain:
        return jsonify({'error': 'Domain is required'}), 400
    ok = dm.add_temp_domain(domain)
    return jsonify({'status': 'added' if ok else 'exists'})

@app.route('/admin/api/domains/add-custom', methods=['POST'])
def admin_add_custom():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    domain      = (data.get('domain')      or '').strip().lower()
    domain_type = 'webhook'
    if not domain:
        return jsonify({'error': 'Domain is required'}), 400
    ok = dm.add_custom_domain(domain)
    return jsonify({'status': 'added' if ok else 'exists'})


def _get_base_url():
    """Return the public base URL, preferring Replit domain, then request host."""
    replit_domains = os.environ.get('REPLIT_DOMAINS', '').strip()
    if replit_domains:
        first = replit_domains.split(',')[0].strip()
        if first:
            return f'https://{first}'
    replit_dev = os.environ.get('REPLIT_DEV_DOMAIN', '').strip()
    if replit_dev:
        return f'https://{replit_dev}'
    return request.host_url.rstrip('/')


@app.route('/admin/api/site-config')
def admin_site_config():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'base_url': _get_base_url()})


@app.route('/admin/api/webhook-secret')
def admin_webhook_secret():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'token': _get_webhook_secret()})


@app.route('/admin/api/webhook-secret/regenerate', methods=['POST'])
def admin_webhook_secret_regenerate():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    token = _secrets.token_urlsafe(32)
    _sto.save('webhook_secret', {'token': token})
    return jsonify({'token': token})


@app.route('/admin/api/webhook-test', methods=['POST'])
def admin_webhook_test():
    """Send a simulated webhook POST to ourselves to verify the endpoint works."""
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    import requests as _req
    token = _get_webhook_secret()
    # Use localhost to avoid SSL certificate issues with the Replit proxy
    port  = int(os.environ.get('PORT', 5000))
    url   = f'http://localhost:{port}/webhook/email?secret={token}'
    # Simulate exactly what mailwip/hanami.run sends: multipart/form-data
    # with an "email" field containing the email data as a JSON string
    import json as _json
    fake_email_json = _json.dumps({
        'from':    'security@facebookmail.com',
        'to':      'test@exceweyn.run.place',
        'subject': 'Your Facebook confirmation code',
        'body':    'Your confirmation code is 123456. Enter this code to confirm your account.',
    })
    try:
        r = _req.post(url, data={'email': fake_email_json}, timeout=8)
        return jsonify({'status': 'sent', 'response_code': r.status_code,
                        'response': r.json(), 'webhook_url': _get_base_url() + f'/webhook/email?secret={token}'})
    except Exception as e:
        return jsonify({'status': 'error', 'msg': str(e)}), 500

@app.route('/admin/api/domains/remove', methods=['POST'])
def admin_remove_domain():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    domain = ((request.json or {}).get('domain') or '').strip().lower()
    ok = dm.remove_domain(domain)
    return jsonify({'status': 'removed' if ok else 'not_found'})

@app.route('/admin/api/domains/set-password', methods=['POST'])
def admin_set_dm_password():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    pw = ((request.json or {}).get('password') or '').strip()
    if not pw:
        return jsonify({'error': 'Password is required'}), 400
    dm.set_domain_password(pw)
    return jsonify({'status': 'updated'})


# ── Webhook email receiver ────────────────────────────────────────────────────

@app.route('/webhook/email', methods=['POST'])
def webhook_email():
    """
    Receive incoming emails via webhook from mail providers.
    Expects ?secret=TOKEN plus a JSON or form-encoded body with:
      to / recipient / To   — destination address
      subject / Subject
      html / body-html / HtmlBody / body / text / body-plain / TextBody  — email body
    Supported providers: Mailgun, SendGrid, Postmark, and any generic JSON sender.
    """
    secret = request.args.get('secret', '')
    if not secret or secret != _get_webhook_secret():
        return jsonify({'error': 'Unauthorized'}), 401

    # ── Parse body (JSON, form, or mailwip multipart) ─────────────────────
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form.to_dict()

    # ── Mailwip/hanami.run: sends multipart/form-data with an "email" field
    # that contains the actual email as a JSON string. Unpack it first.
    if 'email' in data and isinstance(data.get('email'), str):
        try:
            _inner = json.loads(data['email'])
            if isinstance(_inner, dict):
                # Merge inner fields, letting them override the outer form fields
                data = {**data, **_inner}
        except Exception:
            pass

    def _pick(*keys):
        for k in keys:
            v = data.get(k) or data.get(k.lower()) or data.get(k.upper())
            if v:
                return str(v).strip()
        return ''

    to_addr = _pick('to', 'recipient', 'To', 'Recipient', 'delivered-to')
    subject = _pick('subject', 'Subject')
    body    = _pick('html', 'body-html', 'HtmlBody', 'bodyHtml',
                    'body', 'text', 'body-plain', 'TextBody', 'bodyText')

    # Log what arrived for debugging
    print(f'[webhook] to={to_addr!r} subj={subject!r} body_len={len(body)} keys={list(data.keys())}')

    if not to_addr or not body:
        # Return 200 so mailwip doesn't retry forever, but log what we got
        print(f'[webhook] missing field — raw data keys: {list(data.keys())}')
        return jsonify({'error': 'Missing to or body', 'received_keys': list(data.keys())}), 200

    # Normalise — strip display name if present: "Name <addr>" → "addr"
    m_addr = _re.search(r'<([^>]+)>', to_addr)
    email  = m_addr.group(1).strip().lower() if m_addr else to_addr.strip().lower()

    # ── Find the account session matching this email ───────────────────────
    uid = None
    with _session_lock:
        for _uid, entry in _session_store.items():
            if entry.get('email', '').lower() == email:
                uid = _uid
                break

    code = _extract_code_from_body(body)

    # ── Also check for a direct FB confirmation link ───────────────────────
    link_match = _re.search(
        r'https://(?:www|m)\.facebook\.com/(?:confirm|r\.php)[^\s"<>\]\\]+',
        body, _re.IGNORECASE
    )
    fb_link = link_match.group(0).replace('&amp;', '&').rstrip('.') if link_match else None

    if not code and not fb_link:
        return jsonify({'status': 'no_code_found'}), 200

    if code:
        # Always store by email so retry can find it even if uid is not in memory
        _sto.save(f'webhook_code_email_{email}', {'code': code, 'uid': uid or ''})
        print(f'[webhook] stored code {code!r} for email {email!r} uid={uid!r}')

    if uid:
        # Find the job queue for this uid
        with _session_lock:
            _uid_entry = _session_store.get(uid, {})
        _wh_job_id = _uid_entry.get('job_id', '')
        with _jobs_lock:
            _wh_job = _jobs.get(_wh_job_id)
        _wh_jq = _wh_job['task_queue'] if _wh_job else None

        if code:
            if _wh_jq:
                _wh_jq.put({'type': 'confirm_code', 'uid': uid, 'code': code})
            _sto.save(f'webhook_code_{uid}', {'code': code})

        elif fb_link:
            ses_entry = None
            with _session_lock:
                ses_entry = _session_store.get(uid)
            if ses_entry:
                def _follow_link(ses, link, u, jq):
                    try:
                        _ih = {'User-Agent': m.FB_LITE_UA, 'Accept-Language': 'en-US,en;q=0.9'}
                        r = ses.get(link, headers=_ih, timeout=12, allow_redirects=True)
                        st = 'checkpoint' if 'checkpoint' in str(r.url) else 'confirmed'
                    except Exception:
                        st = 'link_error'
                    if jq:
                        jq.put({'type': 'confirm_result', 'uid': u, 'status': st})
                threading.Thread(target=_follow_link, args=(ses_entry['ses'], fb_link, uid, _wh_jq), daemon=True).start()

    return jsonify({
        'status': 'ok',
        'email':  email,
        'uid':    uid or 'not_found',
        'code':   code or ('link' if fb_link else None),
    })


if __name__ == '__main__':
    auth.start_bot()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
