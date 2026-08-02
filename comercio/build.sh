#!/bin/bash
echo "Building project..."
python -m pip install -r requirements.txt --break-system-packages

echo "Make migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Collect static..."
python manage.py collectstatic --noinput