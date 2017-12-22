from app import app
from flask.ext.wtf import Form
from flask import request, flash
from flask.ext.admin.form.upload import FileUploadField
from wtforms import StringField, PasswordField, HiddenField, DateField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
import os.path as op


def prefix_name(obj, file_data):
    parts = op.splitext(file_data.filename)
    return secure_filename('file-%s%s' % parts)


def makeform():
    form = LoginForm(request.values, from_url=request.path)
    if request.method == 'POST' and form.validate_on_submit():
        user = app.config['CORE'].find_one({"email": form.email.data})
        if user and Auth.validate_login(user['password'], form.password.data):
            user_obj = Auth(user['email'], user['access'], user['name'])
            login_user(user_obj)
            flash("Logged in successfully!", category='success')
            # return redirect(request.args.get("next") or url_for("edit"))
        else:
            flash("Wrong username or password!", category='error')
    return form


class LoginForm(Form):
    """Login form to access writing and settings pages"""
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    from_url = HiddenField('', validators=[DataRequired()])
