import pandas as pd
import numpy as np

print("==========================================================")
print("=== FASE 2: LIMPIEZA, CALIDAD Y NORMALIZACIÓN (SILVER) ===")
print("==========================================================")

# 1. Carga del dataset crudo unificado 
input_file = 'simulador_meli_raw.csv'
try:
    df = pd.read_csv(input_file)
    print(f"Archivo cargado exitosamente: {input_file} ({len(df)} registros)")
except FileNotFoundError:
    print(f"Error: No se encontró el archivo '{input_file}'. Ejecutá primero el Script 01.")
    exit()

# 2. Control de Calidad de Precios 
# Corrige pérdidas de escala de miles provenientes de parseos flotantes previos 
def normalizar_escala_precio(p):
    if pd.isna(p) or p <= 0:
        return np.nan
    p_int = int(p)
    if p_int < 800:
        return p_int * 1000  
    return p_int

df['PrecioVentaARS'] = df['PrecioVentaARS'].apply(normalizar_escala_precio)
df = df.dropna(subset=['PrecioVentaARS'])
df['PrecioVentaARS'] = df['PrecioVentaARS'].astype(int)

# 3. Deduplicación por Paginación de Scraping
filas_iniciales = len(df)
df_limpio = df.drop_duplicates(subset=['Categoria', 'Titulo']).copy()
duplicados_removidos = filas_iniciales - len(df_limpio)

# 4. Creación de Banderas de Negocio y Clasificación de Vendedor
df_limpio['Vendedor'] = df_limpio['Vendedor'].fillna('Vendedor Particular').astype(str).str.strip()
df_limpio['EsTiendaOficial'] = df_limpio['Vendedor'].apply(
    lambda v: 0 if v.lower() in ['vendedor particular', 'particular', 'nan', ''] else 1
)

# 5. Generación de Claves Primarias y Estructura Definitiva
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

# 6. Exportación 
output_file = 'simulador_meli_limpio.csv'
df_silver.to_csv(output_file, index=False)

print("\n================ RESUMEN DE CONTROL DE CALIDAD ================")
print(f" • Registros crudos procesados:        {filas_iniciales}")
print(f" • Publicaciones duplicadas removidas: {duplicados_removidos}")
print(f" • Publicaciones únicas consolidadas:  {len(df_silver)}")
print(f" • Archivo limpio generado:            {output_file}")
print("================================================================\n")

print("Distribución de catálogo único por categoría:")
print(df_silver['Categoria'].value_counts().to_string())