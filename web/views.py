from .feed import *
from json import loads

from hashlib import sha256
import requests
import logging


from flask import render_template, session, request, redirect, url_for


log = logging.getLogger(__name__)


@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('login.html', recaptcha_public=app.config['RECAPTCHA_PUBLIC_KEY'])
    else:
        return render_template('feed.html')


@app.route('/login', methods=['POST'])
def do_admin_login():
    response = request.form.get('g-recaptcha-response')
    ip = request.environ['REMOTE_ADDR']
    log.info('Login attempt from {}'.format(ip))
    if not check_recaptcha(response, ip):
        log.warning("Invalid captcha")
        return render_template('login.html')
    hashed_pass = sha256(request.form['password'].encode()).hexdigest()
    if hashed_pass == app.config['credentials']['sha256_password'] and request.form['username'] == 'ja':
        session['logged_in'] = True
        log.warning("Credentials accepted")
        return render_template('feed.html')
    else:
        log.warning("Credentials rejected")
    return render_template('login.html')


@app.route('/logout')
def do_admin_logout():
    session['logged_in'] = False
    return redirect(url_for('index'))


def check_recaptcha(response, ip):
    if not app.config['use_recaptcha']:
        return True
    try:
        content = requests.post('https://www.google.com/recaptcha/api/siteverify',
                                data={'secret': app.config['RECAPTCHA_PRIVATE_KEY'],
                                      'response': response,
                                      'remoteip': ip}).content
    except ConnectionError:
        log.error('Cannot connect to google for captcha verification')
        return False
    jsonobj = loads(content.decode('utf-8'))
    if jsonobj['success']:
        return True
    else:
        return False


if __name__ == '__main__':
    pass
