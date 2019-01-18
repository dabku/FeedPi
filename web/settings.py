from . import app, feed, gallery


from flask import render_template, Response, make_response,jsonify,session,request,flash, send_from_directory
from os import path, walk, listdir


@app.route('/settings')
def settings():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('settings.html')


@app.route('/_save_settings', methods=['POST'])
def save_settings():
    settings_json = request.get_json()
    settings_json['discord']['server_address'] = 'backend_cleared'
    settings_json['discord']['comm_port'] = 'backend_verified'
    result = app.config['sPi'].change_config(settings_json)
    return jsonify(result=result)


# @app.route('/_get_settings')
# def get():
#     settings_json = app.config['sPi'].get_settings()
#     settings_json['discord']['comm_port'] = settings_json['discord']['server_address'] = 'hidden'
#     return jsonify(result='OK', settings=settings_json)


@app.route('/_save_settings_file', methods=['POST'])
def save_settings_file():
    if session.get('logged_in'):
        app.config['sPi'].save_settings()
        return jsonify(result='OK')
    else:
        return jsonify(result='Logged out')


@app.route('/_load_settings_file', methods=['POST'])
def load_settings_file():
    if session.get('logged_in'):
        app.config['sPi'].get_settings()
        return jsonify(result='OK')
    else:
        return jsonify(result='Logged out')


@app.route('/_save_smpt_pwd', methods=['POST'])
def save_smpt_pwd():
    pas = request.get_json()['password']
    if session.get('logged_in'):
        result = app.config['sPi'].set_smtp_pass(pas)
        return jsonify(result=result)
    else:
        return jsonify(result='Logged out')


@app.route('/_get_settings')
def get_setings():
    if session.get('logged_in'):
        settings_json = app.config['sPi'].get_settings()
        settings_json['discord']['comm_port'] = settings_json['discord']['server_address'] = 'hidden'
        return jsonify(result='OK', settings=settings_json)
    return render_template('login.html')


@app.route('/_test_email', methods=['POST'])
def test_email():
    if session.get('logged_in'):
        app.config['sPi'].sendEmailTest()
        return jsonify(result='OK')
    else:
        return jsonify(result='Logged out')
