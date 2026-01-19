from pydantic_settings import BaseSettings
from functools import lru_cache


# Variable global para modo pruebas
_modo_pruebas: bool = False


def get_modo_pruebas() -> bool:
    """Retorna True si está en modo pruebas, False si está en modo productivo."""
    return _modo_pruebas


def set_modo_pruebas(valor: bool) -> bool:
    """Establece el modo pruebas (True) o productivo (False). Retorna el nuevo valor."""
    global _modo_pruebas
    _modo_pruebas = valor
    return _modo_pruebas


def get_instancia_sl(instancia: str) -> str:
    """
    Retorna el nombre de instancia para Service Layer.
    En modo pruebas, agrega '_PRUEBAS' al nombre.
    """
    if _modo_pruebas:
        return f"{instancia}_PRUEBAS"
    return instancia


class Settings(BaseSettings):
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30

    # MSSQL
    MSSQL_HOST: str = "mssql"
    MSSQL_PORT: int = 1433
    MSSQL_USER: str
    MSSQL_PASSWORD: str
    MSSQL_DATABASE: str

    # SAP HANA
    SAP_HANA_HOST: str
    SAP_HANA_PORT: int
    SAP_HANA_USER: str
    SAP_HANA_PASSWORD: str

    # SAP B1 Service Layer (opcional)
    SAP_B1_SERVICE_LAYER_URL: str | None = None
    SAP_B1_USER: str | None = None
    SAP_B1_PASSWORD: str | None = None
    SAP_B1_COMPANY_DB: str | None = None

    # Email
    EMAIL_SUPERVISOR: str | None = None
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 25
    EMAIL_FROM: str = "api-mcp@progex.local"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
