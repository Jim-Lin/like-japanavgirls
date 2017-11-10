#!/usr/bin/python
# -*- coding: utf-8 -*-

from pymongo import MongoClient, IndexModel
from jproperties import Properties

class DAO:

    def __init__(self, *args, **kwargs):
        #args -- tuple of anonymous arguments
        #kwargs -- dictionary of named arguments
        if kwargs.get('mongo') is None:
            self.default_mongo_init()
        else:
            self.mongo = MongoClient(kwargs.get('mongo').get('host'), kwargs.get('mongo').get('port'))
            self.mongo_db = self.mongo[kwargs.get('mongo').get('db')]

    def default_mongo_init(self):
        p = Properties()
        with open("mongodb.properties", "rb") as f:
            p.load(f, "utf-8")

        username, metadata = p["username"]
        password, metadata = p["password"]
        self.mongo = MongoClient('mongodb://' + username + ':' + password + '@localhost:27017/dark')
        self.mongo_db = self.mongo['dark']
        self.mongo_db['actress'].create_index('id', unique=True)

    def update_one_feedback_by_id(self, id, ox, image):
        collection = self.mongo_db['actress']
        result = collection.update_one({"id": id}, {'$inc': {'count': 1}, '$push': {ox: image}}, upsert=True)

    def update_one_works_by_id(self, id, no):
        collection = self.mongo_db['actress']
        result = collection.update_one({"id": id}, {'$push': {"works": no}}, upsert=True)

    def find_one_works_by_id(self, id):
        collection = self.mongo_db['actress']
        return collection.find_one({"id": id}, {"works": True, "_id": False})

    def update_one_info_by_actress(self, actress):
        collection = self.mongo_db['actress']
        result = collection.update_one({"id": actress.get("id")}, {'$set': {"id": actress.get("id"), "name": actress.get("name"), "img": actress.get("img")}}, upsert=True)

    def find_one_actress_by_id(self, id):
        collection = self.mongo_db['actress']
        return collection.find_one({"id": id}, {"_id": False})
