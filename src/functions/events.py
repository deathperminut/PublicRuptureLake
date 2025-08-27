########################################
########### REALIZAMOS EL CRUD #########
########################################
from bson import ObjectId
import sys
sys.path.append('src/functions')
from conect import getInstance
import bcrypt


### FUNCIONES DE CIFRADO DE CONTRASEÑAS


###################
##### CREATE ######
###################
def createEvent(body):
    client =  getInstance()
    db = client["rupture"]
    ## MIRAMOS QUE NO HAYA UN USUARIO REGISTRADO CON LA MISMA CEDULA
    filter_ = {"orden":body['orden']} ## OBTENGO EL USUARIO CON LA CEDULA
    response = db.events.find(filter_)
    response  =  list(response)
    if(len(response) != 0):
        return {'status':'Ya éxiste una orden registrada con dicho valor'}
    else:
        response = db.events.insert_one(
            body
        )
        return {'status':'Orden creada con éxito'}



###################
#### UPDATE #######
###################

def updateEvent(body):

    client =  getInstance()
    db = client["rupture"]
    filter_ = {"orden":body['orden']}
    update={"$set":{
        "ubicacion":body["ubicacion"],
        "presion":body["presion"],
        "subte":body["subte"],
        "dist_tube":body["dist_tube"],
        "dist_tube_uni":body["dist_tube_uni"],
        "dist_tube2":body["dist_tube2"],
        "dist_tube_uni2":body["dist_tube_uni2"],
        "diame_tube":body["diame_tube"],
        "Material":body["Material"],
        "Unidades":body["Unidades"],
        "direccion":body["direccion"],
        "forma":body["forma"],
        "medida_rupt":body["medida_rupt"],
        "medida_uni":body["medida_uni"],
        #"medida_rupt2":body["medida_rupt2"],
        #"medida_uni2":body["medida_uni2"],
        "area":body["area"],
        "flujo":body["flujo"],
        "volumen":body["volumen"],
        "inicio":body["inicio"],
        "duracion":body["duracion"],
        "presion_atmos":body["presion_atmos"],
        "volumen_fuga":body["volumen_fuga"],
        "volumen_muerto":body["volumen_muerto"],
        "diame_equi":body["diame_equi"],
        "aprobado":body["aprobado"],

    }
    }
    response = db.events.update_one(filter_,update)
    return response

##################
### DELETE #######
##################

def deleteEvent(body):

    client =  getInstance()
    db = client["rupture"]
    filter_ = {"_id":ObjectId(body['_id'])}
    response = db.events.delete_one(filter_)
    return response


#################
#### GET ########
#################

def getEvents():

    client =  getInstance()
    db = client["rupture"]
    response = db.events.find()
    return response


def getSpecificEvent(body):

    client =  getInstance()
    db = client["rupture"]
    filter_={
        "orden":body['orden']
    }
    response = db.events.find(filter_)
    return response

