# -*- coding:utf-8 -*-
from app import app
import re


class DB(object):


    def get_spaces_by_key_sorted(self, namespace, key):
        return app.config['SPACES'].find(
                                        {"namespace": namespace}, 
                                        {"namespace": 1, "I_S_codename": 1, "I_S_name": 1, "I_S_type": 1, "intro": 1, "title": 1, "date":1, "epigraph": 1, "points": {"$slice": 1}}
                                        ).sort(key, 1)

    def search(self, expression):
        # return app.config['SPACES'].find(
        #         {
        #         '$text': {'$search': expression, '$language': "ru"}
        #         }, {'score': {'$meta': 'textScore'}})
        return app.config['SPACES'].aggregate([
                            {'$match':{ '$or': [
                                {"points.digest":{'$regex':expression}}, 
                                {"points.title":{'$regex':expression}}, 
                                {"points.img_pool.info_imgDesc":{'$regex':expression }},
                                {"points.sources_pool.title":{'$regex':expression}}
                                ]}}, 
                            { '$unwind' : "$points" },
                            {'$match':{ '$or': [
                                {"points.digest":{'$regex':expression}}, 
                                {"points.title":{'$regex':expression}}, 
                                {"points.img_pool.info_imgDesc":{'$regex':expression }},
                                {"points.sources_pool.title":{'$regex':expression}}
                                ]}}
                            ])

    def get_a_space(self, namespace, key):
        return app.config['SPACES'].find({"namespace": namespace, "I_S_codename": key})

    def get_points_by_codename(self, codename):
        return app.config['SPACES'].aggregate([
                            {'$match':{"points.I_S_codenames":codename}}, 
                            { '$unwind' : "$points" },
                            {'$match':{"points.I_S_codenames":codename}}
                            ])

    def get_points_by_geo(self, codename):
        return app.config['SPACES'].aggregate([
                            {'$match':{"points.info_geo":codename}}, 
                            { '$unwind' : "$points" },
                            {'$match':{"points.info_geo":codename}}
                            ])

    def get_an_object_by_codename(self, codename):
        return app.config['OBJECTS'].find({"I_S_codename": codename})

    def get_objects_by_key_sorted_filter_no(self, val, key):
        return app.config['OBJECTS'].find({"I_S_type_this": {'$ne': val}}, {"I_S_codename": 1, "I_S_name": 1}).sort(key, 1)

    def get_objects_by_key_sorted_filter_yes(self, val, key):
        return app.config['OBJECTS'].find({"I_S_type_this": val}, {"I_S_codename": 1, "I_S_name": 1}).sort(key, 1)

    def get_intros(self):
        return app.config['INTROS'].find({}, {"namespace": 1, "analyst": 1, "subject": 1, "epigraph": 1, "intro": 1})

    def get_an_intro(self, namespace):
        return app.config['INTROS'].find_one({"namespace": namespace})

    def get_a_chapter(self, namespace, chapter):
        return app.config['SPACES'].find_one({"namespace": namespace, "I_S_codename": chapter})

    def get_intros_by_author(self, author):
        return app.config['INTROS'].find({"analyst": author},{"date":1, "namespace":1}).sort("namespace", 1)

    def get_spaces_by_author(self, author):
        return app.config['SPACES'].find({"analyst": author},{"date":1, "namespace":1, "title":1, "I_S_codename":1}).sort("date", -1)        

    def get_data_search(self, title, released):
        try:
            return app.config['INTROS'].find({
                '$text': {'$search': title},
                }, {'score': {'$meta': 'textScore'}})
        except Exception, e:
            print e

    def get_a_user(self, email):
        return app.config['CORE'].find_one({"email": email})

    def find_intro_by_author(self, author, namespace):
        return app.config['INTROS'].find_one({"analyst": author, "namespace": namespace})

    def insert_an_intro(self, data):
        app.config['INTROS'].insert_one(data)
        
    def update_an_intro(self, author, namespace, data):
        app.config['INTROS'].update_one({"analyst": author, "namespace": namespace}, {'$set': data})
