#!/usr/bin/env python3
import os
import sys

# Try to import the required module
try:
    from google.cloud import secretmanager
except ImportError:
    print("❌ Google Cloud Secret Manager not installed!")
    print("\nPlease run:")
    print("  pip3 install google-cloud-secret-manager")
    print("\nOr if using virtual environment:")
    print("  source venv/bin/activate")
    print("  pip install google-cloud-secret-manager")
    sys.exit(1)

def test_secret_access():
    print("=" * 50)
    print("Testing Secret Manager Access")
    print("=" * 50)
    
    # Check credentials
    creds_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    print(f"\n1. Credentials file: {creds_file}")
    if creds_file:
        print(f"   File exists: {os.path.exists(creds_file)}")
    else:
        print("   ❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return
    
    # Check project
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'adugalam')
    print(f"\n2. Project ID: {project_id}")
    
    # Initialize client
    try:
        client = secretmanager.SecretManagerServiceClient()
        print(f"\n3. Client initialized successfully")
        
        # Test fetching a secret
        secret_name = "db-password"
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        
        print(f"\n4. Fetching secret '{secret_name}'...")
        response = client.access_secret_version(request={"name": name})
        password = response.payload.data.decode("UTF-8")
        
        print(f"\n✅ Successfully retrieved secret '{secret_name}'")
        print(f"   Password length: {len(password)} characters")
        print(f"   Password preview: {password[:3]}...{password[-3:]}")
        
        print("\n✨ Secret Manager is working correctly!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you've run: gcloud auth application-default login")
        print("2. Or set GOOGLE_APPLICATION_CREDENTIALS correctly")
        print("3. Verify the service account has access to secrets")
        print("4. Check that the secret 'db-password' exists")

if __name__ == "__main__":
    test_secret_access()
