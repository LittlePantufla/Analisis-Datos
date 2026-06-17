"""
Carga de datos normalizados a Supabase.
Lee los CSVs de Data/normalized/ y los sube con upsert (sin duplicados).

Proyecto: Optimización del Análisis de Datos
Integrantes: Joaquín Martí, Joaquín Paredes, Daniel Ruiz
"""

import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent / 'SRC/.env')
 
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ Faltan SUPABASE_URL o SUPABASE_KEY en el archivo .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Orden respetando dependencias FK
# (las tablas base primero, las que tienen FK al final)
TABLAS = [
    ('region',         'Data/normalized/region.csv'),
    ('tipoproducto',   'Data/normalized/tipoproducto.csv'),
    ('proveedores',    'Data/normalized/proveedores.csv'),
    ('vendedor',       'Data/normalized/vendedor.csv'),
    ('ciudad',         'Data/normalized/ciudad.csv'),
    ('sucursales',     'Data/normalized/sucursales.csv'),
    ('productos',      'Data/normalized/productos.csv'),
    ('clientes',       'Data/normalized/clientes.csv'),
    ('ventasdiarias',  'Data/normalized/ventasdiarias.csv'),
    ('ventasvendedor', 'Data/normalized/ventasvendedor.csv'),
]


def preparar_df(df):
    """
    Convierte el DataFrame para que Supabase lo acepte:
    - NaN → None (JSON null)
    - Números con decimales .0 → enteros donde corresponde
    """
    df = df.where(pd.notnull(df), None)

    for col in df.columns:
        if df[col].dtype == 'float64':
            # Si todos los valores son enteros (ej: 1.0, 2.0), convertir a int
            no_nulos = df[col].dropna()
            if (no_nulos == no_nulos.astype('int64')).all():
                df[col] = df[col].apply(lambda x: int(x) if x is not None else None)

    return df


def subir_tabla(tabla, csv_path, batch_size=500):
    """
    Sube los datos de un CSV a Supabase usando upsert.
    upsert = inserta si no existe, actualiza si ya existe → nunca duplica.
    """
    if not os.path.exists(csv_path):
        print(f"  ⚠️  No encontrado: {csv_path}")
        return 0

    df = pd.read_csv(csv_path)
    df = preparar_df(df)
    registros = df.to_dict('records')
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