import os
import requests
from typing import Dict

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


class TelegramNotifier:
    """Send alerts to owner via Telegram"""

    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

    def _fmt_ingresos(self, value) -> str:
        if value is None:
            return "N/A"
        try:
            return f"${float(value):,.0f}"
        except (ValueError, TypeError):
            return str(value)

    def send_message(self, message: str) -> bool:
        if not self.bot_token or not self.chat_id:
            print(f"[DEV MODE] Would send Telegram: {message}")
            return True
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML",
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False

    def alert_qualified_lead(self, lead_data: Dict) -> bool:
        message = (
            "NUEVO LEAD CALIFICADO\n"
            f"Nombre: {lead_data.get('nombre', 'N/A')}\n"
            f"WhatsApp: {lead_data.get('whatsapp', 'N/A')}\n"
            f"Personas: {lead_data.get('personas', 'N/A')}\n"
            f"Ocupacion: {lead_data.get('ocupacion', 'N/A')}\n"
            f"Ingresos: {self._fmt_ingresos(lead_data.get('ingresos'))}\n"
            f"Mascotas: {'Si' if lead_data.get('mascotas') else 'No'}\n"
            f"Visita: {lead_data.get('fecha_visita', 'Por confirmar')}"
        )
        return self.send_message(message)

    def alert_rejected_lead(self, lead_data: Dict, motivo: str) -> bool:
        message = (
            "LEAD RECHAZADO\n"
            f"Nombre: {lead_data.get('nombre', 'N/A')}\n"
            f"WhatsApp: {lead_data.get('whatsapp', 'N/A')}\n"
            f"Motivo: {motivo}"
        )
        return self.send_message(message)

    def alert_purchase_interest(self, lead_data: Dict) -> bool:
        message = (
            "INTERES EN COMPRA\n"
            f"Nombre: {lead_data.get('nombre', 'N/A')}\n"
            f"WhatsApp: {lead_data.get('whatsapp', 'N/A')}"
        )
        return self.send_message(message)

    def alert_no_confirmation(self, lead_data: Dict, appointment_time: str) -> bool:
        message = (
            "SIN CONFIRMACION DE CITA\n"
            f"Nombre: {lead_data.get('nombre', 'N/A')}\n"
            f"WhatsApp: {lead_data.get('whatsapp', 'N/A')}\n"
            f"Visita: {appointment_time}"
        )
        return self.send_message(message)

    def alert_cancelled_visit(self, lead_data: Dict, motivo: str = "") -> bool:
        message = (
            "CITA CANCELADA\n"
            f"Nombre: {lead_data.get('nombre', 'N/A')}\n"
            f"WhatsApp: {lead_data.get('whatsapp', 'N/A')}\n"
            f"Visita cancelada: {lead_data.get('fecha_visita', 'N/A')}\n"
            f"Motivo: {motivo or 'No especificado'}"
        )
        return self.send_message(message)

    def alert_custom_message(self, lead_data: Dict, mensaje: str) -> bool:
        message = (
            "MENSAJE PUNTUAL DE UN INTERESADO\n"
            f"Nombre: {lead_data.get('nombre', 'N/A')}\n"
            f"WhatsApp: {lead_data.get('whatsapp', 'N/A')}\n"
            f"Mensaje: {mensaje}"
        )
        return self.send_message(message)

    def alert_technical_error(self, error_msg: str, context: str = "") -> bool:
        message = (
            "ERROR TECNICO\n"
            f"Error: {error_msg}\n"
            f"Contexto: {context}"
        )
        return self.send_message(message)
