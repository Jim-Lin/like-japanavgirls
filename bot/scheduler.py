#!/usr/bin/python
# -*- coding: utf-8 -*-

from etl import ETL
from aws import AWS
import urllib2

if __name__ == "__main__":
    etl = ETL()
    aws = AWS()

    # monthly
    actresses = etl.get_monthly_ranking()

    works = etl.get_new_works()
    for detail in works:
    	print detail.get("img")
    	aws.insert_index_face(detail.get("id"), urllib2.urlopen(detail.get("img")).read())
