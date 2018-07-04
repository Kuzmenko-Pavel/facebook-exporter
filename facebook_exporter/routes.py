# -*- coding: UTF-8 -*-
__author__ = 'kuzmenko-pavel'


def includeme(config):
    config.add_route('index', '/')
    config.add_static_view('static', 'static', cache_max_age=0)
