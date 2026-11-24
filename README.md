# agent_adk_diego_garcia — Agente de Gastos Personales

Agente de IA desarrollado con **Python** y **Google Agent Development Kit (ADK)** que ayuda a
administrar gastos personales. El agente interpreta lo que pide el usuario en lenguaje natural,
decide qué herramienta usar, la ejecuta y arma la respuesta con los resultados obtenidos
(no inventa datos: todo sale de las herramientas).

Los gastos se guardan en un archivo local `gastos_agent/gastos.json`.

## Problema que resuelve

Llevar el control de gastos suele ser tedioso. Con este agente basta con escribir
*"ayer gasté $3500 en el súper"* o *"¿en qué gasté más este mes?"* y el agente registra,
busca o calcula lo necesario.

## Herramientas

| Herramienta | Responsabilidad | Parámetros |
|---|---|---|
| `registrar_gasto` | Guarda un gasto nuevo | `descripcion`, `monto`, `categoria`, `fecha` (opcional, AAAA-MM-DD) |
| `buscar_gastos` | Lista gastos con filtros | `categoria`, `desde`, `hasta` (todos opcionales) |
| `resumen_gastos` | Calcula total, promedio, total por categoría y mayor gasto de un mes | `mes` (AAAA-MM, opcional) |
| `eliminar_gasto` | Borra un gasto por su ID | `id_gasto` |

Categorías válidas: `comida`, `transporte`, `servicios`, `salud`, `ocio`, `educacion`, `otros`.

### Validación

Todas las herramientas devuelven un diccionario con un campo `status`:

- `ok` → la operación salió bien.
- `sin_resultados` → la consulta es válida pero no hay datos (ej. un mes sin gastos).
- `error` → argumento inválido o falla interna, con un `mensaje` explicativo.

Se validan: descripción vacía, monto no numérico o ≤ 0, categoría inexistente, fechas con
formato incorrecto, rango de fechas invertido, ID inexistente y archivo de datos corrupto.

## Instrucciones del agente

Definidas en `gastos_agent/agent.py`:

- **Rol:** "Gastón", asistente de finanzas personales.
- **Objetivo:** registrar, consultar, analizar y corregir gastos usando siempre las herramientas.
- **Restricciones:** solo categorías válidas, fechas en formato AAAA-MM-DD, pedir datos faltantes,
  no responder temas ajenos a los gastos.
- **Comportamiento:** explicar errores en lenguaje simple, avisar cuando no hay resultados,
  responder en español de forma breve.

## Estructura

```
agent_adk_diego_garcia/
├── gastos_agent/
│   ├── __init__.py
│   ├── agent.py        # definición del agente (modelo, instrucciones, herramientas)
│   ├── tools.py        # las 4 herramientas
│   └── .env.example    # plantilla de configuración
├── tests/
│   └── test_tools.py   # tests de las herramientas (pytest)
├── requirements.txt
└── README.md
```

## Cómo usarlo

1. **Clonar e instalar dependencias** (Python 3.10+):

   ```bash
   git clone https://github.com/<tu-usuario>/agent_adk_diego_garcia.git
   cd agent_adk_diego_garcia
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configurar el modelo** (vía LiteLLM):

   ```bash
   cp gastos_agent/.env.example gastos_agent/.env
   ```

   Editar `gastos_agent/.env` y poner la API key. Por defecto usa `gemini/gemini-2.5-flash`
   (API key gratuita en https://aistudio.google.com/apikey). Se puede cambiar `MODELO` por
   cualquier modelo soportado por LiteLLM, por ejemplo `groq/llama-3.3-70b-versatile` u
   `ollama_chat/llama3.1` (local).

3. **Levantar la interfaz web de ADK** (desde la carpeta raíz del proyecto):

   ```bash
   adk web
   ```

   Abrir http://localhost:8000 y elegir `gastos_agent` en el desplegable.
   También se puede usar por terminal con `adk run gastos_agent`.

4. **Correr los tests:**

   ```bash
   pytest
   ```

## Ejemplos de prueba

| Mensaje | Herramienta que debería usar |
|---|---|
| "Gasté 4500 en el supermercado" | `registrar_gasto` (categoría inferida: comida) |
| "Ayer cargué nafta por 20000" | `registrar_gasto` (transporte, fecha de ayer) |
| "Mostrame los gastos de comida de noviembre" | `buscar_gastos` |
| "¿Cuánto gasté este mes y en qué gasté más?" | `resumen_gastos` |
| "Borrá el gasto de la nafta" | `buscar_gastos` → `eliminar_gasto` |
| "Gasté -50 en algo" | `registrar_gasto` → error de validación, el agente lo explica |
| "Resumen de enero de 2020" | `resumen_gastos` → sin resultados |

En la interfaz web de ADK (pestaña *Events*) se puede ver qué herramienta eligió el agente
y con qué argumentos en cada paso.
