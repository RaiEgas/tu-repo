# VaR RV - Value at Risk por Simulación Histórica

Aplicación modular para calcular Value at Risk (VaR) usando simulación histórica con datos en Supabase.

## Estructura del Proyecto

```
.
├── app.py                      # Aplicación Flask (servidor web)
├── cli.py                      # Script CLI (línea de comandos)
├── config.py                   # Configuración centralizada
├── models/
│   ├── __init__.py
│   ├── supabase_client.py     # Cliente para conexión Supabase
│   ├── var_calculator.py      # Lógica de cálculo de VaR
├── templates/
│   ├── index.html             # Plantilla web principal
├── requirements.txt           # Dependencias Python
├── Procfile                   # Comando de inicio para Render
├── README.md                  # Este archivo
└── .gitignore                 # Archivos a ignorar en Git
```

## Características

- ✅ Cálculo de VaR por simulación histórica
- ✅ Integración con Supabase (datos en tiempo real)
- ✅ Interfaz web responsiva (Bootstrap)
- ✅ CLI para cálculos sin servidor
- ✅ Modelos centralizados y reutilizables
- ✅ Despliegue fácil en Render

## Requisitos

- Python 3.8+
- Acceso a Supabase (con tablas `RV.Positions` y `RV.Price`)

## Instalación Local

### 1. Clonar/descargar el proyecto

```bash
git clone https://github.com/RaiEgas/tu-repo.git
cd tu-repo
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno (opcional local)

Crea un archivo `.env.local` (NO subir a Git):

```
SUPABASE_URL=https://iqtvuzlmnnovhqhqedwd.supabase.co
SUPABASE_KEY=tu_clave_anon
```

### 4. Usar la aplicación

**Opción A: Servidor web**
```bash
python app.py
# Abre http://127.0.0.1:5000
```

**Opción B: Línea de comandos**
```bash
# Validar conexión
python cli.py --validate

# Calcular VaR
python cli.py --fecha 30/01/2024 --activo AAPL --confianza 0.95
```

## Despliegue en Render

### 1. Subir a GitHub

```bash
git add .
git commit -m "VaR RV - refactored modular structure"
git push origin main
```

### 2. Crear Web Service en Render

- Ve a https://dashboard.render.com → New → Web Service
- Conecta tu repo GitHub
- Configura:
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
  - **Environment Variables**:
    - `SUPABASE_URL=https://iqtvuzlmnnovhqhqedwd.supabase.co`
    - `SUPABASE_KEY=tu_clave_anon`
- Deploy

### 3. Acceder a la app

Tu URL pública será algo como: `https://var-rv.onrender.com`

## API Endpoints

- `GET /` — Página principal
- `POST /` — Calcular VaR (formulario)
- `GET /health` — Estado de la aplicación
- `GET /api/validate` — Validar conexión Supabase

## Modelos Disponibles

### `models.supabase_client`

```python
from models.supabase_client import supabase

# Obtener datos
df_positions = supabase.get_positions()
df_prices = supabase.get_prices()

# Validar conexión
validation = supabase.validate_connection()
```

### `models.var_calculator`

```python
from models.supabase_client import supabase
from models.var_calculator import VaRCalculator

calculator = VaRCalculator(supabase)
res, error = calculator.calculate_for_position(
    fecha_analisis='30/01/2024',
    activo='AAPL',
    confidence=0.95
)

if not error:
    print(f"VaR: ${res['var']:.2f}")
    print(res['simulaciones'])  # DataFrame con resultados
```

## Configuración (`config.py`)

Centraliza todas las constantes y env vars:

```python
SUPABASE_URL = "..."
SUPABASE_KEY = "..."
TABLE_POSITIONS = "RV.Positions"
TABLE_PRICE = "RV.Price"
```

## Notas de Seguridad

⚠️ **NO subir keys sensibles a GitHub**

- Usa variables de entorno en Render
- En desarrollo, usa un archivo `.env.local` local
- Para producción, implementa políticas RLS en Supabase

## Licencia

MIT - Libre para usar y modificar

## Contacto / Soporte

Para problemas o preguntas, abre un issue en GitHub o contacta al desarrollador.

