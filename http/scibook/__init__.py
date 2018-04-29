from flask import Flask
from flask_login import LoginManager
from flask_session import Session

app = Flask(__name__)

app.config.from_object('config')

session = Session(app)
session.sid = {}


lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

from scibook import views, controls, tools
