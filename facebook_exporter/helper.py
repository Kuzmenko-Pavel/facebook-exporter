import base64
import html
from uuid import UUID, uuid4
import re
from random import randint

price_clean = re.compile(r'[^0-9.,]')
price_float_dot = re.compile(r'[0-9]+\.[0-9]+')
price_float_comma = re.compile(r'[0-9]+,[0-9]+')
price_int = re.compile(r'[^0-9]')


def redirect_link(url, guid, campaign_guid):
    offer_url = url
    base64_url = base64.urlsafe_b64encode(str('id=%s\nurl=%s\ncamp=%s' % (
        guid,
        offer_url,
        campaign_guid
    )).encode('utf-8'))
    params = 'a=%s&amp;b=%s&amp;c=%s' % (randint(1, 9), base64_url.decode('utf-8'), randint(1, 9))
    return 'https://click.yottos.com/click/fb?%s' % params


def image_link(url):
    url = url.split(',')
    url = [html.escape(x) for x in url]
    return url[0]


def price(p, default=None):
    if default is None:
        default = 0
    if p is None:
        p = '0'
    p = price_clean.sub('', p)
    p = re.sub(r'\.+', ".", p)
    p = re.sub(r',+', ",", p)
    if price_float_dot.match(p):
        try:
            p = float(p)
        except Exception as e:
            p = default
            print('price_float_dot', e)
    elif price_float_comma.match(p):
        try:
            p = p.replace(',', '.')
            p = float(p)
        except Exception as e:
            p = default
            print('price_float_comma', e)
    else:
        p = price_int.sub('', p)
        try:
            p = int(p)
        except Exception as e:
            p = default
            print('int', e)
    if p < default:
        p = default
    p = str(p)
    p = p.replace('.', ',')
    return '%s UAH' % p


def text_normalize(text):
    # words = text.split()
    # upper_words = [word for word in words if word.isupper()]
    # if len(upper_words) >= len(words):
    #     text = text.capitalize()
    return html.escape(text)


def uuid_to_long(uuid):
    try:
        return int(UUID(uuid).int >> 64 & 9223372036854775806)
    except Exception as e:
        print(e)
        return int(uuid4().int >> 64 & 9223372036854775806)