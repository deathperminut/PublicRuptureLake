from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def getInstance():
    ## funcion para obtener una instancia directa en la base de mongo
    #### CREDENCIALES DE CONEXIÓN DESDE VARIABLES DE ENTORNO
    host = os.getenv('MONGO_HOST')
    port = int(os.getenv('MONGO_PORT'))
    username = os.getenv('MONGO_USERNAME')
    password = os.getenv('MONGO_PASSWORD')
    
    # creamos una instancia del cliente
    client = MongoClient(host, port, username=username, password=password)
    return client


if __name__ == '__main__':
    print(getInstance())

