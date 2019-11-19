import os
from collections import defaultdict
from random import choice

from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.response import FileResponse
from pyramid.security import forget
from pyramid.view import forbidden_view_config
from pyramid.view import view_config

from facebook_exporter.helper import redirect_link, image_link, price
from facebook_exporter.tasks import create_feed, check_feed
from facebook_exporter.models import ParentCampaign, ParentBlock, ParentOffer


@view_config(route_name='index', renderer='templates/index.html', permission='view')
def index(request):
    result = request.dbsession.execute('select 1')
    return {'project': result}


@view_config(route_name='check_feed', renderer='json', permission='view')
def check_feeds(request):
    id = request.GET.get('id')
    check_feed.delay(id)
    return {}


@view_config(route_name='export', renderer='templates/xml.html', permission='view')
def export(request):
    request.response.content_type = 'application/xml'
    offers = []
    count = int(request.GET.get('count', 1000))
    static = True if request.GET.get('static') == 'true' else False
    id = request.matchdict.get('id', '').upper()
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static/xml')
    file_path = os.path.join(dir_path, id + ".xml")
    file_exists = os.path.isfile(file_path)
    if id:
        if file_exists and static:
            response = FileResponse(
                file_path,
                request=request,
                content_type=request.response.content_type
            )
            return response
        if static:
            create_feed.delay(id)

    blocks = request.dbsession.query(ParentBlock).limit(10).all()
    campaign = request.dbsession.query(ParentCampaign).filter(ParentCampaign.guid == id).one_or_none()
    if campaign:
        for offer in request.dbsession.query(ParentOffer).filter(ParentOffer.id_campaign == campaign.id).limit(count).all():
            offer_id = '%s...%s' % (str(offer.guid).upper(), str(offer.guid_account).upper())
            if offer.id_retargeting:
                offer_id = '%s...%s' % (offer.id_retargeting, str(offer.guid_account).upper())
            if offer.images[0]:
                offers.append({
                    'id': offer_id,
                    'title': str(offer.title),
                    'description': str(offer.description),
                    'price': price(offer.price),
                    'url': redirect_link(offer, campaign, choice(blocks)),
                    'image': image_link(offer.images[0]),
                })

    return {'offers': offers}


@view_config(route_name='campaigns', renderer='json', permission='view')
def campaigns(request):
    column = defaultdict(lambda: 'Title')
    column['0'] = 'Title'
    column['1'] = 'Login'
    column['2'] = 'm.Name'
    column['3'] = 'a.AdvertiseID'
    draw = request.GET.get('draw')
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search = request.GET.get('search[value]')
    oreder = request.GET.get('order[0][dir]', 'asc')
    oreder_column = column[request.GET.get('order[0][column]', '')]
    data = []
    campaign_count = request.dbsession.query(ParentCampaign).count()
    recordsTotal = campaign_count
    q = request.dbsession.query(ParentCampaign)
    if search:
        q = q.filter(
            ParentCampaign.name.like('%'+search+'%')
        )

    campaigns = q.all()
    for campaign in campaigns:
        data.append((campaign.name,
                     "<a href='%s' target='_blank''>File Export</a>" % request.route_url('export',
                                                                                         id=str(campaign.guid).upper(),
                                                                                         _query={'static': 'true'})
                     ))

    recordsFiltered = len(data)
    data = data[start:start + length]
    return {
        'draw': draw,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'data': data
    }


@forbidden_view_config()
def forbidden_view(request):
    if request.authenticated_userid is None:
        response = HTTPUnauthorized()
        response.headers.update(forget(request))
    else:
        response = HTTPForbidden()
    return response
