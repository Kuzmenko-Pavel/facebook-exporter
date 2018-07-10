from pyramid.view import view_config
from pyramid.view import forbidden_view_config
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.security import forget
import base64
from collections import defaultdict


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


@view_config(route_name='index', renderer='templates/index.html', permission='view')
def index(request):
    result = request.dbsession.execute('select 1')
    return {'project': result}


@view_config(route_name='export', renderer='templates/xml.html')
def export(request):
    request.response.content_type = 'application/xml'
    offers = []
    id = request.matchdict.get('id')
    if id:
        q = '''
                        SELECT TOP %d  
                        Lot.LotID AS LotID,
                        Lot.Title AS Title,
                        ISNULL(Lot.Descript, '') AS Description,
                        ISNULL(lot.Price, '0') Price,
                        ExternalURL AS UrlToMarket,
                        Lot.ImgURL 
                        FROM Lot 
                        INNER JOIN LotByAdvertise ON LotByAdvertise.LotID = Lot.LotID
                        INNER JOIN Advertise ON Advertise.AdvertiseID = LotByAdvertise.AdvertiseID
                        WHERE Advertise.AdvertiseID = '%s' AND Lot.ExternalURL <> '' 
                            AND Lot.isTest = 1 AND lot.isAdvertising = 1
                        ''' % (100, id)
        result = request.dbsession.execute(q)
        for offer in result:
            offers.append({
                'id': offer[0],
                'title': offer[1],
                'description': offer[2],
                'price': offer[3],
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
                                FROM Advertise a
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
                            m.Name AS Manager
                            FROM Advertise a
                            LEFT OUTER JOIN Users u ON u.UserID = a.UserID
                            LEFT OUTER JOIN Manager m  ON u.ManagerID = m.id
                            WHERE %s ORDER BY %s %s
                            ''' % (' AND '.join(q), oreder_column, oreder)
    result = request.dbsession.execute(sql)
    for campaign in result:
        data.append((campaign[1], campaign[2], campaign[3],
                     "<a href='%s' target='_blank''>File Export</a>" % request.route_url('export', id=campaign[0])))
    recordsFiltered = len(data)
    data = data[start:start+length]
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