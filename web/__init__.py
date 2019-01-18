from flask import Flask
import logging
import sys

app = Flask(__name__)
app.secret_key = '\x83k\xfcj\xce\xeeG;;\xb9\x9d\xa4'

from . import views
from . import feed
from . import gallery

