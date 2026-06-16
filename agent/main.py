import os
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

from agent.brain import AgentBrain
from agent.memory import init_db, Memory
from agent.scheduler import TaskScheduler
from integrations.whapi import WhapiClient
from integrations.telegram import TelegramNotifier

app = FastAPI(title="Agente de Arriendo Los Robles")

brain = AgentBrain()
whapi = WhapiClient()
telegram = TelegramNotifier()
scheduler = TaskScheduler()

init_db()

PORT = int(os.getenv("PORT", 8000))

DIRECCION_APARTAMENTO = (
    "La dirección es: Carrera 111A No. 88B-51, Interior 16, Apto 202, "
    "Conjunto Residencial Los Robles.\n"
    "Ubicación en Google Maps: https://maps.app.goo.gl/MZw9n3NBcLqmoHBQ9\n"
    "Cualquier cosa, Juan Felipe Marín "
    "(el propietario) puede contactarte desde otro número para coordinar "
    "temas adicionales."
)

# Palabras clave que indican intención de reagendar
RESCHEDULE_KEYWORDS = [
    "reagendar", "reagendé", "cambiar la cita", "cambiar cita", "cambiar la visita",
    "cambiar visita", "otra fecha", "otro día", "otro horario", "no puedo ir",
    "no voy a poder", "cambia la cita", "cambia la visita", "modificar la cita",
    "mover la cita", "posponer", "aplazar", "diferente día", "diferente fecha",
]

# --- Protección anti-bot ---
RATE_LIMIT_MAX_MESSAGES = 5       # máximo de mensajes permitidos...
RATE_LIMIT_WINDOW_SECONDS = 120   # ...en esta ventana de tiempo (2 minutos)
REPEAT_DETECTION_COUNT = 3        # cuántos mensajes iguales consecutivos disparan el bloqueo


def user_wants_reschedule(message_text: str) -> bool:
    """Detectar si el usuario está pidiendo reagendar"""
    text_lower = message_text.lower()
    return any(kw in text_lower for kw in RESCHEDULE_KEYWORDS)


def check_rate_limit(memory: Memory, phone_number: str) -> bool:
    """
    Retorna True si el número supera el rate limit.
    Cuenta mensajes de rol 'user' en los últimos RATE_LIMIT_WINDOW_SECONDS segundos.
    """
    from sqlalchemy import func
    from agent.models import Conversation

    cutoff = datetime.utcnow() - timedelta(seconds=RATE_LIMIT_WINDOW_SECONDS)
    count = (
        memory.db.query(func.count(Conversation.id))
        .filter(
            Conversation.phone_number == phone_number,
            Conversation.role == "user",
            Conversation.timestamp >= cutoff,
        )
        .scalar()
    )
    return count >= RATE_LIMIT_MAX_MESSAGES


def check_repeated_messages(memory: Memory, phone_number: str, current_message: str) -> bool:
    """
    Retorna True si los últimos REPEAT_DETECTION_COUNT mensajes del usuario
    son idénticos al mensaje actual (normalizado a minúsculas sin espacios extra).
    """
    from agent.models import Conversation
    from sqlalchemy import desc

    recent = (
        memory.db.query(Conversation)
        .filter(
            Conversation.phone_number == phone_number,
            Conversation.role == "user",
        )
        .order_by(desc(Conversation.timestamp))
        .limit(REPEAT_DETECTION_COUNT - 1)  # los anteriores al actual
        .all()
    )

    if len(recent) < REPEAT_DETECTION_COUNT - 1:
        return False

    normalized_current = " ".join(current_message.lower().split())
    for msg in recent:
        normalized = " ".join(msg.message.lower().split())
        if normalized != normalized_current:
            return False
    return True


def is_bot_alert_already_sent(memory: Memory, phone_number: str) -> bool:
    """
    Evita enviar múltiples alertas Telegram por el mismo episodio de bot.
    Usa la nota 'bot_alert_sent' en el campo notas del lead.
    """
    lead = memory.get_lead(phone_number)
    if not lead or not lead.notas:
        return False
    return "bot_alert_sent" in lead.notas.split("|")


def mark_bot_alert_sent(memory: Memory, phone_number: str) -> None:
    """Marca que ya se envió alerta de bot para este número."""
    lead = memory.get_lead(phone_number)
    notas_actuales = lead.notas if lead and lead.notas else ""
    notas_lista = [n for n in notas_actuales.split("|") if n] if notas_actuales else []
    if "bot_alert_sent" not in notas_lista:
        notas_lista.append("bot_alert_sent")
        memory.update_lead(phone_number, notas="|".join(notas_lista))


