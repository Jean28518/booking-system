#!/bin/bash

if [ -d src ]; then
    cd src/django
fi

source .venv/bin/activate

pip install -r requirements.txt

python3 manage.py compilemessages
python3 manage.py makemigrations --no-input
python3 manage.py migrate --no-input

echo "Starting server..."
python manage.py runserver
