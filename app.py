import os
import sys
import json
import time
import queue
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
app.permanent_session_lifetime = _dt.timedelta(days=30)

# ── Global job state ─────────────────────────────────────────────────────────
task_queue   = queue.Queue()
result_store = []
job_running  = False
job_lock     = threading.Lock()

lock       = threading.Lock()
done_count = [0]
cp_count   = [0]

WORKERS = 50   # 50 parallel workers

# ── Session store for confirmation codes (uid → session + meta) ───────────────
_session_store = {}
_session_lock  = threading.Lock()
_SESSION_TTL   = 21600  # keep sessions for 6 hours

def _prune_sessions():
    """Remove sessions older than TTL."""
    cutoff = time.time() - _SESSION_TTL
    with _session_lock:
        stale = [uid for uid, e in _session_store.items() if e['ts'] < cutoff]
        for uid in stale:
            del _session_store[uid]


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.route('/')
def index():
    key = request.cookies.get('access_key', '')
    if key:
        status, entry = auth.check_key(key)
        if status == 'approved':
            auth.touch_key(key)
            return render_template('index.html', user_name=entry.get('name', ''))
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


@app.route('/verify-key', methods=['POST'])
def verify_key():
    data   = request.json or {}
    key    = (data.get('key') or '').strip().upper()
    status, entry = auth.check_key(key)
    if status == 'approved':
        auth.touch_key(key)
        resp = jsonify({
            'status': 'approved',
            'name':    entry['name'],
            'user_id': entry['user_id'],
        })
        resp.set_cookie('access_key', key, max_age=60*60*24*30, httponly=True, samesite='Lax', path='/')
        return resp
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
    status, _ = auth.check_key(key)
    return status == 'approved'


# ── Main routes ───────────────────────────────────────────────────────────────

@app.route('/start', methods=['POST'])
def start():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    global job_running, result_store, done_count, cp_count
    with job_lock:
        if job_running:
            return jsonify({'error': 'A job is already running'}), 400

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

        result_store  = []
        done_count[0] = 0
        cp_count[0]   = 0
        job_running   = True

        while not task_queue.empty():
            try:
                task_queue.get_nowait()
            except queue.Empty:
                break

        threading.Thread(
            target=run_creation,
            args=(name_type, email_domain, count, password_type, custom_password, gender),
            daemon=True,
        ).start()

    return jsonify({'status': 'started'})


# ── Exact _create_one from main.py ────────────────────────────────────────────

