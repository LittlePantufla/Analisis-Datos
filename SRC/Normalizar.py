"""
Normalización de datos desde SQL Server (.sql) a CSV para Supabase.
Lee el archivo ventas.sql (UTF-16, formato SQL Server) y genera
un CSV por tabla en Data/normalized/, listos para carga con upsert.

Proyecto: Optimización del Análisis de Datos
Integrantes: Joaquín Martí, Joaquín Paredes, Daniel Ruiz
"""

import re
import os
import pandas as pd
import numpy as np

# ── CONFIGURACIÓN ─────────────────────────────────────────────────────────────
SQL_FILE   = 'Data/ventas.sql'        # Archivo SQL Server de origen
OUTPUT_DIR = 'Data/normalized'   # Carpeta de salida


# ── LECTURA DEL ARCHIVO ───────────────────────────────────────────────────────
def leer_sql(path):
    """Lee el .sql exportado desde SQL Server (encoding UTF-16-LE)."""
    try:
        with open(path, 'r', encoding='utf-16-le', errors='ignore') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {path}")


# ── PARSEO DE VALORES SQL SERVER ──────────────────────────────────────────────
def parsear_valor(val):
    """
    Convierte un valor SQL Server a Python:
      CAST(5 AS Numeric(18, 0))     → 5
      CAST(1.000 AS Numeric(18, 3)) → 1.0
      N'texto'                      → 'texto' (strip de espacios)
      NULL                          → None
    """
    val = val.strip()

    if val.upper() == 'NULL':
        return None

    # CAST numérico
    m = re.match(r"CAST\((.+?)\s+AS\s+Numeric\((\d+),\s*(\d+)\)\)", val, re.IGNORECASE)
    if m:
        numero = m.group(1).strip()
        decimales = int(m.group(3))
        try:
            return float(numero) if decimales > 0 else int(float(numero))
        except ValueError:
            return None

    # CAST datetime → string ISO
    m = re.match(r"CAST\(N'(.+?)'\s+AS\s+DateTime\)", val, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # String N'...'
    m = re.match(r"N'(.*)'$", val, re.DOTALL)
    if m:
        texto = m.group(1).strip()
        # Reemplazar guión solo (valor vacío) por None
        return None if texto in ('-', '') else texto

    return val


def parsear_fila(valores_str):
    """
    Parsea la cadena de valores de un INSERT y devuelve una lista Python.
    Maneja correctamente comas dentro de CAST(...) y N'...'.
    """
    tokens = []
    depth   = 0
    current = ''
    in_str  = False

    i = 0
    while i < len(valores_str):
        c = valores_str[i]

        if c == "'" and not in_str:
            in_str  = True
            current += c
        elif c == "'" and in_str:
            # Detectar comilla escapada ''
            if i + 1 < len(valores_str) and valores_str[i + 1] == "'":
                current += "''"
                i += 2
                continue
            in_str  = False
            current += c
        elif c == '(' and not in_str:
            depth   += 1
            current += c
        elif c == ')' and not in_str:
            depth   -= 1
            current += c
        elif c == ',' and not in_str and depth == 0:
            tokens.append(parsear_valor(current.strip()))
            current = ''
            i += 1
            continue
        else:
            current += c
        i += 1

    if current.strip():
        tokens.append(parsear_valor(current.strip()))

    return tokens


# ── EXTRACCIÓN POR TABLA ──────────────────────────────────────────────────────
TABLAS = {
    'region': {
        'patron': r"INSERT \[dbo\]\.\[REGION\]\s*\(\[IDREGION\],\s*\[CODIGOREGION\],\s*\[NOMBREREGION\]\)\s*VALUES\s*\((.+?)\)\s*$",
        'columnas': ['idregion', 'codigoregion', 'nombreregion'],
    },
    'ciudad': {
        'patron': r"INSERT \[dbo\]\.\[CIUDAD\]\s*\(\[IDCIUDAD\],\s*\[IDREGION\],\s*\[NOMBRECIUDAD\]\)\s*VALUES\s*\((.+?)\)\s*$",
        'columnas': ['idciudad', 'idregion', 'nombreciudad'],
    },
    'proveedores': {
        'patron': r"INSERT \[dbo\]\.\[PROVEEDORES\]\s*\(\[IDPROVEEDOR\],\s*\[NOMBREPROVEEDOR\]\)\s*VALUES\s*\((.+?)\)\s*$",
        'columnas': ['idproveedor', 'nombreproveedor'],
    },
    'tipoproducto': {
        'patron': r"INSERT \[dbo\]\.\[TIPOPRODUCTO\]\s*\(\[IDTIPOPRODUCTO\],\s*\[NOMBRETIPOPRODUCTO\]\)\s*VALUES\s*\((.+?)\)\s*$",
        'columnas': ['idtipoproducto', 'nombretipoproducto'],
    },
    'vendedor': {
        'patron': r"INSERT \[dbo\]\.\[VENDEDOR\]\s*\(\[IDVENDEDOR\],\s*\[NOMBREVENDEDOR\],\s*\[APELLIDOPATERNO\],\s*\[APELLIDOMATERNO\]\)\s*VALUES\s*\((.+?)\)\s*$",
        'columnas': ['idvendedor', 'nombrevendedor', 'apellidopaterno', 'apellidomaterno'],
    },
    'sucursales': {
        'patron': r"INSERT \[dbo\]\.\[SUCURSALES\]\s*\(\[IDSUCURSAL\],\s*\[IDCIUDAD\],\s*\[NOMBRESUCURSAL\],\s*\[CODIGOSUCURSAL\]\)\s*VALUES\s*\((.+?)\)\s*$",
        'columnas': ['idsucursal', 'idciudad', 'nombresucursal', 'codigosucursal'],
    },
    'productos': {
        'patron': r"INSERT \[dbo\]\.\[PRODUCTOS\]\s*\(\[IDPRODUCTO\],\s*\[IDTIPOPRODUCTO\],\s*\[IDPROVEEDOR\],\s*\[NOMBREPRODUCTO\],\s*\[CODIGOPRODUCTO\]\)\s*VALUES\s*\((.+?)\)\s*$",
        'columnas': ['idproducto', 'idtipoproducto', 'idproveedor', 'nombreproducto', 'codigoproducto'],
    },
    'clientes': {
        'patron': r"INSERT \[dbo\]\.\[CLIENTES\]\s*\(\[IDCLIENTE\],\s*\[RUT\],\s*\[DV\],\s*\[NOMBRECLIENTE\],\s*\[APELLIDOPATERNO\],\s*\[APELLIDOMATERNO\],\s*\[EMAIL\],\s*\[TELEFONO\],\s*\[CELULAR1\],\s*\[CELULAR2\],\s*\[FECHACREACION\],\s*\[VIGENTE\]\)\s*VALUES\s*\((.+?)\)\s*$",
        'columnas': ['idcliente', 'rut', 'dv', 'nombrecliente', 'apellidopaterno',
                     'apellidomaterno', 'email', 'telefono', 'celular1', 'celular2',
                     'fechacreacion', 'vigente'],
    },
    'ventasdiarias': {
        'patron': r"INSERT \[dbo\]\.\[VENTASDIARIAS\]\s*\(\[NROVENTA\],\s*\[FECHAVENTA\],\s*\[IDCLIENTE\],\s*\[IDPRODUCTO\],\s*\[IDSUCURSAL\],\s*\[TIPOPAGO\],\s*\[CANTIDAD\],\s*\[PRECIO\],\s*\[OBSERVACION\]\)\s*VALUES\s*\((.+?)\)\s*$",
        'columnas': ['nroventa', 'fechaventa', 'idcliente', 'idproducto', 'idsucursal',
                     'tipopago', 'cantidad', 'precio', 'observacion'],
    },
    'ventasvendedor': {
        'patron': r"INSERT \[dbo\]\.\[VENTASVENDEDOR\]\s*\(\[IDVENDEDOR\],\s*\[NROVENTA\]\)\s*VALUES\s*\((.+?)\)\s*$",
        'columnas': ['idvendedor', 'nroventa'],
    },
}


def extraer_tabla(content, tabla, config):
    """Extrae todos los registros de una tabla y devuelve un DataFrame."""
    matches = re.findall(config['patron'], content, re.MULTILINE)
    if not matches:
        print(f"  ⚠️  Sin coincidencias para {tabla}")
        return pd.DataFrame(columns=config['columnas'])

    filas = [parsear_fila(m) for m in matches]

    # Verificar que todas las filas tengan la cantidad correcta de columnas
    n_cols = len(config['columnas'])
    filas_ok = []
    for i, fila in enumerate(filas):
        if len(fila) == n_cols:
            filas_ok.append(fila)
        else:
            print(f"  ⚠️  Fila {i+1} con {len(fila)} columnas (esperadas {n_cols}), se omite")

    return pd.DataFrame(filas_ok, columns=config['columnas'])


# ── LIMPIEZA ──────────────────────────────────────────────────────────────────
def limpiar_strings(df):
    """Strip de espacios en columnas de texto. SQL Server rellena con espacios los nchar."""
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace(['nan', 'None', 'NaN', '', '-'], np.nan)
    return df


def limpiar_telefonos(df):
    """Elimina guiones y espacios de campos de teléfono."""
    for col in ['telefono', 'celular1', 'celular2']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'[-\s]', '', regex=True)
            df[col] = df[col].replace(['nan', 'None', ''], np.nan)
    return df


