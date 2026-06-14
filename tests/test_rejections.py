"""Test rejection scenarios"""
import pytest
from agent.validator import QualificationValidator


def test_reject_low_income():
    """Test rejection for insufficient income"""
    lead_data = {
        "ocupacion": "Vendedor",
        "ingresos": 2000000,  # Below 3.6M
    }

    rejection = QualificationValidator.should_reject_immediately(lead_data)
    assert rejection is not None
    assert rejection[1] == "ingresos_insuficientes"


def test_reject_real_estate_agent():
    """Test rejection for real estate agent"""
    lead_data = {
        "ocupacion": "Agente Inmobiliario",
        "ingresos": 5000000,
    }

    rejection = QualificationValidator.should_reject_immediately(lead_data)
    assert rejection is not None
    assert rejection[1] == "inmobiliaria"


def test_reject_no_insurance():
    """Test rejection for not accepting insurance"""
    lead_data = {
        "ocupacion": "Ingeniero",
        "ingresos": 5000000,
        "acepta_poliza": False,
    }

    rejection = QualificationValidator.should_reject_immediately(lead_data)
    assert rejection is not None
    assert rejection[1] == "poliza_rechazada"


def test_reject_too_many_persons():
    """Test rejection for too many persons"""
    lead_data = {
        "ocupacion": "Profesor",
        "ingresos": 5000000,
        "acepta_poliza": True,
        "personas": 6,  # More than max 4
    }

    rejection = QualificationValidator.should_reject_immediately(lead_data)
    assert rejection is not None
    assert rejection[1] == "demasiadas_personas"


def test_accept_valid_lead():
    """Test that valid lead is not rejected"""
    lead_data = {
        "ocupacion": "Ingeniero",
        "ingresos": 5000000,
        "acepta_poliza": True,
        "personas": 2,
    }

    rejection = QualificationValidator.should_reject_immediately(lead_data)
    assert rejection is None


def test_accept_minimum_income():
    """Test acceptance at minimum income threshold"""
    lead_data = {
        "ocupacion": "Empleado",
        "ingresos": 3600000,  # Exactly minimum
        "acepta_poliza": True,
        "personas": 1,
    }

    rejection = QualificationValidator.should_reject_immediately(lead_data)
    assert rejection is None


def test_accept_various_occupations():
    """Test acceptance of various occupations"""
    occupations = [
        "Ingeniero de Sistemas",
        "Profesor Universitario",
        "Contador",
        "Abogado",
        "Empresario",
    ]

    for occ in occupations:
        lead_data = {
            "ocupacion": occ,
            "ingresos": 5000000,
            "acepta_poliza": True,
            "personas": 2,
        }
        rejection = QualificationValidator.should_reject_immediately(lead_data)
        assert rejection is None, f"Should not reject: {occ}"


def test_reject_various_real_estate_keywords():
    """Test rejection with various real estate keywords"""
    keywords = ["inmobiliaria", "agente", "broker", "corredor", "realtor", "intermediario"]

    for keyword in keywords:
        lead_data = {"ocupacion": keyword.capitalize()}
        rejection = QualificationValidator.should_reject_immediately(lead_data)
        assert rejection is not None, f"Should reject: {keyword}"
        assert rejection[1] == "inmobiliaria"
