import pandas as pd
import numpy as np
from pathlib import Path

print("==========================================================")
print("=== FASE 3: MOTOR DE SIMULACIÓN DE MARGEN OPERATIVO    ===")
print("=== REFERENCIA: PORTAL DE VENDEDORES MERCADO LIBRE     ===")
print("==========================================================")

# Configuración de rutas relativas reproducibles
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# 1. Cargar dataset limpio y deduplicado 
input_file = DATA_DIR / 'simulador_meli_limpio.csv'
if not input_file.exists():
    input_file = BASE_DIR / 'simulador_meli_limpio.csv'

try:
    df = pd.read_csv(input_file)
    print(f"Dataset cargado exitosamente: {input_file} ({len(df)} registros)")
except FileNotFoundError:
    print(f"Error: No se encontró '{input_file}'. Ejecutá primero el Script 02.")
    exit(1)

# 2. Matriz de Tarifas de Referencia (Portal Vendedores Mercado Libre Argentina)
# Nota metodológica: Esquema simulado basado en costos base de plataforma.
# No contempla retenciones impositivas individuales, pauta en Mercado Ads ni logística inversa.

def calcular_comision_meli(row):
    precio = row['PrecioVentaARS']
    cuotas = row['CuotasSinInteres']
    
    # Comisiones de referencia: Clásica 14.5%, Premium 29.5% (con cuotas sin interés)
    pct_comision = 0.295 if cuotas == 1 else 0.145
    comision_variable = precio * pct_comision
    
    # Cargo fijo por unidad vendida en publicaciones menores a $30.000 ARS
    costo_fijo = 1100.0 if precio < 30000 else 0.0
    
    return round(comision_variable + costo_fijo, 2)

def calcular_envio_vendedor(row):
    precio = row['PrecioVentaARS']
    envio_gratis = row['EnvioGratis']
    categoria = row['Categoria']
    
    # Tarifas estimadas de Mercado Envíos obligatorias para publicaciones >= $30.000 ARS con Envío Gratis
    if precio >= 30000 and envio_gratis == 1:
        if categoria in ['Soportes para Notebook', 'Teclados Mecánicos', 'Parlantes Bluetooth']:
            return 4800.0  # Estimación para productos de mayor peso/volumen
        else:
            return 3800.0  # Estimación para accesorios compactos
    return 0.0

# Aplicar comisiones y envíos simulados
df['ComisionMELI_ARS'] = df.apply(calcular_comision_meli, axis=1)
df['CostoEnvioVendedorARS'] = df.apply(calcular_envio_vendedor, axis=1)

# Costo estimado de adquisición mayorista (FOB / reposición) calibrado por categoría
costo_fob_ratio = {
    'Soportes para Notebook': 0.35,
    'Teclados Mecánicos': 0.38,
    'Auriculares Inalámbricos': 0.32,
    'Smartwatches': 0.35,
    'Parlantes Bluetooth': 0.36,
    'Powerbanks': 0.34,
    'Cargadores de Pared': 0.30,
    'Cables USB': 0.25
}

df['CostoEstimadoCompra_FOB'] = round(df['PrecioVentaARS'] * df['Categoria'].map(costo_fob_ratio), 2)

# 3. Cálculo de Márgenes Operativos Estimados de la Simulación
# GananciaNetaARS representa el saldo operativo estimado por venta antes de impuestos y publicidad
df['GananciaNetaARS'] = round(
    df['PrecioVentaARS'] - df['ComisionMELI_ARS'] - df['CostoEnvioVendedorARS'] - df['CostoEstimadoCompra_FOB'], 
    2
)
df['MargenNetoPct'] = round((df['GananciaNetaARS'] / df['PrecioVentaARS']) * 100, 1)
df['ROIPct'] = round((df['GananciaNetaARS'] / df['CostoEstimadoCompra_FOB']) * 100, 1)

# 4. Resumen Ejecutivo por Categoría
resumen_cat = df.groupby('Categoria').agg(
    Publicaciones=('id_producto', 'count'),
    TicketMedianoARS=('PrecioVentaARS', 'median'),
    ComisionMedianaARS=('ComisionMELI_ARS', 'median'),
    CostoFOB_MedianoARS=('CostoEstimadoCompra_FOB', 'median'),
    GananciaEstimadaMedianaARS=('GananciaNetaARS', 'median'),
    MargenEstimadoMedianoPct=('MargenNetoPct', 'median'),
    ROI_EstimadoMedianoPct=('ROIPct', 'median')
).reset_index().sort_values(by='MargenEstimadoMedianoPct', ascending=False)

print("\n--- RESUMEN EJECUTIVO: MARGEN OPERATIVO ESTIMADO POR CATEGORÍA ---")
print(resumen_cat.to_string(index=False))

# 5. Exportar dataset final consolidado para Power BI (exactamente 2.599 publicaciones)
output_final = BASE_DIR / 'simulador_meli_dataset_final.csv'
df.to_csv(output_final, index=False)

print("\n==========================================================")
print("SIMULACIÓN COMPLETADA CON ÉXITO:")
print(f"   - Total publicaciones analizadas: {len(df)}")
print(f"   - Archivo final generado para Power BI: {output_final}")
print("==========================================================")
