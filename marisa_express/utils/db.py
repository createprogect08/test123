# utils/db.py
import mysql.connector
from config import Config

def get_connection():
    """Restituisce una nuova connessione al database."""
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset="utf8mb4"
    )

def query(sql, params=None, fetchone=False, commit=False):
    """
    Esegue una query e restituisce i risultati come lista di dict.
    - fetchone=True  → restituisce un solo dict (o None)
    - commit=True    → esegue commit (INSERT/UPDATE/DELETE)
                       e restituisce lastrowid
    """
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        if commit:
            conn.commit()
            return cursor.lastrowid
        if fetchone:
            return cursor.fetchone()
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
