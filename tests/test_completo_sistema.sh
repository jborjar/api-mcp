#!/bin/bash

BASE_URL="http://localhost:8000"

# Función para obtener un nuevo token
get_token() {
    curl -s -X POST "$BASE_URL/auth/login" \
      -H "Content-Type: application/json" \
      -d '{"username":"sa","password":"G3XP@Ns10n"}' | jq -r '.access_token'
}

echo "=========================================="
echo "PRUEBA COMPLETA DEL SISTEMA"
echo "=========================================="
echo ""

# PASO 1: Login
echo "PASO 1: Autenticación"
echo "======================================================"
TOKEN=$(get_token)

if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
    echo "✓ Token obtenido: ${TOKEN:0:30}..."
else
    echo "✗ Error obteniendo token"
    exit 1
fi
echo ""

# PASO 2: Inicialización de datos
echo "PASO 2: Iniciar proceso de inicialización de datos"
echo "======================================================"
TOKEN=$(get_token)
INIT_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" "$BASE_URL/inicializa_datos")
JOB_ID=$(echo "$INIT_RESPONSE" | jq -r '.job_id')
echo "Job ID: $JOB_ID"
echo "Mensaje: $(echo "$INIT_RESPONSE" | jq -r '.message')"
echo ""

echo "Monitoreando progreso del job..."
echo ""

# Monitorear progreso
MAX_ATTEMPTS=60
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    
    # Renovar token cada 10 intentos
    if [ $((ATTEMPT % 10)) -eq 0 ]; then
        TOKEN=$(get_token)
    fi
    
    STATUS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/inicializa_datos/status/$JOB_ID")
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')
    MESSAGE=$(echo "$STATUS_RESPONSE" | jq -r '.message // "Iniciando..."')
    
    echo "[$ATTEMPT/$MAX_ATTEMPTS] Estado: $STATUS - $MESSAGE"
    
    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
        break
    fi
    
    sleep 2
done

echo ""
echo "Job finalizado con estado: $STATUS"
echo ""

if [ "$STATUS" = "completed" ]; then
    echo "✓ Inicialización completada exitosamente"
else
    echo "✗ Inicialización falló o no completó a tiempo"
fi
echo ""

# PASO 3: Análisis de actividad (años=1, default)
echo "PASO 3: Análisis de actividad de proveedores (años=1)"
echo "======================================================"
TOKEN=$(get_token)
ACTIVIDAD_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" "$BASE_URL/proveedores/analizar-actividad?anos=1")
echo "$ACTIVIDAD_RESPONSE" | jq '{
  success,
  resultados: {
    fecha_analisis,
    anos_analizados,
    total_activos,
    total_inactivos,
    proveedores_analizados: (.resultados.proveedores | length)
  }
}'
echo ""

# PASO 4: Análisis de actividad (años=0, solo año actual)
echo "PASO 4: Análisis de actividad de proveedores (años=0)"
echo "======================================================"
TOKEN=$(get_token)
ACTIVIDAD0_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" "$BASE_URL/proveedores/analizar-actividad?anos=0")
echo "$ACTIVIDAD0_RESPONSE" | jq '{
  success,
  resultados: {
    fecha_analisis,
    anos_analizados,
    total_activos,
    total_inactivos,
    proveedores_analizados: (.resultados.proveedores | length)
  }
}'
echo ""

# PASO 5: Consultar maestro de proveedores
echo "PASO 5: Consultar maestro de proveedores"
echo "======================================================"
TOKEN=$(get_token)
MAESTRO=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/maestro_proveedores")
TOTAL_MAESTRO=$(echo "$MAESTRO" | jq 'length')
echo "Total proveedores en maestro: $TOTAL_MAESTRO"
echo ""
echo "Primeros 3 proveedores:"
echo "$MAESTRO" | jq '.[0:3] | map({CardName, FederalTaxID})'
echo ""

# PASO 6: Listar jobs de inicialización
echo "PASO 6: Listar jobs de inicialización"
echo "======================================================"
TOKEN=$(get_token)
JOBS=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/inicializa_datos/jobs")
echo "$JOBS" | jq '{
  total_jobs,
  ultimos_3_jobs: (.jobs | sort_by(.timestamp) | reverse | .[0:3] | map({job_id, status, timestamp}))
}'
echo ""

# PASO 7: Logout
echo "PASO 7: Cerrar sesión"
echo "======================================================"
TOKEN=$(get_token)
LOGOUT=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" "$BASE_URL/auth/logout")
echo "$LOGOUT" | jq '.'
echo ""

echo "=========================================="
echo "PRUEBA COMPLETA FINALIZADA"
echo "=========================================="

