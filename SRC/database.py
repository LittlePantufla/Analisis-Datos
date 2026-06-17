"""
Módulo de conexión a la base de datos Supabase (PostgreSQL).
Proyecto: Optimización del Análisis de Datos
Integrantes: Joaquín Martí, Joaquín Paredes, Daniel Ruiz
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


def get_engine():
    """
    Crea y retorna un engine de SQLAlchemy para conexión a Supabase.
    
    Returns:
        sqlalchemy.engine.Engine: Engine de conexión a PostgreSQL
    """
    host = os.getenv('SUPABASE_DB_HOST')
    db = os.getenv('SUPABASE_DB_NAME', 'postgres')
    user = os.getenv('SUPABASE_DB_USER', 'postgres')
    password = os.getenv('SUPABASE_DB_PASSWORD')
    port = os.getenv('SUPABASE_DB_PORT', '5432')
    
    if not password:
        raise ValueError("Falta SUPABASE_DB_PASSWORD en el archivo .env")
    
    url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return create_engine(url)


def load_table(table_name):
    """
    Carga una tabla completa desde Supabase a un DataFrame de Pandas.
    
    Args:
        table_name (str): Nombre de la tabla
        
    Returns:
        pd.DataFrame: Datos de la tabla
    """
    engine = get_engine()
    query = f"SELECT * FROM {table_name}"
    return pd.read_sql(query, engine)


def load_query(sql_query):
    """
    Ejecuta una consulta SQL personalizada y retorna los resultados.
    
    Args:
        sql_query (str): Consulta SQL
        
    Returns:
        pd.DataFrame: Resultados de la consulta
    """
    engine = get_engine()
    return pd.read_sql(text(sql_query), engine)


def load_all_tables():
    """
    Carga todas las tablas principales del proyecto.
    
    Returns:
        dict: Diccionario con DataFrames de cada tabla
    """
    tables = {
        'clientes': load_table('CLIENTES'),
        'productos': load_table('PRODUCTOS'),
        'proveedores': load_table('PROVEEDORES'),
        'tipo_producto': load_table('TIPOPRODUCTO'),
        'region': load_table('REGION'),
        'ciudad': load_table('CIUDAD'),
        'sucursales': load_table('SUCURSALES'),
        'vendedor': load_table('VENDEDOR'),
        'ventas_diarias': load_table('VENTASDIARIAS'),
        'ventas_vendedor': load_table('VENTASVENDEDOR'),
    }
    return tables


def load_ventas_completa():
    """
    Carga la vista de ventas completa con todos los joins.
    
    Returns:
        pd.DataFrame: Vista analítica completa
    """
    return load_table('vw_ventas_completa')


if __name__ == "__main__":
    print("Probando conexión a Supabase...")
    try:
        df = load_table('CLIENTES')
        print(f"✅ Conexión exitosa. Clientes cargados: {len(df)}")
        print(df.head(3))
    except Exception as e:
        print(f"❌ Error: {e}")