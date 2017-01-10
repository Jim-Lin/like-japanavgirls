#!/usr/bin/python
# -*- coding: utf-8 -*-

from etl import ETL

if __name__ == "__main__":
    etl = ETL()

    # monthly
    etl.check_monthly_ranking()

    # daily
    etl.check_new_works()
