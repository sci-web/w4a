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
                    print key,":",value
                    if key == "namespace": in_data["namespace"] = value
                    if key == "subject": in_data["subject"] = value
                    if (key == "intro" and value != ""): in_data["intro"] = value
                    if (key == "ref_intro" and value != ""): in_data["ref_intro"] = value
                    if (key == "ref_title" and value != ""): in_data["ref_title"] = value
                    if key == "ep_text": ep_text = value
                    if key == "ep_source": ep_source = value
                    if (re.match("points", key) and value != ""):
                        p, k = key.split("_")
                        points[k] = value
            #         if (re.match("refBlockTtl", key) and value != ""):
            #             p, r = key.split("_")
            #             in_refs[r].append({"ref_title": value})
            #         if (re.match("refBlockDigest", key) and value != ""):
            #             p, r = key.split("_")
            #             in_refs[r].append({"ref_digest": value})
            #         if (re.match("refBlockType", key) and value != ""):
            #             p, r = key.split("_")
            #             in_refs[r].append({"ref_type": value})
            #         if (re.match("linkTitle", key) and value != ""):
            #             p, l, r = key.split("_")
            #             in_refs_pool[r][l].append({"title": value})
            #         if (re.match("linkURL", key) and value != ""):
            #             p, l, r = key.split("_")
            #             in_refs_pool[r][l].append({"link": value})
            #         if (re.match("linkType", key) and value != ""):
            #             p, l, r = key.split("_")
            #             in_refs_pool[r][l].append({"linktype": value})
            #         if (re.match("linkDigest", key) and value != ""):
            #             p, l, r = key.split("_")
            #             in_refs_pool[r][l].append({"digest": value})
            #         if (re.match("linkAuthor", key) and value != ""):
            #             p, l, r = key.split("_")
            #             in_refs_pool[r][l].append({"author": value})
            # for r in in_refs.keys():
            #     refs.append(in_refs[r])
            #     ref_pool = []
            #     for l in in_refs_pool[r].keys():
            #         ref_pool.append(in_refs_pool[r][l])
            #     refs.append({"ref_pool": ref_pool})
            for n, p in sorted(points.iteritems()):
                in_data["points"].append({"num": n, "item": p})
            if ep_text != "": in_data["epigraph"] = {"text": ep_text, "source": ep_source}
            # in_data["refs"] = refs
            print in_data
            print sform.data
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
