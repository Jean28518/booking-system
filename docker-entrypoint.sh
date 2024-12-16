#!/bin/sh

apt-get update
apt-get install -y gettext locales

# if "de_DE.UTF-8 UTF-8" not in /etc/locale.gen
if ! grep -q "de_DE.UTF-8 UTF-8" /etc/locale.gen; then
    echo "de_DE.UTF-8 UTF-8" >> /etc/locale.gen
fi
locale-gen

pip install --upgrade pip

cd /app/
pip install -r requirements.txt

python manage.py migrate --no-input
python manage.py compilemessages
python manage.py collectstatic --no-input

gunicorn root.wsgi:application --bind 0.0.0.0:8000
