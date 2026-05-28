import mysql.connector
from config import DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME

def get_db():
    return mysql.connector.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASS,
        database=DB_NAME
    )

def get_id_ristorante(utente_id):
    """Recupera id_ristorante dal DB tramite id_utente."""
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT id FROM ristoranti WHERE id_utente = %s LIMIT 1", (utente_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row["id"] if row else None
    except Exception:
        return None
