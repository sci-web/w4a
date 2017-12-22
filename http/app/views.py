from app import app
from flask import request, redirect, render_template, url_for, flash, Response
from flask.ext.login import login_user, logout_user, login_required, current_user
from datetime import date
from flask_admin.model import typefmt
import os
from .model import DB
from .forms import LoginForm, makeform


def date_format(view, value):
    return value.strftime('%d.%m.%Y')

MY_DEFAULT_FORMATTERS = dict(typefmt.BASE_FORMATTERS)
MY_DEFAULT_FORMATTERS.update({
    type(None): typefmt.null_formatter,
    date: date_format
})


@app.route('/')
def index():
    # item = app.config['CORE'].find()
    item = {}
    form = makeform()    
    return render_template('index.html', form=form)


@app.route('/next', methods=['GET', 'POST'])
def next():
    form = ClientForm(request.values)
    items = {}
    if request.method == 'POST':
        if form.data:
            data = []
        else:
            flash("Cannot process your form: no data", category='error')
    else:
        flash("Form was not properly sent", category='error')
    return render_template('next.html', items=items, form=form)


@app.route('/tmpl', methods=['GET', 'POST'])
def tmpl():
    start = datetime.datetime.strptime("2016-11-04 00:00:00", '%Y-%m-%d %H:%M:%S')
    end = datetime.datetime.strptime("2016-11-14 23:59:59", '%Y-%m-%d %H:%M:%S')
    items = DB().get_data(start, end)
    return render_template('tmpl.html', items=items)

