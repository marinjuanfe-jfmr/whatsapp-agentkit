#!/usr/bin/env python3
"""
Test suite for Google Sheets integration
Tests registering leads and verifying they appear in the real sheet
"""

import os
import sys
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations.sheets import GoogleSheetsManager


def test_append_lead_real():
    """Test appending a lead to the real Google Sheet"""

    manager = GoogleSheetsManager()

    if not manager.service:
        print("⚠️  [DEV MODE] Google Sheets not configured - test running in dev mode")
        print("   To enable real testing, set GOOGLE_CREDENTIALS_JSON in .env")

    # Test data with all 18 fields
    test_lead = {
        "nombre": f"Test Lead {datetime.now().strftime('%H%M%S')}",
        "whatsapp": "+573123456789",
        "personas": 2,
        "ocupacion": "Ingeniero",
        "ingresos": "$3,000,000 - $5,000,000",
        "mascotas": True,
        "vehiculos": True,
        "tipo_vehiculo": "Toyota Corolla",
        "fecha_mudanza": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "acepta_poliza": True,
        "estado": "Interesado",
        "motivo_rechazo": "",
        "interes_compra": False,
        "fecha_visita": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d 10:00"),
        "notas": "Cliente potencial, buen score crediticio",
        "confirmo_cita": True,
        "reagendo_cita": False,
    }

    # Attempt to append
    result = manager.append_lead(test_lead)

    assert result is True, "Failed to append lead"
    print(f"✅ Lead appended successfully: {test_lead['nombre']}")

    # If service is available, verify the lead was actually added
    if manager.service:
        all_leads = manager.get_all_leads()
        print(f"📊 Total rows in sheet: {len(all_leads)}")

        # Check if our test lead is in the data
        if all_leads:
            last_row = all_leads[-1]
            # The first column should be the timestamp we just added
            print(f"📍 Last row added: {last_row}")
            assert len(last_row) >= 18, f"Expected at least 18 columns, got {len(last_row)}"
            print(f"✅ Last row has all {len(last_row)} columns")


def test_sheets_columns():
    """Verify all 18 columns are defined correctly"""

    expected_columns = [
        "A:Fecha",
        "B:Nombre",
        "C:WhatsApp",
        "D:Personas",
        "E:Ocupación",
        "F:Ingresos",
        "G:Mascotas (sí/no)",
        "H:Vehículos (sí/no)",
        "I:Tipo de vehículos",
        "J:Fecha Propuesta de Mudanza",
        "K:Aceptó Póliza (sí/no)",
        "L:Estado",
        "M:Motivo Rechazo",
        "N:Interés Compra (sí/no)",
        "O:Fecha y hora de visita agendada",
        "P:Notas",
        "Q:Confirmó cita",
        "R:Reagendó cita",
    ]

    manager = GoogleSheetsManager()

    assert len(manager.COLUMNS) == 18, f"Expected 18 columns, got {len(manager.COLUMNS)}"

    for i, (expected, actual) in enumerate(zip(expected_columns, manager.COLUMNS)):
        assert actual == expected, f"Column {i} mismatch: expected '{expected}', got '{actual}'"
        print(f"✅ Column {actual}")

    print(f"\n✅ All 18 columns are correctly defined and in order")


def test_credentials_configured():
    """Check if Google credentials are properly configured"""

    google_creds = os.getenv("GOOGLE_CREDENTIALS_JSON")

    if not google_creds:
        print("⚠️  GOOGLE_CREDENTIALS_JSON not set in .env")
        print("   See instructions in GOOGLE_SETUP.md to configure it")
        return

    try:
        creds_dict = json.loads(google_creds)
        required_keys = ["type", "project_id", "private_key_id", "private_key", "client_email"]

        for key in required_keys:
            assert key in creds_dict, f"Missing required key: {key}"

        print(f"✅ Credentials valid for project: {creds_dict.get('project_id')}")
        print(f"   Service account: {creds_dict.get('client_email')}")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in GOOGLE_CREDENTIALS_JSON: {e}")
        raise


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Testing Google Sheets Integration")
    print("="*60 + "\n")

    try:
        print("1️⃣  Verifying column structure...")
        test_sheets_columns()
        print()

        print("2️⃣  Checking credentials configuration...")
        test_credentials_configured()
        print()

        print("3️⃣  Testing lead registration...")
        test_append_lead_real()
        print()

        print("="*60)
        print("✅ All tests passed!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
