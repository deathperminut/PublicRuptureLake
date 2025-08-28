# RuptureLakes - Sistema de Gestión de Eventos de Ruptura en Gasoductos

Sistema web para la gestión y análisis de eventos de ruptura en sistemas de transporte de gas natural, desarrollado con Flask y MongoDB.

## 🚀 Características Principales

- **Gestión de Eventos**: Registro complejo de eventos de ruptura con cálculos automatizados
- **Carga Masiva**: Sistema de carga masiva mediante archivos Excel con validaciones
- **Sistema de Roles**: Control de acceso basado en roles (SuperAdmin, worker, user)
- **Análisis Avanzado**: Cálculos de flujo, volumen y características de ruptura
- **Reportes**: Generación y descarga de reportes en Excel
- **Interfaz Intuitiva**: UI moderna con Bootstrap y JavaScript

## 📋 Requisitos Previos

- Docker y Docker Compose instalados
- Git para clonar el repositorio
- Puerto 4500 disponible para la aplicación web
- Puerto 27017 disponible para MongoDB

## 🛠️ Instalación y Configuración

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd RuptureLakes
```

### 2. Configuración de Variables de Entorno

```bash
# Copiar el archivo de ejemplo
cp .env.docker.example .env.docker

# Editar las credenciales (IMPORTANTE: cambiar las contraseñas por defecto)
nano .env.docker
```

**Variables importantes a configurar:**
```env
MONGO_INITDB_ROOT_USERNAME=root
MONGO_INITDB_ROOT_PASSWORD=tu_contraseña_segura
MONGO_USERNAME=root  
MONGO_PASSWORD=tu_contraseña_segura
MONGO_DATABASE=rupture
FLASK_PORT=4500
FLASK_DEBUG=false
```

### 3. Ejecutar la Aplicación

```bash
# Construir y ejecutar los contenedores
docker-compose --env-file .env.docker up --build

# Para ejecutar en segundo plano
docker-compose --env-file .env.docker up -d --build
```

### 4. Acceder a la Aplicación

- **URL**: http://localhost:4500
- **Base de datos**: MongoDB corriendo en puerto 27017

## 👥 Sistema de Roles y Usuarios

### Roles Disponibles

#### **SuperAdmin**
- **Permisos**: Acceso completo al sistema
- **Funcionalidades**:
  - ✅ Crear, editar y eliminar eventos
  - ✅ Acceso a panel de administración de usuarios
  - ✅ Carga masiva de eventos
  - ✅ Descargar reportes completos
  - ✅ Crear nuevos administradores
  - ✅ Gestionar roles de usuarios

#### **worker**
- **Permisos**: Usuario operativo con capacidades de carga
- **Funcionalidades**:
  - ✅ Crear y editar eventos
  - ✅ Carga masiva de eventos  
  - ✅ Visualizar eventos existentes
  - ❌ Panel de administración
  - ❌ Gestión de usuarios

#### **user**
- **Permisos**: Usuario básico con permisos de consulta
- **Funcionalidades**:
  - ✅ Crear eventos básicos
  - ✅ Visualizar eventos propios
  - ❌ Carga masiva
  - ❌ Panel de administración
  - ❌ Acceso a reportes completos

### Primer Acceso

1. **Registro inicial**: Registra el primer usuario a través de la interfaz web
2. **Configurar SuperAdmin**: El primer usuario no tiene rol automático, debes editarlo manualmente en la base de datos:
   ```bash
   # Acceder a MongoDB
   docker-compose --env-file .env.docker exec mongodb mongosh -u root -p
   
   # En MongoDB shell:
   use rupture
   db.users.updateOne(
     {"email": "tu_email@ejemplo.com"}, 
     {"$set": {"rol": "SuperAdmin"}}
   )
   ```
3. **Creación de usuarios**: Los SuperAdmin pueden crear nuevos usuarios desde el panel de administración
4. **Asignación de roles**: Los roles se asignan desde el panel de administración

## 📊 Funcionalidades del Sistema

### 1. Gestión de Eventos

**Datos requeridos para un evento:**
- Número de orden único
- Ubicación (coordenadas GPS)
- Presión de operación y unidades
- Características de tubería (diámetro, material)
- Tipo y dimensiones de ruptura
- Fechas de inicio y fin del evento
- Direccionalidad del flujo

**Cálculos automatizados:**
- Flujo de gas en condiciones de ruptura
- Volumen total fugado
- Volumen muerto del sistema
- Presión atmosférica según elevación
- Área y perímetro de ruptura

### 2. Carga Masiva

**Proceso paso a paso:**
1. **Descargar formato**: Excel con múltiples hojas
   - Hoja principal con campos de ejemplo
   - Opciones válidas para campos selectivos
   - Diámetros de tubería comunes
   - Instrucciones detalladas

2. **Llenar datos**: Completar Excel siguiendo las validaciones
3. **Subir archivo**: Drag & drop o selección manual
4. **Procesamiento**: Validación y creación automática de eventos

**Validaciones incluidas:**
- Campos obligatorios completos
- Formatos de fecha correctos
- Valores numéricos válidos
- Opciones de dropdown correctas
- Órdenes únicas (no duplicadas)

### 3. Sistema de Reportes

- **Descarga individual**: Por número de orden
- **Reportes masivos**: Solo para SuperAdmin
- **Formato Excel**: Con cálculos y metadatos completos

## 🗂️ Estructura del Proyecto

```
RuptureLakes/
├── src/
│   ├── main.py                 # Punto de entrada
│   ├── web/
│   │   ├── routes.py           # Rutas y lógica web
│   │   └── templates/          # Plantillas HTML
│   ├── functions/
│   │   ├── events.py           # CRUD de eventos
│   │   ├── conect.py           # Conexión MongoDB
│   │   ├── modelos.py          # Modelos y cálculos
│   │   └── users.py            # Gestión de usuarios
│   └── models/                 # Modelos adicionales
├── docker-compose.yml          # Configuración Docker
├── Dockerfile                  # Imagen de la aplicación
├── requirements.txt            # Dependencias Python
└── .env.docker.example         # Variables de entorno ejemplo
```

## 🔧 Comandos Útiles

### Docker

```bash
# Ver logs de la aplicación
docker-compose logs -f web

