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

DEBUG = os.getenv("DEBUG", "False") == "True"  # Changed to default False for production
APPEND_SLASH = False

# --------------------------------------------------
# CSRF TRUSTED ORIGINS
# --------------------------------------------------
CSRF_TRUSTED_ORIGINS = [
    'https://adugalam.com',
    'https://www.adugalam.com',
    'https://api.adugalam.com',
    'https://*.run.app',
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
    "https://turf-backend-298232774766.asia-southeast1.run.app",
    "https://turf-backend-298232774766.asia-south1.run.app",
    "https://api.adugalam.com",
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

# Only allow all origins in development
CORS_ALLOW_ALL_ORIGINS = DEBUG

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
    db_config = secret_manager.get_db_config()
    
    # If using Cloud SQL socket (production), adjust the config
    db_host = os.getenv('DB_HOST', '')
    if db_host and db_host.startswith('/cloudsql/'):
        db_config['HOST'] = db_host
        db_config['PORT'] = ''  # Socket doesn't use port
        db_config['OPTIONS'] = {}  # No SSL needed for socket
        db_config['CONN_MAX_AGE'] = 60
    
    DATABASES = {"default": db_config}
else:
    # Fallback to environment variables for local development
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    
    # Check if using Cloud SQL socket
    if db_host and db_host.startswith('/cloudsql/'):
        # Unix socket connection (Cloud Run production)
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": os.getenv("DB_NAME", "turf_db"),
                "USER": os.getenv("DB_USER", "postgres"),
                "PASSWORD": os.getenv("DB_PASSWORD", "Adugalam@1234"),
                "HOST": db_host,
                "PORT": "",
                "CONN_MAX_AGE": 60,
            }
        }
    else:
        # TCP connection (local development)
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": os.getenv("DB_NAME", "turf_db"),
                "USER": os.getenv("DB_USER", "postgres"),
                "PASSWORD": os.getenv("DB_PASSWORD", "Adugalam@1234"),
                "HOST": db_host,
                "PORT": db_port,
                "OPTIONS": {
                    "sslmode": "require",
                },
                "CONN_MAX_AGE": 60,
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
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

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

# ==================================================
# CLOUD RUN / PRODUCTION SETTINGS (KEEP AT THE END)
# ==================================================

# Add WhiteNoise middleware if not already present
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    # Insert after SecurityMiddleware (position 1)
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Production security settings (only enforce if not DEBUG)
if not DEBUG:
    # Allow Cloud Run and custom domain
    ALLOWED_HOSTS = [
        'turf-backend-298232774766.asia-southeast1.run.app',
        'turf-backend-298232774766.asia-south1.run.app',
        'adugalam1-app-298232774766.asia-south1.run.app',
        'api.adugalam.com',
        '.run.app',
        'localhost',
        '127.0.0.1',
    ]
    
    # Trust Cloud Run's proxy headers (critical for HTTPS)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Force Django to trust the proxy
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True
    
    # Enforce HTTPS redirects
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Secure cookies
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    
    # Additional security headers
    SECURE_REFERRER_POLICY = 'same-origin'
    SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
else:
    # Development settings - allow all hosts
    ALLOWED_HOSTS = ['*']
    SECURE_SSL_REDIRECT = False
    SECURE_PROXY_SSL_HEADER = None
    USE_X_FORWARDED_HOST = False
    USE_X_FORWARDED_PORT = False
