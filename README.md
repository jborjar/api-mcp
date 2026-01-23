# API MCP - Integración MSSQL, SAP HANA y SAP B1

## Estructura del Proyecto

```
./
├── api_mcp/
│   ├── .env                     # Variables de entorno
│   └── Docker/
│       ├── Dockerfile.api-mcp   # Imagen del servicio Python
│       ├── Dockerfile.mssql2022 # Imagen de MSSQL Server
│       ├── Dockerfile.postfix   # Imagen del servidor SMTP
│       ├── entrypoint_add_gw.sh # Script de rutas estáticas (api-mcp)
│       ├── entrypoint_mssql.sh  # Script de inicialización MSSQL
│       ├── entrypoint_postfix.sh # Script de configuración Postfix
│       └── requirements.txt     # Dependencias Python
├── app/                         # Código fuente FastAPI
│   ├── auth.py                  # Autenticación con Session Tokens
│   ├── config.py                # Configuración desde variables de entorno
│   ├── database.py              # Conexiones a MSSQL y HANA
│   ├── main.py                  # Punto de entrada de la API
│   ├── mcp.py                   # Endpoints MCP
│   ├── sap_service_layer.py     # Cliente SAP B1 Service Layer
│   ├── session.py               # Gestión de sesiones en MSSQL
│   └── websettings.py           # Interfaz web (login y ajustes)
├── tests/                       # Scripts y reportes de pruebas
│   ├── test_completo_sistema.sh # Script de prueba completa automatizada
│   ├── prueba_session_tokens.md # Pruebas del sistema de sesiones
│   └── prueba_inicializa_datos_session_preservation.md
├── db/
│   └── mssql/                   # Datos persistentes de MSSQL (generado)
│       ├── .system/
│       ├── data/
│       ├── log/
│       └── secrets/
└── docker-compose.yml
```

## Requisitos Previos

- Docker
- Docker Compose
- Red externa `vpn-proxy` creada previamente

## Configuración

1. Editar el archivo `./api_mcp/.env` con las credenciales correspondientes:

```env
# JWT
JWT_SECRET_KEY=tu_clave_secreta_aqui
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Configuración de sesiones y filtros
SESIONES_ACTIVAS=2
ANOS_ACTIVO=0

# Microsoft SQL Server
SA_PASSWORD=tu_password_sa
MSSQL_HOST=mssql-api-mcp
MSSQL_PORT=1433
MSSQL_USER=sa
MSSQL_PASSWORD=tu_password_sa
MSSQL_DATABASE=tu_base_de_datos

# SAP HANA
SAP_HANA_HOST=direccion_hana
SAP_HANA_PORT=puerto_hana
SAP_HANA_USER=usuario_hana
SAP_HANA_PASSWORD=password_hana

# SAP Business One Service Layer
SAP_B1_SERVICE_LAYER_URL=https://servidor:50000/b1s/v1/
SAP_B1_USER=usuario_b1
SAP_B1_PASSWORD=password_b1

# Email
EMAIL_SUPERVISOR=correo@dominio.com
SMTP_HOST=postfix-api-mcp
SMTP_PORT=25
EMAIL_FROM=aviso@progex.grupoexpansion

# Postfix - Relay externo (opcional)
# POSTFIX_HOSTNAME=mail.tudominio.com
# POSTFIX_DOMAIN=tudominio.com
# POSTFIX_RELAY_HOST=smtp.office365.com
# POSTFIX_RELAY_PORT=587
# POSTFIX_RELAY_USER=usuario@dominio.com
# POSTFIX_RELAY_PASSWORD=password

# Locale y Timezone
TZ=America/Mexico_City
LANG=es_MX.UTF-8
LC_ALL=es_MX.UTF-8
```

### Variables de Configuración

- **SESIONES_ACTIVAS**: Número máximo de sesiones simultáneas por usuario (default: 2)
  - Cuando se excede el límite, se elimina automáticamente la sesión más antigua
  - Valor recomendado: 1-5 sesiones

- **ANOS_ACTIVO**: Número de años hacia atrás para filtrar proveedores activos (default: 0)
  - 0 = Año actual solamente
  - 1 = Año actual y anterior
  - n = Últimos n años

## Ejecución

```bash
docker compose up -d
```

## Endpoints Disponibles

Total de endpoints: **25**

### Autenticación (5 endpoints)

- `POST /auth/login` - Obtener token de sesión (Session ID)
- `POST /auth/logout` - Cerrar sesión actual
- `GET /auth/sessions` - Listar sesiones activas del usuario
- `POST /auth/logout-all` - Cerrar todas las sesiones del usuario
- `POST /auth/cleanup` - Limpiar sesiones expiradas (mantenimiento)

### Sistema (7 endpoints)

- `GET /health` - Verificar estado del servicio
- `GET /me` - Información del usuario autenticado y sesión actual
- `GET /pruebas` - Consultar modo actual (productivo/pruebas)
- `POST /pruebas/{valor}` - Establecer modo (0=productivo, 1=pruebas)
- `GET /start` - Interfaz web con login y panel de ajustes
- `GET /config/email` - Consultar configuración de email del sistema
- `GET /config/sesiones` - Consultar configuración de sesiones y años activos

### SAP HANA (1 endpoint)

- `GET /empresas_registradas` - Listar empresas SAP B1 registradas en HANA (requiere autenticación)

### MSSQL (3 endpoints)

- `POST /inicializa_datos` - Inicializa las tablas SAP_EMPRESAS y SAP_PROVEEDORES (requiere autenticación)
- `POST /actualizar_empresas` - Actualiza SAP_EMPRESAS con datos de HANA (SAP es fuente de verdad, preserva SL)
- `POST /actualizar_proveedores` - Actualiza SAP_PROVEEDORES con datos de Service Layer (requiere autenticación)

### SAP Service Layer (2 endpoints)

- `GET /proveedores/{instancia}` - Obtener proveedores de una instancia SAP (requiere autenticación)
- `GET /test_service_layer` - Prueba conexión a Service Layer para todas las instancias SAP (requiere autenticación)

### Análisis (3 endpoints)

- `POST /proveedores/analizar-actividad` - Analiza actividad de proveedores en los últimos N años (requiere autenticación)
- `GET /inicializa_datos/status/{job_id}` - Consulta el estado de un job de inicialización (público, sin autenticación)
- `GET /inicializa_datos/jobs` - Lista todos los jobs de inicialización (requiere autenticación)

### MCP (4 endpoints - requieren autenticación con scopes específicos)

- `POST /mcp/tools/list` - Listar herramientas disponibles (scope: `mcp:tools:list`)
- `POST /mcp/tools/call` - Ejecutar herramienta (scope: `mcp:tools:call`)
- `POST /mcp/resources/list` - Listar recursos disponibles (scope: `mcp:resources:list`)
- `POST /mcp/resources/read` - Leer recurso (scope: `mcp:resources:read`)

## Interfaz Web

El sistema incluye una interfaz web accesible en `http://localhost:8000/start` que proporciona:

### Características de la Interfaz Web

- **Formulario de login integrado**: Autenticación directa desde el navegador
- **Gestión de sesión con cookies**: Token almacenado en cookie con validez de 1 hora
- **Diseño de 3 tarjetas independientes**:

  1. **Tarjeta API MCP**:
     - Indicador de sesión activa
     - Visualización del token de sesión
     - Botón para copiar token al portapapeles
     - Botón de cerrar sesión

  2. **Tarjeta INFORMACIÓN DEL USUARIO**:
     - Nombre de usuario
     - Session ID
     - Fecha de creación de la sesión
     - Fecha de expiración (calculada con sliding expiration)
     - Scopes asignados al usuario

  3. **Tarjeta AJUSTES**:
     - **Fila 1**: Modo de Operación + Sesiones activas (1, 2, 5)
     - **Fila 2**: Proveedores activos (0-9 años hacia atrás) + Enviar correo a (readonly)
     - **Botones fila 1**: Iniciar Base Auxiliar (degradado rojo-naranja) + Cambiar Ajustes (degradado amarillo-verde)
     - **Botones fila 2**: Actualizar Proveedores (degradado amarillo-verde) + Respaldar Usuarios (degradado amarillo-verde)
     - **Área de status**: Mensaje de progreso con spinner animado durante ejecución
       - Spinner: Círculo giratorio (20px) alineado a la derecha
       - Colores: Amarillo durante ejecución, verde al completar, rojo en error
       - Formato de mensaje en dos líneas: título + estado actual
     - Los 4 botones se deshabilitan simultáneamente durante la ejecución de "Iniciar Base Auxiliar"
     - Botón "Iniciar Base Auxiliar" con flujo completo de confirmación y monitoreo en tiempo real

