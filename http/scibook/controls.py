from scibook import app, lm
import re
from datetime import datetime
# import xlrd
from flask import request, redirect, render_template, flash, Response, send_from_directory, url_for, g, jsonify, make_response
from flask_login import login_user, logout_user, login_required, current_user
from .auth import Auth
from .model import DB
from .forms import saveIntro, newIntro, saveChapter, newChapter
from bson.json_util import dumps
import json
from subprocess import call
from collections import defaultdict, OrderedDict
from .tools import Tools
from tidylib import tidy_fragment
from views import tmpl_picker, load_vars
from flask import Markup
# def extension_ok(filename, ff):
#     """ return whether file's extension is ok or not"""
#     return '.' in filename and \
#            filename.rsplit('.', 1)[1] in app.config[ff]


def packed(val_dict):
    # vls = ", ".join(['{}={}'.format(k, v) for k, v in val_dict.iteritems()])
    ll = []
    for k, v in val_dict.iteritems():
        exec(k + " = v")
        ll.append(k)
    return ll


def check_html(text):
    document, err = tidy_fragment(text,options={'numeric-entities':1})
    for l in err.split("\n"):
        if (re.search("missing </",l)):
            return 0
    return 1


@app.route('/login/', methods=['GET', 'POST'])
def login():
    url = g.form.from_url.data
    if url is not None and url != "/" and url != "":
        url = str(url.strip("/"))
        return redirect(url)
    else:
        return redirect("/")


@app.route('/logout/')
@app.route('/en/logout/')
def logout():
    logout_user()
    return redirect("/")


@lm.user_loader
def load_user(email):
    u = DB('').get_a_user(email)
    if not u:
        return None
    return Auth(u['email'], u['access'], u['author'])


@app.route('/profile/<author>')
@app.route('/en/profile/<author>')
@app.route('/he/profile/<author>')
@login_required
def profile(author):
    tmpl = tmpl_picker('profile')
    return render_template(tmpl, form=g.form, items=g.items)


@app.route('/editspace/<author>')
@app.route('/en/editspace/<author>')
@app.route('/he/editspace/<author>')
@login_required
def editspace(author):
    namespaces = DB(g.location).get_intros_by_author(author)
    spaces = DB(g.location).get_spaces_by_author(author)
    data = json.loads(dumps(spaces))
    chapters = defaultdict(list)
    for d in range(0, len(data)):
        ns = data[d]["namespace"]
        c_date = datetime.fromtimestamp( data[d]["date"]['$date'] / 1e3 ).strftime('%d-%m-%Y %H:%M')
        try:
            e_date = datetime.fromtimestamp( data[d]["editdate"]['$date'] / 1e3 ).strftime('%d-%m-%Y %H:%M')
        except:
            e_date = ""
        ch = data[d]["title"] + "|" + data[d]["I_S_codename"] + "|" + c_date + "|" + e_date
        chapters[ns].append(ch)
    tmpl = tmpl_picker('cms_start')
    return render_template(tmpl, form=g.form, items=g.items, author=author, namespaces=namespaces, chapters=chapters)


@app.route('/editspace/intro:<author>:<namespace>', methods=['GET', 'POST'])
@app.route('/en/editspace/intro:<author>:<namespace>', methods=['GET', 'POST'])
@app.route('/he/editspace/intro:<author>:<namespace>', methods=['GET', 'POST'])
@login_required
def edit_intro(author, namespace):
    if namespace == "0":
        tmpl = tmpl_picker('form_intro')
        return render_template(tmpl, form=g.form)
    else:
        i_data = DB(g.location).get_an_intro(namespace)
        namespaces = {}
        for l in i_data["langs"]:
            if l != "en":
                namespaces[l] = i_data["namespace_" + l]
        tmpl = tmpl_picker('form_intro_edit')
        return render_template(tmpl, form=g.form, items=i_data, namespaces=namespaces)


def value_match_assign(match, field, key, value, dhash):
    if (match == "pointHidden" and re.match(match, key)):
        # print key, value
        value = int(value)
    if (re.match(match, key) and value != ""):
        p, r = key.split("_")
        if (value != ""):
            try:
                dhash[r].update({field: value})
            except:
                dhash[r] = {field: value}
    return dhash

