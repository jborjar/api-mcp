# Sistema de Proveedores Activos

**Fecha:** 2026-01-21
**Branch:** Modifica-flujo-inicializa_datos
**Versión:** 2.1.0

---

## Descripción General

El sistema de proveedores activos permite consultar todos los proveedores que están:
- **Válidos** (`Valid = 'Y'` en SAP)
- **No congelados** (`Frozen = 'N'` en SAP)

Esta funcionalidad es **consciente del modo** (productivo/pruebas), lo que significa que:
- En modo **productivo**: consulta proveedores de instancias con `SL=1`
- En modo **pruebas**: consulta proveedores de instancias con `SLP=1` AND `Prueba=1`

---

## Arquitectura

### Función en database.py

```python
def get_proveedores_activos(
    instancia: str | None = None,
    limit: int | None = None,
    offset: int = 0
) -> dict
```

**Características:**
- Consulta la tabla `SAP_PROVEEDORES`
- Filtra automáticamente por `Valid='Y'` AND `Frozen='N'`
- Usa `get_instancias_con_service_layer()` para obtener las instancias según el modo
- Soporta paginación con `limit` y `offset`
- Permite filtrar por instancia específica

**Flujo interno:**
1. Determina el modo actual (productivo/pruebas) usando `get_modo_pruebas()`
2. Obtiene las instancias válidas según el modo:
   - Modo productivo → usa vista `vw_productivo`
   - Modo pruebas → usa vista `vw_pruebas`
3. Si se especifica una instancia, valida que esté en las instancias del modo actual
4. Ejecuta query SQL con filtros de proveedores activos
5. Retorna resultados paginados

**Retorno:**
```json
{
  "success": true,
  "modo": "productivo",
  "total": 12345,
  "limit": 100,
  "offset": 0,
  "count": 100,
  "proveedores": [
    {
      "Instancia": "EXPANSION",
      "CardCode": "P0001",
      "CardName": "Proveedor Ejemplo S.A.",
      "GroupCode": 100,
      "FederalTaxID": "RFC123456789",
      "Phone1": "5512345678",
      "EmailAddress": "contacto@ejemplo.com",
      ...
    }
  ],
  "instancias_incluidas": ["EXPANSION", "HEARST", "ANDENES", ...]
}
```

### Endpoint en main.py

```
GET /proveedores/activos
```

**Autenticación:** Requerida (Bearer token)

**Query Parameters:**
- `instancia` (opcional): Filtrar por instancia específica
- `limit` (opcional): Límite de resultados por página
- `offset` (opcional): Número de registros a saltar (por defecto: 0)

**Respuestas:**
- `200 OK`: Proveedores activos retornados exitosamente
- `400 Bad Request`: Error en la consulta (ej: instancia no válida para el modo actual)
- `401 Unauthorized`: Token inválido o expirado

---

## Ejemplos de Uso

### Ejemplo 1: Obtener todos los proveedores activos (modo productivo)

```bash
# 1. Asegurar que estamos en modo productivo
curl -X DELETE http://localhost:8000/pruebas \
  -H "Authorization: Bearer $TOKEN"

# 2. Consultar proveedores activos
curl -X GET "http://localhost:8000/proveedores/activos" \
  -H "Authorization: Bearer $TOKEN"
```

**Resultado:**
```json
{
  "success": true,
  "modo": "productivo",
  "total": 12199,
  "limit": null,
  "offset": 0,
  "count": 12199,
  "proveedores": [...],
  "instancias_incluidas": [
    "AIRPORTS",
    "ANDENES",
    "CINETICA",
    "EXPANSION",
    "HEARST",
    ...
  ]
}
```

### Ejemplo 2: Obtener proveedores activos con paginación

```bash
# Primera página (100 proveedores)
curl -X GET "http://localhost:8000/proveedores/activos?limit=100&offset=0" \
  -H "Authorization: Bearer $TOKEN"

# Segunda página (100 proveedores)
curl -X GET "http://localhost:8000/proveedores/activos?limit=100&offset=100" \
  -H "Authorization: Bearer $TOKEN"

# Tercera página (100 proveedores)
curl -X GET "http://localhost:8000/proveedores/activos?limit=100&offset=200" \
  -H "Authorization: Bearer $TOKEN"
```

### Ejemplo 3: Filtrar por instancia específica

```bash
# Proveedores activos de EXPANSION solamente
curl -X GET "http://localhost:8000/proveedores/activos?instancia=EXPANSION" \
  -H "Authorization: Bearer $TOKEN"
```

**Resultado:**
```json
{
  "success": true,
  "modo": "productivo",
  "total": 3850,
  "limit": null,
  "offset": 0,
  "count": 3850,
  "proveedores": [...],
  "instancias_incluidas": ["EXPANSION"]
}
```

