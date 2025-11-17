# Guía de Configuración - RuptureLakes

## 📋 Resumen de Cambios Recientes

Se actualizó el sistema de roles de usuarios para usar únicamente dos roles:
- **`worker`**: Usuario trabajador estándar (puede crear eventos y usar carga masiva)
- **`SuperAdmin`**: Usuario administrador con acceso total

### ⚠️ Cambios Importantes
1. Se eliminó el sistema antiguo de `tipo_user`
2. Todos los roles ahora usan el campo `rol` con valores: `['worker', 'SuperAdmin']`
3. Se limpiaron referencias obsoletas en el código

---

## 🚀 Configuración Inicial

### 1. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
# MongoDB Configuration (local)
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_USERNAME=root
MONGO_PASSWORD=tu_password_seguro
MONGO_DATABASE=rupture

# Flask Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=4500
FLASK_DEBUG=True
```

**Nota**: Si tu MongoDB local **no tiene autenticación**, deja vacíos `MONGO_USERNAME` y `MONGO_PASSWORD`.

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 3. Inicializar la Base de Datos

Este script creará las colecciones `users` y `events` con sus esquemas de validación:

```bash
python initialization.py
```

Deberías ver:
```
✓ Conexión exitosa a MongoDB
Creando colección de usuarios...
✓ Colección 'users' creada exitosamente
Creando colección de eventos...
✓ Colección 'events' creada exitosamente
🎉 Base de datos 'rupture' inicializada correctamente
```

### 4. Crear el Primer SuperAdmin

```bash
python create_superadmin.py
```

El script te pedirá:
- Nombre
- Apellido
- Email
- Identificación/Cédula
- Contraseña (mínimo 6 caracteres)

### 5. Ejecutar la Aplicación

```bash
python src/main.py
```

La aplicación estará disponible en: `http://localhost:4500`

---

## 🐳 Uso con Docker Compose

### 1. Configurar Variables de Entorno para Docker

Crea un archivo `.env.docker` basado en `.env.docker.example`:

```bash
# MongoDB Configuration
MONGO_INITDB_ROOT_USERNAME=root
MONGO_INITDB_ROOT_PASSWORD=tu_password_seguro
MONGO_DATA_PATH=./mongo_data

# Flask App MongoDB Connection
MONGO_HOST=mongodb_efigas
MONGO_PORT=27017
MONGO_USERNAME=root
MONGO_PASSWORD=tu_password_seguro
MONGO_DATABASE=rupture

# Flask Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=4500
FLASK_DEBUG=false
```

### 2. Levantar los Servicios

```bash
docker-compose --env-file .env.docker up -d
```

Esto levantará:
- MongoDB (puerto 27017)
- Flask App (puerto 4500)

### 3. Crear SuperAdmin en Docker

```bash
# Entrar al contenedor de Flask
docker exec -it rupture_flask_app bash

# Ejecutar el script
python create_superadmin.py

# Salir del contenedor
exit
```

### 4. Ver Logs

```bash
# Ver logs de Flask
docker-compose logs -f flask_app

# Ver logs de MongoDB
docker-compose logs -f mongodb_efigas
```

### 5. Detener los Servicios

```bash
docker-compose down
```

---

## 👥 Sistema de Roles

### Worker
**Permisos:**
- ✅ Crear nuevos eventos
- ✅ Visualizar eventos
- ✅ Editar eventos
- ✅ Usar carga masiva
- ❌ Administrar usuarios
- ❌ Descargar todos los eventos
- ❌ Aprobar eventos

### SuperAdmin
**Permisos:**
- ✅ Todo lo que puede hacer worker
- ✅ Administrar usuarios (habilitar/deshabilitar)
- ✅ Cambiar contraseñas de usuarios
- ✅ Descargar todos los eventos en Excel
- ✅ Aprobar eventos
- ✅ Acceso al panel de administración

---

## 📝 Crear Nuevos Usuarios

