from app import app, lm
import datetime
import xlrd
from flask import redirect, url_for, render_template
# from flask_login import login_user, logout_user, login_required, current_user
from .forms import makeform
from .auth import Auth


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
    form = makeform()
    url = form.from_url.data
    if url is not None and url != "/" and url != "":
        url = url.strip("/")
        return redirect(url_for(url))
    else:
        return redirect("/")


@app.route('/logout/')
def logout():
    logout_user()
    return redirect("/")


@app.errorhandler(404)
def page_not_found(error):
    form = makeform()
    return render_template('404.html', form=form), 404


@app.errorhandler(500)
def internal_error(error):
    form = makeform()
    return render_template('500.html', form=form), 500


@lm.user_loader
def load_user(email):
    u = app.config['STAFF'].find_one({"email": email})
    if not u:
        return None
    return Auth(u['email'], u['access'], u['first_name'], u['surname'])


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
