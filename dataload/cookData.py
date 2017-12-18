#!/usr/bin/python
import re, os, sys
from pymongo import MongoClient
from datetime import datetime


class DBcall(object):
    SECRET_KEY = 'devil in the sky'
    DATABASE = MongoClient()['w4a']

    def __init__(self, collection):
        self.client = self.DATABASE[collection]

    def loadData(self, data):
        for doc in data:
            try:
                self.client.insert_one(doc)
            except Exception, e:
                print "Load to DB failed: " + str(e)

    def updateDatapull(self, keys, values):
        try:
            self.client.update_one(keys, {'$addToSet': values})
        except Exception, e:
            print "Update DB record failed: " + str(e)

    def findData(self, keys):
        return self.client.find_one(keys)

    def findDatalist(self, keys):
        return self.client.find(keys)


def readData_json(file):
    json = {}
    with open(file, "r") as ff:
        errors = []

    return json


def is_match(coll, keys):
    if DBcall(coll).findData(keys):
        return 1
    return 0
