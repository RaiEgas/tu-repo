# VaR RV - Web App

Pequeña aplicación Flask que calcula VaR por simulación histórica usando datos en Supabase.

Contenido del repositorio
- `VaR RV.py` : lógica y funciones para leer Supabase y calcular VaR
- `app.py` : servidor Flask que expone la UI
- `templates/index.html` : plantilla web
- `requirements.txt` : dependencias
- `Procfile` : comando de inicio para Render

Requisitos locales
- Python 3.8+

Instalación local
```
pip install -r requirements.txt
python app.py
```
Abrir http://127.0.0.1:5000/

Despliegue en Render (pasos rápidos)

1. Crea un repo en GitHub y sube el contenido del proyecto.

2. En Render (https://render.com):
   - New → Web Service → Connect to GitHub → selecciona tu repo
   - Branch: `main`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`

3. Configura variables de entorno en Render (Dashboard → Environment):
   - `SUPABASE_URL` = https://iqtvuzlmnnovhqhqedwd.supabase.co
   - `SUPABASE_KEY` = tu_clave_anon_o_service_role (usa `anon` para lecturas con RLS configuradas)

4. Deploy y abre la URL pública que te da Render.

Notas de seguridad
- NO subas la `service_role` key a GitHub. Usa las env vars de Render.
- En producción crea políticas RLS restringidas en Supabase.

Opciones avanzadas
- Añadir autentificación, gráficos (Plotly) o export CSV.
