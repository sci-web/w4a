from app import app, lm
import re
import datetime
# import xlrd
from flask import request, redirect, render_template, flash, Response, send_from_directory, url_for, g
from flask_login import login_user, logout_user, login_required, current_user
from .auth import Auth
from .model import DB
from .forms import editIntro


def extension_ok(filename, ff):
    """ return whether file's extension is ok or not"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config[ff]


def packed(val_dict):
    # vls = ", ".join(['{}={}'.format(k, v) for k, v in val_dict.iteritems()])
    ll = []
    for k, v in val_dict.iteritems():
        exec(k + " = v")
        ll.append(k)
    return ll


@app.route('/login/', methods=['GET', 'POST'])
def login():
    url = g.form.from_url.data
    if url is not None and url != "/" and url != "":
        url = url.strip("/")
        return redirect(url_for(url))
    else:
        return redirect("/")


@app.route('/logout/')
def logout():
    logout_user()
    return redirect("/")


@lm.user_loader
def load_user(email):
    u = DB().get_a_user(email)
    if not u:
        return None
    return Auth(u['email'], u['access'], u['author'])


@app.route('/editspace/<author>')
@login_required
def editspace(author):
    i_data = DB().get_intros()
    sform = editIntro()
    return render_template('form_intro.html', form=g.form, items=g.items, author=author,
        objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, chapters=g.chapters, data=i_data, sform=sform)


@app.route('/editspace/intro:<author>', methods=['GET', 'POST'])
@login_required
def edit_intro(author):
    # sp_data = DB().get_intros_by_namespace(namespace)
    sform = editIntro(request.values) #, namespace=sp_data["namespace"])  # keep defaul values here to see updated results on the edit page
    in_data = {}
    in_data["date"] = datetime.datetime.now().strftime('%d-%m-%Y %H:%M')
    in_data["points"] = []
    in_data["refs"] = []
    if sform.validate_on_submit() and Auth.is_authenticated and (current_user.author == author or current_user.access > 1):
        if sform.data:
            f = request.form
            points = {}
            refs = []
            in_refs = {}
            in_refs_pool = {}
            ep_text = ""
            ep_source = ""
            error = 0
            for key in f.keys():
                for value in f.getlist(key):
                    # print key,":",value
                    if key == "namespace": in_data["namespace"] = value
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
                    if (re.match("refBlockTtl", key) and value != ""):
                        p, r = key.split("_")
                        if (value != ""):
                            try:
                                in_refs[r].update({"ref_title": value})
                            except:
                                in_refs[r] = {"ref_title": value}

                    if (re.match("refBlockDigest", key) and value != ""):
                        p, r = key.split("_")
                        if (value != ""):                         
                            try:
                                in_refs[r].update({"ref_digest": value})
                            except:
                                in_refs[r] = {"ref_digest": value}

                    if (re.match("refBlockType", key) and value != ""):
                        p, r = key.split("_")
                        if (value != ""):                         
                            try:
                                in_refs[r].update({"ref_type": value})
                            except:
                                in_refs[r] = {"ref_type": value}

                    if (re.match("linkTitle", key) and value != ""):
                        p, l, r = key.split("_")
                        if (value != ""):                        
                            try:
                                in_refs_pool[r][l].update({"title": value})
                            except:
                                try:
                                    in_refs_pool[r].update({l : {"title": value}})
                                except:
                                    in_refs_pool[r] = ({l : {"title": value}})

                    if (re.match("linkURL", key) and value != ""):
                        p, l, r = key.split("_")
                        if (value != ""):                        
                            try:
                                in_refs_pool[r][l].update({"link": value})
                            except:
                                try:
                                    in_refs_pool[r].update({l: {"link": value}})
                                except:
                                    in_refs_pool[r] = ({l : {"link": value}})

                    if (re.match("linkType", key) and value != ""):
                        p, l, r = key.split("_")
                        if (value != ""):
                            try:
                                in_refs_pool[r][l].update({"linktype": value})
                            except:
                                try:
                                    in_refs_pool[r].update({l : {"linktype": value}})
                                except:
                                    in_refs_pool[r] = ({l : {"linktype": value}})

                    if (re.match("linkDigest", key) and value != ""):
                        p, l, r = key.split("_")
                        if (value != ""): 
                            try:
                                in_refs_pool[r][l].update({"digest": value})
                            except:
                                try:
                                    in_refs_pool[r].update({l: {"digest": value}})
                                except:
                                    in_refs_pool[r] = ({l : {"digest": value}})
                    if (re.match("linkAuthor", key) and value != ""):
                        p, l, r = key.split("_")
                        if (value != ""): 
                            try:
                                in_refs_pool[r][l].update({"author": value})
                            except:
                                try:
                                    in_refs_pool[r].update({l: {"author": value}})
                                except:
                                    in_refs_pool[r] = ({l : {"author": value}})

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

            for n, p in sorted(points.iteritems()):
                in_data["points"].append({"num": n, "item": p})

            for n, rf in sorted(in_refs.iteritems()):
                try:
                    refs.append(in_refs[n])
                except:
                    if (len(in_refs[n])) > 0:
                        refs = in_refs[n]
            in_data["refs"] = refs

            if ep_text != "": in_data["epigraph"] = {"text": ep_text, "source": ep_source}
            intro = DB().find_intro_by_author(author, in_data["namespace"])
            if not intro:
                in_data["analyst"] = author
                DB().insert_an_intro(in_data)
            else:
                DB().update_an_intro(author, in_data["namespace"], in_data)

        else:
            error = 1
            flash("Something wrong with data update!", category='error')
        if error == 0:
            flash("Data updated successfully!", category='info')
        else:
            flash("Something wrong happened!", category='error')
    return render_template('form_intro.html', form=g.form, items=g.items, 
        objects=g.objects, conditions=g.conditions, drugs=g.drugs, geo_objects=g.objects_geo, chapters=g.chapters, sform=sform)


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
