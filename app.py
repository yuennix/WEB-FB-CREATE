import os
import sys
import json
import time
import queue
import threading
import concurrent.futures as _cfi
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote as _uq

from flask import Flask, render_template, request, jsonify, Response, send_file

sys.path.insert(0, '.')
import main as m

app = Flask(__name__)

# ── Global job state ────────────────────────────────────────────────────────
task_queue   = queue.Queue()
result_store = []
job_running  = False
job_lock     = threading.Lock()

lock         = threading.Lock()   # mirrors main.py's lock
done_count   = [0]                # mirrors main.py's done[0]
cp_count     = [0]                # checkpoint count

WORKERS = 10   # always 10, same as original


# ── Routes ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/start', methods=['POST'])
def start():
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

        if email_domain in m.CUSTOM_DOMAINS:
            if domain_password != m.DOMAIN_PASSWORD:
                return jsonify({'error': 'Wrong domain password'}), 403

        # Reset state
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
            args=(name_type, email_domain, count, password_type,
                  custom_password, gender),
            daemon=True,
        ).start()

    return jsonify({'status': 'started'})


# ── Exact copy of _create_one from main.py, adapted for SSE ─────────────────

def _create_one(name_type, gender, password_type, custom_password, num):
    """
    Direct copy of main.py's _create_one() worker loop.
    Runs until done_count[0] >= num or job_running is False.
    """
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

            # ── Name generation (exact copy) ──────────────────────────────
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

            # ── Sex mapping (exact copy) ──────────────────────────────────
            if gender == '1':
                fb_sex = "2"
            elif gender == '2':
                fb_sex = "1"
            else:
                fb_sex = m.random.choice(["1", "2"])

            phone = m.get_email_for_registration(firstname, lastname)
            pww   = m.get_pass() if password_type == 'auto' else custom_password

            # ── Reg URL (exact copy) ──────────────────────────────────────
            _pt = form.get('privacy_mutation_token', '')
            if _pt:
                _reg_url = (f"https://m.facebook.com/reg/submit/"
                            f"?privacy_mutation_token={_uq(_pt)}&multi_step_form=1&skip_suma=0")
            else:
                _reg_url = "https://m.facebook.com/reg/submit/?multi_step_form=1&skip_suma=0"

            # ── Payload (exact copy) ──────────────────────────────────────
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

            # ── Headers (exact copy) ──────────────────────────────────────
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

            reg_submit  = ses.post(_reg_url, data=payload,
                                   headers=merged_headers, timeout=20)
            login_coki  = ses.cookies.get_dict()

            # ── Success branch (exact copy logic) ────────────────────────
            if "c_user" in login_coki:
                uid = login_coki["c_user"]

                with lock:
                    if done_count[0] >= num or not job_running:
                        return
                    done_count[0] += 1
                    current = done_count[0]

                # Save result and stream to UI
                result = {
                    'num':      current,
                    'name':     f'{firstname} {lastname}',
                    'email':    phone,
                    'password': pww,
                    'uid':      uid,
                    'status':   'success',
                }
                result_store.append(result)

                try:
                    with open('weynFBCreate.txt', 'a') as f:
                        f.write(f"{firstname} {lastname}|{phone}|{pww}|{uid}\n")
                except Exception:
                    pass

                task_queue.put({'type': 'account', 'data': result,
                                'created': current, 'target': num})
                task_queue.put({'type': 'log', 'level': 'success',
                                'msg': (f'[{current}/{num}] ✓ '
                                        f'{firstname} {lastname} | {phone} | UID:{uid}')})

                # ── INSTANT trigger: fire all resend URLs in parallel (exact copy) ──
                _instant_urls = [
                    'https://m.facebook.com/confirmemail.php?send=1',
                    'https://m.facebook.com/confirmemail.php?soft=hjk&send=1',
                    'https://m.facebook.com/confirmemail.php?soft=hjk&resend=1',
                    'https://m.facebook.com/confirmemail.php?soft=1&send=1',
                    'https://www.facebook.com/confirmemail.php?send=1',
                ]
                _ih = {
                    'User-Agent':      m.FB_LITE_UA,
                    'Accept':          'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Referer':         'https://m.facebook.com/confirmemail.php',
                    'x-requested-with':'com.facebook.lite',
                }
                def _ifire(u):
                    try:
                        ses.get(u, headers=_ih, timeout=6, allow_redirects=True)
                    except Exception:
                        pass
                with _cfi.ThreadPoolExecutor(max_workers=len(_instant_urls)) as _ipool:
                    _ipool.map(_ifire, _instant_urls)

                # Background thread handles 1secmail polling + repeat trigger waves (exact copy)
                _t = threading.Thread(
                    target=m._full_email_confirm,
                    args=(ses, phone, uid, pww),
                    daemon=False,
                )
                _t.start()

            # ── Checkpoint branch (exact copy) ────────────────────────────
            elif "checkpoint" in login_coki:
                with lock:
                    cp_count[0] += 1
                task_queue.put({'type': 'log', 'level': 'warn',
                                'msg': (f'⚠ Checkpoint — {firstname} {lastname} | {phone}')})

            # If neither c_user nor checkpoint: loop continues automatically

        except Exception as e:
            task_queue.put({'type': 'log', 'level': 'error', 'msg': str(e)})


# ── Orchestrator ─────────────────────────────────────────────────────────────

def run_creation(name_type, email_domain, count, password_type,
                 custom_password, gender):
    global job_running

    m.EMAIL_DOMAIN = email_domain

    task_queue.put({'type': 'log', 'level': 'info',
                    'msg': (f'Starting {count} account(s) with {WORKERS} workers '
                            f'on {email_domain}…')})

    try:
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futures = [
                pool.submit(_create_one, name_type, gender,
                            password_type, custom_password, count)
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


# ── SSE stream ───────────────────────────────────────────────────────────────

@app.route('/stream')
def stream():
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
    global job_running
    job_running = False
    return jsonify({'status': 'stopped'})


@app.route('/download')
def download():
    path = os.path.abspath('weynFBCreate.txt')
    if os.path.exists(path):
        return send_file(path, as_attachment=True, download_name='weynFBCreate.txt')
    return jsonify({'error': 'No results file yet'}), 404


@app.route('/status')
def status():
    return jsonify({'running': job_running, 'count': len(result_store)})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
