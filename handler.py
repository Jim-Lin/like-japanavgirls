#!/usr/bin/python
# -*- coding: utf-8 -*-

import tornado.web
import json
import requests
import re
import urllib2
from aws import AWS
from dao import DAO

class WebHookHandler(tornado.web.RequestHandler):
    verify_token = <VERIFY_TOKEN>
    page_access_token = <PAGE_ACCESS_TOKEN>
    api_url = 'https://graph.facebook.com/v2.6/me/messages'
    api_headers = {'content-type': 'application/json'}

    aws = AWS()
    dao = DAO()

    def get(self):
        if self.get_argument("hub.verify_token", "") == self.verify_token:
            self.write(self.get_argument("hub.challenge", ""))
        else:
            self.write('Error, wrong validation token')

    def post(self):
        print "receive!"

        data = json.loads(self.request.body)
        print data

        messaging_events = data["entry"][0]["messaging"]
        text = ""
        for event in messaging_events:
            sender = event["sender"]["id"]
            if ("message" in event and "text" in event["message"]):
                text = event["message"]["text"]
                self.sendTextMessage(sender, "給我正妹圖片")

            if ("message" in event and "attachments" in event["message"]):
                attachments = event["message"]["attachments"]
                print attachments

                if attachments[0]["type"] == "image":
                    img_url = attachments[0]["payload"]["url"]
                    print img_url

                    img_bytes = urllib2.urlopen(img_url).read()
                    result = self.aws.search_face(img_bytes)
                    if result is None:
                        self.sendTextMessage(sender, "不是正妹所以找不到")
                    else:
                        pattern = re.compile("https://(.*)/(.*)\?(.*)")
                        match = pattern.search(img_url)
                        img_name = match.group(2)
                        print img_name

                        f = open(r"/var/www/like-av.xyz/images/" + img_name,'wb')
                        f.write(img_bytes)
                        f.close()

                        self.sendImageMessage(sender, result, img_name)

            if ("postback" in event and "payload" in event["postback"]):
                payload = event["postback"]["payload"]
                feedback = payload.split(",")
                if feedback[0] == "O":
                    ox = "like"
                else:
                    ox = "unlike"

                self.dao.update_one_actress_by_id(feedback[1], ox, feedback[2])
                self.sendTextMessage(sender, "感謝回饋")

    def sendTextMessage(self, sender, text):
        if len(text) <= 0:
          return

        data = {
            "recipient": {"id": sender},
            "message": {"text": text}
        }
        params = {"access_token": self.page_access_token}

        r = requests.post(self.api_url, params=params, data=json.dumps(data), headers=self.api_headers)

    def sendImageMessage(self, sender, face, img_name):
        actress = self.dao.hgetall_actress_by_id(face.get("id"))
        attachment = {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {
                        "title": actress.get("name"),
                        "image_url": actress.get("img"),
                        "subtitle": "↑↑↑ 壓我 ↑↑↑\n　\n相似度: " + str(round(face.get("similarity"), 2)) + "%",
                        "default_action": {
                          "type": "web_url",
                          "url": "http://www.dmm.co.jp/mono/dvd/-/list/=/article=actress/id=" + face.get("id") + "/sort=date/",
                          # "url": "http://www.r18.com/videos/vod/movies/list/id=" + face.get("id") + "/sort=new/type=actress/",
                          "webview_height_ratio": "compact"
                        },
                        "buttons": [
                            {
                                "type": "postback",
                                "title": "O 覺得像",
                                "payload": "O," + face.get("id") + "," + img_name
                            },
                            {
                                "type": "postback",
                                "title": "X 差很多",
                                "payload": "X," + face.get("id") + "," + img_name
                            }         
                        ]      
                    }
                ]
            }
        }

        data = {
            "recipient": {"id": sender},
            "message": {"attachment": attachment}
        }
        params = {"access_token": self.page_access_token}

        r = requests.post(self.api_url, params=params, data=json.dumps(data), headers=self.api_headers)
