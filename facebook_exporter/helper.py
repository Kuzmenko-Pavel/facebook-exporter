import base64
import re

price_clean = re.compile(r'[^0-9]')


def redirect_link(url, guid, campaign_guid):
    offer_url = url
    base64_url = base64.urlsafe_b64encode(str('id=%s\nurl=%s\ncamp=%s' % (
        guid,
        offer_url,
        campaign_guid
    )).encode('utf-8'))
    return 'https://click.yottos.com/click/fb?%s' % base64_url.decode('utf-8')


def image_link(url):
    url = url.split(',')
    return url[0]


def price(p):
    p = price_clean.sub('', p)
    return '%s UAH' % p