def nest_value_match_assign(match, field, key, value, dhash):
    if (re.match(match, key) and value != ""):
        p, l, r = key.split("_")
        if (value != ""):
            try:
                dhash[r][l].update({field: value})
            except:
                try:
                    dhash[r].update({l : {field: value}})
                except:
                    dhash[r] = ({l : {field: value}})
    return dhash


@app.route('/editspace/save_intro:<author>:<namespace>', methods=['GET', 'POST'])
@app.route('/en/editspace/save_intro:<author>:<namespace>', methods=['GET', 'POST'])
@app.route('/he/editspace/save_intro:<author>:<namespace>', methods=['GET', 'POST'])
@login_required
def save_intro(author, namespace):
    i_data = {}
    if namespace == "0":
        sform = newIntro(request.values)
    else:
        sform = saveIntro(request.values)
        i_data = DB(g.location).get_an_intro(namespace)  # before update/insert
    in_data = {}
    in_data["points"] = []
    in_data["refs"] = []
    error = 0
    new_namespace = ""
    try:
        langs = i_data["langs"]
    except:
        langs = ["ru", "en"]
    print langs
    # {{ form.hidden_tag() }} must be in template for sform.validate_on_submit() True if fields are ok
    if request.form and Auth.is_authenticated and (current_user.author == author or current_user.access > 1):
        if sform.data:
            f = request.form
            points = {}
            codenames = {}
            acronyms = {}
            refs = []
            in_refs = {}
            in_refs_pool = {}
            ep_text = ""
            ep_source = ""
            for key in f.keys():
                for value in f.getlist(key):
                    # print key,":",value
                    if key == "namespace" and namespace == "0":
                        in_data["namespace"] = value
                        i_data = DB(g.location).get_an_intro(in_data["namespace"])  # before update/insert
                        if i_data and namespace == 0:
                            error = "This namespace:" + in_data["namespace"] + " already exists!"
                            break
                        else:
                            new_namespace = in_data["namespace"]
                    if key == "subject": in_data["subject"] = value
                    if (key == "intro" and value != ""): in_data["intro"] = value
                    if (key == "ref_intro" and value != ""): in_data["ref_intro"] = value
                    if (key == "ref_header" and value != ""): in_data["ref_header"] = value
                    if (key == "summary" and value != ""): in_data["summary"] = value
                    if key == "ep_text": ep_text = value
                    if key == "ep_source": ep_source = value
                    if (re.match("points", key) and value != ""):
                        p, k = key.split("_")
                        points[k] = value
                    if (re.match("namespace_", key) and value != ""):
                        p, k = key.split("_")
                        print p,k,value
                        try:
                            dg = int(k)
                            codenames[k] = value
                        except:
                            dg = "xx"
                        if k != dg:
                            in_data[key] = value
                    if (re.match("acronym_", key) and value != ""):
                        p, k = key.split("_")
                        langs.append(value)
                        acronyms[k] = value

                    in_refs = value_match_assign("refBlockTtl", "ref_title", key, value, in_refs)
                    in_refs = value_match_assign("refBlockDigest", "ref_digest", key, value, in_refs)
                    in_refs = value_match_assign("refBlockType", "ref_type", key, value, in_refs)
                    in_refs_pool = nest_value_match_assign("linkTitle", "title", key, value, in_refs_pool)
                    in_refs_pool = nest_value_match_assign("linkURL", "link", key, value, in_refs_pool)
                    in_refs_pool = nest_value_match_assign("linkType", "linktype", key, value, in_refs_pool)
                    in_refs_pool = nest_value_match_assign("linkDigest", "digest", key, value, in_refs_pool)
                    in_refs_pool = nest_value_match_assign("linkAuthor", "author", key, value, in_refs_pool)
            if error == 0:
                for r in in_refs.keys():
                    ref_pool = []
                    for l in in_refs_pool[r].keys():
                        # print l, in_refs_pool[r][l]
                        try:
                            ref_pool.append(in_refs_pool[r][l])
                        except:
                            if len(in_refs_pool[r][l]) > 0:
                                ref_pool = in_refs_pool[r][l]
                    try:
                        in_refs[r].update({"ref_pool": ref_pool})
                    except:
                        in_refs[r] = {"ref_pool": ref_pool}

                for n, p in sorted(points.iteritems(), key=lambda x: float(x[0])):
                    in_data["points"].append({"num": float(n), "item": p})

                for n, rf in sorted(in_refs.iteritems()):
                    try:
                        refs.append(in_refs[n])
                    except:
                        if (len(in_refs[n])) > 0:
                            refs = in_refs[n]
                in_data["refs"] = refs

                if ep_text != "": in_data["epigraph"] = {"text": ep_text, "source": ep_source}
                in_data["langs"] = langs
                for k, v in codenames.iteritems():
                    in_data["namespace_" + acronyms[k]] = codenames[k]

                if namespace == "0":
                    in_data["date"] = datetime.now()
                    in_data["analyst"] = author
                    DB(g.location).insert_an_intro(in_data)
                else:
                    DB(g.location).update_an_intro(author, namespace, in_data)
            else:
                flash(error, category='error')
        else:
            error = "Something wrong with data update!"
        if error == 0:
            flash("Data updated successfully!", category='info')
        else:
            flash(error, category='error')
    else:
        error = "Something wrong with the form or authentification!"
        flash(error, category='error')
    if namespace != "0":
        i_data = DB(g.location).get_an_intro(namespace) # after update/insert
        tmpl = tmpl_picker('form_intro_edit')
        namespaces = {}
        for l in i_data["langs"]:
            if l != "en":
                namespaces[l] = i_data["namespace_" + l]
        return render_template(tmpl, form=g.form, items=i_data, namespaces=namespaces)
    else:
        if error == 0:
            if g.location == "en":
                return redirect("/en/editspace/intro:" + author + ":" + new_namespace + "")
            else:
                return redirect("/editspace/intro:" + author + ":" + new_namespace + "")
        else:
            i_data = in_data
            itmpl = tmpl_picker('form_intro')
            return render_template(itmpl, form=g.form, items=i_data)


