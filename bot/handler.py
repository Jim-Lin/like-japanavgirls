#!/usr/bin/python
# -*- coding: utf-8 -*-

import tornado.web
import json
import requests
import re
import urllib2
from aws import AWS
from dao import DAO
import os
import datetime
from jproperties import Properties

class WebHookHandler(tornado.web.RequestHandler):
    p = Properties()
    with open("token.properties", "rb") as f:
        p.load(f, "utf-8")

    verify_token, metadata = p["verify_token"]
    page_access_token, metadata = p["page_access_token"]
    api_url = 'https://graph.facebook.com/v2.9/me/messages'
    api_headers = {'content-type': 'application/json'}
    images_root = "/var/www/like-av.xyz/images/"

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

                    self.sendTypingMessage(sender, "typing_on")
                    img_bytes = urllib2.urlopen(img_url).read()
                    result = self.aws.search_faces(img_bytes)
                    self.sendTypingMessage(sender, "typing_off")
                    if result is None:
                        self.sendTextMessage(sender, "不是正妹所以找不到")
                    else:
                        pattern = re.compile("https://(.*)/(.*)\?(.*)")
                        match = pattern.search(img_url)
                        img_name = match.group(2)
                        print img_name

                        today = str(datetime.date.today())
                        self.saveImage(today, img_name, img_bytes)

                        face_count = len(result)
                        for i in xrange(2):
                            face = result[i] if face_count > i else None
                            if face is not None:
                                actress = self.dao.find_one_actress_by_id(face.get("id"))
                                if bool(actress):
                                    self.sendImageMessage(sender, face, today + img_name, actress)

            if ("postback" in event and "payload" in event["postback"]):
                payload = event["postback"]["payload"]
                feedback = payload.split(",")
                if feedback[0] == "O":
                    ox = "like"
                    file = self.images_root + feedback[2]
                    with open(file, "rb") as img_file:
                        self.aws.insert_index_face(feedback[1], img_file.read())
                else:
                    ox = "unlike"

                self.dao.update_one_feedback_by_id(feedback[1], ox, feedback[2])
                self.sendTextMessage(sender, "感謝回饋")

    def saveImage(self, today, img_name, img_bytes):
        directory = self.images_root + today + "/"
        if not os.path.exists(directory):
            os.makedirs(directory)

        f = open(directory + img_name,'wb')
        f.write(img_bytes)
        f.close()

    def sendTextMessage(self, sender, text):
        if len(text) <= 0:
          return

        data = {
            "recipient": {"id": sender},
            "message": {"text": text}
        }
        params = {"access_token": self.page_access_token}

        r = requests.post(self.api_url, params=params, data=json.dumps(data), headers=self.api_headers)

    def sendImageMessage(self, sender, face, img_name, actress):
        attachment = {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {
                        "title": actress.get("name"),
                        "image_url": actress.get("img"),
                        "subtitle": "相似度: " + str(round(face.get("similarity"), 2)) + "%",
                        "default_action": {
                          "type": "web_url",
                          # "url": "http://www.dmm.co.jp/mono/dvd/-/list/=/article=actress/id=" + face.get("id") + "/sort=date/",
                          "url": "http://sp.dmm.co.jp/mono/list/index/shop/dvd/article/actress/id/" + face.get("id") + "/sort/date",
                          # "url": "http://www.r18.com/videos/vod/movies/list/id=" + face.get("id") + "/sort=new/type=actress/",
                          "webview_height_ratio": "compact"
                        },
                        "buttons": [
                            # {
                            #     "type": "web_url",
                            #     "url": "http://sukebei.nyaa.se/?page=search&term=" + actress.get("name"),
                            #     "title": "去找片"
                            # },
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

    def sendTypingMessage(self, sender, action):
        data = {
            "recipient": {"id": sender},
            "sender_action": action
        }
        params = {"access_token": self.page_access_token}

        r = requests.post(self.api_url, params=params, data=json.dumps(data), headers=self.api_headers)
