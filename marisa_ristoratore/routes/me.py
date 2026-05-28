import os
import uuid
import requests
from flask import Blueprint, request, jsonify, current_app
from middleware.auth import richiedi_ristoratore
from config import MAIN_BACKEND, UPLOAD_FOLDER, ALLOWED_EXTENSIONS
from utils import get_id_ristorante

me_bp = Blueprint("me", __name__)

def estensione_permessa(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# ── GET /ristoratore/me ───────────────────────────────────────────────────────
@me_bp.route("/ristoratore/me", methods=["GET"])
@richiedi_ristoratore
def get_me():
    token     = request.token
    utente_id = request.utente_id

    # 1. Dati utente
    try:
        r_utente = requests.get(
            f"{MAIN_BACKEND}/api/utenti/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
    except requests.exceptions.ConnectionError:
        return jsonify({"errore": "Main backend non raggiungibile"}), 503

    if r_utente.status_code != 200:
        return jsonify({"errore": "Errore recupero utente"}), 500

    utente = r_utente.json()

    # 2. Dati ristorante
    id_ristorante = get_id_ristorante(utente_id)
    if not id_ristorante:
        return jsonify({"errore": "Ristorante non trovato"}), 404

    try:
        r_rist = requests.get(
            f"{MAIN_BACKEND}/api/ristoranti/{id_ristorante}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
    except requests.exceptions.ConnectionError:
        return jsonify({"errore": "Main backend non raggiungibile"}), 503

    if r_rist.status_code != 200:
        return jsonify({"errore": "Errore recupero ristorante"}), 500

    ristorante = r_rist.json()

    return jsonify({
        "utente"    : utente,
        "ristorante": ristorante
    })


# ── PUT /ristoratore/me ───────────────────────────────────────────────────────
@me_bp.route("/ristoratore/me", methods=["PUT"])
@richiedi_ristoratore
def put_me():
    token     = request.token
    utente_id = request.utente_id

    id_ristorante = get_id_ristorante(utente_id)
    if not id_ristorante:
        return jsonify({"errore": "Ristorante non trovato"}), 404

    # Gestione upload foto
    foto_path = None
    if "foto" in request.files:
        foto = request.files["foto"]
        if foto.filename and estensione_permessa(foto.filename):
            ext      = foto.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            foto.save(os.path.join(UPLOAD_FOLDER, filename))
            foto_path = f"/static/uploads/{filename}"

    # Dati da aggiornare
    dati = request.form.to_dict() if request.content_type and \
           "multipart" in request.content_type else (request.get_json(silent=True) or {})

    if foto_path:
        dati["foto_profilo"] = foto_path

    try:
        r = requests.put(
            f"{MAIN_BACKEND}/api/ristoranti/{id_ristorante}",
            json=dati,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
    except requests.exceptions.ConnectionError:
        return jsonify({"errore": "Main backend non raggiungibile"}), 503

    if r.status_code != 200:
        return jsonify({"errore": "Errore aggiornamento ristorante", "dettaglio": r.json()}), 500

    return jsonify({"messaggio": "Profilo aggiornato", "ristorante": r.json()})
