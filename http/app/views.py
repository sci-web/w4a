from app import app
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


@app.before_request
def load_vars():
    reader = geoip2.database.Reader(app.config['GEOCITY'])
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    location = "ru"
    ccode = ""
    if (ip != "127.0.0.1"):
        response = reader.city(ip)
        ccode = str(response.country.iso_code)  # country code
    if (ccode == "RU" or ccode == "UA" or ccode == "BY" or ccode == "KZ"):
        g.location = "ru"
    else:
        g.location = "en"
    g.path = request.path.split('/')[1]
    if (g.path == "en"):
        g.location = "en"
    else:
        if (request.referrer == None and g.location != "ru" and g.path != "ru"):
            g.location = "en"
        else:
            g.location = "ru"
    # g.location = request.path.split('/')[1]
    g.items = DB().get_spaces_by_key_sorted_en("vaccines", "date") if g.location == "en" else DB().get_spaces_by_key_sorted("vaccines", "date")
    g.objects = DB().get_objects_by_key_sorted_filter_yes_en("disease", "I_S_name_en") if g.location == "en" else DB().get_objects_by_key_sorted_filter_yes("disease", "I_S_name")
    g.drugs = DB().get_objects_by_key_sorted_filter_yes_en("drug", "I_S_name_en") if g.location == "en" else DB().get_objects_by_key_sorted_filter_yes("drug", "I_S_name")
    g.conditions = DB().get_objects_by_key_sorted_filter_yes_en("condition", "I_S_name_en")  if g.location == "en" else DB().get_objects_by_key_sorted_filter_yes("condition", "I_S_name") 
    g.objects_geo = DB().get_objects_by_key_sorted_filter_yes_en("geo", "I_S_codename") if g.location == "en" else DB().get_objects_by_key_sorted_filter_yes("geo", "I_S_name")
    g.chapters = DB().get_spaces_by_key_sorted_en("vaccines", "date") if g.location == "en" else DB().get_spaces_by_key_sorted("vaccines", "date")
    g.form = makeform()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    try:
        DB().get_intros()
        flash("!")
        return "ok"
    except Exception, e:
        flash(e)
        return redirect(url_for('index'))

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
@app.route('/en')
@app.route('/en/')
@app.route('/ru/')
@app.route('/ru')
def index():
    if (request.referrer == None and g.location == "en" and g.path != "en" and g.path != "ru"):
        return redirect("/en")
    i_data = DB().get_intros_en() if g.location == "en" else DB().get_intros()
    tmpl = 'en/index_en.html' if g.location == "en" else 'index.html'
    return render_template(tmpl, form=g.form, items=g.items, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, 
                    chapters=g.chapters, data=i_data)

