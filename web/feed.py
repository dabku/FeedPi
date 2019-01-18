from web import app
from flask import render_template, make_response, jsonify, session


@app.route('/jpg_feed')
def jpg_feed():
    if session.get('logged_in'):
        response = make_response(get_jpg())
        response.headers['Content-Type'] = 'image/jpg'
        response.headers['Pragma-directive'] = 'no-cache'
        response.headers['Cache-directive'] = 'no-cache'
        response.headers['Cache-control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    return render_template('login.html')


@app.route('/jpg_thr_feed')
def jpg_thr_feed():

    response = make_response(get_thr_jpg())
    response.headers['Content-Type'] = 'image/jpg'
    response.headers['Pragma-directive'] = 'no-cache'
    response.headers['Cache-directive'] = 'no-cache'
    response.headers['Cache-control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/feed')
def feed():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('feed.html')


@app.route('/_save_image', methods=['POST'])
def save_image():
    app.config['sPi'].save_image()
    return jsonify(result='OK')


def get_jpg():
    if session.get('logged_in'):
        return app.config['sPi'].get_frame_jpg()
    else:
        return app.config['sPi'].get_mock_jpg()


def get_thr_jpg():
    if session.get('logged_in'):
        return app.config['sPi'].get_frame_threshold_jpg()
    else:
        return app.config['sPi'].get_mock_jpg()
