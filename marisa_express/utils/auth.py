# utils/auth.py
import jwt
import datetime
from functools import wraps
from flask import request, jsonify
from config import Config

def genera_token(utente_id, tipo):
    payload = {
        "sub"  : str(utente_id),  # <-- stringa!
        "tipo" : tipo,
        "exp"  : datetime.datetime.utcnow() + datetime.timedelta(hours=Config.JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        if not token:
            return jsonify({"errore": "Token mancante"}), 401
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            request.utente_id = int(payload["sub"])  # <-- riconverti a int
            request.utente_tipo = payload["tipo"]
        except jwt.ExpiredSignatureError:
            return jsonify({"errore": "Token scaduto"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"errore": "Token non valido"}), 401
        return f(*args, **kwargs)
    return decorated

def solo_rider(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.utente_tipo != "rider":
            return jsonify({"errore": "Accesso riservato ai rider"}), 403
        return f(*args, **kwargs)
    return decorated

def solo_ristoratore(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.utente_tipo != "ristoratore":
            return jsonify({"errore": "Accesso riservato ai ristoratori"}), 403
        return f(*args, **kwargs)
    return decorated