def limpiar_emails(df):
    """Pasa emails a minúsculas y marca como None los inválidos."""
    if 'email' not in df.columns:
        return df
    df['email'] = df['email'].str.lower().str.strip()
    patron = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    invalidos = ~df['email'].str.match(patron, na=False)
    df.loc[invalidos, 'email'] = np.nan
    return df


def limpiar_observaciones(df):
    """Reemplaza observaciones en blanco por None."""
    if 'observacion' in df.columns:
        df['observacion'] = df['observacion'].replace(
            ['SIN OBSERVACION', 'SIN OBSERVACIÓN', ''], np.nan
        )
    return df


LIMPIEZA_ESPECIAL = {
    'clientes':      [limpiar_strings, limpiar_telefonos, limpiar_emails],
    'ventasdiarias': [limpiar_strings, limpiar_observaciones],
}


def aplicar_limpieza(nombre, df):
    """Aplica limpieza genérica + específica por tabla."""
    df = limpiar_strings(df)
    for fn in LIMPIEZA_ESPECIAL.get(nombre, []):
        df = fn(df)
    return df


# ── PIPELINE PRINCIPAL ────────────────────────────────────────────────────────
def normalizar():
    print("=" * 55)
    print("  NORMALIZACIÓN SQL Server → CSV para Supabase")
    print("=" * 55)

    # Leer SQL
    print(f"\n📂 Leyendo {SQL_FILE}...")
    content = leer_sql(SQL_FILE)
    print(f"   {len(content):,} caracteres cargados\n")

    # Crear carpeta de salida
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Orden de inserción (respeta dependencias FK)
    orden = [
        'region', 'tipoproducto', 'proveedores', 'vendedor',
        'ciudad', 'sucursales', 'productos', 'clientes',
        'ventasdiarias', 'ventasvendedor'
    ]

    resumen = []

    for tabla in orden:
        config = TABLAS[tabla]
        print(f"⚙️  Procesando {tabla.upper()}...")

        df = extraer_tabla(content, tabla, config)
        df = aplicar_limpieza(tabla, df)

        ruta = os.path.join(OUTPUT_DIR, f"{tabla}.csv")
        df.to_csv(ruta, index=False, encoding='utf-8')

        resumen.append((tabla, len(df), ruta))
        print(f"   ✅ {len(df):>5} registros → {ruta}")

    print("\n" + "=" * 55)
    print("  RESUMEN FINAL")
    print("=" * 55)
    total = 0
    for tabla, n, ruta in resumen:
        print(f"  {tabla:<20} {n:>6} registros")
        total += n
    print(f"  {'TOTAL':<20} {total:>6} registros")
    print("=" * 55)
    print(f"\n✅ CSVs listos en: {OUTPUT_DIR}/")
    print("   Siguiente paso: python carga_bd.py\n")


if __name__ == "__main__":
    normalizar()