import os
import sys
from dotenv import load_dotenv

load_dotenv()

from calendar_tool import (
    verificar_disponibilidad,
    agendar_visita,
    listar_visitas_proximas,
    cancelar_visita,
)

def test_calendar():
    print("=" * 50)
    print("TEST GOOGLE CALENDAR — Los Robles 2026")
    print("=" * 50)

    # Test 1: verificar disponibilidad
    print("\n[1] Verificando disponibilidad...")
    fecha_test = "2026-06-20T10:00:00"
    r = verificar_disponibilidad(fecha_test)
    print(f"    {r['mensaje']}")
    assert "disponible" in r, "FALLO: clave 'disponible' no encontrada"
    print("    OK")

    # Test 2: agendar visita
    print("\n[2] Agendando visita de prueba...")
    r = agendar_visita(
        nombre="Juan Test",
        telefono="+57 300 0000000",
        fecha_hora=fecha_test,
    )
    print(f"    {r['mensaje']}")
    assert r["exito"], f"FALLO: {r['mensaje']}"
    evento_id = r["evento_id"]
    print(f"    Evento ID: {evento_id}")
    print(f"    Link: {r['link']}")
    print("    OK")

    # Test 3: listar próximas visitas
    print("\n[3] Listando visitas próximas (30 días)...")
    r = listar_visitas_proximas(dias=30)
    assert r["exito"], f"FALLO: {r['mensaje']}"
    print(f"    Total encontradas: {r['total']}")
    for v in r["visitas"]:
        print(f"    - {v['titulo']} | {v['inicio']}")
    print("    OK")

    # Test 4: cancelar la visita de prueba
    print("\n[4] Cancelando visita de prueba...")
    r = cancelar_visita(evento_id)
    assert r["exito"], f"FALLO: {r['mensaje']}"
    print(f"    {r['mensaje']}")
    print("    OK")

    print("\n" + "=" * 50)
    print("TODOS LOS TESTS PASARON")
    print("=" * 50)

if __name__ == "__main__":
    test_calendar()
