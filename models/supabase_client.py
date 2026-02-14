"""
Cliente para conexión con Supabase
Maneja todas las operaciones de lectura hacia las tablas
"""

import requests
import pandas as pd
from config import SUPABASE_API_URL, SUPABASE_KEY, TABLE_POSITIONS, TABLE_PRICE, COLUMNS


class SupabaseClient:
    """Cliente para interactuar con Supabase REST API"""
    
    def __init__(self, api_url=SUPABASE_API_URL, api_key=SUPABASE_KEY):
        self.api_url = api_url
        self.api_key = api_key
        self.headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def get_table_data(self, table_name):
        """
        Obtiene todos los datos de una tabla Supabase
        
        Args:
            table_name (str): Nombre de la tabla
        
        Returns:
            pd.DataFrame: DataFrame con los datos o DataFrame vacío si falla
        """
        from requests.utils import requote_uri
        
        url = requote_uri(f"{self.api_url}/{table_name}?select=*")
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    return pd.DataFrame()
                return pd.DataFrame(data)
            else:
                print(f"Error HTTP al leer {table_name}: {response.status_code}")
                print(response.text)
                return pd.DataFrame()
        except Exception as e:
            print(f"Excepción al conectar a Supabase: {e}")
            return pd.DataFrame()
    
    def get_positions(self):
        """Obtiene datos de posiciones"""
        return self.get_table_data(TABLE_POSITIONS)
    
    def get_prices(self):
        """Obtiene datos de precios"""
        return self.get_table_data(TABLE_PRICE)
    
    def validate_connection(self):
        """
        Valida la conexión a Supabase y la existencia de tablas
        
        Returns:
            dict: Resultado de validación con estado y detalles
        """
        result = {
            "connected": False,
            "positions_ok": False,
            "prices_ok": False,
            "messages": []
        }
        
        # Test connection
        try:
            url = requote_uri(f"{self.api_url}/{TABLE_PRICE}?limit=1")
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                result["connected"] = True
                result["messages"].append("✅ Conexión a Supabase exitosa")
            else:
                result["messages"].append(f"❌ Error HTTP: {response.status_code}")
                return result
        except Exception as e:
            result["messages"].append(f"❌ Error de conexión: {e}")
            return result
        
        # Validate tables
        df_positions = self.get_positions()
        df_prices = self.get_prices()
        
        if df_positions is not None and not df_positions.empty:
            result["positions_ok"] = True
            result["messages"].append(
                f"✅ Tabla {TABLE_POSITIONS}: {len(df_positions)} registros, "
                f"columnas: {df_positions.columns.tolist()}"
            )
        else:
            result["messages"].append(f"❌ Error al leer tabla {TABLE_POSITIONS}")
        
        if df_prices is not None and not df_prices.empty:
            result["prices_ok"] = True
            result["messages"].append(
                f"✅ Tabla {TABLE_PRICE}: {len(df_prices)} registros, "
                f"columnas: {df_prices.columns.tolist()}"
            )
        else:
            result["messages"].append(f"❌ Error al leer tabla {TABLE_PRICE}")
        
        return result


# Instancia global
supabase = SupabaseClient()
