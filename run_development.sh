#!/bin/bash

if [ -d src ]; then
    cd src/django
fi

source .env/bin/activate

pip install -r requirements.txt

python3 manage.py migrate --no-input
python3 manage.py collectstatic --no-input

echo "Starting server..."
python manage.py runserver
