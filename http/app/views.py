from app import app
import re
from flask import request, redirect, render_template, url_for, flash, Response, g, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import date
import datetime
from flask_admin.model import typefmt
import os
from .model import DB
from .forms import LoginForm, makeform, searchForm
from bson.json_util import dumps
import json

@app.before_request
def load_vars():
    g.items = DB().get_spaces_by_key_sorted("vaccines", "date")
    g.objects = DB().get_objects_by_key_sorted_filter_yes("disease", "I_S_name")
    g.drugs = DB().get_objects_by_key_sorted_filter_yes("drug", "I_S_name")
    g.conditions = DB().get_objects_by_key_sorted_filter_yes("condition", "I_S_name")    
    g.objects_geo = DB().get_objects_by_key_sorted_filter_yes("geo", "I_S_name")
    g.chapters = DB().get_spaces_by_key_sorted("vaccines", "date")
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
    jsonstring = re.sub(r'\[\]', r'', "".join(jsonstring))
    return re.sub(r'\[(.*?)\=\=(.*?)\]', r'<a href=\2>\1</a>', "".join(jsonstring)) # join: make it string

app.jinja_env.filters['rehref'] = rehref


@app.route('/')
def index():
    i_data = DB().get_intros()
    return render_template('index.html', form=g.form, items=g.items, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, 
                    chapters=g.chapters, data=i_data)


@app.route('/content/<namespace>/<codename>')
def show_item(namespace, codename):
    i_data = DB().get_a_space(namespace, codename)
    data = json.loads(dumps(i_data))
    title = data["title"]
    chapters = DB().get_spaces_by_key_sorted(namespace, "date")
    f_date = datetime.datetime.fromtimestamp( data["date"]['$date'] / 1e3 )
    data["date"] = f_date.strftime('%d-%m-%Y %H:%M')
    return render_template('content.html', idata=data, form=g.form, items=g.items, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, 
                            title=namespace.title() + ": " + title, chapters=chapters)


@app.route('/search', methods=['GET','POST'])
def search():
    i_data = {}
    searchfor = ""
    sform = searchForm(request.values)
    fdata = []  # filtered data    
    if request.method == 'POST':
        if sform.data["search"]:
            searchfor = sform.data["search"]
            i_data = DB().search(searchfor)
            idata = json.loads(dumps(i_data))
            for r in idata:
                m_regex = r'\[.*?\=\=.*?\]'
                txt = r["points"]["digest"]
                fnd_link = re.findall(m_regex, txt, re.IGNORECASE)
                words = []
                if len(fnd_link) == 0:
                    fdata.append(r)
                else:
                    for fl in fnd_link:
                        (word, lnk) = fl.split("==")
                        w = re.findall(searchfor, word, re.IGNORECASE)
                        if len(w) > 0:
                            words.append(word)
                    if len(words) > 0:
                        fdata.append(r)
        else:
            flash("Cannot process your form: no data", category='error')
    else:
        flash("Form was not properly sent", category='error')
    return render_template('srp.html', idata=fdata, found=len(fdata), form=g.form, 
            items=g.items, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, chapters=g.chapters, title=searchfor)



@app.route('/browse/obj/<codename>')
def browse(codename):
    i_data = DB().get_points_by_codename(codename)
    obj = DB().get_an_object_by_codename(codename)
    objdata = json.loads(dumps(obj))
    return render_template('browse.html', idata=i_data, obj=objdata, form=g.form, 
            items=g.items, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, chapters=g.chapters, title=objdata[0]["I_S_name"])


@app.route('/browse/geo/<geo>')
def browse_geo(geo):
    i_data = DB().get_points_by_geo(geo)
    obj = DB().get_an_object_by_codename(geo)
    objdata = json.loads(dumps(obj))
    return render_template('browse.html', idata=i_data, obj=objdata, form=g.form, 
            items=g.items, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, chapters=g.chapters, title=objdata[0]["I_S_name"])


@app.route('/intro/<namespace>',methods=['GET','POST'])
def show_intro(namespace):
    i_data = DB().get_an_intro(namespace)
    data = json.loads(dumps(i_data))
    print 
    f_date = datetime.datetime.fromtimestamp( data["date"]['$date'] / 1e3 )
    data["date"] = f_date.strftime('%d-%m-%Y %H:%M')
    if 'div' in request.args:
        return jsonify( {'data': render_template('intro_div.html', idata=data, chapters=g.chapters)} )
    else:
        return render_template('intro.html', idata=data, form=g.form, 
            items=g.items, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, chapters=g.chapters, title=data["subject"])


@app.route('/chapters/<namespace>',methods=['GET','POST'])
def chapters(namespace):
    i_data = DB().get_spaces_by_key_sorted(namespace, "date")
    data = json.loads(dumps(i_data))
    for i in range(0, len(data)):
        f_date = datetime.datetime.fromtimestamp( data[i]["date"]['$date'] / 1e3 )
        data[i]["date"] = f_date.strftime('%d-%m-%Y %H:%M')
    if 'div' in request.args:
        return jsonify( {'data': render_template('chapt_div.html', idata=data, chapters=chapters)} )
    else:
        return render_template('chapt.html', idata=data, form=g.form, 
                            items=g.items, geo_objects=g.objects_geo, objects=g.objects, conditions=g.conditions, drugs=g.drugs, title=namespace)


@app.route('/tmpl', methods=['GET', 'POST'])
def tmpl():
    start = datetime.datetime.strptime("2016-11-04 00:00:00", '%Y-%m-%d %H:%M:%S')
    end = datetime.datetime.strptime("2016-11-14 23:59:59", '%Y-%m-%d %H:%M:%S')
    items = DB().get_data(start, end)
    return render_template('tmpl.html', items=items)


@app.errorhandler(404)
def page_not_found(error):
    form = makeform()
    return render_template('404.html', items=g.items, objects=g.objects, form=g.form), 404


@app.errorhandler(500)
def internal_error(error):
    form = makeform()
    return render_template('500.html', items=g.items, objects=g.objects, form=g.form), 500
