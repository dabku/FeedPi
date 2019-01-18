from . import app, feed, settings


from flask import render_template, Response, make_response,jsonify,session,request,flash, send_from_directory
from os import path, walk, listdir

@app.route('/gallery')
def gallery():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('gallery.html')

@app.route('/_get_images')
def get_photos():
    directory = app.config['sPi'].images_dir
    imgs = {'still_imgs': [],
            'videos': []}
    for data_file in listdir(directory):
        file_path = path.join("", data_file)
        imgs['still_imgs'].append(file_path)
    return jsonify(result=imgs, dir="/data/")

@app.route('/data/<path:filename>')
def imgs_dir(filename):
    directory = app.config['sPi'].images_dir
    return send_from_directory(directory, filename)