def _create_one(name_type, gender, password_type, custom_password, num, session_id):
    global job_running

    while True:
        with lock:
            if done_count[0] >= num or not job_running:
                return

        try:
            ses      = m.requests.Session()
            response = ses.get("https://m.facebook.com/reg/", timeout=15)
            form     = m.extractor(response.text)

            if not form.get("lsd") and not form.get("fb_dtsg"):
                task_queue.put({'type': 'log', 'level': 'warn',
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

                with lock:
                    if done_count[0] >= num or not job_running:
                        return
                    done_count[0] += 1
                    current = done_count[0]

                # Store session so user can submit a confirmation code later
                _prune_sessions()
                with _session_lock:
                    _session_store[uid] = {
                        'ses':      ses,
                        'email':    phone,
                        'password': pww,
                        'ts':       time.time(),
                    }

                result = {
                    'num':      current,
                    'name':     f'{firstname} {lastname}',
                    'email':    phone,
                    'password': pww,
                    'uid':      uid,
                    'status':   'success',
                }
                result_store.append(result)

                _sto.save_account(session_id, uid, pww,
                                  name=f'{firstname} {lastname}', email=phone)


                task_queue.put({'type': 'account', 'data': result,
                                'created': current, 'target': num})
                task_queue.put({'type': 'log', 'level': 'success',
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
                    args=(ses, phone, uid, pww, task_queue),
                    daemon=False,
                ).start()

            elif "checkpoint" in login_coki:
                with lock:
                    cp_count[0] += 1
                task_queue.put({'type': 'log', 'level': 'warn',
                                'msg': f'⚠ Checkpoint — {firstname} {lastname} | {phone}'})

        except Exception as e:
            task_queue.put({'type': 'log', 'level': 'error', 'msg': str(e)})


# ── Orchestrator ──────────────────────────────────────────────────────────────

def run_creation(name_type, email_domain, count, password_type, custom_password, gender):
    global job_running

    import uuid
    session_id = str(uuid.uuid4())

    m.EMAIL_DOMAIN = email_domain

    _sto.save_session(session_id, count, email_domain)

    task_queue.put({'type': 'log', 'level': 'info',
                    'msg': f'Starting {count} account(s) with {WORKERS} workers on {email_domain}…'})

    try:
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futures = [
                pool.submit(_create_one, name_type, gender, password_type, custom_password, count, session_id)
                for _ in range(WORKERS)
            ]
            for f in as_completed(futures):
                try:
                    f.result()
                except Exception as e:
                    task_queue.put({'type': 'log', 'level': 'error', 'msg': str(e)})
    finally:
        job_running = False
        task_queue.put({
            'type':       'done',
            'total':      count,
            'created':    done_count[0],
            'checkpoint': cp_count[0],
            'msg':        (f'Done — {done_count[0]}/{count} created'
                           + (f', {cp_count[0]} checkpointed' if cp_count[0] else '') + '.'),
        })


# ── SSE stream ────────────────────────────────────────────────────────────────

@app.route('/stream')
def stream():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    def generate():
        while True:
            try:
                item = task_queue.get(timeout=20)
                yield f'data: {json.dumps(item)}\n\n'
                if item.get('type') == 'done':
                    break
            except queue.Empty:
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
    global job_running
    job_running = False
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


@app.route('/status')
def status():
    return jsonify({'running': job_running, 'count': len(result_store)})


# ── FB Confirm Page Proxy ──────────────────────────────────────────────────────

@app.route('/fb-confirm-proxy/<uid>')
def fb_confirm_proxy(uid):
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    with _session_lock:
        entry = _session_store.get(uid)

    if not entry:
        return '''<!DOCTYPE html><html><body style="background:#050810;color:#f87171;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;">
        <div style="text-align:center;"><div style="font-size:32px;margin-bottom:16px;">⚠</div>
        <div style="font-size:16px;font-weight:600;">Session expired or not found.</div>
        <div style="font-size:13px;color:#475569;margin-top:8px;">Sessions are kept for 6 hours after account creation.</div></div></body></html>''', 404

    ses = entry['ses']
    _ch = {
        'User-Agent': m.FB_LITE_UA,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
    }
    try:
        r = ses.get('https://m.facebook.com/confirmemail.php', headers=_ch, timeout=15, allow_redirects=True)
        html = r.text
    except Exception as e:
        return f'<p style="color:red">Failed to fetch page: {e}</p>', 502

    # Rewrite form action to go through our submit proxy
    import re as _re2
    from urllib.parse import urljoin

    # Inject base tag and rewrite form action
    toolbar = f'''<div id="weyn-toolbar" style="position:fixed;top:0;left:0;right:0;z-index:99999;background:#0a0f1e;border-bottom:1px solid rgba(0,230,118,0.2);padding:8px 16px;display:flex;align-items:center;gap:12px;font-family:sans-serif;">
  <div style="width:26px;height:26px;background:linear-gradient(135deg,#00e676,#00b84c);border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;color:#000;flex-shrink:0;">W</div>
  <span style="font-size:12px;font-weight:700;color:#f1f5f9;">WEYN — Confirm Email</span>
  <span style="font-size:11px;color:#475569;margin-left:4px;">UID: {uid}</span>
  <span style="margin-left:auto;font-size:11px;color:#334155;">Submitting form will use the account session</span>
</div>
<div style="height:45px;"></div>'''

    # Add base tag so relative URLs resolve to Facebook
    base_tag = '<base href="https://m.facebook.com/">'

    # Rewrite all form actions to our submit endpoint
    def rewrite_action(match):
        return f'action="/fb-confirm-proxy/{uid}/submit"'

    html = _re2.sub(r'action="[^"]*"', rewrite_action, html)
    html = _re2.sub(r"action='[^']*'", lambda m2: f"action='/fb-confirm-proxy/{uid}/submit'", html)

    # Inject base tag and toolbar after <head> and <body>
    html = _re2.sub(r'(<head[^>]*>)', r'\1' + base_tag, html, count=1, flags=_re2.IGNORECASE)
    html = _re2.sub(r'(<body[^>]*>)', r'\1' + toolbar, html, count=1, flags=_re2.IGNORECASE)

    return Response(html, mimetype='text/html')


@app.route('/fb-confirm-proxy/<uid>/submit', methods=['POST'])
def fb_confirm_proxy_submit(uid):
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    with _session_lock:
        entry = _session_store.get(uid)

    if not entry:
        return '''<!DOCTYPE html><html><body style="background:#050810;color:#f87171;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;">
        <div style="text-align:center;"><div style="font-size:32px;">⚠</div>
        <div style="font-size:14px;font-weight:600;margin-top:12px;">Session expired.</div></div></body></html>''', 404

    ses = entry['ses']
    form_data = dict(request.form)

    _ph = {
        'User-Agent': m.FB_LITE_UA,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://m.facebook.com',
        'Referer': 'https://m.facebook.com/confirmemail.php',
        'upgrade-insecure-requests': '1',
        'x-requested-with': 'com.facebook.lite',
    }

    try:
        resp = ses.post('https://m.facebook.com/confirmemail.php', data=form_data,
                        headers=_ph, allow_redirects=True, timeout=18)
        html = resp.text
        final_url = str(resp.url)
    except Exception as e:
        return f'<p style="color:red">Submit error: {e}</p>', 502

    import re as _re2

    # Detect result
    u = final_url.lower()
    t = html.lower()
    if 'checkpoint' in u:
        result_banner_color = '#fbbf24'
        result_banner_text = '⚠ Checkpoint triggered — account may need manual review.'
    elif ('home.php' in u or u.rstrip('/').endswith('facebook.com')
            or 'confirmed' in t or 'verified' in t or 'thank' in t or 'success' in t):
        result_banner_color = '#00e676'
        result_banner_text = '✓ Email confirmed successfully!'
    else:
        result_banner_color = '#60a5fa'
        result_banner_text = '↑ Code submitted — check response below.'

    toolbar = f'''<div id="weyn-toolbar" style="position:fixed;top:0;left:0;right:0;z-index:99999;background:#0a0f1e;border-bottom:1px solid rgba(0,230,118,0.2);padding:8px 16px;display:flex;align-items:center;gap:12px;font-family:sans-serif;">
  <div style="width:26px;height:26px;background:linear-gradient(135deg,#00e676,#00b84c);border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;color:#000;flex-shrink:0;">W</div>
  <span style="font-size:12px;font-weight:700;color:{result_banner_color};">{result_banner_text}</span>
  <button onclick="window.location.href='/fb-confirm-proxy/{uid}'" style="margin-left:auto;padding:5px 12px;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:6px;color:#94a3b8;font-size:11px;cursor:pointer;">↩ Back</button>
</div>
<div style="height:45px;"></div>'''

    base_tag = '<base href="https://m.facebook.com/">'

    def rewrite_action(match):
        return f'action="/fb-confirm-proxy/{uid}/submit"'

    html = _re2.sub(r'action="[^"]*"', rewrite_action, html)
    html = _re2.sub(r"action='[^']*'", lambda m2: f"action='/fb-confirm-proxy/{uid}/submit'", html)
    html = _re2.sub(r'(<head[^>]*>)', r'\1' + base_tag, html, count=1, flags=_re2.IGNORECASE)
    html = _re2.sub(r'(<body[^>]*>)', r'\1' + toolbar, html, count=1, flags=_re2.IGNORECASE)

    return Response(html, mimetype='text/html')


# ── Confirm code endpoint ──────────────────────────────────────────────────────

from bs4 import BeautifulSoup as _BS4

def _check_confirmed(url, text):
    """Return True if the response indicates the email is now confirmed."""
    u = url.lower()
    t = text.lower()
    if 'checkpoint' in u:
        return None   # checkpoint
    if ('home.php' in u or u.rstrip('/').endswith('facebook.com')
            or 'confirmed' in t or 'verified' in t
            or 'thank' in t or 'success' in t):
        return True
    return False


def _submit_confirm_form(ses, page_html, page_url, code, email, uid):
    """
    Parse the confirmation form from page_html, fill in the code, POST it.
    Returns (resp_url, resp_text) or raises.
    """
    soup = _BS4(page_html, 'html.parser')

    # Find the form — FB mobile sometimes wraps it inside a specific div
    form = soup.find('form')
    if not form:
        return None, None

    # Resolve action URL
    action = form.get('action', '').strip()
    if action and not action.startswith('http'):
        action = 'https://m.facebook.com' + action
    if not action:
        action = 'https://m.facebook.com/confirmemail.php'

    # Collect ALL hidden + visible inputs
    form_data = {}
    for inp in form.find_all('input'):
        name = inp.get('name', '').strip()
        val  = inp.get('value', '')
        if name:
            form_data[name] = val

    # Inject the confirmation code into the right field
    _code_names = ['code', 'n', 'confirm_code', 'confirmation_code', 'ccode']
    injected = False
    for fn in _code_names:
        if fn in form_data:
            form_data[fn] = code
            injected = True
            break

    if not injected:
        # Find the first unfilled text/number/tel input — that's the code box
        for inp in form.find_all('input'):
            itype = (inp.get('type') or 'text').lower()
            iname = inp.get('name', '').strip()
            ival  = inp.get('value', '').strip()
            if itype in ('text', 'number', 'tel') and iname and not ival:
                form_data[iname] = code
                injected = True
                break

    if not injected:
        form_data['code'] = code

    _ph = {
        'User-Agent':      m.FB_LITE_UA,
        'Accept':          'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type':    'application/x-www-form-urlencoded',
        'Origin':          'https://m.facebook.com',
        'Referer':         page_url,
        'Cache-Control':   'max-age=0',
        'sec-ch-ua':       '"Android WebView";v="109", "Chromium";v="109", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest':  'document',
        'sec-fetch-mode':  'navigate',
        'sec-fetch-site':  'same-origin',
        'upgrade-insecure-requests': '1',
        'x-requested-with': 'com.facebook.lite',
    }

    resp = ses.post(action, data=form_data, headers=_ph,
                    allow_redirects=True, timeout=18)
    return str(resp.url), resp.text


def _submit_cliff(ses, page_html, email, uid, code):
    """
    Try the confirmation_cliff/ endpoint using tokens extracted from page_html.
    Returns (resp_url, resp_text) or (None, None) if tokens are missing.
    """
    def _ext(patterns, src):
        for pat in patterns:
            mm = _re.search(pat, src)
            if mm:
                return mm.group(1)
        return ''

    # Parse tokens with BeautifulSoup first (more reliable)
    soup     = _BS4(page_html, 'html.parser')
    fb_dtsg  = ''
    jazoest  = ''
    lsd      = ''

    for inp in soup.find_all('input', {'name': True}):
        n = inp['name']
        v = inp.get('value', '')
        if n == 'fb_dtsg':   fb_dtsg = v
        elif n == 'jazoest': jazoest = v
        elif n == 'lsd':     lsd     = v

    # Fallback to regex
    if not fb_dtsg:
        fb_dtsg = _ext([r'"token":"([^"]+)"',
                        r'name="fb_dtsg"\s+value="([^"]+)"',
                        r'\["DTSGInitData"[^\]]*\],\{"token":"([^"]+)"'], page_html)
    if not jazoest:
        jazoest = _ext([r'name="jazoest"\s+value="(\d+)"', r'"jazoest":"(\d+)"'], page_html)
    if not lsd:
        lsd = _ext([r'name="lsd"\s+value="([^"]+)"',
                    r'"LSD",\[\],\{"token":"([^"]+)"\}',
                    r'"lsd":"([^"]+)"'], page_html)

    if not fb_dtsg:
        return None, None   # can't proceed without CSRF token

    rev = (_ext([r'"client_revision":(\d+)', r'"server_revision":(\d+)'], page_html)
           or '1015920645')

    _ph = {
        'User-Agent':      m.FB_LITE_UA,
        'Accept':          'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Cache-Control':   'max-age=0',
        'Content-Type':    'application/x-www-form-urlencoded',
        'Origin':          'https://m.facebook.com',
        'Referer':         'https://m.facebook.com/confirmemail.php?soft=hjk',
        'sec-ch-ua':       '"Android WebView";v="109", "Chromium";v="109", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest':  'document',
        'sec-fetch-mode':  'navigate',
        'sec-fetch-site':  'same-origin',
        'upgrade-insecure-requests': '1',
        'x-requested-with': 'com.facebook.lite',
        'x-fb-lsd':        lsd,
    }

    resp = ses.post(
        'https://m.facebook.com/confirmation_cliff/',
        params={
            'contact':       email,
            'type':          'submit',
            'is_soft_cliff': 'false',
            'medium':        'email',
            'code':          code,
        },
        data={
            'fb_dtsg':     fb_dtsg,
            'jazoest':     jazoest,
            'lsd':         lsd,
            '__dyn':       '',
            '__csr':       '',
            '__req':       str(_random.randint(4, 12)),
            '__a':         '1',
            '__user':      uid,
            '__rev':       rev,
            '__s':         (f'{_random.randint(0,9)}:{_random.randint(0,9)}'
                            f':{_random.randint(0,9)}'),
            '__hsi':       str(_random.randint(7000000000000000000,
                                               7999999999999999999)),
            '__comet_req': '0',
            'action':      'confirm',
        },
        headers=_ph,
        allow_redirects=True,
        timeout=18,
    )
    return str(resp.url), resp.text


def _manual_submit_code(ses, email, uid, code):
    """
    Used by /confirm-code for manual submission.
    Works on a fresh session copy to avoid race conditions with the background thread.
    Returns 'confirmed', 'checkpoint', or 'failed'.
    """
    import requests as _rq
    # Fresh session with same cookies — avoids interference from background thread
    fresh = _rq.Session()
    fresh.cookies.update(ses.cookies.get_dict())

    _ch = {
        'User-Agent':      m.FB_LITE_UA,
        'Accept':          'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'x-requested-with': 'com.facebook.lite',
    }
    _ph = {
        **_ch,
        'Content-Type':    'application/x-www-form-urlencoded',
        'Origin':          'https://m.facebook.com',
        'Cache-Control':   'max-age=0',
        'sec-ch-ua':       '"Android WebView";v="109", "Chromium";v="109", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile':    '?1',
        'sec-ch-ua-platform':  '"Android"',
        'sec-fetch-dest':  'document',
        'sec-fetch-mode':  'navigate',
        'sec-fetch-site':  'same-origin',
        'upgrade-insecure-requests': '1',
    }

    def _chk(url, text):
        u = url.lower(); t = text.lower()
        if 'checkpoint' in u:
            return 'checkpoint'
        if ('home.php' in u or u.rstrip('/').endswith('facebook.com')
                or 'confirmed' in t or 'verified' in t or 'thank' in t):
            return 'confirmed'
        return None

    # ── A1: Parse form from confirmemail.php, inject code, POST ──────────────
    for _url in [
        'https://m.facebook.com/confirmemail.php',
        'https://m.facebook.com/confirmemail.php?soft=hjk',
        'https://m.facebook.com/confirmemail.php?soft=1',
    ]:
        try:
            _r = fresh.get(_url, headers=_ch, timeout=12, allow_redirects=True)
            _ru = str(_r.url)
            q = _chk(_ru, _r.text)
            if q:
                return q
            html = _r.text
            soup = _BS4(html, 'html.parser')
            fd   = {}
            act  = _url
            form = soup.find('form')
            if form:
                _a = form.get('action', '').strip()
                if _a:
                    act = _a if _a.startswith('http') else 'https://m.facebook.com' + _a
                for inp in form.find_all('input'):
                    n = inp.get('name', '').strip()
                    v = inp.get('value', '')
                    if n:
                        fd[n] = v
            # Broaden CSRF token extraction
            if not fd.get('fb_dtsg'):
                mm = _re.search(r'"token"\s*:\s*"([^"]{10,})"', html)
                if mm:
                    fd['fb_dtsg'] = mm.group(1)
            if not fd.get('lsd'):
                mm = _re.search(r'"LSD"[^{]*\{"token":"([^"]+)"', html)
                if mm:
                    fd['lsd'] = mm.group(1)
            # Inject code into every known field name
            for fn in ['n', 'code', 'confirm_code']:
                fd[fn] = code
            resp = fresh.post(act, data=fd,
                              headers={**_ph, 'Referer': _url},
                              allow_redirects=True, timeout=15)
            q = _chk(str(resp.url), resp.text)
            if q:
                return q
        except Exception:
            pass

    # ── A2: confirmation_cliff with CSRF tokens ───────────────────────────────
    try:
        _r   = fresh.get('https://m.facebook.com/confirmemail.php',
                         headers=_ch, timeout=10)
        html = _r.text
        soup = _BS4(html, 'html.parser')
        fb_dtsg = jazoest = lsd = ''
        for inp in soup.find_all('input', {'name': True}):
            n = inp['name']; v = inp.get('value', '')
            if n == 'fb_dtsg':   fb_dtsg  = v
            elif n == 'jazoest': jazoest  = v
            elif n == 'lsd':     lsd      = v
        if not fb_dtsg:
            mm = _re.search(r'"token"\s*:\s*"([^"]{10,})"', html)
            if mm:
                fb_dtsg = mm.group(1)
        if fb_dtsg:
            resp = fresh.post(
                'https://m.facebook.com/confirmation_cliff/',
                params={
                    'contact':       email,
                    'type':          'submit',
                    'is_soft_cliff': 'false',
                    'medium':        'email',
                    'code':          code,
                },
                data={
                    'fb_dtsg':  fb_dtsg,
                    'jazoest':  jazoest,
                    'lsd':      lsd,
                    'action':   'confirm',
                    '__user':   uid,
                    '__a':      '1',
                    '__dyn':    '',
                    '__csr':    '',
                },
                headers={**_ph,
                         'Referer':  'https://m.facebook.com/confirmemail.php',
                         'x-fb-lsd': lsd},
                allow_redirects=True,
                timeout=15,
            )
            q = _chk(str(resp.url), resp.text)
            if q:
                return q
    except Exception:
        pass

    # ── A3: Final state check ─────────────────────────────────────────────────
    try:
        _ck = fresh.get('https://m.facebook.com/', headers=_ch,
                        timeout=10, allow_redirects=True)
        q = _chk(str(_ck.url), _ck.text)
        if q:
            return q
    except Exception:
        pass

    return 'failed'


@app.route('/confirm-code', methods=['POST'])
def confirm_code_route():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json or {}
    uid  = (data.get('uid') or '').strip()
    code = (data.get('code') or '').strip()

    if not uid or not code:
        return jsonify({'error': 'UID and code required'}), 400

    with _session_lock:
        entry = _session_store.get(uid)
    if not entry:
        return jsonify({'error': 'Session expired — re-create the account to try again'}), 404

    ses   = entry['ses']
    email = entry['email']

    try:
        result = _manual_submit_code(ses, email, uid, code)
        if result == 'confirmed':
            return jsonify({'status': 'confirmed'})
        if result == 'checkpoint':
            return jsonify({'status': 'checkpoint'})
        return jsonify({'status': 'submitted',
                        'note': 'Code sent to Facebook — check if email is confirmed.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
        })
    result.sort(key=lambda x: x.get('created_at') or 0, reverse=True)
    return jsonify(result)

@app.route('/admin/api/approve/<key>', methods=['POST'])
def admin_approve(key):
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    ok, entry = auth.approve_key(key.upper())
    if ok:
        return jsonify({'status': 'approved', 'name': entry['name']})
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
    key, uid = auth.add_user(name)
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
    domain = (data.get('domain') or '').strip().lower()
    imap_pass = (data.get('imap_pass') or '').strip()
    if not domain:
        return jsonify({'error': 'Domain is required'}), 400
    ok = dm.add_custom_domain(domain, imap_pass)
    return jsonify({'status': 'added' if ok else 'exists'})

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


if __name__ == '__main__':
    auth.start_bot()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
