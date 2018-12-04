from scibook import app
from flask_wtf import FlaskForm
from flask import request, flash
from flask_admin.form.upload import FileUploadField
from flask_login import login_user, logout_user, login_required, current_user
from wtforms import StringField, PasswordField, HiddenField, DateField, SelectField, TextAreaField, RadioField, BooleanField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
import os.path as op
from .auth import Auth


def prefix_name(obj, file_data):
    parts = op.splitext(file_data.filename)
    return secure_filename('file-%s%s' % parts)

class searchForm(FlaskForm):
    search = StringField('search')

def makeform():
    form = LoginForm(request.values, from_url=request.path)
    if request.method == 'POST' and form.validate_on_submit():
        user = app.config['CORE'].find_one({"email": form.email.data})
        if user and Auth.validate_login(user['password'], form.password.data):
            user_obj = Auth(user['email'], user['access'], user['author'])
            login_user(user_obj)
            # flash("Logged in successfully!", category='success')
            # return redirect(request.args.get("next") or url_for("edit"))
        else:
            flash("Wrong username or password!", category='info')
    return form


class LoginForm(FlaskForm):
    """Login form to access writing and settings pages"""
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    from_url = HiddenField('', validators=[DataRequired()])

class saveIntro(FlaskForm):
	subject = StringField('Subject', validators=[DataRequired()])

class newIntro(FlaskForm):
	subject = StringField('Subject', validators=[DataRequired()])
	namespace = StringField('Namespace', validators=[DataRequired()])

class saveChapter(FlaskForm):
	title = StringField('Title', validators=[DataRequired()])

class newChapter(FlaskForm):
	title = StringField('Title', validators=[DataRequired()])
	chapter = StringField('Namespace', validators=[DataRequired()])

class ContactForm(FlaskForm):
	subject = StringField('Subject', validators=[DataRequired()])
	email = StringField('Email', validators=[DataRequired()])
	msg = TextAreaField('Message', validators=[DataRequired()])

