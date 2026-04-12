import os
from google.cloud import secretmanager
from dotenv import load_dotenv

load_dotenv()

class SecretManager:
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.use_secret_manager = os.getenv('USE_SECRET_MANAGER', 'false').lower() == 'true'
        self.client = None
        
        if self.use_secret_manager:
            try:
                self.client = secretmanager.SecretManagerServiceClient()
                print("✅ Secret Manager client initialized")
            except Exception as e:
                print(f"⚠️ Warning: Could not initialize Secret Manager: {e}")
                self.use_secret_manager = False
    
    def get_secret(self, secret_name, default=None):
        """Get a secret from Secret Manager or fallback to .env"""
        
        # Try environment variable first (for local development)
        env_var_name = secret_name.upper().replace('-', '_')
        env_value = os.getenv(env_var_name)
        
        # If Secret Manager is enabled, try to get from there
        if self.use_secret_manager and self.client:
            try:
                name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
                response = self.client.access_secret_version(request={"name": name})
                secret_value = response.payload.data.decode("UTF-8")
                return secret_value
            except Exception as e:
                print(f"⚠️ Could not fetch secret {secret_name}: {e}")
                if env_value:
                    return env_value
        
        # Final fallback to .env
        return env_value if env_value else default
    
    # Database secrets
    def get_db_password(self):
        return self.get_secret('db-password')
    
    # Email secrets
    def get_smtp_password(self):
        return self.get_secret('smtp-pass')
    
    # Django secrets
    def get_django_secret_key(self):
        return self.get_secret('django-secret-key')
    
    # Razorpay secrets
    def get_razorpay_key_id(self):
        return self.get_secret('razorpay-key-id')
    
    def get_razorpay_key_secret(self):
        return self.get_secret('razorpay-key-secret')
    
    # WhatsApp secrets
    def get_whatsapp_client_id(self):
        return self.get_secret('whatsapp-client-id')
    
    def get_whatsapp_client_password(self):
        return self.get_secret('whatsapp-client-password')
    
    def get_whatsapp_from_number(self):
        return self.get_secret('whatsapp-from-number')
    
    def get_whatsapp_user_id(self):
        return self.get_secret('whatsapp-user-id')
    
    # Database configuration (PostgreSQL)
    def get_db_config(self):
        """Get database configuration for PostgreSQL"""
        return {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'turf_db'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': self.get_db_password(),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'OPTIONS': {
                'sslmode': 'require',
            }
        }
    
    # Email configuration
    def get_email_config(self):
        return {
            'EMAIL_HOST': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
            'EMAIL_PORT': int(os.getenv('SMTP_PORT', 587)),
            'EMAIL_HOST_USER': os.getenv('SMTP_USER', ''),
            'EMAIL_HOST_PASSWORD': self.get_smtp_password(),
            'EMAIL_USE_TLS': True,
        }

# Create singleton instance
secret_manager = SecretManager()
