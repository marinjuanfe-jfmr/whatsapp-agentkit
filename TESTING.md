# Testing — Agente de Arriendo Los Robles

## Ejecución de Tests

### 1. Tests Unitarios (pytest)

```bash
# Todos los tests
pytest tests/ -v

# Tests específicos de flujo
pytest tests/test_flow.py -v

# Tests de rechazo
pytest tests/test_rejections.py -v

# Con cobertura
pytest tests/ --cov=agent --cov=integrations
```

### 2. Simulador Local Interactivo

Prueba el agente como si estuvieras en WhatsApp (sin necesidad de API real):

```bash
python tests/test_local_simulator.py
```

**Comandos disponibles:**
- Escribe mensajes normales para chatear
- `estado` — ver datos del lead actual
- `limpiar` — borrar historial
- `salir` — terminar sesión

**Ejemplo de uso:**
```
Tú: Hola, me interesa el apartamento
🤖 Agente: ¡Hola! 👋 Soy el asistente virtual...

Tú: Somos 2 personas
🤖 Agente: Perfecto, ¿cuál es su ocupación...

Tú: estado
📋 ESTADO DEL LEAD
Estado: Pendiente
Personas: 2
...
```

### 3. Tests Predefinidos

Ejecutar flujos de prueba específicos sin interacción:

```bash
# Happy path: lead califica completamente
python -c "from tests.test_local_simulator import ChatSimulator; ChatSimulator().run_test_flow('happy_path')"

# Rechazo por ingresos bajos
python -c "from tests.test_local_simulator import ChatSimulator; ChatSimulator().run_test_flow('reject_income')"

# Rechazo por ser agente inmobiliario
python -c "from tests.test_local_simulator import ChatSimulator; ChatSimulator().run_test_flow('reject_agent')"

# Interés en compra
python -c "from tests.test_local_simulator import ChatSimulator; ChatSimulator().run_test_flow('purchase_interest')"
```

## Tests Disponibles

### test_flow.py
- ✅ Creación y actualización de leads
- ✅ Historial de conversaciones
- ✅ Creación de citas
- ✅ Estado del lead
- ✅ Validación de calificación
- ✅ Leads incompletos

### test_rejections.py
- ✅ Rechazo por ingresos insuficientes
- ✅ Rechazo por agente inmobiliario
- ✅ Rechazo por no aceptar póliza
- ✅ Rechazo por demasiadas personas
- ✅ Aceptación de leads válidos
- ✅ Aceptación en ingreso mínimo
- ✅ Aceptación de varias ocupaciones

## Base de Datos de Test

Los tests usan SQLite en memoria (`:memory:`), por lo que:
- ✅ Cada test es independiente
- ✅ No contamina `agentkit.db`
- ✅ Es muy rápido

## Estructura de Fixtures

En `conftest.py` hay fixtures útiles:

```python
@pytest.fixture
def memory():
    """Sesión de BD fresca para cada test"""

@pytest.fixture
def sample_lead_data():
    """Lead válido de prueba"""

@pytest.fixture
def rejected_lead_data():
    """Lead rechazado para pruebas"""
```

## Ejemplo: Escribir un nuevo test

```python
def test_my_scenario(memory, sample_lead_data):
    phone = sample_lead_data["phone_number"]
    
    # Crear lead
    lead = memory.get_or_create_lead(phone)
    
    # Actualizar datos
    memory.update_lead(phone, **sample_lead_data)
    
    # Verificar
    status = memory.get_lead_status(phone)
    assert status["personas"] == 2
    assert status["estado"] == "Calificado"
```

## CI/CD Integration

Para Railway o GitHub Actions:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ -v --cov
```

## Troubleshooting

### "ModuleNotFoundError"
```bash
# Asegúrate de estar en la raíz del proyecto
cd /ruta/al/whatsapp-agentkit
python tests/test_local_simulator.py
```

### "No module named 'agent'"
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python tests/test_local_simulator.py
```

### Tests lentos
Los tests usan SQLite en memoria, deberían ser muy rápidos (<1s por test). Si son lentos:
- Verifica que estés usando `:memory:`
- Revisa si hay queries sin índices
