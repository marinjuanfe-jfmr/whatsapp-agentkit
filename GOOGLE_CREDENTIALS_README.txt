╔════════════════════════════════════════════════════════════════════════════════╗
║                  CONFIGURACIÓN DE GOOGLE CREDENTIALS - GUÍA RÁPIDA              ║
╚════════════════════════════════════════════════════════════════════════════════╝

📋 RESUMEN DE LO QUE YA ESTÁ VERIFICADO:
═══════════════════════════════════════════════════════════════════════════════════

✅ sheets.py tiene las 18 columnas correctas en orden:
   A:Fecha, B:Nombre, C:WhatsApp, D:Personas, E:Ocupación, F:Ingresos,
   G:Mascotas (sí/no), H:Vehículos (sí/no), I:Tipo de vehículos,
   J:Fecha Propuesta de Mudanza, K:Aceptó Póliza (sí/no), L:Estado,
   M:Motivo Rechazo, N:Interés Compra (sí/no), O:Fecha y hora de visita,
   P:Notas, Q:Confirmó cita, R:Reagendó cita

✅ tests/test_sheets.py creado con todo lo necesario

✅ GOOGLE_CREDENTIALS_JSON vacío en .env (línea 21) - LISTO PARA LLENAR


═══════════════════════════════════════════════════════════════════════════════════
🔑 PASO 1: PREPARAR EL JSON PARA EL .env
═══════════════════════════════════════════════════════════════════════════════════

Tu archivo JSON de Google Service Account se ve así:

  {
    "type": "service_account",
    "project_id": "agentkit-robles",
    "private_key_id": "abc123...",
    "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
    "client_email": "agentkit@agentkit-robles.iam.gserviceaccount.com",
    ...
  }

El código en integrations/sheets.py hace:
  creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)

Por lo tanto: TODO EL JSON DEBE ESTAR EN UNA SOLA LÍNEA


═══════════════════════════════════════════════════════════════════════════════════
⚡ MÉTODO RÁPIDO: Usar el script Python
═══════════════════════════════════════════════════════════════════════════════════

1. Abre PowerShell/Terminal en la carpeta del proyecto

2. Ejecuta:
   python prepare_google_credentials.py "C:\Users\tu-usuario\Downloads\service-account.json"

   (Reemplaza la ruta con la ubicación real de tu JSON)

3. El script mostrará el JSON listo para copiar. Haz Ctrl+C para copiarlo

4. Abre .env y reemplaza la línea 21:

   ANTES:
   GOOGLE_CREDENTIALS_JSON=

   DESPUÉS:
   GOOGLE_CREDENTIALS_JSON={"type":"service_account","project_id":"...","private_key":"..."}


═══════════════════════════════════════════════════════════════════════════════════
📋 PASO 2: OBTENER TU GOOGLE SHEETS ID
═══════════════════════════════════════════════════════════════════════════════════

1. Crea un nuevo Google Sheet en https://sheets.google.com
2. En la URL verás:
   https://docs.google.com/spreadsheets/d/1HN3rbGtlikkI9cw3nHgrgwwwwtIIfWm8o8UDLRTAnjg/edit

3. Copia el ID (la parte larga entre /d/ y /edit):
   1HN3rbGtlikkI9cw3nHgrgwwwwtIIfWm8o8UDLRTAnjg

4. En .env, actualiza la línea 24:
   GOOGLE_SHEETS_ID=1HN3rbGtlikkI9cw3nHgrgwwwwtIIfWm8o8UDLRTAnjg


═══════════════════════════════════════════════════════════════════════════════════
✉️ PASO 3: COMPARTIR SHEET CON EL SERVICE ACCOUNT
═══════════════════════════════════════════════════════════════════════════════════

1. En tu Google Sheet, haz clic en "Compartir" (esquina superior derecha)

2. En "Invitar a personas", pega el client_email de tu JSON:
   agentkit@agentkit-robles.iam.gserviceaccount.com

3. Dale permisos de "Editor"

4. Haz clic en "Compartir"

Ahora el script Python podrá escribir en el sheet.


═══════════════════════════════════════════════════════════════════════════════════
🧪 PASO 4: PROBAR LA INTEGRACIÓN
═══════════════════════════════════════════════════════════════════════════════════

Abre PowerShell en la carpeta del proyecto y ejecuta:

  python tests/test_sheets.py

Deberías ver:

  ============================================================
  Testing Google Sheets Integration
  ============================================================

  1️⃣  Verifying column structure...
  ✅ Column A:Fecha
  ✅ Column B:Nombre
  ... (todas las 18 columnas)

  2️⃣  Checking credentials configuration...
  ✅ Credentials valid for project: agentkit-robles
     Service account: agentkit@agentkit-robles.iam.gserviceaccount.com

  3️⃣  Testing lead registration...
  ✅ Lead appended successfully: Test Lead 143052
  📊 Total rows in sheet: 2
  📍 Last row added: ['2026-06-02 14:30:52', 'Test Lead 143052', ...]

  ============================================================
  ✅ All tests passed!
  ============================================================

✅ Si ves esto, TODO está funcionando correctamente.


═══════════════════════════════════════════════════════════════════════════════════
⚠️ ERRORES COMUNES
═══════════════════════════════════════════════════════════════════════════════════

ERROR: "json.decoder.JSONDecodeError: Extra data"
→ El JSON tiene saltos de línea. Debe estar TODO en una sola línea.

ERROR: "403 Forbidden"
→ El sheet no está compartido con el service account. Ve a Compartir → Agrega el email.

ERROR: "Invalid JSON"
→ Valida en https://jsonlint.com

ERROR: "No such file or directory"
→ El GOOGLE_SHEETS_ID es incorrecto. Verifica la URL del sheet.


═══════════════════════════════════════════════════════════════════════════════════
🔐 SEGURIDAD
═══════════════════════════════════════════════════════════════════════════════════

⚠️ NUNCA hagas git add .env
   • El archivo .env ya está en .gitignore ✓
   • Contiene credenciales privadas
   • En producción, usa variables de entorno secretas (Railway, GitHub Secrets, etc.)


═══════════════════════════════════════════════════════════════════════════════════
📁 ARCHIVOS CREADOS
═══════════════════════════════════════════════════════════════════════════════════

✅ tests/test_sheets.py
   Test completo que registra un lead de prueba

✅ GOOGLE_SETUP.md
   Guía detallada paso a paso

✅ .env.google-example
   Ejemplo de cómo debería verse tu .env (NO usar directamente)

✅ prepare_google_credentials.py
   Script para convertir tu JSON a una sola línea


═══════════════════════════════════════════════════════════════════════════════════
✨ PRÓXIMOS PASOS
═══════════════════════════════════════════════════════════════════════════════════

1. Ejecuta: python prepare_google_credentials.py "ruta/a/tu/service-account.json"
2. Copia el JSON completo que aparece
3. Abre .env y pégalo en GOOGLE_CREDENTIALS_JSON=
4. Actualiza GOOGLE_SHEETS_ID con tu sheet ID
5. Comparte el sheet con el client_email del JSON
6. Ejecuta: python tests/test_sheets.py
7. ✅ ¡Listo!

═══════════════════════════════════════════════════════════════════════════════════
