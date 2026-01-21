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
│   ├── auth.py                  # Autenticación JWT
│   ├── config.py                # Configuración desde variables de entorno
│   ├── database.py              # Conexiones a MSSQL y HANA
│   ├── main.py                  # Punto de entrada de la API
│   ├── mcp.py                   # Endpoints MCP
│   └── sap_service_layer.py     # Cliente SAP B1 Service Layer
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

## Ejecución

```bash
docker compose up -d
```

## Endpoints Disponibles

### Autenticación

- `POST /auth/login` - Obtener token JWT

### Sistema

- `GET /health` - Verificar estado del servicio
- `GET /me` - Información del usuario autenticado
- `GET /pruebas` - Consultar modo actual (productivo/pruebas)
- `POST /pruebas/{valor}` - Establecer modo (0=productivo, 1=pruebas)

### SAP HANA

- `GET /empresas_registradas` - Listar empresas SAP B1 registradas en HANA (requiere JWT)

### MSSQL

- `POST /inicializa_datos` - Inicializa las tablas SAP_EMPRESAS y SAP_PROVEEDORES (requiere JWT)
- `POST /actualizar_empresas` - Actualiza SAP_EMPRESAS con datos de HANA (SAP es fuente de verdad, preserva ServiceLayer)
- `POST /actualizar_proveedores` - Actualiza SAP_PROVEEDORES con datos de Service Layer (requiere JWT)

### SAP Service Layer

- `GET /proveedores/{instancia}` - Obtener proveedores de una instancia SAP (requiere JWT)
- `GET /test_service_layer` - Prueba conexión a Service Layer para todas las instancias SAP (requiere JWT)
- `GET /maestro_proveedores` - Vista consolidada de proveedores con CardCode por instancia (requiere JWT)

### MCP (requieren JWT con scopes específicos)

- `POST /mcp/tools/list` - Listar herramientas disponibles (scope: `mcp:tools:list`)
- `POST /mcp/tools/call` - Ejecutar herramienta (scope: `mcp:tools:call`)
- `POST /mcp/resources/list` - Listar recursos disponibles (scope: `mcp:resources:list`)
- `POST /mcp/resources/read` - Leer recurso (scope: `mcp:resources:read`)

## Uso de la API

### Obtener Token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "sa", "password": "tu_password"}'
```

### Usar Endpoints Protegidos

```bash
curl http://localhost:8000/me \
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

## Endpoint inicializa_datos

El endpoint `POST /inicializa_datos` realiza las siguientes operaciones:

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

5. **Notificación por correo:**
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

El sistema incluye una función interna `analizar_actividad_proveedores(anos)` que analiza la actividad de los proveedores en SAP Business One en los últimos N años.

### Funcionamiento

La función revisa por cada proveedor en el maestro si tiene documentos de compra (facturas OPCH o órdenes de compra OPOR) en el período especificado, consultando todas las instancias SAP donde el proveedor está registrado.

### Uso de la Función

Esta función es de uso interno y no está expuesta como endpoint público. Se puede invocar desde código Python:

```python
from database import analizar_actividad_proveedores

# Analizar últimos 3 años (default)
resultado = analizar_actividad_proveedores()

# Analizar últimos 5 años
resultado = analizar_actividad_proveedores(anos=5)
```

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

| CardName | FederalTaxID | CardCode | GroupCode | Total Documentos | Instancias con Actividad | Última Fecha |
|----------|--------------|----------|-----------|------------------|-------------------------|--------------|
| PROVEEDOR ACTIVO SA DE CV | ABC123456789 | N1000100, N1000200 | 101 | 45 | AIRPORTS, EXPANSION, CINETICA | 2026-01-15 |

**Columnas:**
- **CardName**: Nombre del proveedor (campo de base de datos)
- **FederalTaxID**: RFC del proveedor (campo de base de datos)
- **CardCode**: Códigos del proveedor en las instancias donde tiene actividad (separados por coma)
- **GroupCode**: Código de grupo del proveedor
- **Total Documentos**: Número total de facturas y órdenes de compra en todas las instancias
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
