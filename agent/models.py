import os
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)  # "user" or "assistant"
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String, nullable=False, unique=True, index=True)
    nombre = Column(String, nullable=True)
    personas = Column(Integer, nullable=True)
    ocupacion = Column(String, nullable=True)
    ingresos = Column(Float, nullable=True)
    mascotas = Column(Boolean, nullable=True)
    vehiculos = Column(Boolean, nullable=True)
    tipo_vehiculo = Column(String, nullable=True)  # carro, moto, ninguno
    fecha_mudanza = Column(String, nullable=True)
    acepta_poliza = Column(Boolean, nullable=True)
    estado = Column(String, default="Pendiente")  # Pendiente, Calificado, Rechazado, Visita agendada
    motivo_rechazo = Column(String, nullable=True)
    interes_compra = Column(Boolean, default=False)
    fecha_visita = Column(DateTime, nullable=True)
    confirmo_cita = Column(Boolean, default=False)
    reagendo_cita = Column(Boolean, default=False)
    notas = Column(Text, nullable=True)
    whatsapp = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    phone_number = Column(String, nullable=False, index=True)
    fecha_hora = Column(DateTime, nullable=False)
    estado = Column(String, default="pendiente")  # pendiente, confirmada, cancelada, realizada
    google_calendar_event_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProcessedMessage(Base):
    __tablename__ = "processed_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String, nullable=False, unique=True, index=True)
    phone_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
