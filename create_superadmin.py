#!/usr/bin/env python3
"""
Script para crear un usuario SuperAdmin inicial en la base de datos.
Ejecutar este script después de inicializar la base de datos.

Uso:
    python create_superadmin.py
"""
import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

sys.path.append('src/functions')
from users import createSuperAdmin

def main():
    print("=" * 60)
    print("CREACIÓN DE SUPERADMIN INICIAL")
    print("=" * 60)

    # Solicitar datos del SuperAdmin
    print("\nIngresa los datos del SuperAdmin inicial:")

    first_name = input("Nombre: ").strip()
    last_name = input("Apellido: ").strip()
    email = input("Email: ").strip()
    identification = input("Identificación/Cédula: ").strip()

    # Solicitar contraseña (sin mostrarla)
    import getpass
    password = getpass.getpass("Contraseña (mínimo 6 caracteres): ")
    password_confirm = getpass.getpass("Confirmar contraseña: ")

    # Validaciones
    if not all([first_name, last_name, email, identification, password]):
        print("\n❌ Error: Todos los campos son obligatorios")
        return

    if len(password) < 6:
        print("\n❌ Error: La contraseña debe tener al menos 6 caracteres")
        return

    if password != password_confirm:
        print("\n❌ Error: Las contraseñas no coinciden")
        return

    # Crear el objeto de usuario
    superadmin_data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "identification": identification,
        "password": password
    }

    # Intentar crear el SuperAdmin
    print(f"\nCreando SuperAdmin con identificación {identification}...")
    try:
        response = createSuperAdmin(superadmin_data)

        if response['status'] == 'SuperAdmin creado con éxito':
            print("\n" + "=" * 60)
            print("✅ SUPERADMIN CREADO EXITOSAMENTE")
            print("=" * 60)
            print(f"Nombre: {first_name} {last_name}")
            print(f"Email: {email}")
            print(f"Identificación: {identification}")
            print(f"Rol: SuperAdmin")
            print(f"Estado: Habilitado")
            print("\nYa puedes iniciar sesión en la aplicación usando estas credenciales.")
            print("=" * 60)
        else:
            print(f"\n❌ Error: {response['status']}")

    except Exception as e:
        print(f"\n❌ Error al crear SuperAdmin: {str(e)}")
        print("\nVerifica que:")
        print("1. La base de datos MongoDB esté corriendo")
        print("2. Las variables de entorno en .env estén configuradas correctamente")
        print("3. La colección 'users' esté creada (ejecuta initialization.py primero)")

if __name__ == "__main__":
    main()
