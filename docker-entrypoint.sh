#!/bin/bash
set -e

echo "Making migrations..."
python manage.py makemigrations --noinput

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn horilla.wsgi:application --bind 0.0.0.0:8000 --workers 3
