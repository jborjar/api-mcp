# Changelog - Sistema de Inicialización de Datos

Todos los cambios notables en el sistema de inicialización de datos se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [2.1.0] - 2026-01-21

### 🎉 Sistema de Proveedores Activos

Esta versión agrega la capacidad de consultar proveedores activos de forma eficiente, respetando el modo actual (productivo/pruebas).

### Added (Agregado)

- **Función `get_proveedores_activos()` en database.py**
  - Consulta proveedores con `Valid='Y'` AND `Frozen='N'`
  - Respeta el modo actual (productivo/pruebas)
  - Usa `get_instancias_con_service_layer()` para obtener instancias según modo
  - Soporte para filtro por instancia específica
  - Soporte para paginación con `limit` y `offset`
  - Retorna total de proveedores activos
  - Retorna lista de instancias incluidas en la consulta

- **Nuevo Endpoint: GET /proveedores/activos**
  - Consulta proveedores activos desde SAP_PROVEEDORES
  - Query parameters: `instancia`, `limit`, `offset`
  - Requiere autenticación
  - Documentación completa en OpenAPI/Swagger

### Documentation (Documentación)

- Creado `proveedores_activos.md` (~800 líneas)
  - Arquitectura del sistema
  - Criterios de "proveedor activo"
  - Ejemplos de uso completos
  - Casos de uso reales
  - Testing manual paso a paso
  - Troubleshooting
  - Performance y optimización

- Actualizado `tests/README.md`
  - Agregada sección "Sistema de Proveedores"
  - Referencia al nuevo documento

### Performance (Rendimiento)

- **Consulta de proveedores activos:**
  - Modo productivo (21 instancias): < 200ms para ~12,200 proveedores
  - Modo pruebas (6 instancias): < 50ms para ~1,350 proveedores
  - Filtro por instancia: < 30ms

### Use Cases (Casos de Uso)

1. **Frontend**: Selector de proveedores para formularios de compra
2. **Integración**: Sincronización con sistemas externos
3. **Reportes**: Estadísticas de proveedores activos por instancia
4. **Auditoría**: Identificar instancias con alto porcentaje de inactivos

---

## [2.0.0] - 2026-01-21

### 🎉 Versión Mayor - Sistema Asíncrono con Job Tracking

Esta versión introduce un rediseño completo del sistema de inicialización, resolviendo el problema crítico de timeout en gateways y agregando soporte para sincronización de proveedores SAP.

### Added (Agregado)

- **Sistema de Job Tracking Asíncrono**
  - Variable global `initialization_jobs` para almacenar estado de jobs
  - Lock thread-safe (`jobs_lock`) para operaciones concurrentes
  - Función `_run_inicializa_datos_background()` para ejecución en background
  - Estados de job: `pending`, `running`, `completed`, `failed`
  - Seguimiento de progreso en tiempo real con mensajes descriptivos

- **Nuevo Endpoint: GET /inicializa_datos/status/{job_id}**
  - Consulta estado y progreso de jobs de inicialización
  - Retorna resultados completos cuando el job termina
  - Manejo de errores detallado

- **Tabla SAP_PROVEEDORES**
  - Esquema: Instancia, CardCode, CardName, CardType, LicTradNum, Phone1, E_Mail
  - Primary key compuesta: (Instancia, CardCode)
  - Creación automática en `inicializa_sap_empresas()`

- **Función `actualizar_sap_proveedores()`**
  - Sincroniza proveedores desde todas las instancias con Service Layer
  - Operación MERGE: update/insert/delete
  - Soporte para modo productivo y modo pruebas
  - Retorna métricas detalladas por instancia

- **Vistas SQL Dinámicas**
  - `vw_productivo`: Instancias con SL=1
  - `vw_pruebas`: Instancias con SLP=1 AND Prueba=1
  - Creadas automáticamente en `inicializa_sap_empresas()`
  - Uso de `CREATE OR ALTER VIEW` para idempotencia

- **Función `get_instancias_con_service_layer()`**
  - Obtiene instancias según modo actual (productivo/pruebas)
  - Usa vistas SQL en lugar de queries directas
  - Retorna lista de nombres de instancias

- **Mejoras en `enviar_correo_inicializacion()`**
  - Soporte para nuevo formato de `service_layer_result` (productivo/pruebas)
  - Inclusión de resultados de `sap_proveedores` en el email
  - Backward compatibility con formato antiguo

### Changed (Cambiado)

- **Endpoint POST /inicializa_datos**
  - Ahora usa `BackgroundTasks` de FastAPI
  - Retorna `job_id` inmediatamente (< 1 segundo)
  - Ya no retorna resultados directamente (usar `/status/{job_id}`)
  - Preservación de sesión movida al background task