@app.route('/editspace/chapter:<author>:<namespace>:<chapter>', methods=['GET', 'POST'])
@app.route('/en/editspace/chapter:<author>:<namespace>:<chapter>', methods=['GET', 'POST'])
@app.route('/he/editspace/chapter:<author>:<namespace>:<chapter>', methods=['GET', 'POST'])
@login_required
def edit_chapter(author, namespace, chapter):
    if chapter == "0":
        tmpl = tmpl_picker('form_chapter')
        return render_template(tmpl, form=g.form, namespace=namespace)
    else:
        i_data = DB(g.location).get_a_chapter(namespace, chapter)
        itmpl = tmpl_picker('form_chapter_edit')
        return render_template(itmpl, form=g.form, items=i_data, namespace=namespace, chapter=chapter)



@app.route('/editspace/save_chapter:<author>:<namespace>:<chapter>', methods=['GET', 'POST'])
@app.route('/en/editspace/save_chapter:<author>:<namespace>:<chapter>', methods=['GET', 'POST'])
@app.route('/he/editspace/save_chapter:<author>:<namespace>:<chapter>', methods=['GET', 'POST'])
@login_required
def save_chapter(author, namespace, chapter):
    if chapter == "0":
        sform = newChapter(request.values)
    else:
        sform = saveChapter(request.values)
    in_data = {}
    if chapter == 0:
        in_data["date"] = datetime.now()
        in_data["editdate"] = ""
    else:
        in_data["editdate"] = datetime.now()
    in_data["points"] = []
    if request.form and Auth.is_authenticated and (current_user.author == author or current_user.access > 1):
        f_msg = ""
        if sform.data:
            f = request.form
            points = {}
            in_pnts = {}
            in_imgs_pool = {}
            in_sources_pool = {}
            ep_text = ""
            ep_source = ""
            error = 0
            in_data["translated"] = 0
            for key in f.keys():
                for value in f.getlist(key):
                    value = value.replace("\r\n","<br>")
                    value = value.replace("\n","<br>")
                    if key == "chapter" and chapter == "0":
                        in_data["analyst"] = author
                        in_data["date"] = datetime.now()
                        in_data["namespace"] = namespace
                        in_data["I_S_codename"] = value
                        i_data = DB(g.location).get_a_chapter(namespace, value)  # before update/insert
                        if i_data and chapter == 0:
                            error = "This chapter:" + in_data["I_S_codename"] + " already exists!"
                            break
                        else:
                            new_chapter = in_data["I_S_codename"]
                    if key == "I_S_namespace":
                        in_data["I_S_namespace"] = value
                    if key == "title":
                        in_data["I_S_name"] = value
                        in_data["title"] = value
                    if key == "translated" and value != "":
                        in_data["translated"] = 1
                    if (key == "intro" and value != ""): in_data["intro"] = value
                    if (key == "interpreter" and value != ""): in_data["interpreter"] = value
                    if (key == "interpreter_link" and value != ""): in_data["interpreter_link"] = value
                    if (key == "summary" and value != ""): in_data["summary"] = value
                    if key == "ep_text": ep_text = value
                    if key == "ep_source": ep_source = value
                    if (re.match("point", key) and value != ""):
                        p, k = key.split("_")
                        points[k] = value
                    if key == "I_S_codename" and value.isalpha():
                        in_data["I_S_codename"] = value
                    in_pnts = value_match_assign("pointHeader", "header", key, value, in_pnts)
                    in_pnts = value_match_assign("pointTitle", "title", key, value, in_pnts)
                    in_pnts = value_match_assign("pointLink", "link", key, value, in_pnts)
                    in_pnts = value_match_assign("pointType", "info_type", key, value, in_pnts)
                    in_pnts = value_match_assign("pointPID", "infoID", key, value, in_pnts)
                    in_pnts = value_match_assign("pointPdate", "info_date", key, value, in_pnts)
                    in_pnts = value_match_assign("pointPauths", "info_authors", key, value, in_pnts)
                    in_pnts = value_match_assign("pointPub", "info_place", key, value, in_pnts)
                    in_pnts = value_match_assign("pointGeo", "info_geo", key, value, in_pnts)
                    in_pnts = value_match_assign("pointImage", "info_img", key, value, in_pnts)
                    in_pnts = value_match_assign("pointIsource", "info_imgSource", key, value, in_pnts)
                    in_pnts = value_match_assign("pointIdescr", "info_imgDescr", key, value, in_pnts)
                    in_pnts = value_match_assign("pointDigest", "digest", key, value, in_pnts)
                    in_pnts = value_match_assign("pointNewID", "num", key, value, in_pnts)
                    in_pnts = value_match_assign("pointHidden", "is_hidden", key, value, in_pnts)
                    if (re.match("pointTags", key) and value != ""):
                        p, r = key.split("_")
                        if (value != ""):
                            lst = value.split(",")
                            c_lst = []
                            for e in lst:
                                c = e.replace(" ", "")
                                c_lst.append(c)
                            try:
                                in_pnts[r].update({"I_S_codenames": c_lst})
                            except:
                                in_pnts[r] = {"I_S_codenames": c_lst}
                    if (re.match("pointGeo", key) and value != ""):
                        p, r = key.split("_")
                        if (value != ""):
                            lst = value.split(",")
                            c_lst = []
                            for e in lst:
                                c = e.replace(" ", "")
                                c_lst.append(c)
                            try:
                                in_pnts[r].update({"info_geo": c_lst})
                            except:
                                in_pnts[r] = {"info_geo": c_lst}

                    in_imgs_pool = nest_value_match_assign("imgDescr", "info_imgDesc", key, value, in_imgs_pool)
                    in_imgs_pool = nest_value_match_assign("imgLink", "info_img", key, value, in_imgs_pool)
                    in_imgs_pool = nest_value_match_assign("imgSrcURL", "info_imgSource", key, value, in_imgs_pool)
                    in_imgs_pool = nest_value_match_assign("imgSrcTitle", "info_imgTitle", key, value, in_imgs_pool)

                    in_sources_pool = nest_value_match_assign("srcTitle", "title", key, value, in_sources_pool)
                    in_sources_pool = nest_value_match_assign("srcLink", "link", key, value, in_sources_pool)
                    in_sources_pool = nest_value_match_assign("srcID", "infoID", key, value, in_sources_pool)
                    in_sources_pool = nest_value_match_assign("srcDate", "info_date", key, value, in_sources_pool)
                    in_sources_pool = nest_value_match_assign("srcAuth", "info_authors", key, value, in_sources_pool)
                    in_sources_pool = nest_value_match_assign("srcPlace", "info_place", key, value, in_sources_pool)
                    in_sources_pool = nest_value_match_assign("srcType", "info_type", key, value, in_sources_pool)
            all_tags = set()
            if error == 0:
                for r in in_pnts.keys():
                    try:
                        for ct in in_pnts[r]["I_S_codenames"].split(","):
                            cn = ct.replace(" ", "")
                            all_tags.update(cn)
                    except:
                        pass
                    try:
                        # print in_pnts[r]["info_geo"]
                        for t in in_pnts[r]["info_geo"].split(","):
                            n = t.replace(" ", "")
                            all_tags.update(n)
                        # all_tags.update(in_pnts[r]["info_geo"])
                    except:
                        pass
                    imgs_pool = []
                    is_i_pool = 1
                    try:
                        in_imgs_pool[r].keys()
                    except:
                        is_i_pool = 0
                    if is_i_pool == 1:
                        for l in in_imgs_pool[r].keys():
                            try:
                                in_imgs_pool[r][l].update({"num": float(l)})
                                imgs_pool.append(in_imgs_pool[r][l])
                            except:
                                if len(in_imgs_pool[r][l]) > 0:
                                    in_imgs_pool[r][l].update({"num": float(l)})
                                    imgs_pool = in_imgs_pool[r][l]
                        try:
                            in_pnts[r].update({"img_pool": imgs_pool})
                        except:
                            in_pnts[r] = {"img_pool": imgs_pool}

                    src_pool= []
                    is_s_pool = 1
                    try:
                        in_sources_pool[r].keys()
                    except:
                        is_s_pool = 0
                    if is_s_pool == 1:
                        for l in in_sources_pool[r].keys():
                            try:
                                in_sources_pool[r][l].update({"num": float(l)})
                                src_pool.append(in_sources_pool[r][l])
                            except:
                                if len(in_imgs_pool[r][l]) > 0:
                                    in_sources_pool[r][l].update({"num": float(l)})
                                    src_pool = in_sources_pool[r][l]
                        try:
                            in_pnts[r].update({"sources_pool": src_pool})
                        except:
                            in_pnts[r] = {"sources_pool": src_pool}

                for n, p in sorted(in_pnts.iteritems(), key=lambda x: float(x[0])):
