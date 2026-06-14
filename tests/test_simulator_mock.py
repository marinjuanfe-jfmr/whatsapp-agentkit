"""
Simulador MOCK — Demostración del flujo sin necesidad de API real
Usa respuestas pre-programadas para validar el flujo de conversación
"""
import os
import sys
from datetime import datetime
from agent.memory import Memory, init_db
from agent.validator import QualificationValidator

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class MockAgentResponse:
    """Mock agent que simula respuestas sin Claude API"""

    def __init__(self):
        self.conversation_state = {}
        self.responses_map = {
            "hola|interesa|apartamento": """Hola! Soy el asistente virtual del apartamento en Los Robles.
Tenemos disponible un apto de 3 habitaciones, 48m2, parqueadero incluido,
por $1.800.000/mes con administración incluida. Te gustaría conocer más detalles?""",

            "personas|cuantas": "Para cuantas personas es el apartamento?",

            "ocupacion|trabajo|profesion": "Cual es su ocupación o fuente de ingreso?",

            "ingresos|gano|salario|ganan": "Sus ingresos mensuales son de al menos $3.600.000?",

            "mascotas|perro|gato|mascota": "Tiene mascotas?",

            "mudarse|mudanza|cuando": "Cuando necesitaría mudarse?",

            "poliza|seguro": "Esta de acuerdo con la poliza de arrendamiento como único requisito?",

            "vehiculo|carro|moto": "Tiene vehículo? Carro, moto o ninguno?",
        }

    def get_response(self, user_input: str, extracted_data: dict) -> str:
        """Generate response based on input and extracted data"""
        user_lower = user_input.lower()

        # Check for patterns
        for pattern, response in self.responses_map.items():
            if any(word in user_lower for word in pattern.split("|")):
                return response

        # Check if fully qualified
        if all([
            extracted_data.get("personas"),
            extracted_data.get("ocupacion"),
            extracted_data.get("ingresos"),
            extracted_data.get("mascotas") is not None,
            extracted_data.get("fecha_mudanza"),
            extracted_data.get("acepta_poliza") is not None,
            extracted_data.get("tipo_vehiculo"),
        ]):
            if extracted_data.get("ingresos", 0) >= 3600000 and extracted_data.get("acepta_poliza"):
                return """[QUALIFIED] Perfecto, calificaste!

Antes de coordinar la visita, te comparto fotos y video del apartamento para que lo conozcas.

[Fotos y video del apartamento serian enviados aqui]

A que dia y hora te quedaria bien para visitarlo?"""

        # Default responses
        if any(x in user_lower for x in ["gracias", "ok", "entendido", "si"]):
            return "Perfecto, continua."

        return "Entendido. Por favor, responde la pregunta anterior para continuar."


