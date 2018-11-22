from scibook import app
import re
from flask import request, redirect, render_template, url_for, flash, Response, g, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import date
import datetime
from flask_admin.model import typefmt
import os
from .model import DB
from .forms import LoginForm, makeform, searchForm, ContactForm
from bson.json_util import dumps
import json
import geoip2.database
from flask_mail import Mail, Message
from flask_session_captcha import FlaskSessionCaptcha
from itertools import chain
from copy import deepcopy


# @app.errorhandler(Exception)
# def exception_handler(error):
#     return render_template('en/404_en.html', items=g.items, navitems=g.navitems, objects=g.objects, form=g.form), 404


@app.before_request
def load_vars():
    if app.config['DB'] == None:
        print "No vars to load: ", e
        return render_template('500.html'), 500
    reader = geoip2.database.Reader(app.config['GEOCITY'])
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    location = "ru"
    ccode = "RU"
    # if (ip != "127.0.0.1"):
    #     response = reader.city(ip)
    #     ccode = str(response.country.iso_code)  # country code
    # if (ccode == "RU" or ccode == "UA" or ccode == "BY" or ccode == "KZ"):
    #     g.location = "ru"
    # else:
    #     g.location = "en"
    g.path = request.path.split('/')[1]
    # if (g.path == "en"):
    #     g.location = "en"
    # else:
    #     if (request.referrer == None and g.location != "ru" and g.path != "ru"):
    #         g.location = "en"
    #     else:
    #         g.location = "ru"
    locations = ["en", "he"]
    g.location = request.path.split('/')[1]
    if g.location in locations:
        g.location = g.location
    elif request.host.split(".")[0] in locations:
        g.location = request.host.split(".")[0]
    else:
        g.location = "ru"
    # print "location:", g.location
    g.namespace = "vaccines"
    g.items = list(DB(g.location).get_spaces_by_key_sorted(g.namespace, "date"))
    g.navitems = g.items[:]
    g.objects = DB(g.location).get_objects_by_key_sorted_filter_yes("disease", "I_S_codename", g.namespace)
    g.drugs = DB(g.location).get_objects_by_key_sorted_filter_yes("drug", "I_S_codename", g.namespace)
    g.conditions = DB(g.location).get_objects_by_key_sorted_filter_yes("condition", "I_S_codename", g.namespace)
    g.objects_geo = DB(g.location).get_objects_by_key_sorted_filter_yes("geo", "I_S_codename", g.namespace)
    # g.chapters = DB(g.location).get_spaces_by_key_sorted(request.path.split('/')[2], "date")
    g.chapters = DB(g.location).get_spaces_by_key_sorted(g.namespace, "date")
    g.form = makeform()


def tmpl_picker(name):
    if g.location == "en":
        return 'en/' + name + '_en.html'
    elif g.location == "he":
        return 'he/' + name + '_he.html'
    else:
        return name + '.html'


@app.errorhandler(404)
def page_not_found(error):
    form = makeform()
    tmpl = tmpl_picker('404')
    return render_template(tmpl, items=g.items, navitems=g.navitems, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, form=g.form), 404  # if there is no corresponding translation


@app.errorhandler(500)
def internal_server_error(error):
    # useless: not working if no DB connection, 500 is handled by apache in production mode anyway
    return render_template('500.html'), 500


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
@app.route('/en', strict_slashes=False)
@app.route('/en/')
@app.route('/he', strict_slashes=False)
@app.route('/he/')
def index():
    if (request.referrer == None and g.location == "en" and g.path != "en" and g.path != "ru"):
        return redirect("/en")

    i_data = DB(g.location).get_intros()
    tmpl = tmpl_picker('index')
    return render_template(tmpl, form=g.form, items=g.items, navitems=g.navitems, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo,
                    chapters=g.chapters, data=i_data)
    # return render_template('500.html'), 500

