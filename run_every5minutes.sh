#!/bin/bash

# If src directory exists change into src/django directory
if [ -d "src" ]; then
    cd src/django
fi

# Enable virtual environment
source .venv/bin/activate

# Run django shell with following commands
python3 manage.py shell -c "import booking.booking; booking.booking.send_reminder_mails()"
