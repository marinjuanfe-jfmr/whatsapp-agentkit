from typing import Dict, Optional, Tuple


class QualificationValidator:
    """Validates leads against qualification criteria"""

    MIN_INCOME = 3600000  # COP
    MAX_PERSONS = 4
    REQUIRES_INSURANCE = True

    @staticmethod
    def validate_ingresos(ingresos: Optional[float]) -> Tuple[bool, str]:
        if ingresos is None:
            return True, "income_not_declared"  # Póliza validates it
        try:
            ingresos = float(ingresos)
        except (ValueError, TypeError):
            return True, "income_not_parseable"
        if ingresos < QualificationValidator.MIN_INCOME:
            return False, "income_insufficient"
        return True, "income_valid"

    @staticmethod
    def validate_poliza(acepta_poliza: Optional[bool]) -> Tuple[bool, str]:
        if acepta_poliza is None:
            return False, "poliza_not_asked"
        if not acepta_poliza:
            return False, "poliza_rejected"
        return True, "poliza_accepted"

    @staticmethod
    def validate_personas(personas: Optional[int]) -> Tuple[bool, str]:
        if personas is None:
            return False, "personas_missing"
        try:
            personas = int(personas)
        except (ValueError, TypeError):
            return False, "personas_missing"
        if personas > QualificationValidator.MAX_PERSONS:
            return False, "personas_too_many"
        return True, "personas_valid"

    @staticmethod
    def validate_inmobiliaria(ocupacion: Optional[str]) -> Tuple[bool, str]:
        if ocupacion is None:
            return True, "ocupacion_missing"

        inmobiliaria_keywords = [
            "inmobiliaria", "broker",
            "corredor", "realtor", "intermediario",
        ]
        # Frases que indican que busca para sí mismo — no rechazar
        uso_propio_keywords = [
            "para sí mismo", "para mi", "para mí", "para vivir",
            "busca para sí", "personal", "propio uso"
        ]
        ocupacion_lower = ocupacion.lower()

        # Si hay indicación de uso propio, no rechazar aunque sea agente
        for keyword in uso_propio_keywords:
            if keyword in ocupacion_lower:
                return True, "uso_propio"

        for keyword in inmobiliaria_keywords:
            if keyword in ocupacion_lower:
                return False, "is_real_estate_agent"

        # "agente" solo rechaza si no hay contexto de uso propio
        if "agente" in ocupacion_lower and "agente de" not in ocupacion_lower:
            return False, "is_real_estate_agent"

        return True, "not_agent"

    @staticmethod
    def should_reject_immediately(lead_data: Dict) -> Optional[Tuple[bool, str, str]]:
        ocupacion = lead_data.get("ocupacion")
        is_valid, reason = QualificationValidator.validate_inmobiliaria(ocupacion)
        if not is_valid:
            msg = "Gracias por contactarnos. Por decision de los propietarios, el apartamento se arrienda directamente sin intermediarios. Exitos!"
            return True, "inmobiliaria", msg

        ingresos = lead_data.get("ingresos")
        if ingresos is not None:
            is_valid, reason = QualificationValidator.validate_ingresos(ingresos)
            if not is_valid:
                msg = "Gracias por tu interes en el apartamento. Por politica de los propietarios, se requiere un ingreso minimo de $3.600.000 para aplicar. Si en el futuro cambian tus circunstancias, con gusto te atendemos. Mucho exito!"
                return True, "ingresos_insuficientes", msg

        acepta_poliza = lead_data.get("acepta_poliza")
        if acepta_poliza is not None:
            is_valid, reason = QualificationValidator.validate_poliza(acepta_poliza)
            if not is_valid:
                msg = "Gracias por comunicarte. La poliza de arrendamiento es un requisito obligatorio que no es negociable. Si en algun momento cambias de opinion, aqui estaremos. Que te vaya bien!"
                return True, "poliza_rechazada", msg

        personas = lead_data.get("personas")
        if personas is not None:
            is_valid, reason = QualificationValidator.validate_personas(personas)
            if not is_valid:
                msg = "Gracias por tu interes. Lamentablemente el apartamento no se ajusta a lo que necesitas en este momento. Mucho exito en tu busqueda!"
                return True, "demasiadas_personas", msg

        return None

    @staticmethod
    def is_fully_qualified(lead_data: Dict) -> bool:
        """
        Check if lead has answered all required questions and qualifies.
        Ingresos is NOT required — the poliza validates it.
        """
        required_fields = [
            "personas",
            "ocupacion",
            "mascotas",
            "fecha_mudanza",
            "acepta_poliza",
            "tipo_vehiculo",
        ]

        for field in required_fields:
            if lead_data.get(field) is None:
                return False

        # Validate criteria
        is_valid, _ = QualificationValidator.validate_personas(lead_data.get("personas"))
        if not is_valid:
            return False

        is_valid, _ = QualificationValidator.validate_poliza(lead_data.get("acepta_poliza"))
        if not is_valid:
            return False

        is_valid, _ = QualificationValidator.validate_inmobiliaria(lead_data.get("ocupacion"))
        if not is_valid:
            return False

        # Only validate ingresos if declared
        ingresos = lead_data.get("ingresos")
        if ingresos is not None:
            is_valid, _ = QualificationValidator.validate_ingresos(ingresos)
            if not is_valid:
                return False

        return True
