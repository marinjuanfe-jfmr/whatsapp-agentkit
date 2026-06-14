"""
Test 3 escenarios con Claude API real (sin mock)
Ejecuta conversaciones automáticas para validar el comportamiento del agente
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

# Asegurar que el path es correcto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Verify API key is loaded
if not os.getenv("ANTHROPIC_API_KEY"):
    print("[ERROR] ANTHROPIC_API_KEY no está configurada")
    sys.exit(1)

from agent.brain import AgentBrain
from agent.memory import Memory, init_db


class ScenarioTester:
    """Tester para ejecutar escenarios de prueba con Claude real"""

    def __init__(self):
        init_db()
        self.brain = AgentBrain()

    def run_scenario(self, scenario_name: str, phone: str, messages: list) -> dict:
        """Run a test scenario and return conversation"""
        print("\n" + "="*70)
        print(f"ESCENARIO: {scenario_name}")
        print("="*70)
        print(f"[Usando Claude API real]\n")

        memory = Memory()
        conversation = []

        for user_msg in messages:
            print(f"[USUARIO]: {user_msg}")

            try:
                # Process with Claude
                result = self.brain.process_message(phone, user_msg)
                response = result.get("response", "")
                actions = result.get("actions", [])

                if response:
                    print(f"[CLAUDE]: {response}\n")
                    conversation.append({
                        "user": user_msg,
                        "agent": response,
                        "actions": len(actions)
                    })
                else:
                    print("[CLAUDE]: [Sin respuesta]\n")
                    conversation.append({
                        "user": user_msg,
                        "agent": "[Sin respuesta]",
                        "actions": 0
                    })

            except Exception as e:
                print(f"[ERROR]: {str(e)}\n")
                conversation.append({
                    "user": user_msg,
                    "agent": f"[Error: {str(e)}]",
                    "actions": 0
                })

        # Get final lead status
        lead_status = memory.get_lead_status(phone)
        lead = memory.get_lead(phone)

        memory.close()

        return {
            "scenario": scenario_name,
            "conversation": conversation,
            "final_status": lead_status,
            "final_lead": lead
        }

    def print_summary(self, result: dict):
        """Print summary of scenario results"""
        print("\n" + "-"*70)
        print("RESUMEN FINAL")
        print("-"*70)

        if result["final_lead"]:
            lead = result["final_lead"]
            print(f"\nEstado Final: {result['final_status'].get('estado', 'N/A')}")
            if lead.nombre:
                print(f"Nombre: {lead.nombre}")
            if lead.ingresos:
                print(f"Ingresos: ${lead.ingresos:,.0f} COP")
            if lead.personas:
                print(f"Personas: {lead.personas}")
            if lead.motivo_rechazo:
                print(f"Motivo Rechazo: {lead.motivo_rechazo}")
            if lead.interes_compra:
                print(f"Interes en Compra: Si")
        else:
            print("\nNo se creó lead en este escenario")

        print("-"*70 + "\n")


def main():
    """Run all 3 scenarios"""
    tester = ScenarioTester()

    # ESCENARIO 1: Lead que califica
    scenario1_messages = [
        "Hola, me interesa mucho el apartamento de Los Robles",
        "Me llamo Carlos Pérez, somos 2 personas",
        "Soy ingeniero de sistemas",
        "Mis ingresos son 4 millones de pesos mensuales",
        "No tenemos mascotas",
        "Tenemos un carro",
        "Nos gustaría mudarnos el próximo mes",
        "Sí, estoy de acuerdo con la póliza de arrendamiento"
    ]

    result1 = tester.run_scenario(
        "1 - Lead que CALIFICA completamente",
        "+573001234567",
        scenario1_messages
    )
    tester.print_summary(result1)

    # ESCENARIO 2: Rechazo por inmobiliaria
    scenario2_messages = [
        "Hola, tengo un cliente muy interesado en el apartamento",
        "Soy agente inmobiliario y represento a varios compradores",
        "Tenemos referencias de bancos y todo"
    ]

    result2 = tester.run_scenario(
        "2 - Rechazo por INMOBILIARIA",
        "+573001234568",
        scenario2_messages
    )
    tester.print_summary(result2)

    # ESCENARIO 3: Interés en compra
    scenario3_messages = [
        "Hola, ¿el apartamento está en venta?",
        "Quisiera comprarlo, me interesa invertir en la zona",
        "Tengo presupuesto disponible ahora mismo"
    ]

    result3 = tester.run_scenario(
        "3 - Interés en COMPRA (no rechazo)",
        "+573001234569",
        scenario3_messages
    )
    tester.print_summary(result3)

    # Final report
    print("\n" + "="*70)
    print("REPORTE FINAL DE 3 ESCENARIOS")
    print("="*70)
    print(f"\nEscenario 1 ({result1['scenario']})")
    print(f"  Estado: {result1['final_status'].get('estado')}")
    print(f"  Mensajes: {len(result1['conversation'])}")

    print(f"\nEscenario 2 ({result2['scenario']})")
    print(f"  Estado: {result2['final_status'].get('estado')}")
    print(f"  Mensajes: {len(result2['conversation'])}")

    print(f"\nEscenario 3 ({result3['scenario']})")
    print(f"  Estado: {result3['final_status'].get('estado')}")
    print(f"  Interes Compra: {result3['final_status'].get('interes_compra')}")
    print(f"  Mensajes: {len(result3['conversation'])}")

    print("\n" + "="*70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR CRÍTICO]: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
