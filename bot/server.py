#!/usr/bin/python
# -*- coding: utf-8 -*-

import tornado.ioloop
import tornado.web
import tornado.httpserver
from handler import WebHookHandler

application = tornado.web.Application([
    (r"/webhook", WebHookHandler)
])

if __name__ == "__main__":
    server = tornado.httpserver.HTTPServer(application)
    server.bind(5000)
    server.start(0)  # Forks multiple sub-processes
    tornado.ioloop.IOLoop.current().start()
