"""Test complete lead qualification flow"""
import pytest
from datetime import datetime, timedelta
from agent.memory import Memory
from agent.validator import QualificationValidator
from agent.brain import AgentBrain


def test_lead_creation_and_update(memory, sample_lead_data):
    """Test creating and updating a lead"""
    phone = sample_lead_data["phone_number"]

    # Create lead
    lead = memory.get_or_create_lead(phone)
    assert lead is not None
    assert lead.phone_number == phone
    assert lead.estado == "Pendiente"

    # Update lead
    updated_lead = memory.update_lead(phone, **sample_lead_data)
    assert updated_lead.nombre == sample_lead_data["nombre"]
    assert updated_lead.ingresos == sample_lead_data["ingresos"]
    assert updated_lead.estado == "Calificado"


def test_conversation_history(memory):
    """Test saving and retrieving conversation history"""
    phone = "+573001234567"

    # Save messages
    memory.save_conversation(phone, "user", "Hola, me interesa el apartamento")
    memory.save_conversation(phone, "assistant", "¡Hola! Me da gusto tu interés.")
    memory.save_conversation(phone, "user", "¿Cuál es el precio?")
    memory.save_conversation(phone, "assistant", "$1.800.000 mensuales")

    # Retrieve history
    history = memory.get_conversation_history(phone)
    assert len(history) == 4
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"


def test_appointment_creation(memory, sample_lead_data):
    """Test creating an appointment"""
    phone = sample_lead_data["phone_number"]

    # Create lead first
    lead = memory.get_or_create_lead(phone)
    memory.update_lead(phone, **sample_lead_data)

    # Create appointment
    visit_time = datetime.utcnow() + timedelta(days=1)
    appointment = memory.save_appointment(phone, lead.id, visit_time, "google_event_123")

    assert appointment is not None
    assert appointment.lead_id == lead.id
    assert appointment.estado == "pendiente"
    assert appointment.google_calendar_event_id == "google_event_123"


def test_get_lead_status(memory, sample_lead_data):
    """Test retrieving lead status"""
    phone = sample_lead_data["phone_number"]

    # Create and update lead
    memory.get_or_create_lead(phone)
    memory.update_lead(phone, **sample_lead_data)

    # Get status
    status = memory.get_lead_status(phone)
    assert status["estado"] == "Calificado"
    assert status["nombre"] == sample_lead_data["nombre"]
    assert status["personas"] == 2
    assert status["ingresos"] == 5000000


def test_fully_qualified_lead(memory, sample_lead_data):
    """Test checking if lead is fully qualified"""
    phone = sample_lead_data["phone_number"]

    # Update lead with all required data
    memory.get_or_create_lead(phone)
    memory.update_lead(phone, **sample_lead_data)

    # Check qualification
    status = memory.get_lead_status(phone)
    is_qualified = QualificationValidator.is_fully_qualified(status)
    assert is_qualified is True


def test_incomplete_lead(memory):
    """Test lead that's not fully qualified yet"""
    phone = "+573001234567"

    # Create lead with minimal data
    lead = memory.get_or_create_lead(phone)
    memory.update_lead(phone, nombre="Juan", personas=2)

    # Check qualification
    status = memory.get_lead_status(phone)
    is_qualified = QualificationValidator.is_fully_qualified(status)
    assert is_qualified is False
