# utils/jwt_helper.py
import jwt
import datetime
from config import Config
from utils.db import query

def genera_token(utente_id: int, tipo: str) -> str:
    """Genera un JWT firmato con id e tipo utente."""
    payload = {
        "sub" : str(utente_id),
        "tipo": tipo,
        "exp" : datetime.datetime.utcnow() + datetime.timedelta(hours=Config.JWT_EXPIRY_HOURS),
        "iat" : datetime.datetime.utcnow()
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")


def verifica_token(token: str) -> dict | None:
    """
    Verifica il token JWT.
    Ritorna il payload se valido, None se scaduto/invalido.
    Controlla anche la blacklist.
    """
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

    # Controlla blacklist
    in_blacklist = query(
        "SELECT id FROM token_blacklist WHERE token=%s",
        (token,), fetchone=True
    )
    if in_blacklist:
        return None

    payload["sub"] = int(payload["sub"])
    return payload


def blacklist_token(token: str) -> None:
    """Aggiunge il token alla blacklist (logout)."""
    # Evita duplicati
    esistente = query(
        "SELECT id FROM token_blacklist WHERE token=%s",
        (token,), fetchone=True
    )
    if not esistente:
        query(
            "INSERT INTO token_blacklist (token) VALUES (%s)",
            (token,), commit=True
        )


def get_redirect_url(tipo: str) -> str:
    """Ritorna il redirect_url in base al tipo utente."""
    from config import Config
    mapping = {
        "utente"      : Config.REDIRECT_UTENTE,
        "rider"       : Config.REDIRECT_RIDER,
        "ristoratore" : Config.REDIRECT_RISTORATORE
    }
    return mapping.get(tipo, Config.REDIRECT_UTENTE)


def token_da_header() -> str | None:
    """Estrae il Bearer token dall'header Authorization."""
    from flask import request
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(" ")[1]
    return None