- **Validación automática**: Verifica el token contra el servidor al cargar la página
- **Diseño responsive**: Layout de 3 columnas en escritorio, adaptado para dispositivos móviles
- **Centrado vertical**: Contenido de las tarjetas centrado verticalmente

### Acceso a la Interfaz Web

```bash
# Navegador web
http://localhost:8000/start
```

La interfaz valida automáticamente si existe una sesión activa (cookie) y muestra:
- **Login form** si no hay sesión válida
- **Panel autenticado con 3 tarjetas** si la sesión es válida

### Funcionalidad "Iniciar Base Auxiliar"

El botón "Iniciar Base Auxiliar" en la tarjeta AJUSTES ejecuta el siguiente flujo:

1. **Lectura de configuración:**
   - Modo de operación (Productivo/Pruebas)
   - Años de actividad para análisis de proveedores (0-9)
   - Email del supervisor para notificaciones

2. **Confirmación del usuario:**
   - Muestra popup modal personalizado con todos los parámetros
   - Advierte que la base operativa actual será eliminada y recreada
   - Botones "Cancelar" e "Iniciar"

3. **Ejecución del proceso:**
   - Deshabilita los 4 botones de la tarjeta AJUSTES para evitar múltiples ejecuciones
   - Muestra mensaje de estatus en tiempo real bajo los botones
   - Establece el modo de operación vía `POST /pruebas/{modo}`
   - Inicia la inicialización vía `POST /inicializa_datos?anos={anos}&email={email}`
   - Retorna Job ID para monitorear el progreso

4. **Monitoreo en tiempo real:**
   - Realiza polling automático cada 2 segundos al endpoint `/inicializa_datos/status/{job_id}`
   - Actualiza el mensaje de estatus con el progreso actual en formato de dos líneas:
     ```
     Ejecutando proceso de inicialización
     [Estado actual del job]
     ```
   - Muestra spinner animado (círculo giratorio) alineado a la derecha durante la ejecución
   - Estados visuales: running (amarillo con spinner), completed (verde), failed (rojo)
   - Manejo robusto de reinicios del servidor:
     - Si el servidor reinicia durante la ejecución, detecta el error 404
     - Detiene el polling automáticamente
     - Muestra mensaje de completado con historial de jobs disponible
     - Re-habilita los 4 botones para permitir nuevas operaciones
   - Habilita los 4 botones cuando el proceso termina (exitosamente o con error)
   - Muestra historial de las últimas 3 inicializaciones con fechas y estados

5. **Uso de parámetros:**
   - **anos**: Utilizado en `analizar_actividad_proveedores` (0=solo año actual, 1=actual+1 anterior, etc.)
   - **email**: Si es diferente a EMAIL_SUPERVISOR del .env, se usa como destinatario de notificaciones

### Otros Botones de la Tarjeta AJUSTES

La tarjeta AJUSTES incluye tres botones adicionales para operaciones específicas:

1. **Cambiar Ajustes** (degradado amarillo-verde):
   - Pendiente de implementación
   - Permitirá modificar configuraciones de sesiones activas, proveedores activos y email del supervisor

2. **Actualizar Proveedores** (degradado amarillo-verde):
   - Pendiente de implementación
   - Sincronizará la tabla SAP_PROVEEDORES con Service Layer sin recrear la base de datos

3. **Respaldar Usuarios** (degradado amarillo-verde):
   - Pendiente de implementación
   - Creará un respaldo de la tabla USER_SESSIONS

**Nota:** Los 4 botones se deshabilitan simultáneamente cuando "Iniciar Base Auxiliar" está en ejecución.

## Endpoints de Configuración

### GET /config/email

Obtiene la configuración de email del sistema desde las variables de entorno.

```bash
curl http://localhost:8000/config/email \
  -H "Authorization: Bearer <token>"
```

Respuesta:
```json
{
  "email_supervisor": "supervisor@empresa.com",
  "smtp_host": "postfix-api-mcp",
  "smtp_port": 25,
  "email_from": "aviso@progex.grupoexpansion"
}
```

### GET /config/sesiones

Obtiene la configuración de sesiones y años activos desde las variables de entorno.

```bash
curl http://localhost:8000/config/sesiones \
  -H "Authorization: Bearer <token>"
```

Respuesta:
```json
{
  "sesiones_activas": 2,
  "anos_activo": 0
}
```

## Sistema de Autenticación

La API utiliza **Session Tokens** almacenados en MSSQL con **renovación automática** (sliding expiration).

### Características del Sistema de Sesiones

- **Sliding Expiration**: La sesión se renueva automáticamente en cada petición
- **Timeout configurable**: 30 minutos de inactividad por defecto (configurable en `JWT_EXPIRATION_MINUTES`)
- **Control total**: Invalidar sesiones individual o masivamente
- **Sin dependencias externas**: Usa MSSQL existente (no requiere Redis)
- **Límite de sesiones activas**: Configurable por usuario vía variable de entorno `SESIONES_ACTIVAS` (default: 2)
  - Cuando un usuario excede el límite, se elimina automáticamente su sesión más antigua
  - Permite controlar recursos y seguridad limitando sesiones simultáneas

### Tabla USER_SESSIONS

```sql
CREATE TABLE USER_SESSIONS (
    SessionID NVARCHAR(100) PRIMARY KEY,
    Username NVARCHAR(100) NOT NULL,
    CreatedAt DATETIME NOT NULL,
    LastActivity DATETIME NOT NULL,
    Scopes NVARCHAR(500),
    INDEX idx_username (Username),
    INDEX idx_last_activity (LastActivity)
)
```

### Flujo de Autenticación

1. **Login**: Usuario se autentica y recibe un SessionID (UUID)
2. **Cada petición**: El SessionID se valida y la sesión se renueva automáticamente
3. **Inactividad**: Si pasan 30 minutos sin actividad, la sesión expira
4. **Logout**: El usuario puede cerrar sesión manualmente

### Comportamiento de Sliding Expiration

**Ejemplo:**
- Login a las 8:00 → Sesión expira a las 8:30
- Petición a las 8:10 → Sesión se renueva, ahora expira a las 8:40
- Petición a las 8:35 → Sesión se renueva, ahora expira a las 9:05
- Si no hay actividad por 30 minutos, la sesión expira automáticamente

## Uso de la API

### Obtener Token (Login)

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "sa", "password": "tu_password"}'
```

Respuesta:
```json
{
  "access_token": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "token_type": "bearer"
}
```

### Usar Endpoints Protegidos

```bash
curl http://localhost:8000/me \
  -H "Authorization: Bearer <token>"
```

Respuesta:
```json
{
  "username": "sa",
  "scopes": ["mcp:tools:list", "mcp:tools:call", "mcp:resources:list", "mcp:resources:read"],
  "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "created_at": "2026-01-22T10:00:00",
  "expires_at": "2026-01-22T10:30:00"
}
```

### Gestión de Sesiones

#### Listar sesiones activas

```bash
curl http://localhost:8000/auth/sessions \
  -H "Authorization: Bearer <token>"
