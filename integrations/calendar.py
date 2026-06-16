import os
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.oauth2.service_account import Credentials

GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

BOGOTA_TZ = ZoneInfo("America/Bogota")
VISIT_DURATION_MINUTES = 20

DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

AVAILABLE_WINDOWS = [
    {"date": "2026-06-15", "start": "14:30", "end": "18:00"},  # Lunes
    {"date": "2026-06-16", "start": "14:00", "end": "18:20"},  # Martes tarde
    {"date": "2026-06-18", "start": "09:40", "end": "13:00"},  # Jueves mañana
    {"date": "2026-06-18", "start": "14:00", "end": "18:20"},  # Jueves tarde
]


def get_all_slots() -> list:
    """Generate all 20-min slots from available windows, excluding past slots"""
    now = datetime.now(tz=BOGOTA_TZ)
    slots = []
    for window in AVAILABLE_WINDOWS:
        current = datetime.strptime(
            f"{window['date']} {window['start']}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=BOGOTA_TZ)
        end = datetime.strptime(
            f"{window['date']} {window['end']}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=BOGOTA_TZ)
        while current <= end:
            if current > now:
                slots.append(current)
            current += timedelta(minutes=VISIT_DURATION_MINUTES)
    return slots


class CalendarManager:
    """Google Calendar integration for scheduling visits"""

    def __init__(self):
        self.calendar_id = GOOGLE_CALENDAR_ID
        self.service = self._init_service()

    def _init_service(self):
        if not GOOGLE_CREDENTIALS_JSON:
            print("[WARNING] Google Calendar credentials not configured (dev mode)")
            return None
        try:
            creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
            credentials = Credentials.from_service_account_info(
                creds_dict,
                scopes=["https://www.googleapis.com/auth/calendar"],
            )
            from googleapiclient.discovery import build
            return build("calendar", "v3", credentials=credentials)
        except Exception as e:
            print(f"Error initializing Google Calendar: {e}")
            return None

    def check_availability(self, start_datetime: datetime) -> bool:
        if start_datetime.tzinfo is None:
            start_datetime = start_datetime.replace(tzinfo=BOGOTA_TZ)
        end_datetime = start_datetime + timedelta(minutes=VISIT_DURATION_MINUTES)
        if not self.service:
            return True
        try:
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_datetime.isoformat(),
                timeMax=end_datetime.isoformat(),
                singleEvents=True,
            ).execute()
            return len(events_result.get("items", [])) == 0
        except Exception as e:
            print(f"Error checking calendar availability: {e}")
            return False

    def create_event(self, start_datetime: datetime, attendee_name: str, attendee_phone: str, num_persons: int = 1) -> str:
        if start_datetime.tzinfo is None:
            start_datetime = start_datetime.replace(tzinfo=BOGOTA_TZ)
        end_datetime = start_datetime + timedelta(minutes=VISIT_DURATION_MINUTES)
        if not self.service:
            print(f"[DEV MODE] Would create event for {attendee_name} at {start_datetime}")
            return f"DEV_EVENT_{start_datetime.timestamp()}"
        event = {
            "summary": f"Visita - {attendee_name} ({num_persons} persona{'s' if num_persons != 1 else ''})",
            "description": f"Telefono: {attendee_phone}\nPersonas: {num_persons}\nApartamento: Los Robles, Bogota",
            "start": {"dateTime": start_datetime.isoformat(), "timeZone": "America/Bogota"},
            "end": {"dateTime": end_datetime.isoformat(), "timeZone": "America/Bogota"},
            "location": "Apartamento Los Robles, Bogota",
        }
        try:
            result = self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
            return result.get("id")
        except Exception as e:
            print(f"Error creating calendar event: {e}")
            return None

    def delete_event(self, event_id: str) -> bool:
        """Delete an existing calendar event"""
        if not event_id:
            return False
        if not self.service:
            print(f"[DEV MODE] Would delete event {event_id}")
            return True
        try:
            self.service.events().delete(calendarId=self.calendar_id, eventId=event_id).execute()
            print(f"[DEBUG] Calendar event deleted: {event_id}")
            return True
        except Exception as e:
            print(f"Error deleting calendar event {event_id}: {e}")
            return False

    def update_event(self, event_id: str, start_datetime: datetime) -> bool:
        if start_datetime.tzinfo is None:
            start_datetime = start_datetime.replace(tzinfo=BOGOTA_TZ)
        end_datetime = start_datetime + timedelta(minutes=VISIT_DURATION_MINUTES)
        if not self.service:
            print(f"[DEV MODE] Would update event {event_id} to {start_datetime}")
            return True
        try:
            event = self.service.events().get(calendarId=self.calendar_id, eventId=event_id).execute()
            event["start"]["dateTime"] = start_datetime.isoformat()
            event["end"]["dateTime"] = end_datetime.isoformat()
            self.service.events().update(calendarId=self.calendar_id, eventId=event_id, body=event).execute()
            return True
        except Exception as e:
            print(f"Error updating calendar event: {e}")
            return False

    def get_available_slots(self) -> list:
        all_slots = get_all_slots()
        if not self.service:
            return [s.strftime("%Y-%m-%d %H:%M") for s in all_slots]
        available = []
        for slot in all_slots:
            if self.check_availability(slot):
                available.append(slot.strftime("%Y-%m-%d %H:%M"))
        return available

    def get_available_days(self) -> list:
        slots = self.get_available_slots()
        days = []
        seen = set()
        for slot in slots:
            date_str = slot.split(" ")[0]
            if date_str not in seen:
                seen.add(date_str)
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                days.append({"date": date_str, "dia_semana": DIAS_SEMANA[dt.weekday()]})
        return days

    def get_available_times(self, date: str) -> dict:
        slots = self.get_available_slots()
        times = [s.split(" ")[1] for s in slots if s.startswith(date)]
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            dia_semana = DIAS_SEMANA[dt.weekday()]
        except ValueError:
            dia_semana = None
        return {"date": date, "dia_semana": dia_semana, "available_times": times}
