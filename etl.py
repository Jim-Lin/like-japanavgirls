#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup as bs
import re

class ETL:

    def get_monthly_ranking(self):
        count = 0
        ranking = []
        intervals = ["1_20", "21_40", "41_60", "61_80", "81_100"]
        for interval in intervals:
            url = "http://www.dmm.co.jp/mono/dvd/-/ranking/=/term=monthly/mode=actress/rank=" + interval
            r = requests.get(url)
            soup = bs(r.text)
            actresses = soup.find_all("td", {"class": "bd-b"})
            for actress in actresses:
                actress_a = actress.find("a")
                pattern = re.compile("/mono/dvd/-/list/=/article=actress/id=(.*)/")
                match = pattern.search(actress_a.get("href"))
                actress_id = match.group(1)
                actress_img = actress_a.find("img").get("src")

                actress_data = actress.find("div", {"class": "data"}).find("p").find("a")
                actress_name = actress_data.text
                # actress_url = "http://www.dmm.co.jp" + actress_data.get("href") # + "sort=date/"

                ranking.append({"id": actress_id, "name": actress_name, "img": actress_img})
                count += 1

        return ranking
