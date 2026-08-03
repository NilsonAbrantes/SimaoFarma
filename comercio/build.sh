#!/bin/bash
echo "Building project..."
python -m pip install -r requirements.txt --break-system-packages

echo "Collect static..."
python manage.py collectstatic --noinput

echo "Movendo a pasta staticfiles para a raiz..."
mv comercio/staticfiles .