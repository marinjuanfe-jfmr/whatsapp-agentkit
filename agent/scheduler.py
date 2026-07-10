import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from agent.memory import Memory
from agent.models import Conversation, Lead
from integrations.whapi import WhapiClient
from integrations.telegram import TelegramNotifier

BOGOTA_TZ = ZoneInfo("America/Bogota")

# Minutos de inactividad para cada acción
INACTIVITY_PING_MINUTES = 10
INACTIVITY_CLOSE_MINUTES = 20

# Estados que no deben recibir pings de inactividad
ESTADOS_EXCLUIDOS_INACTIVIDAD = {"Rechazado", "Cancelado", "Inactivo"}

# Nota interna que marca que ya se envió el ping de inactividad
NOTA_PING = "inactivity_ping_sent"
NOTA_CIERRE = "inactivity_closed"

# Notas para recordatorios de visita
NOTA_RECORDATORIO_DIA_ANTERIOR = "reminder_day_before_sent"
NOTA_RECORDATORIO_MISMO_DIA = "reminder_same_day_sent"
NOTA_ALERTA_SIN_CONFIRMACION = "owner_alerted_no_confirmation"


def _now_bogota() -> datetime:
    return datetime.now(tz=BOGOTA_TZ)


def _last_user_message_time(memory: Memory, phone_number: str):
    """Devuelve el timestamp (naive UTC) del último mensaje del usuario, o None."""
    conv = (
        memory.db.query(Conversation)
        .filter(
            Conversation.phone_number == phone_number,
            Conversation.role == "user",
        )
        .order_by(Conversation.timestamp.desc())
        .first()
    )
    return conv.timestamp if conv else None


def _minutes_since(ts_utc) -> float:
    """Minutos transcurridos desde un timestamp UTC naive."""
    if isinstance(ts_utc, str):
        ts_utc = datetime.fromisoformat(ts_utc)
    now_utc = datetime.utcnow()
    return (now_utc - ts_utc).total_seconds() / 60


def _parse_fecha_visita(fv) -> datetime:
    """Convierte fecha_visita a datetime con timezone Bogotá, sea datetime o string."""
    if isinstance(fv, str):
        fv = datetime.fromisoformat(fv)
    return datetime(fv.year, fv.month, fv.day, fv.hour, fv.minute, tzinfo=BOGOTA_TZ)


def _has_nota(lead: Lead, nota: str) -> bool:
    return lead.notas and nota in lead.notas


def _add_nota(memory: Memory, phone: str, nota: str):
    """Agrega una nota al campo notas del lead sin pisar las existentes."""
    lead = memory.get_lead(phone)
    existing = lead.notas or ""
    if nota not in existing:
        new_notas = (existing + "|" + nota).strip("|")
        memory.update_lead(phone, notas=new_notas)


