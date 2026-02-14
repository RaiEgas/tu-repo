import numpy as np
import pandas as pd
import sys
import requests
from io import StringIO

# Configuración Supabase
SUPABASE_URL = "https://iqtvuzlmnnovhqhqedwd.supabase.co"
SUPABASE_KEY = "sb_publishable_w9A8Wv_l9DBRMtgHxuIAew_SW0_w7Q_"
SUPABASE_API_URL = f"{SUPABASE_URL}/rest/v1"

# historical_var.py
# Modelo de VaR por Simulación Histórica
# Uso: importar la función compute_historical_var(...) o ejecutar como script


def get_supabase_data(table_name):
    """
    Obtiene datos de una tabla Supabase via API REST
    """
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    # usar select=* para asegurar que se devuelvan columnas; url-encode por si hay puntos
    from requests.utils import requote_uri
    url = requote_uri(f"{SUPABASE_API_URL}/{table_name}?select=*")
    headers.update({"Accept": "application/json", "Content-Type": "application/json"})
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if not data:
                # devolver DataFrame vacío pero mostrar aviso
                return pd.DataFrame()
            return pd.DataFrame(data)
        else:
            print(f"Error HTTP al leer {table_name}: {response.status_code}")
            print(response.text)
            return pd.DataFrame()
    except Exception as e:
        print(f"Excepción al conectar a Supabase: {e}")
        return pd.DataFrame()


