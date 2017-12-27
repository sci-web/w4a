# -*- coding:utf-8 -*-
from app import app
import re


class DB(object):


    def get_spaces_by_key_sorted(self, namespace, key):
        return app.config['SPACES'].find({"namespace": namespace}, {"namespace": 1, "I_S_codename": 1, "I_S_name": 1}).sort(key, 1)

    def get_a_space(self, namespace, key):
        return app.config['SPACES'].find({"namespace": namespace, "I_S_codename": key})

    def get_objects_by_key_sorted(self, key):
        return app.config['OBJECTS'].find({}, {"I_S_codename": 1, "I_S_name": 1}).sort(key, 1)

    def get_intros(self):
        return app.config['INTROS'].find({}, {"namespace": 1, "analyst": 1, "subject": 1, "epigraph": 1, "intro": 1})

    def get_an_intro(self, namespace):
        return app.config['INTROS'].find({"namespace": namespace})

    def get_data_search(self, title, released):
        try:
            return app.config['INTROS'].find({
                '$text': {'$search': title},
                }, {'score': {'$meta': 'textScore'}})
        except Exception, e:
            print e

    def get_data(self, start, end):
        return app.config['SPACES'].find({ "appeared": 
                { '$elemMatch' : 
                    { "start_time": { '$gt': start }, "end_time": { '$lt': end } }
                } 
            })

    def get_meta(self):
        return app.config['META'].find()
