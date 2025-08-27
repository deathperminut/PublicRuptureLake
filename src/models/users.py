################################################################
######## definimos la estructura de la colección################
################################################################
import sys
sys.path.append('src/models')
from conect import getInstance


def generateUsersCollections():
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
                "required": ["first_name","last_name","email","identification","password","rol","state"],
                "properties": {
                    "first_name": {"bsonType": "string"},
                    "last_name": {"bsonType": "string"},
                    "email": {"bsonType": "string"},
                    "identification": {"bsonType": "string"},
                    "rol": {
                      "enum":['worker','admin']
                    },
                    "state":{
                        "enum":[True,False]
                    }
                }
            }
        }
    }

    db.create_collection('users',**schema)



if __name__ == "__main__":

    generateUsersCollections()
