#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup as bs
import re
from dao import DAO
import datetime

class ETL:

    def __init__(self):
        self.dao = DAO()

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

        self.dao.hmset_actresses(ranking)
        return ranking

    def get_new_works(self):
        day = str(datetime.datetime.now().day)
        url = "http://www.dmm.co.jp/mono/dvd/-/calendar/=/day=" + day + "-" + day + "/"
        r = requests.get(url)
        soup = bs(r.text)
        
        cal = soup.find("table", {"id": "monocal"})
        works_list = cal.find_all("tr")
        if len(works_list) == 0:
            return

        new_works = list()
        for works in works_list:
            actress_tag  = works.find("td", {"class": "info-01"})
            if actress_tag is None or actress_tag.text == "----":
                continue

            title_tag  = works.find("td", {"class": "title-monocal"})
            title = title_tag.find("a")
            title_name = title.text
            pattern = re.compile(ur"(^(【数量限定】|【DMM限定】|【アウトレット】)|（ブルーレイディスク）$)", re.UNICODE)
            match = re.search(pattern, title_name)
            if match:
                continue

            title_url = "http://www.dmm.co.jp" + title.get("href")
            detail = self.get_works_detail(title_url)
            if detail is None:
                continue
            else:
                new_works.append(detail)

        return new_works

    def get_works_detail(self, url):
        r = requests.get(url)
        soup = bs(r.text)
        
        sample = soup.find("div", {"class": "tx10 pd-3 lh4"})
        if sample is None:
            return
        
        # No Image
        a_tag = sample.find("a")
        if a_tag is None:
            return

        print a_tag.get('href')

        performer = soup.find("span", {"id": "performer"})
        performer_a_tag = performer.find_all("a")
        if len(performer_a_tag) == 1:
            actress_url = performer_a_tag[0].get("href")
            pattern = re.compile("/mono/dvd/-/list/=/article=actress/id=(.*)/")
            match = pattern.search(actress_url)
            actress_id = match.group(1)
            print actress_id
            
            if self.dao.is_actress_exists_by_id(actress_id):
                pattern = re.compile("/mono/dvd/-/detail/=/cid=(.*)/")
                match = pattern.search(url)
                cid = match.group(1)
                print cid

                works = self.dao.find_one_works_by_id(actress_id)
                print works

                if works is not None and cid in works:
                    return
                else:
                    self.dao.update_one_works_by_id(actress_id, cid)
                    return {"id": actress_id, "img": a_tag.get('href')}
            else:
                return
        else:
            return
