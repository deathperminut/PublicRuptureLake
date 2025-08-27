import sys
sys.path.append('src/models')
from conect import getInstance


def editCollectionEvents():
    client =  getInstance()
    # accedemos a la base de datos correspondiente
    db = client["rupture"]
    command = {
            "collMod": "events",
            "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required":  ["orden","ubicacion","presion","subte","dist_tube","dist_tube_uni","dist_tube2","dist_tube_uni2","diame_tube","Material","Unidades","direccion","forma","medida_rupt","medida_uni","medida_rupt2","medida_uni2","area","flujo","volumen","inicio","duracion","hora_reg","presion_atmos","volumen_fuga","volumen_muerto","diame_equi","aprobado"],
            }
           }
        }

    db.command(command)
    print("Actualizado con éxito")


if __name__=="__main__":
    editCollectionEvents()
