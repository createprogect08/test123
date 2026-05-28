import requests
from flask import Blueprint, request, jsonify
from middleware.auth import richiedi_rider
from config import MAIN_BACKEND
from utils import get_db, get_id_rider, calcola_distanza_km

ordini_bp = Blueprint("ordini", __name__)


# ── GET /rider/ordini/disponibili ─────────────────────────────────────────────
@ordini_bp.route("/rider/ordini/disponibili", methods=["GET"])
@richiedi_rider
def get_disponibili():
    utente_id = request.utente_id

    # Posizione rider dal DB
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT id, lat, lng FROM riders WHERE id_utente = %s LIMIT 1", (utente_id,))
        rider = cur.fetchone()

        # Ordini accettati dal ristorante, non ancora assegnati a un rider
        cur.execute("""
            SELECT o.*, r.nome AS nome_ristorante, r.lat AS lat_ristorante, r.lng AS lng_ristorante
            FROM ordini o
            JOIN ristoranti r ON o.id_ristorante = r.id
            WHERE o.stato = 'accettato' AND o.id_rider IS NULL
            ORDER BY o.created_at DESC
        """)
        ordini = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"errore": f"Errore DB: {e}"}), 500

    if not rider:
        return jsonify({"errore": "Profilo rider non trovato"}), 404

    # Converti decimali
    for o in ordini:
        for campo in ["totale", "lat_consegna", "lng_consegna", "lat_ristorante", "lng_ristorante"]:
            if o.get(campo) is not None:
                o[campo] = float(o[campo])
        if o.get("created_at"):
            o["created_at"] = o["created_at"].isoformat()

    # Filtra per raggio se rider ha posizione
    raggio = float(request.args.get("raggio", 10))
    if rider.get("lat") and rider.get("lng"):
        lat_r = float(rider["lat"])
        lng_r = float(rider["lng"])
        ordini_filtrati = []
        for o in ordini:
            if o.get("lat_ristorante") and o.get("lng_ristorante"):
                dist = calcola_distanza_km(lat_r, lng_r,
                                           o["lat_ristorante"], o["lng_ristorante"])
                o["distanza_km"] = round(dist, 2)
                if dist <= raggio:
                    ordini_filtrati.append(o)
            else:
                o["distanza_km"] = None
                ordini_filtrati.append(o)
        ordini = ordini_filtrati

    return jsonify({"ordini": ordini, "totale": len(ordini)})


# ── POST /rider/ordini/<id>/accetta ───────────────────────────────────────────
@ordini_bp.route("/rider/ordini/<int:id_ordine>/accetta", methods=["POST"])
@richiedi_rider
def accetta_ordine(id_ordine):
    utente_id = request.utente_id
    token     = request.token

    id_rider = get_id_rider(utente_id)
    if not id_rider:
        return jsonify({"errore": "Profilo rider non trovato"}), 404

    # Verifica che l'ordine sia ancora disponibile
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT id, stato, id_rider FROM ordini WHERE id = %s LIMIT 1", (id_ordine,))
        ordine = cur.fetchone()

        if not ordine:
            cur.close(); conn.close()
            return jsonify({"errore": "Ordine non trovato"}), 404

        if ordine["stato"] != "accettato" or ordine["id_rider"] is not None:
            cur.close(); conn.close()
            return jsonify({"errore": "Ordine non più disponibile"}), 409

        # Assegna rider e aggiorna stato
        cur.execute("""
            UPDATE ordini SET id_rider = %s, stato = 'in_consegna'
            WHERE id = %s AND stato = 'accettato' AND id_rider IS NULL
        """, (id_rider, id_ordine))
        conn.commit()

        if cur.rowcount == 0:
            cur.close(); conn.close()
            return jsonify({"errore": "Ordine già preso da un altro rider"}), 409

        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"errore": f"Errore DB: {e}"}), 500

    # Notifica WebSocket
    try:
        from app import socketio
        socketio.emit("ordine_assegnato", {
            "id_ordine": id_ordine,
            "id_rider" : id_rider
        }, room=f"ordine_{id_ordine}")
    except Exception:
        pass

    return jsonify({"messaggio": "Ordine accettato, sei in consegna!", "id_ordine": id_ordine})


