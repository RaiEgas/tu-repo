"""
Configuración de la aplicación VaR RV
Variables de entorno y constantes globales
"""

import os

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://iqtvuzlmnnovhqhqedwd.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_w9A8Wv_l9DBRMtgHxuIAew_SW0_w7Q_")
SUPABASE_API_URL = f"{SUPABASE_URL}/rest/v1"

# Flask Configuration
FLASK_ENV = os.getenv("FLASK_ENV", "production")
DEBUG = FLASK_ENV == "development"
PORT = int(os.getenv("PORT", 5000))

# Tabla names
TABLE_POSITIONS = "RV.Positions"
TABLE_PRICE = "RV.Price"

# Column names
COLUMNS = {
    "fecha": "Fecha",
    "nemonico": "Nemonico",
    "nominal": "Nominal",
    "precio": "Precio"
}
