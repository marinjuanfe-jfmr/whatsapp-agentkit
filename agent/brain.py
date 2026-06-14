import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo
import anthropic
from agent.memory import Memory
from agent.validator import QualificationValidator
from agent.tools import AGENT_TOOLS
from integrations.sheets import GoogleSheetsManager

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SYSTEM_PROMPT_FILE = "config/prompts.yaml"

PROPERTY_PHOTOS = [
    {"id": "1pY1pOHaFteRL8VhA9094R_0HPMFgoD-Y", "type": "image"},
    {"id": "159nPojzlEGJ2bpXzH9wwtbQEx1J3G4xE", "type": "image"},
    {"id": "1D0ZW9SmgZrwBJ_5J9cIkXjeGGEQAGYPR", "type": "image"},
    {"id": "1WYr2pKu2DdMD7VFl81PmHdBw6_neJJ5r", "type": "image"},
    {"id": "1bbSjZSjwfZ5xu0W2vUA4wznE-wgG0yyd", "type": "image"},
    {"id": "1MMz9XChJWZqnXhyUh2r0ymbPSG0_7o9j", "type": "image"},
    {"id": "1Y1ba8-Skep8gDzEGIVLrjzfzInv0EH5v", "type": "image"},
    {"id": "19oBjRCEdoK5PkFh2WTjJZvnqTdaKQcXV", "type": "image"},
    {"id": "1wb2eWybNye__gPuwaDIrBM3xLPaxM9fY", "type": "image"},
    {"id": "14546UhU_Gb-G2vFII2J5srgR8mq3mGvS", "type": "image"},
    {"id": "1tswlpgV9QME8jZD7g8hwhBkuz9GhfI8Q", "type": "image"},
    {"id": "1tKN2gsTEllH1hQt74Kr1IyobDLje5_Uv", "type": "image"},
    {"id": "19DBr1Fg8aRTcsIYxcAUIl06GCCa9ve9M", "type": "image"},
    # Video: enviado como link de YouTube (183 MB, no apto para descarga directa)
    # {"id": "15LbNZqIP2jkTI7JGDb6Rzef6hwPkB1xN", "type": "video"},
]


