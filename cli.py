"""
Script CLI para calcular VaR por línea de comandos
Utiliza los modelos centralizados
"""

import sys
import argparse
from models.supabase_client import supabase
from models.var_calculator import VaRCalculator


def main():
    parser = argparse.ArgumentParser(
        description='VaR RV - Calculadora de Value at Risk por Simulación Histórica'
    )
    parser.add_argument('--validate', action='store_true', help='Validar conexión a Supabase')
    parser.add_argument('--fecha', type=str, help='Fecha de análisis (DD/MM/YYYY)', default=None)
    parser.add_argument('--activo', type=str, help='Código del activo', default='AAPL')
    parser.add_argument('--confianza', type=float, help='Nivel de confianza (0-1)', default=0.95)
    
    args = parser.parse_args()
    
    if args.validate:
        # Validar conexión
        print("="*70)
        print("VALIDACIÓN DE CONEXIÓN A SUPABASE")
        print("="*70)
        
        validation = supabase.validate_connection()
        
        for msg in validation['messages']:
            print(msg)
        
        print("="*70)
        if validation['connected'] and validation['positions_ok'] and validation['prices_ok']:
            print("✅ VALIDACIÓN EXITOSA")
        else:
            print("❌ VALIDACIÓN FALLIDA")
        print("="*70)
        
    else:
        # Calcular VaR
        print(f"📊 Calculando VaR...")
        
        calculator = VaRCalculator(supabase)
        res, error = calculator.calculate_for_position(args.fecha, args.activo, args.confianza)
        
        if error:
            print(f"❌ Error: {error}")
            sys.exit(1)
        
        # Mostrar resultados
        print(f"\n{'='*70}")
        print(f"VaR - Simulación Histórica")
        print(f"{'='*70}")
        print(f"Activo: {res['activo']}")
        print(f"Fecha de análisis: {res['fecha']}")
        print(f"Nominal (posición): {res['nominal']:.0f} unidades")
        print(f"Confianza: {int(res['confidence']*100)}%")
        print(f"Rango de precios: {res['fecha_min']} a {res['fecha_max']}")
        print(f"Número de precios históricos: {res['num_precios']}")
        print(f"Número de shocks: {res['num_shocks']}")
        print(f"-"*70)
        print(f"Precio base (última fecha): ${res['base_price']:.2f}")
        print(f"MtM base: ${res['mtm_base']:.2f}")
        print(f"VaR ({int(res['confidence']*100)}%): ${res['var']:.2f}")
        print(f"Percentil de UP: ${res['percentile_value']:.2f}")
        print(f"{'='*70}\n")
        
        # Guardar simulaciones
        res['simulaciones'].to_csv("historical_var_simulations.csv", index=False)
        print("✓ Simulaciones guardadas en historical_var_simulations.csv")


if __name__ == '__main__':
    main()