def clear_bot_alert_flag(memory: Memory, phone_number: str) -> None:
    """
    Limpia la marca de alerta de bot cuando la actividad vuelve a la normalidad.
    Se llama al inicio de cada mensaje si NO hay rate limit activo.
    """
    lead = memory.get_lead(phone_number)
    if not lead or not lead.notas:
        return
    notas_lista = [n for n in lead.notas.split("|") if n and n != "bot_alert_sent"]
    nueva_notas = "|".join(notas_lista) or None
    if nueva_notas != lead.notas:
        memory.update_lead(phone_number, notas=nueva_notas)


async def process_message_background(phone_number: str, message_text: str):
    try:
        memory = Memory()

        # ---------------------------------------------------------------
        # PROTECCIÓN ANTI-BOT — debe ir antes de cualquier otra lógica
        # ---------------------------------------------------------------

        # 1. Guardar el mensaje del usuario en historial ANTES de los checks
        #    (necesario para que check_rate_limit y check_repeated_messages
        #     cuenten el mensaje actual)
        memory.save_conversation(phone_number, "user", message_text)
        from integrations.sheets import GoogleSheetsManager
        sheets = GoogleSheetsManager()
        sheets.append_message(phone_number, "user", message_text)

        # 2. Rate limit: ¿demasiados mensajes en poco tiempo?
        rate_exceeded = check_rate_limit(memory, phone_number)

        # 3. Repetición: ¿mismo mensaje N veces seguidas?
        repeat_detected = check_repeated_messages(memory, phone_number, message_text)

        if rate_exceeded or repeat_detected:
            reason = "rate_limit" if rate_exceeded else "repeated_messages"
            print(f"[ANTIBOT] Bloqueado {phone_number} — razón: {reason}")

            # Alerta Telegram solo una vez por episodio
            if not is_bot_alert_already_sent(memory, phone_number):
                mark_bot_alert_sent(memory, phone_number)
                alert_msg = (
                    f"*Posible bot detectado*\n"
                    f"Número: {phone_number}\n"
                    f"Razón: {'demasiados mensajes en 2 min' if rate_exceeded else 'mensaje repetido ' + str(REPEAT_DETECTION_COUNT) + ' veces'}\n"
                    f"Último mensaje: {message_text[:200]}"
                )
                telegram.send_message(alert_msg)

            memory.close()
            return  # No procesar con el LLM

        # Si ya no hay actividad de bot, limpiar la marca para futuros episodios
        clear_bot_alert_flag(memory, phone_number)

        # ---------------------------------------------------------------
        # FLUJO NORMAL
        # ---------------------------------------------------------------

        # Si el lead estaba Inactivo y vuelve a escribir, reactivarlo
        lead_pre = memory.get_lead(phone_number)
        if lead_pre:
            if lead_pre.estado == "Inactivo":
                memory.update_lead(phone_number, estado="Pendiente")
            # Limpiar notas de inactividad para que el ciclo se reinicie
            if lead_pre.notas:
                notas_limpias = "|".join(
                    n for n in lead_pre.notas.split("|")
                    if n not in ("inactivity_ping_sent", "inactivity_closed")
                ).strip("|") or None
                if notas_limpias != lead_pre.notas:
                    memory.update_lead(phone_number, notas=notas_limpias)

        # Pre-check: ¿tiene cita y está pidiendo reagendar?
        lead_pre = memory.get_lead(phone_number)
        has_existing_visit = lead_pre and lead_pre.fecha_visita
        wants_reschedule = user_wants_reschedule(message_text)

        # Inyectar señal fuerte si es reagendamiento
        if has_existing_visit and wants_reschedule:
            message_text = (
                f"{message_text}\n\n"
                f"[SISTEMA: El prospecto quiere reagendar. Cita actual: {lead_pre.fecha_visita}. "
                f"Debes usar get_available_days → get_available_times → reschedule_visit. "
                f"NO uses schedule_visit. NO respondas solo con horarios sin llamar reschedule_visit al final.]"
            )

        result = brain.process_message(phone_number, message_text)
        response_text = result.get("response", "")
        actions = result.get("actions", [])
        tool_names = [a.get("tool") for a in actions]

        # Detectar si se agendó o reagendó en este turno
        lead_before_status = result.get("lead_status", {})
        had_existing_visit = bool(lead_before_status.get("fecha_visita"))

        schedule_action = next(
            (a for a in actions if a.get("tool") == "schedule_visit"
             and a.get("input", {}).get("date")),
            None
        )
        reschedule_action = next(
            (a for a in actions if a.get("tool") == "reschedule_visit"
             and a.get("input", {}).get("date")),
            None
        )

        effective_reschedule = reschedule_action or (schedule_action and had_existing_visit)
        effective_schedule = schedule_action and not had_existing_visit
        visit_confirmed = effective_schedule or effective_reschedule

        # Al reagendar: limpiar notas de recordatorio para que se envíen de nuevo
        if effective_reschedule:
            lead_reschedule = memory.get_lead(phone_number)
            if lead_reschedule and lead_reschedule.notas:
                NOTAS_RECORDATORIO = {
                    "reminder_day_before_sent",
                    "reminder_same_day_sent",
                    "owner_alerted_no_confirmation",
                }
                notas_limpias = "|".join(
                    n for n in lead_reschedule.notas.split("|")
                    if n not in NOTAS_RECORDATORIO
                ).strip("|") or None
                if notas_limpias != lead_reschedule.notas:
                    memory.update_lead(phone_number, notas=notas_limpias, confirmo_cita=False)

        # Garantizar alerta Telegram cuando se agenda por primera vez
        if effective_schedule and "send_lead_alert" not in tool_names:
            print("[ERROR] send_lead_alert omitido por LLM — disparando desde main.py")
            lead = memory.get_lead(phone_number)
            if lead:
                lead_dict = {
                    "nombre": lead.nombre,
                    "whatsapp": phone_number,
                    "personas": lead.personas,
                    "ocupacion": lead.ocupacion,
                    "ingresos": lead.ingresos,
                    "mascotas": lead.mascotas,
                    "fecha_visita": str(lead.fecha_visita) if lead.fecha_visita else None,
                }
                sent = telegram.alert_qualified_lead(lead_dict)
                print(f"[ERROR] Alerta Telegram desde main.py: sent={sent}")

        # Garantizar dirección + link Maps al confirmar cita (agenda o reagenda)
        if visit_confirmed and response_text:
            maps_incluido = "maps.app.goo.gl" in response_text or "maps.google.com" in response_text
            if not maps_incluido:
                print("[ERROR] Dirección/Maps no incluida — agregando desde main.py")
                response_text = response_text.rstrip() + "\n\n" + DIRECCION_APARTAMENTO

        # Enviar respuesta al WhatsApp
        if response_text:
            clean_phone = phone_number.lstrip("+")
            whapi.send_text_message(clean_phone, response_text)

        # Guardar respuesta final en historial y Sheets
        if response_text:
            memory.save_conversation(phone_number, "assistant", response_text)
            sheets.append_message(phone_number, "assistant", response_text)

        # Solo verificar rechazo si el lead NO está ya calificado/agendado
        lead = memory.get_lead(phone_number)
        lead_estado = lead.estado if lead else None
        lead_fecha_visita = lead.fecha_visita if lead else None

        if lead_estado not in ("Calificado", "Rechazado", "Cancelado") and not lead_fecha_visita:
            rejection = brain.check_rejection(phone_number)
            if rejection:
                clean_phone = phone_number.lstrip("+")
                whapi.send_text_message(clean_phone, rejection["message"])
                memory.update_lead(phone_number, estado="Rechazado", motivo_rechazo=rejection["reason"])
                rejected_lead = memory.get_lead(phone_number)
                telegram.alert_rejected_lead(
                    {"nombre": rejected_lead.nombre if rejected_lead else "N/A", "whatsapp": phone_number},
                    rejection["reason"]
                )

        memory.close()

    except Exception as e:
        print(f"[ERROR] Processing message from {phone_number}: {e}")
        import traceback
        traceback.print_exc()
        telegram.alert_technical_error(str(e), f"phone={phone_number}")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook/whapi")
