import pandas as pd
import numpy as np

print("==========================================================")
print("=== FASE 3: MOTOR DE CÁLCULO DE RENTABILIDAD Y MARGEN  ===")
print("=== FUENTE: PORTAL OFICIAL VENDEDORES MERCADO LIBRE    ===")
print("=== URL: vendedores.mercadolibre.com.ar/ayuda/870      ===")
print("==========================================================")

# 1. Cargar dataset limpio y deduplicado 
df = pd.read_csv('simulador_meli_limpio.csv')

# 2. Matriz de Tarifas Oficial de Mercado Libre Argentina (Portal Oficial Vendedores #870)
def calcular_comision_meli_oficial(row):
    precio = row['PrecioVentaARS']
    cuotas = row['CuotasSinInteres']
    
    # Comisiones oficiales: Clásica 14.5%, Premium 29.5% (con cuotas sin interés)
    pct_comision = 0.295 if cuotas == 1 else 0.145
    comision_variable = precio * pct_comision
    
    # Costo fijo adicional por unidad vendida para productos menores a $30.000 ARS
    costo_fijo = 1100.0 if precio < 30000 else 0.0
    
    return round(comision_variable + costo_fijo, 2)

def calcular_envio_vendedor_oficial(row):
    precio = row['PrecioVentaARS']
    envio_gratis = row['EnvioGratis']
    categoria = row['Categoria']
    
    # Tarifas bonificadas de Mercado Envíos para productos >= $30.000 ARS con Envío Gratis
    if precio >= 30000 and envio_gratis == 1:
        if categoria in ['Soportes para Notebook', 'Teclados Mecánicos', 'Parlantes Bluetooth']:
            return 4800.0  # Productos de mayor volumen/peso
        else:
            return 3800.0  # Productos livianos y compactos
    return 0.0

# Aplicar comisiones y envíos
df['ComisionMELI_ARS'] = df.apply(calcular_comision_meli_oficial, axis=1)
df['CostoEnvioVendedorARS'] = df.apply(calcular_envio_vendedor_oficial, axis=1)

# Costo FOB estimado de adquisición/importación calibrado por categoría
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

# 3. Cálculo de Márgenes Financieros & Rentabilidad Neta
df['GananciaNetaARS'] = round(df['PrecioVentaARS'] - df['ComisionMELI_ARS'] - df['CostoEnvioVendedorARS'] - df['CostoEstimadoCompra_FOB'], 2)
df['MargenNetoPct'] = round((df['GananciaNetaARS'] / df['PrecioVentaARS']) * 100, 1)
df['ROIPct'] = round((df['GananciaNetaARS'] / df['CostoEstimadoCompra_FOB']) * 100, 1)

# 4. Resumen Ejecutivo por Categoría
resumen_cat = df.groupby('Categoria').agg(
    Publicaciones=('id_producto', 'count'),
    TicketMedianoARS=('PrecioVentaARS', 'median'),
    ComisionMedianaARS=('ComisionMELI_ARS', 'median'),
    CostoFOB_MedianoARS=('CostoEstimadoCompra_FOB', 'median'),
    GananciaNetaMedianaARS=('GananciaNetaARS', 'median'),
    MargenNetoMedianoPct=('MargenNetoPct', 'median'),
    ROI_MedianoPct=('ROIPct', 'median')
).reset_index().sort_values(by='MargenNetoMedianoPct', ascending=False)

print("\n--- RESUMEN EJECUTIVO: RENTABILIDAD CON COSTOS OFICIALES MERCADO LIBRE ---")
print(resumen_cat.to_string(index=False))

# 5. Guardar dataset final para Power BI
output_final = 'simulador_meli_dataset_final.csv'
df.to_csv(output_final, index=False)

print("\n==========================================================")
print("MODELADO DEL SIMULADOR COMPLETADO:")
print(f"   - Total publicaciones analizadas: {len(df)}")
print(f"   - Archivo final generado para Power BI: {output_final}")
print("==========================================================")