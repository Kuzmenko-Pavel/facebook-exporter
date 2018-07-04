# -*- coding: UTF-8 -*-
__author__ = 'kuzmenko-pavel'
from pyramid.config import Configurator


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    includeme(config)
    app = config.make_wsgi_app()
    return app


def includeme(config):
    config.include('pyramid_jinja2')
    config.add_jinja2_renderer('.html')
    config.add_jinja2_search_path("facebook_exporter:templates")
    config.include('.models')
    config.include('.routes')
    config.commit()
    config.scan()
