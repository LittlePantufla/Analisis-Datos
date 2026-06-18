"""
Carga de datos normalizados a Supabase.
Lee los CSVs de Data/normalized/ y los sube con upsert (sin duplicados).

Proyecto: Optimización del Análisis de Datos
Integrantes: Joaquín Martí, Joaquín Paredes, Daniel Ruiz
"""

import os
import math
import numpy as np
import pandas as pd
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Busca el .env en la raíz del proyecto (un nivel arriba de SRC/)
load_dotenv(Path(__file__).parent.parent / '.venv/.env')

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ Faltan SUPABASE_URL o SUPABASE_KEY en el archivo .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

BASE_DIR = Path(__file__).parent.parent

# Orden respetando dependencias FK
# (las tablas base primero, las que tienen FK al final)
TABLAS = [
    ('region',         BASE_DIR / 'Data/normalized/region.csv'),
    ('tipoproducto',   BASE_DIR / 'Data/normalized/tipoproducto.csv'),
    ('proveedores',    BASE_DIR / 'Data/normalized/proveedores.csv'),
    ('vendedor',       BASE_DIR / 'Data/normalized/vendedor.csv'),
    ('ciudad',         BASE_DIR / 'Data/normalized/ciudad.csv'),
    ('sucursales',     BASE_DIR / 'Data/normalized/sucursales.csv'),
    ('productos',      BASE_DIR / 'Data/normalized/productos.csv'),
    ('clientes',       BASE_DIR / 'Data/normalized/clientes.csv'),
    ('ventasdiarias',  BASE_DIR / 'Data/normalized/ventasdiarias.csv'),
    ('ventasvendedor', BASE_DIR / 'Data/normalized/ventasvendedor.csv'),
]


def limpiar_valor(val):
    """
    Convierte un valor individual a tipo Python nativo compatible con JSON.
    NaN / inf / strings vacíos → None
    float sin decimales → int
    """
    # None directo
    if val is None:
        return None

    # Numpy entero → int Python
    if isinstance(val, np.integer):
        return int(val)

    # Numpy / Python float
    if isinstance(val, (float, np.floating)):
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        # Si es .0 convertir a int (ej: 412234541.0 → 412234541)
        if f.is_integer():
            return int(f)
        return f

    # Numpy bool → bool Python
    if isinstance(val, np.bool_):
        return bool(val)

    # String vacío o 'nan'
    if isinstance(val, str) and val.strip().lower() in ('nan', 'none', 'nat', '', '-'):
        return None

    return val


def preparar_df(df):
    """
    Convierte el DataFrame completo a lista de dicts listos para Supabase.
    """
    registros = []
    for _, row in df.iterrows():
        record = {col: limpiar_valor(row[col]) for col in df.columns}

        # Campo NOT NULL con default
        if 'observacion' in record and record['observacion'] is None:
            record['observacion'] = 'Sin observacion'

        registros.append(record)
    return registros


def subir_tabla(tabla, csv_path, batch_size=500):
    """
    Sube los datos de un CSV a Supabase usando upsert.
    upsert = inserta si no existe, actualiza si ya existe → nunca duplica.
    """
    if not os.path.exists(csv_path):
        print(f"  ⚠️  No encontrado: {csv_path}")
        return 0

    df = pd.read_csv(csv_path)
    registros = preparar_df(df)
    total = len(registros)
    subidos = 0

    for i in range(0, total, batch_size):
        batch = registros[i:i + batch_size]
        n_batch = i // batch_size + 1
        try:
            supabase.table(tabla).upsert(batch).execute()
            subidos += len(batch)
            print(f"  ✅ Batch {n_batch}: {len(batch)} registros")
        except Exception as e:
            print(f"  ❌ Error en batch {n_batch}: {e}")

    return subidos


if __name__ == "__main__":
    print("=" * 55)
    print("  CARGA DE DATOS A SUPABASE")
    print("=" * 55)

    total_global = 0

    for tabla, ruta in TABLAS:
        print(f"\n📤 Subiendo {tabla.upper()}...")
        n = subir_tabla(tabla, ruta)
        print(f"   Total: {n} registros en '{tabla}'")
        total_global += n

    print("\n" + "=" * 55)
    print(f"  ✅ Carga completada: {total_global} registros totales")
    print("=" * 55)