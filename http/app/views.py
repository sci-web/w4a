from app import app
import re
from flask import request, redirect, render_template, url_for, flash, Response, g, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import date
import datetime
from flask_admin.model import typefmt
import os
from .model import DB
from .forms import LoginForm, makeform
from bson.json_util import dumps
import json

@app.before_request
def load_vars():
    g.items = DB().get_spaces_by_key_sorted("vaccines", "date")
    g.objects = DB().get_objects_by_key_sorted("I_S_name")
    g.form = makeform()

def date_format(view, value):
    return value.strftime('%d.%m.%Y')

MY_DEFAULT_FORMATTERS = dict(typefmt.BASE_FORMATTERS)
MY_DEFAULT_FORMATTERS.update({
    type(None): typefmt.null_formatter,
    date: date_format
})


"""regex in template by rehref: replacing markups with HTML a href"""
def rehref(jsonstring):
    return re.sub(r'\[(.*?)\=\=(.*?)\]', r'<a href=\2>\1</a>', "".join(jsonstring)) # join: make it string
app.jinja_env.filters['rehref'] = rehref


@app.route('/')
def index():
    i_data = DB().get_intros()
    return render_template('index.html', form=g.form, items=g.items, objects=g.objects, data=i_data)


@app.route('/content/<namespace>/<codename>')
def show_item(namespace, codename):
    return render_template('index.html', form=g.form, items=g.items, objects=g.objects)


@app.route('/intro/<namespace>',methods=['GET','POST'])
def show_intro(namespace):
    i_data = DB().get_an_intro(namespace)
    data = json.loads(dumps(i_data))
    f_date = datetime.datetime.fromtimestamp( data[0]["date"]['$date'] / 1e3 )
    data[0]["date"] = f_date.strftime('%d-%m-%Y %H:%M')
    if 'div' in request.args:
        return jsonify( {'data': render_template('intro_div.html', idata=data)} )
    else:
        return render_template('intro.html', idata=data, items=g.items, objects=g.objects, title=data[0]["subject"])


@app.route('/chapters/<namespace>',methods=['GET','POST'])
def chapters(namespace):
    i_data = DB().get_spaces_by_key_sorted(namespace, "date")
    data = json.loads(dumps(i_data))
    for i in range(0, len(data)):
        f_date = datetime.datetime.fromtimestamp( data[i]["date"]['$date'] / 1e3 )
        data[i]["date"] = f_date.strftime('%d-%m-%Y %H:%M')
    if 'div' in request.args:
        return jsonify( {'data': render_template('chapt_div.html', idata=data)} )
    else:
        return render_template('chapt.html', idata=data, items=g.items, objects=g.objects, title=namespace)


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