### Opción 1: Desde la Aplicación Web
1. Ir a la página de inicio
2. Hacer clic en "Registrarse"
3. Completar el formulario
4. Por defecto se creará como `worker`

### Opción 2: Usando la API
```bash
curl -X POST http://localhost:4500/rupture/createUser \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "juan@example.com",
    "identification": "12345678",
    "password": "password123",
    "rol": "worker"
  }'
```

### Opción 3: Crear SuperAdmin desde la API
```bash
curl -X POST http://localhost:4500/rupture/createSuperAdmin \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Admin",
    "last_name": "Principal",
    "email": "admin@example.com",
    "identification": "87654321",
    "password": "admin123"
  }'
```

---

## 🔧 Solución de Problemas

### Error: "No se puede conectar a MongoDB"
```bash
# Verificar que MongoDB esté corriendo
# En Linux/Mac:
systemctl status mongod

# En Windows:
net start MongoDB

# Con Docker:
docker ps | grep mongo
```

### Error: "Usuario con cédula ya existente"
La identificación debe ser única. Usa otra identificación diferente.

### Error: "Usuario deshabilitado"
Un SuperAdmin debe habilitar tu cuenta desde el panel de administración.

### Cambiar Contraseña de Usuario
Solo SuperAdmin puede cambiar contraseñas desde el panel de administración:
1. Login como SuperAdmin
2. Ir a "Administración"
3. Buscar el usuario
4. Hacer clic en "Cambiar Contraseña"

---

## 📚 Estructura del Proyecto

```
RuptureLakes/
├── src/
│   ├── functions/        # Lógica de negocio
│   │   ├── users.py      # CRUD de usuarios
│   │   ├── events.py     # CRUD de eventos
│   │   └── modelos.py    # Cálculos de ruptura
│   ├── models/           # Esquemas MongoDB
│   │   ├── users.py      # Esquema de usuarios
│   │   └── eventos.py    # Esquema de eventos
│   ├── web/
│   │   ├── routes.py     # Rutas web de Flask
│   │   ├── templates/    # Templates HTML
│   │   └── static/       # CSS, JS, imágenes
│   └── main.py           # Punto de entrada Flask
├── initialization.py     # Script de inicialización DB
├── create_superadmin.py  # Script para crear SuperAdmin
├── requirements.txt      # Dependencias Python
├── docker-compose.yml    # Configuración Docker
├── Dockerfile            # Imagen Docker de Flask
└── .env                  # Variables de entorno (NO subir a git)
```

---

## 🔐 Seguridad

1. **Contraseñas**: Se hashean con bcrypt antes de guardarlas
2. **Validación de roles**: MongoDB valida que solo se usen roles permitidos
3. **Control de acceso**: Las rutas verifican el rol antes de permitir acciones

### Recomendaciones:
- Usa contraseñas fuertes (mínimo 6 caracteres, idealmente 12+)
- No compartas credenciales de SuperAdmin
- Cambia las contraseñas por defecto en producción
- Usa HTTPS en producción

---

## 📊 Endpoints de la API

### Usuarios
- `GET /rupture/getUsers` - Obtener todos los usuarios
- `POST /rupture/createUser` - Crear usuario worker
- `POST /rupture/createSuperAdmin` - Crear SuperAdmin
- `POST /rupture/deleteUser` - Eliminar usuario
- `POST /rupture/updateUser` - Actualizar usuario
- `POST /rupture/login` - Iniciar sesión

### Eventos
- `GET /rupture/getEvents` - Obtener todos los eventos
- `POST /rupture/getSpecificEvent` - Buscar evento por orden
- `POST /rupture/createEvent` - Crear nuevo evento
- `POST /rupture/deleteEvent` - Eliminar evento
- `POST /rupture/updateEvent` - Actualizar evento

---

## 📞 Soporte

Si encuentras problemas:
1. Verifica que MongoDB esté corriendo
2. Revisa los logs de la aplicación
3. Verifica las variables de entorno en `.env`
4. Consulta este documento

---

**Última actualización**: 2025-01-21
