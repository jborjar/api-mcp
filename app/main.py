from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from auth import (
    LoginRequest,
    TokenData,
    TokenResponse,
    create_access_token,
    get_current_user,
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


@app.get("/health", tags=["Sistema"])
async def health_check() -> dict:
    return {"status": "ok"}


@app.get("/me", tags=["Usuario"])
async def get_me(
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> dict:
    return {
        "username": current_user.sub,
        "scopes": current_user.scopes
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


@app.post("/inicializa_datos", tags=["MSSQL"])
async def inicializa_datos(
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> dict:
    """
    Inicializa la base de datos y tabla SAP_EMPRESAS.

    Realiza las siguientes operaciones:
    1. Elimina y recrea la base de datos desde cero
    2. Crea la tabla SAP_EMPRESAS y la carga desde HANA
    3. Verifica si existen versiones _PRUEBAS de cada instancia
    4. Obtiene datos de OADM (PrintHeadr, CompnyAddr, TaxIdNum)
    5. Prueba login/logout en Service Layer para cada instancia
    6. Actualiza el campo SL en SAP_EMPRESAS (1=éxito, 0=fallo)
    """
    resultado_empresas = inicializa_sap_empresas()
    resultado_sl = test_service_layer_all_instances(sap_empresas_result=resultado_empresas, skip_email=True)

    return {
        "sap_empresas": resultado_empresas,
        "service_layer": resultado_sl
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