```

Respuesta:
```json
{
  "username": "sa",
  "total_sessions": 2,
  "sessions": [
    {
      "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "username": "sa",
      "created_at": "2026-01-20T10:00:00",
      "last_activity": "2026-01-20T10:30:00",
      "scopes": ["mcp:tools:list", "mcp:tools:call", ...]
    }
  ]
}
```

#### Cerrar sesión actual

```bash
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer <token>"
```

#### Cerrar todas las sesiones

```bash
curl -X POST http://localhost:8000/auth/logout-all \
  -H "Authorization: Bearer <token>"
```

#### Limpiar sesiones expiradas (mantenimiento)

```bash
curl -X POST http://localhost:8000/auth/cleanup \
  -H "Authorization: Bearer <token>"
```

### Listar Empresas SAP B1

```bash
curl http://localhost:8000/empresas_registradas \
  -H "Authorization: Bearer <token>"
```

### Obtener Proveedores de una Instancia

```bash
# Todos los proveedores
curl http://localhost:8000/proveedores/NOMBRE_INSTANCIA \
  -H "Authorization: Bearer <token>"

# Limitar cantidad de resultados
curl "http://localhost:8000/proveedores/NOMBRE_INSTANCIA?top=10" \
  -H "Authorization: Bearer <token>"

# Filtrar por CardCode (contiene)
curl "http://localhost:8000/proveedores/NOMBRE_INSTANCIA?card_code=N1000" \
  -H "Authorization: Bearer <token>"

# Filtrar por nombre (contiene)
curl "http://localhost:8000/proveedores/NOMBRE_INSTANCIA?card_name=CEMEX" \
  -H "Authorization: Bearer <token>"

# Filtrar por RFC (contiene)
curl "http://localhost:8000/proveedores/NOMBRE_INSTANCIA?federal_tax_id=ABC123" \
  -H "Authorization: Bearer <token>"

# Combinación de filtros
curl "http://localhost:8000/proveedores/NOMBRE_INSTANCIA?card_name=AMERICAN&top=5" \
  -H "Authorization: Bearer <token>"
```

Parámetros disponibles:

| Parámetro | Descripción |
|-----------|-------------|
| `top` | Limita el número de registros retornados |
| `card_code` | Filtra por CardCode que contenga el valor |
| `card_name` | Filtra por CardName que contenga el valor |
| `federal_tax_id` | Filtra por FederalTaxID (RFC) que contenga el valor |

Respuesta:
```json
{
  "instancia": "NOMBRE_INSTANCIA",
  "total": "4075",
  "proveedores": [
    {
      "CardCode": "N1000011",
      "CardName": "American Express Company México SA de CV",
      "FederalTaxID": "AEC810901298",
      "Phone1": "5551234567",
      "EmailAddress": "proveedor@ejemplo.com",
      "Address": "Av. Patriotismo 635",
      "City": "CDMX",
      "Country": "MX",
      ...
    }
  ]
}
```

### Listar Herramientas MCP

```bash
curl -X POST http://localhost:8000/mcp/tools/list \
  -H "Authorization: Bearer <token>"
```

## Documentación Interactiva

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Servicios

| Servicio        | Puerto | Descripción                    |
|-----------------|--------|--------------------------------|
| api-mcp         | 8000   | API FastAPI                    |
| mssql-api-mcp   | 1433   | SQL Server (solo red interna)  |
| postfix-api-mcp | 25     | Servidor SMTP (solo red interna) |

## Red Docker

Todos los servicios están conectados a la red externa `vpn-proxy`. El servicio Python puede conectarse a:
- MSSQL usando el hostname `mssql-api-mcp`
- Postfix usando el hostname `postfix-api-mcp`
- SAP HANA mediante rutas estáticas configuradas en el entrypoint

## Rutas Estáticas

El contenedor `api-mcp` configura automáticamente las siguientes rutas al iniciar:
- `10.0.0.0/8` via `172.19.50.254`
- `172.16.1.0/24` via `172.19.50.254`

## Locale y Timezone

Todos los contenedores están configurados con:
- **Timezone:** America/Mexico_City (CST)
- **Locale:** es_MX.UTF-8

Esto asegura que las fechas y horas se muestren correctamente en español y con la zona horaria de México.

## Inicialización Automática de MSSQL

El contenedor `mssql-api-mcp` ejecuta un script de inicialización que:
1. Inicia SQL Server
2. Espera a que el servicio esté disponible
3. Verifica si existe la base de datos especificada en `MSSQL_DATABASE`
4. Si no existe, la crea automáticamente
5. Verifica si existe la tabla `SAP_EMPRESAS`
6. Si no existe, la crea con la siguiente estructura:

```sql
CREATE TABLE SAP_EMPRESAS (
    Instancia NVARCHAR(100) NOT NULL,
    Prueba BIT NOT NULL DEFAULT 0,
    ServiceLayer BIT NOT NULL DEFAULT 0,
    PrintHeadr NVARCHAR(255),
    CompnyAddr NVARCHAR(500),
    TaxIdNum NVARCHAR(50),
    PRIMARY KEY (Instancia)
)
```

| Columna      | Tipo           | Descripción                                      |
|--------------|----------------|--------------------------------------------------|
| Instancia    | NVARCHAR(100)  | Identificador único (PK)                         |
| Prueba       | BIT            | 1 si existe instancia _PRUEBAS en HANA, 0 si no  |
| ServiceLayer | BIT            | 1 si login en Service Layer exitoso, 0 si falló  |
| PrintHeadr   | NVARCHAR(255)  | Encabezado de impresión (o nombre de instancia)  |
| CompnyAddr   | NVARCHAR(500)  | Dirección de la empresa                          |
| TaxIdNum     | NVARCHAR(50)   | Número de identificación fiscal                  |

Esto garantiza que la base de datos y las tablas estén listas antes de que el servicio `api-mcp` intente conectarse.

### Tabla SAP_PROVEEDORES

La tabla `SAP_PROVEEDORES` se crea automáticamente al ejecutar `/inicializa_datos`:

```sql
CREATE TABLE SAP_PROVEEDORES (
    -- Identificación básica
    Instancia NVARCHAR(100) NOT NULL,
    CardCode NVARCHAR(50) NOT NULL,
    CardName NVARCHAR(200),
    GroupCode INT,
    FederalTaxID NVARCHAR(50),
    -- Fechas de auditoría
    CreateDate DATE,
    CreateTime TIME,
    UpdateDate DATE,
    UpdateTime TIME,
    -- Dirección principal
    Address NVARCHAR(500),
    Block NVARCHAR(200),
    ZipCode NVARCHAR(20),
    City NVARCHAR(100),
    County NVARCHAR(100),
    BillToState NVARCHAR(10),
    Country NVARCHAR(10),
    -- Dirección postal / Envío
    MailAddress NVARCHAR(500),
    MailZipCode NVARCHAR(20),
    ShipToState NVARCHAR(10),
    ShipToDefault NVARCHAR(100),
    -- Contacto
    Phone1 NVARCHAR(50),
    Phone2 NVARCHAR(50),
    Fax NVARCHAR(50),
    Cellular NVARCHAR(50),
    EmailAddress NVARCHAR(200),
    ContactPerson NVARCHAR(200),
    -- Condiciones financieras
    PayTermsGrpCode INT,
    PeymentMethodCode NVARCHAR(50),
    CreditLimit DECIMAL(18,2),
    MaxCommitment DECIMAL(18,2),
    DiscountPercent DECIMAL(5,2),
    PriceListNum INT,
    Currency NVARCHAR(10),
    -- Impuestos y deducciones
    DeductibleAtSource NVARCHAR(10),
    DeductionPercent DECIMAL(5,2),
    DeductionValidUntil DATE,
    VatGroupLatinAmerica NVARCHAR(20),
    -- Datos bancarios
    DefaultBankCode NVARCHAR(50),
    DefaultAccount NVARCHAR(100),
    BankCountry NVARCHAR(10),
    HouseBank NVARCHAR(50),
    HouseBankCountry NVARCHAR(10),
    HouseBankAccount NVARCHAR(50),
    HouseBankBranch NVARCHAR(20),
    HouseBankIBAN NVARCHAR(50),
    IBAN NVARCHAR(50),
    CreditCardCode INT,
    CreditCardNum NVARCHAR(50),
    CreditCardExpiration DATE,
    DebitorAccount NVARCHAR(50),
    -- Saldos y oportunidades
    CurrentAccountBalance DECIMAL(18,2),
    OpenDeliveryNotesBalance DECIMAL(18,2),
    OpenOrdersBalance DECIMAL(18,2),
    OpenChecksBalance DECIMAL(18,2),
    OpenOpportunities INT,
    -- Estado del proveedor
    Valid NVARCHAR(10),
    Frozen NVARCHAR(10),
    BlockDunning NVARCHAR(10),
    BackOrder NVARCHAR(10),
    PartialDelivery NVARCHAR(10),
    PRIMARY KEY (Instancia, CardCode)
)
```

| Grupo | Campos |
|-------|--------|
| Identificación | Instancia, CardCode, CardName, GroupCode, FederalTaxID |
| Fechas | CreateDate, CreateTime, UpdateDate, UpdateTime |
| Dirección principal | Address, Block, ZipCode, City, County, BillToState, Country |
| Dirección postal | MailAddress, MailZipCode, ShipToState, ShipToDefault |
| Contacto | Phone1, Phone2, Fax, Cellular, EmailAddress, ContactPerson |
| Financiero | PayTermsGrpCode, PeymentMethodCode, CreditLimit, MaxCommitment, DiscountPercent, PriceListNum, Currency |
| Impuestos | DeductibleAtSource, DeductionPercent, DeductionValidUntil, VatGroupLatinAmerica |
| Bancario | DefaultBankCode, DefaultAccount, BankCountry, HouseBank, HouseBankCountry, HouseBankAccount, HouseBankBranch, HouseBankIBAN, IBAN, CreditCardCode, CreditCardNum, CreditCardExpiration, DebitorAccount |
| Saldos | CurrentAccountBalance, OpenDeliveryNotesBalance, OpenOrdersBalance, OpenChecksBalance, OpenOpportunities |
| Estado | Valid, Frozen, BlockDunning, BackOrder, PartialDelivery |

## Job Tracking para Inicialización de Datos

El sistema de inicialización de datos utiliza un modelo asíncrono con tracking de jobs para permitir operaciones de larga duración.

### POST /inicializa_datos - Iniciar proceso de inicialización

Inicia un proceso asíncrono de inicialización y retorna inmediatamente un Job ID para monitorear el progreso.

**Parámetros opcionales:**
- `anos` (int, default: 0): Años de actividad a analizar (0=solo año actual, 1=actual+1 anterior, etc.)
- `email` (str, opcional): Email destinatario de notificaciones. Si no se proporciona o es igual a EMAIL_SUPERVISOR, usa el configurado en .env

```bash
# Inicialización básica
curl -X POST http://localhost:8000/inicializa_datos \
  -H "Authorization: Bearer <token>"

