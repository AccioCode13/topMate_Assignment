# db.py
import mysql.connector
from mysql.connector import pooling
import os

DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASS", "Shreya1322#"),
    "database": os.environ.get("MYSQL_DB", "ipl"),
    "port": int(os.environ.get("MYSQL_PORT", 3306)),
    "autocommit": True
}

# Simple connection pool
pool = pooling.MySQLConnectionPool(pool_name="ipl_pool", pool_size=5, **DB_CONFIG)

def query(sql: str, params: tuple = ()):
    conn = pool.get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        # try fetchall (SELECT) else return {}
        if cur.with_rows:
            rows = cur.fetchall()
            cur.close()
            return rows
        else:
            cur.close()
            return []
    finally:
        conn.close()
