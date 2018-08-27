# -*- coding: UTF-8 -*-
__author__ = 'kuzmenko-pavel'
from pyramid_celery import celery_app as app
import transaction


@app.task(ignore_result=True)
def check_feed():
        dbsession = app.conf['PYRAMID_REGISTRY']['dbsession_factory']()
        with transaction.manager:
                result = dbsession.execute('''SELECT
                                              a.AdvertiseID AS AdvertiseID
                                              FROM Advertise a
                                              LEFT OUTER JOIN MarketByAdvertise mark ON mark.AdvertiseID = a.AdvertiseID
                                              where MarketID is not NULL
                                                ''')
                for adv in result:
                        create_feed.delay(adv[0])


@app.task(ignore_result=True)
def create_feed(id):
        print(id)