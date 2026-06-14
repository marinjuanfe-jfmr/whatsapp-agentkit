import os
import json
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def _get_service():
    credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not credentials_json:
        raise ValueError("GOOGLE_CREDENTIALS_JSON no está configurado en .env")

    credentials_info = json.loads(credentials_json)
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=credentials)

def agendar_visita(nombre: str, telefono: str, fecha_hora: str, duracion_minutos: int = 30) -> dict:
    """
    Agenda una visita en Google Calendar.
    fecha_hora: formato ISO 8601, ej: '2026-06-15T10:00:00'
    Retorna: dict con 'exito', 'evento_id', 'link', 'mensaje'
    """
    try:
        service = _get_service()
        calendar_id = os.environ.get("GOOGLE_CALENDAR_ID")
        if not calendar_id:
            raise ValueError("GOOGLE_CALENDAR_ID no está configurado en .env")

        inicio = datetime.fromisoformat(fecha_hora)
        fin = inicio + timedelta(minutes=duracion_minutos)

        evento = {
            "summary": f"Visita apartamento — {nombre}",
            "description": f"Interesado: {nombre}\nTeléfono: {telefono}",
            "start": {
                "dateTime": inicio.isoformat(),
                "timeZone": "America/Bogota",
            },
            "end": {
                "dateTime": fin.isoformat(),
                "timeZone": "America/Bogota",
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 60},
                    {"method": "popup", "minutes": 15},
                ],
            },
        }

        resultado = service.events().insert(
            calendarId=calendar_id, body=evento
        ).execute()

        return {
            "exito": True,
            "evento_id": resultado.get("id"),
            "link": resultado.get("htmlLink"),
            "mensaje": f"Visita agendada para {inicio.strftime('%d/%m/%Y a las %H:%M')}",
        }

    except HttpError as e:
        return {"exito": False, "mensaje": f"Error Google Calendar: {e}"}
    except Exception as e:
        return {"exito": False, "mensaje": f"Error inesperado: {e}"}


def verificar_disponibilidad(fecha_hora: str, duracion_minutos: int = 30) -> dict:
    """
    Verifica si un horario está disponible.
    Retorna: dict con 'disponible' y 'mensaje'
    """
    try:
        service = _get_service()
        calendar_id = os.environ.get("GOOGLE_CALENDAR_ID")

        inicio = datetime.fromisoformat(fecha_hora)
        fin = inicio + timedelta(minutes=duracion_minutos)

        body = {
            "timeMin": inicio.isoformat() + "-05:00",
            "timeMax": fin.isoformat() + "-05:00",
            "timeZone": "America/Bogota",
            "items": [{"id": calendar_id}],
        }

        resultado = service.freebusy().query(body=body).execute()
        ocupado = resultado["calendars"][calendar_id]["busy"]

        if ocupado:
            return {
                "disponible": False,
                "mensaje": f"El horario {inicio.strftime('%d/%m/%Y %H:%M')} ya está ocupado.",
            }
        return {
            "disponible": True,
            "mensaje": f"El horario {inicio.strftime('%d/%m/%Y %H:%M')} está disponible.",
        }

    except HttpError as e:
        return {"disponible": False, "mensaje": f"Error Google Calendar: {e}"}
    except Exception as e:
        return {"disponible": False, "mensaje": f"Error inesperado: {e}"}


def cancelar_visita(evento_id: str) -> dict:
    """
    Cancela una visita dado su evento_id.
    """
    try:
        service = _get_service()
        calendar_id = os.environ.get("GOOGLE_CALENDAR_ID")

        service.events().delete(
            calendarId=calendar_id, eventId=evento_id
        ).execute()

        return {"exito": True, "mensaje": "Visita cancelada correctamente."}

    except HttpError as e:
        return {"exito": False, "mensaje": f"Error Google Calendar: {e}"}
    except Exception as e:
        return {"exito": False, "mensaje": f"Error inesperado: {e}"}


def listar_visitas_proximas(dias: int = 7) -> dict:
    """
    Lista las visitas agendadas en los próximos N días.
    """
    try:
        service = _get_service()
        calendar_id = os.environ.get("GOOGLE_CALENDAR_ID")

        ahora = datetime.utcnow()
        limite = ahora + timedelta(days=dias)

        resultado = service.events().list(
            calendarId=calendar_id,
            timeMin=ahora.isoformat() + "Z",
            timeMax=limite.isoformat() + "Z",
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        eventos = resultado.get("items", [])
        visitas = []
        for e in eventos:
            inicio = e["start"].get("dateTime", e["start"].get("date"))
            visitas.append({
                "id": e["id"],
                "titulo": e.get("summary", "Sin título"),
                "inicio": inicio,
                "link": e.get("htmlLink"),
            })

        return {
            "exito": True,
            "total": len(visitas),
            "visitas": visitas,
        }

    except HttpError as e:
        return {"exito": False, "mensaje": f"Error Google Calendar: {e}"}
    except Exception as e:
        return {"exito": False, "mensaje": f"Error inesperado: {e}"}
