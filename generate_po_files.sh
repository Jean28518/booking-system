#!/bin/bash

if [ -d src ]; then
    cd src/django
fi

source .env/bin/activate

pip install -r requirements.txt


django-admin makemessages -l de
django-admin makemessages -l en
