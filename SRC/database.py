"""
Módulo de conexión a Supabase (PostgreSQL) vía SQLAlchemy.
Permite leer tablas y ejecutar consultas personalizadas.

Proyecto: Optimización del Análisis de Datos
Integrantes: Joaquín Martí, Joaquín Paredes, Daniel Ruiz
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()


def get_engine():
    """
    Crea un engine SQLAlchemy para conectarse a Supabase (PostgreSQL).
    Las credenciales vienen del archivo .env
    """
    host     = os.getenv('SUPABASE_DB_HOST')
    db       = os.getenv('SUPABASE_DB_NAME', 'postgres')
    user     = os.getenv('SUPABASE_DB_USER', 'postgres')
    password = os.getenv('Hipopotamo09.')
    port     = os.getenv('SUPABASE_DB_PORT', '5432')

    if not host or not password:
        raise ValueError("Faltan SUPABASE_DB_HOST o SUPABASE_DB_PASSWORD en el .env")

    url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return create_engine(url)


def load_table(table_name):
    """Carga una tabla completa como DataFrame."""
    engine = get_engine()
    # Comillas dobles para respetar el nombre exacto en PostgreSQL
    query = f'SELECT * FROM "{table_name}"'
    return pd.read_sql(query, engine)


def load_query(sql_query):
    """Ejecuta una consulta SQL personalizada y retorna los resultados."""
    engine = get_engine()
    return pd.read_sql(text(sql_query), engine)


def load_all_tables():
    """
    Carga todas las tablas del proyecto.
    Retorna un diccionario {nombre: DataFrame}.
    """
    # Nombres en minúsculas — así quedaron creadas en Supabase
    nombres = [
        'region',
        'tipoproducto',
        'proveedores',
        'vendedor',
        'ciudad',
        'sucursales',
        'productos',
        'clientes',
        'ventasdiarias',
        'ventasvendedor',
    ]

    tablas = {}
    for nombre in nombres:
        try:
            tablas[nombre] = load_table(nombre)
            print(f"  ✅ {nombre:<20} {len(tablas[nombre]):>6} registros")
        except Exception as e:
            print(f"  ❌ {nombre:<20} Error: {e}")
            tablas[nombre] = None

    return tablas


def load_ventas_completa():
    """
    Carga la vista analítica completa de ventas con todos los joins.
    Requiere que la vista 'vw_ventas_completa' exista en Supabase.
    """
    return load_table('vw_ventas_completa')


if __name__ == "__main__":
    print("=" * 55)
    print("  PROBANDO CONEXIÓN A SUPABASE")
    print("=" * 55 + "\n")

    try:
        tablas = load_all_tables()
        print("\n✅ Conexión exitosa.\n")

        # Mostrar muestra de clientes
        if tablas.get('clientes') is not None:
            print("Muestra de CLIENTES:")
            print(tablas['clientes'].head(3).to_string(index=False))

    except Exception as e:
        print(f"\n❌ Error de conexión: {e}")
        print("\nVerifica tu archivo .env:")
        print("  SUPABASE_DB_HOST=db.xxxx.supabase.co")
        print("  SUPABASE_DB_PASSWORD=tu_password")
        print("  SUPABASE_DB_NAME=postgres")
        print("  SUPABASE_DB_USER=postgres")
        print("  SUPABASE_DB_PORT=5432")