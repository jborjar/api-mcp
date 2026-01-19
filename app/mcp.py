from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from auth import TokenData, get_current_user, require_scope

router = APIRouter(prefix="/mcp", tags=["MCP"])


class MCPRequest(BaseModel):
    method: str
    params: dict[str, Any] | None = None


class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: str | None = None
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


class MCPToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


class MCPResourceDefinition(BaseModel):
    uri: str
    name: str
    description: str
    mime_type: str | None = None


AVAILABLE_TOOLS: list[MCPToolDefinition] = [
    MCPToolDefinition(
        name="query_mssql",
        description="Ejecutar consulta SQL en Microsoft SQL Server",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Consulta SQL a ejecutar"}
            },
            "required": ["query"]
        }
    ),
    MCPToolDefinition(
        name="query_hana",
        description="Ejecutar consulta en SAP HANA",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Consulta SQL a ejecutar"}
            },
            "required": ["query"]
        }
    ),
    MCPToolDefinition(
        name="sap_b1_get",
        description="Obtener datos de SAP Business One Service Layer",
        input_schema={
            "type": "object",
            "properties": {
                "endpoint": {"type": "string", "description": "Endpoint del Service Layer"}
            },
            "required": ["endpoint"]
        }
    )
]

AVAILABLE_RESOURCES: list[MCPResourceDefinition] = [
    MCPResourceDefinition(
        uri="mssql://database/tables",
        name="Tablas MSSQL",
        description="Lista de tablas disponibles en la base de datos MSSQL"
    ),
    MCPResourceDefinition(
        uri="hana://database/tables",
        name="Tablas HANA",
        description="Lista de tablas disponibles en SAP HANA"
    )
]


@router.post("/tools/list", response_model=MCPResponse)
async def list_tools(
    current_user: Annotated[TokenData, Depends(require_scope("mcp:tools:list"))]
) -> MCPResponse:
    return MCPResponse(
        result={
            "tools": [tool.model_dump() for tool in AVAILABLE_TOOLS]
        }
    )


@router.post("/tools/call", response_model=MCPResponse)
async def call_tool(
    request: MCPRequest,
    current_user: Annotated[TokenData, Depends(require_scope("mcp:tools:call"))]
) -> MCPResponse:
    tool_name = request.params.get("name") if request.params else None

    if not tool_name:
        return MCPResponse(
            error={"code": -32602, "message": "Parámetro 'name' requerido"}
        )

    valid_tools = {t.name for t in AVAILABLE_TOOLS}
    if tool_name not in valid_tools:
        return MCPResponse(
            error={"code": -32601, "message": f"Herramienta '{tool_name}' no encontrada"}
        )

    return MCPResponse(
        result={
            "content": [
                {"type": "text", "text": f"Herramienta '{tool_name}' ejecutada correctamente"}
            ]
        }
    )


@router.post("/resources/list", response_model=MCPResponse)
async def list_resources(
    current_user: Annotated[TokenData, Depends(require_scope("mcp:resources:list"))]
) -> MCPResponse:
    return MCPResponse(
        result={
            "resources": [resource.model_dump() for resource in AVAILABLE_RESOURCES]
        }
    )


@router.post("/resources/read", response_model=MCPResponse)
async def read_resource(
    request: MCPRequest,
    current_user: Annotated[TokenData, Depends(require_scope("mcp:resources:read"))]
) -> MCPResponse:
    uri = request.params.get("uri") if request.params else None

    if not uri:
        return MCPResponse(
            error={"code": -32602, "message": "Parámetro 'uri' requerido"}
        )

    valid_uris = {r.uri for r in AVAILABLE_RESOURCES}
    if uri not in valid_uris:
        return MCPResponse(
            error={"code": -32601, "message": f"Recurso '{uri}' no encontrado"}
        )

    return MCPResponse(
        result={
            "contents": [
                {"uri": uri, "text": f"Contenido del recurso '{uri}'"}
            ]
        }
    )
