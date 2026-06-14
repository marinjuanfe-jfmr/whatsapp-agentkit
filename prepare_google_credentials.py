#!/usr/bin/env python3
"""
Script para preparar credenciales de Google para el .env

Uso:
    python prepare_google_credentials.py path/to/service-account.json

Esto mostrará el JSON en una sola línea, listo para copiar al .env
"""

import json
import sys
import os
from pathlib import Path


def prepare_credentials(json_file_path):
    """Load JSON and output as single-line string"""

    if not os.path.exists(json_file_path):
        print(f"❌ Archivo no encontrado: {json_file_path}")
        sys.exit(1)

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            creds = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error al parsear JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error al leer archivo: {e}")
        sys.exit(1)

    # Validate required fields
    required_fields = [
        "type",
        "project_id",
        "private_key_id",
        "private_key",
        "client_email",
        "client_id",
        "auth_uri",
        "token_uri",
    ]

    missing = [f for f in required_fields if f not in creds]
    if missing:
        print(f"⚠️  Campos faltantes: {', '.join(missing)}")
        print("   (Esto podría causar problemas más adelante)")

    # Convert to single-line JSON
    single_line_json = json.dumps(creds, separators=(',', ':'))

    # Display instructions
    print("\n" + "="*80)
    print("✅ CREDENCIALES PREPARADAS")
    print("="*80 + "\n")

    print(f"📋 Proyecto: {creds.get('project_id')}")
    print(f"👤 Service Account: {creds.get('client_email')}")
    print()

    print("📌 INSTRUCCIONES:")
    print("-" * 80)
    print("1. Abre el archivo .env")
    print("2. Encuentra la línea: GOOGLE_CREDENTIALS_JSON=")
    print("3. Borra cualquier contenido después del = ")
    print("4. Copia TODO el siguiente JSON (todo debe estar en una sola línea)")
    print("-" * 80)
    print()

    # Show the JSON with wrapping for readability
    print("Copia esto exactamente (todo en UNA SOLA LÍNEA):")
    print()
    print(f"GOOGLE_CREDENTIALS_JSON={single_line_json}")
    print()

    print("-" * 80)
    print("\n✨ PASOS SIGUIENTES:")
    print()
    print("1. Abre .env en tu editor (Visual Studio Code, Notepad++, etc.)")
    print("2. Busca la línea: GOOGLE_CREDENTIALS_JSON=")
    print("3. Borra lo que tenga después del = (si algo)")
    print("4. Pega el JSON completo (está en tu portapapeles)")
    print("5. Guarda el archivo (.env)")
    print()
    print("6. Compartir en Google Sheets:")
    print(f"   - Ve a tu sheet de Google")
    print(f"   - Haz clic en 'Compartir'")
    print(f"   - Pega este email: {creds.get('client_email')}")
    print(f"   - Dale permisos de 'Editor'")
    print()
    print("7. Ejecuta el test:")
    print("   python tests/test_sheets.py")
    print()
    print("=" * 80)

    return single_line_json


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python prepare_google_credentials.py <ruta-al-json>")
        print()
        print("Ejemplo:")
        print("  python prepare_google_credentials.py ~/Downloads/service-account.json")
        print()
        sys.exit(1)

    json_file = sys.argv[1]
    prepare_credentials(json_file)


if __name__ == "__main__":
    main()
