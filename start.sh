#!/bin/bash
set -e

echo "==> Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "==> Aplicando migrations..."
python manage.py migrate --noinput

echo "==> Criando admin padrão (se necessário)..."
python manage.py create_default_admin

echo "==> Iniciando gunicorn..."
exec gunicorn barrs_erp.wsgi --bind 0.0.0.0:"${PORT:-8080}" --workers 2 --log-file -