class MockSimulator:
    """Mock chat simulator with pre-programmed responses"""

    def __init__(self):
        init_db()
        self.memory = Memory()
        self.phone = "+573001234567"
        self.mock_agent = MockAgentResponse()
        self.extracted_data = {}

    def extract_from_input(self, user_input: str) -> dict:
        """Improved extraction from user input"""
        user_lower = user_input.lower()
        extraction = {}

        # Extract nombre
        if "me llamo" in user_lower or "nombre" in user_lower:
            words = user_input.split()
            for i, word in enumerate(words):
                if word.lower() in ["llamo", "es"]:
                    if i + 1 < len(words):
                        # Get next 1-2 words as name
                        name_parts = [words[i+1]]
                        if i + 2 < len(words) and words[i+2][0].isupper():
                            name_parts.append(words[i+2].rstrip(","))
                        extraction["nombre"] = " ".join(name_parts)
                    break

        # Extract personas - look for number followed by "persona" or "personas"
        import re
        persona_match = re.search(r'(\d+)\s*persona', user_lower)
        if persona_match:
            extraction["personas"] = int(persona_match.group(1))
        else:
            # Fallback: look for standalone numbers 1-10 at start of relevant sentence
            if "somos" in user_lower or "personas" in user_lower:
                for word in user_input.split():
                    if word.isdigit() and 1 <= int(word) <= 10:
                        extraction["personas"] = int(word)
                        break

        # Extract ocupación
        jobs = ["ingeniero", "profesor", "contador", "abogado", "vendedor", "empleado", "empresario", "doctor"]
        for job in jobs:
            if job in user_lower:
                extraction["ocupacion"] = job.capitalize()
                break

        # Extract ingresos - look for number + "millones"
        income_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:millones?|m)', user_lower)
        if income_match:
            num = float(income_match.group(1).replace(",", "."))
            extraction["ingresos"] = int(num * 1000000)

        # Extract mascotas
        if any(x in user_lower for x in ["no tenemos", "no tengo", "no tiene", "no tienen", "sin mascotas"]):
            extraction["mascotas"] = False
        elif any(x in user_lower for x in ["si tenemos", "tenemos", "perro", "gato", "mascota"]):
            if "no " not in user_lower:
                extraction["mascotas"] = True

        # Extract fecha_mudanza
        if any(x in user_lower for x in ["proximo mes", "siguiente mes", "mes que viene", "abril", "mayo", "mes que viene"]):
            extraction["fecha_mudanza"] = "Proximo mes"

        # Extract aceptación de póliza - be strict: only if "si" or "acepto" without "no"
        if ("si " in user_lower or "si," in user_lower or "acepto" in user_lower) and "no " not in user_lower:
            extraction["acepta_poliza"] = True
        elif "no" in user_lower and "de acuerdo" in user_lower:
            extraction["acepta_poliza"] = False

        # Extract vehículos
        if "carro" in user_lower:
            extraction["tipo_vehiculo"] = "carro"
            extraction["vehiculos"] = True
        elif "moto" in user_lower:
            extraction["tipo_vehiculo"] = "moto"
            extraction["vehiculos"] = True
        elif any(x in user_lower for x in ["ninguno", "no tenemos", "no tengo"]):
            extraction["tipo_vehiculo"] = "ninguno"
            extraction["vehiculos"] = False

        return extraction

    def run_test_carlos_perez(self):
        """Run test flow with Carlos Perez data"""
        print("\n" + "="*70)
        print("[MOCK SIMULATOR] Agente de Arriendo Los Robles")
        print("="*70)
        print("\n[Mode: Simulation without real API - predefined responses]\n")

        messages = [
            ("Hola, me interesa el apartamento", "lead"),
            ("Me llamo Carlos Perez, somos 2 personas", "lead"),
            ("Soy ingeniero de sistemas", "lead"),
            ("Mis ingresos son 4 millones de pesos mensuales", "lead"),
            ("No tenemos mascotas", "lead"),
            ("Queremos mudarnos el proximo mes", "lead"),
            ("Si, estoy de acuerdo con la poliza de arrendamiento", "lead"),
            ("Si, tenemos un carro", "lead"),
        ]

        for msg, role in messages:
            print(f"[CARLOS]: {msg}")

            # Extract data
            extracted = self.extract_from_input(msg)
            self.extracted_data.update(extracted)

            # Save to memory
            self.memory.save_conversation(self.phone, "user", msg)

            # Get mock response
            response = self.mock_agent.get_response(msg, self.extracted_data)
            self.memory.save_conversation(self.phone, "assistant", response)

            print(f"[AGENT]: {response}\n")

            # Small delay for readability
            import time
            time.sleep(0.3)

        # Final validation
        print("\n" + "-"*70)
        print("[VALIDATION SUMMARY]")
        print("-"*70)

        print(f"\nExtracted Data:")
        print(f"  - Name: {self.extracted_data.get('nombre', 'N/A')}")
        print(f"  - Persons: {self.extracted_data.get('personas', 'N/A')}")
        print(f"  - Occupation: {self.extracted_data.get('ocupacion', 'N/A')}")
        print(f"  - Income: ${self.extracted_data.get('ingresos', 0):,.0f} COP")
        print(f"  - Pets: {'No' if not self.extracted_data.get('mascotas') else 'Yes'}")
        print(f"  - Vehicle: {self.extracted_data.get('tipo_vehiculo', 'N/A')}")
        print(f"  - Move Date: {self.extracted_data.get('fecha_mudanza', 'N/A')}")
        print(f"  - Accepts Insurance: {'Yes' if self.extracted_data.get('acepta_poliza') else 'No'}")

        # Validate qualification
        validator = QualificationValidator()
        rejection = validator.should_reject_immediately(self.extracted_data)

        if not rejection:
            is_qualified = validator.is_fully_qualified(self.extracted_data)
            print(f"\n[RESULT]: {'QUALIFIED - SUCCESS' if is_qualified else 'INCOMPLETE (missing data)'}")
        else:
            print(f"\n[RESULT]: REJECTED - {rejection[1]}")

        print("-"*70 + "\n")

        # Save to memory
        self.memory.update_lead(
            self.phone,
            **self.extracted_data,
            estado="Calificado" if not rejection else "Rechazado"
        )

        self.memory.close()


if __name__ == "__main__":
    simulator = MockSimulator()
    simulator.run_test_carlos_perez()
