# Documentación de Pruebas - API MCP

Este directorio contiene la documentación de pruebas y reportes del sistema API MCP.

## Índice de Documentación

### Sistema de Inicialización

| Documento | Versión | Descripción | Estado |
|-----------|---------|-------------|--------|
| [prueba_inicializa_datos_async_completo.md](prueba_inicializa_datos_async_completo.md) | **2.0** | Sistema asíncrono con job tracking, poblado de SAP_PROVEEDORES, y vistas SQL | ✅ **ACTUAL** |
| [prueba_inicializa_datos_session_preservation.md](prueba_inicializa_datos_session_preservation.md) | 1.0 | Sistema síncrono con preservación de sesión | ⚠️ OBSOLETO |

### Sistema de Sesiones

| Documento | Descripción | Estado |
|-----------|-------------|--------|
| [reporte_pruebas_session_tokens.md](reporte_pruebas_session_tokens.md) | Implementación del sistema de session tokens con sliding expiration | ✅ VIGENTE |

### Sistema de Proveedores

| Documento | Descripción | Estado |
|-----------|-------------|--------|
| [proveedores_activos.md](proveedores_activos.md) | Sistema de consulta de proveedores activos con modo productivo/pruebas | ✅ VIGENTE |

## Resumen Ejecutivo

### Sistema de Inicialización v2.0 (Asíncrono)

El sistema de inicialización ha sido completamente rediseñado para ejecutarse de forma asíncrona, resolviendo problemas de timeout en gateways (Cloudflare/Nginx) y mejorando la experiencia del usuario.

**Características principales:**
- ✅ Ejecución asíncrona con job tracking
- ✅ Sin timeouts (procesos de 5+ minutos)
- ✅ Monitoreo de progreso en tiempo real
- ✅ Poblado automático de 13,000+ proveedores
- ✅ Soporte para modo productivo y modo pruebas
- ✅ Preservación de sesión del usuario
- ✅ Notificación por email automática

**Endpoints:**
```bash
POST /inicializa_datos              # Inicia proceso (retorna job_id)
GET  /inicializa_datos/status/{id}  # Consulta progreso
```

**Guía rápida:**
```bash
# 1. Hacer login
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"sa","password":"********"}' \
  | jq -r '.access_token')

# 2. Iniciar proceso
JOB_ID=$(curl -X POST http://localhost:8000/inicializa_datos \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.job_id')

# 3. Consultar progreso
curl -X GET http://localhost:8000/inicializa_datos/status/$JOB_ID \
  -H "Authorization: Bearer $TOKEN"
```

### Sistema de Session Tokens

Sistema de autenticación basado en tokens con sliding expiration.

**Características:**
- ✅ Tokens con expiración deslizante (sliding window)
- ✅ Almacenamiento en base de datos (tabla USER_SESSIONS)
- ✅ Renovación automática en cada request
- ✅ Gestión de múltiples sesiones por usuario
- ✅ Endpoints administrativos para gestión de sesiones

**Endpoints:**
```bash
POST   /auth/login         # Login y generación de token
GET    /auth/sessions      # Listar sesiones activas
DELETE /auth/sessions/{id} # Cerrar sesión específica
POST   /auth/logout        # Cerrar sesión actual
```

## Arquitectura del Sistema

### Base de Datos (MSSQL)

**Tablas principales:**

```sql
-- Empresas SAP
SAP_EMPRESAS (
    Instancia NVARCHAR(50) PK,
    PrintHeadr NVARCHAR(255),
    CompnyAddr NVARCHAR(255),
    TaxIdNum NVARCHAR(50),
    SL BIT,          -- Service Layer productivo
    SLP BIT,         -- Service Layer pruebas
    Prueba BIT       -- Tiene versión _PRUEBAS
)

-- Proveedores SAP
SAP_PROVEEDORES (
    Instancia NVARCHAR(50),
    CardCode NVARCHAR(50),
    CardName NVARCHAR(255),
    CardType NVARCHAR(1),
    LicTradNum NVARCHAR(50),
    Phone1 NVARCHAR(50),
    E_Mail NVARCHAR(100),
    PK (Instancia, CardCode)
)

-- Sesiones de usuario
USER_SESSIONS (
    SessionID NVARCHAR(50) PK,
    Username NVARCHAR(50),
    CreatedAt DATETIME,
    LastActivity DATETIME,
    Scopes NVARCHAR(255)
)
```

**Vistas dinámicas:**

```sql
-- Instancias productivas con SL habilitado
vw_productivo (Instancia, PrintHeadr, CompnyAddr, TaxIdNum)

-- Instancias de pruebas con SLP habilitado
vw_pruebas (Instancia, PrintHeadr, CompnyAddr, TaxIdNum)
```

### Sistema de Modos (Productivo/Pruebas)

El sistema opera en dos modos mutuamente excluyentes:

| Modo | Variable Global | Vista SQL | Service Layer |
|------|-----------------|-----------|---------------|
| **Productivo** | `_modo_pruebas = False` | `vw_productivo` | Instancias base (ej: EXPANSION) |
| **Pruebas** | `_modo_pruebas = True` | `vw_pruebas` | Instancias _PRUEBAS (ej: EXPANSION_PRUEBAS) |

