"""
Simulador MEJORADO — Agente inteligente que NO repite preguntas
Procesa respuestas naturales y solo pregunta lo que falta
"""
import os
import sys
import re
from datetime import datetime
from agent.memory import Memory, init_db
from agent.validator import QualificationValidator

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class IntelligentMockAgent:
    """Smart agent that processes natural language without repeating questions"""

    def __init__(self):
        self.required_fields = ["nombre", "personas", "ocupacion", "ingresos", "mascotas", "tipo_vehiculo", "fecha_mudanza", "acepta_poliza"]

    def get_missing_fields(self, extracted_data: dict) -> list:
        """Get list of fields that still need to be filled"""
        missing = []
        for field in self.required_fields:
            value = extracted_data.get(field)
            if value is None or (isinstance(value, str) and value == ""):
                missing.append(field)
        return missing

    def get_next_question(self, missing_fields: list) -> str:
        """Generate next question based on missing fields"""
        if not missing_fields:
            return None

        next_field = missing_fields[0]
        questions = {
            "nombre": "Como te llamas o cual es tu nombre?",
            "personas": "Para cuantas personas seria el apartamento?",
            "ocupacion": "Cual es tu ocupacion o fuente de ingreso?",
            "ingresos": "Aproximadamente cuales son tus ingresos mensuales?",
            "mascotas": "Tienen mascotas?",
            "tipo_vehiculo": "Tienen vehiculo? (carro, moto o ninguno)",
            "fecha_mudanza": "Cuando necesitarian mudarse?",
            "acepta_poliza": "Estan de acuerdo con que la poliza de arrendamiento sea el unico requisito?",
        }
        return questions.get(next_field, "Cual es tu siguiente duda?")

    def check_qualification(self, extracted_data: dict) -> dict:
        """Check if lead qualifies or should be rejected"""
        ingresos = extracted_data.get("ingresos")
        if ingresos and ingresos < 3600000:
            return {
                "qualified": False,
                "reason": "ingresos_insuficientes",
                "message": "Gracias por tu interes. Se requiere ingreso minimo de $3.600.000. Si cambian tus circunstancias, te atendemos. Mucho exito!"
            }

        acepta_poliza = extracted_data.get("acepta_poliza")
        if acepta_poliza is False:
            return {
                "qualified": False,
                "reason": "poliza_rechazada",
                "message": "Gracias. La poliza es requisito obligatorio. Si cambias de opinion, aqui estaremos. Que te vaya bien!"
            }

        personas = extracted_data.get("personas")
        if personas and personas > 4:
            return {
                "qualified": False,
                "reason": "demasiadas_personas",
                "message": "Gracias por tu interes. El apartamento no se ajusta a eso. Mucho exito en tu busqueda!"
            }

        ocupacion = extracted_data.get("ocupacion")
        if ocupacion:
            if any(x in ocupacion.lower() for x in ["inmobiliaria", "agente", "broker", "corredor"]):
                return {
                    "qualified": False,
                    "reason": "inmobiliaria",
                    "message": "Gracias. Los propietarios arriendan directamente sin intermediarios. Exitos!"
                }

        # Check if fully qualified
        if all([
            extracted_data.get("nombre"),
            extracted_data.get("personas"),
            extracted_data.get("ocupacion"),
            extracted_data.get("ingresos"),
            extracted_data.get("mascotas") is not None,
            extracted_data.get("fecha_mudanza"),
            extracted_data.get("acepta_poliza") is not None,
            extracted_data.get("tipo_vehiculo"),
        ]):
            if ingresos >= 3600000 and acepta_poliza:
                return {
                    "qualified": True,
                    "message": "[QUALIFIED] Excelente! Calificaste perfectamente.\n\nAntes de agendar, te envio fotos y video del apartamento.\n\n[Fotos y video del apartamento serian enviados aqui]\n\nA que dia y hora te quedaria bien para visitarlo?"
                }

        return {"qualified": None}

    def get_response(self, user_input: str, extracted_data: dict) -> str:
        """Generate intelligent response without repeating questions"""
        user_lower = user_input.lower()

        # Check for immediate qualifications/rejections
        qualification = self.check_qualification(extracted_data)
        if qualification.get("qualified") is False:
            return qualification["message"]

        if qualification.get("qualified") is True:
            return qualification["message"]

        # Get missing fields
        missing = self.get_missing_fields(extracted_data)

        if not missing:
            final_check = self.check_qualification(extracted_data)
            if final_check.get("message"):
                return final_check["message"]
            return "Perfecto! Tienes todos los datos. Cuando quieres agendar tu visita?"

        # Generate next question based on what's missing
        next_q = self.get_next_question(missing)
        return next_q if next_q else "Que mas te gustaria saber del apartamento?"


