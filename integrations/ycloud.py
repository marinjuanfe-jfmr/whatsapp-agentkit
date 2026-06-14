import os
import requests
from typing import Optional, List

YCLOUD_API_KEY = os.getenv("YCLOUD_API_KEY")
YCLOUD_PHONE_NUMBER = os.getenv("YCLOUD_PHONE_NUMBER", "+573243939750")
YCLOUD_API_URL = "https://api.ycloud.com/v2"


class YCloudClient:
    """YCloud WhatsApp API client"""

    def __init__(self):
        self.api_key = YCLOUD_API_KEY
        self.phone_number = YCLOUD_PHONE_NUMBER
        self.base_url = YCLOUD_API_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def send_text_message(self, to: str, text: str) -> bool:
        """Send text message via YCloud"""
        if not self.api_key:
            print(f"[DEBUG] Would send to {to}: {text}")
            return True

        try:
            url = f"{self.base_url}/message/send"
            payload = {
                "phone": to,
                "text": text,
            }
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error sending YCloud message: {e}")
            return False

    def send_media_message(self, to: str, media_url: str, media_type: str = "image", caption: str = "") -> bool:
        """Send media (image/video) via YCloud"""
        if not self.api_key:
            print(f"[DEBUG] Would send {media_type} to {to}: {media_url}")
            return True

        try:
            url = f"{self.base_url}/message/send"
            payload = {
                "phone": to,
                media_type: {
                    "link": media_url,
                    "caption": caption,
                },
            }
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error sending YCloud media: {e}")
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
