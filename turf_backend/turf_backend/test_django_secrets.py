#!/usr/bin/env python3
import os
import sys

# Set up Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'turf_backend.settings')

# Import after setting up Django
from secret_manager import secret_manager

def test_integration():
    print("=" * 60)
    print("Testing Django + Secret Manager Integration")
    print("=" * 60)
    
    # Test 1: Secret Manager status
    print("\n1. Secret Manager Status:")
    print(f"   Enabled: {secret_manager.use_secret_manager}")
    print(f"   Client: {'Initialized' if secret_manager.client else 'Not initialized'}")
    print(f"   Project: {secret_manager.project_id}")
    
    # Test 2: Database configuration
    print("\n2. Database Configuration:")
    db_config = secret_manager.get_db_config()
    print(f"   Engine: {db_config['ENGINE']}")
    print(f"   Host: {db_config['HOST']}")
    print(f"   Database: {db_config['NAME']}")
    print(f"   User: {db_config['USER']}")
    print(f"   Password: {'*' * len(db_config['PASSWORD']) if db_config['PASSWORD'] else 'Not set'}")
    
    # Test 3: Test database connection
    print("\n3. Testing Database Connection:")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=db_config['HOST'],
            port=db_config['PORT'],
            database=db_config['NAME'],
            user=db_config['USER'],
            password=db_config['PASSWORD'],
            sslmode='require'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM auth_user")
        count = cursor.fetchone()[0]
        print(f"   ✅ Connected successfully!")
        print(f"   Total users: {count}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
    
    # Test 4: Email configuration
    print("\n4. Email Configuration:")
    email_config = secret_manager.get_email_config()
    print(f"   Host: {email_config['EMAIL_HOST']}")
    print(f"   Port: {email_config['EMAIL_PORT']}")
    print(f"   User: {email_config['EMAIL_HOST_USER']}")
    print(f"   Password: {'*' * len(email_config['EMAIL_HOST_PASSWORD']) if email_config['EMAIL_HOST_PASSWORD'] else 'Not set'}")
    
    # Test 5: Razorpay keys
    print("\n5. Razorpay Keys:")
    print(f"   Key ID: {secret_manager.get_razorpay_key_id()[:10] if secret_manager.get_razorpay_key_id() else 'Not set'}...")
    print(f"   Key Secret: {'Set' if secret_manager.get_razorpay_key_secret() else 'Not set'}")
    
    # Test 6: WhatsApp credentials
    print("\n6. WhatsApp Credentials:")
    print(f"   Client ID: {secret_manager.get_whatsapp_client_id()[:15] if secret_manager.get_whatsapp_client_id() else 'Not set'}...")
    print(f"   Client Password: {'Set' if secret_manager.get_whatsapp_client_password() else 'Not set'}")
    print(f"   From Number: {secret_manager.get_whatsapp_from_number()}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_integration()