# Con parámetros personalizados
curl -X POST "http://localhost:8000/inicializa_datos?anos=2&email=supervisor@empresa.com" \
  -H "Authorization: Bearer <token>"
```

Respuesta:
```json
{
  "job_id": "174f89bd-9f47-48c0-ac2f-2fc75f926ec8",
  "message": "Inicialización iniciada. Use GET /inicializa_datos/status/{job_id} para consultar el progreso"
}
```

### GET /inicializa_datos/status/{job_id} - Consultar estado de un job

Consulta el estado actual de un job de inicialización específico.

**NOTA IMPORTANTE:** Este endpoint **NO requiere autenticación** para permitir el monitoreo durante el proceso de inicialización, cuando la sesión del usuario puede estar siendo recreada en la base de datos.

```bash
# Sin autenticación (recomendado durante inicialización)
curl http://localhost:8000/inicializa_datos/status/174f89bd-9f47-48c0-ac2f-2fc75f926ec8

# Con autenticación (también funciona)
curl http://localhost:8000/inicializa_datos/status/174f89bd-9f47-48c0-ac2f-2fc75f926ec8 \
  -H "Authorization: Bearer <token>"
```

**Manejo de errores:**
- Si el job no existe o el servidor reinició, retorna `404 Not Found`
- La interfaz web maneja automáticamente este caso mostrando el mensaje de completado con historial

Respuesta (en progreso):
```json
{
  "job_id": "174f89bd-9f47-48c0-ac2f-2fc75f926ec8",
  "status": "running",
  "message": "Sincronizando proveedores..."
}
```

Respuesta (completado):
```json
{
  "job_id": "174f89bd-9f47-48c0-ac2f-2fc75f926ec8",
  "status": "completed",
  "message": "Inicialización completada",
  "result": {
    "sap_empresas": {...},
    "service_layer": {...},
    "sap_proveedores": {...}
  }
}
```

### GET /inicializa_datos/jobs - Listar todos los jobs

Lista todos los jobs de inicialización del usuario actual.

```bash
curl http://localhost:8000/inicializa_datos/jobs \
  -H "Authorization: Bearer <token>"