class TaskScheduler:
    """Background task scheduler para inactividad y recordatorios de visita."""

    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=str(BOGOTA_TZ))
        self.whapi = WhapiClient()
        self.telegram = TelegramNotifier()

    def start(self):
        if not self.scheduler.running:

            # Inactividad: revisar cada 5 minutos, empezando de inmediato
            self.scheduler.add_job(
                self.check_inactivity,
                IntervalTrigger(minutes=5, start_date=datetime.now(tz=BOGOTA_TZ)),
                id="check_inactivity",
                name="Detectar conversaciones inactivas",
            )

            # DESACTIVADOS (9 jul 2026) — el apartamento ya fue arrendado y Juan
            # cancelará manualmente las visitas programadas, así que Robin no debe
            # escribir a nadie a confirmar/recordar citas. Para reactivar, descomentar
            # estos tres add_job.
            #
            # # Recordatorio día anterior: cron 18:00 Bogotá
            # self.scheduler.add_job(
            #     self.send_reminder_day_before,
            #     CronTrigger(hour=18, minute=0, timezone=str(BOGOTA_TZ)),
            #     id="reminder_day_before",
            #     name="Recordatorio visita día anterior",
            # )
            #
            # # Recordatorio mismo día: revisar cada 30 minutos, empezando de inmediato
            # self.scheduler.add_job(
            #     self.send_reminder_same_day,
            #     IntervalTrigger(minutes=30, start_date=datetime.now(tz=BOGOTA_TZ)),
            #     id="reminder_same_day",
            #     name="Recordatorio visita mismo día (2h antes)",
            # )
            #
            # # Alerta sin confirmación: revisar cada 30 minutos
            # self.scheduler.add_job(
            #     self.alert_no_confirmation,
            #     IntervalTrigger(minutes=30, start_date=datetime.now(tz=BOGOTA_TZ)),
            #     id="alert_no_confirmation",
            #     name="Alerta dueño por visita sin confirmar",
            # )

            self.scheduler.start()
            print("[SCHEDULER] Iniciado — jobs registrados: check_inactivity (5min). Recordatorios de visita DESACTIVADOS (apartamento ya arrendado).")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("[SCHEDULER] Detenido")

    # ─────────────────────────────────────────────
    # INACTIVIDAD
    # ─────────────────────────────────────────────

    def check_inactivity(self):
        """Revisa leads con conversación activa que no han respondido."""
        try:
            memory = Memory()
            leads = memory.get_all_leads()
            print(f"[SCHEDULER] check_inactivity corriendo — {len(leads)} leads en DB")

            for lead in leads:
                phone = lead.phone_number
                estado = lead.estado or "Pendiente"

                # No molestar a rechazados, cancelados ni ya cerrados por inactividad
                if estado in ESTADOS_EXCLUIDOS_INACTIVIDAD:
                    continue

                # Si ya tiene una visita agendada, el seguimiento natural son los
                # recordatorios (día anterior / mismo día), no el ping de "¿sigues ahí?".
                # Mandarle eso después de que ya quedó la cita lista (ej. justo después
                # de un simple "gracias") se ve robótico y fuera de lugar.
                if lead.fecha_visita:
                    continue

                # Tampoco si ya se envió el cierre
                if _has_nota(lead, NOTA_CIERRE):
                    continue

                last_ts = _last_user_message_time(memory, phone)
                if not last_ts:
                    continue

                minutes_ago = _minutes_since(last_ts)

                # Ping de "¿sigues ahí?" a los 10 minutos
                if (
                    minutes_ago >= INACTIVITY_PING_MINUTES
                    and not _has_nota(lead, NOTA_PING)
                ):
                    self._send_inactivity_ping(memory, phone)

                # Mensaje de cierre a los 20 minutos
                elif (
                    minutes_ago >= INACTIVITY_CLOSE_MINUTES
                    and _has_nota(lead, NOTA_PING)
                    and not _has_nota(lead, NOTA_CIERRE)
                ):
                    self._send_inactivity_close(memory, phone)

            memory.close()

        except Exception as e:
            print(f"[ERROR] check_inactivity: {e}")
            try:
                self.telegram.alert_technical_error(str(e), "check_inactivity")
            except Exception:
                pass

    def _send_inactivity_ping(self, memory: Memory, phone: str):
        try:
            msg = (
                "¿Sigues ahí? Si tienes alguna duda sobre el apartamento, "
                "con gusto te ayudo."
            )
            clean = phone.lstrip("+")
            self.whapi.send_text_message(clean, msg)
            _add_nota(memory, phone, NOTA_PING)
            print(f"[SCHEDULER] Ping de inactividad enviado a {phone}")
        except Exception as e:
            print(f"[ERROR] _send_inactivity_ping {phone}: {e}")

    def _send_inactivity_close(self, memory: Memory, phone: str):
        try:
            msg = (
                "Voy a cerrar la conversación por ahora. "
                "Si en algún momento quieres retomar o tienes alguna duda, "
                "no dudes en escribirnos de nuevo. ¡Que te vaya bien!"
            )
            clean = phone.lstrip("+")
            self.whapi.send_text_message(clean, msg)
            _add_nota(memory, phone, NOTA_CIERRE)
            memory.update_lead(phone, estado="Inactivo")
            print(f"[SCHEDULER] Conversación cerrada por inactividad: {phone}")
        except Exception as e:
            print(f"[ERROR] _send_inactivity_close {phone}: {e}")

    # ─────────────────────────────────────────────
    # RECORDATORIO DÍA ANTERIOR (cron 18:00)
    # ─────────────────────────────────────────────

    def send_reminder_day_before(self):
        """Manda recordatorio a leads con visita mañana que no han confirmado."""
        try:
            memory = Memory()
            now = _now_bogota()
            tomorrow = (now + timedelta(days=1)).date()

            leads = memory.get_all_leads()
            for lead in leads:
                if not lead.fecha_visita:
                    continue
                if lead.estado == "Cancelado":
                    continue
                if lead.confirmo_cita:
                    continue
                if _has_nota(lead, NOTA_RECORDATORIO_DIA_ANTERIOR):
                    continue

                # fecha_visita puede llegar como str o datetime desde SQLite
                fv_bogota = _parse_fecha_visita(lead.fecha_visita)
                if fv_bogota.date() != tomorrow:
                    continue

                hora_str = fv_bogota.strftime("%I:%M %p").lstrip("0")
                nombre = lead.nombre or "hola"

                msg = (
                    f"Hola{' ' + nombre if lead.nombre else ''}, te escribo para recordarte "
                    f"que mañana tienes visita al apartamento a las *{hora_str}*. "
                    f"¿Confirmas que vas a poder asistir?"
                )
                clean = lead.phone_number.lstrip("+")
                self.whapi.send_text_message(clean, msg)
                _add_nota(memory, lead.phone_number, NOTA_RECORDATORIO_DIA_ANTERIOR)
                print(f"[SCHEDULER] Recordatorio día anterior enviado a {lead.phone_number}")

            memory.close()

        except Exception as e:
            print(f"[ERROR] send_reminder_day_before: {e}")
            try:
                self.telegram.alert_technical_error(str(e), "send_reminder_day_before")
            except Exception:
                pass

    # ─────────────────────────────────────────────
    # RECORDATORIO MISMO DÍA (2 horas antes)
    # ─────────────────────────────────────────────

    def send_reminder_same_day(self):
        """Manda recordatorio si la visita es hoy y faltan ~2 horas."""
        try:
            memory = Memory()
            now = _now_bogota()

            leads = memory.get_all_leads()
            for lead in leads:
                if not lead.fecha_visita:
                    continue
                if lead.estado == "Cancelado":
                    continue
                if lead.confirmo_cita:
                    continue
                if _has_nota(lead, NOTA_RECORDATORIO_MISMO_DIA):
                    continue

                fv_bogota = _parse_fecha_visita(lead.fecha_visita)
                if fv_bogota.date() != now.date():
                    continue

                minutes_until = (fv_bogota - now).total_seconds() / 60

                # Ventana: entre 90 y 150 minutos antes (centrado en 2h,
                # tolerancia ±30 min por la frecuencia del cron de 30 min)
                if not (90 <= minutes_until <= 150):
                    continue

                hora_str = fv_bogota.strftime("%I:%M %p").lstrip("0")
                nombre = lead.nombre or ""

                msg = (
                    f"Hola{' ' + nombre if nombre else ''}, tu visita al apartamento "
                    f"es hoy a las *{hora_str}*. ¿Vas a poder asistir?"
                )
                clean = lead.phone_number.lstrip("+")
                self.whapi.send_text_message(clean, msg)
                _add_nota(memory, lead.phone_number, NOTA_RECORDATORIO_MISMO_DIA)
                print(f"[SCHEDULER] Recordatorio mismo día enviado a {lead.phone_number}")

            memory.close()

        except Exception as e:
            print(f"[ERROR] send_reminder_same_day: {e}")
            try:
                self.telegram.alert_technical_error(str(e), "send_reminder_same_day")
            except Exception:
                pass

    # ─────────────────────────────────────────────
    # ALERTA AL DUEÑO POR FALTA DE CONFIRMACIÓN
    # ─────────────────────────────────────────────

    def alert_no_confirmation(self):
        """
        Si pasaron 3h desde el recordatorio y el lead no confirmó ni canceló,
        avisa a Juan por Telegram.
        """
        try:
            memory = Memory()
            now = _now_bogota()

            leads = memory.get_all_leads()
            for lead in leads:
                if not lead.fecha_visita:
                    continue
                if lead.confirmo_cita:
                    continue
                if lead.estado == "Cancelado":
                    continue
                if _has_nota(lead, NOTA_ALERTA_SIN_CONFIRMACION):
                    continue

                # Solo si se envió algún recordatorio
                sent_reminder = (
                    _has_nota(lead, NOTA_RECORDATORIO_DIA_ANTERIOR)
                    or _has_nota(lead, NOTA_RECORDATORIO_MISMO_DIA)
                )
                if not sent_reminder:
                    continue

                # Verificar que ya pasaron 3h desde el último mensaje del lead
                last_ts = _last_user_message_time(memory, lead.phone_number)
                if last_ts and _minutes_since(last_ts) < 180:
                    continue

                fv_bogota = _parse_fecha_visita(lead.fecha_visita)
                hora_str = fv_bogota.strftime("%d/%m %I:%M %p")

                self.telegram.alert_no_confirmation(
                    {
                        "nombre": lead.nombre or "Sin nombre",
                        "whatsapp": lead.phone_number,
                    },
                    hora_str,
                )
                _add_nota(memory, lead.phone_number, NOTA_ALERTA_SIN_CONFIRMACION)
                print(f"[SCHEDULER] Alerta sin confirmación enviada para {lead.phone_number}")

            memory.close()

        except Exception as e:
            print(f"[ERROR] alert_no_confirmation: {e}")
            try:
                self.telegram.alert_technical_error(str(e), "alert_no_confirmation")
            except Exception:
                pass
