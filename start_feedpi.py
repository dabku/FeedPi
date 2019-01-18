from web import app
import threading
from libs.feedpi import FeedPi
import logging
import json
import sys
from logging.handlers import RotatingFileHandler
from os import path, makedirs


def create_app(spi_instance, security_config):
    app.config['RECAPTCHA_PRIVATE_KEY'] = security_config['recaptcha_secretkey']
    app.config['RECAPTCHA_PUBLIC_KEY'] = security_config['recaptcha_sitekey']
    app.config['use_https'] = security_config['use_adhoc_https']
    app.config['use_recaptcha'] = security_config['use_recaptcha']
    app.config['credentials'] = {'user': security_config['user'],
                                 'sha256_password': security_config['sha256_password']}
    app.config['sPi'] = spi_instance


def flask_runner():
    if not app.config['use_https']:
        app.run(host='0.0.0.0', debug=False, threaded=True, ssl_context=None)
    else:
        app.run(host='0.0.0.0', debug=False, threaded=True, ssl_context='adhoc')


def setup_logger(debug):
    loga = logging.getLogger("werkzeug")
    loga.setLevel(logging.ERROR)
    loga = logging.getLogger("urllib3")
    loga.setLevel(logging.ERROR)
    web_log = logging.getLogger("web")
    if web_log.hasHandlers():
        web_log.handlers.clear()

    script_dir = path.dirname(path.realpath(sys.argv[0]))
    if not path.exists(path.join(script_dir, 'log')):
        makedirs(path.join(script_dir, 'log'))
    log = logging.getLogger(__name__)
    for module, level in debug['debug_modules'].items():
        if level is None:
            continue
        log = logging.getLogger(module)
        log.propagate = False
        handler = RotatingFileHandler(debug['log_path'], maxBytes=1048576, backupCount=5)

        formatter = logging.Formatter(
            '%(asctime)s%(levelname)8s()|%(filename)s:%(lineno)s - %(funcName)s() - %(message)s')
        handler.setFormatter(formatter)
        log.addHandler(handler)
        web_log.addHandler(handler)

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        log.addHandler(handler)
        web_log.addHandler(handler)
        log.setLevel(level)
    return log


if __name__ == '__main__':

    with open('config.json') as cnf_file:
        config = json.load(cnf_file)

    logger = setup_logger(config['debug'])

    logger.info('starting SecurityPi')
    fPi = FeedPi('config.json')
    with open('config.json') as cnf_file:
        config = json.load(cnf_file)
    security_settings = config['security']
    logger.info('Creating App for Web interface')
    create_app(fPi, security_settings)

    flask_thread = threading.Thread(target=flask_runner)
    flask_thread.setDaemon(True)
    logger.info('Starting Flask thread')
    flask_thread.start()

    while True:
        fPi.loop()