class AgentBrain:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.memory = Memory()
        self.sheets = GoogleSheetsManager()
        self.system_prompt = self._load_system_prompt()
        self.model = "claude-haiku-4-5-20251001"

    def _load_system_prompt(self) -> str:
        try:
            import yaml
            with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                prompt = config.get("system_prompt", "")
                meses = ["enero","febrero","marzo","abril","mayo","junio",
                         "julio","agosto","septiembre","octubre","noviembre","diciembre"]
                dias_semana = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
                now = datetime.now(ZoneInfo("America/Bogota"))
                today = f"{dias_semana[now.weekday()]} {now.day} de {meses[now.month - 1]} de {now.year}, {now.strftime('%H:%M')} (hora Colombia)"
                prompt = f"Fecha y hora actual: {today}\n\n" + prompt
                return prompt
        except Exception as e:
            print(f"Error loading system prompt: {e}")
            return "You are a helpful WhatsApp rental agent."

    def process_message(self, phone_number: str, user_message: str) -> Dict:
        self.memory.save_conversation(phone_number, "user", user_message)
        self.sheets.append_message(phone_number, "user", user_message)

        history = self.memory.get_conversation_history(phone_number, last_n=20)
        lead_status = self.memory.get_lead_status(phone_number)

        messages = [{"role": m["role"], "content": m["content"]} for m in history]

        status_context = f"\n[LEAD STATUS: {json.dumps(lead_status, default=str)}]"
        if lead_status.get("fecha_visita"):
            status_context += f"\n[CITA YA AGENDADA: {lead_status['fecha_visita']} — Si el prospecto quiere cambiarla, usa reschedule_visit. NO uses schedule_visit ni get_available_days/times a menos que el prospecto pida explicitamente reagendar.]"
        if messages:
            messages[-1]["content"] += status_context

        actions_needed = []

        for iteration in range(10):
            print(f"[DEBUG] Tool loop iteration {iteration}, messages={len(messages)}")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=self.system_prompt,
                tools=AGENT_TOOLS,
                messages=messages,
            )

            print(f"[DEBUG] stop_reason={response.stop_reason}, blocks={[b.type for b in response.content]}")

            tool_uses = []
            response_text = ""

            for block in response.content:
                if block.type == "text":
                    response_text = block.text
                elif block.type == "tool_use":
                    tool_uses.append(block)
                    actions_needed.append({
                        "tool": block.name,
                        "input": block.input,
                    })
                    print(f"[DEBUG] Tool called: {block.name} input={json.dumps(block.input, default=str)}")

            if not tool_uses:
                print(f"[DEBUG] No tools called, final response length={len(response_text)}")
                break

            messages.append({"role": "assistant", "content": response.content})

            TOOL_ORDER = ["get_available_days", "get_available_times", "schedule_visit", "reschedule_visit",
                          "update_lead_data", "validate_qualification", "check_calendar_availability",
                          "send_property_photos", "notify_owner", "cancel_visit", "send_lead_alert", "save_to_sheets"]
            tool_uses_sorted = sorted(
                tool_uses,
                key=lambda t: TOOL_ORDER.index(t.name) if t.name in TOOL_ORDER else 99
            )

            tool_results = []
            for tool_use_block in tool_uses_sorted:
                print(f"[DEBUG] Executing tool: {tool_use_block.name}")
                result = self._execute_tool(
                    tool_use_block.name,
                    tool_use_block.input,
                    phone_number,
                )
                print(f"[DEBUG] Tool result: {tool_use_block.name} -> {result}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_block.id,
                    "content": result,
                })

            messages.append({"role": "user", "content": tool_results})

        if not response_text:
            print("[DEBUG] Respuesta vacia tras tool loop, solicitando respuesta explicita")
            try:
                nudge_messages = messages + [{
                    "role": "user",
                    "content": "[SISTEMA: Continua la conversacion ahora. Responde al usuario de forma natural con base en lo que ya sabes, sin llamar mas herramientas.]"
                }]
                follow_up = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=self.system_prompt,
                    messages=nudge_messages,
                )
                for block in follow_up.content:
                    if block.type == "text":
                        response_text = block.text
                        break
                print(f"[DEBUG] Respuesta de fallback length={len(response_text)}")
            except Exception as e:
                print(f"[ERROR] Fallback de respuesta vacia: {e}")

        return {
            "response": response_text,
            "actions": actions_needed,
            "lead_status": lead_status,
        }

    def _execute_tool(self, tool_name: str, tool_input: dict, phone_number: str) -> str:
        from integrations.calendar import CalendarManager
        from integrations.sheets import GoogleSheetsManager
        from integrations.telegram import TelegramNotifier
        from integrations.whapi import WhapiClient

        calendar = CalendarManager()
        sheets = GoogleSheetsManager()
        telegram = TelegramNotifier()
        whapi = WhapiClient()

        try:
            if tool_name == "get_available_days":
                days = calendar.get_available_days()
                return json.dumps({"available_days": days})

            elif tool_name == "get_available_times":
                date_str = tool_input.get("date")
                if date_str:
                    return json.dumps(calendar.get_available_times(date_str))
                return json.dumps({"date": None, "dia_semana": None, "available_times": []})

            elif tool_name == "check_calendar_availability":
                date_str = tool_input.get("date")
                time_str = tool_input.get("time")
                if date_str and time_str:
                    dt = datetime.fromisoformat(f"{date_str}T{time_str}")
                    is_available = calendar.check_availability(dt)
                    return json.dumps({"available": is_available})
                return json.dumps({"available": False})

            elif tool_name == "schedule_visit":
                date_str = tool_input.get("date")
                time_str = tool_input.get("time")
                nombre = tool_input.get("nombre")
                num_personas = tool_input.get("num_personas", 1)
                if date_str and time_str:
                    dt = datetime.fromisoformat(f"{date_str}T{time_str}")

                    # Guardia: si ya hay una cita agendada, redirigir a reschedule_visit
                    existing_lead = self.memory.get_lead(phone_number)
                    if existing_lead and existing_lead.fecha_visita:
                        print(f"[DEBUG] schedule_visit llamado con cita existente — redirigiendo a reschedule_visit")
                        return self._execute_tool("reschedule_visit", tool_input, phone_number)

                    event_id = calendar.create_event(dt, nombre, phone_number, num_personas)
                    lead = self.memory.get_or_create_lead(phone_number)
                    if lead.id:
                        self.memory.save_appointment(phone_number, lead.id, dt, event_id)
                    self.memory.update_lead(phone_number, fecha_visita=dt, reagendo_cita=False)
                    return json.dumps({"event_id": event_id, "scheduled": bool(event_id)})
                return json.dumps({"scheduled": False})

            elif tool_name == "cancel_visit":
                motivo = tool_input.get("motivo", "No especificado")

                # 1. Obtener lead y cita
                lead = self.memory.get_or_create_lead(phone_number)
                old_appointment = self.memory.get_appointment(lead.id) if lead.id else None

                # 2. Eliminar evento de Calendar
                if old_appointment and old_appointment.google_calendar_event_id:
                    calendar.delete_event(old_appointment.google_calendar_event_id)
                    print(f"[DEBUG] Calendar event deleted on cancellation: {old_appointment.google_calendar_event_id}")

                # 3. Actualizar estado del appointment
                if old_appointment:
                    old_appointment.estado = "cancelado"
                    self.memory.db.commit()

                # 4. Actualizar lead
                self.memory.update_lead(phone_number, estado="Cancelado", motivo_rechazo=f"Canceló cita: {motivo}", fecha_visita=None)

                # 5. Actualizar Sheets
                updated_lead = self.memory.get_lead(phone_number)
                if updated_lead:
                    lead_dict = {
                        "nombre": updated_lead.nombre,
                        "whatsapp": phone_number,
                        "personas": updated_lead.personas,
                        "ocupacion": updated_lead.ocupacion,
                        "ingresos": updated_lead.ingresos,
                        "mascotas": updated_lead.mascotas,
                        "vehiculos": updated_lead.vehiculos,
                        "tipo_vehiculo": updated_lead.tipo_vehiculo,
                        "fecha_mudanza": updated_lead.fecha_mudanza,
                        "acepta_poliza": updated_lead.acepta_poliza,
                        "estado": "Cancelado",
                        "motivo_rechazo": f"Canceló cita: {motivo}",
                        "interes_compra": updated_lead.interes_compra,
                        "fecha_visita": "",
                        "confirmo_cita": updated_lead.confirmo_cita,
                        "reagendo_cita": updated_lead.reagendo_cita,
                        "notas": updated_lead.notas,
                    }
                    sheets.append_lead(lead_dict)

                # 6. Alerta Telegram
                lead_dict_telegram = {
                    "nombre": lead.nombre,
                    "whatsapp": phone_number,
                    "fecha_visita": str(old_appointment.fecha_hora) if old_appointment else "N/A",
                }
                telegram.alert_cancelled_visit(lead_dict_telegram, motivo)

                return json.dumps({"cancelled": True})

            elif tool_name == "reschedule_visit":
                date_str = tool_input.get("date")
                time_str = tool_input.get("time")
                nombre = tool_input.get("nombre")
                num_personas = tool_input.get("num_personas", 1)
                if not (date_str and time_str):
                    return json.dumps({"rescheduled": False, "error": "Missing date or time"})

                # 1. Buscar cita anterior y eliminar evento de Calendar
                lead = self.memory.get_or_create_lead(phone_number)
                old_appointment = self.memory.get_appointment(lead.id) if lead.id else None
                if old_appointment and old_appointment.google_calendar_event_id:
                    calendar.delete_event(old_appointment.google_calendar_event_id)
                    print(f"[DEBUG] Old event deleted: {old_appointment.google_calendar_event_id}")

                # 2. Crear nuevo evento en Calendar
                dt = datetime.fromisoformat(f"{date_str}T{time_str}")
                new_event_id = calendar.create_event(dt, nombre, phone_number, num_personas)

                # 3. Actualizar appointment en DB
                if old_appointment:
                    old_appointment.fecha_hora = dt
                    old_appointment.google_calendar_event_id = new_event_id
                    old_appointment.estado = "pendiente"
                    self.memory.db.commit()
                else:
                    if lead.id:
                        self.memory.save_appointment(phone_number, lead.id, dt, new_event_id)

                # 4. Actualizar lead
                self.memory.update_lead(phone_number, fecha_visita=dt, reagendo_cita=True)

                # 5. Actualizar Sheets con nueva fila de reagendamiento
                updated_lead = self.memory.get_lead(phone_number)
                if updated_lead:
                    sheets.append_lead({
                        "nombre": updated_lead.nombre,
                        "whatsapp": phone_number,
                        "personas": updated_lead.personas,
                        "ocupacion": updated_lead.ocupacion,
                        "ingresos": updated_lead.ingresos,
                        "mascotas": updated_lead.mascotas,
                        "vehiculos": updated_lead.vehiculos,
                        "tipo_vehiculo": updated_lead.tipo_vehiculo,
                        "fecha_mudanza": updated_lead.fecha_mudanza,
                        "acepta_poliza": updated_lead.acepta_poliza,
                        "estado": updated_lead.estado,
                        "motivo_rechazo": updated_lead.motivo_rechazo,
                        "interes_compra": updated_lead.interes_compra,
                        "fecha_visita": str(dt),
                        "confirmo_cita": updated_lead.confirmo_cita,
                        "reagendo_cita": True,
                        "notas": updated_lead.notas,
                    })

                # 6. Alerta Telegram de reagendamiento
                lead_dict_telegram = {
                    "nombre": updated_lead.nombre if updated_lead else nombre,
                    "whatsapp": phone_number,
                    "personas": updated_lead.personas if updated_lead else num_personas,
                    "ocupacion": updated_lead.ocupacion if updated_lead else None,
                    "ingresos": updated_lead.ingresos if updated_lead else None,
                    "mascotas": updated_lead.mascotas if updated_lead else None,
                    "fecha_visita": str(dt),
                }
                telegram.alert_custom_message(
                    lead_dict_telegram,
                    f"Reagendamiento de cita: nueva fecha {date_str} a las {time_str}"
                )

                return json.dumps({"rescheduled": True, "new_event_id": new_event_id})

            elif tool_name == "update_lead_data":
                lead_data = {k: v for k, v in tool_input.items() if k != "phone_number" and v is not None}
                if lead_data:
                    self.memory.update_lead(phone_number, **lead_data)
                return json.dumps({"updated": True})

            elif tool_name == "validate_qualification":
                is_qualified = self.is_fully_qualified(phone_number)
                if is_qualified:
                    lead = self.memory.get_lead(phone_number)
                    if lead and lead.estado == "Rechazado":
                        self.memory.update_lead(phone_number, estado="Pendiente", motivo_rechazo=None)
                return json.dumps({"qualified": is_qualified})

            elif tool_name == "send_property_photos":
                clean_phone = phone_number.lstrip("+")
                sent_count = 0
                failed_count = 0
                for item in PROPERTY_PHOTOS:
                    file_id = item["id"]
                    media_type = item["type"]
                    url = f"https://drive.google.com/uc?export=download&id={file_id}"
                    success = whapi.send_media_message(clean_phone, url, media_type)
                    if success:
                        sent_count += 1
                    else:
                        failed_count += 1
                    print(f"[DEBUG] send_property_photos: {media_type} id={file_id} sent={success}")
                return json.dumps({"sent": sent_count, "failed": failed_count})

            elif tool_name == "notify_owner":
                mensaje = tool_input.get("mensaje", "")
                lead = self.memory.get_or_create_lead(phone_number)
                lead_dict = {"nombre": lead.nombre, "whatsapp": phone_number}
                success = telegram.alert_custom_message(lead_dict, mensaje)
                return json.dumps({"sent": success})

            elif tool_name == "send_lead_alert":
                alert_type = tool_input.get("alert_type")
                motivo = tool_input.get("motivo")
                lead = self.memory.get_or_create_lead(phone_number)
                lead_dict = {
                    "nombre": lead.nombre,
                    "whatsapp": phone_number,
                    "personas": lead.personas,
                    "ocupacion": lead.ocupacion,
                    "ingresos": lead.ingresos,
                    "mascotas": lead.mascotas,
                    "fecha_visita": str(lead.fecha_visita) if lead.fecha_visita else None,
                }
                if alert_type == "qualified":
                    success = telegram.alert_qualified_lead(lead_dict)
                elif alert_type == "rejected":
                    success = telegram.alert_rejected_lead(lead_dict, motivo or "")
                elif alert_type == "purchase_interest":
                    success = telegram.alert_purchase_interest(lead_dict)
                elif alert_type == "no_confirmation":
                    success = telegram.alert_no_confirmation(lead_dict, str(lead.fecha_visita))
                else:
                    success = False
                return json.dumps({"sent": success})

            elif tool_name == "save_to_sheets":
                lead = self.memory.get_lead(phone_number)
                if lead:
                    lead_dict = {
                        "nombre": lead.nombre,
                        "whatsapp": phone_number,
                        "personas": lead.personas,
                        "ocupacion": lead.ocupacion,
                        "ingresos": lead.ingresos,
                        "mascotas": lead.mascotas,
                        "vehiculos": lead.vehiculos,
                        "tipo_vehiculo": lead.tipo_vehiculo,
                        "fecha_mudanza": lead.fecha_mudanza,
                        "acepta_poliza": lead.acepta_poliza,
                        "estado": lead.estado,
                        "motivo_rechazo": lead.motivo_rechazo,
                        "interes_compra": lead.interes_compra,
                        "fecha_visita": str(lead.fecha_visita) if lead.fecha_visita else "",
                        "confirmo_cita": lead.confirmo_cita,
                        "reagendo_cita": lead.reagendo_cita,
                        "notas": lead.notas,
                    }
                    success = sheets.append_lead(lead_dict)
                    return json.dumps({"saved": success})
                return json.dumps({"saved": False})

            else:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})

        except Exception as e:
            print(f"[ERROR] Tool execution {tool_name}: {e}")
            import traceback
            traceback.print_exc()
            return json.dumps({"error": str(e)})

    def extract_income(self, text: str) -> Optional[float]:
        text_lower = text.lower()
        import re
        pattern = r"(\d+[.,]?\d*)\s*(millones?|mil|m|k)?"
        matches = re.findall(pattern, text_lower)
        if matches:
            for match in matches:
                number_str = match[0].replace(",", ".")
                unit = match[1] if len(match) > 1 else ""
                try:
                    number = float(number_str)
                    if "millones" in unit or unit == "m":
                        number *= 1000000
                    elif "mil" in unit or unit == "k":
                        number *= 1000
                    return int(number)
                except ValueError:
                    continue
        return None

    def check_rejection(self, phone_number: str) -> Optional[Dict]:
        lead_data = self.memory.get_lead_status(phone_number)
        rejection = QualificationValidator.should_reject_immediately(lead_data)
        if rejection:
            should_reject, reason, message = rejection
            return {"should_reject": True, "reason": reason, "message": message}
        return None

    def is_fully_qualified(self, phone_number: str) -> bool:
        lead_data = self.memory.get_lead_status(phone_number)
        return QualificationValidator.is_fully_qualified(lead_data)

    def close(self):
        self.memory.close()
