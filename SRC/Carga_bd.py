"""
Carga de datos normalizados a Supabase.
Este script se ejecuta LOCALMENTE en tu PC.
Proyecto: Optimización del Análisis de Datos
Integrantes: Joaquín Martí, Joaquín Paredes, Daniel Ruiz
"""

import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno (SOLO local, NUNCA en GitHub)
load_dotenv()

# Configuración Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Inicializar cliente
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def subir_datos_csv(tabla_nombre, csv_path):
    """
    Sube datos desde CSV a una tabla de Supabase.
    
    Args:
        tabla_nombre: Nombre de la tabla en Supabase
        csv_path: Ruta al archivo CSV normalizado
    """
    if not os.path.exists(csv_path):
        print(f"⚠️ No encontrado: {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    
    # Eliminar columnas que no existen en la tabla (opcional)
    # df = df[['columnas', 'que', 'necesitas']]
    
    # Convertir a lista de diccionarios
    registros = df.to_dict('records')
    
    # Insertar en batches de 1000
    batch_size = 1000
    for i in range(0, len(registros), batch_size):
        batch = registros[i:i + batch_size]
        
        try:
            response = supabase.table(tabla_nombre).insert(batch).execute()
            print(f"✅ Batch {i//batch_size + 1}: {len(batch)} registros en {tabla_nombre}")
        except Exception as e:
            print(f"❌ Error en batch {i//batch_size + 1}: {e}")
    
    print(f"🎉 Total: {len(registros)} registros en {tabla_nombre}")


def limpiar_tabla(tabla_nombre):
    """Elimina todos los datos de una tabla."""
    try:
        supabase.table(tabla_nombre).delete().neq('id', 0).execute()
        print(f"🗑️ Tabla {tabla_nombre} limpiada")
    except Exception as e:
        print(f"⚠️ No se pudo limpiar {tabla_nombre}: {e}")
        
if __name__ == "__main__":
    print("=" * 50)
    print("CARGA DE DATOS A SUPABASE")
    print("=" * 50)
    
    # Crear carpeta normalized si no existe
    os.makedirs('Data/normalized', exist_ok=True)
    
    # Subir cada tabla normalizada
    tablas = [
        ('REGION', 'Data/normalized/region.csv'),
        ('CIUDAD', 'Data/normalized/ciudad.csv'),
        ('PROVEEDORES', 'Data/normalized/proveedores.csv'),
        ('TIPOPRODUCTO', 'Data/normalized/tipo_producto.csv'),
        ('PRODUCTOS', 'Data/normalized/productos.csv'),
        ('CLIENTES', 'Data/normalized/clientes.csv'),
        ('SUCURSALES', 'Data/normalized/sucursales.csv'),
        ('VENDEDOR', 'Data/normalized/vendedor.csv'),
        ('VENTASDIARIAS', 'Data/normalized/ventas_diarias.csv'),
        ('VENTASVENDEDOR', 'Data/normalized/ventas_vendedor.csv'),
    ]
    
    for tabla, ruta in tablas:
        print(f"\n📤 Subiendo {tabla}...")
        subir_datos_csv(tabla, ruta)
    
    print("\n" + "=" * 50)
    print("✅ Carga completada!")
    print("=" * 50)