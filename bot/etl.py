#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup as bs
import re
from dao import DAO
import datetime
from aws import AWS
import urllib2

class ETL:

    def __init__(self):
        self.dao = DAO()
        self.aws = AWS()

    def check_monthly_ranking(self):
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

                detail =  self.dao.find_one_actress_by_id(actress_id)
                if detail is None or detail.get("name") is None:
                    img = actress_a.find("img")
                    actress_img = img.get("src").replace('medium/', '')
                    actress_name = img.get("alt").encode('utf-8')
                    print actress_name

                    self.dao.update_one_info_by_actress({"id": actress_id, "name": actress_name, "img": actress_img})
                    self.aws.insert_index_face(actress_id, urllib2.urlopen(actress_img).read())

    def check_new_actress(self):
        self.get_new_actress("http://actress.dmm.co.jp/-/top/", "act-box-125 group", 1, "/-/detail/=/actress_id=(.*)/")
        self.get_new_actress("http://www.dmm.co.jp/mono/dvd/-/actress/", "act-box-100 group mg-b20", 0, "/mono/dvd/-/list/=/article=actress/id=(.*)/")

    def get_new_actress(self, url, cssClass, index, hrefPattern):
        r = requests.get(url)
        soup = bs(r.text)

        act_box = soup.find_all("ul", {"class": cssClass})
        actresses = act_box[index].find_all("a")
        for actress in actresses:
            pattern = re.compile(hrefPattern)
            match = pattern.search(actress.get("href"))
            actress_id = match.group(1)

            detail =  self.dao.find_one_actress_by_id(actress_id)
            if detail is None or detail.get("name") is None:
                actress_img = actress.find("img").get("src").replace('medium/', '')
                actress_name = actress.text.encode('utf-8')
                print actress_name

                self.dao.update_one_info_by_actress({"id": actress_id, "name": actress_name, "img": actress_img})
                self.aws.insert_index_face(actress_id, urllib2.urlopen(actress_img).read())

    def check_new_works(self):
        now = datetime.datetime.now()
        year = str(now.year)
        month = str(now.month)
        day = str(now.day)
        url = "http://www.dmm.co.jp/mono/dvd/-/calendar/=/month=" + month + "/year=" + year + "/day=" + day + "-" + day + "/"
        r = requests.get(url)
        soup = bs(r.text)
        print datetime.date.today()

        cal = soup.find("table", {"id": "monocal"})
        works_list = cal.find_all("tr")
        if len(works_list) == 0:
            return

        for works in works_list:
            actress_tag  = works.find("td", {"class": "info-01"})
            if actress_tag is None or actress_tag.text == "----":
                continue

            pattern = re.compile("/mono/dvd/-/list/=/article=actress/id=(.*)/")
            match = pattern.search(actress_tag.find("a").get("href"))
            actress_id = match.group(1)
            if self.dao.find_one_actress_by_id(actress_id) is None:
                continue

            title_tag  = works.find("td", {"class": "title-monocal"})
            title = title_tag.find("a")
            title_name = title.text
            pattern = re.compile(ur"(^(【数量限定】|【DMM限定】|【DMM限定販売】|【アウトレット】|【特選アウトレット】)|（ブルーレイディスク）$)", re.UNICODE)
            match = re.search(pattern, title_name)
            if match:
                continue

            title_url = "http://www.dmm.co.jp" + title.get("href")
            detail = self.get_works_detail(title_url, actress_id)
            if detail is None:
                continue
            else:
                print detail.get("img")
                self.aws.insert_index_face(detail.get("id"), urllib2.urlopen(detail.get("img")).read())

    def get_works_detail(self, url, actress_id):
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
            pattern = re.compile("/mono/dvd/-/detail/=/cid=(.*)/")
            match = pattern.search(url)
            cid = match.group(1)
            print cid

            project_works = self.dao.find_one_works_by_id(actress_id)
            print project_works

            if bool(project_works) and any(cid in s for s in project_works.get("works")):
                return
            else:
                self.dao.update_one_works_by_id(actress_id, cid)
                self.get_sample(soup, actress_id)
                return {"id": actress_id, "img": a_tag.get('href')}
        else:
            return

    def get_sample(self, soup, actress_id):
        sample_image = soup.find("div", {"id": "sample-image-block"})
        if sample_image is None:
            return

        sample_head = soup.find("div", {"class": "headline mg-b10 lh3"})
        sample_small = sample_head.find("span", {"class": "nw"})
        if sample_small is not None:
            return

        images = map(lambda tag: re.sub(r'-(\d+)', r'jp-\1', tag.get("src")), sample_image.find_all("img"))
        for image in images:
            print image
            self.aws.insert_index_face(actress_id, urllib2.urlopen(image).read())