class ImprovedSimulator:
    """Improved chat simulator with intelligent agent"""

    def __init__(self):
        init_db()
        self.memory = Memory()
        self.phone = "+573001234567"
        self.agent = IntelligentMockAgent()
        self.extracted_data = {}

    def extract_from_input(self, user_input: str) -> dict:
        """Improved extraction with better pattern matching"""
        user_lower = user_input.lower()
        extraction = {}

        # Extract nombre
        if "me llamo" in user_lower or "nombre" in user_lower:
            words = user_input.split()
            for i, word in enumerate(words):
                if word.lower() in ["llamo", "es"]:
                    if i + 1 < len(words):
                        name_parts = [words[i+1]]
                        if i + 2 < len(words) and words[i+2][0].isupper():
                            name_parts.append(words[i+2].rstrip(","))
                        extraction["nombre"] = " ".join(name_parts)
                    break

        # Extract personas
        persona_match = re.search(r'(\d+)\s*persona', user_lower)
        if persona_match:
            extraction["personas"] = int(persona_match.group(1))

        # Extract ocupacion
        jobs = ["ingeniero", "profesor", "contador", "abogado", "vendedor", "empleado", "empresario", "doctor"]
        for job in jobs:
            if job in user_lower:
                extraction["ocupacion"] = job.capitalize()
                break

        # Extract ingresos
        income_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:millones?|m)', user_lower)
        if income_match:
            num = float(income_match.group(1).replace(",", "."))
            extraction["ingresos"] = int(num * 1000000)

        # Extract mascotas
        if any(x in user_lower for x in ["no tenemos", "no tengo", "sin mascotas", "sin mascota"]):
            extraction["mascotas"] = False
        elif any(x in user_lower for x in ["tenemos", "tengo", "perro", "gato"]) and "no " not in user_lower[:30]:
            extraction["mascotas"] = True

        # Extract fecha_mudanza
        if any(x in user_lower for x in ["proximo mes", "siguiente mes", "mes que viene"]):
            extraction["fecha_mudanza"] = "Proximo mes"

        # Extract aceptacion de poliza
        if ("si " in user_lower or "si," in user_lower or "acepto" in user_lower or "acuerdo" in user_lower) and "no " not in user_lower:
            extraction["acepta_poliza"] = True
        elif "no" in user_lower and "de acuerdo" in user_lower:
            extraction["acepta_poliza"] = False

        # Extract vehiculos
        if "carro" in user_lower:
            extraction["tipo_vehiculo"] = "carro"
            extraction["vehiculos"] = True
        elif "moto" in user_lower:
            extraction["tipo_vehiculo"] = "moto"
            extraction["vehiculos"] = True
        elif "ninguno" in user_lower:
            extraction["tipo_vehiculo"] = "ninguno"
            extraction["vehiculos"] = False

        return extraction

    def run_test_carlos_perez(self):
        """Run test flow with Carlos Perez - more realistic"""
        print("\n" + "="*70)
        print("[IMPROVED SIMULATOR] Agente de Arriendo Los Robles")
        print("="*70)
        print("\n[Smart agent - NO repetidas preguntas - lenguaje natural]\n")

        # More realistic conversation with multiple answers in one message
        messages = [
            "Hola, me interesa el apartamento",
            "Me llamo Carlos Perez, somos 2 personas, soy ingeniero de sistemas",
            "Gano 4 millones de pesos mensuales",
            "No tenemos mascotas, pero tenemos un carro",
            "Queremos mudarnos el proximo mes",
            "Si, estoy de acuerdo con la poliza de arrendamiento",
        ]

        for msg in messages:
            print(f"[CARLOS]: {msg}")

            # Extract data from input
            extracted = self.extract_from_input(msg)
            self.extracted_data.update(extracted)

            # Save to memory
            self.memory.save_conversation(self.phone, "user", msg)

            # Get intelligent response
            response = self.agent.get_response(msg, self.extracted_data)
            self.memory.save_conversation(self.phone, "assistant", response)

            print(f"[AGENTE]: {response}\n")

            import time
            time.sleep(0.3)

        # Final validation
        print("\n" + "-"*70)
        print("[RESUMEN FINAL]")
        print("-"*70)

        print(f"\nDatos Extraidos:")
        print(f"  - Nombre: {self.extracted_data.get('nombre', 'N/A')}")
        print(f"  - Personas: {self.extracted_data.get('personas', 'N/A')}")
        print(f"  - Ocupacion: {self.extracted_data.get('ocupacion', 'N/A')}")
        print(f"  - Ingresos: ${self.extracted_data.get('ingresos', 0):,.0f} COP")
        print(f"  - Mascotas: {'No' if not self.extracted_data.get('mascotas') else 'Si'}")
        print(f"  - Vehiculo: {self.extracted_data.get('tipo_vehiculo', 'N/A')}")
        print(f"  - Fecha mudanza: {self.extracted_data.get('fecha_mudanza', 'N/A')}")
        print(f"  - Acepta poliza: {'Si' if self.extracted_data.get('acepta_poliza') else 'No' if self.extracted_data.get('acepta_poliza') is not None else 'N/A'}")

        # Validate
        validator = QualificationValidator()
        rejection = validator.should_reject_immediately(self.extracted_data)

        if not rejection:
            is_qualified = validator.is_fully_qualified(self.extracted_data)
            print(f"\n[RESULTADO]: {'CALIFICADO - EXITO' if is_qualified else 'INCOMPLETO (datos faltantes)'}")
        else:
            print(f"\n[RESULTADO]: RECHAZADO - {rejection[1]}")

        print("-"*70 + "\n")

        self.memory.close()


if __name__ == "__main__":
    simulator = ImprovedSimulator()
    simulator.run_test_carlos_perez()
