"""
Gestión de sesiones de usuario con tokens en base de datos.
Permite renovación automática y control total sobre las sesiones activas.
"""
import os
import uuid
from datetime import datetime, timedelta
from database import get_mssql_connection
from utils import now as tz_now, get_timezone


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
    conn = get_mssql_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'USER_SESSIONS')
            CREATE TABLE USER_SESSIONS (
                SessionID NVARCHAR(100) PRIMARY KEY,
                Username NVARCHAR(100) NOT NULL,
                CreatedAt DATETIME NOT NULL,
                LastActivity DATETIME NOT NULL,
                Scopes NVARCHAR(500),
                INDEX idx_username (Username),
                INDEX idx_last_activity (LastActivity)
            )
        """)
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def create_session(username: str, scopes: list[str]) -> str:
    """
    Crea una nueva sesión para el usuario.
    Si el usuario excede el límite de sesiones activas, elimina la más antigua.
    Retorna el SessionID (token).
    """
    ensure_sessions_table_exists()

    session_id = str(uuid.uuid4())
    now = tz_now()
    scopes_str = ",".join(scopes)

    # Obtener límite de sesiones activas desde variable de entorno
    max_sessions = int(os.getenv("SESIONES_ACTIVAS", "2"))

    conn = get_mssql_connection()
    cursor = conn.cursor()

    try:
        # Contar sesiones activas del usuario
        cursor.execute("""
            SELECT COUNT(*)
            FROM USER_SESSIONS
            WHERE Username = ?
        """, (username,))
        active_sessions = cursor.fetchone()[0]

        # Si excede el límite, eliminar la sesión más antigua
        if active_sessions >= max_sessions:
            cursor.execute("""
                DELETE FROM USER_SESSIONS
                WHERE SessionID = (
                    SELECT TOP 1 SessionID
                    FROM USER_SESSIONS
                    WHERE Username = ?
                    ORDER BY LastActivity ASC
                )
            """, (username,))
            conn.commit()

        # Crear nueva sesión
        cursor.execute("""
            INSERT INTO USER_SESSIONS (SessionID, Username, CreatedAt, LastActivity, Scopes)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, username, now, now, scopes_str))
        conn.commit()
        return session_id
    finally:
        cursor.close()
        conn.close()


def validate_and_renew_session(session_id: str, timeout_minutes: int = 30) -> dict | None:
    """
    Valida si la sesión existe y no ha expirado.
    Si es válida, renueva el LastActivity (sliding expiration).

    Args:
        session_id: ID de la sesión a validar
        timeout_minutes: Minutos de inactividad antes de expirar (default: 30)

    Returns:
        dict con username y scopes si es válida, None si expiró o no existe
    """
    ensure_sessions_table_exists()

    conn = get_mssql_connection()
    cursor = conn.cursor()

    try:
        # Buscar sesión
        cursor.execute("""
            SELECT Username, Scopes, LastActivity
            FROM USER_SESSIONS
            WHERE SessionID = ?
        """, (session_id,))

        row = cursor.fetchone()
        if not row:
            return None

        username, scopes_str, last_activity = row

        # Hacer que last_activity sea timezone-aware si no lo es
        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=get_timezone())

        # Verificar si expiró
        expiration_time = last_activity + timedelta(minutes=timeout_minutes)
        if tz_now() > expiration_time:
            # Sesión expirada, eliminar
            cursor.execute("DELETE FROM USER_SESSIONS WHERE SessionID = ?", (session_id,))
            conn.commit()
            return None

        # Sesión válida, renovar LastActivity
        cursor.execute("""
            UPDATE USER_SESSIONS
            SET LastActivity = ?
            WHERE SessionID = ?
        """, (tz_now(), session_id))
        conn.commit()

        scopes = scopes_str.split(",") if scopes_str else []
        return {
            "username": username,
            "scopes": scopes,
            "session_id": session_id
        }
    finally:
        cursor.close()
        conn.close()


def invalidate_session(session_id: str) -> bool:
    """
    Invalida (elimina) una sesión específica.
    Retorna True si se eliminó, False si no existía.
    """
    ensure_sessions_table_exists()

    conn = get_mssql_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM USER_SESSIONS WHERE SessionID = ?", (session_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()


def invalidate_user_sessions(username: str) -> int:
    """
    Invalida todas las sesiones de un usuario.
    Retorna el número de sesiones eliminadas.
    """
    ensure_sessions_table_exists()

    conn = get_mssql_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM USER_SESSIONS WHERE Username = ?", (username,))
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def cleanup_expired_sessions(timeout_minutes: int = 30) -> int:
    """
    Elimina sesiones expiradas de la base de datos.
    Retorna el número de sesiones eliminadas.
    """
    ensure_sessions_table_exists()

    conn = get_mssql_connection()
    cursor = conn.cursor()

    try:
        expiration_time = tz_now() - timedelta(minutes=timeout_minutes)
        cursor.execute("""
            DELETE FROM USER_SESSIONS
            WHERE LastActivity < ?
        """, (expiration_time,))
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def get_active_sessions(username: str | None = None) -> list[dict]:
    """
    Obtiene lista de sesiones activas.
    Si se proporciona username, solo retorna sesiones de ese usuario.
    """
    ensure_sessions_table_exists()

    conn = get_mssql_connection()
    cursor = conn.cursor()

    try:
        if username:
            cursor.execute("""
                SELECT SessionID, Username, CreatedAt, LastActivity, Scopes
                FROM USER_SESSIONS
                WHERE Username = ?
                ORDER BY LastActivity DESC
            """, (username,))
        else:
            cursor.execute("""
                SELECT SessionID, Username, CreatedAt, LastActivity, Scopes
                FROM USER_SESSIONS
                ORDER BY LastActivity DESC
            """)

        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                "session_id": row[0],
                "username": row[1],
                "created_at": row[2].isoformat() if row[2] else None,
                "last_activity": row[3].isoformat() if row[3] else None,
                "scopes": row[4].split(",") if row[4] else []
            })
        return sessions
    finally:
        cursor.close()
        conn.close()