async def webhook_whapi(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        messages = data.get("messages", [])
        if not messages:
            return JSONResponse({"received": True})

        for message in messages:
            if message.get("from_me"):
                continue

            phone_number_raw = message.get("chat_id", "").replace("@s.whatsapp.net", "")
            if not phone_number_raw:
                continue
            phone_number = phone_number_raw if phone_number_raw.startswith("+") else f"+{phone_number_raw}"

            if message.get("type") != "text":
                message_id = message.get("id")
                if message_id:
                    mem = Memory()
                    if mem.is_message_processed(message_id):
                        mem.close()
                        continue
                    mem.mark_message_processed(message_id, phone_number)
                    mem.close()

                clean_phone = phone_number.lstrip("+")
                whapi.send_text_message(
                    clean_phone,
                    "Por ahora solo puedo leer mensajes de texto, no puedo procesar audios, imagenes, videos ni stickers. "
                    "Si me escribes con palabras lo que necesitas, con gusto te ayudo.",
                )
                continue

            message_id = message.get("id")
            message_text = message.get("text", {}).get("body", "").strip()

            if not message_text:
                continue

            if message_id:
                mem = Memory()
                already_processed = mem.is_message_processed(message_id)
                if already_processed:
                    print(f"[ANTIBOT] Mensaje duplicado ignorado: {message_id}")
                    mem.close()
                    continue
                mem.mark_message_processed(message_id, phone_number)
                mem.close()

            background_tasks.add_task(process_message_background, phone_number, message_text)

        return JSONResponse({"received": True})

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        print(f"[ERROR] Webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup():
    scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    scheduler.stop()
    brain.close()


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        reload=os.getenv("ENVIRONMENT") == "development",
    )