@app.route('/en/content/<namespace>/<codename>')
@app.route('/he/content/<namespace>/<codename>')
@app.route('/content/<namespace>/<codename>')
def show_item(namespace, codename):
    i_data = DB(g.location).get_a_space(namespace, codename)
    data = json.loads(dumps(i_data))
    try:
        title = data["title"]
        space = data["I_S_namespace"].title()
    except:
        tmpl = tmpl_picker('404')
        return render_template(tmpl, items=g.items, navitems=g.navitems, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, form=g.form), 404  # if there is no corresponding translation
    chapters = DB(g.location).get_spaces_by_key_sorted(namespace, "date")
    f_date = datetime.datetime.fromtimestamp( data["date"]['$date'] / 1e3 )
    data["date"] = f_date.strftime('%d-%m-%Y %H:%M')
    if data["translated"] == 1:
        tmpl = tmpl_picker('content')
    else:
        tmpl = tmpl_picker('to_translate')
    return render_template(tmpl, idata=data, form=g.form, items=g.items, navitems=g.navitems, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, 
                            title=namespace.title() + " / " + space + ": " + title, chapters=chapters)
    # return render_template(tmpl, idata=data, form=g.form, items=g.items, navitems=g.navitems, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo,
    #                         title=space + " / " + namespace.title() + ": " + title, chapters=chapters)


@app.route('/search', methods=['GET','POST'])
@app.route('/en/search', methods=['GET','POST'])
@app.route('/he/search', methods=['GET','POST'])
def search():
    i_data = {}
    searchfor = ""
    sform = searchForm(request.values)
    fdata = []  # filtered data
    items = {}
    if request.method == 'POST':
        if sform.data["search"]:
            searchfor = sform.data["search"]
            i_data = DB(g.location).search(searchfor)
            idata = json.loads(dumps(i_data))
            # items = [x for x in chain(items, idata)]
            for r in idata:
                m_regex = r'\[.*?\=\=.*?\]'
                # print r[0]
                txt = r["points"]["digest"]
                fnd_link = re.findall(m_regex, txt, re.IGNORECASE)
                fdata.append(r)
        else:
            flash("Cannot process your form: no data", category='error')
    else:
        flash("Form was not properly sent", category='error')
    tmpl = tmpl_picker('srp')
    return render_template(tmpl, idata=fdata, found=len(fdata), form=g.form,
            items=g.items, navitems=g.navitems, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, chapters=g.chapters, title=searchfor)

@app.route('/en/browse/obj/<namespace>:<codename>')
@app.route('/he/browse/obj/<namespace>:<codename>')
@app.route('/browse/obj/<namespace>:<codename>')
def browse(codename, namespace):
    i_data = DB(g.location).get_points_by_codename(codename, namespace)
    obj = DB(g.location).get_an_object_by_codename(codename, namespace)
    objdata = json.loads(dumps(obj))
    tmpl = tmpl_picker('browse')
    fld = "I_S_name" if g.location == "ru" else "I_S_name_" + g.location
    try:
        title = objdata[0][fld]
    except:
        title = "no data found"
    return render_template(tmpl, idata=i_data, obj=objdata, form=g.form,
            items=g.items, navitems=g.navitems, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, chapters=g.chapters, title=title)


@app.route('/en/browse/geo/<namespace>:<geo>')
@app.route('/browse/geo/<namespace>:<geo>')
def browse_geo(geo, namespace):
    i_data = DB(g.location).get_points_by_geo(geo, namespace)
    obj = DB(g.location).get_an_object_by_codename(geo, namespace)

    objdata = json.loads(dumps(obj))
    tmpl = tmpl_picker('browse')
    fld = "I_S_name" if g.location == "ru" else "I_S_name_" + g.location
    try:
        title = objdata[0][fld]
    except:
        title = "no data found"
    return render_template(tmpl, idata=i_data, obj=objdata, form=g.form,
            items=g.items, navitems=g.navitems, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, chapters=g.chapters, title=title)


