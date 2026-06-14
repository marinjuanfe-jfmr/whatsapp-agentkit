import os
import requests
from typing import List

WHAPI_API_URL = "https://gate.whapi.cloud"


class WhapiClient:
    """Whapi.cloud WhatsApp API client"""

    def __init__(self):
        self.token = os.getenv("WHAPI_TOKEN")
        self.base_url = WHAPI_API_URL
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def send_text_message(self, to: str, text: str) -> bool:
        """Send text message via Whapi.cloud"""
        if not self.token:
            print(f"[DEBUG] WHAPI_TOKEN no configurado — mensaje no enviado a {to}")
            return False

        try:
            url = f"{self.base_url}/messages/text"
            payload = {
                "to": to,
                "body": text,
            }
            print(f"[DEBUG] Whapi send_text_message to={to} body_len={len(text)}")
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            print(f"[DEBUG] Whapi response status={response.status_code} body={response.text[:300]}")
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"[ERROR] Whapi send_text_message: {e}")
            return False

    def send_media_message(self, to: str, media_url: str, media_type: str = "image", caption: str = "") -> bool:
        """Send media (image/video) via Whapi.cloud"""
        if not self.token:
            print(f"[DEBUG] WHAPI_TOKEN no configurado — media no enviada a {to}")
            return False

        endpoint_map = {
            "image": "messages/image",
            "video": "messages/video",
            "document": "messages/document",
        }
        endpoint = endpoint_map.get(media_type, "messages/image")

        try:
            url = f"{self.base_url}/{endpoint}"
            payload = {
                "to": to,
                "media": media_url,
                "caption": caption,
            }
            print(f"[DEBUG] Whapi send_media_message to={to} type={media_type}")
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            print(f"[DEBUG] Whapi media response status={response.status_code} body={response.text[:300]}")
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"[ERROR] Whapi send_media_message: {e}")
            return False

    def send_multiple_media(self, to: str, media_list: List[dict]) -> bool:
        """Send multiple media messages"""
        for media in media_list:
            media_url = media.get("url")
            media_type = media.get("type", "image")
            caption = media.get("caption", "")
            if not self.send_media_message(to, media_url, media_type, caption):
                return False
        return True

    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        if not phone.startswith("+"):
            return False
        if len(phone) < 10:
            return False
        return True