**Cambio de modo:**
```bash
# Activar modo pruebas
curl -X POST http://localhost:8000/pruebas \
  -H "Authorization: Bearer $TOKEN"

# Desactivar modo pruebas
curl -X DELETE http://localhost:8000/pruebas \
  -H "Authorization: Bearer $TOKEN"

# Consultar modo actual
curl -X GET http://localhost:8000/pruebas \
  -H "Authorization: Bearer $TOKEN"
```

## Métricas de Rendimiento

### Inicialización Completa

| Métrica | Valor |
|---------|-------|
| Tiempo total | ~5 minutos |
| Empresas insertadas | 24 |
| Proveedores sincronizados | 13,199 |
| Instancias productivas | 21 (exitosas) de 24 |
| Instancias de pruebas | 6 (exitosas) de 7 |
| Service Layer tests | Paralelo (max 10 workers) |
| Email enviado | ✅ Automático |
| Sesión preservada | ✅ Automático |

### Distribución de Proveedores

Top 5 instancias por cantidad de proveedores:

1. EXPANSION: 4,075
2. HEARST: 1,272
3. ANDENES: 1,215
4. CINETICA: 1,171
5. NOTICIAS: 1,077

## Entorno de Desarrollo

### Requisitos

- Python 3.11+
- FastAPI
- MSSQL Server 2022
- SAP HANA
- SAP Business One Service Layer
- Docker & Docker Compose

### Estructura de Contenedores

```yaml
services:
  mssql-api-mcp:    # MSSQL Server 2022
  postfix-api-mcp:  # Servidor SMTP
  api-mcp:          # API FastAPI
```

### Variables de Entorno

```env
# JWT
JWT_SECRET_KEY=***
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# MSSQL
MSSQL_HOST=mssql
MSSQL_PORT=1433
MSSQL_USER=sa
MSSQL_PASSWORD=***
MSSQL_DATABASE=MCP_DATA

# SAP HANA
SAP_HANA_HOST=***
SAP_HANA_PORT=30015
SAP_HANA_USER=***
SAP_HANA_PASSWORD=***

# SAP B1 Service Layer
SAP_B1_SERVICE_LAYER_URL=http://***
SAP_B1_USER=***
SAP_B1_PASSWORD=***
SAP_B1_COMPANY_DB=***

# Email
EMAIL_SUPERVISOR=***@progex.grupoexpansion.com
SMTP_HOST=localhost
SMTP_PORT=25
EMAIL_FROM=api-mcp@progex.local
```

## Solución de Problemas

### Error 504 Gateway Timeout

**Problema:** Timeout al ejecutar `/inicializa_datos` desde URL externa (Cloudflare).

**Solución:** Usar la versión 2.0 asíncrona del sistema. El endpoint retorna inmediatamente con un `job_id`, y el progreso se consulta con `/inicializa_datos/status/{job_id}`.

### Token inválido después de inicialización

**Problema:** El token de autenticación se invalida durante la ejecución de `/inicializa_datos`.

**Solución:** Esto es esperado ya que la base de datos (incluyendo USER_SESSIONS) se elimina y recrea. La sesión se restaura automáticamente al final del proceso. El token vuelve a ser válido después de que el job se completa.

### Service Layer login failed

**Problema:** Algunas instancias fallan al conectar con Service Layer.

**Causas comunes:**
- Credenciales incorrectas en `.env`
- Service Layer no disponible para esa instancia
- Red no alcanza el Service Layer
- Licencia de SAP expirada

**Verificación:**
```bash
# Revisar resultados detallados del job
curl -X GET http://localhost:8000/inicializa_datos/status/{job_id} \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.result.service_layer.detalle_fallidos'
```

### Base de datos no existe al hacer login

**Problema:** Error al intentar login cuando la base de datos MCP_DATA no existe.

**Solución:** Esto está manejado automáticamente. El sistema llama a `ensure_database_exists()` y `ensure_sessions_table_exists()` antes de crear sesiones, por lo que la base de datos y la tabla se crean automáticamente si no existen.

## Próximos Pasos Sugeridos

### Mejoras al Sistema de Job Tracking

1. **Persistencia en base de datos:** Almacenar jobs en tabla SQL en lugar de memoria
2. **Limpieza automática:** Eliminar jobs antiguos (> 24 horas) automáticamente
3. **WebSocket:** Notificaciones en tiempo real del progreso
4. **Cancelación:** Endpoint para cancelar jobs en ejecución
5. **Historia:** Guardar histórico de ejecuciones

### Mejoras al Sistema de Proveedores

1. **Sincronización incremental:** Solo sincronizar proveedores modificados
2. **Campos adicionales:** Agregar más campos de BusinessPartners
3. **Clientes:** Sincronizar también clientes (CardType='C')
4. **Scheduling:** Sincronización automática programada (cron)

### Mejoras al Sistema de Sesiones

1. **Refresh tokens:** Implementar refresh tokens para mayor seguridad
2. **Multi-dispositivo:** Identificar y gestionar sesiones por dispositivo
3. **Geolocalización:** Registrar IP y ubicación de sesiones
4. **Alertas:** Notificar al usuario de nuevas sesiones

## Contacto

Para preguntas o problemas con la documentación:
- Revisar los archivos de documentación detallada en este directorio
- Consultar el código fuente en `/app`
- Revisar logs del contenedor: `docker logs api-mcp`

---

**Última actualización:** 2026-01-21
**Versión de documentación:** 2.0
**Branch:** Modifica-flujo-inicializa_datos
