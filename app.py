import os
import importlib.util
from flask import Flask, render_template, request

BASE_DIR = os.path.dirname(__file__)
MODULE_PATH = os.path.join(BASE_DIR, "VaR RV.py")

spec = importlib.util.spec_from_file_location("varscript", MODULE_PATH)
varmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(varmod)

app = Flask(__name__)


def parse_date_input(s):
    # try common formats; accept empty -> None
    if not s:
        return None
    try:
        return varmod.pd.to_datetime(s, dayfirst=True)
    except Exception:
        try:
            return varmod.pd.to_datetime(s)
        except Exception:
            return None


@app.route('/', methods=['GET', 'POST'])
def index():
    df_positions = varmod.get_supabase_data("RV.Positions")
    df_price = varmod.get_supabase_data("RV.Price")

    assets = []
    if df_positions is not None and not df_positions.empty and "Nemonico" in df_positions.columns:
        assets = sorted(df_positions["Nemonico"].dropna().unique().tolist())
    elif df_price is not None and not df_price.empty and "Nemonico" in df_price.columns:
        assets = sorted(df_price["Nemonico"].dropna().unique().tolist())

    result = None
    table_html = None

    if request.method == 'POST':
        fecha_in = request.form.get('fecha')
        activo = request.form.get('activo')
        confidence = float(request.form.get('confidence') or 0.95)

        fecha_dt = parse_date_input(fecha_in)
        if fecha_dt is None:
            error = "Fecha inválida (use DD/MM/YYYY o YYYY-MM-DD)."
            return render_template('index.html', assets=assets, error=error)

        # find nominal in positions
        df_positions["Fecha"] = varmod.pd.to_datetime(df_positions["Fecha"]) if "Fecha" in df_positions.columns else df_positions["Fecha"]
        port_activo = df_positions[(df_positions["Fecha"] == fecha_dt) & (df_positions["Nemonico"] == activo)]
        if port_activo.empty:
            error = f"No hay posición para {activo} en {fecha_dt.strftime('%d/%m/%Y')}"
            return render_template('index.html', assets=assets, error=error)

        nominal = port_activo["Nominal"].iloc[0]

        # get prices up to fecha
        df_price["Fecha"] = varmod.pd.to_datetime(df_price["Fecha"]) if "Fecha" in df_price.columns else df_price["Fecha"]
        df_precios_filtrado = df_price[(df_price["Fecha"] <= fecha_dt) & (df_price["Nemonico"] == activo)].copy()
        df_precios_filtrado = df_precios_filtrado.sort_values("Fecha")
        if df_precios_filtrado.empty or len(df_precios_filtrado) < 2:
            error = f"No hay suficientes precios históricos para {activo} hasta {fecha_dt.strftime('%d/%m/%Y')}"
            return render_template('index.html', assets=assets, error=error)

        prices = df_precios_filtrado["Precio"].astype(float).values

        # compute var
        res = varmod.compute_historical_var(prices, nominal, confidence)

        result = {
            'activo': activo,
            'fecha': fecha_dt.strftime('%d/%m/%Y'),
            'nominal': int(nominal),
            'confidence': confidence,
            'base_price': f"{res['base_price']:.2f}",
            'mtm_base': f"{res['mtm_base']:.2f}",
            'var': f"{res['var']:.2f}",
            'percentile_value': f"{res['percentile_value']:.2f}",
        }

        out_df = varmod.pd.DataFrame({
            'Fecha': df_precios_filtrado['Fecha'].dt.strftime('%Y-%m-%d').values[1:],
            'shock': res['shocks'],
            'simulated_price': res['simulated_prices'],
            'mtm_sim': res['mtm_sim'],
            'up': res['up']
        })
        table_html = out_df.to_html(classes='table table-sm table-striped', index=False, float_format='%.2f')

    return render_template('index.html', assets=assets, result=result, table_html=table_html)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
