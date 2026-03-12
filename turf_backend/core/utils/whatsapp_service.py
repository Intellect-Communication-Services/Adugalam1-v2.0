import requests
from django.conf import settings


def send_whatsapp(phone, message):

    url = settings.GOINFINITY_WHATSAPP_URL

    headers = {
        "Authorization": f"Bearer {settings.GOINFINITY_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "phone": phone,
        "message": message
    }

    try:
        res = requests.post(url, json=payload, headers=headers)
        print("WhatsApp Response:", res.text)
        return res.json()
    except Exception as e:
        print("WhatsApp Error:", str(e))