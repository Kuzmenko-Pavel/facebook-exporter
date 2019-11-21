# -*- coding: UTF-8 -*-
from __future__ import absolute_import, unicode_literals

from os import environ, getpid
import sys
import socket

from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from zope.sqlalchemy import register

from .ParentCampaigns import ParentCampaign
from .ParentOffers import ParentOffer
from .ParentBlocks import ParentBlock
from .meta import metadata, DBScopedSession

server_name = socket.gethostname()


def get_engine(settings, prefix='sqlalchemy.', **kwargs):
    if 'connect_args' not in kwargs.keys():
        worker = 'Facebook Exporter Web'
        if '-A' in sys.argv:
            worker = 'Facebook Exporter Celery'
        application_name = '%s on %s pid=%s' % (worker, server_name, getpid())
        kwargs['connect_args'] = {"application_name": application_name}
    return engine_from_config(settings, prefix, **kwargs)


def get_session_factory(engine):
    factory = sessionmaker()
    factory.configure(bind=engine)
    return factory


def get_tm_session(session_factory, transaction_manager):
    dbsession = session_factory()
    register(dbsession, transaction_manager=transaction_manager)
    return dbsession


def includeme(config):
    settings = config.get_settings()
    config.include('pyramid_tm')
    engine = get_engine(settings)
    engine.pool._use_threadlocal = True
    metadata.bind = engine
    DBScopedSession.configure(bind=engine)
    session_factory = get_session_factory(engine)
    config.registry['dbsession_factory'] = session_factory

    config.add_request_method(
        # r.tm is the transaction manager used by pyramid_tm
        lambda r: get_tm_session(session_factory, r.tm),
        'dbsession',
        reify=True
    )