### Ejemplo 4: Modo pruebas

```bash
# 1. Activar modo pruebas
curl -X POST http://localhost:8000/pruebas \
  -H "Authorization: Bearer $TOKEN"

# 2. Consultar proveedores activos (ahora de instancias _PRUEBAS)
curl -X GET "http://localhost:8000/proveedores/activos" \
  -H "Authorization: Bearer $TOKEN"
```

**Resultado:**
```json
{
  "success": true,
  "modo": "pruebas",
  "total": 1200,
  "limit": null,
  "offset": 0,
  "count": 1200,
  "proveedores": [...],
  "instancias_incluidas": [
    "EXPANSION",
    "HEARST",
    "ANDENES",
    ...
  ]
}
```

**Nota:** En modo pruebas, aunque las instancias se llaman igual (ej: "EXPANSION"), internamente el sistema consulta las instancias `_PRUEBAS` (ej: "EXPANSION_PRUEBAS") en SAP Service Layer.

### Ejemplo 5: Error al filtrar por instancia no disponible en el modo actual

```bash
# En modo productivo, intentar consultar una instancia que solo existe en pruebas
curl -X GET "http://localhost:8000/proveedores/activos?instancia=INSTANCIA_INEXISTENTE" \
  -H "Authorization: Bearer $TOKEN"
```

**Resultado:**
```json
{
  "success": false,
  "error": "Instancia 'INSTANCIA_INEXISTENTE' no disponible en modo productivo",
  "instancias_disponibles": [
    "AIRPORTS",
    "ANDENES",
    "CINETICA",
    ...
  ]
}
```

---

## Campos Retornados

Cada proveedor en el array `proveedores` contiene los siguientes campos:

### Identificación
- `Instancia`: Nombre de la instancia SAP
- `CardCode`: Código del proveedor (llave)
- `CardName`: Nombre del proveedor
- `GroupCode`: Código de grupo
- `FederalTaxID`: RFC del proveedor

### Contacto
- `Phone1`: Teléfono principal
- `Phone2`: Teléfono secundario
- `Fax`: Número de fax
- `Cellular`: Teléfono celular
- `EmailAddress`: Correo electrónico
- `ContactPerson`: Persona de contacto

### Dirección
- `Address`: Dirección principal
- `Block`: Colonia
- `ZipCode`: Código postal
- `City`: Ciudad
- `County`: Municipio/Condado
- `BillToState`: Estado (facturación)
- `Country`: País

### Información Financiera
- `PayTermsGrpCode`: Código de términos de pago
- `CreditLimit`: Límite de crédito
- `Currency`: Moneda
- `CurrentAccountBalance`: Saldo actual
- `OpenDeliveryNotesBalance`: Saldo de entregas pendientes
- `OpenOrdersBalance`: Saldo de órdenes abiertas

### Estado
- `Valid`: Válido ('Y' / 'N')
- `Frozen`: Congelado ('Y' / 'N')

---

## Criterios de "Proveedor Activo"

Un proveedor se considera **activo** cuando cumple **ambas** condiciones:

### 1. Valid = 'Y'
Indica que el proveedor está **válido** en SAP Business One.

**Significado:**
- El proveedor puede ser utilizado en transacciones
- Los documentos pueden ser creados con este proveedor
- El proveedor aparece en las búsquedas y selecciones

**Cuando Valid = 'N':**
- El proveedor fue marcado como inválido manualmente
- Usualmente indica que el proveedor ya no debe ser utilizado
- Puede ser un proveedor obsoleto o duplicado

### 2. Frozen = 'N'
Indica que el proveedor **NO está congelado** en SAP Business One.

**Significado:**
- Se pueden crear nuevas transacciones con este proveedor
- El proveedor está activo operacionalmente

**Cuando Frozen = 'Y':**
- No se pueden crear nuevas transacciones
- El proveedor está temporalmente suspendido
- Usualmente por problemas de crédito, legal, o administrativos
- Los documentos existentes no se ven afectados

---

## Comparación: Proveedores Activos vs Todos los Proveedores

| Endpoint | Criterio | Uso Típico |
|----------|----------|------------|
| `GET /proveedores/activos` | `Valid='Y' AND Frozen='N'` | Consultar proveedores disponibles para operaciones actuales |
| `GET /sap/proveedores` | Todos | Auditoría, análisis histórico, reporte completo |

---

## Integración con el Sistema de Modos

El sistema de proveedores activos está completamente integrado con el sistema de modos:

```
┌─────────────────────────────────────────────────────────────┐
│                    MODO ACTUAL                              │
│  (Variable global _modo_pruebas en config.py)               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ├─── False (Productivo)
                            │      │
                            │      └─→ Usa vw_productivo
                            │           │
                            │           └─→ Instancias con SL=1
                            │
                            └─── True (Pruebas)
                                   │
                                   └─→ Usa vw_pruebas
                                        │
                                        └─→ Instancias con SLP=1 AND Prueba=1
```

**Endpoints de control de modo:**
- `GET /pruebas` - Consultar modo actual
- `POST /pruebas` - Activar modo pruebas
- `DELETE /pruebas` - Activar modo productivo

---

## Performance

### Índices Recomendados

Para optimizar el rendimiento de las consultas de proveedores activos:

```sql
-- Índice compuesto en Valid y Frozen
CREATE INDEX IX_SAP_PROVEEDORES_Valid_Frozen
ON SAP_PROVEEDORES (Valid, Frozen)
INCLUDE (Instancia, CardCode, CardName);

-- Índice en Instancia para filtros por instancia específica
CREATE INDEX IX_SAP_PROVEEDORES_Instancia
ON SAP_PROVEEDORES (Instancia)
WHERE Valid = 'Y' AND Frozen = 'N';
```

### Métricas Esperadas

| Escenario | Total Proveedores | Proveedores Activos | % Activos | Tiempo Consulta |
|-----------|-------------------|---------------------|-----------|-----------------|
| Modo productivo (21 instancias) | ~13,199 | ~12,200 | ~92% | < 200ms |
| Modo pruebas (6 instancias) | ~1,500 | ~1,350 | ~90% | < 50ms |
| Filtro por instancia (EXPANSION) | ~4,075 | ~3,850 | ~94% | < 30ms |

---

## Casos de Uso

### 1. Frontend: Selector de Proveedores
Un formulario necesita mostrar solo los proveedores disponibles para crear una nueva orden de compra.

```javascript
// Obtener proveedores activos con paginación
const response = await fetch(
  '/proveedores/activos?limit=50&offset=0',
  {
    headers: { 'Authorization': `Bearer ${token}` }
  }
);

const data = await response.json();
// Usar data.proveedores para poblar el selector
```

### 2. Integración: Sincronización con ERP Externo
Un sistema externo necesita sincronizar solo los proveedores activos.

```python
import requests

response = requests.get(
    'http://api.example.com/proveedores/activos',
    headers={'Authorization': f'Bearer {token}'}
)

if response.json()['success']:
    proveedores = response.json()['proveedores']
    # Sincronizar con sistema externo
    sync_to_external_system(proveedores)
```

### 3. Reporte: Proveedores Activos por Instancia
Generar un reporte de cuántos proveedores activos hay por cada instancia.

```bash
# Obtener todas las instancias
INSTANCIAS=$(curl -X GET "http://localhost:8000/pruebas" \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.instancias_disponibles[]')

# Para cada instancia, contar proveedores activos
for INST in $INSTANCIAS; do
  COUNT=$(curl -X GET "http://localhost:8000/proveedores/activos?instancia=$INST" \
    -H "Authorization: Bearer $TOKEN" \
    | jq '.total')
  echo "$INST: $COUNT proveedores activos"
done
```

### 4. Auditoría: Comparar Activos vs Total
Identificar instancias con alto porcentaje de proveedores inactivos.

```sql
-- Query SQL directa (para auditoría)
SELECT
    Instancia,
    COUNT(*) AS Total,
    SUM(CASE WHEN Valid='Y' AND Frozen='N' THEN 1 ELSE 0 END) AS Activos,
    SUM(CASE WHEN Valid='N' OR Frozen='Y' THEN 1 ELSE 0 END) AS Inactivos,
    CAST(SUM(CASE WHEN Valid='Y' AND Frozen='N' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS PorcentajeActivos
FROM SAP_PROVEEDORES
GROUP BY Instancia
ORDER BY PorcentajeActivos ASC;
```

---

## Testing

### Test Manual 1: Verificar Modo Productivo

```bash
# 1. Login
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"sa","password":"********"}' \
  | jq -r '.access_token')

# 2. Activar modo productivo
curl -X DELETE http://localhost:8000/pruebas \
  -H "Authorization: Bearer $TOKEN"

# 3. Consultar proveedores activos
curl -X GET "http://localhost:8000/proveedores/activos?limit=10" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'

# 4. Verificar que el modo sea "productivo"
curl -X GET "http://localhost:8000/proveedores/activos?limit=1" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.modo'
# Resultado esperado: "productivo"
```

### Test Manual 2: Verificar Modo Pruebas

