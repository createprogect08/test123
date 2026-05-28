# routes/auth.py
from flask import Blueprint, request, jsonify
from pyisemail import is_email
from utils.db import query
from utils.jwt_helper import genera_token, verifica_token, blacklist_token, get_redirect_url, token_da_header
import requests as http
from config import Config

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

MAIN = Config.MAIN_BACKEND_URL

# ── POST /auth/check-email ────────────────────────────────────────────────────
@auth_bp.route("/check-email", methods=["POST"])
def check_email():
    d = request.get_json(silent=True) or {}
    email = d.get("email", "").strip().lower()

    if not email:
        return jsonify({"errore": "Email obbligatoria"}), 400

    if not is_email(email, check_dns=False):
        return jsonify({
            "errore"    : "Email non valida o dominio inesistente",
            "registrato": False,
            "tipo"      : None
        }), 422

    utente = query(
        "SELECT id, tipo FROM utenti WHERE email=%s",
        (email,), fetchone=True
    )

    if utente:
        return jsonify({"registrato": True, "tipo": utente["tipo"]})
    else:
        return jsonify({"registrato": False, "tipo": None})


# ── POST /auth/register/utente ────────────────────────────────────────────────
@auth_bp.route("/register/utente", methods=["POST"])
def register_utente():
    d = request.get_json(silent=True) or {}
    required = ["nome", "email", "password"]
    for campo in required:
        if not d.get(campo):
            return jsonify({"errore": f"Campo obbligatorio mancante: {campo}"}), 400

    email = d["email"].strip().lower()

    if not is_email(email, check_dns=False):
        return jsonify({"errore": "Email non valida o dominio inesistente"}), 422

    try:
        risposta = http.post(
            f"{MAIN}/api/utenti/registra",
            json={
                "nome"    : d["nome"],
                "email"   : email,
                "password": d["password"],
                "telefono": d.get("telefono"),
                "tipo"    : "utente"
            },
            timeout=5
        )
    except http.exceptions.ConnectionError:
        return jsonify({"errore": "Main backend non raggiungibile"}), 503

    if risposta.status_code == 409:
        return jsonify({"errore": "Email già registrata"}), 409
    if risposta.status_code != 201:
        return jsonify({"errore": "Errore durante la registrazione", "dettaglio": risposta.json()}), 500

    nuovo_id = risposta.json()["id"]
    token = genera_token(nuovo_id, "utente")

    return jsonify({
        "messaggio"   : "Registrazione completata",
        "token"       : token,
        "id"          : nuovo_id,
        "tipo"        : "utente",
        "redirect_url": get_redirect_url("utente") + "?token=" + token + "&nome=" + str(d.get("nome", "")) + "&id=" + str(nuovo_id) + "&tipo=utente"
    }), 201


# ── POST /auth/register/rider ─────────────────────────────────────────────────
@auth_bp.route("/register/rider", methods=["POST"])
def register_rider():
    d = request.get_json(silent=True) or {}
    required = ["nome", "cognome", "email", "password", "codice_fiscale"]
    for campo in required:
        if not d.get(campo):
            return jsonify({"errore": f"Campo obbligatorio mancante: {campo}"}), 400

    email = d["email"].strip().lower()

    if not is_email(email, check_dns=False):
        return jsonify({"errore": "Email non valida o dominio inesistente"}), 422

    # Codice fiscale uppercase
    cf = d["codice_fiscale"].strip().upper()
    if len(cf) != 16:
        return jsonify({"errore": "Codice fiscale non valido (16 caratteri)"}), 400

    # Verifica CF non già usato (tabella riders nel nuovo schema)
    cf_esistente = query(
        "SELECT id FROM riders WHERE codice_fiscale=%s",
        (cf,), fetchone=True
    )
    if cf_esistente:
        return jsonify({"errore": "Codice fiscale già registrato"}), 409

    # 1. Registra utente sul main backend
    try:
        risposta = http.post(
            f"{MAIN}/api/utenti/registra",
            json={
                "nome"    : d["nome"],
                "email"   : email,
                "password": d["password"],
                "telefono": d.get("telefono"),
                "tipo"    : "rider"
            },
            timeout=5
        )
    except http.exceptions.ConnectionError:
        return jsonify({"errore": "Main backend non raggiungibile"}), 503

    if risposta.status_code == 409:
        return jsonify({"errore": "Email già registrata"}), 409
    if risposta.status_code != 201:
        return jsonify({"errore": "Errore registrazione utente", "dettaglio": risposta.json()}), 500

    nuovo_id = risposta.json()["id"]

    # 2. Salva dettagli rider nella tabella riders (schema unificato)
    try:
        query(
            """INSERT INTO riders
               (id_utente, nome, codice_fiscale, telefono, zona)
               VALUES (%s, %s, %s, %s, %s)""",
            (nuovo_id, d["nome"], cf, d.get("telefono"), d.get("zona")),
            commit=True
        )
    except Exception as e:
        # Rollback: elimina utente appena creato
        http.delete(f"{MAIN}/api/utenti/{nuovo_id}", timeout=5)
        return jsonify({"errore": "Errore salvataggio dettagli rider", "dettaglio": str(e)}), 500

    # 4. Genera JWT
    token = genera_token(nuovo_id, "rider")

    return jsonify({
        "messaggio"   : "Registrazione rider completata",
        "token"       : token,
        "id"          : nuovo_id,
        "tipo"        : "rider",
        "redirect_url": get_redirect_url("rider") + "?token=" + token + "&nome=" + str(d.get("nome", "")) + "&id=" + str(nuovo_id) + "&tipo=rider"
    }), 201


