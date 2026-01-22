from typing import Annotated
import uuid
import threading
import asyncio
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from auth import (
    LoginRequest,
    TokenData,
    TokenResponse,
    create_access_token,
    get_current_user,
    logout as logout_session,
)
from config import get_settings, get_modo_pruebas, set_modo_pruebas
from database import (
    get_empresas_sap,
    inicializa_sap_empresas,
    test_service_layer_all_instances,
    get_proveedores_sl,
    poblar_sap_proveedores,
    enviar_correo_inicializacion,
    actualizar_sap_empresas,
    actualizar_sap_proveedores,
    create_or_update_vista_maestro_proveedores,
    get_maestro_proveedores,
    analizar_actividad_proveedores,
    get_mssql_connection,
)
from session import (
    get_active_sessions,
    cleanup_expired_sessions,
    invalidate_user_sessions,
)
from mcp import router as mcp_router

app = FastAPI(
    title="API MCP",
    description="API con soporte MCP para integración con MSSQL, SAP HANA y SAP B1 Service Layer",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mcp_router)

# Incluir router de web settings
from websettings import router as websettings_router
app.include_router(websettings_router)

# Variable global para controlar el task de limpieza
cleanup_task = None


async def scheduled_cleanup():
    """
    Tarea de background que ejecuta limpieza periódica de sesiones y jobs.
    Se ejecuta cada 1 hora.
    """
    while True:
        try:
            # Esperar 1 hora (3600 segundos)
            await asyncio.sleep(3600)

            # Ejecutar limpieza de sesiones expiradas
            deleted_sessions = cleanup_expired_sessions()
            print(f"[Cleanup] Sesiones expiradas eliminadas: {deleted_sessions}")

            # Ejecutar limpieza de jobs antiguos
            deleted_jobs = cleanup_old_jobs()
            print(f"[Cleanup] Jobs antiguos eliminados: {deleted_jobs}")

        except Exception as e:
            print(f"[Cleanup] Error en limpieza programada: {e}")


@app.on_event("startup")
async def startup_event():
    """Ejecuta tareas de inicialización al arrancar la aplicación."""
    global cleanup_task

    # Limpiar sesiones expiradas al inicio
    cleanup_expired_sessions()

    # Limpiar jobs antiguos al inicio
    cleanup_old_jobs()

    # Iniciar tarea de limpieza programada (cada 1 hora)
    cleanup_task = asyncio.create_task(scheduled_cleanup())
    print("[Startup] Tarea de limpieza programada iniciada (cada 1 hora)")


@app.on_event("shutdown")
async def shutdown_event():
    """Ejecuta tareas de limpieza al apagar la aplicación."""
    global cleanup_task

    # Cancelar la tarea de limpieza programada
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

    print("[Shutdown] Tarea de limpieza programada detenida")


# Diccionario global para almacenar el estado de los jobs de inicialización
# job_id -> {status, progress, result, error, created_at, completed_at}
initialization_jobs = {}
jobs_lock = threading.Lock()


def cleanup_old_jobs():
    """
    Elimina jobs completados o fallidos que tengan más de 24 horas.
    Mantiene jobs en ejecución (running) y pendientes (pending) sin importar su antigüedad.
    """
    from datetime import timedelta

    now = datetime.now()
    with jobs_lock:
        jobs_to_remove = []
        for job_id, job_info in initialization_jobs.items():
            # Solo limpiar jobs completados o fallidos
            if job_info["status"] in ["completed", "failed"]:
                created_at = job_info.get("created_at")
                if created_at and isinstance(created_at, datetime):
                    age = now - created_at
                    if age > timedelta(hours=24):
                        jobs_to_remove.append(job_id)

        # Eliminar jobs antiguos
        for job_id in jobs_to_remove:
            del initialization_jobs[job_id]

        return len(jobs_to_remove)


@app.post("/auth/login", response_model=TokenResponse, tags=["Autenticación"])
async def login(request: LoginRequest) -> TokenResponse:
    settings = get_settings()

    if request.username == settings.MSSQL_USER and request.password == settings.MSSQL_PASSWORD:
        scopes = [
            "mcp:tools:list",
            "mcp:tools:call",
            "mcp:resources:list",
            "mcp:resources:read"
        ]
        token = create_access_token(subject=request.username, scopes=scopes)
        return TokenResponse(access_token=token)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"}
    )


