import base64


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
