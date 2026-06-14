"""
Script de diagnóstico rápido - corre en Railway con:
python test_integrations.py
"""
import os, json, sys
from datetime import datetime

print("=" * 50)
print("DIAGNÓSTICO DE INTEGRACIONES")
print("=" * 50)

# 1. TELEGRAM
print("\n[1] TELEGRAM")
try:
    import requests
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("  ERROR: Variables no configuradas")
    else:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": "TEST: Diagnostico agente Los Robles"},
            timeout=10
        )
        if r.status_code == 200:
            print("  OK: Mensaje enviado")
        else:
            print(f"  ERROR {r.status_code}: {r.text}")
except Exception as e:
    print(f"  EXCEPTION: {e}")

# 2. GOOGLE SHEETS - leer y escribir
print("\n[2] GOOGLE SHEETS")
try:
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    sheets_id = os.getenv("GOOGLE_SHEETS_ID")
    if not creds_json or not sheets_id:
        print("  ERROR: Variables no configuradas")
    else:
        creds_dict = json.loads(creds_json)
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        creds = Credentials.from_service_account_info(
            creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        service = build("sheets", "v4", credentials=creds)
        
        # Leer columna C para ver qué números hay
        result = service.spreadsheets().values().get(
            spreadsheetId=sheets_id, range="Sheet1!C:C"
        ).execute()
        rows = result.get("values", [])
        print(f"  OK: Sheet accesible, {len(rows)} filas en col C")
        print(f"  Valores col C: {[r[0] for r in rows if r][:5]}")
        
        # Intentar escribir fila de prueba con número real
        test_phone = "TEST_57300000001"
        test_row = [[
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            "TEST Lead", test_phone, 2, "Prueba", "",
            "No", "No", "", "inmediato", "Si",
            "Prueba", "", "No", "2026-06-13 14:00", "", "No", "No"
        ]]
        service.spreadsheets().values().append(
            spreadsheetId=sheets_id,
            range="Sheet1!A:R",
            valueInputOption="USER_ENTERED",
            body={"values": test_row}
        ).execute()
        print(f"  OK: Fila de prueba escrita con phone={test_phone}")
        
        # Verificar upsert: buscar ese número y actualizar
        result2 = service.spreadsheets().values().get(
            spreadsheetId=sheets_id, range="Sheet1!C:C"
        ).execute()
        rows2 = result2.get("values", [])
        found_row = None
        for i, row in enumerate(rows2):
            if row and row[0] == test_phone:
                found_row = i + 1
                break
        if found_row:
            print(f"  OK: Upsert funciona - fila encontrada en row {found_row}")
        else:
            print("  ERROR: No se encontró la fila recién escrita")

except Exception as e:
    import traceback
    print(f"  EXCEPTION: {e}")
    traceback.print_exc()

# 3. GOOGLE CALENDAR
print("\n[3] GOOGLE CALENDAR")
try:
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    cal_id = os.getenv("GOOGLE_CALENDAR_ID")
    if not creds_json or not cal_id:
        print("  ERROR: Variables no configuradas")
    else:
        creds_dict = json.loads(creds_json)
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        from zoneinfo import ZoneInfo
        from datetime import timedelta
        creds = Credentials.from_service_account_info(
            creds_dict, scopes=["https://www.googleapis.com/auth/calendar"]
        )
        service = build("calendar", "v3", credentials=creds)
        now = datetime.now(ZoneInfo("America/Bogota"))
        print(f"  Hora actual Bogota: {now.strftime('%Y-%m-%d %H:%M %Z')}")
        # Listar próximos eventos
        events = service.events().list(
            calendarId=cal_id,
            timeMin=now.isoformat(),
            maxResults=3,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        items = events.get("items", [])
        print(f"  OK: Calendar accesible, {len(items)} eventos próximos")
        for e in items:
            print(f"    - {e.get('summary')} @ {e['start'].get('dateTime', e['start'].get('date'))}")
except Exception as e:
    import traceback
    print(f"  EXCEPTION: {e}")
    traceback.print_exc()

print("\n" + "=" * 50)
print("FIN DIAGNÓSTICO")
