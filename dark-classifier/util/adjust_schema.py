#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup as bs
import re
import json
import codecs

root = "/home/shuai/face/"
actress_json = root + 'actress.json'

if __name__ == "__main__":
    with codecs.open(actress_json, 'r', 'utf-8') as f:
        try:
            dict_actress = json.load(f)
        # if the file is empty the ValueError will be thrown
        except ValueError:
            dict_actress = {}

    for actress_id in dict_actress:
        url = "http://actress.dmm.co.jp/-/detail/=/actress_id=" + actress_id + "/"
        r = requests.get(url)
        soup = bs(r.text)

        tr = soup.find("tr", {"class": "area-av30"})
        img = tr.find("img")
        actress_img = img.get("src")
        actress_name = img.get("alt").encode('utf-8')

        dict_actress[actress_id] = {"name": unicode(actress_name, 'utf-8'), "img": actress_img}
        print actress_name
        print actress_img

    with codecs.open(actress_json, 'w', 'utf-8') as f:
        json.dump(dict_actress, f, ensure_ascii=False)
