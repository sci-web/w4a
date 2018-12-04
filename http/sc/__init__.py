from flask import Flask, render_template
from flask_login import LoginManager
from flask_session import Session

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['DEBUG'] = True
app.config['TRAP_HTTP_EXCEPTIONS'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config.from_object('config')

session = Session(app)
session.sid = {}

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

try: 
    print app.config['DB'].last_status()["connectionId"]
except Exception, e:
    print "DB Server error, connection is", app.config['DB']

from sc import views, controls, tools