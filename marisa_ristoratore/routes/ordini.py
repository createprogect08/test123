import requests
from flask import Blueprint, request, jsonify
from middleware.auth import richiedi_ristoratore
from config import MAIN_BACKEND
from utils import get_id_ristorante, get_db

ordini_bp = Blueprint("ordini", __name__)


def genera_token_ordine(id_ordine: int) -> str:
    return str(id_ordine % 1000).zfill(3)


# ── GET /ristoratore/ordini ───────────────────────────────────────────────────
@ordini_bp.route("/ristoratore/ordini", methods=["GET"])
@richiedi_ristoratore
def get_ordini():
    token     = request.token
    utente_id = request.utente_id

    try:
        r = requests.get(
            f"{MAIN_BACKEND}/api/ordini",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
    except requests.exceptions.ConnectionError:
        return jsonify({"errore": "Main backend non raggiungibile"}), 503

    if r.status_code != 200:
        return jsonify({"errore": "Errore recupero ordini"}), 500

    ordini = r.json()

    stato_filtro = request.args.get("stato", None)
    if stato_filtro:
        ordini = [o for o in ordini if o.get("stato") == stato_filtro]
    else:
        ordini = [o for o in ordini if o.get("stato") == "in_attesa"]

    # Carica items per ogni ordine
    for o in ordini:
        o["token_ordine"] = genera_token_ordine(o["id"])
        if not o.get("nome_utente") and o.get("id_utente"):
            try:
                r_u = requests.get(
                    f"{MAIN_BACKEND}/api/utenti/{o['id_utente']}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=3
                )
                if r_u.status_code == 200:
                    ud = r_u.json()
                    o["nome_utente"] = ud.get("nome") or ud.get("username") or "Cliente"
            except Exception:
                o["nome_utente"] = "Cliente"

        # Carica items dell'ordine
        if not o.get("items"):
            try:
                r_det = requests.get(
                    f"{MAIN_BACKEND}/api/ordini/{o['id']}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=3
                )
                if r_det.status_code == 200:
                    det = r_det.json()
                    o["items"] = det.get("items", [])
                    # Normalizza il campo prezzo
                    for item in o["items"]:
                        if "prezzo_unitario" in item and "prezzo" not in item:
                            item["prezzo"] = item["prezzo_unitario"]
            except Exception:
                o["items"] = []

    return jsonify({"ordini": ordini, "totale": len(ordini)})


# ── GET /ristoratore/ordini/<id> ──────────────────────────────────────────────
@ordini_bp.route("/ristoratore/ordini/<int:id_ordine>", methods=["GET"])
@richiedi_ristoratore
def get_ordine(id_ordine):
    token = request.token

    try:
        r = requests.get(
            f"{MAIN_BACKEND}/api/ordini/{id_ordine}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
    except requests.exceptions.ConnectionError:
        return jsonify({"errore": "Main backend non raggiungibile"}), 503

    if r.status_code == 404:
        return jsonify({"errore": "Ordine non trovato"}), 404
    if r.status_code != 200:
        return jsonify({"errore": "Errore recupero ordine"}), 500

    o = r.json()
    o["token_ordine"] = genera_token_ordine(id_ordine)
    # Normalizza prezzo
    for item in o.get("items", []):
        if "prezzo_unitario" in item and "prezzo" not in item:
            item["prezzo"] = item["prezzo_unitario"]
    return jsonify(o)


# ── POST /ristoratore/ordini/<id>/accetta ─────────────────────────────────────
@ordini_bp.route("/ristoratore/ordini/<int:id_ordine>/accetta", methods=["POST"])
@richiedi_ristoratore
def accetta_ordine(id_ordine):
    utente_id = request.utente_id
    id_ristorante = get_id_ristorante(utente_id)

    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id FROM ordini WHERE id=%s AND id_ristorante=%s LIMIT 1",
            (id_ordine, id_ristorante)
        )
        ordine = cur.fetchone()
        if not ordine:
            cur.close(); conn.close()
            return jsonify({"errore": "Ordine non trovato"}), 404

        cur.execute("UPDATE ordini SET stato='accettato' WHERE id=%s", (id_ordine,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"errore": f"Errore DB: {e}"}), 500

    try:
        from app import socketio
        socketio.emit("ordine_accettato", {
            "id_ordine": id_ordine
        }, room=f"ristorante_{id_ristorante}")
    except Exception:
        pass

    return jsonify({"messaggio": "Ordine accettato", "id_ordine": id_ordine})


# ── POST /ristoratore/ordini/<id>/rifiuta ─────────────────────────────────────
@ordini_bp.route("/ristoratore/ordini/<int:id_ordine>/rifiuta", methods=["POST"])
@richiedi_ristoratore
def rifiuta_ordine(id_ordine):
    token     = request.token
    utente_id = request.utente_id

    d      = request.get_json(silent=True) or {}
    motivo = d.get("motivo", "Ordine rifiutato dal ristorante")

    try:
        r = requests.put(
            f"{MAIN_BACKEND}/api/ordini/{id_ordine}/stato",
            json={"stato": "rifiutato"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
    except requests.exceptions.ConnectionError:
        return jsonify({"errore": "Main backend non raggiungibile"}), 503

    if r.status_code != 200:
        return jsonify({"errore": "Errore aggiornamento stato ordine"}), 500

    id_ristorante = get_id_ristorante(utente_id)
    try:
        from app import socketio
        socketio.emit("ordine_rifiutato", {
            "id_ordine": id_ordine,
            "motivo"   : motivo
        }, room=f"ristorante_{id_ristorante}")
    except Exception:
        pass

    return jsonify({"messaggio": "Ordine rifiutato", "motivo": motivo})


# ── POST /interno/nuovo_ordine ────────────────────────────────────────────────
from flask import Blueprint as _bp
from routes.ws import socketio as _socketio

@ordini_bp.route("/interno/nuovo_ordine", methods=["POST"])
def interno_nuovo_ordine():
    from flask import request as _req, jsonify as _json
    d = _req.get_json(silent=True) or {}
    id_ordine     = d.get("id_ordine")
    id_ristorante = d.get("id_ristorante")
    if id_ordine and id_ristorante:
        _socketio.emit("nuovo_ordine", {
            "ordine": {"id": id_ordine, "id_ristorante": id_ristorante}
        }, room=f"ristorante_{id_ristorante}")
    return _json({"ok": True})


@ordini_bp.route("/interno/ordine_assegnato", methods=["POST"])
def interno_ordine_assegnato():
    from flask import request as _req, jsonify as _json
    from routes.ws import socketio as _socketio
    d = _req.get_json(silent=True) or {}
    id_ordine     = d.get("id_ordine")
    id_ristorante = d.get("id_ristorante")
    if id_ordine and id_ristorante:
        _socketio.emit("ordine_assegnato", {
            "id_ordine": id_ordine
        }, room=f"ristorante_{id_ristorante}")
    return _json({"ok": True})