@app.route('/en/intro/<namespace>',methods=['GET','POST'])
@app.route('/he/intro/<namespace>',methods=['GET','POST'])
@app.route('/intro/<namespace>',methods=['GET','POST'])
def show_intro(namespace):
    i_data = DB(g.location).get_an_intro(namespace)
    data = json.loads(dumps(i_data))
    f_date = datetime.datetime.fromtimestamp( data["date"]['$date'] / 1e3 )
    data["date"] = f_date.strftime('%d-%m-%Y %H:%M')
    tmpl = tmpl_picker('intro')
    div = tmpl_picker('intro_div')
    g.chapters = DB(g.location).get_spaces_by_key_sorted(g.namespace, "date")
    if 'div' in request.args:
        return jsonify( {'data': render_template(div, idata=data, chapters=g.chapters)} )
    else:
        return render_template(tmpl, idata=data, form=g.form,
            items=g.items, navitems=g.navitems, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, chapters=g.chapters, title=data["subject"])


@app.route('/en/chapters/<namespace>',methods=['GET','POST'])
@app.route('/he/chapters/<namespace>',methods=['GET','POST'])
@app.route('/chapters/<namespace>',methods=['GET','POST'])
def chapters(namespace):
    i_data = DB(g.location).get_spaces_by_key_sorted(namespace, "date")
    data = json.loads(dumps(i_data))
    tmpl = tmpl_picker('chapt')
    div = tmpl_picker('chapt_div')
    for i in range(0, len(data)):
        f_date = datetime.datetime.fromtimestamp( data[i]["date"]['$date'] / 1e3 )
        data[i]["date"] = f_date.strftime('%d-%m-%Y %H:%M')
    space = data[0]["namespace"].title() if g.location == "en" else data[0]["I_S_namespace"]
    if 'div' in request.args:
        return jsonify( {'data': render_template(div, idata=data, chapters=chapters)} )
    else:
        return render_template(tmpl, idata=data, form=g.form,
                            items=g.items, navitems=g.navitems, geo_objects=g.objects_geo, objects=g.objects, conditions=g.conditions, drugs=g.drugs, title=space + " / " + namespace.title())

@app.route('/en/contact/', methods=['GET', 'POST'])
@app.route('/he/contact/', methods=['GET', 'POST'])
@app.route('/contact/', methods=['GET', 'POST'])
def send_email():
    captcha = FlaskSessionCaptcha(app)
    cform = ContactForm(request.values)
    tmpl = tmpl_picker('contact')
    reply = tmpl_picker('autoreply')
    if request.method == 'POST':
        if cform.validate_on_submit():
            if captcha.validate():
                try:
                    mail = Mail(app)
                    msg = Message(">>> message from SciBook: " + cform.data["subject"],
                        sender=cform.data["email"],
                        recipients=[app.config["EMAIL_1"]])
                    msg.add_recipient(app.config["EMAIL_2"])
                    msg.body = cform.data["msg"] + "\n\n" + "signed as from:\n" + cform.data["email"]
                    mail.send(msg)
                    flash("Your message is sent!", category='info')
                    return render_template(reply, form=g.form, cform=cform)
                except:
                    flash("Your message is not sent fast way... Something went wrong, we are soory, but we look at your message a bit later", category='error')
                    return render_template(reply, form=g.form, cform=cform)
            else:
                flash("Captcha is wrong!", category='error')
                return render_template(tmpl, form=g.form, cform=cform, email=cform.data["email"], subject=cform.data["subject"], msg=cform.data["msg"])
        else:
            flash("All fields are necessary to fill in!", category='error')
            return render_template(tmpl, form=g.form, cform=cform, email=cform.data["email"], subject=cform.data["subject"], msg=cform.data["msg"])
    else:
        return render_template(tmpl, form=g.form, cform=cform)