```

Respuesta:
```json
{
  "username": "sa",
  "total_jobs": 3,
  "jobs": [
    {
      "job_id": "174f89bd-9f47-48c0-ac2f-2fc75f926ec8",
      "status": "completed",
      "created_at": "2026-01-22T10:00:00",
      "completed_at": "2026-01-22T10:05:30"
    },
    {
      "job_id": "a2b3c4d5-...",
      "status": "running",
      "created_at": "2026-01-22T11:00:00",
      "completed_at": null
    }
  ]
}
```

### Manejo de Reinicios del Servidor

El sistema de tracking de jobs utiliza un diccionario en memoria que se resetea cuando el servidor se reinicia (por ejemplo, cuando uvicorn detecta cambios en el código con `--reload`). Para manejar esta situación:

**Comportamiento del sistema:**
1. Los jobs en ejecución continúan procesándose en segundo plano incluso si el servidor reinicia
2. El tracking del job (estado, progreso) se pierde al reiniciar porque está en memoria
3. La interfaz web detecta automáticamente cuando un job ya no existe (404) durante el polling
4. Al detectar un 404, la interfaz:
   - Detiene el polling automáticamente
   - Re-habilita los botones de la tarjeta AJUSTES
   - Muestra mensaje de completado con el historial disponible de jobs
   - Permite al usuario verificar manualmente si la inicialización se completó

**Recomendación:**
- Si un job queda "atorado" en estado running después de un reinicio del servidor, refresca la página en el navegador
- Verifica el estado de la base de datos para confirmar si la inicialización se completó exitosamente
- Consulta los logs del contenedor para ver el resultado completo: `docker compose logs api-mcp --tail=200`

## Endpoint inicializa_datos - Detalle del proceso

El proceso de inicialización realiza las siguientes operaciones:

1. **Verificación de infraestructura:**
   - Verifica si la base de datos existe, si no la crea
   - Verifica si la tabla `SAP_EMPRESAS` existe, si no la crea

2. **Sincronización SAP_EMPRESAS:**
   - Elimina todos los registros existentes en `SAP_EMPRESAS` (MSSQL)
   - Obtiene la lista de instancias/empresas desde SAP HANA (solo lectura)
   - Para cada instancia:
     - Verifica si existe una versión `{instancia}_PRUEBAS` en HANA
     - Obtiene `PrintHeadr`, `CompnyAddr` y `TaxIdNum` de la tabla `OADM`
     - Si `PrintHeadr` está vacío, usa el nombre de la instancia
   - Inserta los registros en `SAP_EMPRESAS` (MSSQL)

3. **Test de Service Layer:**
   - Para cada instancia, intenta hacer login en Service Layer
   - Si el login es exitoso, hace logout para liberar la sesión
   - Actualiza el campo `ServiceLayer` en `SAP_EMPRESAS` (1=éxito, 0=fallo)
   - Si `EMAIL_SUPERVISOR` está configurado, envía un correo con los resultados
   - Retorna un resumen de conexiones exitosas y fallidas

4. **Sincronizar SAP_PROVEEDORES:**
   - Verifica si la tabla `SAP_PROVEEDORES` existe, si no la crea
   - Para cada instancia con `ServiceLayer = 1`:
     - Obtiene todos los proveedores (BusinessPartners con CardType='S') desde Service Layer
     - Actualiza registros existentes, inserta nuevos, elimina los que ya no existen en SAP
   - SAP Service Layer es la fuente de verdad
   - Retorna un resumen de proveedores actualizados/insertados/eliminados por instancia

5. **Análisis de actividad de proveedores:**
   - Analiza la actividad de proveedores usando el parámetro `anos` especificado
   - Crea/actualiza las tablas SAP_PROV_ACTIVOS y SAP_PROV_INACTIVOS
   - Crea la vista `dbo.vw_maestro_proveedores` (INNER JOIN entre SAP_PROV_ACTIVOS y SAP_PROVEEDORES)
   - Retorna un resumen de proveedores activos e inactivos

6. **Notificación por correo:**
   - **Destinatario:** Usa el parámetro `email` si se proporciona y es diferente a EMAIL_SUPERVISOR, caso contrario usa EMAIL_SUPERVISOR del .env
   - **Remitente:** aviso@progex.grupoexpansion
   - **Asunto:** Inicializacion de datos - YYYY-MM-DD HH:MM:SS
   - **Cuerpo:**
     ```
     Inicializacion de datos realizada

     SAP Empresas: 24 insertadas
     Service Layer: 21 exitosos, 3 fallidos (ALIANZA, BALLIANCE, ZZMAQGEX)
     SAP Proveedores: 13,199 sincronizados de 21 instancias
       - Actualizados: 12,500
       - Insertados: 699

     Desglose de proveedores por instancia:
       EXPANSION: 4,075
       HEARST: 1,272
       ANDENES: 1,215
       CINETICA: 1,171
       NOTICIAS: 1,077
       AIRPORTS: 1,069
       ...
     ```
   - **Adjunto:** `inicializacion_YYYYMMDD_HHMMSS.json` con resumen (sin desglose detallado):
     ```json
     {
       "sap_empresas": {...},
       "service_layer": {...},
       "sap_proveedores": {
         "total_instancias": 21,
         "proveedores_actualizados": 12500,
         "proveedores_insertados": 699,
         "proveedores_eliminados": 0,
         "errores": []
       }
     }
     ```

**Modo de operación:** Se controla con el endpoint `/pruebas/{valor}`:
- `/pruebas/0`: modo productivo (sincroniza proveedores de instancias normales)
- `/pruebas/1`: modo pruebas (sincroniza proveedores de instancias con `Prueba = 1`, conectando a `{instancia}_PRUEBAS`)

```bash
# Establecer modo productivo
curl -X POST http://localhost:8000/pruebas/0 \
  -H "Authorization: Bearer <token>"

# Establecer modo pruebas
curl -X POST http://localhost:8000/pruebas/1 \
  -H "Authorization: Bearer <token>"

# Inicializar datos (usa el modo establecido)
curl -X POST http://localhost:8000/inicializa_datos \
  -H "Authorization: Bearer <token>"
```

Respuesta:
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
    "detalle_exitosos": ["AIRPORTS", "ANDENES", "..."],
    "detalle_fallidos": [
      {"instancia": "ALIANZA", "error": "Login failed"},
      {"instancia": "BALLIANCE", "error": "Login failed"},
      {"instancia": "ZZMAQGEX", "error": "Login failed"}
    ],
    "email_enviado": {"success": true}
  },
  "sap_proveedores": {
    "total_instancias": 21,
    "proveedores_actualizados": 12500,
    "proveedores_insertados": 699,
    "proveedores_eliminados": 0,
    "instancias_procesadas": [
      {"instancia": "AIRPORTS", "actualizados": 1000, "insertados": 69, "proveedores": 1069},
      {"instancia": "ANDENES", "actualizados": 1200, "insertados": 15, "proveedores": 1215},
      {"instancia": "EXPANSION", "actualizados": 4000, "insertados": 75, "proveedores": 4075},
      ...
    ],
    "errores": []
  }
}
```

## Endpoints de actualización

### POST /actualizar_empresas

Actualiza `SAP_EMPRESAS` con los datos actuales de SAP HANA. SAP HANA es la fuente de verdad.

**Comportamiento:**
- Actualiza empresas existentes con datos de OADM (PrintHeadr, CompnyAddr, TaxIdNum)
- Inserta nuevas empresas que aparezcan en HANA
- Elimina empresas que ya no existen en HANA
- **Preserva** el campo `ServiceLayer` existente

```bash
curl -X POST http://localhost:8000/actualizar_empresas \
  -H "Authorization: Bearer <token>"
```

Respuesta:
```json
{
  "total_empresas": 24,
  "actualizadas": 22,
  "insertadas": 2,
  "eliminadas": 0,
  "errores": []
}
```

### POST /actualizar_proveedores

Actualiza `SAP_PROVEEDORES` con los datos actuales de SAP Service Layer. SAP es la fuente de verdad.

**Modo de operación:** Se controla con el endpoint `/pruebas/{valor}`:
- `/pruebas/0`: modo productivo (usa instancias normales con `ServiceLayer = 1`)
- `/pruebas/1`: modo pruebas (usa instancias con `ServiceLayer = 1` Y `Prueba = 1`, conecta a `{instancia}_PRUEBAS`)

**Comportamiento:**
- Actualiza proveedores existentes con todos sus campos
- Inserta nuevos proveedores que aparezcan en SAP
- Elimina proveedores que ya no existen en SAP
- Solo procesa instancias según el modo establecido

```bash
# Consultar modo actual
curl http://localhost:8000/pruebas \
  -H "Authorization: Bearer <token>"

# Actualizar proveedores (usa el modo establecido)
curl -X POST http://localhost:8000/actualizar_proveedores \
  -H "Authorization: Bearer <token>"
```

Respuesta:
```json
{
  "modo": "productivo",
  "total_instancias": 21,
  "proveedores_actualizados": 13000,
  "proveedores_insertados": 199,
  "proveedores_eliminados": 5,
  "instancias_procesadas": [
    {"instancia": "EXPANSION", "actualizados": 4000, "insertados": 75, "proveedores": 4075},
    ...
  ],
  "errores": []
}
```

## Endpoint test_service_layer

El endpoint `GET /test_service_layer` prueba la conexión a SAP B1 Service Layer para todas las instancias:

1. Obtiene la lista de instancias desde HANA
2. Para cada instancia, intenta hacer login en Service Layer
3. Si el login es exitoso, hace logout para liberar la sesión
4. Actualiza el campo `ServiceLayer` en `SAP_EMPRESAS` (1=éxito, 0=fallo)
5. Si `EMAIL_SUPERVISOR` está configurado, envía un correo con los resultados
6. Retorna un resumen de conexiones exitosas y fallidas

```bash
curl http://localhost:8000/test_service_layer \
  -H "Authorization: Bearer <token>"
```

Respuesta:
```json
{
  "total": 24,
  "exitosos": 21,
  "fallidos": 3,
  "detalle_exitosos": ["AIRPORTS", "ANDENES", "..."],
  "detalle_fallidos": [
    {"instancia": "ALIANZA", "error": "Login failed"},
    {"instancia": "BALLIANCE", "error": "Login failed"},
    {"instancia": "ZZMAQGEX", "error": "Login failed"}
  ]
}
```

## Endpoint proveedores