- **Función `inicializa_sap_empresas()`**
  - Agregada creación de tabla `SAP_PROVEEDORES`
  - Agregada creación de vistas `vw_productivo` y `vw_pruebas`
  - Actualizada documentación del docstring

- **Función `test_service_layer_all_instances()`**
  - Nuevo parámetro `skip_email=True` para evitar envío duplicado de emails
  - Retorna formato nuevo con `productivo` y `pruebas` separados
  - Backward compatibility con formato antiguo

### Fixed (Corregido)

- **Error 504 Gateway Timeout**
  - Resuelto mediante ejecución asíncrona
  - El cliente ya no espera 5+ minutos por la respuesta
  - Compatible con todos los gateways (Cloudflare, Nginx, etc.)

- **Uso incorrecto de SAP_EMPRESAS en lugar de vistas**
  - `get_instancias_con_service_layer()` ahora usa `vw_productivo`/`vw_pruebas`
  - Asegura consistencia entre modos productivo y pruebas

### Performance (Rendimiento)

- **Tiempo de respuesta inicial**: Reducido de ~5 minutos a < 1 segundo
- **Sincronización de proveedores**: 13,199 registros en ~2 minutos
- **Service Layer tests**: Continúa siendo paralelo (max 10 workers)

### Documentation (Documentación)

- Creado `prueba_inicializa_datos_async_completo.md` (versión 2.0)
- Actualizado `prueba_inicializa_datos_session_preservation.md` (marcado como v1.0 obsoleto)
- Creado `tests/README.md` (índice general)
- Creado `tests/CHANGELOG.md` (este archivo)

### Testing (Pruebas)

- ✅ Prueba completa de inicialización asíncrona
- ✅ Verificación de job tracking (pending → running → completed)
- ✅ Sincronización de 13,199 proveedores
- ✅ Preservación de sesión en background task
- ✅ Email enviado correctamente con nuevos resultados

---

## [1.1.0] - 2026-01-21

### Added

- **Función `test_service_layer_all_instances()`**
  - Prueba paralela de Service Layer para todas las instancias
  - Actualización de campos SL y SLP en SAP_EMPRESAS
  - Soporte para instancias productivas y de pruebas
  - ThreadPoolExecutor con max 10 workers
  - Timeouts individuales por instancia (60 segundos)

- **Campos en tabla SAP_EMPRESAS**
  - `SL BIT`: Indica si Service Layer productivo está disponible
  - `SLP BIT`: Indica si Service Layer de pruebas está disponible
  - `Prueba BIT`: Indica si existe versión _PRUEBAS de la instancia

### Changed

- **Endpoint POST /inicializa_datos**
  - Ahora llama a `test_service_layer_all_instances()` con `skip_email=True`
  - Envía un solo email con todos los resultados al final

- **Función `inicializa_sap_empresas()`**
  - Actualizada para marcar campo `Prueba=1` si existe instancia_PRUEBAS

### Performance

- **Pruebas de Service Layer**: Reducido de ~5 minutos (serial) a ~1 minuto (paralelo)

---

## [1.0.0] - 2026-01-21

### 🎉 Versión Inicial - Preservación de Sesión

Primera versión del sistema de inicialización con preservación automática de sesión.

### Added

- **Función `inicializa_sap_empresas()`**
  - Elimina y recrea base de datos completa
  - Crea tabla SAP_EMPRESAS
  - Crea tabla USER_SESSIONS
  - Obtiene empresas desde SAP HANA
  - Inserta registros en SAP_EMPRESAS

- **Función `ensure_sessions_table_exists()` en session.py**
  - Crea base de datos si no existe
  - Crea tabla USER_SESSIONS si no existe
  - Permite autenticación incluso sin base de datos previa

- **Endpoint POST /inicializa_datos**
  - Requiere autenticación (token JWT)
  - Guarda información de sesión antes de eliminar BD
  - Ejecuta inicialización de empresas
  - Restaura sesión del usuario con mismo SessionID
  - Retorna resultados con `session_restored: true`

### Fixed

- **Invalidación de token durante inicialización**
  - La sesión del usuario se preserva automáticamente
  - El token JWT permanece válido después de la operación
  - No se requiere login nuevamente

### Documentation

- Creado `prueba_inicializa_datos_session_preservation.md`
- Documentados escenarios cubiertos
- Documentadas pruebas realizadas

### Testing

- ✅ Escenario 1: Base de datos no existe → Login exitoso
- ✅ Escenario 2: Base de datos existe → Sesión preservada
- ✅ Escenario 3: Múltiples ejecuciones → Token siempre válido