# https://dzone.com/articles/pymongo-and-key-order
                    try:
                        p["num"] = float(p["num"])
                    except:
                        p.update({"num": float(n)})
                    in_data["points"].append(p)

                if ep_text != "": in_data["epigraph"] = {"text": ep_text, "source": ep_source}
                for tag in all_tags:
                    # print tag
                    o = DB(g.location).get_an_object_by_codename(tag, namespace)
                    # print tag, list(o)
                    if len(list(o)) == 0:
                        DB(g.location).insert_an_object({"I_S_codename": tag, "I_S_type_this": "", "I_S_type": "", "I_S_name": "", "namespace" : [namespace] })
                        f_msg = f_msg + "<small><b>" + tag + "</b> is a new tag! <br>Mind to <a style='color:blue' href=https://www.scibook.org/editspace/tags:" + author + ":0> edit the tag list</a>!</small><br>"
                if chapter == "0":
                    intro = DB(g.location).get_an_intro(namespace)
                    j_intro = json.loads(dumps(intro))
                    for l in j_intro["langs"]:
                        if l == g.location:
                            if l != "en":
                                I_S = "namespace_" + l
                            else:
                                I_S = "namespace"
                            in_data["I_S_namespace"] = j_intro[I_S].capitalize()
                    DB(g.location).insert_a_chapter(in_data)
                else:
                    DB(g.location).update_a_chapter(author, namespace, chapter, in_data)
            else:
                flash(error, category='error')
            # print all_tags
        else:
            error = "Something wrong with data update!"
        if error == 0:
            flash(Markup("<div align=left>" + f_msg + "Data updated successfully!</div>"), category='info')
        else:
            flash(error, category='error')
    else:
        error = "Something wrong with a form or authentification!"
        flash(error, category='error')
    if chapter != "0":
        i_data = DB(g.location).get_a_chapter(namespace, chapter) # after update/insert
        tmpl = tmpl_picker('form_chapter_edit')
        return render_template(tmpl, form=g.form, items=i_data)
    else:
        if error == 0:
            if g.location == "en":
                return redirect("/en/editspace/chapter:" + author + ":" + namespace + ":" + new_chapter)
            else:
                return redirect("/editspace/chapter:" + author + ":" + namespace + ":" + new_chapter)
        else:
            i_data = in_data
            tmpl = tmpl_picker('form_chapter')
            return render_template(tmpl, form=g.form, items=i_data, namespace=namespace)


