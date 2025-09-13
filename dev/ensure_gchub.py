#!/usr/bin/env python3
"""
Idempotent helper to ensure a developer Postgres role and database exist.

Connects to Postgres using a superuser account, creates a role and database if
missing, and grants privileges. Intended for local dev and CI helper usage.
"""

from __future__ import annotations

import os
import sys
import time
import traceback
from typing import Optional

try:
    import psycopg2
    from psycopg2 import sql
except Exception:
    print(
        "psycopg2 is required. Install in the venv: python -m pip install psycopg2-binary",
        file=sys.stderr,
    )
    raise


HOST = os.environ.get("DEV_DB_HOST", "127.0.0.1")
PORT = int(os.environ.get("DEV_DB_PORT", "5432"))
SUPERUSER = os.environ.get("DEV_DB_SUPERUSER", "postgres")
SUPERPASSWORD = os.environ.get("DEV_DB_SUPERUSER_PASSWORD", os.environ.get("DEV_DB_SUPERUSER_PASS", "postgres"))

TARGET_USER = os.environ.get("DEV_DB_USER", "gchub")
TARGET_PASSWORD = os.environ.get("DEV_DB_PASSWORD", "gchub")
TARGET_DB = os.environ.get("DEV_DB_NAME", "gchub_dev")

RETRY_SECONDS = 1
MAX_RETRIES = int(os.environ.get("DEV_DB_MAX_RETRIES", "60"))


def connect_superuser(timeout_seconds: int = 60) -> psycopg2.extensions.connection:
    last_exc: Optional[BaseException] = None
    deadline = time.time() + timeout_seconds
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        try:
            conn = psycopg2.connect(
                dbname="postgres",
                user=SUPERUSER,
                password=SUPERPASSWORD,
                host=HOST,
                port=PORT,
                connect_timeout=3,
            )
            conn.autocommit = True
            print(f"Connected to Postgres at {HOST}:{PORT} as {SUPERUSER}")
            return conn
        except Exception as exc:
            last_exc = exc
            print(
                (f"Attempt {attempt}: Postgres not ready ({exc!r}) - retrying in {RETRY_SECONDS}s..."),
                file=sys.stderr,
            )
            time.sleep(RETRY_SECONDS)
    print(f"Timed out connecting to Postgres at {HOST}:{PORT}; last error:")
    if last_exc is not None:
        traceback.print_exception(type(last_exc), last_exc, getattr(last_exc, "__traceback__", None))
        raise last_exc
    else:
        raise RuntimeError("Failed to connect to Postgres but no exception was captured")


def role_exists(cur, role_name: str) -> bool:
    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role_name,))
    return cur.fetchone() is not None


def db_exists(cur, db_name: str) -> bool:
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    return cur.fetchone() is not None


def ensure_role_and_db() -> int:
    conn = connect_superuser(timeout_seconds=MAX_RETRIES)
    try:
        cur = conn.cursor()

        if role_exists(cur, TARGET_USER):
            print(f"Role '{TARGET_USER}' already exists")
            try:
                cur.execute(
                    sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD %s").format(sql.Identifier(TARGET_USER)),
                    (TARGET_PASSWORD,),
                )
                print(f"Updated password for role '{TARGET_USER}'")
            except Exception as exc:
                print(
                    f"Warning: failed to update password for {TARGET_USER}: {exc}",
                    file=sys.stderr,
                )
        else:
            print(f"Creating role '{TARGET_USER}'")
            cur.execute(
                sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD %s").format(sql.Identifier(TARGET_USER)),
                (TARGET_PASSWORD,),
            )
            print(f"Created role '{TARGET_USER}'")

        if db_exists(cur, TARGET_DB):
            print(f"Database '{TARGET_DB}' already exists")
        else:
            print(f"Creating database '{TARGET_DB}' owned by '{TARGET_USER}'")
            cur.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(sql.Identifier(TARGET_DB), sql.Identifier(TARGET_USER)))
            print(f"Created database '{TARGET_DB}'")

        # Best-effort: grant privileges inside the target DB
        try:
            conn_db = psycopg2.connect(
                dbname=TARGET_DB,
                user=SUPERUSER,
                password=SUPERPASSWORD,
                host=HOST,
                port=PORT,
                connect_timeout=3,
            )
            conn_db.autocommit = True
            cur_db = conn_db.cursor()
            print(f"Granting privileges on database '{TARGET_DB}' to '{TARGET_USER}'")
            cur_db.execute(
                sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {};").format(sql.Identifier(TARGET_DB), sql.Identifier(TARGET_USER))
            )
            cur_db.execute(sql.SQL("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {};").format(sql.Identifier(TARGET_USER)))
            cur_db.execute(
                sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {};").format(sql.Identifier(TARGET_USER))
            )
            cur_db.close()
            conn_db.close()
            print("Privileges granted (best-effort)")
        except Exception as exc:
            print(f"Warning: could not set internal privileges in {TARGET_DB}: {exc}")

        return 0
    finally:
        try:
            conn.close()
        except Exception:
            pass


def main() -> int:
    try:
        rc = ensure_role_and_db()
        print("ensure_gchub completed successfully")
        return rc
    except Exception:
        print("ensure_gchub failed:")
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    sys.exit(main())