---

## [0.1.0] - 2026-01-20 (Versión Pre-release)

### Added

- Estructura básica del proyecto
- Conexión a MSSQL
- Conexión a SAP HANA
- Sistema de autenticación con JWT
- Sistema de sesiones con tabla USER_SESSIONS

### Known Issues

- ❌ El token se invalida al ejecutar `/inicializa_datos`
- ❌ No existe sincronización de proveedores
- ❌ Timeout en gateways para operaciones largas

---

## Comparación de Versiones

| Característica | v0.1.0 | v1.0.0 | v1.1.0 | v2.0.0 | v2.1.0 |
|----------------|--------|--------|--------|--------|--------|
| Inicialización de BD | ✅ | ✅ | ✅ | ✅ | ✅ |
| Preservación de sesión | ❌ | ✅ | ✅ | ✅ | ✅ |
| Service Layer tests | ❌ | ❌ | ✅ (paralelo) | ✅ (paralelo) | ✅ (paralelo) |
| SAP_PROVEEDORES | ❌ | ❌ | ❌ | ✅ | ✅ |
| Vistas SQL (productivo/pruebas) | ❌ | ❌ | ❌ | ✅ | ✅ |
| Ejecución asíncrona | ❌ | ❌ | ❌ | ✅ | ✅ |
| Job tracking | ❌ | ❌ | ❌ | ✅ | ✅ |
| Sin timeout 504 | ❌ | ❌ | ❌ | ✅ | ✅ |
| Consulta proveedores activos | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Roadmap

### v2.1.0 ✅ COMPLETADO (2026-01-21)

**Mejoras al Job Tracking:**
- [x] Limpieza automática de jobs antiguos (> 24 horas)
- [x] Endpoint para listar todos los jobs
- [ ] Persistencia de jobs en base de datos (pospuesto a v2.2.0)
- [ ] Endpoint para cancelar jobs en ejecución (pospuesto a v2.2.0)

**Sistema de Proveedores Activos:**
- [x] Endpoint GET /proveedores/activos
- [x] Filtro por instancia
- [x] Paginación (limit/offset)
- [x] Respeto del modo productivo/pruebas
- [x] Documentación completa

### v2.2.0 (Planificado)

**Mejoras al Job Tracking:**
- [ ] Persistencia de jobs en base de datos
- [ ] Endpoint para cancelar jobs en ejecución

**Mejoras a Proveedores:**
- [ ] Filtros adicionales (CardName, FederalTaxID, GroupCode)
- [ ] Ordenamiento personalizable
- [ ] Endpoint de estadísticas
- [ ] Export a Excel/CSV

**Mejoras a la Sincronización:**
- [ ] Sincronización incremental de proveedores (solo cambios)
- [ ] Sincronización de clientes (CardType='C')
- [ ] Campos adicionales de BusinessPartners
- [ ] Retry automático en caso de error temporal

### v3.0.0 (Planificado)

**Notificaciones en Tiempo Real:**
- [ ] WebSocket para notificaciones de progreso
- [ ] Server-Sent Events (SSE) como alternativa
- [ ] Webhooks para integración con otros sistemas

**Scheduling:**
- [ ] Sincronización programada (cron)
- [ ] Configuración de horarios por instancia
- [ ] Sincronización nocturna automática

### v3.1.0 (Planificado)

**Auditoría y Reportes:**
- [ ] Tabla de auditoría de sincronizaciones
- [ ] Dashboard de métricas
- [ ] Reportes de cambios (diff)
- [ ] Alertas automáticas por email

---

## Convenciones

Este changelog sigue las siguientes convenciones:

**Categorías de cambios:**
- `Added`: Nuevas funcionalidades
- `Changed`: Cambios en funcionalidades existentes
- `Deprecated`: Funcionalidades marcadas como obsoletas
- `Removed`: Funcionalidades eliminadas
- `Fixed`: Correcciones de bugs
- `Security`: Correcciones de seguridad
- `Performance`: Mejoras de rendimiento
- `Documentation`: Cambios en documentación
- `Testing`: Cambios en pruebas

**Formato de versiones:**
- MAJOR.MINOR.PATCH (ejemplo: 2.0.0)
- MAJOR: Cambios incompatibles en la API
- MINOR: Nuevas funcionalidades (compatible)
- PATCH: Correcciones de bugs (compatible)

**Emojis:**
- 🎉 Versión mayor o hito importante
- ✅ Característica completa y probada
- ❌ Problema conocido o funcionalidad faltante
- ⚠️ Advertencia o deprecación

---

**Última actualización:** 2026-01-21
**Versión actual:** 2.0.0
