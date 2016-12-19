#!/usr/bin/python
# -*- coding: utf-8 -*-

import tornado.web
import json
import requests

class WebHookHandler(tornado.web.RequestHandler):
    verify_token = <VERIFY_TOKEN>
    page_access_token = <PAGE_ACCESS_TOKEN>

    def get(self):
        if self.get_argument("hub.verify_token", "") == self.verify_token:
            self.write(self.get_argument("hub.challenge", ""));
        else:
            self.write('Error, wrong validation token');

    def post(self):
        print "receive!"
        data = json.loads(self.request.body)
        print data
        messaging_events = data["entry"][0]["messaging"]
        text = ""
        for event in messaging_events:
            sender = event["sender"]["id"];
            if ("message" in event and "text" in event["message"]):
                text = event["message"]["text"];
                self.sendTextMessage(sender, text)

    def sendTextMessage(self, sender, text):
        if len(text) <= 0:
          return
        
        url = 'https://graph.facebook.com/v2.6/me/messages'
        headers = {'content-type': 'application/json'}
        data = {
            "recipient": {"id": sender},
            "message": {"text": "echo: " + text}
        }
        params = {"access_token": self.page_access_token}

        r = requests.post(url, params=params, data=json.dumps(data), headers=headers)
