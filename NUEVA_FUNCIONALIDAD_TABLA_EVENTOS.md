# 📊 Nueva Funcionalidad: Tabla de Visualización de Eventos

## ✨ Resumen de Cambios

Se agregó una nueva página de **Visualización de Eventos** con tabla interactiva, búsqueda avanzada y control de permisos por roles.

---

## 🎯 Características Principales

### 1. **Tabla Interactiva con DataTables**
- ✅ **Búsqueda en tiempo real** - Filtra por cualquier campo de la tabla
- ✅ **Ordenamiento** - Haz clic en cualquier columna para ordenar
- ✅ **Paginación** - Configura cuántos eventos ver (10, 25, 50, 100 o todos)
- ✅ **Responsive** - Se adapta a móviles y tablets
- ✅ **Exportación** - Soporte para copiar y exportar datos

### 2. **Panel de Estadísticas**
En la parte superior de la tabla verás 4 tarjetas con:
- 📋 **Total de Eventos** - Número total de eventos registrados
- ✅ **Eventos Aprobados** - Eventos con estado "aprobado"
- ⏰ **Eventos Pendientes** - Eventos sin aprobar
- 💧 **Volumen Total** - Suma de todos los volúmenes en m³

### 3. **Columnas de la Tabla**
| Columna | Descripción |
|---------|-------------|
| Orden | Número de orden del evento |
| Fecha Inicio | Fecha y hora de inicio de la fuga |
| Ubicación | Coordenadas geográficas |
| Volumen (m³) | Volumen total calculado |
| Flujo (m³/h) | Flujo calculado |
| Presión (psig) | Presión de la tubería |
| Duración (hrs) | Duración del evento en horas |
| Forma | Tipo de ruptura (circular, recta, total) |
| Estado | Aprobado o Pendiente |
| Acciones | Botones de acción según permisos |

### 4. **Control de Permisos por Rol**

#### 👷 **Worker**
- ✅ Ver la tabla completa de eventos
- ✅ Buscar y filtrar eventos
- ✅ Ver detalles de eventos (botón "Ver")
- ❌ **NO** puede editar eventos
- ❌ **NO** puede eliminar eventos
- ❌ **NO** puede descargar todos los eventos

#### 👑 **SuperAdmin**
- ✅ Todo lo que puede hacer Worker
- ✅ **Editar** eventos (botón "Editar")
- ✅ **Eliminar** eventos (botón "Eliminar" con confirmación)
- ✅ **Descargar** todos los eventos en Excel

---

## 🚀 Cómo Acceder

### Opción 1: Desde el Menú Principal
1. Iniciar sesión
2. En la pantalla principal verás el botón: **"📊 Tabla de eventos"**
3. Hacer clic para acceder

### Opción 2: Desde Búsqueda de Eventos
1. Ir a **"Visualizar evento"** (o **"Buscar evento"**)
2. Verás un botón: **"📊 Ver Todos los Eventos"**
3. Hacer clic para acceder a la tabla completa

### Opción 3: URL Directa
```
http://localhost:4500/VisualizarEventos
```

---

## 📝 Uso de la Tabla

### Búsqueda y Filtrado
1. **Búsqueda Global**: Usa el campo de búsqueda en la parte superior derecha
   - Busca por: orden, ubicación, forma, estado, etc.
   - Actualiza en tiempo real mientras escribes

2. **Ordenamiento**: Haz clic en cualquier encabezado de columna
   - Primera vez: orden ascendente ⬆️
   - Segunda vez: orden descendente ⬇️
   - Tercera vez: vuelve al orden original

3. **Paginación**: Controla cuántos eventos ver por página
   - Selector en la parte superior izquierda
   - Opciones: 10, 25, 50, 100 o "Todos"

### Acciones en los Eventos

#### 👁️ Ver Evento (Todos los usuarios)
1. Hacer clic en el botón **"👁️ Ver"**
2. Se abrirá la página de reporte detallado del evento

#### ✏️ Editar Evento (Solo SuperAdmin)
1. Hacer clic en el botón **"✏️ Editar"**
2. Se abrirá el formulario de edición
3. Modificar los datos necesarios
4. Guardar cambios

#### 🗑️ Eliminar Evento (Solo SuperAdmin)
1. Hacer clic en el botón **"🗑️ Eliminar"**
2. Aparecerá un modal de confirmación
3. Confirmar la eliminación
4. El evento se eliminará de la base de datos
5. La tabla se actualiza automáticamente

**⚠️ IMPORTANTE**: La eliminación es permanente y no se puede deshacer.

---

## 🔧 Archivos Modificados/Creados

### Archivos Nuevos
1. **`src/web/templates/visualizar_eventos.html`**
   - Template principal con la tabla
   - Incluye DataTables, Bootstrap 5 y Font Awesome
   - JavaScript para manejar acciones

