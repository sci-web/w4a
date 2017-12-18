# -*- coding:utf-8 -*-
from app import app
import re


class DB(object):

    def get_data_search(self, title, released):
        try:
            return app.config['INTRO'].find({
                '$text': {'$search': title},
                }, {'score': {'$meta': 'textScore'}})
        except Exception, e:
            print e

    def get_data(self, start, end):
        return app.config['INSTANCE'].find({ "appeared": 
                { '$elemMatch' : 
                    { "start_time": { '$gt': start }, "end_time": { '$lt': end } }
                } 
            })

    def get_meta(self):
        return app.config['META'].find()
