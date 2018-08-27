# -*- coding: UTF-8 -*-
__author__ = 'kuzmenko-pavel'
from pyramid_celery import celery_app as app
import transaction
import os
from shutil import move
import time
import html
from facebook_exporter.helper import redirect_link, image_link


tpl_xml_start = '''<?xml version="1.0"?>\n<rss xmlns:g="http://base.google.com/ns/1.0" version="2.0">\n<channel>
<title></title>\n<link>https://yottos.com</link>\n<description></description>'''

tpl_xml_offer = '''\n<item>\n<g:id>%s</g:id>\n<g:title>%s</g:title>\n<g:description>%s</g:description>
<g:link>%s</g:link>\n<g:image_link>%s</g:image_link>\n<g:price>%s</g:price>\n<g:condition>new</g:condition>
<g:availability>in stock</g:availability>
<g:gtin>2112345678900</g:gtin>
<g:brand>yottos.com</g:brand>
</item>'''
tpl_xml_end = '''\n</channel>\n</rss>'''


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
        count = 2000000
        q = '''
                        SELECT TOP %s  
                        View_Lot.LotID AS LotID,
                        View_Lot.Title AS Title,
                        ISNULL(View_Lot.Descript, '') AS Description,
                        ISNULL(View_Lot.Price, '0') Price,
                        View_Lot.ExternalURL AS UrlToMarket,
                        View_Lot.ImgURL 
                        FROM View_Lot 
                        INNER JOIN LotByAdvertise ON LotByAdvertise.LotID = View_Lot.LotID
                        INNER JOIN View_Advertise ON View_Advertise.AdvertiseID = LotByAdvertise.AdvertiseID
                        WHERE View_Advertise.AdvertiseID = '%s' AND View_Lot.ExternalURL <> '' 
                            AND View_Lot.isTest = 1 AND View_Lot.isAdvertising = 1
                        ''' % (count, id)

        dbsession = app.conf['PYRAMID_REGISTRY']['dbsession_factory']()
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static/xml')
        file_path = os.path.join(dir_path, id + ".xml")
        temp_file = file_path + '.' + str(int(time.time()))
        with open(temp_file, 'w') as f:
            f.write(tpl_xml_start)
            with transaction.manager:
                    result = dbsession.execute(q)
                    for offer in result:
                        try:
                            data = tpl_xml_offer % (
                                offer[0],
                                html.escape(offer[1]),
                                html.escape(offer[2]),
                                offer[3],
                                redirect_link(offer[4], offer[0], id),
                                image_link(offer[5])
                            )
                        except Exception as e:
                            print(e)
                        else:
                            f.write(data)
            f.write(tpl_xml_end)
            os.fsync(f)

        move(temp_file, file_path)