### Archivos Modificados
1. **`src/web/routes.py`**
   - Nueva ruta: `/VisualizarEventos`
   - Control de permisos por rol
   - Formateo de datos para la tabla

2. **`src/functions/events.py`**
   - Función `deleteEvent()` actualizada
   - Ahora acepta tanto `_id` como `orden` para eliminar

3. **`src/web/templates/principal.html`**
   - Nuevo botón: "📊 Tabla de eventos"
   - Iconos agregados a todos los botones
   - Botón "Crear admin" ahora oculto por defecto

4. **`src/web/templates/buscar.html`**
   - Título actualizado: "Búsqueda de Eventos"
   - Nuevo botón: "📊 Ver Todos los Eventos"
   - Descripción mejorada
   - Placeholder en campo de búsqueda

---

## 💻 Tecnologías Utilizadas

- **Backend**: Flask, Python
- **Frontend**: Bootstrap 5.3.2
- **Tabla**: DataTables 1.13.7 con extensiones responsive
- **Iconos**: Font Awesome 6
- **Base de datos**: MongoDB
- **Idioma tabla**: Español (es-ES)

---

## 🎨 Diseño y UX

### Características de Diseño
- **Responsive**: Se adapta a cualquier tamaño de pantalla
- **Fondo translúcido**: La tabla tiene fondo blanco semi-transparente sobre la imagen de fondo
- **Gradiente en header**: Header con gradiente púrpura/azul moderno
- **Badges de estado**: Colores distintivos para estados (verde=aprobado, amarillo=pendiente)
- **Hover effects**: Las filas se resaltan al pasar el mouse
- **Loading overlay**: Indicador de carga al eliminar eventos
- **Modal de confirmación**: Previene eliminaciones accidentales

### Paleta de Colores
- **Header**: Gradiente púrpura-azul (#667eea → #764ba2)
- **Aprobado**: Verde (#28a745)
- **Pendiente**: Amarillo (#ffc107)
- **Ver**: Azul (#0d6efd)
- **Editar**: Amarillo/Naranja (#ffc107)
- **Eliminar**: Rojo (#dc3545)

---

## 🔐 Seguridad

1. **Autenticación**: Solo usuarios autenticados pueden acceder
2. **Validación de rol**: Se verifica el rol antes de mostrar botones
3. **Confirmación de eliminación**: Modal previene eliminaciones accidentales
4. **Backend seguro**: Las rutas verifican permisos en el servidor

---

## 📈 Estadísticas Dinámicas

Las estadísticas en la parte superior se actualizan automáticamente:
- Al cargar la página
- Al eliminar un evento
- Al cambiar filtros (próximamente)

---

## 🚨 Mensajes de Error/Éxito

### Eliminación Exitosa
```
✓ Evento eliminado exitosamente
```

### Error al Eliminar
```
✗ Error al eliminar el evento: [mensaje de error]
```

### Sin Resultados
La tabla muestra automáticamente "No se encontraron registros" cuando no hay eventos que coincidan con la búsqueda.

---

## 📱 Compatibilidad

### Navegadores Soportados
- ✅ Chrome/Edge (últimas versiones)
- ✅ Firefox (últimas versiones)
- ✅ Safari (últimas versiones)
- ✅ Opera (últimas versiones)

### Dispositivos
- ✅ Desktop (Windows, Mac, Linux)
- ✅ Tablets (iPad, Android tablets)
- ✅ Móviles (iPhone, Android)

---

## 🐛 Solución de Problemas

### La tabla no carga
1. Verificar que estés autenticado
2. Verificar que MongoDB esté corriendo
3. Revisar la consola del navegador (F12)

### Botones de acción no aparecen
1. Verificar tu rol de usuario
2. Workers solo ven el botón "Ver"
3. SuperAdmin ven "Ver", "Editar" y "Eliminar"

### Error al eliminar evento
1. Verificar que seas SuperAdmin
2. Verificar que el evento exista
3. Revisar logs del servidor

### La búsqueda no funciona
1. Limpiar caché del navegador
2. Recargar la página (Ctrl+F5)
3. Verificar JavaScript habilitado

---

## 🔄 Próximas Mejoras (Roadmap)

- [ ] Exportar tabla a PDF
- [ ] Filtros avanzados por fecha
- [ ] Gráficos de estadísticas
- [ ] Edición inline (sin cambiar de página)
- [ ] Selección múltiple para acciones en batch
- [ ] Historial de cambios en eventos

---

## 📞 Soporte

Si encuentras algún problema:
1. Verifica que todas las dependencias estén instaladas
2. Revisa los logs del servidor
3. Verifica tu rol de usuario
4. Consulta este documento

---

**Última actualización**: 2025-01-21
**Versión**: 1.0.0
