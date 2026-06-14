# ✅ Google Sheets Integration - Setup Checklist

## 📋 Lo que ya está hecho

- [x] `sheets.py` tiene las **18 columnas correctas** en orden
- [x] `tests/test_sheets.py` creado y listo para probar
- [x] `prepare_google_credentials.py` script creado para ayudarte

---

## 🚀 Tu checklist de configuración

### 1️⃣ Obtén tu JSON de Google Service Account
```
[ ] Tengo el archivo service-account.json descargado
[ ] Sé dónde está ubicado en mi computadora
```

### 2️⃣ Prepara el JSON para el .env
**Opción A (Recomendada - Automática):**
```bash
python prepare_google_credentials.py "C:\Users\tu-usuario\ruta\service-account.json"
```

**Opción B (Manual):**
1. Abre el JSON con un editor de texto
2. Selecciona TODO el contenido
3. Copia a un convertidor JSON: https://www.tools4noobs.com/online_tools/minify_json/
4. Obtén el resultado en una sola línea

### 3️⃣ Configura el .env
```
[ ] Abrí el archivo .env en el editor
[ ] Encontré la línea: GOOGLE_CREDENTIALS_JSON=
[ ] Pegué el JSON completo sin saltos de línea
[ ] Guardé el archivo .env
```

**Cómo debería verse:**
```env
GOOGLE_CREDENTIALS_JSON={"type":"service_account","project_id":"...","private_key":"..."}
```

### 4️⃣ Obtén tu Google Sheets ID
```
[ ] Creé un nuevo Google Sheet
[ ] Copié el ID de la URL
```

**Donde encontrarlo:**
```
URL: https://docs.google.com/spreadsheets/d/1HN3rbGtlikkI9cw3nHgrgwwwwtIIfWm8o8UDLRTAnjg/edit
ID:  1HN3rbGtlikkI9cw3nHgrgwwwwtIIfWm8o8UDLRTAnjg
                                    ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
```

### 5️⃣ Actualiza GOOGLE_SHEETS_ID en .env
```
[ ] Actualicé la línea 24 del .env con mi sheet ID
[ ] Guardé el archivo
```

### 6️⃣ Comparte el sheet con Google Service Account
```
[ ] Abrí el Google Sheet
[ ] Hice clic en "Compartir"
[ ] Pegué el email: agentkit@agentkit-robles.iam.gserviceaccount.com
[ ] Asigné permisos de "Editor"
[ ] Hice clic en "Compartir"
```

### 7️⃣ Crea los encabezados en el Google Sheet
```
[ ] Abrí el Google Sheet
[ ] En la fila 1, agregué estos encabezados:
```

| A | B | C | D | E | F | G | H | I | J | K | L | M | N | O | P | Q | R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Fecha | Nombre | WhatsApp | Personas | Ocupación | Ingresos | Mascotas (sí/no) | Vehículos (sí/no) | Tipo de vehículos | Fecha Propuesta de Mudanza | Aceptó Póliza (sí/no) | Estado | Motivo Rechazo | Interés Compra (sí/no) | Fecha y hora de visita agendada | Notas | Confirmó cita | Reagendó cita |

### 8️⃣ Prueba la integración
```bash
python tests/test_sheets.py
```

```
[ ] El test pasó exitosamente
[ ] Vi un nuevo row en el Google Sheet
[ ] Las 18 columnas están presentes
```

---

## 📋 Verificación final

```bash
# Verifica que el JSON es válido
python -c "import os, json; json.loads(os.getenv('GOOGLE_CREDENTIALS_JSON'))"
# Debería mostrar: (sin errores)
```

```bash
# Verifica que el sheet ID es correcto
python tests/test_sheets.py
# Debería mostrar: ✅ All tests passed!
```

---

## 🎯 Resumen

| Paso | Acción | Estado |
|------|--------|--------|
| 1 | sheets.py tiene 18 columnas | ✅ Hecho |
| 2 | test_sheets.py existe | ✅ Hecho |
| 3 | prepare_google_credentials.py existe | ✅ Hecho |
| 4 | Extraer JSON a una sola línea | 👤 Tu turno |
| 5 | Pegar en GOOGLE_CREDENTIALS_JSON= | 👤 Tu turno |
| 6 | Actualizar GOOGLE_SHEETS_ID | 👤 Tu turno |
| 7 | Compartir sheet con service account | 👤 Tu turno |
| 8 | Crear encabezados en sheet | 👤 Tu turno |
| 9 | Ejecutar python tests/test_sheets.py | 👤 Tu turno |

---

## 🆘 Problemas comunes

### ❌ "json.decoder.JSONDecodeError"
**Problema:** El JSON tiene saltos de línea  
**Solución:** Asegúrate de que TODO esté en una sola línea

### ❌ "403 Forbidden"
**Problema:** El sheet no está compartido  
**Solución:** Ve a Compartir → Agrega el email del service account

### ❌ "Sheet not found"
**Problema:** GOOGLE_SHEETS_ID es incorrecto  
**Solución:** Copia el ID correctamente de la URL

---

## 📚 Documentación completa

Para más detalles, ve a:
- `GOOGLE_SETUP.md` - Guía detallada paso a paso
- `GOOGLE_CREDENTIALS_README.txt` - Referencia rápida
- `.env.google-example` - Ejemplo de .env

---

**Una vez completado este checklist, estarás listo para registrar leads en Google Sheets.** ✨
