# -*- coding:utf-8 -*-
from scibook import app
import re
from bson.objectid import ObjectId


class DB(object):

    def __init__(self, lang):
        self.lang = lang
        if lang != "ru":
            self.spaces = 'SPACES_' + lang.upper()
            self.intros = 'INTROS_' + lang.upper()
        else:
            self.spaces = 'SPACES'
            self.intros = 'INTROS'
        # self.objects = 'OBJECTS'

    def server_info(self):
        return app.config['DB'].server_info()

    def get_any_chapter(self):
        return app.config[self.spaces].find_one({},{"namespace": 1})

    def get_spaces_by_key_sorted(self, namespace, key):
        return app.config[self.spaces].find(
                            {"namespace": namespace}, 
                            {"I_S_namespace":1, "namespace": 1, "I_S_codename": 1, "I_S_name": 1, "I_S_type": 1, "intro": 1, "title": 1, "date":1, "epigraph": 1, "points": {"$slice": 1}}
                                        ).sort(key, 1)
    def search(self, expression):
        # return app.config[self.spaces].find(
        #         {
        #         '$text': {'$search': expression, '$language': "ru"}
        #         }, {'score': {'$meta': 'textScore'}})
        return app.config[self.spaces].aggregate([
                            {'$match':{ '$or': [
                                {"points.digest":{'$regex':expression, '$options' : 'i' }}, 
                                {"points.title":{'$regex':expression, '$options' : 'i' }}, 
                                {"points.img_pool.info_imgDesc":{'$regex':expression, '$options' : 'i' }},
                                {"points.sources_pool.title":{'$regex':expression, '$options' : 'i' }}
                                ]}}, 
                            { '$unwind' : "$points" },
                            {'$match':{ '$or': [
                                {"points.digest":{'$regex':expression, '$options' : 'i' }}, 
                                {"points.title":{'$regex':expression, '$options' : 'i' }}, 
                                {"points.img_pool.info_imgDesc":{'$regex':expression, '$options' : 'i' }},
                                {"points.sources_pool.title":{'$regex':expression, '$options' : 'i' }}
                                ]}}
                            ])

    def get_a_space(self, namespace, key):
        return app.config[self.spaces].find_one({"namespace": namespace, "I_S_codename": key})

    def get_points_by_codename(self, codename, namespace):
        return app.config[self.spaces].aggregate([
                            {'$match':{"points.I_S_codenames":codename, "namespace":namespace}}, 
                            { '$unwind' : "$points" },
                            {'$match':{"points.I_S_codenames":codename, "namespace":namespace}}
                            ])

    def get_points_by_geo(self, codename, namespace):
        return app.config[self.spaces].aggregate([
                            {'$match':{"points.info_geo":codename,"namespace":namespace}}, 
                            { '$unwind' : "$points" },
                            {'$match':{"points.info_geo":codename,"namespace":namespace}}
                            ])

    def get_an_object_by_codename(self, codename, namespace):
        return app.config['OBJECTS'].find({"I_S_codename": codename, "namespace": [namespace]})

    def get_objects_by_key_sorted_filter_no(self, val, key, namespace):
        return app.config['OBJECTS'].find({"I_S_type_this": {'$ne': val}, "namespace": [namespace]}, {"I_S_codename": 1, "I_S_name_en": 1, "I_S_name": 1}).sort(key, 1)

    def get_objects_by_key_sorted_filter_yes(self, val, key, namespace):
        return app.config['OBJECTS'].find({"I_S_type_this": val, "namespace":[namespace] }).sort(key, 1)

    def search_objects(self, q, namespace):
        return app.config['OBJECTS'].find({"I_S_codename": {'$regex': "^" + q, '$options': 'i' }, "I_S_type_this": {'$ne': "geo"}}, {"I_S_codename": 1})  # case insensitive

    def search_objects_geo(self, q, namespace):
        return app.config['OBJECTS'].find({"I_S_codename": {'$regex': "^" + q, '$options': 'i' }, "I_S_type_this": "geo"}, {"I_S_codename": 1})  # case insensitive

    def del_an_object(self, codename, namespace):
        return app.config['OBJECTS'].remove({"I_S_codename": codename, "namespace": [namespace]})

    def insert_an_object(self, data):
        app.config['OBJECTS'].insert_one(data)

    def update_an_object(self,_id, data):
        app.config['OBJECTS'].update_one({"_id": ObjectId(_id)}, {'$set': data})

    def get_intros(self):
        return app.config[self.intros].find({"published":1}, {"namespace": 1, "analyst": 1, "subject": 1, "epigraph": 1, "intro": 1})

    def get_an_intro(self, namespace):
        return app.config[self.intros].find_one({"namespace": namespace})

    def get_a_chapter(self, namespace, chapter):
        return app.config[self.spaces].find_one({"namespace": namespace, "I_S_codename": chapter})

    def get_intros_by_author(self, author):
        return app.config[self.intros].find({"analyst": author},{"date":1, "namespace":1}).sort("namespace", 1)

    def get_spaces_by_author(self, author):
        return app.config[self.spaces].find({"analyst": author},{"date":1, "editdate":1, "namespace":1, "title":1, "I_S_codename":1}).sort("date", -1)        

    def get_data_search(self, title, released):
        try:
            return app.config[self.intros].find({
                '$text': {'$search': title},
                }, {'score': {'$meta': 'textScore'}})
        except Exception, e:
            print e

    def get_a_user(self, email):
        return app.config['CORE'].find_one({"email": email})

    def find_intro_by_author(self, author, namespace):
        return app.config[self.intros].find_one({"analyst": author, "namespace": namespace})

    def insert_an_intro(self, data):
        app.config[self.intros].insert_one(data)
        
    def update_an_intro(self, author, namespace, data):
        app.config[self.intros].update_one({"analyst": author, "namespace": namespace}, {'$set': data})

    def insert_a_chapter(self, data):
        app.config[self.spaces].insert_one(data)
        
    def update_a_chapter(self, author, namespace, chapter, data):
        app.config[self.spaces].update_one({"analyst": author, "namespace": namespace, "I_S_codename":chapter}, {'$set': data})

    def del_point_from_a_chapter(self, author, namespace, chapter, point):
        app.config[self.spaces].update_one({ "analyst": author, "namespace": namespace, "I_S_codename":chapter}, { '$pull': { 'points': { "num": float(point) } } } );

    def hide_point_in_a_chapter(self, author, namespace, chapter, point, h):
        app.config[self.spaces].update_one({ "analyst": author, "namespace": namespace, "I_S_codename":chapter, "points.num": float(point) }, { '$set': { 'points.$.is_hidden': h } } );

    def del_srcpool_from_a_chapter(self, author, namespace, chapter, point, src):
        app.config[self.spaces].update_one({ "analyst": author, "namespace": namespace, "I_S_codename":chapter ,'points.num': float(point)}, 
                                        { '$pull': { 'points.$.sources_pool': { "num": float(src) } } } );

    def del_imgpool_from_a_chapter(self, author, namespace, chapter, point, img):
        app.config[self.spaces].update_one({ "analyst": author, "namespace": namespace, "I_S_codename":chapter ,'points.num': float(point) }, 
                                        { '$pull': { 'points.$.img_pool': { "num": float(img) } } } );

    # def put_task(self, data):
    #     app.config['TASKS'].insert_one(data)

