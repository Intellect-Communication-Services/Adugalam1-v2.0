#!/bin/bash

echo "🔧 Setting up virtual environment with Python 3.12"

# Navigate to project
cd /Users/machd/Adugalam1-v2.0/turf_backend

# Clean up old venvs
rm -rf venv venv311 venv312

# Create virtual environment with Python 3.12
echo "📦 Creating virtual environment..."
python3.12 -m venv venv312

# Activate
echo "🔌 Activating virtual environment..."
source venv312/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install packages
echo "📦 Installing Django and dependencies..."
pip install Django==4.2.10
pip install djangorestframework==3.14.0
pip install django-cors-headers==4.3.1
pip install djangorestframework-simplejwt==5.3.0
pip install psycopg2-binary==2.9.9
pip install google-cloud-secret-manager==2.20.0
pip install python-dotenv==1.0.0
pip install razorpay==1.4.2
pip install Pillow==10.1.0

# Test imports
echo ""
echo "🧪 Testing imports..."
python -c "import django; print('  ✅ Django:', django.get_version())"
python -c "import psycopg2; print('  ✅ psycopg2:', psycopg2.__version__)"
python -c "import razorpay; print('  ✅ Razorpay:', razorpay.__version__)"

echo ""
echo "✅ Virtual environment ready!"
echo ""
echo "To activate: source venv312/bin/activate"
echo "To run server: python manage.py runserver 0.0.0.0:8000"
