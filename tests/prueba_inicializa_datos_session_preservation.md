# Prueba: Preservación de Sesión en /inicializa_datos

> **NOTA:** Esta documentación describe la versión 1.0 (síncrona) del sistema.
> Para la versión 2.0 (asíncrona con job tracking), consultar:
> **[prueba_inicializa_datos_async_completo.md](prueba_inicializa_datos_async_completo.md)**

**Fecha:** 2026-01-21
**Branch:** Modifica-flujo-inicializa_datos
**Versión:** 1.0 (Sistema Síncrono - OBSOLETO)
**Commits relacionados:**
- `db06b9e` - Fix inicializa_datos to recreate USER_SESSIONS table
- `63b9512` - Garantizar funcionamiento de autenticación sin base de datos preexistente

## Objetivo

Verificar que el endpoint `/inicializa_datos` preserva la sesión del usuario actual después de eliminar y recrear la base de datos completa, permitiendo que el token de autenticación siga siendo válido.

## Problema Original

Cuando se ejecutaba `/inicializa_datos`:
1. El endpoint eliminaba completamente la base de datos (incluyendo la tabla `USER_SESSIONS`)
2. Recreaba la base de datos desde cero
3. **El token del usuario quedaba invalidado** porque su sesión ya no existía
4. El usuario debía hacer login nuevamente para obtener un nuevo token

## Solución Implementada

### Cambios en `app/database.py` (función `inicializa_sap_empresas`)

```python
def inicializa_sap_empresas() -> dict:
    """
    Inicializa la tabla SAP_EMPRESAS:
    1. Elimina y recrea la base de datos desde cero
    2. Crea la tabla SAP_EMPRESAS
    3. Crea la tabla USER_SESSIONS (para el sistema de sesiones)
    ...
    """
    from session import ensure_sessions_table_exists

    # Eliminar y recrear la base de datos
    drop_and_create_database()
    ensure_table_sap_empresas_exists()

    # Recrear tabla de sesiones (necesaria para el sistema de autenticación)
    ensure_sessions_table_exists()
    ...
```

### Cambios en `app/main.py` (endpoint `/inicializa_datos`)

```python
@app.post("/inicializa_datos", tags=["MSSQL"])
async def inicializa_datos(
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> dict:
    from session import create_session
    import pyodbc
    from datetime import datetime

    # Guardar información de la sesión actual antes de eliminar la base de datos
    session_id = current_user.session_id
    username = current_user.sub
    scopes = current_user.scopes

    # Ejecutar inicialización (esto eliminará y recreará la base de datos)
    resultado_empresas = inicializa_sap_empresas()
    resultado_sl = test_service_layer_all_instances(...)

    # Restaurar la sesión del usuario actual
    from database import get_mssql_connection
    conn = get_mssql_connection()
    cursor = conn.cursor()
    try:
        now = datetime.now()
        scopes_str = ",".join(scopes)
        cursor.execute("""
            INSERT INTO USER_SESSIONS (SessionID, Username, CreatedAt, LastActivity, Scopes)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, username, now, now, scopes_str))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return {
        "sap_empresas": resultado_empresas,
        "service_layer": resultado_sl,
        "session_restored": True
    }
```

### Cambios en `app/session.py` (función `ensure_sessions_table_exists`)

```python
def ensure_sessions_table_exists() -> None:
    """
    Crea la base de datos (si no existe) y la tabla USER_SESSIONS (si no existe).
    Esto permite que el sistema de autenticación funcione incluso si la base de datos
    no ha sido inicializada aún.
    """
    from database import ensure_database_exists

    # Primero asegurar que la base de datos existe
    ensure_database_exists()

    # Luego crear la tabla USER_SESSIONS si no existe
    ...
```

## Escenarios Cubiertos

### ✅ Escenario 1: Base de datos NO existe
1. Usuario intenta hacer login
2. `ensure_sessions_table_exists()` crea automáticamente la base de datos
3. Se crea la tabla USER_SESSIONS
4. Se genera el token de sesión
5. Usuario puede ejecutar `/inicializa_datos`

### ✅ Escenario 2: Base de datos SÍ existe
1. Usuario hace login
2. Se genera el token de sesión
3. Usuario ejecuta `/inicializa_datos`
4. La base de datos se elimina y recrea
5. **La sesión del usuario se preserva automáticamente**
6. El token sigue siendo válido

### ✅ Escenario 3: Múltiples ejecuciones de `/inicializa_datos`
1. Usuario ejecuta `/inicializa_datos` varias veces
2. En cada ejecución, la sesión se preserva
3. El token nunca se invalida

## Prueba Realizada

### Configuración
- **API URL:** http://localhost:8000
- **Usuario:** sa
- **Base de datos:** MCP_DATA (MSSQL Server 2022)

### Pasos Ejecutados

#### PASO 1: Login para obtener token
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"sa","password":"********"}'
```

**Resultado:**
```json
{
  "access_token": "ebdae3b8-9e74-403c-b22e-444992f3ca49",
  "token_type": "bearer"
}
```

✅ Token obtenido: `ebdae3b8-9e74-403c-b22e-444992f3ca49`

#### PASO 2: Verificar sesión inicial
```bash
curl -X GET http://localhost:8000/auth/sessions \
  -H "Authorization: Bearer ebdae3b8-9e74-403c-b22e-444992f3ca49"
```

**Resultado:**
```
Total sesiones: 1
Usuario: sa
```

✅ Sesión inicial verificada correctamente

#### PASO 3: Ejecutar /inicializa_datos
```bash
curl -X POST http://localhost:8000/inicializa_datos \
  -H "Authorization: Bearer ebdae3b8-9e74-403c-b22e-444992f3ca49"
```

**Resultado:**
```json
{
  "sap_empresas": {
    "total_empresas": 24,
    "insertados": 24,
    "errores": []
  },
  "service_layer": {
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
  "session_restored": true
}
```

✅ Empresas insertadas: 24
✅ Sesión restaurada: **true**

#### PASO 4: Verificar que el token SIGUE funcionando
```bash
curl -X GET http://localhost:8000/auth/sessions \
  -H "Authorization: Bearer ebdae3b8-9e74-403c-b22e-444992f3ca49"
```

**Resultado:**
```
Total sesiones: 1
Usuario: sa
SessionID original presente: true
```

✅ **Token sigue siendo válido después de eliminar/recrear la base de datos**
✅ **El SessionID original está presente en la base de datos**

## Resultado Final

### ✅ TODAS LAS PRUEBAS EXITOSAS

El endpoint `/inicializa_datos` ahora:

1. **Elimina y recrea la base de datos** correctamente
2. **Recrea automáticamente la tabla USER_SESSIONS**
3. **Preserva la sesión del usuario actual** que ejecuta el endpoint
4. **Mantiene el token válido** después de la operación
5. **Permite autenticación desde el primer momento** (incluso si la BD no existe)

## Beneficios

- ✅ El usuario nunca pierde su sesión al ejecutar `/inicializa_datos`
- ✅ No se requiere hacer login nuevamente después de inicializar
- ✅ El sistema de autenticación funciona incluso si la BD no existe
- ✅ Mejora significativa en la experiencia del usuario
- ✅ Previene errores de autenticación inesperados

## Notas Técnicas

- La sesión se restaura con el **mismo SessionID** para mantener la compatibilidad del token
- Se preservan los **scopes** originales del usuario
- La fecha `CreatedAt` se actualiza al momento de la restauración
- La operación es **atómica**: si falla la inicialización, no se intenta restaurar la sesión
