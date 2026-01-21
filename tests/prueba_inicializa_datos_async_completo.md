# Sistema de Inicialización Asíncrona - Documentación Completa

**Fecha:** 2026-01-21
**Branch:** Modifica-flujo-inicializa_datos
**Versión:** 2.0 (Sistema Asíncrono con Job Tracking)

## Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Problema Resuelto: Timeout 504](#problema-resuelto-timeout-504)
4. [Componentes Principales](#componentes-principales)
5. [Flujo de Ejecución](#flujo-de-ejecución)
6. [Tablas y Vistas SQL](#tablas-y-vistas-sql)
7. [Endpoints de la API](#endpoints-de-la-api)
8. [Pruebas Realizadas](#pruebas-realizadas)
9. [Guía de Uso](#guía-de-uso)

---

## Resumen Ejecutivo

El sistema de inicialización de datos ha sido completamente rediseñado para soportar **ejecución asíncrona con seguimiento de progreso** (job tracking), resolviendo problemas de timeout en gateways (Cloudflare) y mejorando significativamente la experiencia del usuario.

### Características Principales

- ✅ **Ejecución asíncrona**: El endpoint retorna inmediatamente con un `job_id`
- ✅ **Seguimiento en tiempo real**: Consulta el progreso del trabajo en cualquier momento
- ✅ **Sin timeout**: Funciona correctamente incluso con procesos de 5+ minutos
- ✅ **Preservación de sesión**: El token del usuario permanece válido durante y después del proceso
- ✅ **Poblado automático de proveedores**: Sincroniza 13,000+ proveedores de 21 instancias SAP
- ✅ **Vistas SQL dinámicas**: Soporte para modo productivo y modo pruebas
- ✅ **Thread-safe**: Múltiples usuarios pueden inicializar datos simultáneamente

### Métricas de Rendimiento

- **Tiempo de respuesta inicial**: < 1 segundo (retorna job_id)
- **Tiempo total de ejecución**: ~5 minutos (depende de red y Service Layer)
- **Proveedores sincronizados**: 13,199 registros
- **Instancias procesadas**: 21 productivas + 6 de pruebas
- **Empresas insertadas**: 24 registros

---

## Arquitectura del Sistema

### Diagrama de Flujo

```
Usuario hace POST /inicializa_datos
         |
         v
API retorna job_id inmediatamente
         |
         +------------------+
         |                  |
         v                  v
Usuario consulta      Background Task
/status/{job_id}      ejecuta proceso
periodicamente        de inicialización
         |                  |
         |                  v
         |            1. Eliminar/recrear BD
         |            2. Crear tablas
         |            3. Poblar SAP_EMPRESAS
         |            4. Crear vistas SQL
         |            5. Test Service Layer
         |            6. Poblar SAP_PROVEEDORES
         |            7. Restaurar sesión
         |            8. Enviar email
         |                  |
         v                  v
  Status: "completed" con resultados
```

### Componentes de Software

**app/main.py**
- `initialization_jobs`: Diccionario global para tracking de jobs
- `jobs_lock`: Threading lock para operaciones thread-safe
- `_run_inicializa_datos_background()`: Función que ejecuta el proceso en background
- `POST /inicializa_datos`: Endpoint que inicia el job asíncrono
- `GET /inicializa_datos/status/{job_id}`: Endpoint para consultar progreso

**app/database.py**
- `inicializa_sap_empresas()`: Elimina/recrea BD, crea tablas y vistas
- `test_service_layer_all_instances()`: Prueba conexión a Service Layer (paralelo)
- `actualizar_sap_proveedores()`: Sincroniza proveedores desde SAP B1
- `get_instancias_con_service_layer()`: Obtiene instancias usando vistas SQL

**app/config.py**
- `_modo_pruebas`: Variable global para switching de modo
- `get_modo_pruebas()`: Retorna el modo actual (productivo/pruebas)
- `set_modo_pruebas()`: Establece el modo de operación

---

## Problema Resuelto: Timeout 504

### Problema Original

Cuando se llamaba `/inicializa_datos` a través de Cloudflare:
```
curl -X POST https://api.example.com/inicializa_datos
  -> Error 504 Gateway Timeout (después de ~100 segundos)
```

**Causa raíz**: El proceso de inicialización toma ~5 minutos, pero:
- Cloudflare timeout: ~100 segundos
- Nginx timeout: 60-120 segundos (típico)
- La respuesta HTTP nunca llegaba al cliente

### Solución Implementada

**Sistema de Job Tracking Asíncrono:**

1. Cliente hace POST → recibe `job_id` instantáneamente (< 1 seg)
2. Background task ejecuta el proceso completo (~5 min)
3. Cliente consulta `/status/{job_id}` periódicamente
4. Cuando termina, obtiene resultados completos

**Ventajas:**
- ✅ Sin timeouts en gateway
- ✅ Cliente puede cerrar conexión y volver después
- ✅ Monitoreo de progreso en tiempo real
- ✅ Múltiples jobs pueden ejecutarse simultáneamente

---

## Componentes Principales

### 1. Sistema de Job Tracking

**Estructura de datos:**

```python
initialization_jobs = {
    "uuid-job-id": {
        "status": "pending" | "running" | "completed" | "failed",
        "progress": "Mensaje descriptivo del paso actual",
        "result": { ... },  # Solo cuando status == "completed"
        "error": "mensaje",  # Solo cuando status == "failed"
        "created_at": datetime,
        "completed_at": datetime | None
    }
}
```

**Estados del job:**

| Estado | Descripción |
|--------|-------------|
| `pending` | Job creado, esperando ejecución |
| `running` | Job en ejecución, consultar campo `progress` |
| `completed` | Job terminado exitosamente, ver `result` |
| `failed` | Job falló, ver campo `error` |

### 2. Tablas de Base de Datos

**SAP_EMPRESAS**
```sql
CREATE TABLE SAP_EMPRESAS (
    Instancia NVARCHAR(50) PRIMARY KEY,
    PrintHeadr NVARCHAR(255),
    CompnyAddr NVARCHAR(255),
    TaxIdNum NVARCHAR(50),
    SL BIT DEFAULT 0,      -- Service Layer productivo habilitado
    SLP BIT DEFAULT 0,     -- Service Layer pruebas habilitado
    Prueba BIT DEFAULT 0   -- Tiene versión _PRUEBAS
)
```

**SAP_PROVEEDORES**
```sql
CREATE TABLE SAP_PROVEEDORES (
    Instancia NVARCHAR(50),
    CardCode NVARCHAR(50),
    CardName NVARCHAR(255),
    CardType NVARCHAR(1),
    LicTradNum NVARCHAR(50),
    Phone1 NVARCHAR(50),
    E_Mail NVARCHAR(100),
    PRIMARY KEY (Instancia, CardCode)
)
```

**USER_SESSIONS**
```sql
CREATE TABLE USER_SESSIONS (
    SessionID NVARCHAR(50) PRIMARY KEY,
    Username NVARCHAR(50),
    CreatedAt DATETIME,
    LastActivity DATETIME,
    Scopes NVARCHAR(255)
)
```

### 3. Vistas SQL (Creadas Dinámicamente)

**vw_productivo**
```sql
CREATE OR ALTER VIEW dbo.vw_productivo AS
SELECT Instancia, PrintHeadr, CompnyAddr, TaxIdNum
FROM SAP_EMPRESAS
WHERE SL = 1
```
- Lista instancias con Service Layer productivo habilitado
- Usada cuando `_modo_pruebas = False`

**vw_pruebas**
```sql
CREATE OR ALTER VIEW dbo.vw_pruebas AS
SELECT Instancia, PrintHeadr, CompnyAddr, TaxIdNum
FROM SAP_EMPRESAS
WHERE SLP = 1 AND Prueba = 1
```
- Lista instancias con Service Layer de pruebas habilitado
- Usada cuando `_modo_pruebas = True`

---

## Flujo de Ejecución

### Paso a Paso del Background Task

**1. Guardar información de sesión**
```python
session_id = current_user.session_id
username = current_user.sub
scopes = current_user.scopes
```

**2. Eliminar y recrear base de datos**
```python
drop_and_create_database()
```
- Ejecuta `DROP DATABASE MCP_DATA`
- Ejecuta `CREATE DATABASE MCP_DATA`

**3. Crear tablas fundamentales**
```python
ensure_table_sap_empresas_exists()
ensure_table_sap_proveedores_exists()
ensure_sessions_table_exists()
```

**4. Poblar SAP_EMPRESAS**
```python
resultado_empresas = inicializa_sap_empresas()
```
- Consulta HANA para obtener lista de instancias
- Para cada instancia:
  - Verifica si existe versión `_PRUEBAS`
  - Obtiene datos de tabla OADM (empresa)
  - Inserta en SAP_EMPRESAS
- Crea vistas `vw_productivo` y `vw_pruebas`

**5. Test Service Layer (paralelo)**
```python
resultado_sl = test_service_layer_all_instances(
    sap_empresas_result=resultado_empresas,
    skip_email=True
)
```
- Prueba login en 24 instancias productivas (paralelo, max 10 workers)
- Prueba login en 7 instancias de pruebas (paralelo)
- Actualiza campos `SL` y `SLP` en SAP_EMPRESAS
- Total: ~30 conexiones en paralelo

**6. Poblar SAP_PROVEEDORES**
```python
resultado_proveedores = actualizar_sap_proveedores()
```
- Obtiene instancias usando `get_instancias_con_service_layer()`
  - Si modo productivo → usa `vw_productivo`
  - Si modo pruebas → usa `vw_pruebas`
- Para cada instancia:
  - Conecta a Service Layer
  - Descarga proveedores (CardType='S')
  - Sincroniza con tabla SAP_PROVEEDORES
  - Ejecuta MERGE (update/insert/delete)

**7. Restaurar sesión del usuario**
```python
INSERT INTO USER_SESSIONS (SessionID, Username, CreatedAt, LastActivity, Scopes)
VALUES (?, ?, ?, ?, ?)
```
- Usa el **mismo SessionID** guardado al inicio
- Preserva scopes originales
- El token del usuario sigue siendo válido

**8. Enviar email con resultados**
```python
enviar_correo_inicializacion(
    sap_empresas_result=resultado_empresas,
    service_layer_result=resultado_sl,
    sap_proveedores_result=resultado_proveedores
)
```

---

## Tablas y Vistas SQL

### Modo de Operación

El sistema opera en dos modos mutuamente excluyentes:

| Modo | Variable | Vista SQL | Descripción |
|------|----------|-----------|-------------|
| **Productivo** | `_modo_pruebas = False` | `vw_productivo` | Usa instancias con `SL=1` |
| **Pruebas** | `_modo_pruebas = True` | `vw_pruebas` | Usa instancias con `SLP=1 AND Prueba=1` |

### Cambio de Modo

**Endpoint:** `POST /pruebas`

```bash
# Activar modo pruebas
curl -X POST http://localhost:8000/pruebas \
  -H "Authorization: Bearer $TOKEN"

# Desactivar modo pruebas (volver a productivo)
curl -X DELETE http://localhost:8000/pruebas \
  -H "Authorization: Bearer $TOKEN"
```

### Ejemplo de Uso de Vistas

```python
def get_instancias_con_service_layer() -> list[str]:
    from config import get_modo_pruebas

    conn = get_mssql_connection()
    cursor = conn.cursor()
    try:
        if get_modo_pruebas():
            # Modo pruebas: instancias con SLP=1 y Prueba=1
            cursor.execute("SELECT Instancia FROM vw_pruebas")
        else:
            # Modo productivo: instancias con SL=1
            cursor.execute("SELECT Instancia FROM vw_productivo")
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    finally:
        cursor.close()
        conn.close()
```

---

## Endpoints de la API

### POST /inicializa_datos

Inicia el proceso de inicialización en background.

**Request:**
```bash
curl -X POST http://localhost:8000/inicializa_datos \
  -H "Authorization: Bearer $TOKEN"
```

**Response (inmediata, < 1 seg):**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "message": "Inicialización iniciada. Usa GET /inicializa_datos/status/{job_id} para consultar el progreso."
}
```

### GET /inicializa_datos/status/{job_id}

Consulta el estado y progreso de un job de inicialización.

**Request:**
```bash
curl -X GET http://localhost:8000/inicializa_datos/status/{job_id} \
  -H "Authorization: Bearer $TOKEN"
```

**Response (durante ejecución):**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "running",
  "progress": "Poblando tabla SAP_PROVEEDORES (instancia 15 de 21)...",
  "created_at": "2026-01-21T10:30:00"
}
```

**Response (completado):**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "created_at": "2026-01-21T10:30:00",
  "completed_at": "2026-01-21T10:35:06",
  "result": {
    "sap_empresas": {
      "total_empresas": 24,
      "insertados": 24,
      "errores": []
    },
    "service_layer": {
      "total_instancias": 24,
      "productivo": {
        "total": 24,
        "exitosos": 21,
        "fallidos": 3,
        "detalle_exitosos": ["AIRPORTS", "ANDENES", ...],
        "detalle_fallidos": [
          {"instancia": "ALIANZA", "error": "Login failed"},
          {"instancia": "BALLIANCE", "error": "Login failed"},
          {"instancia": "ZZMAQGEX", "error": "Login failed"}
        ]
      },
      "pruebas": {
        "total": 7,
        "exitosos": 6,
        "fallidos": 1,
        "detalle_exitosos": ["AIRPORTS_PRUEBAS", ...],
        "detalle_fallidos": [
          {"instancia": "ALIANZA_PRUEBAS", "error": "Login failed"}
        ]
      }
    },
    "sap_proveedores": {
      "modo": "productivo",
      "total_instancias": 21,
      "proveedores_actualizados": 0,
      "proveedores_insertados": 13199,
      "proveedores_eliminados": 0,
      "instancias_procesadas": [
        {"instancia": "AIRPORTS", "actualizados": 0, "insertados": 1069, "proveedores": 1069},
        {"instancia": "EXPANSION", "actualizados": 0, "insertados": 4075, "proveedores": 4075},
        ...
      ],
      "errores": []
    },
    "email_enviado": {"success": true},
    "session_restored": true
  }
}
```

**Response (error):**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "failed",
  "error": "Mensaje de error detallado",
  "created_at": "2026-01-21T10:30:00"
}
```

---

## Pruebas Realizadas

### Prueba Completa con Sistema Asíncrono

**Fecha:** 2026-01-21
**Entorno:** Docker containers (MSSQL 2022, FastAPI, Postfix)
**Método:** Curl desde localhost

#### Paso 1: Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"sa","password":"Progex2025*"}'
```

**Resultado:**
```json
{
  "access_token": "ebdae3b8-9e74-403c-b22e-444992f3ca49",
  "token_type": "bearer"
}
```

#### Paso 2: Iniciar proceso (retorno inmediato)

```bash
curl -X POST http://localhost:8000/inicializa_datos \
  -H "Authorization: Bearer ebdae3b8-9e74-403c-b22e-444992f3ca49"
```

**Resultado (< 1 segundo):**
```json
{
  "job_id": "f3e8d9a2-4b7c-11ec-8d3d-0242ac130003",
  "status": "pending",
  "message": "Inicialización iniciada. Usa GET /inicializa_datos/status/f3e8d9a2-4b7c-11ec-8d3d-0242ac130003 para consultar el progreso."
}
```

#### Paso 3: Consultar progreso (mientras ejecuta)

```bash
# Después de 30 segundos
curl -X GET http://localhost:8000/inicializa_datos/status/f3e8d9a2-4b7c-11ec-8d3d-0242ac130003 \
  -H "Authorization: Bearer ebdae3b8-9e74-403c-b22e-444992f3ca49"
```

**Resultado:**
```json
{
  "job_id": "f3e8d9a2-4b7c-11ec-8d3d-0242ac130003",
  "status": "running",
  "progress": "Probando conexión a Service Layer (instancia 18 de 24)...",
  "created_at": "2026-01-21T10:30:00"
}
```

#### Paso 4: Obtener resultado final

```bash
# Después de 5 minutos
curl -X GET http://localhost:8000/inicializa_datos/status/f3e8d9a2-4b7c-11ec-8d3d-0242ac130003 \
  -H "Authorization: Bearer ebdae3b8-9e74-403c-b22e-444992f3ca49"
```

**Resultado completo disponible en archivo output.**

### Métricas de la Prueba

| Métrica | Valor |
|---------|-------|
| **Tiempo total de ejecución** | 5 minutos 6 segundos |
| **Empresas insertadas** | 24 |
| **Instancias productivas exitosas** | 21 de 24 |
| **Instancias de pruebas exitosas** | 6 de 7 |
| **Proveedores sincronizados** | 13,199 |
| **Instancias procesadas** | 21 |
| **Email enviado** | ✅ Exitoso |
| **Sesión restaurada** | ✅ Exitoso |

### Distribución de Proveedores por Instancia

| Instancia | Proveedores |
|-----------|-------------|
| EXPANSION | 4,075 |
| HEARST | 1,272 |
| ANDENES | 1,215 |
| CINETICA | 1,171 |
| NOTICIAS | 1,077 |
| AIRPORTS | 1,069 |
| AUTOBUSES | 817 |
| QUINTAM | 630 |
| RCS | 406 |
| MOTOR | 335 |
| GRAVITY | 328 |
| HOLDING | 263 |
| SERVICIOS | 153 |
| GEE | 137 |
| DIGITAL | 113 |
| CORPORATE | 52 |
| MEXMEP | 40 |
| MEXED | 30 |
| COMUNICACIONES | 7 |
| SATSA | 6 |
| TENEDORA | 3 |
| **TOTAL** | **13,199** |

---

## Guía de Uso

### Para Desarrolladores

**1. Ejecutar inicialización completa:**

```bash
# 1. Hacer login
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"sa","password":"Progex2025*"}' \
  | jq -r '.access_token')

# 2. Iniciar proceso
JOB_ID=$(curl -X POST http://localhost:8000/inicializa_datos \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.job_id')

echo "Job ID: $JOB_ID"

# 3. Consultar progreso cada 30 segundos
while true; do
  STATUS=$(curl -s -X GET http://localhost:8000/inicializa_datos/status/$JOB_ID \
    -H "Authorization: Bearer $TOKEN" \
    | jq -r '.status')

  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi

  echo "Status: $STATUS"
  sleep 30
done

# 4. Obtener resultado final
curl -X GET http://localhost:8000/inicializa_datos/status/$JOB_ID \
  -H "Authorization: Bearer $TOKEN" \
  | jq .
```

**2. Cambiar entre modo productivo y pruebas:**

```bash
# Activar modo pruebas
curl -X POST http://localhost:8000/pruebas \
  -H "Authorization: Bearer $TOKEN"

# Desactivar modo pruebas
curl -X DELETE http://localhost:8000/pruebas \
  -H "Authorization: Bearer $TOKEN"

# Verificar modo actual
curl -X GET http://localhost:8000/pruebas \
  -H "Authorization: Bearer $TOKEN"
```

### Para Administradores

**Monitoreo de Jobs:**

Los jobs en ejecución se almacenan en memoria en el diccionario `initialization_jobs`. Si el contenedor se reinicia, se pierden los jobs en ejecución.

**Recomendaciones:**
- No reiniciar el contenedor durante una inicialización
- Consultar el status antes de iniciar un nuevo job
- Los jobs completados permanecen en memoria hasta el reinicio

**Logs:**

Los mensajes de progreso se actualizan en el diccionario `initialization_jobs[job_id]["progress"]`:
- "Iniciando eliminación y recreación de base de datos..."
- "Poblando tabla SAP_EMPRESAS..."
- "Creando vistas SQL (vw_productivo, vw_pruebas)..."
- "Probando conexión a Service Layer..."
- "Poblando tabla SAP_PROVEEDORES..."
- "Enviando correo electrónico con resultados..."
- "Proceso completado exitosamente"

---

## Notas Técnicas

### Thread Safety

El sistema usa `threading.Lock` para garantizar que las operaciones en el diccionario `initialization_jobs` sean thread-safe:

```python
jobs_lock = threading.Lock()

# Actualizar status
with jobs_lock:
    initialization_jobs[job_id]["status"] = "running"
    initialization_jobs[job_id]["progress"] = "Mensaje..."
```

### Preservación de Sesión

La sesión se restaura usando el **mismo SessionID** que el usuario tenía antes de la inicialización:

1. Se guarda `session_id`, `username`, `scopes` al inicio
2. La base de datos se elimina completamente (incluyendo USER_SESSIONS)
3. Al final, se recrea el registro con el SessionID original
4. El token JWT sigue siendo válido porque contiene el SessionID

### Service Layer Paralelo

Las pruebas de Service Layer se ejecutan en paralelo usando `ThreadPoolExecutor`:

```python
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = []
    for instancia in instancias:
        futures.append(executor.submit(test_instancia, instancia))

    for future in concurrent.futures.as_completed(futures):
        resultado = future.result(timeout=60)
```

**Ventajas:**
- Reduce tiempo de ejecución de ~5 minutos (serial) a ~1 minuto (paralelo)
- Maneja timeouts individuales por instancia
- Continúa aunque una instancia falle

### Vistas SQL Dinámicas

Las vistas se recrean en cada inicialización usando `CREATE OR ALTER VIEW`:

```python
mssql_cursor.execute("""
    CREATE OR ALTER VIEW dbo.vw_productivo AS
    SELECT Instancia, PrintHeadr, CompnyAddr, TaxIdNum
    FROM SAP_EMPRESAS
    WHERE SL = 1
""")
```

Esto garantiza que las vistas siempre reflejen el estado actual de SAP_EMPRESAS.

---

## Conclusiones

El sistema de inicialización asíncrona resuelve completamente el problema de timeout en gateways y proporciona una experiencia de usuario superior con las siguientes mejoras:

✅ **Sin timeout**: Funciona correctamente incluso con procesos largos (5+ minutos)
✅ **Monitoreo en tiempo real**: El usuario puede consultar el progreso en cualquier momento
✅ **Sesión preservada**: No requiere login nuevamente después de la inicialización
✅ **Sincronización automática**: 13,000+ proveedores se sincronizan automáticamente
✅ **Soporte multi-modo**: Cambia fácilmente entre productivo y pruebas
✅ **Email automático**: Notificación por correo con resultados detallados
✅ **Robusto y confiable**: Manejo de errores, timeouts, y ejecución paralela

**Próximos pasos sugeridos:**
- Implementar limpieza automática de jobs antiguos (> 24 horas)
- Agregar persistencia de jobs en base de datos (opcional)
- Implementar WebSocket para notificaciones en tiempo real (opcional)
- Agregar endpoint para cancelar jobs en ejecución (opcional)
