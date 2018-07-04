from pyramid.view import view_config


@view_config(route_name='index', renderer='templates/index.html')
def my_view(request):
    result = request.dbsession.execute('select 1')
    return {'project': result}