def chapters_for_tags(data):
    chapters = {}
    for d in range(0, len(data)):
        arr = data[d]["points"]
        points = []
        for el in range(0, len(arr)):
            try:
                if len(arr[el]["I_S_codenames"]) > 0:
                    points.append(str(int(arr[el]["num"])))
                    for nm in arr[el]["I_S_codenames"]:
                        try:
                            chapters[nm].update({
                                d: { 'I_S_codename' : data[d]["I_S_codename"], 'points' : ", ".join(points), 'title': data[d]["title"] },
                                })

                        except:
                            chapters[nm] = {
                                d: { 'I_S_codename' : data[d]["I_S_codename"], 'points' : ", ".join(points), 'title': data[d]["title"]},
                                }
            except:
                pass
    return chapters


@app.route('/editspace/tags:<author>:<namespace>:<action>', methods=['GET', 'POST'])
@app.route('/en/editspace/tags:<author>:<namespace>:<action>', methods=['GET', 'POST'])
@app.route('/he/editspace/tags:<author>:<namespace>:<action>', methods=['GET', 'POST'])
@login_required
def edit_tags(namespace, author, action):
    itmpl = tmpl_picker('form_tags')
    new_objects = DB(g.location).get_objects_by_key_sorted_filter_yes("", "I_S_codename", namespace)
    spaces = DB(g.location).get_spaces_by_author_ns(author, namespace)
    data = json.loads(dumps(spaces))
    chapters = chapters_for_tags(data)

    return render_template(itmpl, form=g.form, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, new_objects=new_objects, namespace=namespace, chapters=chapters)


