import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

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

def extraer_precio_real(row):
    # En Mercado Libre, si el producto tiene descuento el precio final aparece
    # en andes-money-amount__fraction 2 y el precio tachado en fraction 1.
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

    if p1 is not None and p2 is not None:
        if p2 < p1 and p2 >= 500:
            return p2
        return p1

    if p1 is not None:
        return p1
    if p2 is not None:
        return p2

    return None

all_rows = []
discarded_rows = []
counter = 1

for file_name, category_name in files_map.items():
    file_path = RAW_DIR / file_name
    if not file_path.exists():
        file_path = BASE_DIR / file_name

    try:
        df = pd.read_csv(file_path)
        print(f"Procesando {file_name} ({category_name}) - {len(df)} filas...")
        
        for idx, row in df.iterrows():
            fila_csv = idx + 2
            
            title = row.get('poly-component__title', '')
            if pd.isna(title) or not str(title).strip():
                discarded_rows.append({
                    'Archivo': file_name,
                    'Fila_CSV': fila_csv,
                    'Motivo': 'Título vacío'
                })
                continue
            title = str(title).strip()
            
            price_ars = extraer_precio_real(row)
            if price_ars is None:
                discarded_rows.append({
                    'Archivo': file_name,
                    'Fila_CSV': fila_csv,
                    'Motivo': 'Sin precio válido'
                })
                continue
                
            seller_raw = row.get('poly-component__seller', '')
            seller = str(seller_raw).replace('Por ', '').replace('por ', '').strip() if pd.notna(seller_raw) and str(seller_raw).strip() != 'nan' else 'Vendedor Particular'
            
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
        print(f"Error al leer {file_name}: {e}")

df_final = pd.DataFrame(all_rows)
output_raw = DATA_DIR / 'simulador_meli_raw.csv'
df_final.to_csv(output_raw, index=False)

df_errores = pd.DataFrame(discarded_rows)
output_errores = DATA_DIR / 'errores_extraccion.csv'
df_errores.to_csv(output_errores, index=False)

print(f"\nIngesta completada: {len(df_final)} publicaciones válidas guardadas en {output_raw.name}")
print(f"Registros descartados: {len(df_errores)}")
