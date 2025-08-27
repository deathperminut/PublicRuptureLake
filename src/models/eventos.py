################################################################
######## definimos la estructura de la colección################
################################################################
import sys
sys.path.append('src/models')
from conect import getInstance


def generateEventsCollections():
    # Obtenemos una instancia de la base de datos
    client =  getInstance()
    # accedemos a la base de datos
    db = client["rupture"]
    #db.users.drop()
    # Define the JSON schema
    schema = {
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["orden","ubicacion","presion","subte","dist_tube","dist_tube_uni","dist_tube2","dist_tube_uni2","diame_tube","Material","Unidades","direccion","forma","medida_rupt","medida_uni","area","flujo","volumen","inicio","duracion","hora_reg","presion_atmos","volumen_fuga","volumen_muerto","diame_equi","aprobado"],
            }
        }
    }

    db.create_collection('events',**schema)



if __name__ == "__main__":
    generateEventsCollections()
