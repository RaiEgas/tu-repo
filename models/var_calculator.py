"""
Calculadora de VaR por Simulación Histórica
"""

import numpy as np
import pandas as pd


def compute_historical_var(prices, nominal, confidence=0.95):
    """
    Calcula VaR por simulación histórica
    
    Args:
        prices (array-like): Precios históricos ordenados cronológicamente (antiguo...reciente)
        nominal (float): Cantidad del instrumento (positivo)
        confidence (float): Nivel de confianza (e.g. 0.95 para VaR 95%)
    
    Returns:
        dict: Resultado con shocks, precios simulados, P&L, VaR, etc.
    
    Raises:
        ValueError: Si hay menos de 2 precios
    """
    prices = np.asarray(prices, dtype=float)
    
    if prices.size < 2:
        raise ValueError("Se requieren al menos 2 precios históricos.")
    
    # Calcular shocks (retornos): Precio_t / Precio_{t-1}
    shocks = prices[1:] / prices[:-1]
    
    # Precio base = último precio en la serie
    base_price = prices[-1]
    
    # Precios simulados aplicando cada shock al precio base
    simulated_prices = base_price * shocks
    
    # MtM (Mark-to-Market)
    mtm_base = nominal * base_price
    mtm_sim = nominal * simulated_prices
    
    # UP = P&L = MtM simulado - MtM base
    up = mtm_sim - mtm_base
    
    # VaR: percentil de pérdidas
    # Convención: VaR positivo = pérdida esperada en el percentil extremo
    alpha = confidence
    tail_pct = (1 - alpha) * 100  # e.g. 5 para alpha=0.95
    pct_value = np.percentile(up, tail_pct)
    var = -pct_value  # Negativo porque UP negativos son pérdidas
    
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


class VaRCalculator:
    """
    Calculadora integrada de VaR que obtiene datos de Supabase
    """
    
    def __init__(self, supabase_client):
        """
        Inicializa el calculador con un cliente Supabase
        
        Args:
            supabase_client: Instancia de SupabaseClient
        """
        self.supabase = supabase_client
    
    def calculate_for_position(self, fecha_analisis, activo, confidence=0.95):
        """
        Calcula VaR para una posición específica
        
        Args:
            fecha_analisis (str o datetime): Fecha de análisis (DD/MM/YYYY o datetime)
            activo (str): Código del activo (e.g. 'AAPL')
            confidence (float): Nivel de confianza (default 0.95)
        
        Returns:
            tuple: (resultado_dict, error_msg) - uno será None si no hay error
        """
        error = None
        
        # Obtener datos
        df_positions = self.supabase.get_positions()
        df_prices = self.supabase.get_prices()
        
        if df_positions.empty or df_prices.empty:
            return None, "Error: No se pudieron obtener datos de Supabase"
        
        # Convertir fechas
        df_positions["Fecha"] = pd.to_datetime(df_positions["Fecha"], errors='coerce')
        df_prices["Fecha"] = pd.to_datetime(df_prices["Fecha"], errors='coerce')
        
        # Parsear fecha de análisis
        if isinstance(fecha_analisis, str):
            try:
                fecha_dt = pd.to_datetime(fecha_analisis, format="%d/%m/%Y")
            except:
                try:
                    fecha_dt = pd.to_datetime(fecha_analisis)
                except:
                    return None, "Formato de fecha inválido. Use DD/MM/YYYY o YYYY-MM-DD"
        else:
            fecha_dt = pd.to_datetime(fecha_analisis)
        
        # Obtener nominal del portafolio
        port_activo = df_positions[
            (df_positions["Fecha"] == fecha_dt) & 
            (df_positions["Nemonico"] == activo)
        ]
        
        if port_activo.empty:
            activos_disp = df_positions[df_positions["Fecha"] == fecha_dt]["Nemonico"].unique().tolist()
            msg = f"No hay posición para {activo} en {fecha_dt.strftime('%d/%m/%Y')}"
            if activos_disp:
                msg += f". Activos disponibles: {', '.join(activos_disp)}"
            return None, msg
        
        nominal = port_activo["Nominal"].iloc[0]
        
        # Obtener precios históricos hasta la fecha
        df_precios_filt = df_prices[
            (df_prices["Fecha"] <= fecha_dt) & 
            (df_prices["Nemonico"] == activo)
        ].copy()
        df_precios_filt = df_precios_filt.sort_values("Fecha")
        
        if df_precios_filt.empty or len(df_precios_filt) < 2:
            return None, f"No hay suficientes precios históricos para {activo}"
        
        # Convertir precios a numérico
        prices = pd.to_numeric(df_precios_filt["Precio"], errors='coerce').dropna().values
        
        if len(prices) < 2:
            return None, "Precios inválidos o insuficientes"
        
        # Calcular VaR
        try:
            res = compute_historical_var(prices, nominal, confidence)
        except Exception as e:
            return None, f"Error en cálculo: {str(e)}"
        
        # Envolver resultado con metadatos
        resultado = {
            "activo": activo,
            "fecha": fecha_dt.strftime("%d/%m/%Y"),
            "nominal": int(nominal),
            "confidence": confidence,
            "base_price": res["base_price"],
            "mtm_base": res["mtm_base"],
            "var": res["var"],
            "percentile_value": res["percentile_value"],
            "num_precios": len(prices),
            "num_shocks": len(res["shocks"]),
            "fecha_min": df_precios_filt["Fecha"].min().strftime("%d/%m/%Y"),
            "fecha_max": df_precios_filt["Fecha"].max().strftime("%d/%m/%Y"),
            # Datos para tabla
            "simulaciones": pd.DataFrame({
                "fecha": df_precios_filt["Fecha"].dt.strftime("%Y-%m-%d").values[1:],
                "shock": res["shocks"],
                "simulated_price": res["simulated_prices"],
                "mtm_sim": res["mtm_sim"],
                "up": res["up"]
            })
        }
        
        return resultado, None
