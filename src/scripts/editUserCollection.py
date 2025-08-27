import sys
sys.path.append('src/models')
from conect import getInstance


def editCollectionUser():
    client =  getInstance()
    # accedemos a la base de datos correspondiente
    db = client["rupture"]
    command = {
            "collMod": "users",
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

    db.command(command)
    print("Actualizado con éxito")


if __name__=="__main__":
    editCollectionUser()
