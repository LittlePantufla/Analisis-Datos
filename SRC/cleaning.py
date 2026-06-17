"""
Módulo de limpieza y validación de datos.
Opera sobre DataFrames ya cargados desde Supabase o desde los CSVs normalizados.
 
Proyecto: Optimización del Análisis de Datos
Integrantes: Joaquín Martí, Joaquín Paredes, Daniel Ruiz
"""
 
import pandas as pd
import numpy as np
 
 
# ── LIMPIEZA GENERAL ──────────────────────────────────────────────────────────
 
def trim_text_columns(df, columns=None):
    """Elimina espacios al inicio y final de columnas de texto."""
    df = df.copy()
    if columns is None:
        columns = df.select_dtypes(include=['object', 'str']).columns
 
    for col in columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace(['nan', 'None', 'NaN', '', '-'], np.nan)
 
    return df
 
 
def normalize_email(df, column='email'):
    """Normaliza emails a minúsculas y marca como NaN los inválidos."""
    df = df.copy()
    if column not in df.columns:
        return df
 
    df[column] = df[column].str.lower().str.strip()
    patron = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    invalidos = ~df[column].str.match(patron, na=False)
    df.loc[invalidos, column] = np.nan
 
    return df
 
 
def normalize_phone(df, columns=None):
    """Elimina guiones y espacios de campos de teléfono."""
    df = df.copy()
    if columns is None:
        columns = ['telefono', 'celular1', 'celular2']
 
    for col in columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'[-\s]', '', regex=True)
            df[col] = df[col].replace(['', 'nan', 'None', 'NaN'], np.nan)
 
    return df
 
 
# ── VALIDACIÓN RUT CHILENO ────────────────────────────────────────────────────
 
def validate_rut(rut, dv):
    """Valida un RUT chileno usando el algoritmo módulo 11."""
    if pd.isna(rut) or pd.isna(dv):
        return False
    try:
        rut = int(rut)
        dv  = str(dv).upper().strip()
 
        reversed_digits = map(int, reversed(str(rut)))
        factors = [2, 3, 4, 5, 6, 7] * 6
        s   = sum(d * f for d, f in zip(reversed_digits, factors))
        mod = 11 - (s % 11)
 
        if mod == 11:
            calculated_dv = '0'
        elif mod == 10:
            calculated_dv = 'K'
        else:
            calculated_dv = str(mod)
 
        return calculated_dv == dv
    except Exception:
        return False
 
 
def add_rut_validation(df):
    """Agrega columna booleana 'rut_valido' al DataFrame de clientes."""
    df = df.copy()
    if 'rut' in df.columns and 'dv' in df.columns:
        df['rut_valido'] = df.apply(
            lambda row: validate_rut(row['rut'], row['dv']), axis=1
        )
    return df
 
 
# ── VARIABLES DERIVADAS ───────────────────────────────────────────────────────
 
def create_derived_features(df_ventas, df_clientes):
    """
    Crea columnas calculadas sobre el DataFrame de ventas:
    - monto_total, año, mes, día, trimestre, fin de semana, antigüedad cliente
    """
    df = df_ventas.copy()
 
    # Monto total
    df['monto_total'] = df['cantidad'] * df['precio']
 
    # Componentes de fecha
    df['fechaventa'] = pd.to_datetime(df['fechaventa'])
    df['anio_venta']      = df['fechaventa'].dt.year
    df['mes_venta']       = df['fechaventa'].dt.month
    df['dia_venta']       = df['fechaventa'].dt.day
    df['dia_semana']      = df['fechaventa'].dt.dayofweek
    df['trimestre']       = df['fechaventa'].dt.quarter
    df['es_fin_de_semana'] = df['dia_semana'].isin([5, 6]).astype(int)
 
    # Antigüedad del cliente (días desde su creación hasta la venta)
    df_clientes = df_clientes.copy()
    df_clientes['fechacreacion'] = pd.to_datetime(df_clientes['fechacreacion'])
    df = df.merge(
        df_clientes[['idcliente', 'fechacreacion']],
        on='idcliente',
        how='left'
    )
    df['antiguedad_dias'] = (df['fechaventa'] - df['fechacreacion']).dt.days
 
    # Categoría de monto
    df['categoria_monto'] = pd.cut(
        df['monto_total'],
        bins=[0, 50_000, 150_000, 300_000, float('inf')],
        labels=['Bajo', 'Medio', 'Alto', 'Premium']
    )
 
    return df
 
 
# ── PIPELINE COMPLETO ─────────────────────────────────────────────────────────
 
def clean_ventas_completa(df_ventas, df_clientes, df_productos, df_sucursales):
    """
    Pipeline de limpieza y enriquecimiento completo.
    Retorna un DataFrame listo para análisis o visualización.
    """
    # 1. Limpiar textos
    df_ventas    = trim_text_columns(df_ventas)
    df_clientes  = trim_text_columns(df_clientes)
    df_productos = trim_text_columns(df_productos)
 
    # 2. Normalizar emails y teléfonos de clientes
    df_clientes = normalize_email(df_clientes)
    df_clientes = normalize_phone(df_clientes)
 
    # 3. Validar RUTs
    df_clientes = add_rut_validation(df_clientes)
 
    # 4. Variables derivadas
    df_ventas = create_derived_features(df_ventas, df_clientes)
 
    # 5. Merge con dimensiones
    df = df_ventas.merge(df_productos, on='idproducto', how='left')
    df = df.merge(df_sucursales,  on='idsucursal',  how='left')
 
    # 6. Limpiar observaciones vacías
    if 'observacion' in df.columns:
        df['observacion'] = df['observacion'].replace(
            ['SIN OBSERVACION', 'SIN OBSERVACIÓN', ''], np.nan
        )
 
    return df
 
 
if __name__ == "__main__":
    print("✅ Módulo cleaning cargado correctamente.")
    print("   Funciones disponibles:")
    print("   - trim_text_columns(df)")
    print("   - normalize_email(df)")
    print("   - normalize_phone(df)")
    print("   - add_rut_validation(df)")
    print("   - create_derived_features(df_ventas, df_clientes)")
    print("   - clean_ventas_completa(df_ventas, df_clientes, df_productos, df_sucursales)")
 