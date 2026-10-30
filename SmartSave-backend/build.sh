#!/usr/bin/env bash
# Render build script for SMARTSAVE backend
set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files (Whitenoise)
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate