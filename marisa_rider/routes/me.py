import os
import uuid
import requests
from flask import Blueprint, request, jsonify
from middleware.auth import richiedi_rider
from config import MAIN_BACKEND, UPLOAD_FOLDER, ALLOWED_EXTENSIONS
from utils import get_db, get_id_rider

me_bp = Blueprint("me", __name__)

def estensione_permessa(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@me_bp.route("/rider/me", methods=["GET"])
@richiedi_rider
def get_me():
    token     = request.token
    utente_id = request.utente_id

    # Dati utente dal main backend
    try:
        r = requests.get(f"{MAIN_BACKEND}/api/utenti/me",
                         headers={"Authorization": f"Bearer {token}"}, timeout=5)
    except requests.exceptions.ConnectionError:
        return jsonify({"errore": "Main backend non raggiungibile"}), 503

    if r.status_code != 200:
        return jsonify({"errore": "Errore recupero utente"}), 500

    utente = r.json()

    # Dati rider dal DB
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM riders WHERE id_utente = %s LIMIT 1", (utente_id,))
        rider = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"errore": f"Errore DB: {e}"}), 500

    if not rider:
        return jsonify({"errore": "Profilo rider non trovato"}), 404

    # Converti decimali a float
    if rider.get("lat"): rider["lat"] = float(rider["lat"])
    if rider.get("lng"): rider["lng"] = float(rider["lng"])

    return jsonify({"utente": utente, "rider": rider})


@me_bp.route("/rider/me", methods=["PUT"])
@richiedi_rider
def put_me():
    utente_id = request.utente_id

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

    dati = request.form.to_dict() if request.content_type and \
           "multipart" in request.content_type else (request.get_json(silent=True) or {})

    campi_aggiornabili = ["veicolo", "targa", "disponibile"]
    updates = {k: v for k, v in dati.items() if k in campi_aggiornabili}
    if foto_path:
        updates["foto_profilo"] = foto_path

    if not updates:
        return jsonify({"errore": "Nessun campo da aggiornare"}), 400

    try:
        conn = get_db()
        cur  = conn.cursor()
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        cur.execute(f"UPDATE riders SET {set_clause} WHERE id_utente = %s",
                    list(updates.values()) + [utente_id])
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"errore": f"Errore DB: {e}"}), 500

    return jsonify({"messaggio": "Profilo aggiornato"})