El endpoint `GET /proveedores/{instancia}` obtiene los proveedores (BusinessPartners con CardType='S') desde SAP B1 Service Layer.

### Configuración de peticiones a Service Layer

Todas las peticiones a Service Layer incluyen por defecto:
- **Parámetro:** `$inlinecount=allpages` - Retorna el conteo total de registros
- **Header:** `Prefer: odata.maxpagesize=N` - Donde N es el valor del parámetro `top` (si se proporciona) o 0 para retornar todos los registros sin paginación

### Campos retornados

El endpoint retorna los siguientes campos de cada proveedor, organizados por grupo:

| Grupo | Campos |
|-------|--------|
| **Identificación** | CardCode, CardName, GroupCode, FederalTaxID |
| **Fechas** | CreateDate, CreateTime, UpdateDate, UpdateTime |
| **Dirección principal** | Address, Block, ZipCode, City, County, BillToState, Country |
| **Dirección postal** | MailAddress, MailZipCode, ShipToState, ShipToDefault |
| **Contacto** | Phone1, Phone2, Fax, Cellular, EmailAddress, ContactPerson |
| **Financiero** | PayTermsGrpCode, PeymentMethodCode, CreditLimit, MaxCommitment, DiscountPercent, PriceListNum, Currency |
| **Impuestos** | DeductibleAtSource, DeductionPercent, DeductionValidUntil, VatGroupLatinAmerica |
| **Bancario** | DefaultBankCode, DefaultAccount, BankCountry, HouseBank, HouseBankCountry, HouseBankAccount, HouseBankBranch, HouseBankIBAN, IBAN, CreditCardCode, CreditCardNum, CreditCardExpiration, DebitorAccount |
| **Saldos** | CurrentAccountBalance, OpenDeliveryNotesBalance, OpenOrdersBalance, OpenChecksBalance, OpenOpportunities |
| **Estado** | Valid, Frozen, BlockDunning, BackOrder, PartialDelivery |

## Endpoint maestro_proveedores

El endpoint `GET /maestro_proveedores` consulta una vista pivoteada que muestra todos los proveedores con una columna por cada instancia SAP.

### Estructura de la respuesta

| Columna | Descripción |
|---------|-------------|
| CardName | Nombre del proveedor |
| GroupCode | Código de grupo |
| FederalTaxID | RFC del proveedor |
| AIRPORTS, ANDENES, ... | CardCode del proveedor en cada instancia (NULL si no existe) |

### Parámetros

| Parámetro | Descripción |
|-----------|-------------|
| `top` | Limita el número de registros retornados |
| `card_name` | Filtra por nombre que contenga el valor |
| `federal_tax_id` | Filtra por RFC que contenga el valor |

### Ejemplo de uso

```bash
# Buscar proveedores por nombre
curl "http://localhost:8000/maestro_proveedores?card_name=DAHFSA&top=5" \
  -H "Authorization: Bearer <token>"
```

Respuesta:
```json
{
  "success": true,
  "total": 3,
  "columnas": ["CardName", "GroupCode", "FederalTaxID", "AIRPORTS", "ANDENES", ...],
  "proveedores": [
    {
      "CardName": "DAHFSA DE MÉXICO, S.A. DE C.V.",
      "GroupCode": 101,
      "FederalTaxID": "DME0905224P7",
      "AIRPORTS": "N1000119",
      "ANDENES": "N1000119",
      "AUTOBUSES": "N1000119",
      "EXPANSION": "N1000119",
      "CINETICA": null,
      ...
    }
  ]
}
```

### Notas

- La vista se actualiza automáticamente al ejecutar `/inicializa_datos`
- Las columnas de instancias son dinámicas y se generan según las instancias existentes en SAP_PROVEEDORES
- Un proveedor puede tener el mismo CardCode en múltiples instancias o CardCodes diferentes

## Análisis de Inconsistencias

El sistema incluye una función interna `analizar_inconsistencias_maestro_proveedores()` que detecta problemas de calidad de datos en el maestro de proveedores.

### Tipos de Inconsistencias Detectadas

1. **Mismo RFC+GroupCode con diferentes nombres**: Proveedores con el mismo RFC y grupo pero registrados con nombres distintos
2. **Mismo nombre con diferentes RFCs**: Proveedores con el mismo nombre pero RFCs diferentes
3. **Diferentes CardCodes entre instancias**: Mismo proveedor (RFC) con códigos diferentes en distintas instancias SAP
4. **Valores NULL**: Proveedores sin CardName o sin RFC
5. **Proveedores sin email**: Proveedores que no tienen EmailAddress registrado (NULL o vacío)

### Uso de la Función

Esta función es de uso interno y no está expuesta como endpoint público. Se puede invocar desde código Python:

```python
from database import analizar_inconsistencias_maestro_proveedores

resultado = analizar_inconsistencias_maestro_proveedores()
```

### Reporte Automático por Correo

La función envía automáticamente un correo al `EMAIL_SUPERVISOR` configurado con:

- **Resumen ejecutivo** con totales de cada tipo de inconsistencia
- **Archivo Excel adjunto** con el detalle completo de todas las inconsistencias en múltiples hojas

Ejemplo de resumen:

```
REPORTE DE INCONSISTENCIAS - MAESTRO DE PROVEEDORES
================================================================================
Fecha: 2026-01-20 04:54:08
Total registros en vista: 7,627

RESUMEN DE INCONSISTENCIAS:
--------------------------------------------------------------------------------
1. Mismo RFC+GroupCode, diferente nombre: 643 casos
2. Mismo nombre, diferente RFC: 89 casos
3. Diferentes CardCodes entre instancias: 1,234 casos
4. Proveedores con CardName NULL: 0
5. Proveedores con RFC NULL: 0
6. Proveedores sin EmailAddress: 1,500 casos

Adjunto encontrará un archivo Excel con el detalle completo de todas las inconsistencias.
```

### Estructura del Archivo Excel

El archivo Excel adjunto (`inconsistencias_YYYYMMDD_HHMMSS.xlsx`) contiene múltiples hojas:

#### 1. Hoja "Resumen"
Tabla resumen con el total de cada tipo de inconsistencia.

#### 2. Hoja "RFC - Diferentes Nombres"
| RFC | GroupCode | Nombres Diferentes | Nombres |
|-----|-----------|-------------------|---------|
| XEXX010101000 | 103 | 394 | LINEUP SYSTEMS \|\| LEONARD GARY \|\| ... |

#### 3. Hoja "Nombre - Diferentes RFCs"
| Nombre | RFCs Diferentes | RFCs |
|--------|----------------|------|
| PROVEEDOR EJEMPLO | 2 | ABC123456789, XYZ987654321 |

#### 4. Hoja "Diferentes CardCodes"
| RFC | Nombre | Códigos Diferentes | Total Instancias | Detalle CardCodes |
|-----|--------|-------------------|------------------|-------------------|
| ABC123456789 | PROVEEDOR EJEMPLO | 3 | 5 | AIRPORTS: N1000100 \| EXPANSION: N1000200 \| CINETICA: N1000300 |

#### 5. Hoja "Sin Email"
| CardCode | Nombre | RFC | Instancia |
|----------|--------|-----|-----------|
| N1000255 | PROVEEDOR SIN EMAIL | ABC123456789 | AIRPORTS |

### Características del Excel

- **Formato profesional**: Encabezados con fondo azul y texto blanco
- **Columnas ajustadas**: Anchos optimizados para lectura
- **Organización por hojas**: Cada tipo de inconsistencia en su propia hoja
- **Fácil análisis**: Datos tabulados listos para filtrado y análisis en Excel

## Análisis de Actividad de Proveedores

El endpoint `POST /proveedores/analizar-actividad` analiza la actividad de los proveedores en SAP Business One en los últimos N años.

### Funcionamiento

