#!/usr/bin/python
# -*- coding: utf-8 -*-

import redis

class DAO:

    def __init__(self, *args, **kwargs):
        #args -- tuple of anonymous arguments
        #kwargs -- dictionary of named arguments
        if len(kwargs) == 0:
            self.r = redis.StrictRedis(host='localhost', port=6379, db=0)
        else:
            self.r = redis.StrictRedis(host=kwargs.get('host'), port=kwargs.get('port'), db=kwargs.get('db'))

    def insert_actresses(self, actresses):
        for actress in actresses:
            if not self.r.exists(actress.get("id")):
                self.r.hmset(actress.get("id"), actress)

    def get_actress_by_id(self, id):
        return self.r.hget(id)
