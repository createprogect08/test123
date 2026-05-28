import os
import uuid
import requests
from flask import Blueprint, request, jsonify
from middleware.auth import richiedi_ristoratore
from config import MAIN_BACKEND, UPLOAD_FOLDER, ALLOWED_EXTENSIONS
from utils import get_id_ristorante

menu_bp = Blueprint("menu", __name__)


def estensione_permessa(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ── GET /ristoratore/menu ─────────────────────────────────────────────────────
@menu_bp.route("/ristoratore/menu", methods=["GET"])
@richiedi_ristoratore
def get_menu():
    token     = request.token
    utente_id = request.utente_id

    id_ristorante = get_id_ristorante(utente_id)
    if not id_ristorante:
        return jsonify({"errore": "Ristorante non trovato"}), 404

    try:
        r = requests.get(
            f"{MAIN_BACKEND}/api/menu/{id_ristorante}/items",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
    except requests.exceptions.ConnectionError:
        return jsonify({"errore": "Main backend non raggiungibile"}), 503

    if r.status_code != 200:
        return jsonify({"errore": "Errore recupero menu"}), 500

    menu = r.json()

    # Estrai categorie uniche
    categorie = sorted(list(set(
        (item.get("categoria") or "").strip()
        for item in menu
        if (item.get("categoria") or "").strip()
    )))

    return jsonify({"menu": menu, "id_ristorante": id_ristorante, "categorie": categorie})


# ── POST /ristoratore/menu ────────────────────────────────────────────────────
@menu_bp.route("/ristoratore/menu", methods=["POST"])
@richiedi_ristoratore
def crea_item():
    token     = request.token
    utente_id = request.utente_id

    id_ristorante = get_id_ristorante(utente_id)
    if not id_ristorante:
        return jsonify({"errore": "Ristorante non trovato"}), 404

    # Gestione multipart (con immagine) o JSON
    if request.content_type and "multipart" in request.content_type:
        dati = request.form.to_dict()
        if dati.get("prezzo"):
            dati["prezzo"] = float(dati["prezzo"])
        if dati.get("disponibile"):
            dati["disponibile"] = dati["disponibile"].lower() == "true"

        if "immagine" in request.files:
            img = request.files["immagine"]
            if img.filename and estensione_permessa(img.filename):
                ext      = img.filename.rsplit('.', 1)[1].lower()
                filename = f"{uuid.uuid4().hex}.{ext}"
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                img.save(os.path.join(UPLOAD_FOLDER, filename))
                dati["foto"] = f"/static/uploads/{filename}"
    else:
        dati = request.get_json(silent=True) or {}

    if not dati.get("nome") or not dati.get("prezzo"):
        return jsonify({"errore": "Campi obbligatori: nome, prezzo"}), 400

    try:
        r = requests.post(
            f"{MAIN_BACKEND}/api/menu/{id_ristorante}/items",
            json=dati,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
    except requests.exceptions.ConnectionError:
        return jsonify({"errore": "Main backend non raggiungibile"}), 503

    if r.status_code != 201:
        return jsonify({"errore": "Errore creazione item", "dettaglio": r.json()}), 500

    return jsonify(r.json()), 201


# ── PUT /ristoratore/menu/<id> ────────────────────────────────────────────────
@menu_bp.route("/ristoratore/menu/<int:id_item>", methods=["PUT"])
@richiedi_ristoratore
def modifica_item(id_item):
    token = request.token

    if request.content_type and "multipart" in request.content_type:
        dati = request.form.to_dict()
        if dati.get("prezzo"):
            dati["prezzo"] = float(dati["prezzo"])
        if dati.get("disponibile"):
            dati["disponibile"] = dati["disponibile"].lower() == "true"

        if "immagine" in request.files:
            img = request.files["immagine"]
            if img.filename and estensione_permessa(img.filename):
                ext      = img.filename.rsplit('.', 1)[1].lower()
                filename = f"{uuid.uuid4().hex}.{ext}"
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                img.save(os.path.join(UPLOAD_FOLDER, filename))
                dati["foto"] = f"/static/uploads/{filename}"
    else:
        dati = request.get_json(silent=True) or {}

    try:
        r = requests.put(
            f"{MAIN_BACKEND}/api/menu/items/{id_item}",
            json=dati,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
    except requests.exceptions.ConnectionError:
        return jsonify({"errore": "Main backend non raggiungibile"}), 503

    if r.status_code == 404:
        return jsonify({"errore": "Item non trovato"}), 404
    if r.status_code != 200:
        return jsonify({"errore": "Errore modifica item"}), 500

    return jsonify(r.json())


# ── DELETE /ristoratore/menu/<id> ─────────────────────────────────────────────
@menu_bp.route("/ristoratore/menu/<int:id_item>", methods=["DELETE"])
@richiedi_ristoratore
def elimina_item(id_item):
    token = request.token

    try:
        r = requests.delete(
            f"{MAIN_BACKEND}/api/menu/items/{id_item}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
    except requests.exceptions.ConnectionError:
        return jsonify({"errore": "Main backend non raggiungibile"}), 503

    if r.status_code == 404:
        return jsonify({"errore": "Item non trovato"}), 404
    if r.status_code != 200:
        return jsonify({"errore": "Errore eliminazione item"}), 500

    return jsonify({"messaggio": "Item eliminato"})
