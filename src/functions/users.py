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
def createUser(body):
    client =  getInstance()
    db = client["rupture"]
    ## MIRAMOS QUE NO HAYA UN USUARIO REGISTRADO CON LA MISMA CEDULA
    filter_ = {"identification":body['identification']} ## OBTENGO EL USUARIO CON LA CEDULA
    response = db.users.find(filter_)
    response  =  list(response)
    if(len(response) != 0):
        return {'status':'Usuario con cédula ya éxistente'}
    else:
        response = db.users.insert_one(
            body
        )
        return {'status':'Usuario creado con éxito'}

###################
#### UPDATE #######
###################

def updateUser(body):

    client =  getInstance()
    db = client["rupture"]
    filter_ = {"_id":ObjectId(body['_id'])}
    update={"$set":{
        "first_name": body['first_name'],
        "email":body['email'],
        "identification": body['identification'],
        "last_name": body['last_name'],
        "rol": body['rol'],
        "state":body['state']
    }
    }
    response = db.users.update_one(filter_,update)
    return response

##################
### DELETE #######
##################

def deleteUser(body):

    client =  getInstance()
    db = client["rupture"]
    filter_ = {"_id":ObjectId(body['_id'])}
    response = db.users.delete_one(filter_)
    return response


#################
#### GET ########
#################

def getUsers():

    client =  getInstance()
    db = client["rupture"]
    response = db.users.find()
    return response


#####################
###### LOGIN_V2 #####
#####################

# Función para hashear la contraseña
def hash_password(password):
    # Genera un salt y hashea la contraseña
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password


def verificar_password(stored_password, provided_password):
    # Compara la contraseña proporcionada con la almacenada
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password)



def loginUserV2(body):
    client =  getInstance()
    db = client["rupture"]
    filter_ = {"identification":body['identification']} ## OBTENGO EL USUARIO CON LA CEDULA
    response = db.users.find(filter_)
    response  =  list(response)
    if(len(response) == 0):
        return {'status':'No hay ningun usuario registrado con dicha identificación'}
    else:
        ## VALIDAMOS EL HASH DE LA CONTRASEÑA
        user_ = response[0]
        answer = verificar_password(user_['password'], body['password'])
        if(answer):
            user_body = response[0]
            user_body['status'] = 'Registro éxitoso'
            return user_body
        else:
            return {'status':'La contraseña no coincide'}

def GetSpecificUser(dni):
    client =  getInstance()
    db = client["rupture"]
    filter_ = {"dni":dni}
    response = db.users.find(filter_)
    return response

