#!/bin/bash

# Check if there is already a process with run_every5minutes.sh running
# (We have to count more than 2 because this script itself and the pgrep command will also show up)
if [ $(pgrep -fc run_every5minutes.sh) -gt 2 ]; then
  echo "Another instance of run_every5minutes.sh is still running. Exiting."
  echo "Another instance of run_every5minutes.sh is still running. Exiting." > /var/log/run_every5minutes.log 2>&1
  exit 1
fi

# If src directory exists change into src/django directory
if [ -d "src" ]; then
    cd src/django
fi

# if app directory exists change into app directory (inside docker container)
if [ -d "/app" ]; then
    cd /app
fi

# Enable virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "Running every 5 minutes scripts..."

# Run django shell with following commands
python manage.py shell -c "import booking.booking; booking.booking.send_reminder_mails()"

python manage.py shell -c "import booking.calendar; booking.calendar.retrieve_all_caldav_calendars_for_all_users()"
