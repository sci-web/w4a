from app import app, lm
import re
from datetime import datetime
# import xlrd
from flask import request, redirect, render_template, flash, Response, send_from_directory, url_for, g
from flask_login import login_user, logout_user, login_required, current_user
from .auth import Auth
from .model import DB
from .forms import saveIntro, newIntro, saveContent, newContent
from bson.json_util import dumps
import json
from collections import defaultdict


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
    namespaces = DB().get_intros_by_author(author)
    spaces = DB().get_spaces_by_author(author)
    data = json.loads(dumps(spaces))
    chapters = defaultdict(list)
    for d in range(0, len(data)):
        ns = data[d]["namespace"]
        c_date = datetime.fromtimestamp( data[d]["date"]['$date'] / 1e3 )
        ch = data[d]["title"] + "|" + data[d]["I_S_codename"] + "|" + c_date.strftime('%d-%m-%Y %H:%M')
        chapters[ns].append(ch)

    return render_template('cms_start.html', form=g.form, items=g.items, author=author, namespaces=namespaces, chapters=chapters)


@app.route('/editspace/intro:<author>:<namespace>', methods=['GET', 'POST'])
@login_required
def edit_intro(author, namespace):
    if namespace == "0":
        return render_template('form_intro.html', form=g.form)
    else:
        i_data = DB().get_an_intro(namespace)
        return render_template('form_intro_edit.html', form=g.form, items=i_data)


@app.route('/editspace/save_intro:<author>:<namespace>', methods=['GET', 'POST'])
@login_required
def save_intro(author, namespace):
    # sp_data = DB().get_intros_by_namespace(namespace)
    if namespace == "0":
        sform = newIntro(request.values)
    else:
        sform = saveIntro(request.values)
    in_data = {}
    in_data["points"] = []
    in_data["refs"] = []
    error = 0
    new_namespace = ""
    # {{ form.hidden_tag() }} must be in template for sform.validate_on_submit() True if fields are ok
    if sform.validate_on_submit() and Auth.is_authenticated and (current_user.author == author or current_user.access > 1):
        if sform.data:
            f = request.form
            points = {}
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
                        i_data = DB().get_an_intro(in_data["namespace"])  # before update/insert
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

                if namespace == "0":
                    in_data["date"] = datetime.now()
                    in_data["analyst"] = author
                    DB().insert_an_intro(in_data)
                else:
                    DB().update_an_intro(author, namespace, in_data)
            else:
                flash(error, category='error')    
        else:
            error = "Something wrong with data update!"
        if error == 0:
            flash("Data updated successfully!", category='info')
        else:
            flash(error, category='error')
    else:
        error = "Something wrong with a form or authentification!"
        flash(error, category='error')                
    if namespace != "0":
        i_data = DB().get_an_intro(namespace)  # after update/insert
        return render_template('form_intro_edit.html', form=g.form, items=i_data)
    else:
        if error == 0:
            i_data = DB().get_an_intro(namespace)
            return redirect("/editspace/intro:" + new_namespace + ":" + author + "")
        else:
            i_data = in_data
            return render_template('form_intro.html', form=g.form, items=i_data)


@app.route('/editspace/chapter:<author>:<namespace>:<chapter>', methods=['GET', 'POST'])
@login_required
def edit_chapter(author, namespace, chapter):
    if chapter == "0":
        return render_template('form_chapter.html', form=g.form, namespace=namespace)
    else:
        i_data = DB().get_a_chapter(namespace, chapter)
        return render_template('form_chapter_edit.html', form=g.form, items=i_data, namespace=namespace, chapter=chapter)


def value_match_assign(match, field, dhash):
    if (re.match(match, key) and value != ""):
        p, r = key.split("_")
        if (value != ""):
            try:
                dhash[r].update({field: value})
            except:
                dhash[r] = {field: value}
    return dhash

