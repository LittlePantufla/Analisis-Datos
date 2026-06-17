"""
Módulo de limpieza y preprocesamiento de datos.
Proyecto: Optimización del Análisis de Datos
Integrantes: Joaquín Martí, Joaquín Paredes, Daniel Ruiz
"""

import pandas as pd
import numpy as np


def trim_text_columns(df, columns=None):
    """
    Elimina espacios en blanco al inicio y final de columnas de texto.
    """
    df = df.copy()
    if columns is None:
        columns = df.select_dtypes(include=['object']).columns
    
    for col in columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace(['nan', 'None', 'NaN', ''], np.nan)
    
    return df


def normalize_email(df, column='EMAIL'):
    """
    Normaliza emails a minúsculas y elimina espacios.
    """
    df = df.copy()
    if column in df.columns:
        df[column] = df[column].str.lower().str.strip()
        # Marcar emails inválidos como NaN
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        df.loc[~df[column].str.match(email_pattern, na=False), column] = np.nan
    return df


def normalize_phone(df, columns=['TELEFONO', 'CELULAR1', 'CELULAR2']):
    """
    Normaliza formatos de teléfono.
    """
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('-', '', regex=False)
            df[col] = df[col].str.replace(' ', '', regex=False)
            df[col] = df[col].replace(['', '-', 'nan', 'None', 'NaN'], np.nan)
    return df


def validate_rut(rut, dv):
    """
    Valida un RUT chileno usando el algoritmo módulo 11.
    """
    if pd.isna(rut) or pd.isna(dv):
        return False
    
    try:
        rut = int(rut)
        dv = str(dv).upper().strip()
        
        reversed_digits = map(int, reversed(str(rut)))
        factors = [2, 3, 4, 5, 6, 7] * 6
        
        s = sum(d * f for d, f in zip(reversed_digits, factors))
        mod = 11 - (s % 11)
        
        if mod == 11:
            calculated_dv = '0'
        elif mod == 10:
            calculated_dv = 'K'
        else:
            calculated_dv = str(mod)
        
        return calculated_dv == dv
    except:
        return False


def add_rut_validation(df):
    """
    Agrega columna de validación de RUT.
    """
    df = df.copy()
    df['RUT_VALIDO'] = df.apply(lambda row: validate_rut(row['RUT'], row['DV']), axis=1)
    return df


def create_derived_features(df_ventas, df_clientes):
    """
    Crea variables derivadas para análisis.
    """
    df = df_ventas.copy()
    
    # Monto total de la transacción
    df['MONTO_TOTAL'] = df['CANTIDAD'] * df['PRECIO']
    
    # Componentes de fecha
    df['FECHAVENTA'] = pd.to_datetime(df['FECHAVENTA'])
    df['AÑO_VENTA'] = df['FECHAVENTA'].dt.year
    df['MES_VENTA'] = df['FECHAVENTA'].dt.month
    df['DIA_VENTA'] = df['FECHAVENTA'].dt.day
    df['DIA_SEMANA'] = df['FECHAVENTA'].dt.dayofweek
    df['TRIMESTRE'] = df['FECHAVENTA'].dt.quarter
    df['ES_FIN_DE_SEMANA'] = df['DIA_SEMANA'].isin([5, 6]).astype(int)
    
    # Calcular antigüedad del cliente
    df_clientes['FECHACREACION'] = pd.to_datetime(df_clientes['FECHACREACION'])
    df = df.merge(df_clientes[['IDCLIENTE', 'FECHACREACION']], on='IDCLIENTE', how='left')
    df['ANTIGUEDAD_DIAS'] = (df['FECHAVENTA'] - df['FECHACREACION']).dt.days
    
    # Categoría de monto
    df['CATEGORIA_MONTO'] = pd.cut(
        df['MONTO_TOTAL'],
        bins=[0, 50000, 150000, 300000, float('inf')],
        labels=['Bajo', 'Medio', 'Alto', 'Premium']
    )
    
    return df


def clean_ventas_completa(df_ventas, df_clientes, df_productos, df_sucursales):
    """
    Pipeline completo de limpieza de datos de ventas.
    """
    # 1. Limpiar textos
    df_ventas = trim_text_columns(df_ventas)
    df_clientes = trim_text_columns(df_clientes)
    
    # 2. Normalizar emails
    df_clientes = normalize_email(df_clientes)
    
    # 3. Normalizar teléfonos
    df_clientes = normalize_phone(df_clientes)
    
    # 4. Validar RUTs
    df_clientes = add_rut_validation(df_clientes)
    
    # 5. Crear variables derivadas
    df_ventas = create_derived_features(df_ventas, df_clientes)
    
    # 6. Merge con dimensiones
    df = df_ventas.merge(df_productos, on='IDPRODUCTO', how='left')
    df = df.merge(df_sucursales, on='IDSUCURSAL', how='left')
    
    # 7. Limpiar observaciones vacías
    df['OBSERVACION'] = df['OBSERVACION'].replace('SIN OBSERVACION', np.nan)
    
    return df


if __name__ == "__main__":
    print("Módulo de limpieza cargado correctamente.")