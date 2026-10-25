import pandas as pd
import glob
import re

print("==========================================================")
print("===           INGESTA Y REGISTRO DE ERRORES            ===")
print("==========================================================")

files_map = {
    'cat_1_soporte.csv': 'Soportes para Notebook',
    'cat_2_teclados.csv': 'Teclados Mecánicos',
    'cat_3_auriculares.csv': 'Auriculares Inalámbricos',
    'cat_4_smartwatch.csv': 'Smartwatches',
    'cat_5_parlantes.csv': 'Parlantes Bluetooth',
    'cat_6_powerbank.csv': 'Powerbanks',
    'cat_7_cargadores de pared.csv': 'Cargadores de Pared',
    'cat_8_cableUSB.csv': 'Cables USB'
}

all_rows = []
discarded_rows = []
counter = 1

def extraer_precio_real(row):
    """
    Extracción robusta de precios en Mercado Libre:
    - f1 (andes-money-amount__fraction): Precio de catálogo / lista.
    - f2 (andes-money-amount__fraction 2): Precio con descuento cuando existe oferta.
    - Evita falsos positivos con palabras como 'Office' o 'Official'.
    """
    f1_raw = row.get('andes-money-amount__fraction')
    f2_raw = row.get('andes-money-amount__fraction 2')

    def parse_num(v):
        if pd.isna(v):
            return None
        s = str(v).strip().replace('.', '').replace(',', '')
        try:
            p = int(s)
            return p if p > 0 else None
        except ValueError:
            return None

    p1 = parse_num(f1_raw)
    p2 = parse_num(f2_raw)

    # Si existen ambos precios: si p2 es menor que p1 (oferta), tomar p2
    if p1 is not None and p2 is not None:
        if p2 < p1 and p2 >= 500:
            return p2
        return p1

    if p1 is not None:
        return p1
    if p2 is not None:
        return p2

    return None

for file_path, category_name in files_map.items():
    try:
        df = pd.read_csv(file_path)
        print(f"\nProcesando: {file_path} ({category_name}) - {len(df)} filas crudas...")
        
        for idx, row in df.iterrows():
            numero_fila_csv = idx + 2  # Fila considerando el encabezado
            
            # 1. Validación de Título
            title = row.get('poly-component__title', '')
            if pd.isna(title) or not str(title).strip():
                error_info = {
                    'Archivo': file_path,
                    'Fila_CSV': numero_fila_csv,
                    'Motivo': 'Título faltante o vacío',
                    'Detalle': 'Columna poly-component__title sin datos'
                }
                discarded_rows.append(error_info)
                print(f"  [ERROR] Fila {numero_fila_csv} en {file_path}: Título vacío. Fila descartada.")
                continue
                
            title = str(title).strip()
            
            # 2. Validación de Precio Real
            price_ars = extraer_precio_real(row)
            if price_ars is None:
                error_info = {
                    'Archivo': file_path,
                    'Fila_CSV': numero_fila_csv,
                    'Motivo': 'Precio no numérico o ausente',
                    'Detalle': f"Título: {title[:45]}..."
                }
                discarded_rows.append(error_info)
                print(f"  [ERROR] Fila {numero_fila_csv} en {file_path}: Sin precio válido ('{title[:30]}...').")
                continue
                
            # 3. Extracción de Vendedor
            seller_raw = row.get('poly-component__seller', '')
            seller = str(seller_raw).replace('Por ', '').replace('por ', '').strip() if pd.notna(seller_raw) and str(seller_raw).strip() != 'nan' else 'Vendedor Particular'
            
            # 4. Detección de Badges Comerciales
            row_text = ' '.join([str(v) for v in row.values if pd.notna(v)]).lower()
            es_full = 1 if ('full' in row_text or 'llega mañana' in row_text) else 0
            envio_gratis = 1 if 'gratis' in row_text else 0
            cuotas_sin_interes = 1 if ('cuotas sin interés' in row_text or 'mismo precio' in row_text or 'sin interés' in row_text) else 0
            
            all_rows.append({
                'id_sustituto': f"SIM-MELI-{counter:04d}",
                'Categoria': category_name,
                'Titulo': title,
                'PrecioVentaARS': price_ars,
                'Vendedor': seller,
                'EsFull': es_full,
                'EnvioGratis': envio_gratis,
                'CuotasSinInteres': cuotas_sin_interes
            })
            counter += 1
            
    except Exception as e:
        print(f"[ERROR CRITICO] No se pudo leer {file_path}: {e}")

# Exportar dataset limpio
df_final = pd.DataFrame(all_rows)
output_clean = 'simulador_meli_raw.csv'
df_final.to_csv(output_clean, index=False)

# Exportar log de errores
df_errores = pd.DataFrame(discarded_rows)
output_errores = 'errores_extraccion.csv'
df_errores.to_csv(output_errores, index=False)

print("\n==========================================================")
print(f"INGESTA FINALIZADA CON EXITO:")
print(f"   - Registros válidos procesados: {len(df_final)}")
print(f"   - Registros descartados con error: {len(df_errores)}")
print(f"   - Archivo consolidado generado: {output_clean}")
print(f"   - Log de errores generado: {output_errores}")
print("==========================================================")