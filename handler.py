#!/usr/bin/python
# -*- coding: utf-8 -*-

import tornado.web

class WebHookHandler(tornado.web.RequestHandler):
    verify_token = <VERIFY_TOKEN>

    def get(self):
        if self.get_argument("hub.verify_token", "") == self.verify_token:
            self.write(self.get_argument("hub.challenge", ""));
        else:
            self.write('Error, wrong validation token');
