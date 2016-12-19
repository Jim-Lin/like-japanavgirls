#!/usr/bin/python
# -*- coding: utf-8 -*-

from etl import ETL
from dao import DAO
from aws import AWS

if __name__ == "__main__":
    etl = ETL()
    actresses = etl.get_monthly_ranking()

    dao = DAO()
    dao.insert_actresses(actresses)

    aws = AWS()
    aws.insert_index_faces(actresses)
