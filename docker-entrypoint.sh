#!/bin/sh

apk add gettext

pip install --upgrade pip

cd /app/
pip install -r requirements.txt

python manage.py migrate --no-input
python manage.py compilemessages
python manage.py collectstatic --no-input

gunicorn root.wsgi:application --bind 0.0.0.0:8000
