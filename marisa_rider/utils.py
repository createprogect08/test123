import mysql.connector
from config import DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME

def get_db():
    return mysql.connector.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASS,
        database=DB_NAME
    )

def get_id_rider(utente_id):
    """Recupera id_rider dal DB tramite id_utente."""
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT id FROM riders WHERE id_utente = %s LIMIT 1", (utente_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row["id"] if row else None
    except Exception as e:
        print(f"Errore get_id_rider: {e}")
        return None

def calcola_distanza_km(lat1, lng1, lat2, lng2):
    """Calcola distanza approssimativa in km tra due coordinate."""
    from math import radians, sin, cos, sqrt, atan2
    R = 6371
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))
