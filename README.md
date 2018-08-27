# facebook-exporter

celery worker -A pyramid_celery.celery_app --ini development.ini
celery beat -A pyramid_celery.celery_app --ini development.ini