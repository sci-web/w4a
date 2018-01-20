from app import app
from flask_wtf import Form
from flask import request, flash
from flask_admin.form.upload import FileUploadField
from flask_login import login_user, logout_user, login_required, current_user
from wtforms import StringField, PasswordField, HiddenField, DateField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
import os.path as op
from .auth import Auth


def prefix_name(obj, file_data):
    parts = op.splitext(file_data.filename)
    return secure_filename('file-%s%s' % parts)

class searchForm(Form):
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


class LoginForm(Form):
    """Login form to access writing and settings pages"""
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    from_url = HiddenField('', validators=[DataRequired()])


class editIntro(Form):
	subject = StringField('Subject', validators=[DataRequired()])
	namespace = StringField('Subject', validators=[DataRequired()])

	    #  Namespace: {{ sform.namespace }} <font color="red">(*)</font>
        #     Epigraph text: {{ sform.epigraph_text }}<br>
        #     Epigraph source: {{ sform.epigraph_source }}
        # Introduction: {{ sform.intro }}
        #     Point: {{ sform.point }}<br>
        #     <a href="/edit/?add_intro_point">add next point</a>
        #     References header: {{ sform.ref_header }}<br>
        #     References intro: {{ sform.ref_intro }}
        #         References block #1 title: {{ sform.ref_title_1 }}<br>
        #         References block #1 digest: {{ sform.ref_digest_1 }}
        #                 Link #1 title: {{ sform.ref_1_link_title_1 }}<br>
        #                 Link #1 address: {{ sform.ref_1_link_href_1 }}<br>
        #                 Link #1 type: {{ sform.ref_1_link_type_1 }}<br>
        #                 Link #1 digest: {{ sform.ref_1_link_digest_1 }}<br>
        #         Summary: {{ sform.summary }}