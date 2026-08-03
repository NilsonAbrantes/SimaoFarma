#!/bin/bash
echo "Building project..."
python -m pip install -r requirements.txt --break-system-packages

echo "Collect static..."
python manage.py collectstatic --noinput