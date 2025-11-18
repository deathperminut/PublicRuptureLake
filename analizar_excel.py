#!/usr/bin/env python3
"""
Script para analizar el archivo formato.xlsx
"""
import pandas as pd
import sys

try:
    # Leer el archivo Excel
    print("Leyendo archivo formato.xlsx...")
    df = pd.read_excel('formato.xlsx', sheet_name='Eventos')

    print("\n" + "="*60)
    print("INFORMACIÓN GENERAL DEL ARCHIVO")
    print("="*60)
    print(f"Total de filas: {len(df)}")
    print(f"Total de columnas: {len(df.columns)}")

    print("\n" + "="*60)
    print("COLUMNAS DEL EXCEL")
    print("="*60)
    for i, col in enumerate(df.columns, 1):
        print(f"{i}. {col}")

    print("\n" + "="*60)
    print("PRIMERAS 5 FILAS COMPLETAS")
    print("="*60)
    print(df.head().to_string())

    print("\n" + "="*60)
    print("ANÁLISIS DETALLADO DE CADA FILA")
    print("="*60)

    for index, row in df.iterrows():
        fila_excel = index + 2  # +2 porque Excel empieza en 1 y tiene header
        print(f"\n--- FILA {fila_excel} (índice {index}) ---")

        # Numero_Orden
        orden = row.get('Numero_Orden')
        print(f"  Numero_Orden: [{orden}]")
        print(f"    Tipo: {type(orden).__name__}")
        print(f"    Es NaN: {pd.isna(orden)}")

        # Latitud
        latitud = row.get('Latitud')
        print(f"  Latitud: [{latitud}]")
        print(f"    Tipo: {type(latitud).__name__}")
        print(f"    Es NaN: {pd.isna(latitud)}")
        if not pd.isna(latitud):
            print(f"    Como string: '{str(latitud)}'")

        # Longitud
        longitud = row.get('Longitud')
        print(f"  Longitud: [{longitud}]")
        print(f"    Tipo: {type(longitud).__name__}")
        print(f"    Es NaN: {pd.isna(longitud)}")
        if not pd.isna(longitud):
            print(f"    Como string: '{str(longitud)}'")

        # Simular conversión como lo hace el código
        form_data = {}
        for col in df.columns:
            form_data[col] = '' if pd.isna(row[col]) else str(row[col])

        print(f"  Después de conversión:")
        print(f"    Numero_Orden: [{form_data.get('Numero_Orden')}] (vacío: {form_data.get('Numero_Orden') == ''})")
        print(f"    Latitud: [{form_data.get('Latitud')}] (vacío: {form_data.get('Latitud') == ''})")
        print(f"    Longitud: [{form_data.get('Longitud')}] (vacío: {form_data.get('Longitud') == ''})")

        # Ubicación como la construye el código
        latitud_str = form_data.get('Latitud', '')
        longitud_str = form_data.get('Longitud', '')
        ubicacion = f"{latitud_str},{longitud_str}" if latitud_str and longitud_str else ''
        print(f"    Ubicación construida: [{ubicacion}] (vacío: {ubicacion == ''})")

        # Mostrar algunos campos más
        print(f"  Presion_Tuberia: [{form_data.get('Presion_Tuberia')}]")
        print(f"  Diametro_Tuberia_Pulgadas: [{form_data.get('Diametro_Tuberia_Pulgadas')}]")

    print("\n" + "="*60)
    print("ANÁLISIS COMPLETADO")
    print("="*60)

except FileNotFoundError:
    print("ERROR: No se encontró el archivo formato.xlsx")
    print("Asegúrate de ejecutar este script desde el directorio donde está el archivo")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
