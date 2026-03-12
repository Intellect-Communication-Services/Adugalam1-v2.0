import secrets
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ValidationError

def generate_otp():
    return str(secrets.randbelow(900000) + 100000)

def send_email_otp(email, otp):
    subject = "Your OTP Verification Code - Adugalam"
    
    message = f"""
Your OTP for account verification is:

{otp}

🔒 Do not share with anyone.

If you did not request this, please ignore this email.

- Adugalam Security Team
"""

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False
        )
    except Exception as e:
        raise ValidationError(f"Email service failed: {str(e)}")