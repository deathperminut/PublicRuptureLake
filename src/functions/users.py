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
        # Hashear la contraseña antes de guardar
        if 'password' in body:
            body['password'] = hash_password(body['password'])
        
        # Establecer valores por defecto si no están definidos
        if 'rol' not in body or body['rol'] not in ['worker', 'SuperAdmin']:
            body['rol'] = 'worker'  # Por defecto es worker
            
        if 'state' not in body:
            body['state'] = True  # Por defecto habilitado (true = enabled, false = disabled)
        
        response = db.users.insert_one(
            body
        )
        return {'status':'Usuario creado con éxito'}

def createSuperAdmin(body):
    """Crear un usuario SuperAdmin - para uso en APIs o scripts de inicialización"""
    client = getInstance()
    db = client["rupture"]
    
    # Verificar si ya existe
    filter_ = {"identification": body['identification']}
    response = db.users.find(filter_)
    response = list(response)
    if len(response) != 0:
        return {'status': 'Usuario con cédula ya existente'}
    
    # Hashear contraseña
    if 'password' in body:
        body['password'] = hash_password(body['password'])
    
    # Forzar rol SuperAdmin y estado habilitado
    body['rol'] = 'SuperAdmin'
    body['state'] = True
    
    response = db.users.insert_one(body)
    return {'status': 'SuperAdmin creado con éxito'}

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
    return hashed_password.decode('utf-8')  # Devolver como string para MongoDB


def verificar_password(stored_password, provided_password):
    # Compara la contraseña proporcionada con la almacenada
    # Si stored_password es string, convertir a bytes
    if isinstance(stored_password, str):
        stored_password = stored_password.encode('utf-8')
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
        
        # Verificar si el usuario está habilitado (true = habilitado, false = deshabilitado)
        if user_.get('state', True) == False:
            return {'status':'Usuario deshabilitado. Contacte al administrador'}
        
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

def updateUserState(user_id, new_state_bool):
    """Actualizar el estado (habilitado/deshabilitado) de un usuario"""
    client = getInstance()
    db = client["rupture"]
    filter_ = {"_id": ObjectId(user_id)}
    # new_state_bool debe ser True (habilitado) o False (deshabilitado)
    update = {"$set": {"state": new_state_bool}}
    response = db.users.update_one(filter_, update)
    return response

def updateUserPassword(user_id, new_password):
    """Cambiar la contraseña de un usuario (solo SuperAdmin)"""
    client = getInstance()
    db = client["rupture"]
    hashed_password = hash_password(new_password)
    filter_ = {"_id": ObjectId(user_id)}
    update = {"$set": {"password": hashed_password}}
    response = db.users.update_one(filter_, update)
    return response

def getUserById(user_id):
    """Obtener un usuario específico por ID"""
    client = getInstance()
    db = client["rupture"]
    filter_ = {"_id": ObjectId(user_id)}
    response = db.users.find_one(filter_)
    return response

