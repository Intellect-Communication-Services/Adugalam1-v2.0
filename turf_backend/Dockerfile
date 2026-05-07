FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Create directory for static files
RUN mkdir -p staticfiles

# Run migrations and collect static at build time
RUN python manage.py migrate --noinput || true
RUN python manage.py collectstatic --noinput || true

# Run the application
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 turf_backend.wsgi:application