@app.post("/auth/logout", tags=["Autenticación"])
async def logout(
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> dict:
    """
    Cierra la sesión del usuario invalidando su token.
    """
    success = logout_session(current_user.session_id)
    if success:
        return {"message": "Sesión cerrada exitosamente"}
    return {"message": "Sesión no encontrada"}


@app.get("/auth/sessions", tags=["Autenticación"])
async def list_sessions(
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> dict:
    """
    Lista todas las sesiones activas del usuario actual.
    Útil para ver desde qué dispositivos/ubicaciones está conectado.
    """
    sessions = get_active_sessions(username=current_user.sub)
    return {
        "username": current_user.sub,
        "total_sessions": len(sessions),
        "sessions": sessions
    }


@app.post("/auth/logout-all", tags=["Autenticación"])
async def logout_all(
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> dict:
    """
    Cierra todas las sesiones del usuario actual.
    Útil para cerrar sesión en todos los dispositivos.
    """
    count = invalidate_user_sessions(current_user.sub)
    return {
        "message": f"Se cerraron {count} sesiones",
        "sessions_closed": count
    }


@app.post("/auth/cleanup", tags=["Autenticación"])
async def cleanup_sessions(
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> dict:
    """
    Limpia sesiones expiradas y jobs antiguos de la base de datos.
    Solo accesible por usuarios autenticados (mantenimiento).

    Esta limpieza también se ejecuta automáticamente cada 1 hora en segundo plano.
    """
    sessions_count = cleanup_expired_sessions()
    jobs_count = cleanup_old_jobs()
    return {
        "message": f"Se eliminaron {sessions_count} sesiones expiradas y {jobs_count} jobs antiguos",
        "sessions_cleaned": sessions_count,
        "jobs_cleaned": jobs_count
    }




@app.get("/health", tags=["Sistema"])
async def health_check() -> dict:
    return {"status": "ok"}


@app.get("/me", tags=["Usuario"])
async def get_me(
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> dict:
    """
    Retorna información completa del usuario autenticado y su sesión actual.
    """
    from session import get_active_sessions
    from datetime import datetime, timedelta

    # Obtener información completa de la sesión desde la BD
    sessions = get_active_sessions(username=current_user.sub)

    # Buscar la sesión actual
    current_session = None
    for session in sessions:
        if session["session_id"] == current_user.session_id:
            current_session = session
            break

    if not current_session:
        # Si no se encuentra la sesión, devolver info básica
        return {
            "username": current_user.sub,
            "scopes": current_user.scopes,
            "session_id": current_user.session_id
        }

    # Calcular expiración (30 minutos desde última actividad)
    last_activity = datetime.fromisoformat(current_session["last_activity"])
    expires_at = last_activity + timedelta(minutes=30)

    return {
        "username": current_user.sub,
        "scopes": current_user.scopes,
        "session_id": current_user.session_id,
        "created_at": current_session["created_at"],
        "expires_at": expires_at.isoformat()
    }


@app.get("/pruebas", tags=["Sistema"])
async def get_pruebas(
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> dict:
    """Retorna el modo actual: pruebas (True) o productivo (False)."""
    return {
        "modo_pruebas": get_modo_pruebas(),
        "descripcion": "pruebas" if get_modo_pruebas() else "productivo"
    }


@app.post("/pruebas/{valor}", tags=["Sistema"])
async def set_pruebas(
    valor: int,
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> dict:
    """
    Establece el modo de operación.
    - **/pruebas/1**: Activa modo pruebas (usa instancias con Prueba=1 y agrega _PRUEBAS)
    - **/pruebas/0**: Activa modo productivo (usa instancias normales)
    """
    if valor not in (0, 1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El valor debe ser 0 (productivo) o 1 (pruebas)"
        )

    nuevo_valor = set_modo_pruebas(valor == 1)
    return {
        "modo_pruebas": nuevo_valor,
        "descripcion": "pruebas" if nuevo_valor else "productivo"
    }


@app.get("/empresas_registradas", tags=["SAP HANA"])
async def empresas_registradas(
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> dict:
    empresas = get_empresas_sap()
    return {
        "total": len(empresas),
        "empresas": empresas
    }


def _run_inicializa_datos_background(job_id: str, session_id: str, username: str, scopes: list[str]):
    """Función que se ejecuta en background para inicializar datos."""
    from database import get_mssql_connection

    try:
        # Actualizar estado: iniciando
        with jobs_lock:
            initialization_jobs[job_id]["status"] = "running"
            initialization_jobs[job_id]["progress"] = "Iniciando eliminación y recreación de base de datos..."

        # Ejecutar inicialización (esto eliminará y recreará la base de datos)
        with jobs_lock:
            initialization_jobs[job_id]["progress"] = "Creando tablas SAP_EMPRESAS, SAP_PROVEEDORES y USER_SESSIONS..."
        resultado_empresas = inicializa_sap_empresas()

        # Prueba Service Layer
        with jobs_lock:
            initialization_jobs[job_id]["progress"] = "Probando conexión a Service Layer (productivo y pruebas)..."
        resultado_sl = test_service_layer_all_instances(sap_empresas_result=resultado_empresas, skip_email=True)

        # Poblar SAP_PROVEEDORES
        with jobs_lock:
            initialization_jobs[job_id]["progress"] = "Poblando SAP_PROVEEDORES desde Service Layer..."
        resultado_proveedores = actualizar_sap_proveedores()

        # Analizar actividad de proveedores
        with jobs_lock:
            initialization_jobs[job_id]["progress"] = "Analizando actividad de proveedores y creando tablas SAP_PROV_ACTIVOS/INACTIVOS..."
        resultado_actividad = analizar_actividad_proveedores()

        # Restaurar la sesión del usuario actual
        with jobs_lock:
            initialization_jobs[job_id]["progress"] = "Restaurando sesión del usuario..."
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

        # Enviar correo con todos los resultados
        with jobs_lock:
            initialization_jobs[job_id]["progress"] = "Enviando correo con resultados..."
        from config import get_settings
        settings = get_settings()
        if settings.EMAIL_SUPERVISOR:
            email_result = enviar_correo_inicializacion(
                resultado_empresas,
                resultado_sl,
                resultado_proveedores,
                resultado_actividad
            )
        else:
            email_result = {"success": False, "error": "No hay destinatario configurado"}

        # Marcar como completado
        with jobs_lock:
            initialization_jobs[job_id]["status"] = "completed"
            initialization_jobs[job_id]["progress"] = "Inicialización completada exitosamente"
            initialization_jobs[job_id]["result"] = {
                "sap_empresas": resultado_empresas,
                "service_layer": resultado_sl,
                "sap_proveedores": resultado_proveedores,
                "analisis_actividad": resultado_actividad,
                "email_enviado": email_result,
                "session_restored": True
            }
            initialization_jobs[job_id]["finished_at"] = datetime.now().isoformat()

    except Exception as e:
        # Marcar como fallido
        with jobs_lock:
            initialization_jobs[job_id]["status"] = "failed"
            initialization_jobs[job_id]["error"] = str(e)
            initialization_jobs[job_id]["finished_at"] = datetime.now().isoformat()


@app.post("/inicializa_datos", tags=["MSSQL"])
async def inicializa_datos(
    background_tasks: BackgroundTasks,
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> dict:
    """
    Inicializa la base de datos completa de forma asíncrona.

    Este endpoint retorna inmediatamente un job_id que puede usarse para consultar
    el progreso de la inicialización mediante GET /inicializa_datos/status/{job_id}

    Operaciones realizadas en background:
    1. Elimina y recrea la base de datos desde cero
    2. Crea las tablas SAP_EMPRESAS, SAP_PROVEEDORES y USER_SESSIONS
    3. Carga SAP_EMPRESAS desde HANA
    4. Restaura la sesión del usuario actual
    5. Verifica si existen versiones _PRUEBAS de cada instancia
    6. Obtiene datos de OADM (PrintHeadr, CompnyAddr, TaxIdNum)
    7. Prueba login/logout en Service Layer para cada instancia
    8. Actualiza los campos SL y SLP en SAP_EMPRESAS (1=éxito, 0=fallo)
    9. Puebla SAP_PROVEEDORES con datos del Service Layer

    NOTA: Este endpoint recrea la base de datos completa, por lo que la sesión
    del usuario se elimina y se vuelve a crear automáticamente.
    """
    # Generar job_id único
    job_id = str(uuid.uuid4())

    # Guardar información de la sesión actual
    session_id = current_user.session_id
    username = current_user.sub
    scopes = current_user.scopes

    # Registrar job
    with jobs_lock:
        initialization_jobs[job_id] = {
            "status": "pending",
            "progress": "Trabajo en cola...",
            "result": None,
            "error": None,
            "started_at": datetime.now().isoformat(),
            "finished_at": None
        }

    # Ejecutar en background
    background_tasks.add_task(
        _run_inicializa_datos_background,
        job_id,
        session_id,
        username,
        scopes
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Inicialización iniciada. Use GET /inicializa_datos/status/{job_id} para consultar el progreso",
        "status_url": f"/inicializa_datos/status/{job_id}"
    }


@app.get("/inicializa_datos/status/{job_id}", tags=["MSSQL"])
async def get_inicializa_datos_status(
    job_id: str,
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> dict:
    """
    Consulta el estado de un trabajo de inicialización.

    Estados posibles:
    - pending: El trabajo está en cola
    - running: El trabajo está ejecutándose
    - completed: El trabajo terminó exitosamente
    - failed: El trabajo falló
    """
    with jobs_lock:
        if job_id not in initialization_jobs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job ID {job_id} no encontrado"
            )

        job_info = initialization_jobs[job_id].copy()

    return {
        "job_id": job_id,
        "status": job_info["status"],
        "progress": job_info["progress"],
        "started_at": job_info["started_at"],
        "finished_at": job_info["finished_at"],
        "result": job_info["result"] if job_info["status"] == "completed" else None,
        "error": job_info["error"] if job_info["status"] == "failed" else None
    }


@app.get("/inicializa_datos/jobs", tags=["MSSQL"])
async def list_initialization_jobs(
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> dict:
    """
    Lista todos los jobs de inicialización almacenados en memoria.
    Útil para administración y debugging.
    """
    with jobs_lock:
        jobs_summary = []
        for job_id, job_info in initialization_jobs.items():
            jobs_summary.append({
                "job_id": job_id,
                "status": job_info["status"],
                "created_at": job_info.get("created_at"),
                "completed_at": job_info.get("completed_at")
            })

    return {
        "total_jobs": len(jobs_summary),
        "jobs": sorted(jobs_summary, key=lambda x: x.get("created_at") or datetime.min, reverse=True)
    }


@app.post("/inicializa_datos/jobs/cleanup", tags=["MSSQL"])
async def cleanup_initialization_jobs(
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> dict:
    """
    Limpia manualmente los jobs completados o fallidos que tengan más de 24 horas.
    """
    removed = cleanup_old_jobs()
    return {
        "message": f"Limpieza completada. {removed} job(s) eliminado(s).",
        "jobs_removed": removed
    }


@app.post("/actualizar_empresas", tags=["MSSQL"])
async def actualizar_empresas(
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> dict:
    """
    Actualiza SAP_EMPRESAS con datos de SAP HANA (fuente de verdad).
    - Actualiza empresas existentes
    - Inserta nuevas empresas
    - Elimina empresas que ya no existen en HANA
    - Preserva el campo SL
    """
    return actualizar_sap_empresas()


@app.post("/actualizar_proveedores", tags=["MSSQL"])
async def actualizar_proveedores(
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> dict:
    """
    Actualiza SAP_PROVEEDORES con datos de SAP Service Layer (fuente de verdad).
    - Actualiza proveedores existentes
    - Inserta nuevos proveedores
    - Elimina proveedores que ya no existen en SAP

    El modo (productivo/pruebas) se controla con el endpoint /pruebas/{valor}:
    - /pruebas/0: modo productivo (usa instancias normales)
    - /pruebas/1: modo pruebas (usa instancias con Prueba=1 y conecta a {instancia}_PRUEBAS)
    """
    return actualizar_sap_proveedores()


@app.get("/test_service_layer", tags=["SAP Service Layer"])
async def test_service_layer(
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> dict:
    resultado = test_service_layer_all_instances()
    return resultado


@app.get("/proveedores/{instancia}", tags=["SAP Service Layer"])
async def get_proveedores(
    instancia: str,
    current_user: Annotated[TokenData, Depends(get_current_user)],
    top: int | None = None,
    card_code: str | None = None,
    card_name: str | None = None,
    federal_tax_id: str | None = None
) -> dict:
    """
    Obtiene los proveedores (BusinessPartners con CardType='S') de una instancia SAP.

    - **top**: Limita el número de registros retornados (opcional)
    - **card_code**: Filtra por CardCode específico, ej: N1000255 (opcional)
    - **card_name**: Filtra por nombre que contenga el valor (opcional)
    - **federal_tax_id**: Filtra por RFC que contenga el valor (opcional)
    """
    resultado = get_proveedores_sl(
        instancia,
        top=top,
        card_code=card_code,
        card_name=card_name,
        federal_tax_id=federal_tax_id
    )
    if not resultado["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("error", "Error al obtener proveedores")
        )
    return {
        "instancia": instancia,
        "total": resultado["total"],
        "proveedores": resultado["proveedores"]
    }


@app.get("/maestro_proveedores", tags=["MSSQL"])
async def maestro_proveedores(
    current_user: Annotated[TokenData, Depends(get_current_user)],
    top: int | None = None,
    card_name: str | None = None,
    federal_tax_id: str | None = None
) -> dict:
    """
    Consulta la vista maestro_proveedores.

    Muestra proveedores con una columna por cada instancia SAP,
    donde el valor es el CardCode en esa instancia (o NULL si no existe).

    - **top**: Limita el número de registros retornados (opcional)
    - **card_name**: Filtra por nombre que contenga el valor (opcional)
    - **federal_tax_id**: Filtra por RFC que contenga el valor (opcional)
    """
    resultado = get_maestro_proveedores(
        top=top,
        card_name=card_name,
        federal_tax_id=federal_tax_id
    )
    if not resultado["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("error", "Error al consultar maestro de proveedores")
        )
    return resultado


@app.post("/proveedores/analizar-actividad", tags=["Proveedores"])
async def analizar_actividad_proveedores_endpoint(
    current_user: Annotated[TokenData, Depends(get_current_user)],
    anos: int = 1
) -> dict:
    """
    Analiza la actividad de proveedores y crea/actualiza las tablas SAP_PROV_ACTIVOS y SAP_PROV_INACTIVOS.

    Este endpoint ejecuta un análisis completo de actividad de proveedores basado en transacciones
    de compras (OPCH - facturas) y órdenes de compra (OPOR) en SAP HANA.

    **Parámetro `anos`:**
    - **0**: Solo año actual (por ejemplo, 2026)
    - **1**: Año actual + 1 año anterior (2 años en total: 2025-2026) [DEFAULT]
    - **2**: Año actual + 2 años anteriores (3 años en total: 2024-2026)
    - **N**: Año actual + N años anteriores

    **Proceso ejecutado:**
    1. Consulta transacciones OPCH y OPOR en SAP HANA para cada instancia
    2. Identifica proveedores con actividad en el período especificado
    3. Crea/actualiza tabla `SAP_PROV_ACTIVOS` con proveedores activos
    4. Crea/actualiza tabla `SAP_PROV_INACTIVOS` con proveedores sin actividad
    5. Envía reporte por email al supervisor

    **Importante:**
    - Este proceso puede tardar varios minutos dependiendo del volumen de transacciones
    - El análisis respeta el modo actual (productivo/pruebas)
    - Se envía email automático con los resultados

    **Retorna:**
    - **success**: Indica si el análisis fue exitoso
    - **anos_analizados**: Años analizados (0=solo actual, 1=actual+1 anterior, etc.)
    - **total_activos**: Total de proveedores con actividad detectada
    - **total_inactivos**: Total de proveedores sin actividad
    - **detalle_activos**: Desglose de proveedores activos por instancia
    - **email_enviado**: Información sobre el envío del email de notificación

    **Ejemplo de uso:**
    ```bash
    # Analizar solo año actual
    POST /proveedores/analizar-actividad?anos=0

    # Analizar año actual + 1 anterior (default)
    POST /proveedores/analizar-actividad
    POST /proveedores/analizar-actividad?anos=1

    # Analizar últimos 3 años
    POST /proveedores/analizar-actividad?anos=2
    ```
    """
    try:
        resultado = analizar_actividad_proveedores(anos=anos)

        if not resultado.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=resultado.get("error", "Error al analizar actividad de proveedores")
            )

        return resultado

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al analizar actividad: {str(e)}"
        )


