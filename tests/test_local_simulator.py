"""Local chat simulator for testing agent without WhatsApp"""
import os
import sys
from agent.brain import AgentBrain
from agent.memory import Memory, init_db
from agent.validator import QualificationValidator

# Use in-memory SQLite for testing
os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class ChatSimulator:
    """Interactive chat simulator for testing the agent"""

    def __init__(self):
        init_db()
        self.brain = AgentBrain()
        self.phone = "+573001234567"
        self.memory = Memory()

    def run_interactive(self):
        """Run interactive chat session"""
        print("\n" + "="*60)
        print("🤖 SIMULADOR DE CHAT — Agente de Arriendo Los Robles")
        print("="*60)
        print("\nEscribe 'salir' para terminar")
        print("Escribe 'estado' para ver el estado del lead")
        print("Escribe 'limpiar' para borrar el historial\n")

        while True:
            try:
                user_input = input("Tú: ").strip()

                if not user_input:
                    continue

                if user_input.lower() == "salir":
                    print("\n👋 ¡Hasta luego!")
                    break

                if user_input.lower() == "estado":
                    self._show_lead_status()
                    continue

                if user_input.lower() == "limpiar":
                    self._clear_history()
                    continue

                # Process message with agent
                result = self.brain.process_message(self.phone, user_input)
                response = result.get("response", "")
                actions = result.get("actions", [])

                # Display response
                if response:
                    print(f"\n🤖 Agente: {response}\n")

                # Show actions if any
                if actions:
                    print(f"[Actions: {len(actions)} tool(s) to execute]")
                    for action in actions:
                        print(f"  - {action['tool']}: {action['input']}")
                    print()

            except KeyboardInterrupt:
                print("\n\n👋 Interrupted")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")

        self.memory.close()

    def _show_lead_status(self):
        """Display current lead status"""
        status = self.memory.get_lead_status(self.phone)
        lead = self.memory.get_lead(self.phone)

        print("\n" + "-"*60)
        print("📋 ESTADO DEL LEAD")
        print("-"*60)
        print(f"Estado: {status['estado']}")
        if lead:
            print(f"Nombre: {lead.nombre or '-'}")
            print(f"Personas: {status['personas'] or '-'}")
            print(f"Ocupación: {status['ocupacion'] or '-'}")
            print(f"Ingresos: ${status['ingresos']:,.0f}" if status['ingresos'] else "Ingresos: -")
            print(f"Mascotas: {'Sí' if status['mascotas'] else 'No' if status['mascotas'] is not None else '-'}")
            print(f"Vehículo: {'Sí' if status['vehiculos'] else 'No' if status['vehiculos'] is not None else '-'}")
            print(f"Fecha de mudanza: {status['fecha_mudanza'] or '-'}")
            print(f"Acepta póliza: {'Sí' if status['acepta_poliza'] else 'No' if status['acepta_poliza'] is not None else '-'}")
            print(f"Interés en compra: {'Sí' if status['interes_compra'] else 'No'}")
            if status['fecha_visita']:
                print(f"Fecha de visita: {status['fecha_visita']}")

        print("-"*60 + "\n")

    def _clear_history(self):
        """Clear conversation history"""
        self.memory.close()
        self.memory = Memory()
        print("\n✓ Historial limpiado\n")

    def run_test_flow(self, test_name: str = "happy_path"):
        """Run predefined test flows"""
        print(f"\n🧪 Ejecutando flujo de prueba: {test_name}\n")

        if test_name == "happy_path":
            self._test_happy_path()
        elif test_name == "reject_income":
            self._test_reject_income()
        elif test_name == "reject_agent":
            self._test_reject_agent()
        elif test_name == "purchase_interest":
            self._test_purchase_interest()
        else:
            print(f"❌ Test no encontrado: {test_name}")

    def _test_happy_path(self):
        """Test: Lead qualifies and schedules visit"""
        messages = [
            "Hola, me interesa el apartamento de Los Robles",
            "Somos 2 personas",
            "Soy ingeniero de sistemas",
            "Mis ingresos son de 5 millones de pesos mensuales",
            "No tenemos mascotas",
            "Necesitamos mudarnos en abril de este año",
            "Sí, estoy de acuerdo con la póliza",
            "Tenemos un carro",
        ]

        for msg in messages:
            print(f"👤 Usuario: {msg}")
            result = self.brain.process_message(self.phone, msg)
            response = result.get("response", "")
            if response:
                print(f"🤖 Agente: {response}\n")

    def _test_reject_income(self):
        """Test: Lead rejected for low income"""
        messages = [
            "Hola, me interesa el apartamento",
            "Somos 1 persona",
            "Trabajo en ventas",
            "Mis ingresos son de 2 millones mensuales",
        ]

        for msg in messages:
            print(f"👤 Usuario: {msg}")
            result = self.brain.process_message(self.phone, msg)
            response = result.get("response", "")
            if response:
                print(f"🤖 Agente: {response}\n")

    def _test_reject_agent(self):
        """Test: Lead rejected for being real estate agent"""
        messages = [
            "Hola, estoy interesado en el apartamento",
            "Trabajo como agente inmobiliario",
        ]

        for msg in messages:
            print(f"👤 Usuario: {msg}")
            result = self.brain.process_message(self.phone, msg)
            response = result.get("response", "")
            if response:
                print(f"🤖 Agente: {response}\n")

    def _test_purchase_interest(self):
        """Test: Lead shows interest in buying"""
        messages = [
            "Hola, ¿venden el apartamento?",
            "Me gustaría comprarlo",
        ]

        for msg in messages:
            print(f"👤 Usuario: {msg}")
            result = self.brain.process_message(self.phone, msg)
            response = result.get("response", "")
            if response:
                print(f"🤖 Agente: {response}\n")


if __name__ == "__main__":
    simulator = ChatSimulator()

    if len(sys.argv) > 1:
        # Run specific test flow
        test_name = sys.argv[1]
        simulator.run_test_flow(test_name)
    else:
        # Run interactive mode
        simulator.run_interactive()