@app.route('/en/content/<namespace>/<codename>')
@app.route('/content/<namespace>/<codename>')
def show_item(namespace, codename):
    i_data = DB().get_a_space_en(namespace, codename) if g.location == "en" else DB().get_a_space(namespace, codename)
    data = json.loads(dumps(i_data))
    try:
        title = data["title"]
    except:
        return render_template('en/404_en.html', items=g.items, objects=g.objects, form=g.form), 404  # if there is no corresponding translation      
    chapters = DB().get_spaces_by_key_sorted_en(namespace, "date") if g.location == "en" else DB().get_spaces_by_key_sorted(namespace, "date")

    f_date = datetime.datetime.fromtimestamp( data["date"]['$date'] / 1e3 )
    data["date"] = f_date.strftime('%d-%m-%Y %H:%M')
    tmpl = 'en/content_en.html' if g.location == "en" else 'content.html'
    return render_template(tmpl, idata=data, form=g.form, items=g.items, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, 
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


@app.route('/en/browse/obj/<codename>')
@app.route('/browse/obj/<codename>')
def browse(codename):
    i_data = DB().get_points_by_codename_en(codename) if g.location == "en" else DB().get_points_by_codename(codename)
    obj = DB().get_an_object_by_codename_en(codename) if g.location == "en" else DB().get_an_object_by_codename(codename)
    objdata = json.loads(dumps(obj))
    tmpl = 'en/browse_en.html' if g.location == "en" else 'browse.html'
    title = objdata[0]["I_S_name_en"] if g.location == "en" else objdata[0]["I_S_name"]
    return render_template(tmpl, idata=i_data, obj=objdata, form=g.form, 
            items=g.items, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, chapters=g.chapters, title=title)


@app.route('/en/browse/geo/<geo>')
@app.route('/browse/geo/<geo>')
def browse_geo(geo):
    i_data = DB().get_points_by_geo_en(geo) if g.location == "en" else DB().get_points_by_geo(geo)
    obj = DB().get_an_object_by_codename_en(geo) if g.location == "en" else DB().get_an_object_by_codename(geo)
    objdata = json.loads(dumps(obj))
    tmpl = 'en/browse_en.html' if g.location == "en" else 'browse.html'
    title = objdata[0]["I_S_codename"] if g.location == "en" else objdata[0]["I_S_name"]
    return render_template(tmpl, idata=i_data, obj=objdata, form=g.form, 
            items=g.items, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, chapters=g.chapters, title=title)


@app.route('/en/intro/<namespace>',methods=['GET','POST'])
@app.route('/intro/<namespace>',methods=['GET','POST'])
def show_intro(namespace):
    i_data = DB().get_an_intro_en(namespace) if g.location == "en" else DB().get_an_intro(namespace)
    data = json.loads(dumps(i_data))
    f_date = datetime.datetime.fromtimestamp( data["date"]['$date'] / 1e3 )
    data["date"] = f_date.strftime('%d-%m-%Y %H:%M')
    tmpl = 'en/intro_en.html' if g.location == "en" else 'intro.html'
    div = 'en/intro_div_en.html' if g.location == "en" else 'intro_div.html'
    if 'div' in request.args:
        return jsonify( {'data': render_template(div, idata=data, chapters=g.chapters)} )
    else:
        return render_template(tmpl, idata=data, form=g.form, 
            items=g.items, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, chapters=g.chapters, title=data["subject"])


@app.route('/en/chapters/<namespace>',methods=['GET','POST'])
@app.route('/chapters/<namespace>',methods=['GET','POST'])
def chapters(namespace):
    i_data = DB().get_spaces_by_key_sorted_en(namespace, "date") if g.location == "en" else DB().get_spaces_by_key_sorted(namespace, "date")
    data = json.loads(dumps(i_data))
    tmpl = 'en/chapt_en.html' if g.location == "en" else 'chapt.html'
    div = 'en/chapt_div_en.html' if g.location == "en" else 'chapt_div.html'    
    for i in range(0, len(data)):
        f_date = datetime.datetime.fromtimestamp( data[i]["date"]['$date'] / 1e3 )
        data[i]["date"] = f_date.strftime('%d-%m-%Y %H:%M')
    if 'div' in request.args:
        return jsonify( {'data': render_template(div, idata=data, chapters=chapters)} )
    else:
        return render_template(tmpl, idata=data, form=g.form, 
                            items=g.items, geo_objects=g.objects_geo, objects=g.objects, conditions=g.conditions, drugs=g.drugs, title=namespace)

@app.route('/en/contact/', methods=['GET', 'POST'])
@app.route('/contact/', methods=['GET', 'POST'])
def send_email():
    captcha = FlaskSessionCaptcha(app)    
    cform = ContactForm(request.values)
    tmpl = 'en/contact_en.html' if g.location == "en" else 'contact.html'
    reply = 'en/autoreply_en.html' if g.location == "en" else 'autoreply.html'
    if request.method == 'POST':
        if cform.validate_on_submit():
            if captcha.validate():
                mail = Mail(app)
                msg = Message(">>> message from SciBook: " + cform.data["subject"],
                    sender=cform.data["email"],
                    recipients=[app.config["EMAILS"]])
                msg.body = cform.data["msg"] + "\n\n" + "signed as from:\n" + cform.data["email"]
                mail.send(msg)
                flash("Your message is sent!", category='info')
                return render_template(reply, form=g.form, cform=cform)

            else:
                flash("Captcha is wrong!", category='error')
                return render_template(tmpl, form=g.form, cform=cform, email=cform.data["email"], subject=cform.data["subject"], msg=cform.data["msg"])
        else:
            flash("All fields are necessary to fill in!", category='error')
            return render_template(tmpl, form=g.form, cform=cform, email=cform.data["email"], subject=cform.data["subject"], msg=cform.data["msg"])
    else:
        return render_template(tmpl, form=g.form, cform=cform)


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
