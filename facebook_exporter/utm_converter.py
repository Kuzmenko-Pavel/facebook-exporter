__all__ = ['UtmConverter']
from trans import trans
from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse, quote
import random


class UtmConverter:
    source = 'fb'
    utm_default = 'yottos_cpcf'
    utm_source = 'yottos_cpcf'
    utm_campaign = 'yottos'
    utm_medium = 'cpcf'
    utm_content = 'cpcf'
    utm_term = 'yottos'
    utm_rand = str(random.randint(0, 1000000))

    makros = ['{source}', '{source_id}', '{source_guid}', '{campaign}', '{campaign_id}', '{campaign_guid}', '{name}',
              '{offer}', '{offer_id}', '{offer_guid}', '{rand}']

    def __init__(self, offer, campaign, block):
        self.raw_url = offer.url
        self.id_offer = str(offer.id)
        self.id_block = str(block.id)
        self.guid_block = str(block.guid)
        self.id_campaign = str(campaign.id)
        self.id_site = str(block.id_site)
        self.offer_name = self.trans(str(offer.title))
        self.site_name = self.trans(str(block.site_name))
        self.campaign_name = self.trans(str(campaign.name))
        self.utm = bool(campaign.utm)
        self.utm_human_data = bool(campaign.utm_human_data)

    @staticmethod
    def char_replace(string, chars=None, to_char=None):
        if chars is None:
            chars = [' ', '.', ',', ';', '!', '?', ':']
        if to_char is None:
            to_char = '_'
        for ch in chars:
            if ch in string:
                string = string.replace(ch, to_char)
        return string.lower()

    def trans(self, string):
        try:
            return trans(self.char_replace(string))
        except Exception:
            return string

    def get_source(self):
        if self.utm_human_data:
            return self.site_name
        return self.guid_block

    def get_source_id(self):
        return self.id_block

    def get_campaign(self):
        return self.campaign_name

    def get_campaign_id(self):
        return self.id_campaign

    def get_offer(self):
        return self.offer_name

    def get_offer_id(self):
        return self.id_offer

    def get_rand(self):
        return self.utm_rand

    def get_utm_source(self):
        return self.get_source()

    def get_utm_campaign(self):
        return self.get_campaign()

    def get_utm_content(self):
        return self.get_offer()

    def get_utm_medium(self):
        return self.utm_medium

    def get_utm_term(self):
        return self.get_source_id()

    def get_utm_rand(self):
        return self.get_rand()

    def get_default_utm(self, name):
        return self.utm_default

    def __add_makros(self, params, values):
        for key, value in params.items():
            for i in self.makros:
                value = value.replace(i, values.get(i, self.get_default_utm(i)))
            params[key] = value
        return urlencode(params, quote_via=quote)

    def utm_exist(self, key, params):
        if key == 'utm_medium':
            return False
        return key in params

    def __add_utm(self, params, keys):
        for key, value in keys.items():
            if not self.utm_exist(key, params):
                params[key] = value
        return urlencode(params, quote_via=quote)

    def get_makros_values(self):
        return {
            '{source}': self.get_source(),
            '{source_id}': self.get_source_id(),
            '{campaign}': self.get_campaign(),
            '{campaign_id}': self.get_campaign_id(),
            '{offer}': self.get_offer(),
            '{offer_id}': self.get_offer_id(),
            '{rand}': self.get_rand()
        }

    def get_utm_keys(self):
        return {
            'utm_medium': self.get_utm_medium(),
            'utm_source': self.get_utm_source(),
            'utm_campaign': self.get_utm_campaign(),
            'utm_content': self.get_utm_content(),
            'utm_term': self.get_utm_term(),
        }

    def __add_dynamic_param(self, url):
        try:
            values = self.get_makros_values()
            url_parts = list(urlparse(url))

            params = dict(parse_qsl(url_parts[3]))
            if len(params) > 0:
                url_parts[3] = self.__add_makros(params, values)

            query = dict(parse_qsl(url_parts[4]))
            if len(query) > 0:
                url_parts[4] = self.__add_makros(query, values)

            url = urlunparse(url_parts)
        except Exception as e:
            print(e)
        return url

    def __add_utm_param(self, url):
        try:
            keys = self.get_utm_keys()
            url_parts = list(urlparse(url))
            params = dict(parse_qsl(url_parts[3]))
            if len(params) > 0:
                url_parts[3] = self.__add_utm(params, keys)

            query = dict(parse_qsl(url_parts[4]))
            url_parts[4] = self.__add_utm(query, keys)
            url = urlunparse(url_parts)
        except Exception as e:
            print(e)
        return url

    @property
    def url(self):
        print(self.raw_url)
        url = self.__add_dynamic_param(self.raw_url)
        if self.utm:
            url = self.__add_utm_param(url)
        print(url)
        return url
