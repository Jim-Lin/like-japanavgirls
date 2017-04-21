#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup as bs
import re
import datetime
import json
import os
import codecs
from multiprocessing import Pool

class ETL:
    root = "/home/shuai/face/"
    root_training = root + "training-images/"
    actress_json = root + 'actress.json'

    def __init__(self):
        with codecs.open(self.actress_json, 'r', 'utf-8') as f:
            try:
                self.dict_actress = json.load(f)
            # if the file is empty the ValueError will be thrown
            except ValueError:
                self.dict_actress = {}

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

                if actress_id not in self.dict_actress:
                    img = actress_a.find("img")
                    actress_img = img.get("src").replace('medium/', '')
                    actress_name = img.get("alt").encode('utf-8')

                    directory = self.root_training + actress_id
                    if not os.path.exists(directory):
                        os.makedirs(directory)

                    os.system('wget ' + actress_img + ' -nc -P ' + directory)
                    self.dict_actress[actress_id] = {"name": unicode(actress_name, 'utf-8'), "img": actress_img}
                    print actress_name
                    print actress_img

        with codecs.open(self.actress_json, 'w', 'utf-8') as f:
            json.dump(self.dict_actress, f, ensure_ascii=False)

    def check_new_actress(self):
        url = "http://actress.dmm.co.jp/-/top/"
        r = requests.get(url)
        soup = bs(r.text)

        act_box = soup.find_all("ul", {"class": "act-box-125 group"})
        actresses = act_box[1].find_all("a")
        for actress in actresses:
            pattern = re.compile("/-/detail/=/actress_id=(.*)/")
            match = pattern.search(actress.get("href"))
            actress_id = match.group(1)
            
            if actress_id not in self.dict_actress:
                actress_img = actress.find("img").get("src")
                actress_name = actress.text.encode('utf-8')

                directory = self.root_training + actress_id
                if not os.path.exists(directory):
                    os.makedirs(directory)

                os.system('wget ' + actress_img + ' -nc -P ' + directory)
                self.dict_actress[actress_id] = {"name": unicode(actress_name, 'utf-8'), "img": actress_img}
                print actress_name
                print actress_img

        with codecs.open(self.actress_json, 'w', 'utf-8') as f:
            json.dump(self.dict_actress, f, ensure_ascii=False)

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
            if actress_id not in self.dict_actress:
                continue

            title_tag  = works.find("td", {"class": "title-monocal"})
            title = title_tag.find("a")
            title_name = title.text
            pattern = re.compile(ur"(^(【数量限定】|【DMM限定】|【DMM限定販売】|【アウトレット】)|（ブルーレイディスク）$)", re.UNICODE)
            match = re.search(pattern, title_name)
            if match:
                continue

            title_url = "http://www.dmm.co.jp" + title.get("href")
            self.get_works_detail(title_url, actress_id)

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

        performer = soup.find("span", {"id": "performer"})
        performer_a_tag = performer.find_all("a")
        if len(performer_a_tag) == 1:
            directory = self.root_training + actress_id
            os.system('wget ' + a_tag.get('href') + ' -nc -P ' + directory)
            print performer_a_tag[0]
            print a_tag.get('href')

            sample_image = soup.find("div", {"id": "sample-image-block"})
            if sample_image is None:
                return

            sample_head = soup.find("div", {"class": "headline mg-b10 lh3"})
            sample_small = sample_head.find("span", {"class": "nw"})
            if sample_small is not None:
                return

            images = map(lambda tag: re.sub(r'-(\d+)', r'jp-\1', tag.get("src")), sample_image.find_all("img"))

            # make the Pool of workers
            pool = Pool()

            # open the urls in their own threads
            pool.map(ParallelFetchSampleImage([directory]), images)

            # close the pool and wait for the work to finish 
            pool.close() 
            pool.join()

class ParallelFetchSampleImage:

    def __init__(self, args):
        self.directory = args[0]

    def __call__(self, image):
        os.system('wget ' + image + ' -nc -P ' + self.directory)
        print image
