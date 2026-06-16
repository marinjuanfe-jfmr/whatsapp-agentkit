AGENT_TOOLS = [
    {
        "name": "get_available_days",
        "description": "Get the list of upcoming dates that have at least one available visit slot in Google Calendar. Call this FIRST when the prospect wants to schedule a visit, before offering any dates. Returns a list of objects with 'date' (YYYY-MM-DD) and 'dia_semana' (weekday name in Spanish, already computed - use this exact weekday name, do not calculate it yourself).",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_available_times",
        "description": "Get the list of available visit times for a specific date, based on Google Calendar. Call this AFTER the prospect has chosen a date from get_available_days, before offering times. Returns 'date', 'dia_semana' (weekday name in Spanish, already computed) and 'available_times'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format (e.g., 2026-06-13), taken from a 'date' field returned by get_available_days",
                },
            },
            "required": ["date"],
        },
    },
    {
        "name": "check_calendar_availability",
        "description": "Check if a specific date and time slot is available in Google Calendar. Only call when the prospect has chosen a specific date and time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format (e.g., 2026-06-13)",
                },
                "time": {
                    "type": "string",
                    "description": "Time in HH:MM format (e.g., 14:30)",
                },
            },
            "required": ["date", "time"],
        },
    },
    {
        "name": "schedule_visit",
        "description": "Schedule a NEW visit in Google Calendar. Call ONCE after the prospect chooses date and time AND you already know their nombre and num_personas. If you don't have nombre or num_personas yet, ask for them in the same message instead of telling the prospect the visit is confirmed — never say the visit is scheduled/confirmed without calling this tool in the same turn. Do NOT call if [CITA YA AGENDADA] appears in context — use reschedule_visit instead.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Visit date in YYYY-MM-DD format"},
                "time": {"type": "string", "description": "Visit time in HH:MM format"},
                "nombre": {"type": "string", "description": "Lead name"},
                "num_personas": {"type": "integer", "description": "Number of people attending"},
            },
            "required": ["date", "time", "nombre", "num_personas"],
        },
    },
    {
        "name": "cancel_visit",
        "description": "Cancel the existing visit when the prospect explicitly says they will not attend (e.g. found another apartment, changed plans, not interested anymore). Deletes the Calendar event, updates lead status, saves to Sheets, and sends owner alert. Call once when cancellation is clear and definitive.",
        "input_schema": {
            "type": "object",
            "properties": {
                "motivo": {
                    "type": "string",
                    "description": "Reason for cancellation as expressed by the prospect (e.g. 'rentó otro apartamento', 'cambió de planes')",
                },
            },
            "required": ["motivo"],
        },
    },
    {
        "name": "reschedule_visit",
        "description": "Cancel the existing visit and schedule a new one. Use this ONLY when [CITA YA AGENDADA] appears in context and the prospect explicitly asks to change the date or time. This deletes the old Calendar event and creates a new one.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "New visit date in YYYY-MM-DD format"},
                "time": {"type": "string", "description": "New visit time in HH:MM format"},
                "nombre": {"type": "string", "description": "Lead name"},
                "num_personas": {"type": "integer", "description": "Number of people attending"},
            },
            "required": ["date", "time", "nombre", "num_personas"],
        },
    },
    {
        "name": "update_lead_data",
        "description": "Save lead info from the conversation. Call this in the SAME turn the prospect mentions ANY new piece of data, even just one field — do not wait to collect everything first. If several new fields appear in the same message, include all of them in a single call.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre": {"type": "string", "description": "Lead full name"},
                "personas": {"type": "integer", "description": "Number of persons who will live in the apartment"},
                "ocupacion": {"type": "string", "description": "Occupation or income source"},
                "ingresos": {"type": "number", "description": "Monthly income in COP (only if prospect mentioned it voluntarily)"},
                "mascotas": {"type": "boolean", "description": "Has pets (true/false)"},
                "vehiculos": {"type": "boolean", "description": "Has vehicles (true/false)"},
                "tipo_vehiculo": {"type": "string", "description": "Type of vehicle: carro, moto, carro y moto, ninguno"},
                "fecha_mudanza": {"type": "string", "description": "Proposed move date"},
                "acepta_poliza": {"type": "boolean", "description": "Accepts insurance policy requirement (true/false)"},
                "interes_compra": {"type": "boolean", "description": "Prospect expressed interest in buying the apartment (true/false)"},
                "confirmo_cita": {"type": "boolean", "description": "Prospect explicitly confirmed they will attend the scheduled visit (true). Set to true when they respond positively to a visit reminder."},
            },
            "required": [],
        },
    },
    {
        "name": "validate_qualification",
        "description": "Check if the lead meets all criteria. Call only once when you have: nombre, personas, ocupacion, mascotas, vehiculos, fecha_mudanza, acepta_poliza.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "send_property_photos",
        "description": "Send the apartment photos directly to the prospect via WhatsApp. Call this when the prospect asks for photos/pictures/video of the apartment, or confirms they want to see them after your suggestion. After calling this tool, always share the video link in your response: https://youtu.be/DLrNo8uTnr0. Do NOT call more than once per conversation.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "notify_owner",
        "description": "Send a specific, free-text message to the property owner (Juan Felipe) via Telegram, when the prospect asks something specific that you cannot resolve yourself. Use when you tell the prospect 'le aviso al propietario' about something specific.",
        "input_schema": {
            "type": "object",
            "properties": {
                "mensaje": {"type": "string", "description": "The specific message/question to relay to the owner, summarized clearly"},
            },
            "required": ["mensaje"],
        },
    },
    {
        "name": "send_lead_alert",
        "description": "Send Telegram alert to owner. Call once per event: once when qualified+scheduled, once if rejected.",
        "input_schema": {
            "type": "object",
            "properties": {
                "alert_type": {
                    "type": "string",
                    "enum": ["qualified", "rejected", "purchase_interest", "no_confirmation"],
                    "description": "Type of alert",
                },
                "motivo": {"type": "string", "description": "Rejection reason (only for alert_type=rejected)"},
            },
            "required": ["alert_type"],
        },
    },
    {
        "name": "save_to_sheets",
        "description": "Save or update lead data in Google Sheets. Call after scheduling or rescheduling a visit.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]
