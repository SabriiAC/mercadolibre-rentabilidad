import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

input_file = DATA_DIR / 'simulador_meli_limpio.csv'
if not input_file.exists():
    input_file = BASE_DIR / 'simulador_meli_limpio.csv'

df = pd.read_csv(input_file)

# Comisiones oficiales de Mercado Libre Argentina:
# 14.5% para publicación Clásica y 29.5% para Premium (cuotas sin interés).
# En tickets menores a $30.000 se suma el cargo fijo de $1.100 por unidad.
def calcular_comision(row):
    precio = row['PrecioVentaARS']
    pct = 0.295 if row['CuotasSinInteres'] == 1 else 0.145
    cargo_fijo = 1100.0 if precio < 30000 else 0.0
    return round((precio * pct) + cargo_fijo, 2)

# Envío bonificado a cargo del vendedor para publicaciones con Envío Gratis >= $30.000.
# $4.800 para productos con mayor peso o bulto y $3.800 para accesorios chicos.
def calcular_envio(row):
    if row['PrecioVentaARS'] >= 30000 and row['EnvioGratis'] == 1:
        if row['Categoria'] in ['Soportes para Notebook', 'Teclados Mecánicos', 'Parlantes Bluetooth']:
            return 4800.0
        return 3800.0
    return 0.0

df['ComisionMELI_ARS'] = df.apply(calcular_comision, axis=1)
df['CostoEnvioVendedorARS'] = df.apply(calcular_envio, axis=1)

# Estimación de costo de adquisición mayorista / reposición por categoría (% del PVP).
costo_compra_ratio = {
    'Soportes para Notebook': 0.35,
    'Teclados Mecánicos': 0.38,
    'Auriculares Inalámbricos': 0.32,
    'Smartwatches': 0.35,
    'Parlantes Bluetooth': 0.36,
    'Powerbanks': 0.34,
    'Cargadores de Pared': 0.30,
    'Cables USB': 0.25
}

df['CostoEstimadoCompra_FOB'] = round(df['PrecioVentaARS'] * df['Categoria'].map(costo_compra_ratio), 2)

# Margen operativo estimado por unidad antes de impuestos directos y publicidad
df['GananciaNetaARS'] = round(
    df['PrecioVentaARS'] - df['ComisionMELI_ARS'] - df['CostoEnvioVendedorARS'] - df['CostoEstimadoCompra_FOB'],
    2
)
df['MargenNetoPct'] = round((df['GananciaNetaARS'] / df['PrecioVentaARS']) * 100, 1)
df['ROIPct'] = round((df['GananciaNetaARS'] / df['CostoEstimadoCompra_FOB']) * 100, 1)

resumen = df.groupby('Categoria').agg(
    Publicaciones=('id_producto', 'count'),
    TicketMediano=('PrecioVentaARS', 'median'),
    ComisionMediana=('ComisionMELI_ARS', 'median'),
    CostoCompraMediano=('CostoEstimadoCompra_FOB', 'median'),
    GananciaEstimadaMediana=('GananciaNetaARS', 'median'),
    MargenEstimadoMedianoPct=('MargenNetoPct', 'median'),
    ROI_MedianoPct=('ROIPct', 'median')
).reset_index().sort_values(by='MargenEstimadoMedianoPct', ascending=False)

print("Resumen de margen operativo estimado por categoría:")
print(resumen.to_string(index=False))

output_final = BASE_DIR / 'simulador_meli_dataset_final.csv'
df.to_csv(output_final, index=False)

print(f"\nArchivo final generado para Power BI: {output_final.name} ({len(df)} filas)")
