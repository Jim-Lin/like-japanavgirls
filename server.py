#!/usr/bin/python
# -*- coding: utf-8 -*-

import tornado.httpserver
import tornado.ioloop
from handler import WebHookHandler

application = tornado.web.Application([
    (r"/webhook", WebHookHandler)
])

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application, ssl_options={
        "certfile": "/etc/tornado/ssl/tornado.csr",
        "keyfile": "/etc/tornado/ssl/tornado.key",
    })
    http_server.listen(443)
    tornado.ioloop.IOLoop.instance().start()
