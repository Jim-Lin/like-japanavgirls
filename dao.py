#!/usr/bin/python
# -*- coding: utf-8 -*-

import redis
from pymongo import MongoClient, IndexModel

class DAO:

    def __init__(self, *args, **kwargs):
        #args -- tuple of anonymous arguments
        #kwargs -- dictionary of named arguments
        if kwargs.get('redis') is None:
            self.r = redis.StrictRedis(host='localhost', port=6379, db=0)
        else:
            self.r = redis.StrictRedis(host=kwargs.get('redis').get('host'), port=kwargs.get('redis').get('port'), db=kwargs.get('redis').get('db'))

        if kwargs.get('mongo') is None:
            self.default_mongo_init()
        else:
            self.mongo = MongoClient(kwargs.get('mongo').get('host'), kwargs.get('mongo').get('port'))
            self.mongo_db = self.mongo[kwargs.get('mongo').get('db')]

    def default_mongo_init(self):
        self.mongo = MongoClient('mongodb://localhost:27017/')
        self.mongo_db = self.mongo['dark']
        self.mongo_db['actress'].create_index('id', unique=True)

    def hmset_actresses(self, actresses):
        for actress in actresses:
            if not self.r.exists(actress.get("id")):
                self.r.hmset(actress.get("id"), actress)

    def is_actress_exists_by_id(self, id):
        return self.r.exists(id)

    def hgetall_actress_by_id(self, id):
        return self.r.hgetall(id)

    def update_one_feedback_by_id(self, id, ox, image):
        collection = self.mongo_db['actress']
        result = collection.update_one({"id": id}, {'$inc': {'count': 1}, '$push': {ox: image}}, upsert=True)

    def update_one_works_by_id(self, id, no):
        collection = self.mongo_db['actress']
        result = collection.update_one({"id": id}, {'$push': {"works": no}}, upsert=True)

    def find_one_works_by_id(self, id):
        collection = self.mongo_db['actress']
        return collection.find_one({"id": id}, {"works": True, "_id": False})
