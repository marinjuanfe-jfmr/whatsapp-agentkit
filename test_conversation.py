"""
Simula una conversacion completa sin WhatsApp.
Uso: python test_conversation.py
Edita PHONE_NUMBER y MESSAGES abajo para cada prueba.
"""
import sys
from agent.brain import AgentBrain
from agent.memory import init_db, Memory

init_db()

# Cambia esto en cada prueba para evitar choques con leads anteriores
PHONE_NUMBER = "+573010000999"

MESSAGES = [
    "Hola buenas, vi el anuncio del apartamento en los robles, sigue disponible? una pregunta, tiene agua caliente o calentador?",
    "Y el parqueadero como es, es privado o comunal?",
    "Que estrato es el sector?",
    "Eso lo vemos despues, mejor cuentame mas del apartamento, las habitaciones por ejemplo",
    "Ah bueno, le cuento que yo en realidad soy agente inmobiliario, manejo varios clientes interesados en la zona",
    "Pero mirando bien, lo que realmente me interesa a mi es comprar el apartamento, el propietario estaria dispuesto a vender?",
]

brain = AgentBrain()

print("=" * 60)
print(f"SIMULANDO CONVERSACION: {PHONE_NUMBER}")
print("=" * 60)

for i, msg in enumerate(MESSAGES, 1):
    print(f"\n--- Mensaje {i} ---")
    print(f"USUARIO: {msg}")
    result = brain.process_message(PHONE_NUMBER, msg)
    print(f"AGENTE: {result.get('response')}")

print("\n" + "=" * 60)
print("ESTADO FINAL DEL LEAD")
print("=" * 60)
memory = Memory()
lead = memory.get_lead(PHONE_NUMBER)
if lead:
    for col in lead.__table__.columns:
        print(f"  {col.name}: {getattr(lead, col.name)}")
else:
    print("  Lead no encontrado")
memory.close()
brain.close()
