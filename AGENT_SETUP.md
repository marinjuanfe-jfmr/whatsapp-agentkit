# Agente de Arriendo Los Robles — Guía de Instalación

## Requisitos

- Python 3.9+
- pip
- API keys configuradas en `.env`

## Instalación

### 1. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Copia `.env.example` a `.env` y completa todos los valores:

```bash
cp .env.example .env
```

**Variables requeridas:**
- `ANTHROPIC_API_KEY` - Tu API key de Claude
- `YCLOUD_API_KEY` - Tu API key de YCloud
- `YCLOUD_PHONE_NUMBER` - Número de teléfono del bot
- `TELEGRAM_BOT_TOKEN` - Token de tu bot de Telegram
- `TELEGRAM_CHAT_ID` - ID del chat para alertas
- `GOOGLE_CALENDAR_ID` - ID del calendario de Google
- `GOOGLE_CREDENTIALS_JSON` - Credenciales de Google (JSON)
- `GOOGLE_SHEETS_ID` - ID del Google Sheet para leads

### 4. Inicializar base de datos

```bash
python -c "from agent.memory import init_db; init_db()"
```

## Ejecución

### Desarrollo

```bash
python -m uvicorn agent.main:app --reload --port 8000
```

El agente estará disponible en: `http://localhost:8000`

### Producción

```bash
python -m uvicorn agent.main:app --host 0.0.0.0 --port 8000
```

## Verificación

Endpoint de salud: `GET http://localhost:8000/health`

```bash
curl http://localhost:8000/health
# Respuesta esperada: {"status":"ok"}
```

## Configuración de Webhook

En YCloud, configura el webhook para que apunte a:

```
POST https://tu-dominio.com/webhook/ycloud
```

Incluye el secret en el header `X-YCloud-Signature`.

## Archivos de Configuración

- `config/business.yaml` - Datos del apartamento y tiempos
- `config/prompts.yaml` - System prompt del agente Claude
- `knowledge/apartamento.txt` - Características del apartamento
- `knowledge/calificacion.txt` - Criterios y flujo de calificación

## Estructura de Base de Datos

Se crea automáticamente con SQLite (`agentkit.db`):

- **conversations**: Historial de mensajes por usuario
- **leads**: Datos de leads y calificaciones
- **appointments**: Citas agendadas

## Troubleshooting

### "ModuleNotFoundError: No module named 'agent'"

Asegúrate de ejecutar desde la raíz del proyecto:
```bash
cd /ruta/al/whatsapp-agentkit
python -m uvicorn agent.main:app --reload
```

### "SQLAlchemy error"

Borra `agentkit.db` y reinicia para recrear la DB:
```bash
rm agentkit.db
python -c "from agent.memory import init_db; init_db()"
```

### Google APIs no funcionan

Verifica que `GOOGLE_CREDENTIALS_JSON` sea válido JSON:
```bash
python -c "import json, os; json.loads(os.getenv('GOOGLE_CREDENTIALS_JSON'))"
```

## Logs y Debugging

Para más verbosidad:

```bash
export DEBUG=1
python -m uvicorn agent.main:app --reload --log-level debug
```

## Deployment en Railway

```bash
railway up
```

O en la web: https://railway.app/dashboard
