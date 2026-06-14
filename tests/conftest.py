import pytest
import os
from datetime import datetime
from agent.memory import Memory, init_db, SessionLocal
from agent.models import Base

# Use test database
os.environ["DATABASE_URL"] = "sqlite:///:memory:"


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Setup test database for all tests"""
    init_db()
    yield
    # Cleanup happens automatically with in-memory DB


@pytest.fixture
def memory():
    """Provide fresh memory (DB session) for each test"""
    mem = Memory()
    yield mem
    mem.close()


@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing"""
    return {
        "phone_number": "+573001234567",
        "nombre": "Juan Pérez",
        "whatsapp": "+573001234567",
        "personas": 2,
        "ocupacion": "Ingeniero de Sistemas",
        "ingresos": 5000000,
        "mascotas": False,
        "vehiculos": True,
        "tipo_vehiculo": "carro",
        "fecha_mudanza": "2024-04-01",
        "acepta_poliza": True,
        "estado": "Calificado",
    }


@pytest.fixture
def rejected_lead_data():
    """Sample rejected lead data"""
    return {
        "phone_number": "+573001234568",
        "nombre": "Carlos López",
        "whatsapp": "+573001234568",
        "personas": 2,
        "ocupacion": "Agente Inmobiliario",
        "ingresos": 5000000,
        "mascotas": False,
        "estado": "Rechazado",
        "motivo_rechazo": "is_real_estate_agent",
    }
