#!/bin/sh

# Wait for the database to be ready
python manage.py wait_for_db

# Apply database migrations
python manage.py migrate

# Create superuser if not exists
python manage.py create_superuser_if_not_exists

# Collect static files
python manage.py collectstatic --noinput

# Compile messages for i18n
python manage.py compilemessages

exec "$@"