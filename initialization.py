################################################################
######## Script de inicialización de la base de datos ###########
################################################################
import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

sys.path.append('src/models')
from conect import getInstance
from users import generateUsersCollections
from eventos import generateEventsCollections

def initialize_database():
    """
    Inicializa la base de datos MongoDB con todas las colecciones necesarias
    Crea la base de datos si no existe
    """
    try:
        # Obtener instancia de la base de datos
        client = getInstance()
        
        # Verificar conexión
        print("Conectando a MongoDB...")
        client.admin.command('ping')
        print("✓ Conexión exitosa a MongoDB")
        
        # Listar bases de datos existentes
        existing_dbs = client.list_database_names()
        print(f"Bases de datos existentes: {existing_dbs}")
        
        # Acceder/crear la base de datos usando variable de entorno
        database_name = os.getenv('MONGO_DATABASE')
        db = client[database_name]
        
        if database_name not in existing_dbs:
            print(f"La base de datos '{database_name}' no existe, se creará automáticamente...")
        else:
            print(f"La base de datos '{database_name}' ya existe")
        
        print(f"Trabajando con la base de datos: {db.name}")
        
        # Verificar si las colecciones ya existen
        existing_collections = db.list_collection_names()
        print(f"Colecciones existentes: {existing_collections}")
        
        # Crear colecciones con sus respectivos esquemas
        if "users" not in existing_collections:
            print("Creando colección de usuarios...")
            generateUsersCollections()
            print("✓ Colección 'users' creada exitosamente")
        else:
            print("⚠️  La colección 'users' ya existe")
        
        if "events" not in existing_collections:
            print("Creando colección de eventos...")
            generateEventsCollections()
            print("✓ Colección 'events' creada exitosamente")
        else:
            print("⚠️  La colección 'events' ya existe")
        
        # Listar las colecciones finales
        final_collections = db.list_collection_names()
        print(f"\nColecciones en la base de datos '{database_name}': {final_collections}")
        
        # Verificar que la base de datos se creó
        updated_dbs = client.list_database_names()
        if database_name in updated_dbs:
            print(f"\n🎉 Base de datos '{database_name}' inicializada correctamente")
        else:
            print(f"\n❌ Error: La base de datos '{database_name}' no se creó correctamente")
        
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {str(e)}")
        raise e
    finally:
        if 'client' in locals():
            client.close()
            print("Conexión cerrada")

if __name__ == "__main__":
    initialize_database()