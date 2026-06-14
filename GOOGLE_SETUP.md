# Configuración de Google Sheets - Guía Paso a Paso

## 1️⃣ Obtener el archivo de credenciales

Ya tienes el archivo JSON de Google Service Account. Este archivo contiene algo como:

```json
{
  "type": "service_account",
  "project_id": "tu-proyecto-123",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----\n",
  "client_email": "agent@tu-proyecto-123.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/...",
  "universe_domain": "googleapis.com"
}
```

## 2️⃣ Preparar el JSON para el .env

### OPCIÓN A (Recomendada): JSON en una sola línea en el .env

El código en `integrations/sheets.py` usa:
```python
creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
```

Esto significa que debes colocar todo el JSON en **una sola línea**, sin saltos ni espacios extra.

**Pasos:**

1. Abre tu archivo `service-account.json` (o el nombre que tenga)
2. Selecciona TODO el contenido
3. Cópialo completamente
4. Abre `.env` en tu editor
5. En la línea `GOOGLE_CREDENTIALS_JSON=` (línea 21), pega el JSON directamente:

```
GOOGLE_CREDENTIALS_JSON={"type":"service_account","project_id":"tu-proyecto","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\nMIIE...","client_email":"agent@...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"...","universe_domain":"googleapis.com"}
```

⚠️ **IMPORTANTE:**
- ✅ Todo debe estar en **UNA SOLA LÍNEA**
- ✅ Sin saltos de línea (`\n` literales se convierten a espacios)
- ✅ Sin espacios extra entre campos
- ✅ El `private_key` contiene `\n` (mantén esos tal cual, son parte del key)

### Verificación rápida:

Abre PowerShell en la carpeta del proyecto y ejecuta:

```powershell
python -c "import os; import json; print(json.loads(os.getenv('GOOGLE_CREDENTIALS_JSON')).get('project_id'))"
```

Debería mostrar tu `project_id` sin errores.

## 3️⃣ Crear el Google Sheet

1. Ve a [Google Sheets](https://sheets.google.com)
2. Crea una nueva hoja de cálculo
3. En la primera fila, agrega estos encabezados en las columnas A-R:

| A | B | C | D | E | F | G | H | I | J | K | L | M | N | O | P | Q | R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Fecha | Nombre | WhatsApp | Personas | Ocupación | Ingresos | Mascotas (sí/no) | Vehículos (sí/no) | Tipo de vehículos | Fecha Propuesta de Mudanza | Aceptó Póliza (sí/no) | Estado | Motivo Rechazo | Interés Compra (sí/no) | Fecha y hora de visita agendada | Notas | Confirmó cita | Reagendó cita |

4. Copia el ID de la hoja (está en la URL):
   - URL: `https://docs.google.com/spreadsheets/d/1HN3rbGtlikkI9cw3nHgrgwwwwtIIfWm8o8UDLRTAnjg/edit`
   - ID: `1HN3rbGtlikkI9cw3nHgrgwwwwtIIfWm8o8UDLRTAnjg`

5. En `.env`, actualiza:
   ```
   GOOGLE_SHEETS_ID=1HN3rbGtlikkI9cw3nHgrgwwwwtIIfWm8o8UDLRTAnjg
   ```

## 4️⃣ Compartir la hoja con el Service Account

1. En Google Sheets, haz clic en "Compartir" (esquina superior derecha)
2. En "Invitar a personas", pega el `client_email` del JSON:
   ```
   agent@tu-proyecto-123.iam.gserviceaccount.com
   ```
3. Dale permiso de "Editor"
4. Haz clic en "Compartir"

## 5️⃣ Probar la integración

### Opción A: Usar Python directamente

```bash
python tests/test_sheets.py
```

Verás algo como:
```
============================================================
Testing Google Sheets Integration
============================================================

1️⃣  Verifying column structure...
✅ Column A:Fecha
✅ Column B:Nombre
...
✅ All 18 columns are correctly defined and in order

2️⃣  Checking credentials configuration...
✅ Credentials valid for project: tu-proyecto-123
   Service account: agent@tu-proyecto-123.iam.gserviceaccount.com

3️⃣  Testing lead registration...
✅ Lead appended successfully: Test Lead 143052
📊 Total rows in sheet: 2
📍 Last row added: ['2026-06-02 14:30:52', 'Test Lead 143052', ...]
✅ Last row has all 18 columns

============================================================
✅ All tests passed!
============================================================
```

### Opción B: Test desde Python interactivo

```python
from integrations.sheets import GoogleSheetsManager

manager = GoogleSheetsManager()

# Registrar un lead de prueba
test_lead = {
    "nombre": "Juan Test",
    "whatsapp": "+573123456789",
    "personas": 2,
    "ocupacion": "Ingeniero",
    "ingresos": "$3,000,000",
    "mascotas": True,
    "vehiculos": True,
    "tipo_vehiculo": "Honda Civic",
    "fecha_mudanza": "2026-07-02",
    "acepta_poliza": True,
    "estado": "Interesado",
    "motivo_rechazo": "",
    "interes_compra": False,
    "fecha_visita": "2026-06-04 10:00",
    "notas": "Cliente potencial",
    "confirmo_cita": True,
    "reagendo_cita": False,
}

manager.append_lead(test_lead)

# Ver todos los leads
all_leads = manager.get_all_leads()
print(f"Total leads: {len(all_leads)}")
```

## 6️⃣ Verificar que todo está correcto

Después de pegar el JSON y ejecutar el test:

1. ✅ El test debería pasar sin errores
2. ✅ En Google Sheets, deberías ver una nueva fila con los datos del test
3. ✅ Las 18 columnas deberían estar todas presentes

## 📋 Checklist final

- [ ] Tengo el archivo `service-account.json` con las credenciales de Google
- [ ] He pegado el contenido JSON completo en `GOOGLE_CREDENTIALS_JSON=` en `.env` (todo en una línea)
- [ ] He actualizado `GOOGLE_SHEETS_ID` en `.env` con mi sheet ID
- [ ] He compartido el sheet con el email del service account (con permisos de Editor)
- [ ] He ejecutado `python tests/test_sheets.py` y pasó exitosamente
- [ ] Puedo ver los datos de prueba en mi Google Sheet

## ❓ Solución de problemas

### Error: "json.decoder.JSONDecodeError: Extra data"
**Causa:** El JSON tiene saltos de línea
**Solución:** Asegúrate de que el JSON esté en una sola línea sin quiebres

### Error: "403 Forbidden"
**Causa:** El sheet no está compartido con el service account
**Solución:** Ve a Google Sheets → Compartir → Agrega `client_email`

### Error: "Invalid JSON"
**Causa:** Falta una comilla o hay un error de formato
**Solución:** Valida el JSON en [jsonlint.com](https://jsonlint.com)

### Los datos no aparecen en el sheet
**Causa:** El `GOOGLE_SHEETS_ID` es incorrecto
**Solución:** Verifica el ID en la URL del sheet

## 🔐 Seguridad

⚠️ **NUNCA** commits `.env` a GitHub
- El `.env` ya está en `.gitignore`
- El JSON contiene credenciales privadas
- En producción, usa variables de entorno secretas (Railway, etc.)