@app.route('/editspace/save_chapter:<author>:<namespace>:<chapter>', methods=['GET', 'POST'])
@login_required
def save_chapter(author):
    # sp_data = DB().get_intros_by_namespace(namespace)
    sform = saveContent(request.values) #, namespace=sp_data["namespace"])  # keep defaul values here to see updated results on the edit page
    in_data = {}
    in_data["date"] = datetime.now()
    in_data["points"] = []
    if sform.validate_on_submit() and Auth.is_authenticated and (current_user.author == author or current_user.access > 1):
        if sform.data:
            f = request.form
            points = {}
            in_pnts = {}
            in_imgs_pool = {}
            in_sources_pool = {}
            ep_text = ""
            ep_source = ""
            error = 0
            for key in f.keys():
                for value in f.getlist(key):
                    in_data["I_S_codename"] = new_chapter
                    if key == "chapter" and chapter == "0": 
                        in_data["I_S_codename"] = value              
                        i_data = DB().get_a_chapter(namespace, in_data["I_S_codename"])  # before update/insert
                        if i_data and chapter == 0:
                            error = "This chapter:" + in_data["I_S_codename"] + " already exists!"
                            break
                        else:
                            new_chapter = in_data["I_S_codename"] 

                    if key == "title": in_data["title"] = value
                    if (key == "intro" and value != ""): in_data["intro"] = value
                    if (key == "summary" and value != ""): in_data["summary"] = value
                    if key == "ep_text": ep_text = value
                    if key == "ep_source": ep_source = value
                    if (re.match("point", key) and value != ""):
                        p, k = key.split("_")
                        points[k] = value

                    value_match_assign("pointHeader", "field", in_pnts) 
                       
                    # if (re.match("pointHeader", key) and value != ""):
                    #     p, r = key.split("_")
                    #     if (value != ""):
                    #         try:
                    #             in_pnts[r].update({"header": value})
                    #         except:
                    #             in_pnts[r] = {"header": value}

                    if (re.match("pointTitle", key) and value != ""):
                        p, r = key.split("_")
                        if (value != ""):                         
                            try:
                                in_pnts[r].update({"title": value})
                            except:
                                in_pnts[r] = {"title": value}

                    if (re.match("pointLink", key) and value != ""):
                        p, r = key.split("_")
                        if (value != ""):                         
                            try:
                                in_pnts[r].update({"link": value})
                            except:
                                in_pnts[r] = {"link": value}

                    if (re.match("pointType", key) and value != ""):
                        p, r = key.split("_")
                        if (value != ""):                         
                            try:
                                in_pnts[r].update({"info_type": value})
                            except:
                                in_pnts[r] = {"info_type": value}

                    if (re.match("pointPID", key) and value != ""):
                        p, r = key.split("_")
                        if (value != ""):                         
                            try:
                                in_pnts[r].update({"infoID": value})
                            except:
                                in_pnts[r] = {"infoID": value}

                    if (re.match("pointPdate", key) and value != ""):
                        p, r = key.split("_")
                        if (value != ""):                         
                            try:
                                in_pnts[r].update({"info_date": value})
                            except:
                                in_pnts[r] = {"info_date": value}
                    if (re.match("pointPauths", key) and value != ""):
                        p, r = key.split("_")
                        if (value != ""):                         
                            try:
                                in_pnts[r].update({"info_authors": value})
                            except:
                                in_pnts[r] = {"info_authors": value}

                    if (re.match("pointPub", key) and value != ""):
                        p, r = key.split("_")
                        if (value != ""):                         
                            try:
                                in_pnts[r].update({"info_place": value})
                            except:
                                in_pnts[r] = {"info_place": value}

                    if (re.match("pointGeo", key) and value != ""):
                        p, r = key.split("_")
                        if (value != ""):                         
                            try:
                                in_pnts[r].update({"info_geo": value})
                            except:
                                in_pnts[r] = {"info_geo": value}

                    if (re.match("pointTags", key) and value != ""):
                        p, r = key.split("_")
                        if (value != ""):                            
                            lst = value.split(",")
                            for e in lst:
                                e.replace(" ", "")                   
                            try:
                                in_pnts[r].update({"I_S_codenames": lst})
                            except:
                                in_pnts[r] = {"I_S_codenames": lst}

                    if (re.match("pointImage", key) and value != ""):
                        p, r = key.split("_")
                        if (value != ""):                         
                            try:
                                in_pnts[r].update({"info_img": value})
                            except:
                                in_pnts[r] = {"info_img": value}                            

                    if (re.match("pointIsource", key) and value != ""):
                        p, r = key.split("_")
                        if (value != ""):                         
                            try:
                                in_pnts[r].update({"info_imgSource": value})
                            except:
                                in_pnts[r] = {"info_imgSource": value}                            

                    if (re.match("pointIdescr", key) and value != ""):
                        p, r = key.split("_")
                        if (value != ""):                         
                            try:
                                in_pnts[r].update({"info_imgDescr": value})
                            except:
                                in_pnts[r] = {"info_imgDescr": value}                            

                    if (re.match("pointDigest", key) and value != ""):
                        p, r = key.split("_")
                        if (value != ""):                         
                            try:
                                in_pnts[r].update({"digest": value})
                            except:
                                in_pnts[r] = {"digest": value}                            


                    if (re.match("imgPoolDescr", key) and value != ""):
                        p, l, r = key.split("_")
                        if (value != ""):                        
                            try:
                                in_imgs_pool[r][l].update({"info_imgDesc": value})
                            except:
                                try:
                                    in_imgs_pool[r].update({l : {"info_imgDesc": value}})
                                except:
                                    in_imgs_pool[r] = ({l : {"info_imgDesc": value}})

                    if (re.match("imgPoolLink", key) and value != ""):
                        p, l, r = key.split("_")
                        if (value != ""):                        
                            try:
                                in_imgs_pool[r][l].update({"info_img": value})
                            except:
                                try:
                                    in_imgs_pool[r].update({l: {"info_img": value}})
                                except:
                                    in_imgs_pool[r] = ({l : {"info_img": value}})

                    if (re.match("imgPoolSrcURL", key) and value != ""):
                        p, l, r = key.split("_")
                        if (value != ""):
                            try:
                                in_imgs_pool[r][l].update({"info_imgSource": value})
                            except:
                                try:
                                    in_imgs_pool[r].update({l : {"info_imgSource": value}})
                                except:
                                    in_imgs_pool[r] = ({l : {"info_imgSource": value}})

                    if (re.match("imgSrcTitle", key) and value != ""):
                        p, l, r = key.split("_")
                        if (value != ""): 
                            try:
                                in_imgs_pool[r][l].update({"info_imgTitle": value})
                            except:
                                try:
                                    in_imgs_pool[r].update({l: {"info_imgTitle": value}})
                                except:
                                    in_imgs_pool[r] = ({l : {"info_imgTitle": value}})

                    if (re.match("srcTitle", key) and value != ""):
                        p, l, r = key.split("_")
                        if (value != ""): 
                            try:
                                in_sources_pool[r][l].update({"title": value})
                            except:
                                try:
                                    in_sources_pool[r].update({l: {"title": value}})
                                except:
                                    in_sources_pool[r] = ({l : {"title": value}})


                    if (re.match("srcLink", key) and value != ""):
                        p, l, r = key.split("_")
                        if (value != ""):                        
                            try:
                                in_sources_pool[r][l].update({"link": value})
                            except:
                                try:
                                    in_sources_pool[r].update({l : {"link": value}})
                                except:
                                    in_sources_pool[r] = ({l : {"link": value}})

                    if (re.match("srcID", key) and value != ""):
                        p, l, r = key.split("_")
                        if (value != ""):                        
                            try:
                                in_sources_pool[r][l].update({"infoID": value})
                            except:
                                try:
                                    in_sources_pool[r].update({l: {"infoID": value}})
                                except:
                                    in_sources_pool[r] = ({l : {"infoID": value}})

                    if (re.match("srcDate", key) and value != ""):
                        p, l, r = key.split("_")
                        if (value != ""):
                            try:
                                in_sources_pool[r][l].update({"info_date": value})
                            except:
                                try:
                                    in_sources_pool[r].update({l : {"info_date": value}})
                                except:
                                    in_sources_pool[r] = ({l : {"info_date": value}})

                    if (re.match("srcAuth", key) and value != ""):
                        p, l, r = key.split("_")
                        if (value != ""): 
                            try:
                                in_sources_pool[r][l].update({"info_authors": value})
                            except:
                                try:
                                    in_sources_pool[r].update({l: {"info_authors": value}})
                                except:
                                    in_sources_pool[r] = ({l : {"info_authors": value}})

                    if (re.match("srcPlace", key) and value != ""):
                        p, l, r = key.split("_")
                        if (value != ""): 
                            try:
                                in_sources_pool[r][l].update({"info_place": value})
                            except:
                                try:
                                    in_sources_pool[r].update({l: {"info_place": value}})
                                except:
                                    in_sources_pool[r] = ({l : {"info_place": value}})

                    if (re.match("srcType", key) and value != ""):
                        p, l, r = key.split("_")
                        if (value != ""): 
                            try:
                                in_sources_pool[r][l].update({"info_type": value})
                            except:
                                try:
                                    in_sources_pool[r].update({l: {"info_type": value}})
                                except:
                                    in_sources_pool[r] = ({l : {"info_type": value}})
            if error == 0:                
                for r in in_pnts.keys():
                    imgs_pool = []
                    for l in in_imgs_pool[r].keys():
                        # print l, in_refs_pool[r][l]
                        try:
                            imgs_pool.append(in_imgs_pool[r][l])
                        except:
                            if len(in_imgs_pool[r][l]) > 0:
                                imgs_pool = in_imgs_pool[r][l]
                    try:
                        in_pnts[r].update({"img_pool": imgs_pool})
                    except:
                        in_pnts[r] = {"img_pool": imgs_pool}

                    src_pool= []
                    for l in in_sources_pool[r].keys():
                        # print l, in_refs_pool[r][l]
                        try:
                            src_pool.append(in_sources_pool[r][l])
                        except:
                            if len(in_imgs_pool[r][l]) > 0:
                                src_pool = in_sources_pool[r][l]
                    try:
                        in_pnts[r].update({"sources_pool": imgs_pool})
                    except:
                        in_pnts[r] = {"sources_pool": imgs_pool}

                for n, p in sorted(in_pnts.iteritems()):
                    p.update({"num": n})
                    in_data["points"].append(p)

                if ep_text != "": in_data["epigraph"] = {"text": ep_text, "source": ep_source}

                if chapter == "0":
                    in_data["date"] = datetime.now()
                    in_data["analyst"] = author
                    DB().insert_a_chapter(namespace, in_data)
                else:
                    DB().update_a_chapter(author, namespace, chapter, in_data)
            else:
                flash(error, category='error')    
        else:
            error = "Something wrong with data update!"
        if error == 0:
            flash("Data updated successfully!", category='info')
        else:
            flash(error, category='error')
    else:
        error = "Something wrong with a form or authentification!"
        flash(error, category='error')                
    if chapter != "0":
        i_data = DB().get_a_chapter(namespace, chapter)  # after update/insert
        return render_template('form_intro_edit.html', form=g.form, items=i_data)
    else:
        if error == 0:
            i_data = DB().get_an_intro(namespace)
            return redirect("/editspace/chapter:" + author + ":" + namespace + ":" + new_chapter)
        else:
            i_data = in_data
            return render_template('form_intro.html', form=g.form, items=i_data)



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
