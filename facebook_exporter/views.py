import os
from collections import defaultdict

from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.response import FileResponse
from pyramid.security import forget
from pyramid.view import forbidden_view_config
from pyramid.view import view_config

from facebook_exporter.helper import redirect_link, image_link, price
from facebook_exporter.tasks import create_feed, check_feed


@view_config(route_name='index', renderer='templates/index.html', permission='view')
def index(request):
    result = request.dbsession.execute('select 1')
    return {'project': result}


@view_config(route_name='check_feed', renderer='json', permission='view')
def check_feeds(request):
    check_feed.delay()
    return {}


@view_config(route_name='export', renderer='templates/xml.html', permission='view')
def export(request):
    request.response.content_type = 'application/xml'
    offers = []
    count = request.GET.get('count', 1000)
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
    q = '''
                    SELECT TOP %s  
                    View_Lot.LotID AS LotID,
                    View_Lot.Title AS Title,
                    ISNULL(View_Lot.Descript, '') AS Description,
                    ISNULL(View_Lot.Price, '0') Price,
                    View_Lot.ExternalURL AS UrlToMarket,
                    View_Lot.ImgURL,
                    RetargetingID,
                    View_Lot.Auther
                    FROM View_Lot 
                    INNER JOIN LotByAdvertise ON LotByAdvertise.LotID = View_Lot.LotID
                    INNER JOIN View_Advertise ON View_Advertise.AdvertiseID = LotByAdvertise.AdvertiseID
                    WHERE View_Advertise.AdvertiseID = '%s' AND View_Lot.ExternalURL <> '' 
                        AND View_Lot.isTest = 1 AND View_Lot.isAdvertising = 1
                    ''' % (count, id)
    result = request.dbsession.execute(q)
    for offer in result:
        offer_id = '%s...%s' % (offer[0], offer[7])
        if offer[6]:
            offer_id = '%s...%s' % (offer[6], offer[7])
        offers.append({
            'id': offer_id,
            'title': str(offer[1]),
            'description': str(offer[2]),
            'price': price(offer[3]),
            'url': redirect_link(offer[4], offer[0], id),
            'image': image_link(offer[5]),
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
    result = request.dbsession.execute('''
                                SELECT count(*)
                                FROM View_Advertise a
                                LEFT OUTER JOIN Users u ON u.UserID = a.UserID
                                LEFT OUTER JOIN Manager m  ON u.ManagerID = m.id
                                WHERE m.Name IS NOT NULL AND isActive=1
                                ''').fetchone()
    recordsTotal = result[0]
    q = [
        'm.Name IS NOT NULL',
        'isActive=1'
    ]
    if search:
        sq = [
            "Title like '%" + search + "%'",
            "Login like '%" + search + "%'",
            "m.Name like '%" + search + "%'",
        ]
        q.append('(%s)' % ' OR '.join(sq))
    sql = '''
                            SELECT
                            a.AdvertiseID AS AdvertiseID,
                            Title,
                            Login, 
                            m.Name AS Manager,
                            CASE WHEN MarketID IS NULL THEN 'false' ELSE 'true' END Market
                            FROM View_Advertise a
                            LEFT OUTER JOIN Users u ON u.UserID = a.UserID
                            LEFT OUTER JOIN Manager m  ON u.ManagerID = m.id
                            LEFT OUTER JOIN MarketByAdvertise mark ON mark.AdvertiseID = a.AdvertiseID
                            WHERE %s ORDER BY %s %s
                            ''' % (' AND '.join(q), oreder_column, oreder)
    result = request.dbsession.execute(sql)
    for campaign in result:
        data.append((campaign[1], campaign[2], campaign[3],
                     "<a href='%s' target='_blank''>File Export</a>" % request.route_url('export',
                                                                                         id=campaign[0],
                                                                                         _query={'static': campaign[4]})
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
