"""
Carga de datos normalizados a Supabase.
Este script se ejecuta LOCALMENTE en tu PC, no en GitHub.
"""

import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno (SOLO local, NUNCA en GitHub)
load_dotenv()

# Configuración Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")        # ej: https://xxxx.supabase.co
SUPABASE_KEY = os.getenv("SUPABASE_KEY")      # tu API key (service_role o anon)

# Inicializar cliente
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def subir_datos_csv(tabla_nombre, csv_path):
    """
    Sube datos desde CSV a una tabla de Supabase.
    
    Args:
        tabla_nombre: Nombre de la tabla en Supabase
        csv_path: Ruta al archivo CSV normalizado
    """
    df = pd.read_csv(csv_path)
    
    # Convertir a lista de diccionarios (formato que acepta Supabase)
    registros = df.to_dict('records')
    
    # Insertar en batches de 1000 (límite de Supabase)
    batch_size = 1000
    for i in range(0, len(registros), batch_size):
        batch = registros[i:i + batch_size]
        
        response = supabase.table(tabla_nombre).insert(batch).execute()
        
        print(f"✅ Batch {i//batch_size + 1}: {len(batch)} registros insertados en {tabla_nombre}")
    
    print(f"🎉 Total: {len(registros)} registros en {tabla_nombre}")


def limpiar_tabla(tabla_nombre):
    """Elimina todos los datos de una tabla (cuidado!)."""
    supabase.table(tabla_nombre).delete().neq('id', 0).execute()
    print(f"🗑️ Tabla {tabla_nombre} limpiada")


if __name__ == "__main__":
    # Ejemplo de uso
    # Primero normalizas los datos con tu Normalizar.py
    # Luego ejecutas este script para subirlos
    
    print("=" * 50)
    print("CARGA DE DATOS A SUPABASE")
    print("=" * 50)
    
    # Subir cada tabla normalizada
    tablas = [
        ('REGION', 'data/normalized/region.csv'),
        ('CIUDAD', 'data/normalized/ciudad.csv'),
        ('PROVEEDORES', 'data/normalized/proveedores.csv'),
        ('TIPOPRODUCTO', 'data/normalized/tipo_producto.csv'),
        ('PRODUCTOS', 'data/normalized/productos.csv'),
        ('CLIENTES', 'data/normalized/clientes.csv'),
        ('SUCURSALES', 'data/normalized/sucursales.csv'),
        ('VENDEDOR', 'data/normalized/vendedor.csv'),
        ('VENTASDIARIAS', 'data/normalized/ventas_diarias.csv'),
        ('VENTASVENDEDOR', 'data/normalized/ventas_vendedor.csv'),
    ]
    
    for tabla, ruta in tablas:
        if os.path.exists(ruta):
            print(f"\n📤 Subiendo {tabla}...")
            subir_datos_csv(tabla, ruta)
        else:
            print(f"⚠️ No encontrado: {ruta}")
    
    print("\n✅ Carga completada!")