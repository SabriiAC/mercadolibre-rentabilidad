import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

input_file = DATA_DIR / 'simulador_meli_raw.csv'
if not input_file.exists():
    input_file = BASE_DIR / 'simulador_meli_raw.csv'

df = pd.read_csv(input_file)
filas_iniciales = len(df)

# Corrección de escala de miles: algunos precios scrapeados con coma/punto
# quedaron truncados (por ejemplo $68.000 quedó como 68). Si es menor a 800,
# se multiplica por 1.000 para recuperar el valor real en ARS.
def corregir_escala_precio(p):
    if pd.isna(p) or p <= 0:
        return np.nan
    p_int = int(p)
    return p_int * 1000 if p_int < 800 else p_int

df['PrecioVentaARS'] = df['PrecioVentaARS'].apply(corregir_escala_precio)
df = df.dropna(subset=['PrecioVentaARS'])
df['PrecioVentaARS'] = df['PrecioVentaARS'].astype(int)

# Al raspar varias páginas del catálogo se repiten registros.
# Deduplicamos por categoría y título exacto.
df_limpio = df.drop_duplicates(subset=['Categoria', 'Titulo']).copy()
duplicados = filas_iniciales - len(df_limpio)

# Clasificación de vendedor: separa las publicaciones que tienen una marca o nombre
# informado frente a las que no tienen datos visibles ('Vendedor Particular').
df_limpio['Vendedor'] = df_limpio['Vendedor'].fillna('Vendedor Particular').astype(str).str.strip()
df_limpio['EsTiendaOficial'] = df_limpio['Vendedor'].apply(
    lambda v: 0 if v.lower() in ['vendedor particular', 'particular', 'nan', ''] else 1
)

df_limpio = df_limpio.reset_index(drop=True)
df_limpio['id_producto'] = [f"MELI-{i+1:04d}" for i in range(len(df_limpio))]

columnas_ordenadas = [
    'id_producto',
    'Categoria',
    'Titulo',
    'PrecioVentaARS',
    'Vendedor',
    'EsTiendaOficial',
    'EsFull',
    'EnvioGratis',
    'CuotasSinInteres'
]
df_silver = df_limpio[columnas_ordenadas]

output_file = DATA_DIR / 'simulador_meli_limpio.csv'
df_silver.to_csv(output_file, index=False)

print(f"Limpieza completada:")
print(f"- Filas iniciales: {filas_iniciales}")
print(f"- Duplicados eliminados: {duplicados}")
print(f"- Publicaciones únicas: {len(df_silver)}")
print(f"\nDistribución por categoría:")
print(df_silver['Categoria'].value_counts().to_string())