El endpoint revisa por cada proveedor en el maestro si tiene documentos de compra (facturas OPCH o órdenes de compra OPOR) en el período especificado, consultando todas las instancias SAP donde el proveedor está registrado.

### Uso del Endpoint

```bash
# Analizar año actual + 1 año anterior (default: anos=1)
curl -X POST "http://localhost:8000/proveedores/analizar-actividad" \
  -H "Authorization: Bearer <token>"

# Analizar solo el año actual (anos=0)
curl -X POST "http://localhost:8000/proveedores/analizar-actividad?anos=0" \
  -H "Authorization: Bearer <token>"

# Analizar año actual + 2 años anteriores (anos=2)
curl -X POST "http://localhost:8000/proveedores/analizar-actividad?anos=2" \
  -H "Authorization: Bearer <token>"
```

### Parámetros

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `anos` | int | 1 | Años adicionales hacia atrás (0=solo año actual, 1=actual+1 anterior, 2=actual+2 anteriores) |

### Reporte Automático por Correo

La función envía automáticamente un correo al `EMAIL_SUPERVISOR` configurado con:

- **Resumen ejecutivo** con totales de proveedores activos e inactivos
- **Archivo Excel adjunto** con el detalle de la actividad

Ejemplo de resumen:

```
REPORTE DE ACTIVIDAD DE PROVEEDORES
================================================================================
Fecha: 2026-01-20 10:30:00
Período analizado: Últimos 3 años
Total proveedores analizados: 7,627

RESUMEN:
--------------------------------------------------------------------------------
Proveedores ACTIVOS: 5,234 (68.6%)
Proveedores INACTIVOS: 2,393 (31.4%)

Adjunto encontrará un archivo Excel con el detalle completo de la actividad.
```

### Estructura del Archivo Excel

El archivo Excel adjunto (`Actividad_Proveedores_Ultimos_N_Anos_YYYYMMDD_HHMMSS.xlsx`) contiene dos hojas:

#### 1. Hoja "Activos"
Proveedores con actividad en el período especificado.

| CardName | FederalTaxID | CardCode | GroupCode | Total Documentos | Saldo Total | Instancias con Actividad | Última Fecha |
|----------|--------------|----------|-----------|------------------|-------------|-------------------------|--------------|
| PROVEEDOR ACTIVO SA DE CV | ABC123456789 | N1000100, N1000200 | 101 | 45 | 125,500.00 | AIRPORTS, EXPANSION, CINETICA | 2026-01-15 |

**Columnas:**
- **CardName**: Nombre del proveedor (campo de base de datos)
- **FederalTaxID**: RFC del proveedor (campo de base de datos)
- **CardCode**: Códigos del proveedor en las instancias donde tiene actividad (separados por coma)
- **GroupCode**: Código de grupo del proveedor
- **Total Documentos**: Número total de facturas y órdenes de compra en todas las instancias
- **Saldo Total**: Saldo total de documentos (CurrentAccountBalance) sumado de todas las instancias
- **Instancias con Actividad**: Lista de instancias SAP donde tiene documentos
- **Última Fecha**: Fecha del documento más reciente

#### 2. Hoja "Inactivos"
Proveedores sin actividad en el período especificado.

| CardName | FederalTaxID | CardCode | GroupCode |
|----------|--------------|----------|-----------|
| PROVEEDOR INACTIVO SA DE CV | XYZ987654321 | N1000300, N1000400 | 102 |

**Columnas:**
- **CardName**: Nombre del proveedor (campo de base de datos)
- **FederalTaxID**: RFC del proveedor (campo de base de datos)
- **CardCode**: Códigos del proveedor en todas las instancias (separados por coma)
- **GroupCode**: Código de grupo del proveedor

### Criterios de Clasificación

- **Activo**: Tiene al menos un documento (factura OPCH o orden de compra OPOR) en el período especificado en cualquier instancia SAP
- **Inactivo**: No tiene ningún documento en el período especificado en ninguna instancia SAP

### Tablas de Resultados

La función crea/recrea dos tablas en MSSQL en cada ejecución:

**SAP_PROV_ACTIVOS:**
```sql
CREATE TABLE SAP_PROV_ACTIVOS (
    Instancia NVARCHAR(50) NOT NULL,
    CardCode NVARCHAR(50) NOT NULL,
    CardName NVARCHAR(200),
    FederalTaxID NVARCHAR(50),
    GroupCode INT,
    TotalDocumentos INT,
    SaldoDocumentos DECIMAL(18,2),
    UltimaFecha DATE,
    FechaAnalisis DATETIME,
    PRIMARY KEY (Instancia, CardCode)
)
```

**SAP_PROV_INACTIVOS:**
```sql
CREATE TABLE SAP_PROV_INACTIVOS (
    Instancia NVARCHAR(50) NOT NULL,
    CardCode NVARCHAR(50) NOT NULL,
    CardName NVARCHAR(200),
    FederalTaxID NVARCHAR(50),
    GroupCode INT,
    FechaAnalisis DATETIME,
    PRIMARY KEY (Instancia, CardCode)
)
```

**Comportamiento:** Las tablas se eliminan (`DROP TABLE IF EXISTS`) y se recrean en cada ejecución para garantizar que la estructura esté actualizada y los datos sean frescos.

### Notas Técnicas

- La función consulta las tablas `OPCH` (Facturas de proveedores) y `OPOR` (Órdenes de compra) en SAP HANA
- Se analiza cada instancia SAP de forma independiente
- Si un proveedor tiene actividad en al menos una instancia, se considera activo
- La última fecha mostrada corresponde al documento más reciente en todas las instancias
- El total de documentos es la suma de facturas y órdenes en todas las instancias
- El parámetro `anos` indica años adicionales hacia atrás (0=solo año actual, 1=actual+1 anterior, 2=actual+2 anteriores, etc.)
- Las tablas SAP_PROV_ACTIVOS y SAP_PROV_INACTIVOS se eliminan y recrean completamente en cada ejecución

## Servidor de Correo (Postfix)

El proyecto incluye un contenedor Postfix para el envío de correos electrónicos. Por defecto está configurado para envío directo (sin relay).

### Características

- **DNS externo:** Usa servidores DNS de Google (8.8.8.8, 8.8.4.4) para resolver dominios externos
- **Reescritura de remitente:** Todos los correos salen con remitente `aviso@progex.grupoexpansion`
- **Redes permitidas:** 172.16.0.0/12, 192.168.0.0/16, 10.0.0.0/8
- **Puerto expuesto:** 25
- **Timezone:** America/Mexico_City

### Configuración Básica

Las siguientes variables controlan el envío de correos desde la API:

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `EMAIL_SUPERVISOR` | Destinatario de notificaciones | (ninguno) |
| `SMTP_HOST` | Hostname del servidor SMTP | `postfix-api-mcp` |
| `SMTP_PORT` | Puerto SMTP | `25` |
| `EMAIL_FROM` | Dirección del remitente | `aviso@progex.grupoexpansion` |

### Configuración de Relay Externo (Opcional)

Para enviar correos a través de un servidor externo (Office 365, Gmail, etc.), descomentar y configurar las siguientes variables en `.env`:

```env
POSTFIX_RELAY_HOST=smtp.office365.com
POSTFIX_RELAY_PORT=587
POSTFIX_RELAY_USER=usuario@dominio.com
POSTFIX_RELAY_PASSWORD=password
```

Y descomentar las líneas correspondientes en `docker-compose.yml`:

```yaml
environment:
  - POSTFIX_RELAY_HOST=${POSTFIX_RELAY_HOST:-}
  - POSTFIX_RELAY_PORT=${POSTFIX_RELAY_PORT:-587}
  - POSTFIX_RELAY_USER=${POSTFIX_RELAY_USER:-}
  - POSTFIX_RELAY_PASSWORD=${POSTFIX_RELAY_PASSWORD:-}
```

### Verificar Estado de Postfix

```bash
docker exec postfix-api-mcp postfix status
```

### Ver Logs de Correo

