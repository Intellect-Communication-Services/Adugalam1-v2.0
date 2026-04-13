#!/bin/bash

echo "🚀 Starting Turf Backend Docker Container"

# Set environment variables
export GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
export GOOGLE_CLOUD_PROJECT=adugalam
export USE_SECRET_MANAGER=true

# Run migrations (optional - for production you might want to run separately)
echo "📦 Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "✨ Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:8080 \
    --workers 4 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    turf_backend.wsgi:application