def validate_supabase_connection():
    """
    Valida la conexión a Supabase y la existencia de tablas
    """
    print("="*70)
    print("VALIDACIÓN DE CONEXIÓN A SUPABASE")
    print("="*70)
    
    # Probar conexión
    print(f"\n🔍 Conectando a: {SUPABASE_URL}")
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    
    try:
        test_url = f"{SUPABASE_API_URL}/RV.Price?limit=1"
        response = requests.get(test_url, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Conexión a Supabase: EXITOSA")
        else:
            print(f"❌ Conexión a Supabase: FALLIDA")
            print(f"   Código de error: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False
    
    # Validar tabla RV.Price
    print(f"\n📊 Validando tabla RV.Price...")
    df_price = get_supabase_data("RV.Price")
    if df_price is not None and not df_price.empty:
        print(f"✅ Tabla RV.Price encontrada")
        print(f"   Registros: {len(df_price)}")
        print(f"   Columnas: {df_price.columns.tolist()}")
        print(f"\n   Primeros registros:")
        print(df_price.head(3).to_string())
    else:
        print(f"❌ No se pudo leer tabla RV.Price")
        return False
    
    # Validar tabla RV.Positions
    print(f"\n\n📊 Validando tabla RV.Positions...")
    df_positions = get_supabase_data("RV.Positions")
    if df_positions is not None and not df_positions.empty:
        print(f"✅ Tabla RV.Positions encontrada")
        print(f"   Registros: {len(df_positions)}")
        print(f"   Columnas: {df_positions.columns.tolist()}")
        print(f"\n   Primeros registros:")
        print(df_positions.head(3).to_string())
    else:
        print(f"❌ No se pudo leer tabla RV.Positions")
        return False
    
    print(f"\n{'='*70}")
    print("✅ VALIDACIÓN COMPLETADA - TODO CORRECTO")
    print(f"{'='*70}\n")
    return True


def compute_historical_var(prices, nominal, confidence=0.95):
    """
    prices: array-like de precios históricos ordenados cronológicamente (antiguo...reciente).
    nominal: cantidad del instrumento (positivo).
    confidence: nivel de confianza (e.g. 0.95 para VaR 95%).
    Retorna: dict con shocks, precios simulados, up (P&L), VaR (positivo, en la misma unidad que MtM).
    """
    prices = np.asarray(prices, dtype=float)
    if prices.size < 2:
        raise ValueError("Se requieren al menos 2 precios históricos.")
    # shocks = Precio_t / Precio_{t-1}  -> hay N-1 shocks si hay N precios históricos
    shocks = prices[1:] / prices[:-1]
    # precio base = precio en la fecha de cálculo (último precio en la serie)
    base_price = prices[-1]
    # aplicar cada shock al precio base para obtener precios simulados
    simulated_prices = base_price * shocks
    # MtM base y MtM simulados
    mtm_base = nominal * base_price
    mtm_sim = nominal * simulated_prices
    # UP = MtM_simulado - MtM_base
    up = mtm_sim - mtm_base
    # VaR: tomar el percentil de pérdidas. Convención: VaR positivo = pérdida esperada en el percentil extremo.
    alpha = confidence
    tail_pct = (1 - alpha) * 100  # e.g. 5 para alpha=0.95
    # percentil de UP (P&L). Las pérdidas son valores negativos en UP, por eso VaR = -percentil.
    pct_value = np.percentile(up, tail_pct)
    var = -pct_value
    return {
        "base_price": base_price,
        "shocks": shocks,
        "simulated_prices": simulated_prices,
        "mtm_base": mtm_base,
        "mtm_sim": mtm_sim,
        "up": up,
        "confidence": confidence,
        "var": var,
        "percentile_value": pct_value,
        "tail_pct": tail_pct
    }

if __name__ == "__main__":
    # Verificar si se solicita validación
    if len(sys.argv) > 1 and sys.argv[1].lower() == "validate":
        validate_supabase_connection()
        sys.exit(0)
    
    # Parámetros
    fecha_analisis = sys.argv[1] if len(sys.argv) > 1 else None
    activo = sys.argv[2] if len(sys.argv) > 2 else "AAPL"
    confidence = float(sys.argv[3]) if len(sys.argv) > 3 else 0.95

    try:
        # Obtener datos de Supabase
        print("📡 Conectando a Supabase...")
        df_port = get_supabase_data("RV.Positions")
        df_precios = get_supabase_data("RV.Price")
        
        if df_port is None or df_precios is None:
            print("Error: No se pudieron obtener datos de Supabase")
            sys.exit(1)
        
        print(f"✓ Datos cargados desde Supabase")
        print(f"  - RV.Positions: {len(df_port)} registros, columnas: {df_port.columns.tolist()}")
        print(f"  - RV.Price: {len(df_precios)} registros, columnas: {df_precios.columns.tolist()}\n")
        
        # Usar nombres de columnas confirmados por el usuario
        fecha_col = 'Fecha'
        nemo_col = 'Nemonico'
        nominal_col = 'Nominal'
        precio_col = 'Precio'

        # Validar que las columnas existan
        missing = []
        for dfname, df, cols in [("RV.Positions", df_port, [fecha_col, nemo_col, nominal_col]),
                                 ("RV.Price", df_precios, [fecha_col, nemo_col, precio_col])]:
            for c in cols:
                if c not in df.columns:
                    missing.append((dfname, c))
        if missing:
            print("❌ Error: Faltan columnas esperadas en Supabase:")
            for tab, col in missing:
                print(f"   - Tabla {tab}: columna '{col}' no encontrada")
            print("   Columnas RV.Positions:", df_port.columns.tolist())
            print("   Columnas RV.Price:", df_precios.columns.tolist())
            sys.exit(1)

        # Convertir fechas a datetime (Supabase las provee como ISO date)
        df_port[fecha_col] = pd.to_datetime(df_port[fecha_col], errors='coerce')
        df_precios[fecha_col] = pd.to_datetime(df_precios[fecha_col], errors='coerce')
        if df_port[fecha_col].isna().any() or df_precios[fecha_col].isna().any():
            print("❌ Error: Algunas filas tienen fechas inválidas tras la conversión. Revisa el formato de 'Fecha'.")
            sys.exit(1)

        # Convertir Precio a numérico en RV.Price
        df_precios[precio_col] = pd.to_numeric(df_precios[precio_col], errors='coerce')
        if df_precios[precio_col].isna().all():
            print("❌ Error: la columna 'Precio' no pudo convertirse a numérico (valores NaN).")
            sys.exit(1)
        # Eliminar filas de precio sin valor numérico
        df_precios = df_precios.dropna(subset=[precio_col])
        
        print(f"✓ Datos cargados desde Supabase")
        print(f"  - RV.Positions: {len(df_port)} registros")
        print(f"  - RV.Price: {len(df_precios)} registros")
        print(f"  - Columnas RV.Positions: {df_port.columns.tolist()}")
        print(f"  - Columnas RV.Price: {df_precios.columns.tolist()}\n")
        
        # si no se especifica fecha, usar la última del portafolio
        if fecha_analisis is None:
            fecha_analisis = df_port[fecha_col].max()
            print(f"ℹ Fecha no especificada. Usando fecha máxima del portafolio: {fecha_analisis.strftime('%d/%m/%Y')}\n")
        else:
            try:
                fecha_analisis = pd.to_datetime(fecha_analisis, format="%d/%m/%Y")
            except:
                print(f"Error: Formato de fecha inválido. Use DD/MM/YYYY")
                sys.exit(1)
        
        # obtener nominal del portafolio para la fecha y activo especificados
        # Intentar con Nemonico (según imagen de Supabase)
        nemo_col = None
        for col in df_port.columns:
            if col.lower() in ['nemonico', 'nemo', 'symbol']:
                nemo_col = col
                break
        
        if nemo_col is None:
            print(f"❌ Error: No se encontró columna de nemónico en RV.Positions")
            print(f"   Columnas disponibles: {df_port.columns.tolist()}")
            sys.exit(1)
        
        nominal_col = None
        for col in df_port.columns:
            if col.lower() in ['nominal', 'posicion', 'position']:
                nominal_col = col
                break
        
        if nominal_col is None:
            print(f"❌ Error: No se encontró columna de nominal en RV.Positions")
            print(f"   Columnas disponibles: {df_port.columns.tolist()}")
            sys.exit(1)
        
        port_activo = df_port[(df_port[fecha_col] == fecha_analisis) & (df_port[nemo_col] == activo)]
        if port_activo.empty:
            # Mostrar activos disponibles en esa fecha
            activos_disponibles = df_port[df_port[fecha_col] == fecha_analisis][nemo_col].unique().tolist()
            print(f"Error: No hay posición para {activo} en la fecha {fecha_analisis.strftime('%d/%m/%Y')}")
            print(f"Activos disponibles en esa fecha: {', '.join(activos_disponibles)}")
            sys.exit(1)
        
        nominal = port_activo[nominal_col].iloc[0]
        
        # obtener precios históricos hasta la fecha de análisis, ordenados cronológicamente
        precio_col = None
        for col in df_precios.columns:
            if col.lower() in ['precio', 'price']:
                precio_col = col
                break
        
        if precio_col is None:
            print(f"❌ Error: No se encontró columna de precio en RV.Price")
            print(f"   Columnas disponibles: {df_precios.columns.tolist()}")
            sys.exit(1)
        
        df_precios_filtrado = df_precios[(df_precios[fecha_col] <= fecha_analisis) & 
                                          (df_precios[nemo_col] == activo)].copy()
        df_precios_filtrado = df_precios_filtrado.sort_values(fecha_col)
        
        if df_precios_filtrado.empty:
            print(f"Error: No hay datos de precios para {activo} hasta {fecha_analisis.strftime('%d/%m/%Y')}")
            sys.exit(1)
        
        prices = df_precios_filtrado[precio_col].values
        
        if len(prices) < 2:
            print(f"Error: Se requieren al menos 2 precios históricos para {activo}")
            sys.exit(1)

        # calcular VaR
        res = compute_historical_var(prices, nominal, confidence)
        
        # mostrar resultados
        print(f"\n{'='*70}")
        print(f"VaR - Simulación Histórica (Datos desde Supabase - RV.Positions + RV.Price)")
        print(f"{'='*70}")
        print(f"Activo: {activo}")
        print(f"Fecha de análisis: {fecha_analisis.strftime('%d/%m/%Y')}")
        print(f"Nominal (posición): {nominal:.0f} unidades")
        print(f"Confianza: {int(confidence*100)}%")
        print(f"Rango de precios: {df_precios_filtrado[fecha_col].min().strftime('%d/%m/%Y')} a {df_precios_filtrado[fecha_col].max().strftime('%d/%m/%Y')}")
        print(f"Número de precios históricos: {len(prices)}")
        print(f"Número de shocks: {len(res['shocks'])}")
        print(f"-"*70)
        print(f"Precio base (última fecha): ${res['base_price']:.2f}")
        print(f"MtM base: ${res['mtm_base']:.2f}")
        print(f"VaR ({int(confidence*100)}%): ${res['var']:.2f}")
        print(f"Percentil de UP: ${res['percentile_value']:.2f}")
        print(f"{'='*70}\n")
        
        # guardar resultados detallados
        out_df = pd.DataFrame({
            "shock": res["shocks"],
            "simulated_price": res["simulated_prices"],
            "mtm_sim": res["mtm_sim"],
            "up": res["up"]
        })
        out_df.to_csv("historical_var_simulations.csv", index=False)
        print("✓ Simulaciones guardadas en historical_var_simulations.csv")
        
    except FileNotFoundError as e:
        print(f"Error: Archivo no encontrado - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print(f"\nUso: python 'VaR RV.py' [fecha] [activo] [confianza]")
    print(f"     python 'VaR RV.py' 2/01/2024 AAPL 0.95")
    print(f"\nValidar conexión: python 'VaR RV.py' validate")