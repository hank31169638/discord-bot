import os


def _import_psycopg2():
    """Lazy import psycopg2 and return (psycopg2, sql).

    This avoids raising ImportError at module import time when the
    dependency isn't installed (useful for static analysis or dev
    environments). Callers will receive a RuntimeError with a helpful
    message if the package is missing when a DB operation is attempted.
    """
    try:
        import psycopg2
        from psycopg2 import sql
        return psycopg2, sql
    except ImportError:
        raise RuntimeError(
            "psycopg2 is required for database operations but is not installed. "
            "Install it (e.g. pip install psycopg2-binary) or provide a DB client.")


def _normalize_pg_uri(uri: str) -> str:
    """Normalize common postgres URI forms to a form accepted by psycopg2.

    Some providers (and older URIs) use the "postgres://" scheme. Convert it
    to "postgresql://" which is the recommended scheme for psycopg2.
    """
    if uri.startswith("postgres://"):
        return uri.replace("postgres://", "postgresql://", 1)
    return uri


def get_database_url() -> str:
    """Auto-detect a PostgreSQL connection URL from environment variables.

    Priority order:
    1. Common single-string vars: DATABASE_URL, POSTGRES_URL, POSTGRESQL_URL,
       ZEABUR_POSTGRESQL_URL, ZEABUR_DATABASE_URL
    2. Build from individual PG* variables: PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
    If nothing is found, raises RuntimeError so the caller can fail fast.
    """
    # Single-string candidates (common providers and Zeabur variants)
    candidates = [
        'DATABASE_URL',
        'POSTGRES_CONNECTION_STRING',
        'POSTGRES_URI',
        'POSTGRES_URL',
        'POSTGRESQL_URL',
        'ZEABUR_POSTGRESQL_URL',
        'ZEABUR_DATABASE_URL',
        # Zeabur may also expose provider-specific or auto-generated names
        'POSTGRES_CONNECTION_STRING',
    ]

    for name in candidates:
        val = os.getenv(name)
        if val:
            print(f"Using database URL from env {name}")
            return _normalize_pg_uri(val)

    # Try to assemble from individual environment variables (Zeabur / common names)
    host = os.getenv('POSTGRES_HOST') or os.getenv('PGHOST')
    user = os.getenv('POSTGRES_USER') or os.getenv('POSTGRES_USERNAME') or os.getenv('PGUSER')
    password = os.getenv('POSTGRES_PASSWORD') or os.getenv('PASSWORD') or os.getenv('PGPASSWORD')
    database = os.getenv('POSTGRES_DB') or os.getenv('POSTGRES_DATABASE') or os.getenv('PGDATABASE')
    port = os.getenv('POSTGRES_PORT') or os.getenv('PGPORT') or '5432'

    if host and user and password and database:
        built = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        print("Built database URL from POSTGRES_/PG* environment variables")
        return _normalize_pg_uri(built)

    # As a last resort, some platforms expose a plain connection string in PGDATA
    pgdata = os.getenv('PGDATA')
    if pgdata:
        print("Using PGDATA environment variable as connection info")
        return _normalize_pg_uri(pgdata)

    raise RuntimeError(
        "No PostgreSQL connection info found in environment. Set one of: DATABASE_URL, POSTGRES_CONNECTION_STRING, POSTGRES_URI, POSTGRES_URL, or provide POSTGRES_HOST/POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB (or PGHOST/PGUSER/PGPASSWORD/PGDATABASE)."
    )


# Internal Database URL (auto-detected). If no env is present at import time,
# don't raise — store None and let connection attempts raise a clear error later.
try:
    DATABASE_URL = get_database_url()
except RuntimeError as e:
    # Keep import-time safe: don't crash the whole process.
    print(f"Database URL not found at import: {e}")
    DATABASE_URL = None

def create_table():
    # If DATABASE_URL was not detected at import, skip table creation.
    if not DATABASE_URL:
        print("Skipping create_table: no DATABASE_URL available in environment.")
        return
    try:
        psycopg2, sql = _import_psycopg2()

        # psycopg2 accepts a DSN string; if provider requires SSL and the URI
        # doesn't specify sslmode, pass sslmode='require'.
        conn_kwargs = {}
        if 'sslmode' not in DATABASE_URL:
            conn_kwargs['sslmode'] = 'require'

        with psycopg2.connect(DATABASE_URL, **conn_kwargs) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS members (
                        name TEXT PRIMARY KEY,
                        val INT DEFAULT 0
                    );
                """)
                conn.commit()
    except Exception as e:
        # If the DB is not reachable at startup, print an informative message
        # but don't crash the whole process immediately.
        print(f"Warning: could not create table at startup: {e}")

# Note: do NOT run create_table() at import time to keep import safe.
# Call create_table() explicitly after startup if you want automatic table
# creation. This prevents failures when psycopg2 isn't installed or the DB
# is unreachable during import.

def get_connection():
    # Ensure we have a database URL when callers request a connection.
    if not DATABASE_URL:
        raise RuntimeError(
        "No DATABASE_URL available. Set DATABASE_URL or POSTGRES_* environment variables (Zeabur provides them)."
        )

    # Keep same ssl fallback logic as in create_table
    conn_kwargs = {}
    if 'sslmode' not in DATABASE_URL:
        conn_kwargs['sslmode'] = 'require'
    psycopg2, _ = _import_psycopg2()
    return psycopg2.connect(DATABASE_URL, **conn_kwargs)


def reset_database():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE members")
            conn.commit()


def is_member(name):
    psycopg2, sql = _import_psycopg2()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT COUNT(*) FROM members WHERE name = %s"), [name])
            return cur.fetchone()[0] > 0


def add_newMember(newMember):
    members = newMember.split(',')
    print(members)
    try:
        psycopg2, sql = _import_psycopg2()
        with get_connection() as conn:
            with conn.cursor() as cur:
                for member in members:
                    cur.execute(sql.SQL("INSERT INTO members (name) VALUES (%s) ON CONFLICT (name) DO NOTHING"),
                                [member])
                conn.commit()
    except Exception as e:
        print(f"An error occurred: {e}")


def get_all_members():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM members")
            return [row[0] for row in cur.fetchall()]


def delete_member(member):
    psycopg2, sql = _import_psycopg2()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("DELETE FROM members WHERE name = %s"), [member])
            conn.commit()


def remove_all_member():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM members")
            conn.commit()