# ── POST /auth/register/ristoratore ──────────────────────────────────────────
@auth_bp.route("/register/ristoratore", methods=["POST"])
def register_ristoratore():
    d = request.get_json(silent=True) or {}

    # Campi obbligatori utente
    required_utente = ["nome", "email", "password"]
    for campo in required_utente:
        if not d.get(campo):
            return jsonify({"errore": f"Campo obbligatorio mancante: {campo}"}), 400

    # Campi obbligatori ristorante
    required_ristorante = ["nome_ristorante", "via", "lat", "lng"]
    for campo in required_ristorante:
        if not d.get(campo):
            return jsonify({"errore": f"Campo obbligatorio mancante: {campo}"}), 400

    email = d["email"].strip().lower()

    if not is_email(email, check_dns=False):
        return jsonify({"errore": "Email non valida o dominio inesistente"}), 422

    # 1. Registra utente ristoratore sul main backend
    try:
        risposta_utente = http.post(
            f"{MAIN}/api/utenti/registra",
            json={
                "nome"    : d["nome"],
                "email"   : email,
                "password": d["password"],
                "telefono": d.get("telefono"),
                "tipo"    : "ristoratore"
            },
            timeout=5
        )
    except http.exceptions.ConnectionError:
        return jsonify({"errore": "Main backend non raggiungibile"}), 503

    if risposta_utente.status_code == 409:
        return jsonify({"errore": "Email già registrata"}), 409
    if risposta_utente.status_code != 201:
        return jsonify({"errore": "Errore registrazione utente", "dettaglio": risposta_utente.json()}), 500

    nuovo_id = risposta_utente.json()["id"]

    # 2. Login sul main backend per ottenere il token :5000
    try:
        risposta_login = http.post(
            f"{MAIN}/api/utenti/login",
            json={"email": email, "password": d["password"]},
            timeout=5
        )
    except http.exceptions.ConnectionError:
        query("DELETE FROM utenti WHERE id=%s", (nuovo_id,), commit=True)
        return jsonify({"errore": "Main backend non raggiungibile"}), 503

    if risposta_login.status_code != 200:
        query("DELETE FROM utenti WHERE id=%s", (nuovo_id,), commit=True)
        return jsonify({"errore": "Errore login dopo registrazione"}), 500

    token_main = risposta_login.json()["token"]

    # 3. Crea ristorante sul main backend
    try:
        risposta_ristorante = http.post(
            f"{MAIN}/api/ristoranti",
            json={
                "nome"       : d["nome_ristorante"],
                "via"        : d["via"],
                "lat"        : d["lat"],
                "lng"        : d["lng"],
                "descrizione": d.get("descrizione"),
                "partita_iva": d.get("partita_iva"),
                "categoria"  : d.get("categoria"),
            },
            headers={"Authorization": f"Bearer {token_main}"},
            timeout=5
        )
    except http.exceptions.ConnectionError:
        query("DELETE FROM utenti WHERE id=%s", (nuovo_id,), commit=True)
        return jsonify({"errore": "Main backend non raggiungibile"}), 503

    if risposta_ristorante.status_code != 201:
        query("DELETE FROM utenti WHERE id=%s", (nuovo_id,), commit=True)
        return jsonify({"errore": "Errore creazione ristorante", "dettaglio": risposta_ristorante.json()}), 500

    id_ristorante = risposta_ristorante.json()["id"]

    # 4. Genera JWT auth service
    token = genera_token(nuovo_id, "ristoratore")

    return jsonify({
        "messaggio"     : "Registrazione ristoratore completata",
        "token"         : token,
        "id"            : nuovo_id,
        "id_ristorante" : id_ristorante,
        "tipo"          : "ristoratore",
        "redirect_url"  : get_redirect_url("ristoratore") + "?token=" + token + "&nome=" + str(d.get("nome", "")) + "&id=" + str(nuovo_id) + "&tipo=ristoratore"
    }), 201


