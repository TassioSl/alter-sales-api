from __future__ import annotations

from contextlib import closing
from typing import Any

from .config import settings


class DatabaseConnectionError(RuntimeError):
    pass


def _split_host_port(raw_host: str) -> tuple[str, int]:
    host = raw_host.strip()
    if not host:
        raise DatabaseConnectionError("SQL_HOST ausente")
    if "," not in host:
        return host, 1433
    server, port = host.rsplit(",", 1)
    return server.strip(), int(port.strip())


def sql_is_configured() -> bool:
    return all(
        [
            settings.sql_host.strip(),
            settings.sql_database.strip(),
            settings.sql_user.strip(),
            settings.sql_password.strip(),
        ]
    )


def fetch_all_dict(query: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
    if not sql_is_configured():
        raise DatabaseConnectionError("Variaveis SQL_* ausentes")

    try:
        import pytds
    except ImportError as exc:  # pragma: no cover
        raise DatabaseConnectionError("Dependencia python-tds nao instalada") from exc

    server, port = _split_host_port(settings.sql_host)
    sql = query.replace("?", "%s")

    try:
        with closing(
            pytds.connect(
                server=server,
                port=port,
                database=settings.sql_database,
                user=settings.sql_user,
                password=settings.sql_password,
                cafile=None,
                validate_host=False,
                enc_login_only=False,
            )
        ) as conn, closing(conn.cursor()) as cur:
            cur.execute(sql, params)
            columns = [col[0] for col in cur.description or []]
            rows = cur.fetchall()
            return [dict(zip(columns, row, strict=False)) for row in rows]
    except Exception as exc:  # noqa: BLE001
        raise DatabaseConnectionError(str(exc)) from exc


def test_connection() -> dict[str, Any]:
    if not sql_is_configured():
        return {"ok": False, "error": "Variaveis SQL_* ausentes"}
    try:
        rows = fetch_all_dict("SELECT 1 AS ok", tuple())
        return {"ok": bool(rows), "provider": "python-tds"}
    except DatabaseConnectionError as exc:
        return {"ok": False, "error": str(exc)}
