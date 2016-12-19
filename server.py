#!/usr/bin/python
# -*- coding: utf-8 -*-

import tornado.ioloop
import json
from handler import WebHookHandler

application = tornado.web.Application([
    (r"/webhook", WebHookHandler)
])

if __name__ == "__main__":
    application.listen(5000)
    tornado.ioloop.IOLoop.instance().start()
