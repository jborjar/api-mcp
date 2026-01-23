"""
Utilidades generales del sistema.
"""
import os
from datetime import datetime
from zoneinfo import ZoneInfo


def get_timezone() -> ZoneInfo:
    """
    Obtiene el timezone configurado en la variable de entorno TZ.
    Por defecto usa America/Mexico_City.
    """
    tz_name = os.getenv('TZ', 'America/Mexico_City')
    return ZoneInfo(tz_name)


def now() -> datetime:
    """
    Retorna la fecha y hora actual con timezone awareness.
    Usa el timezone configurado en TZ (default: America/Mexico_City).
    """
    return datetime.now(get_timezone())
