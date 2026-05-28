# routes/utenti.py
from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from utils.db import query
from utils.auth import genera_token, token_required

utenti_bp = Blueprint("utenti", __name__, url_prefix="/api/utenti")
bcrypt = Bcrypt()

# ── POST /api/utenti/registra ─────────────────────────────────────────────────
@utenti_bp.route("/registra", methods=["POST"])
def registra():
    d = request.get_json(silent=True) or {}
    required = ["nome", "email", "password", "tipo"]
    for campo in required:
        if not d.get(campo):
            return jsonify({"errore": f"Campo obbligatorio mancante: {campo}"}), 400

    if d["tipo"] not in ("utente", "rider", "ristoratore"):
        return jsonify({"errore": "Tipo non valido"}), 400

    # Email già esistente?
    esistente = query("SELECT id FROM utenti WHERE email=%s", (d["email"],), fetchone=True)
    if esistente:
        return jsonify({"errore": "Email già registrata"}), 409

    pw_hash = bcrypt.generate_password_hash(d["password"]).decode("utf-8")

    nuovo_id = query(
        """INSERT INTO utenti (nome, email, password_hash, telefono, tipo, foto_profilo)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (d["nome"], d["email"], pw_hash,
         d.get("telefono"), d["tipo"], d.get("foto_profilo")),
        commit=True
    )
    return jsonify({"messaggio": "Utente registrato", "id": nuovo_id}), 201


# ── POST /api/utenti/login ────────────────────────────────────────────────────
@utenti_bp.route("/login", methods=["POST"])
def login():
    d = request.get_json(silent=True) or {}
    if not d.get("email") or not d.get("password"):
        return jsonify({"errore": "Email e password obbligatorie"}), 400

    utente = query("SELECT * FROM utenti WHERE email=%s", (d["email"],), fetchone=True)
    if not utente or not bcrypt.check_password_hash(utente["password_hash"], d["password"]):
        return jsonify({"errore": "Credenziali non valide"}), 401

    token = genera_token(utente["id"], utente["tipo"])
    return jsonify({
        "token"  : token,
        "id"     : utente["id"],
        "nome"   : utente["nome"],
        "tipo"   : utente["tipo"],
        "crediti": float(utente["crediti"])
    })


# ── GET /api/utenti/<id> ──────────────────────────────────────────────────────
@utenti_bp.route("/<int:uid>", methods=["GET"])
@token_required
def get_utente(uid):
    utente = query(
        "SELECT id, nome, email, telefono, tipo, crediti, foto_profilo, created_at "
        "FROM utenti WHERE id=%s",
        (uid,), fetchone=True
    )
    if not utente:
        return jsonify({"errore": "Utente non trovato"}), 404
    utente["crediti"] = float(utente["crediti"])
    return jsonify(utente)


# ── PUT /api/utenti/<id> ──────────────────────────────────────────────────────
@utenti_bp.route("/<int:uid>", methods=["PUT"])
@token_required
def update_utente(uid):
    if request.utente_id != uid:
        return jsonify({"errore": "Non puoi modificare un altro utente"}), 403

    d = request.get_json(silent=True) or {}
    campi_aggiornabili = ["nome", "telefono", "foto_profilo"]
    aggiornamenti = {k: v for k, v in d.items() if k in campi_aggiornabili}

    if not aggiornamenti:
        return jsonify({"errore": "Nessun campo valido da aggiornare"}), 400

    set_clause = ", ".join(f"{k}=%s" for k in aggiornamenti)
    valori = list(aggiornamenti.values()) + [uid]
    query(f"UPDATE utenti SET {set_clause} WHERE id=%s", valori, commit=True)
    return jsonify({"messaggio": "Utente aggiornato"})


# ── DELETE /api/utenti/<id> ───────────────────────────────────────────────────
@utenti_bp.route("/<int:uid>", methods=["DELETE"])
@token_required
def delete_utente(uid):
    if request.utente_id != uid:
        return jsonify({"errore": "Non puoi eliminare un altro utente"}), 403

    query("DELETE FROM utenti WHERE id=%s", (uid,), commit=True)
    return jsonify({"messaggio": "Utente eliminato"})


# ── GET /api/utenti/me ────────────────────────────────────────────────────────
@utenti_bp.route("/me", methods=["GET"])
@token_required
def me():
    utente = query(
        "SELECT id, nome, email, telefono, tipo, crediti, foto_profilo, created_at "
        "FROM utenti WHERE id=%s",
        (request.utente_id,), fetchone=True
    )
    if not utente:
        return jsonify({"errore": "Utente non trovato"}), 404
    utente["crediti"] = float(utente["crediti"])
    return jsonify(utente)