# Ver logs de MongoDB
docker-compose logs -f mongodb

# Reiniciar servicios
docker-compose restart

# Detener servicios
docker-compose down

# Limpiar volúmenes (⚠️ Elimina datos de BD)
docker-compose down -v
```

### Base de Datos

```bash
# Acceder a MongoDB
docker-compose exec mongodb mongosh -u root -p

# Backup de base de datos
docker-compose exec mongodb mongodump --username root --password tu_contraseña --authenticationDatabase admin --db rupture --out /backup

# Restaurar base de datos
docker-compose exec mongodb mongorestore --username root --password tu_contraseña --authenticationDatabase admin --db rupture /backup/rupture
```

## 🐛 Solución de Problemas

### Configuración Inicial de SuperAdmin

Si necesitas asignar rol SuperAdmin a un usuario existente:

```bash
# 1. Acceder a MongoDB
docker-compose --env-file .env.docker exec mongodb mongosh -u root -p

# 2. En el shell de MongoDB:
use rupture

# 3. Ver usuarios existentes
db.users.find({}, {"email": 1, "nombre1": 1, "rol": 1})

# 4. Asignar rol SuperAdmin (reemplaza con el email correcto)
db.users.updateOne(
  {"email": "usuario@ejemplo.com"}, 
  {"$set": {"rol": "SuperAdmin"}}
)

# 5. Verificar el cambio
db.users.findOne({"email": "usuario@ejemplo.com"}, {"email": 1, "rol": 1})
```

### Error de Conexión a MongoDB
```bash
# Verificar que MongoDB esté ejecutándose
docker-compose ps

# Revisar logs de MongoDB
docker-compose logs mongodb
```

### Error de Permisos
```bash
# Asegurar permisos de directorio
sudo chown -R $USER:$USER ./mongo_data
```

### Puerto en Uso
```bash
# Verificar puertos ocupados
netstat -tulpn | grep :4500
netstat -tulpn | grep :27017

# Cambiar puerto en .env.docker si es necesario
FLASK_PORT=4501
```

## 🔐 Seguridad

### Recomendaciones de Producción

1. **Cambiar credenciales por defecto**:
   ```env
   MONGO_INITDB_ROOT_PASSWORD=contraseña_muy_segura
   MONGO_PASSWORD=contraseña_muy_segura
   ```

2. **Configurar HTTPS**: Usar proxy reverso (nginx/Apache)

3. **Backup regular**: Configurar copias de seguridad automáticas

4. **Firewall**: Restringir acceso a puertos 4500 y 27017

5. **Monitoreo**: Implementar logs y alertas

## 📝 Notas de Desarrollo

### Agregar Nuevas Funcionalidades

1. **Rutas**: Agregar en `src/web/routes.py`
2. **Templates**: Crear en `src/web/templates/`
3. **Cálculos**: Extender `src/functions/modelos.py`
4. **Base de datos**: Modificar `src/functions/events.py`

### Testing

```bash
# Ejecutar tests (si están configurados)
docker-compose exec web python -m pytest

# Verificar sintaxis Python
docker-compose exec web python -m py_compile src/main.py
```

## 📞 Soporte

Para problemas o preguntas sobre el sistema:

1. Revisar logs con `docker-compose logs -f`
2. Verificar configuración en `.env.docker`
3. Consultar esta documentación
4. Contactar al equipo de desarrollo

---

**Desarrollado por**: Equipo EFIGAS  
**Versión**: 2.0  
**Última actualización**: 2024