```bash
docker logs postfix-api-mcp
```

### Verificar Timezone y Locale

```bash
docker exec api-mcp date
docker exec mssql-api-mcp date
docker exec postfix-api-mcp date
```

Todos deben mostrar la hora en formato español con zona horaria CST (America/Mexico_City).

## Notas Técnicas

### Límite de parámetros en SQL Server

SQL Server tiene un límite de aproximadamente 2,100 parámetros por consulta. Esto afecta operaciones con cláusulas `IN` o `NOT IN` cuando se manejan grandes volúmenes de datos.

**Solución implementada:** Para la sincronización de proveedores (que puede manejar más de 4,000 registros por instancia), se utiliza una **tabla temporal** en lugar de `NOT IN`:

```sql
-- En lugar de esto (falla con >2100 parámetros):
DELETE FROM SAP_PROVEEDORES
WHERE Instancia = ? AND CardCode NOT IN (?, ?, ?, ...)

-- Se usa esto (sin límite de parámetros):
CREATE TABLE #CardCodesSAP (CardCode NVARCHAR(50) PRIMARY KEY)
INSERT INTO #CardCodesSAP (CardCode) VALUES (?), (?), ...  -- en lotes de 1000
DELETE p FROM SAP_PROVEEDORES p
WHERE p.Instancia = ?
AND NOT EXISTS (SELECT 1 FROM #CardCodesSAP t WHERE t.CardCode = p.CardCode)
DROP TABLE #CardCodesSAP
```

Esta estrategia es más eficiente y escala sin problemas para cualquier cantidad de registros.

### Rendimiento de sincronización

El endpoint `/inicializa_datos` sincroniza aproximadamente 13,000+ proveedores de 21 instancias SAP. Los tiempos de ejecución típicos son:

| Operación | Registros | Tiempo aproximado |
|-----------|-----------|-------------------|
| SAP Empresas | 24 | < 5 segundos |
| Test Service Layer | 24 instancias | < 30 segundos |
| SAP Proveedores | ~13,000 | 2-5 minutos |

**Recomendación:** Usar un timeout de al menos 10 minutos para el endpoint `/inicializa_datos`.

## Pruebas

El proyecto incluye reportes detallados de las pruebas realizadas en el directorio `tests/`.

### Script de Prueba Completa del Sistema

**Archivo:** [tests/test_completo_sistema.sh](tests/test_completo_sistema.sh)

Script automatizado que ejecuta una prueba completa del flujo del sistema:

1. **Autenticación**: Login y obtención de token
2. **Inicialización de datos**: Ejecuta `/inicializa_datos` y monitorea el job
3. **Análisis de actividad**: Prueba análisis con diferentes períodos de años
4. **Consulta de maestro**: Obtiene lista consolidada de proveedores
5. **Listado de jobs**: Verifica historial de ejecuciones
6. **Logout**: Cierra la sesión

**Ejecución:**
```bash
chmod +x tests/test_completo_sistema.sh
./tests/test_completo_sistema.sh
```

**Requisitos:**
- `curl` y `jq` instalados
- API corriendo en `http://localhost:8000`
- Credenciales válidas en el script

### Pruebas del Sistema de Session Tokens

**Archivo:** [tests/prueba_session_tokens.md](tests/prueba_session_tokens.md)

**Fecha:** 2026-01-21

**Resultado:** ✅ TODAS LAS PRUEBAS EXITOSAS

El sistema de session tokens fue probado exhaustivamente, verificando:

1. ✅ Login y creación de sesión
2. ✅ Autenticación con token
3. ✅ Sliding expiration (renovación automática)
4. ✅ Listado de sesiones activas
5. ✅ Logout individual
6. ✅ Logout de todas las sesiones
7. ✅ Limpieza de sesiones expiradas
8. ✅ Múltiples sesiones concurrentes

**Características verificadas:**
- Sliding expiration funciona correctamente (LastActivity se actualiza en cada petición)
- Tokens se invalidan inmediatamente al hacer logout
- Múltiples sesiones por usuario soportadas
- Sistema completamente funcional y listo para producción

Para más detalles, consultar el reporte completo en `tests/prueba_session_tokens.md`.

### Pruebas de Preservación de Sesión en inicializa_datos

**Archivo:** [tests/prueba_inicializa_datos_session_preservation.md](tests/prueba_inicializa_datos_session_preservation.md)

**Fecha:** 2026-01-21

**Resultado:** ✅ TODAS LAS PRUEBAS EXITOSAS

El endpoint `/inicializa_datos` fue modificado para preservar la sesión del usuario cuando elimina y recrea la base de datos.

**Escenarios probados:**

1. ✅ Base de datos no existe: Login crea BD automáticamente
2. ✅ Base de datos existe: inicializa_datos preserva sesión del usuario
3. ✅ Múltiples ejecuciones: Token siempre permanece válido

**Características verificadas:**
- La sesión del usuario se restaura automáticamente con el mismo SessionID
- El token permanece válido después de eliminar/recrear la base de datos
- El sistema de autenticación funciona desde el primer momento (incluso sin BD)
- No se requiere re-autenticación después de ejecutar inicializa_datos
- 24 empresas insertadas correctamente en SAP_EMPRESAS
- 21 de 24 instancias con Service Layer funcional

Para más detalles, consultar el reporte completo en `tests/prueba_inicializa_datos_session_preservation.md`.

## Configuración de Git

### Hook prepare-commit-msg

El repositorio incluye un hook de Git configurado en `.git/hooks/prepare-commit-msg` que automáticamente remueve líneas de co-autoría relacionadas con herramientas de IA de los mensajes de commit.

**Función del hook:**
- Elimina líneas `Co-Authored-By` que contengan "claude" o dominios "anthropic.com"
- Limpia líneas en blanco residuales en los mensajes de commit
- Se ejecuta automáticamente antes de cada commit

**Ubicación:** `.git/hooks/prepare-commit-msg`

**Nota:** Este hook ya está configurado y activo en el repositorio local. No requiere configuración adicional.

## Configuración de Timezone y Locales

El sistema está configurado para usar **America/Mexico_City** como timezone y **es_MX.UTF-8** como locale en todos los contenedores.

### Configuración en docker-compose.yml

Todos los servicios (api-mcp, mssql-api-mcp, postfix-api-mcp) tienen las siguientes variables de entorno:

```yaml
environment:
  - TZ=${TZ:-America/Mexico_City}
  - LANG=${LANG:-es_MX.UTF-8}
  - LC_ALL=${LC_ALL:-es_MX.UTF-8}
```

### Configuración en Dockerfiles

Todos los Dockerfiles instalan y configuran los locales necesarios:

1. **Dockerfile.api-mcp**: Instala `locales` y `tzdata`, genera `es_MX.UTF-8`
2. **Dockerfile.mssql2022**: Instala `locales`, genera `es_MX.UTF-8` y actualiza locale
3. **Dockerfile.postfix**: Instala `locales` y `tzdata`, genera `es_MX.UTF-8`

### Timezone-aware datetimes en Python

El código Python usa `utils.now()` en lugar de `datetime.now()` para asegurar que todas las fechas sean timezone-aware:

```python
from utils import now as tz_now

# Crear fecha con timezone awareness
fecha_actual = tz_now()  # datetime con ZoneInfo('America/Mexico_City')
```

**Archivos actualizados:**
- `app/utils.py`: Función helper `now()` que retorna datetime con timezone
- `app/main.py`: Usa `tz_now()` para registros de jobs
- `app/session.py`: Usa `tz_now()` para gestión de sesiones
- `app/database.py`: Usa `tz_now()` para timestamps de emails y reportes

Esta configuración asegura que:
- Todas las fechas se almacenan y muestran en timezone México (GMT-6)
- Los formatos de fecha/hora respetan el locale español mexicano
- No aparecen fechas inválidas (31/12/1969) por timezone-naive datetimes
