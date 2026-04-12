#!/bin/bash

echo "🚀 Starting Django Development Server with Secret Manager"

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/turf-local-dev-key.json
export GOOGLE_CLOUD_PROJECT=adugalam
export USE_SECRET_MANAGER=true

# Load .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run Django migrations (optional)
echo "📦 Running migrations..."
python manage.py migrate --noinput

# Start Django server
echo "✨ Starting Django server..."
python manage.py runserver 0.0.0.0:8000
