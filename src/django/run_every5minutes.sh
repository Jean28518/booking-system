#!/bin/bash

# If src directory exists change into src/django directory
if [ -d "src" ]; then
    cd src/django
fi

# if app directory exists change into app directory (inside docker container)
if [ -d "app" ]; then
    cd app
fi

# Enable virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "Running every 5 minutes scripts..."

# Run django shell with following commands
python manage.py shell -c "import booking.booking; booking.booking.send_reminder_mails()"
