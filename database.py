import os
import psycopg2
from psycopg2 import sql

# Internal Database URL
DATABASE_URL = os.getenv('DATABASE_URL')

def create_table():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS members (
                    name TEXT PRIMARY KEY,
                    val INT DEFAULT 0
                );
            """)
            conn.commit()

# init table
create_table()

def get_connection():
    return psycopg2.connect(DATABASE_URL)


def reset_database():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE members")
            conn.commit()


def is_member(name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT COUNT(*) FROM members WHERE name = %s"), [name])
            return cur.fetchone()[0] > 0


def add_newMember(newMember):
    members = newMember.split(',')
    print(members)
    try:
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
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("DELETE FROM members WHERE name = %s"), [member])
            conn.commit()


def remove_all_member():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM members")
            conn.commit()
