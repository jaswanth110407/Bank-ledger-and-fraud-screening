"""
database.py – MySQL connection pool manager
Provides get_db() which returns a thread-local connection,
and close_db() which is registered as an app teardown handler.
"""

import mysql.connector
from mysql.connector import pooling, Error
from flask import g, current_app
from config import Config

# Module-level connection pool (created once at startup)
_pool: pooling.MySQLConnectionPool | None = None


def init_pool() -> None:
    """Create the MySQL connection pool. Called once from app.py."""
    global _pool
    _pool = pooling.MySQLConnectionPool(
        pool_name="bank_pool",
        pool_size=5,
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci",
        autocommit=False,
        connection_timeout=10,
    )


def get_db():
    """
    Return a connection from the pool and cache it in Flask's g object
    so the same connection is reused within a single request.
    """
    if "db" not in g:
        if _pool is None:
            init_pool()
        g.db = _pool.get_connection()
    return g.db


def close_db(e=None) -> None:
    """Release the connection back to the pool at request teardown."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def execute_query(sql: str, params: tuple = (), fetch: str = "all"):
    """
    Helper that executes a parameterised query and returns results.

    Args:
        sql    : SQL string with %s placeholders.
        params : Tuple of parameter values.
        fetch  : "all" | "one" | "none"

    Returns:
        List of dicts ("all"), single dict or None ("one"),
        or lastrowid int ("none" – for INSERT/UPDATE/DELETE).
    """
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        if fetch == "all":
            return cursor.fetchall()
        elif fetch == "one":
            return cursor.fetchone()
        else:   # INSERT / UPDATE / DELETE
            conn.commit()
            return cursor.lastrowid
    except Error as exc:
        conn.rollback()
        raise exc
    finally:
        cursor.close()
