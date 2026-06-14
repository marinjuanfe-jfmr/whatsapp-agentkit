import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")


class GoogleSheetsManager:
    """Google Sheets integration for lead tracking"""

    def __init__(self):
        self.sheets_id = GOOGLE_SHEETS_ID
        self.service = self._init_service()

    def _init_service(self):
        if not GOOGLE_CREDENTIALS_JSON:
            print("[WARNING] Google Sheets credentials not configured (dev mode)")
            return None
        try:
            creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            credentials = Credentials.from_service_account_info(
                creds_dict,
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )
            return build("sheets", "v4", credentials=credentials)
        except Exception as e:
            print(f"Error initializing Google Sheets: {e}")
            return None

    def _build_row(self, lead_data: Dict) -> list:
        return [
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            lead_data.get("nombre", ""),
            lead_data.get("whatsapp", ""),
            lead_data.get("personas", ""),
            lead_data.get("ocupacion", ""),
            lead_data.get("ingresos", ""),
            "Si" if lead_data.get("mascotas") else "No",
            "Si" if lead_data.get("vehiculos") else "No",
            lead_data.get("tipo_vehiculo", ""),
            lead_data.get("fecha_mudanza", ""),
            "Si" if lead_data.get("acepta_poliza") else "No",
            lead_data.get("estado", "Pendiente"),
            lead_data.get("motivo_rechazo", ""),
            "Si" if lead_data.get("interes_compra") else "No",
            lead_data.get("fecha_visita", ""),
            lead_data.get("notas", ""),
            "Si" if lead_data.get("confirmo_cita") else "No",
            "Si" if lead_data.get("reagendo_cita") else "No",
        ]

    def _find_row_by_phone(self, phone_number: str) -> Optional[int]:
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheets_id,
                range="Sheet1!C:C",
            ).execute()
            rows = result.get("values", [])
            for i, row in enumerate(rows):
                if row and row[0] == phone_number:
                    return i + 1
            return None
        except Exception as e:
            print(f"Error finding row by phone: {e}")
            return None

    def append_lead(self, lead_data: Dict) -> bool:
        """Upsert: update existing row or append new one"""
        if not self.service:
            print(f"[DEV MODE] Would upsert lead: {lead_data}")
            return True

        try:
            phone_number = lead_data.get("whatsapp", "")
            row = self._build_row(lead_data)
            existing_row = self._find_row_by_phone(phone_number) if phone_number else None

            if existing_row:
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.sheets_id,
                    range=f"Sheet1!A{existing_row}:R{existing_row}",
                    valueInputOption="USER_ENTERED",
                    body={"values": [row]},
                ).execute()
                print(f"[SHEETS] Updated row {existing_row} for {phone_number}")
            else:
                self.service.spreadsheets().values().append(
                    spreadsheetId=self.sheets_id,
                    range="Sheet1!A:R",
                    valueInputOption="USER_ENTERED",
                    body={"values": [row]},
                ).execute()
                print(f"[SHEETS] Appended new row for {phone_number}")

            return True
        except Exception as e:
            print(f"Error upserting to Google Sheets: {e}")
            return False

    def append_message(self, phone_number: str, role: str, message: str) -> bool:
        """Append a single conversation message to the 'Conversaciones' tab"""
        if not self.service:
            print(f"[DEV MODE] Would log message: {phone_number} {role}: {message[:50]}")
            return True

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            phone_number,
            role,
            message,
        ]
        try:
            self.service.spreadsheets().values().append(
                spreadsheetId=self.sheets_id,
                range="Conversaciones!A:D",
                valueInputOption="USER_ENTERED",
                body={"values": [row]},
            ).execute()
            return True
        except Exception as e:
            print(f"Error logging message to Google Sheets: {e}")
            return False

    def get_all_leads(self) -> List[Dict]:
        if not self.service:
            return []
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheets_id,
                range="Sheet1!A:R",
            ).execute()
            return result.get("values", [])
        except Exception as e:
            print(f"Error reading Google Sheets: {e}")
            return []