# ── POST /rider/ordini/<id>/rifiuta ───────────────────────────────────────────
@ordini_bp.route("/rider/ordini/<int:id_ordine>/rifiuta", methods=["POST"])
@richiedi_rider
def rifiuta_ordine(id_ordine):
    # Il rider rifiuta — l'ordine torna disponibile (rimane accettato senza rider)
    return jsonify({"messaggio": "Ordine rifiutato, tornerà disponibile agli altri rider"})


# ── GET /rider/ordini/miei ────────────────────────────────────────────────────
@ordini_bp.route("/rider/ordini/miei", methods=["GET"])
@richiedi_rider
def get_miei_ordini():
    utente_id = request.utente_id

    id_rider = get_id_rider(utente_id)
    if not id_rider:
        return jsonify({"errore": "Profilo rider non trovato"}), 404

    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT o.*, r.nome AS nome_ristorante
            FROM ordini o
            JOIN ristoranti r ON o.id_ristorante = r.id
            WHERE o.id_rider = %s
            ORDER BY o.created_at DESC
        """, (id_rider,))
        ordini = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"errore": f"Errore DB: {e}"}), 500

    for o in ordini:
        for campo in ["totale", "lat_consegna", "lng_consegna"]:
            if o.get(campo) is not None:
                o[campo] = float(o[campo])
        if o.get("created_at"):
            o["created_at"] = o["created_at"].isoformat()

    return jsonify({"ordini": ordini, "totale": len(ordini)})


# ── POST /rider/ordini/<id>/sotto_casa ───────────────────────────────────────
@ordini_bp.route("/rider/ordini/<int:id_ordine>/sotto_casa", methods=["POST"])
@richiedi_rider
def sotto_casa(id_ordine):
    import random, string
    token = ''.join(random.choices(string.digits, k=6))
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT id_utente FROM ordini WHERE id = %s LIMIT 1", (id_ordine,))
        ordine = cur.fetchone()
        if ordine:
            cur.execute(
                "UPDATE ordini SET stato='sotto_casa', token_consegna=%s WHERE id=%s",
                (token, id_ordine)
            )
            conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"errore": f"Errore DB: {e}"}), 500

    if not ordine:
        return jsonify({"errore": "Ordine non trovato"}), 404

    try:
        from app import socketio
        socketio.emit("rider_sotto_casa", {
            "id_ordine": id_ordine,
            "token": token
        }, room=f"cliente_{ordine['id_utente']}")
    except Exception:
        pass

    return jsonify({"messaggio": "Utente notificato", "token": token})


# ── POST /rider/ordini/<id>/consegnato ────────────────────────────────────────
@ordini_bp.route("/rider/ordini/<int:id_ordine>/consegnato", methods=["POST"])
@richiedi_rider
def segna_consegnato(id_ordine):
    utente_id = request.utente_id
    id_rider  = get_id_rider(utente_id)

    d = request.get_json(silent=True) or {}
    token_input = str(d.get("token", "")).strip()

    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT token_consegna FROM ordini WHERE id=%s AND id_rider=%s LIMIT 1",
                    (id_ordine, id_rider))
        ordine = cur.fetchone()
        if not ordine:
            cur.close(); conn.close()
            return jsonify({"errore": "Ordine non trovato"}), 404
        if ordine["token_consegna"] != token_input:
            cur.close(); conn.close()
            return jsonify({"errore": "Codice non valido"}), 400
        cur.execute("UPDATE ordini SET stato='consegnato' WHERE id=%s AND id_rider=%s",
                    (id_ordine, id_rider))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"errore": f"Errore DB: {e}"}), 500

    try:
        from app import socketio
        socketio.emit("ordine_consegnato", {"id_ordine": id_ordine},
                      room=f"ordine_{id_ordine}")
    except Exception:
        pass

    return jsonify({"messaggio": "Ordine segnato come consegnato"})
