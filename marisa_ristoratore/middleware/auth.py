import requests
from functools import wraps
from flask import request, jsonify
from config import AUTH_BACKEND

def richiedi_ristoratore(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"errore": "Token mancante"}), 401

        token = auth_header.split(" ", 1)[1]

        try:
            risposta = requests.get(
                f"{AUTH_BACKEND}/auth/verify",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )
        except requests.exceptions.ConnectionError:
            return jsonify({"errore": "Auth service non raggiungibile"}), 503

        if risposta.status_code != 200:
            return jsonify({"errore": "Token non valido o scaduto"}), 401

        dati = risposta.json()

        if not dati.get("valido"):
            return jsonify({"errore": "Token non valido"}), 401

        utente = dati.get("utente", {})
        if utente.get("tipo") != "ristoratore":
            return jsonify({"errore": "Accesso riservato ai ristoratori"}), 403

        # Inietta utente nella request
        request.utente    = utente
        request.utente_id = utente["id"]
        request.token     = token

        return f(*args, **kwargs)
    return decorated