@app.route('/editspace/save_tags:<author>:<namespace>:<action>', methods=['GET', 'POST'])
@app.route('/en/editspace/save_tags:<author>:<namespace>:<action>', methods=['GET', 'POST'])
@app.route('/he/editspace/save_tags:<author>:<namespace>:<action>', methods=['GET', 'POST'])
@login_required
def save_tags(namespace, author, action):
    error = 0
    if Auth.is_authenticated and (current_user.author == author or current_user.access > 1):
        f = request.form
        if f:
            datadic = {}
            for key in f.keys():
                _id = key.rsplit('_', 1)[1]
                k = key.rsplit('_', 1)[0]
                if len(_id) == 24:  # ObjectID in Mongo
                    try:
                        datadic[_id].update({k: f.get(key)})
                    except:
                        datadic[_id] = {k: f.get(key)}
            datadic[_id].update({"namespace" : [namespace]})
            for _id, data in datadic.iteritems():
                DB(g.location).update_an_object(_id, data)
        else:
            error == 1
    else:
        error = "Something wrong with a form or authentification!"
        flash(error, category='error')
    if error == 0:
        flash("Data updated successfully!", category='info')
    else:
        error = "Something wrong with a form or authentification!"
        flash(error, category='error')
    itmpl = tmpl_picker('form_tags')
    new_objects = DB(g.location).get_objects_by_key_sorted_filter_yes("", "I_S_codename", namespace)
    spaces = DB(g.location).get_spaces_by_author_ns(author, namespace)
    data = json.loads(dumps(spaces))
    chapters = chapters_for_tags(data)
    return render_template(itmpl, form=g.form, objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, new_objects=new_objects, namespace=namespace, chapters=chapters)


@app.route('/editspace/del_a_tag:<author>:<namespace>:<codename>', methods=['GET', 'POST'])
@login_required
def del_a_tag(author, namespace, codename):
    DB(g.location).del_an_object(codename, namespace)
    return jsonify( {'data': "tag with a codename <b>" + codename + "</b> is deleted!"} )


@app.route('/editspace/detach_a_tag:<author>:<namespace>:<codename>', methods=['GET', 'POST'])
@login_required
def detach_a_tag(author, namespace, codename):
    DB(g.location).detach_an_object(codename, namespace)
    return jsonify( {'data': "tag with a codename <b>" + codename + "</b> is detached!"} )


@app.route('/editspace/del_point:<author>:<namespace>:<chapter>:<point>', methods=['GET', 'POST'])
@app.route('/en/editspace/del_point:<author>:<namespace>:<chapter>:<point>', methods=['GET', 'POST'])
@app.route('/he/editspace/del_point:<author>:<namespace>:<chapter>:<point>', methods=['GET', 'POST'])
@login_required
def del_point(author, namespace, chapter, point):
    DB(g.location).del_point_from_a_chapter(author, namespace, chapter, point)
    return jsonify( {'data': "point <b>" + point + "</b> is deleted!"} )


