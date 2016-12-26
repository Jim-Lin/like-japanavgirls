#!/usr/bin/python
# -*- coding: utf-8 -*-

from etl import ETL
from aws import AWS

if __name__ == "__main__":
    etl = ETL()
    aws = AWS()

    # monthly
    actresses = etl.get_monthly_ranking()
    aws.insert_index_faces_actresses(actresses)

    works = etl.get_new_works()
    aws.insert_index_faces_works(works)
