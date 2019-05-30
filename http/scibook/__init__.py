from flask import Flask, render_template
from flask_login import LoginManager
from flask_session import Session
import logging

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['DEBUG'] = True
app.config['TRAP_HTTP_EXCEPTIONS'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config.from_object('config')
logging.basicConfig(filename='./controls.log',level=logging.DEBUG)

session = Session(app)
session.sid = {}

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

try:
    print app.config['DB'].last_status()["connectionId"]
except Exception, e:
    print "DB Server error, connection is", app.config['DB']
    # return " DB Server error, connection is", app.config['DB']

from scibook import views, controls, tools
