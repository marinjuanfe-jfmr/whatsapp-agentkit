import os
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from agent.memory import Memory
from integrations.whapi import WhapiClient
from integrations.telegram import TelegramNotifier


class TaskScheduler:
    """Background task scheduler for reminders and follow-ups"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.whapi = WhapiClient()
        self.telegram = TelegramNotifier()
        self.memory = Memory()

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            # Check for abandoned conversations every hour
            self.scheduler.add_job(
                self.check_abandoned_conversations,
                IntervalTrigger(hours=1),
                id="check_abandoned",
                name="Check abandoned conversations",
            )

            # Send visit reminders daily at 9:00 AM
            self.scheduler.add_job(
                self.send_visit_reminders,
                CronTrigger(hour=9, minute=0),
                id="send_visit_reminders",
                name="Send visit reminders",
            )

            self.scheduler.start()
            print("[SCHEDULER] Started background tasks")

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("[SCHEDULER] Stopped")

    def check_abandoned_conversations(self):
        """Check for leads without response for 6+ hours"""
        try:
            memory = Memory()
            all_leads = memory.get_all_leads(estado="Pendiente")

            for lead in all_leads:
                if not lead.phone_number:
                    continue

                # Get last message timestamp
                conversations = (
                    memory.db.query(__import__("agent.models", fromlist=["Conversation"]).Conversation)
                    .filter_by(phone_number=lead.phone_number)
                    .order_by(__import__("agent.models", fromlist=["Conversation"]).Conversation.timestamp.desc())
                    .first()
                )

                if not conversations:
                    continue

                time_since_last = datetime.utcnow() - conversations.timestamp
                hours_since = time_since_last.total_seconds() / 3600

                # First reminder after 6 hours
                if 6 <= hours_since < 6.5 and lead.notas != "abandoned_first_reminder":
                    self._send_abandonment_reminder_1(lead, memory)

                # Second reminder after 12 hours
                elif hours_since >= 12 and lead.notas != "abandoned_second_reminder":
                    self._send_abandonment_reminder_2(lead, memory)

            memory.close()

        except Exception as e:
            print(f"Error in check_abandoned_conversations: {e}")
            self.telegram.alert_technical_error(str(e), "check_abandoned_conversations")

    def _send_abandonment_reminder_1(self, lead, memory):
        """Send first abandonment reminder"""
        try:
            message = "Hola, queria saber si sigues interesado en el apartamento. Continua cuando quieras, con gusto te atiendo."
            self.whapi.send_text_message(lead.phone_number, message)
            memory.update_lead(lead.phone_number, notas="abandoned_first_reminder")
            print(f"[REMINDER] Sent first abandonment reminder to {lead.phone_number}")
        except Exception as e:
            print(f"Error sending abandonment reminder 1: {e}")

    def _send_abandonment_reminder_2(self, lead, memory):
        """Send second abandonment reminder and close"""
        try:
            message = "Entendido, cerramos la conversacion por ahora. Si en algun momento retomas tu busqueda, con gusto te atendemos. Que te vaya bien."
            self.whapi.send_text_message(lead.phone_number, message)
            memory.update_lead(lead.phone_number, estado="Pendiente", notas="abandoned_closed")
            print(f"[REMINDER] Sent closing message to {lead.phone_number}")
        except Exception as e:
            print(f"Error sending abandonment reminder 2: {e}")

    def send_visit_reminders(self):
        """Send reminders for visits scheduled for tomorrow"""
        try:
            memory = Memory()
            tomorrow = datetime.utcnow().date() + timedelta(days=1)

            # Get all appointments for tomorrow
            from agent.models import Appointment
            appointments = (
                memory.db.query(Appointment)
                .filter(
                    Appointment.fecha_hora >= datetime.combine(tomorrow, __import__("datetime").time.min),
                    Appointment.fecha_hora < datetime.combine(tomorrow, __import__("datetime").time.max),
                    Appointment.estado != "cancelada",
                )
                .all()
            )

            for apt in appointments:
                lead = memory.get_lead_by_id(apt.lead_id)
                if lead:
                    self._send_visit_reminder(lead, apt, memory)

            memory.close()

        except Exception as e:
            print(f"Error in send_visit_reminders: {e}")
            self.telegram.alert_technical_error(str(e), "send_visit_reminders")

    def _send_visit_reminder(self, lead, appointment, memory):
        """Send visit reminder message"""
        try:
            fecha_hora = appointment.fecha_hora
            fecha_str = fecha_hora.strftime("%A, %d de %B")
            hora_str = fecha_hora.strftime("%H:%M")

            message = f"Recordatorio: manana tienes visita al apartamento de Los Robles a las {hora_str}. Confirmas tu asistencia?"
            self.whapi.send_text_message(lead.phone_number, message)
            memory.update_lead(lead.phone_number, notas=f"reminder_sent_{fecha_str}")
            print(f"[REMINDER] Sent visit reminder to {lead.phone_number} for {fecha_str} at {hora_str}")

            # Schedule second reminder in 4 hours if no confirmation
            self.scheduler.add_job(
                self._check_visit_confirmation,
                IntervalTrigger(hours=4),
                args=[lead.phone_number, appointment.id, fecha_str, hora_str],
                id=f"visit_confirmation_{appointment.id}",
                replace_existing=True,
            )

        except Exception as e:
            print(f"Error sending visit reminder: {e}")

    def _check_visit_confirmation(self, phone_number: str, appointment_id: int, fecha_str: str, hora_str: str):
        """Check if visit was confirmed, send second reminder if not"""
        try:
            memory = Memory()
            lead = memory.get_lead(phone_number)

            if not lead or not lead.confirmo_cita:
                message = f"Sigues con planes de visitar el apartamento manana a las {hora_str}? Confirma para mantener tu cupo."
                self.whapi.send_text_message(phone_number, message)
                memory.update_lead(phone_number, notas="second_reminder_sent")
                print(f"[REMINDER] Sent second reminder to {phone_number}")

                # Schedule alert to owner if still no confirmation in 2 more hours
                self.scheduler.add_job(
                    self._alert_owner_no_confirmation,
                    IntervalTrigger(hours=2),
                    args=[phone_number, appointment_id, fecha_str, hora_str],
                    id=f"alert_owner_{appointment_id}",
                    replace_existing=True,
                )

            memory.close()

        except Exception as e:
            print(f"Error checking visit confirmation: {e}")

    def _alert_owner_no_confirmation(self, phone_number: str, appointment_id: int, fecha_str: str, hora_str: str):
        """Alert owner if lead hasn't confirmed visit"""
        try:
            memory = Memory()
            lead = memory.get_lead(phone_number)

            if lead and not lead.confirmo_cita:
                self.telegram.alert_no_confirmation(
                    {
                        "nombre": lead.nombre,
                        "whatsapp": lead.whatsapp,
                    },
                    f"{fecha_str} a las {hora_str}",
                )
                print(f"[ALERT] Notified owner about unconfirmed visit for {phone_number}")

            memory.close()

        except Exception as e:
            print(f"Error alerting owner: {e}")
