import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
from secret_manager import secret_manager

# Load environment variables
load_dotenv()

# --------------------------------------------------
# BASE DIR
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --------------------------------------------------
# SECURITY
# --------------------------------------------------
# Use Secret Manager for secret key in production, fallback to env for local
SECRET_KEY = secret_manager.get_django_secret_key() or os.getenv(
    "SECRET_KEY", 
    "django-insecure-change-this-in-production"
)

DEBUG = os.getenv("DEBUG", "True") == "True"
APPEND_SLASH = False

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "34.14.169.159",  # Cloud SQL IP
    "*",  # For development
]

# --------------------------------------------------
# APPLICATIONS
# --------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'corsheaders',

    # Local apps
    'core',
]

# --------------------------------------------------
# MIDDLEWARE (⚠️ ORDER IMPORTANT)
# --------------------------------------------------
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',   # ✅ MUST be first (top)
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# --------------------------------------------------
# CORS CONFIG (Frontend ↔ Backend)
# --------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    "https://adugalam1-app-298232774766.asia-south1.run.app",
    "https://turf-backend-298232774766.asia-south1.run.app",
    "http://localhost:5173",  # For local development
    "http://localhost:5000",   # For local development
]
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_ALL_ORIGINS = True 
# --------------------------------------------------
# URLS / WSGI
# --------------------------------------------------
ROOT_URLCONF = 'turf_backend.urls'
WSGI_APPLICATION = 'turf_backend.wsgi.application'

# --------------------------------------------------
# TEMPLATES
# --------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# --------------------------------------------------
# DATABASE (PostgreSQL with Secret Manager)
# --------------------------------------------------
# Use Secret Manager for database configuration
if secret_manager.use_secret_manager:
    DATABASES = {
        "default": secret_manager.get_db_config()
    }
else:
    # Fallback to environment variables for local development
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "turf_db"),
            "USER": os.getenv("DB_USER", "postgres"),
            "PASSWORD": os.getenv("DB_PASSWORD", "Adugalam@1234"),
            "HOST": os.getenv("DB_HOST", "34.14.169.159"),
            "PORT": os.getenv("DB_PORT", "5432"),
            "OPTIONS": {
                "sslmode": "require",
            },
        }
    }

# --------------------------------------------------
# RAZORPAY KEYS (from Secret Manager)
# --------------------------------------------------
RAZORPAY_KEY_ID = secret_manager.get_razorpay_key_id() or os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = secret_manager.get_razorpay_key_secret() or os.getenv("RAZORPAY_KEY_SECRET", "")

# --------------------------------------------------
# PASSWORD VALIDATION
# --------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'core.AppUser'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# --------------------------------------------------
# INTERNATIONALIZATION
# --------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --------------------------------------------------
# STATIC FILES
# --------------------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --------------------------------------------------
# DRF + JWT CONFIG
# --------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=3),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# --------------------------------------------------
# EMAIL CONFIGURATION (with Secret Manager)
# --------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Try to get email config from Secret Manager first
email_config = secret_manager.get_email_config()
EMAIL_HOST = email_config['EMAIL_HOST'] or os.getenv("SMTP_HOST", "smtp.gmail.com")
EMAIL_PORT = email_config['EMAIL_PORT'] or int(os.getenv("SMTP_PORT", 587))
EMAIL_HOST_USER = email_config['EMAIL_HOST_USER'] or os.getenv("SMTP_USER", "")
EMAIL_HOST_PASSWORD = email_config['EMAIL_HOST_PASSWORD'] or os.getenv("SMTP_PASS", "")
EMAIL_USE_TLS = email_config['EMAIL_USE_TLS']
EMAIL_USE_SSL = False

DEFAULT_FROM_EMAIL = f"TurfApp <{EMAIL_HOST_USER}>"

# --------------------------------------------------
# WHATSAPP CONFIGURATION (with Secret Manager)
# --------------------------------------------------
WHATSAPP_API_URL = "https://103.229.250.150/unified/v2/send"
WHATSAPP_CLIENT_ID = secret_manager.get_whatsapp_client_id() or os.getenv("WHATSAPP_CLIENT_ID", "woowlocal5dhn6wxesv14a2m")
WHATSAPP_CLIENT_PASSWORD = secret_manager.get_whatsapp_client_password() or os.getenv("WHATSAPP_CLIENT_PASSWORD", "dnud6xluv1uopqss6amv1fxaenv0f56p")
WHATSAPP_FROM_NUMBER = secret_manager.get_whatsapp_from_number() or os.getenv("WHATSAPP_FROM_NUMBER", "916380433385")
WHATSAPP_USER_ID = int(secret_manager.get_whatsapp_user_id() or os.getenv("WHATSAPP_USER_ID", 3))

# --------------------------------------------------
# LOGGING (Optional - for debugging)
# --------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'ERROR',
            'propagate': False,
        },
    },
}

# Add near the end of settings.py
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')  # Add after SecurityMiddleware

ALLOWED_HOSTS = [
    'turf-backend-298232774766.asia-south1.run.app',
    'adugalam1-app-298232774766.asia-south1.run.app',
    'localhost',
    '127.0.0.1',
]
