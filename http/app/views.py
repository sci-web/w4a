from app import app
from flask import request, redirect, render_template, url_for, flash, Response
import datetime
import os
from itertools import chain
from .forms import ClientForm
from .model import DB


@app.route('/')
def index():
    form = ClientForm()
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