# ── POST /auth/login ──────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    d = request.get_json(silent=True) or {}
    if not d.get("email") or not d.get("password"):
        return jsonify({"errore": "Email e password obbligatorie"}), 400

    email = d["email"].strip().lower()

    # Chiama il main backend
    try:
        risposta = http.post(
            f"{MAIN}/api/utenti/login",
            json={"email": email, "password": d["password"]},
            timeout=5
        )
    except http.exceptions.ConnectionError:
        return jsonify({"errore": "Main backend non raggiungibile"}), 503

    if risposta.status_code == 401:
        return jsonify({"errore": "Credenziali non valide"}), 401
    if risposta.status_code != 200:
        return jsonify({"errore": "Errore durante il login"}), 500

    dati = risposta.json()
    utente_id = dati["id"]
    tipo      = dati["tipo"]
    nome      = dati["nome"]
    crediti   = dati.get("crediti", 0.0)

    # Genera JWT auth service
    token = genera_token(utente_id, tipo)

    return jsonify({
        "messaggio"   : "Login effettuato",
        "token"       : token,
        "id"          : utente_id,
        "nome"        : nome,
        "tipo"        : tipo,
        "crediti"     : crediti,
        "redirect_url": get_redirect_url(tipo) + "?token=" + token + "&nome=" + nome + "&id=" + str(utente_id) + "&tipo=" + tipo
    })


# ── GET /auth/verify ──────────────────────────────────────────────────────────
@auth_bp.route("/verify", methods=["GET"])
def verify():
    token = token_da_header()
    if not token:
        return jsonify({"valido": False, "errore": "Token mancante"}), 401

    payload = verifica_token(token)
    if not payload:
        return jsonify({"valido": False, "errore": "Token non valido o scaduto"}), 401

    # Recupera dati aggiornati utente dal main backend
    try:
        risposta = http.get(
            f"{MAIN}/api/utenti/{payload['sub']}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
    except http.exceptions.ConnectionError:
        # Ritorna comunque i dati dal token se il main è irraggiungibile
        return jsonify({
            "valido": True,
            "utente": {
                "id"  : payload["sub"],
                "tipo": payload["tipo"]
            },
            "avviso": "Main backend non raggiungibile, dati parziali"
        })

    if risposta.status_code != 200:
        return jsonify({"valido": False, "errore": "Utente non trovato"}), 401

    utente = risposta.json()
    return jsonify({
        "valido": True,
        "utente": {
            "id"          : utente["id"],
            "nome"        : utente["nome"],
            "email"       : utente["email"],
            "tipo"        : utente["tipo"],
            "crediti"     : utente.get("crediti", 0.0),
            "foto_profilo": utente.get("foto_profilo"),
            "created_at"  : utente.get("created_at")
        },
        "redirect_url": get_redirect_url(utente["tipo"]) + "?token=" + token_da_header() + "&nome=" + utente["nome"] + "&id=" + str(utente["id"]) + "&tipo=" + utente["tipo"]
    })


# ── POST /auth/logout ─────────────────────────────────────────────────────────
@auth_bp.route("/logout", methods=["POST"])
def logout():
    token = token_da_header()
    if not token:
        return jsonify({"errore": "Token mancante"}), 401

    payload = verifica_token(token)
    if not payload:
        return jsonify({"errore": "Token non valido o già scaduto"}), 401

    blacklist_token(token)
    return jsonify({"messaggio": "Logout effettuato"})
