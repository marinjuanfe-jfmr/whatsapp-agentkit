import os
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from agent.models import Base, Conversation, Lead, Appointment, ProcessedMessage

_raw_url = os.getenv("DATABASE_URL", "sqlite:///agentkit.db")
DATABASE_URL = _raw_url.replace("sqlite+aiosqlite://", "sqlite://").replace("sqlite://", "sqlite+pysqlite://") if _raw_url.startswith("sqlite") else _raw_url
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get database session"""
    return SessionLocal()


class Memory:
    def __init__(self):
        self.db = get_db()

    def close(self):
        self.db.close()

    def save_conversation(self, phone_number: str, role: str, message: str) -> None:
        """Save message to conversation history"""
        try:
            conv = Conversation(phone_number=phone_number, role=role, message=message)
            self.db.add(conv)
            self.db.commit()
        except Exception:
            self.db.rollback()
            # Reintentar una vez tras rollback (recupera sesión de PendingRollbackError)
            try:
                conv = Conversation(phone_number=phone_number, role=role, message=message)
                self.db.add(conv)
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                print(f"[ERROR] save_conversation reintento fallido: {e}")

    def get_conversation_history(self, phone_number: str, last_n: int = 20) -> List[Dict]:
        """Get last N messages from conversation"""
        conversations = (
            self.db.query(Conversation)
            .filter(Conversation.phone_number == phone_number)
            .order_by(desc(Conversation.timestamp))
            .limit(last_n)
            .all()
        )
        return [
            {
                "role": c.role,
                "content": c.message,
                "timestamp": c.timestamp.isoformat(),
            }
            for c in reversed(conversations)
        ]

    def get_or_create_lead(self, phone_number: str) -> Lead:
        """Get existing lead or create new one"""
        lead = self.db.query(Lead).filter(Lead.phone_number == phone_number).first()
        if not lead:
            lead = Lead(phone_number=phone_number, estado="Pendiente")
            self.db.add(lead)
            self.db.commit()
        return lead

    # Campos que el modelo define como Boolean — el LLM a veces devuelve strings
    _BOOLEAN_FIELDS = {"mascotas", "vehiculos", "acepta_poliza", "interes_compra",
                       "confirmo_cita", "reagendo_cita"}

    @staticmethod
    def _coerce_bool(value) -> bool:
        """Convierte cualquier valor a bool de forma segura."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() not in ("", "no", "false", "0", "none", "null")
        return bool(value)

    def update_lead(self, phone_number: str, **kwargs) -> Lead:
        """Update lead data"""
        # Sanitizar campos booleanos antes de tocar la DB
        for field in self._BOOLEAN_FIELDS:
            if field in kwargs and not isinstance(kwargs[field], bool):
                kwargs[field] = self._coerce_bool(kwargs[field])
        try:
            lead = self.get_or_create_lead(phone_number)
            for key, value in kwargs.items():
                if hasattr(lead, key):
                    setattr(lead, key, value)
            lead.updated_at = datetime.utcnow()
            self.db.commit()
            return lead
        except Exception:
            self.db.rollback()
            try:
                lead = self.get_or_create_lead(phone_number)
                for key, value in kwargs.items():
                    if hasattr(lead, key):
                        setattr(lead, key, value)
                lead.updated_at = datetime.utcnow()
                self.db.commit()
                return lead
            except Exception as e:
                self.db.rollback()
                print(f"[ERROR] update_lead reintento fallido para {phone_number}: {e}")
                return self.get_or_create_lead(phone_number)

    def get_lead(self, phone_number: str) -> Optional[Lead]:
        """Get lead by phone number"""
        return self.db.query(Lead).filter(Lead.phone_number == phone_number).first()

    def get_lead_by_id(self, lead_id: int) -> Optional[Lead]:
        """Get lead by ID"""
        return self.db.query(Lead).filter(Lead.id == lead_id).first()

    def get_lead_status(self, phone_number: str) -> Dict:
        """Get lead status and extracted data"""
        lead = self.get_lead(phone_number)
        if not lead:
            return {"estado": "Nuevo"}
        return {
            "estado": lead.estado,
            "nombre": lead.nombre,
            "personas": lead.personas,
            "ocupacion": lead.ocupacion,
            "ingresos": lead.ingresos,
            "mascotas": lead.mascotas,
            "vehiculos": lead.vehiculos,
            "tipo_vehiculo": lead.tipo_vehiculo,
            "fecha_mudanza": lead.fecha_mudanza,
            "acepta_poliza": lead.acepta_poliza,
            "interes_compra": lead.interes_compra,
            "fecha_visita": lead.fecha_visita,
        }

    def save_appointment(self, phone_number: str, lead_id: int, fecha_hora: datetime, google_event_id: str = None) -> Appointment:
        """Save appointment to database"""
        appointment = Appointment(
            lead_id=lead_id,
            phone_number=phone_number,
            fecha_hora=fecha_hora,
            estado="pendiente",
            google_calendar_event_id=google_event_id,
        )
        self.db.add(appointment)
        self.db.commit()
        return appointment

    def get_appointment(self, lead_id: int) -> Optional[Appointment]:
        """Get appointment by lead ID"""
        return self.db.query(Appointment).filter(Appointment.lead_id == lead_id).first()

    def update_appointment_status(self, appointment_id: int, estado: str) -> Appointment:
        """Update appointment status"""
        appointment = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if appointment:
            appointment.estado = estado
            self.db.commit()
        return appointment

    def get_all_leads(self, estado: Optional[str] = None) -> List[Lead]:
        """Get all leads, optionally filtered by status"""
        query = self.db.query(Lead)
        if estado:
            query = query.filter(Lead.estado == estado)
        return query.all()

    def is_message_processed(self, message_id: str) -> bool:
        """Check if a webhook message_id was already processed (idempotency)"""
        if not message_id:
            return False
        existing = self.db.query(ProcessedMessage).filter(
            ProcessedMessage.message_id == message_id
        ).first()
        return existing is not None

    def mark_message_processed(self, message_id: str, phone_number: str = None) -> None:
        """Mark a webhook message_id as processed (idempotency)"""
        if not message_id:
            return
        try:
            pm = ProcessedMessage(message_id=message_id, phone_number=phone_number)
            self.db.add(pm)
            self.db.commit()
        except Exception:
            self.db.rollback()
