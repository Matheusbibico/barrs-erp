web: gunicorn barrs_erp.wsgi --bind 0.0.0.0:$PORT --workers 2 --log-file -
release: python manage.py migrate --noinput && python manage.py create_default_admin
