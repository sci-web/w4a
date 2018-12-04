from sc import app, lm
import shlex, subprocess, time, io
from .model import DB
from datetime import datetime


class Tools(object):

    def exportJson(self, author, namespace, chapter, loc):
        if loc == "en":
            command_line = app.config['MONGOEXP'] + " --db w4a --collection chapters_en --query '{\"analyst\":\"" + author + "\",\"namespace\":\"" + namespace + "\",\"I_S_codename\":\"" + chapter + "\"}' --pretty"
        elif loc == "he":
            command_line = app.config['MONGOEXP'] + " --db w4a --collection chapters_he --query '{\"analyst\":\"" + author + "\",\"namespace\":\"" + namespace + "\",\"I_S_codename\":\"" + chapter + "\"}' --pretty"
        else: 
            command_line = app.config['MONGOEXP'] + " --db w4a --collection chapters --query '{\"analyst\":\"" + author + "\",\"namespace\":\"" + namespace + "\",\"I_S_codename\":\"" + chapter + "\"}' --pretty"
        args = shlex.split(command_line)
        try:
            json = ""
            output = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            content = output.stdout.read()
            content = content.replace("\u003c","<")
            content = content.replace("\u003e",">")            
            return content
        except Exception, e:
            logdata = {"time": datetime.now(), "pid": 0, "action": "exportJson:" + str(e), "type": "error"}
            # DB().load_one("logs", [logdata])
            return "there is a mistake in data export: " + e


    def exportJson_intro(self, author, namespace, loc):
        if loc == "en":
            command_line = app.config['MONGOEXP'] + " --db w4a --collection intros_en --query '{\"analyst\":\"" + author + "\",\"namespace\":\"" + namespace + "\"}' --pretty"
        elif loc == "he":
            command_line = app.config['MONGOEXP'] + " --db w4a --collection intros_he --query '{\"analyst\":\"" + author + "\",\"namespace\":\"" + namespace + "\"}' --pretty"
        else: 
            command_line = app.config['MONGOEXP'] + " --db w4a --collection intros --query '{\"analyst\":\"" + author + "\",\"namespace\":\"" + namespace + "\"}' --pretty"
        args = shlex.split(command_line)
        try:
            json = ""
            output = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            content = output.stdout.read()
            content = content.replace("\u003c","<")
            content = content.replace("\u003e",">")            
            return content
        except Exception, e:
            logdata = {"time": datetime.now(), "pid": 0, "action": "exportJson:" + str(e), "type": "error"}
            # DB('').load_one("logs", [logdata])
            return "there is a mistake in data export: " + e