```bash
# 1. Activar modo pruebas
curl -X POST http://localhost:8000/pruebas \
  -H "Authorization: Bearer $TOKEN"

# 2. Consultar proveedores activos
curl -X GET "http://localhost:8000/proveedores/activos?limit=10" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'

# 3. Verificar que el modo sea "pruebas"
curl -X GET "http://localhost:8000/proveedores/activos?limit=1" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.modo'
# Resultado esperado: "pruebas"
```

### Test Manual 3: Verificar Filtro por Instancia

```bash
# Consultar solo EXPANSION
curl -X GET "http://localhost:8000/proveedores/activos?instancia=EXPANSION" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{modo, total, instancias_incluidas}'

# Resultado esperado:
# {
#   "modo": "productivo",
#   "total": 3850,
#   "instancias_incluidas": ["EXPANSION"]
# }
```

### Test Manual 4: Verificar Paginación

```bash
# Primera página
P1=$(curl -X GET "http://localhost:8000/proveedores/activos?limit=100&offset=0" \
  -H "Authorization: Bearer $TOKEN")

# Segunda página
P2=$(curl -X GET "http://localhost:8000/proveedores/activos?limit=100&offset=100" \
  -H "Authorization: Bearer $TOKEN")

# Verificar que sean diferentes
echo $P1 | jq '.proveedores[0].CardCode'
echo $P2 | jq '.proveedores[0].CardCode'
# Los CardCode deben ser diferentes
```

### Test Manual 5: Verificar Criterios de Activo

```bash
# Consultar un proveedor activo
curl -X GET "http://localhost:8000/proveedores/activos?limit=1" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.proveedores[0] | {CardCode, CardName, Valid, Frozen}'

# Resultado esperado:
# {
#   "CardCode": "...",
#   "CardName": "...",
#   "Valid": "Y",
#   "Frozen": "N"
# }
```

---

## Troubleshooting

### Error: "Instancia 'XXX' no disponible en modo YYY"

**Causa:** La instancia especificada no está disponible en el modo actual.

**Solución:**
1. Verificar el modo actual: `GET /pruebas`
2. Consultar instancias disponibles: el error incluye la lista
3. Cambiar de modo si es necesario o usar una instancia válida

### No se retornan proveedores (total = 0)

**Posibles causas:**
1. **Tabla SAP_PROVEEDORES vacía**: Ejecutar `/inicializa_datos` o `/sap/proveedores/actualizar`
2. **Modo incorrecto**: Verificar con `GET /pruebas` si estás en el modo correcto
3. **Todos los proveedores están inactivos**: Verificar en SAP B1 los campos Valid y Frozen

**Verificación:**
```bash
# Verificar si hay proveedores en la tabla (sin filtros)
# (requiere acceso directo a la BD o endpoint sin filtros)
```

### Performance lento (> 1 segundo)

**Posibles causas:**
1. Falta de índices en la tabla
2. Tabla muy grande sin paginación
3. Red lenta

**Soluciones:**
1. Crear índices recomendados (ver sección Performance)
2. Usar paginación: `?limit=100&offset=0`
3. Filtrar por instancia específica

---

## Próximos Pasos Sugeridos

### Mejoras Corto Plazo
1. **Filtros adicionales:**
   - Filtrar por `CardName` (búsqueda parcial)
   - Filtrar por `FederalTaxID` (RFC)
   - Filtrar por `GroupCode`

2. **Ordenamiento:**
   - Permitir ordenar por diferentes campos
   - Orden ascendente/descendente

3. **Estadísticas:**
   - Endpoint para obtener solo el conteo por instancia
   - Endpoint para métricas (% activos, % congelados, etc.)

### Mejoras Largo Plazo
1. **Cache:**
   - Implementar cache de proveedores activos (TTL: 5 minutos)
   - Invalidar cache cuando se actualiza SAP_PROVEEDORES

2. **Búsqueda full-text:**
   - Implementar búsqueda por nombre o RFC con wildcards
   - Soporte para búsqueda difusa (fuzzy search)

3. **Export:**
   - Endpoint para exportar a Excel
   - Endpoint para exportar a CSV

---

## Archivos Modificados

### app/database.py
**Líneas agregadas:** ~150 (nueva función `get_proveedores_activos()`)

**Funciones agregadas:**
- `get_proveedores_activos(instancia, limit, offset)`

### app/main.py
**Líneas agregadas:** ~60 (nuevo endpoint)

**Endpoints agregados:**
- `GET /proveedores/activos`

**Imports agregados:**
- `get_proveedores_activos` desde database

---

**Documento generado:** 2026-01-21
**Versión del sistema:** 2.1.0
**Autor:** Sistema API MCP
