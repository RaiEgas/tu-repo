"""
Aplicación Flask para VaR RV
Interfaz web para calcular Value at Risk por simulación histórica
"""

from flask import Flask, render_template, request
from models.supabase_client import supabase
from models.var_calculator import VaRCalculator
import config

app = Flask(__name__)
app.config['DEBUG'] = config.DEBUG

# Inicializar calculador
calculator = VaRCalculator(supabase)


@app.route('/', methods=['GET', 'POST'])
def index():
    """Página principal con formulario de cálculo de VaR"""
    
    # Obtener lista de activos disponibles
    df_positions = supabase.get_positions()
    assets = []
    
    if not df_positions.empty and "Nemonico" in df_positions.columns:
        assets = sorted(df_positions["Nemonico"].dropna().unique().tolist())
    else:
        df_prices = supabase.get_prices()
        if not df_prices.empty and "Nemonico" in df_prices.columns:
            assets = sorted(df_prices["Nemonico"].dropna().unique().tolist())
    
    result = None
    error = None
    table_html = None

    if request.method == 'POST':
        fecha_in = request.form.get('fecha', '').strip()
        activo = request.form.get('activo', '').strip()
        confidence = float(request.form.get('confidence') or 0.95)

        # Validar entrada
        if not fecha_in:
            error = "Por favor ingrese una fecha (DD/MM/YYYY)"
        elif not activo:
            error = "Por favor seleccione un activo"
        else:
            # Calcular VaR
            result, error = calculator.calculate_for_position(fecha_in, activo, confidence)
            
            if error:
                result = None

    return render_template('index.html', assets=assets, result=result, error=error)


@app.route('/health', methods=['GET'])
def health():
    """Endpoint para verificar estado de la app"""
    return {'status': 'ok', 'service': 'var-rv'}, 200


@app.route('/api/validate', methods=['GET'])
def api_validate():
    """API para validar conexión a Supabase"""
    validation = supabase.validate_connection()
    return validation, 200 if validation['connected'] else 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.PORT, debug=config.DEBUG)