@app.route('/editspace/hide_point:<author>:<namespace>:<chapter>:<point>:<h>', methods=['GET', 'POST'])
@app.route('/en/editspace/hide_point:<author>:<namespace>:<chapter>:<point>:<h>', methods=['GET', 'POST'])
@app.route('/he/editspace/hide_point:<author>:<namespace>:<chapter>:<point>:<h>', methods=['GET', 'POST'])
@login_required
def hide_point(author, namespace, chapter, point, h):
    # print author, namespace, chapter, point, h
    DB(g.location).hide_point_in_a_chapter(author, namespace, chapter, point, int(h))
    if int(h) == 1:
        msg = "hidden now!"
    else:
        msg = "visible now!"
    return jsonify( {'data': "point <b>" + point + "</b> is " + msg} )


@app.route('/editspace/del_source:<author>:<namespace>:<chapter>:<point>:<source>', methods=['GET', 'POST'])
@app.route('/en/editspace/del_source:<author>:<namespace>:<chapter>:<point>:<source>', methods=['GET', 'POST'])
@app.route('/he/editspace/del_source:<author>:<namespace>:<chapter>:<point>:<source>', methods=['GET', 'POST'])
@login_required
def del_sources_pool(author, namespace, chapter, point, source):
    DB(g.location).del_srcpool_from_a_chapter(author, namespace, chapter, point, source)
    return jsonify( {'data': "source <b>" + source + "</b> from <b>" + point + "</b> point is deleted!"} )


@app.route('/editspace/del_img:<author>:<namespace>:<chapter>:<point>:<img>', methods=['GET', 'POST'])
@app.route('/en/editspace/del_img:<author>:<namespace>:<chapter>:<point>:<img>', methods=['GET', 'POST'])
@app.route('/he/editspace/del_img:<author>:<namespace>:<chapter>:<point>:<img>', methods=['GET', 'POST'])
@login_required
def del_img_pool(author, namespace, chapter, point, img):
    DB(g.location).del_imgpool_from_a_chapter(author, namespace, chapter, point, img)
    return jsonify( {'data': "image pool <b>" + img +  "</b> from <b>" + point + "</b> point is deleted!"} )


@app.route('/editspace/export_json:<author>:<namespace>:<chapter>', methods=['GET', 'POST'])
@app.route('/en/editspace/export_json:<author>:<namespace>:<chapter>', methods=['GET', 'POST'])
@app.route('/he/editspace/export_json:<author>:<namespace>:<chapter>', methods=['GET', 'POST'])
@login_required
def export_json(author, namespace, chapter):
    data = Tools().exportJson(author, namespace, chapter, g.location)
    # print data
    json = namespace + "_" + chapter + "_" + g.location + ".json"
    response = make_response(data)
    response.headers["Content-Disposition"] = "attachment; filename=" + json
    return response


@app.route('/editspace/export_json_intro:<author>:<namespace>', methods=['GET', 'POST'])
@app.route('/en/editspace/export_json_intro:<author>:<namespace>', methods=['GET', 'POST'])
@app.route('/he/editspace/export_json_intro:<author>:<namespace>', methods=['GET', 'POST'])
@login_required
def export_json_intro(author, namespace):
    data = Tools().exportJson_intro(author, namespace, g.location)
    # print data
    json = namespace + "_intro_" + g.location + ".json"
    response = make_response(data)
    response.headers["Content-Disposition"] = "attachment; filename=" + json
    return response


@app.route('/editspace/autocomplete', methods=['GET', 'POST'])
@login_required
def autocomplete():
    search = request.args.get('query')
    data = DB(g.location).search_objects(str(search))
    results = json.loads(dumps(data))
    suggestions = []
    for entry in results:
        suggestions.append(entry["I_S_codename"])
    return jsonify({"suggestions": suggestions})


@app.route('/editspace/autocomplete_geo', methods=['GET', 'POST'])
@login_required
def autocomplete_geo():
    search = request.args.get('query')
    data = DB(g.location).search_objects_geo(str(search))
    results = json.loads(dumps(data))
    suggestions = []
    for entry in results:
        suggestions.append(entry["I_S_codename"])
    return jsonify({"suggestions": suggestions})


@app.context_processor
def utility_processor():
    def format_color(num):
        if not num:
            num = 1
        num = "{}".format(num)
        hexstr = "%06x" % (float(num) * 20)
        r, g, b = hexstr[4:], "F" + hexstr[3:4], "A" + hexstr[1:2]
        r, g, b = [int(n, 16) for n in (r, g, b)]
        return r, g, b

    return dict(format_color=format_color)
