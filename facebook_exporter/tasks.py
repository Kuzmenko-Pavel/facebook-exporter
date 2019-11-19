# -*- coding: UTF-8 -*-
__author__ = 'kuzmenko-pavel'
import os
import time
from shutil import move
from random import choice

from pyramid_celery import celery_app as app

from facebook_exporter.helper import redirect_link, image_link, price, text_normalize
from facebook_exporter.models import ParentCampaign, ParentOffer, ParentBlock


tpl_xml_start = '''<?xml version="1.0"?>\n<rss xmlns:g="http://base.google.com/ns/1.0" version="2.0">\n<channel>
<title></title>\n<link>https://yottos.com</link>\n<description></description>'''

tpl_xml_offer = '''\n<item>\n<g:id>%s</g:id>\n<g:title>%s</g:title>\n<g:description>%s</g:description>
<g:link>%s</g:link>\n<g:image_link>%s</g:image_link>\n<g:price>%s</g:price>\n<g:condition>new</g:condition>
<g:availability>in stock</g:availability>
<g:google_product_category>111</g:google_product_category>
<g:gtin>2112345678900</g:gtin>
<g:brand>yottos.com</g:brand>
</item>'''
tpl_xml_end = '''\n</channel>\n</rss>'''


@app.task(ignore_result=True)
def check_feed(id):
    print('START RECREATE FEED')
    dbsession = app.conf['PYRAMID_REGISTRY']['dbsession_factory']()
    result = dbsession.query(ParentCampaign)
    if id:
        result = result.filter(ParentCampaign.id == id)
    for adv in result.all():
        create_feed.delay(str(adv.guid).upper())
    dbsession.commit()
    print('STOP RECREATE FEED')


@app.task(ignore_result=True)
def create_feed(id):
    print('START CREATE FEED %s' % id)
    dbsession = app.conf['PYRAMID_REGISTRY']['dbsession_factory']()
    campaign = dbsession.query(ParentCampaign).filter(ParentCampaign.guid == id).one_or_none()
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static/xml')
    file_path = os.path.join(dir_path, id + ".xml")
    temp_file = file_path + '.' + str(int(time.time()))
    line = 0
    with open(temp_file, 'w', encoding='utf-8', errors='xmlcharrefreplace') as f:
        f.write(tpl_xml_start)
        f.flush()
        blocks = dbsession.query(ParentBlock).limit(10).all()
        if campaign:
            for offer in dbsession.query(ParentOffer).filter(ParentOffer.id_campaign == campaign.id).all():
                data = ''
                try:
                    offer_id = '%s...%s' % (str(offer.guid).upper(), str(offer.guid_account).upper())
                    if offer.id_retargeting:
                        offer_id = '%s...%s' % (offer.id_retargeting, str(offer.guid_account).upper())
                    data = tpl_xml_offer % (
                        offer_id,
                        text_normalize(str(offer.title)),
                        text_normalize(str(offer.description)),
                        redirect_link(offer, campaign, choice(blocks)),
                        image_link(offer.images[0]),
                        price(offer.price)
                    )
                except Exception as e:
                    print(e)
                else:
                    f.write(data)
                line += 1
                if line % 1000 == 0:
                    print('Writen %d offers' % line)
                    f.flush()
            f.flush()
            f.write(tpl_xml_end)
            f.flush()
    dbsession.commit()
    move(temp_file, file_path)
    print('STOP CREATE FEED %s on %d offers' % (id, line))
