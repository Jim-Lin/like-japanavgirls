#!/usr/bin/python
# -*- coding: utf-8 -*-

from pymongo import MongoClient, IndexModel
from jproperties import Properties
import os

class DAO:

    def __init__(self, *args, **kwargs):
        p = Properties()
        with open(os.path.dirname(os.path.realpath(__file__)) + "/mongodb.properties", "rb") as f:
            p.load(f, "utf-8")

        self.username, metadata = p["username"]
        self.password, metadata = p["password"]

    def update_one_feedback_by_id(self, id, ox, image):
        db = db()
        collection = db['actress']
        result = collection.update_one({"id": id}, {'$inc': {'count': 1}, '$push': {ox: image}}, upsert=True)

    def update_one_works_by_id(self, id, no):
        db = self.get_db()
        collection = db['actress']
        result = collection.update_one({"id": id}, {'$push': {"works": no}}, upsert=True)

    def find_one_works_by_id(self, id):
        db = self.get_db()
        collection = db['actress']
        return collection.find_one({"id": id}, {"works": True, "_id": False})

    def update_one_info_by_actress(self, actress):
        db = self.get_db()
        collection = db['actress']
        collection.create_index('id', unique=True)
        result = collection.update_one({"id": actress.get("id")}, {'$set': {"id": actress.get("id"), "name": actress.get("name"), "img": actress.get("img")}}, upsert=True)

    def find_one_actress_by_id(self, id):
        db = self.get_db()
        collection = db['actress']
        return collection.find_one({"id": id}, {"_id": False})

    def get_db(self):
        client = MongoClient('mongodb://' + self.username + ':' + self.password + '@localhost:27017/dark')
        return client['dark']
