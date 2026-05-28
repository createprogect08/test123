from flask import Blueprint, request, jsonify
from middleware.auth import richiedi_rider
from utils import get_db, get_id_rider

posizione_bp = Blueprint("posizione", __name__)


# ── POST /rider/posizione ─────────────────────────────────────────────────────
@posizione_bp.route("/rider/posizione", methods=["POST"])
@richiedi_rider
def aggiorna_posizione():
    utente_id = request.utente_id
    dati      = request.get_json(silent=True) or {}

    lat = dati.get("lat")
    lng = dati.get("lng")

    if lat is None or lng is None:
        return jsonify({"errore": "Campi obbligatori: lat, lng"}), 400

    id_rider = get_id_rider(utente_id)
    if not id_rider:
        return jsonify({"errore": "Profilo rider non trovato"}), 404

    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)

        # Aggiorna posizione corrente nel profilo rider
        cur.execute("UPDATE riders SET lat = %s, lng = %s WHERE id = %s", (lat, lng, id_rider))

        # Salva storico posizione
        cur.execute("""
            INSERT INTO rider_posizioni (id_rider, lat, lng)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE lat = %s, lng = %s, updated_at = CURRENT_TIMESTAMP
        """, (id_rider, lat, lng, lat, lng))

        # Trova ordine in_consegna assegnato a questo rider
        cur.execute("""
            SELECT id, id_utente FROM ordini
            WHERE id_rider = %s AND stato = 'in_consegna'
            LIMIT 1
        """, (id_rider,))
        ordine = cur.fetchone()

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"errore": f"Errore DB: {e}"}), 500

    # Notifica cliente via WebSocket
    if ordine:
        try:
            from app import socketio
            socketio.emit("rider_posizione", {
                "id_rider" : id_rider,
                "id_ordine": ordine["id"],
                "lat"      : lat,
                "lng"      : lng
            }, room=f"cliente_{ordine['id_utente']}")
        except Exception:
            pass

    return jsonify({"messaggio": "Posizione aggiornata", "lat": lat, "lng": lng})


# ── POST /rider/ordini/<id>/consegnato ────────────────────────────────────────
@posizione_bp.route("/rider/ordini/<int:id_ordine>/consegnato", methods=["POST"])
@richiedi_rider
def segna_consegnato(id_ordine):
    utente_id = request.utente_id

    id_rider = get_id_rider(utente_id)
    if not id_rider:
        return jsonify({"errore": "Profilo rider non trovato"}), 404

    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)

        # Verifica che l'ordine appartenga a questo rider
        cur.execute("""
            SELECT id, id_utente, stato FROM ordini
            WHERE id = %s AND id_rider = %s LIMIT 1
        """, (id_ordine, id_rider))
        ordine = cur.fetchone()

        if not ordine:
            cur.close(); conn.close()
            return jsonify({"errore": "Ordine non trovato o non assegnato a te"}), 404

        if ordine["stato"] != "in_consegna":
            cur.close(); conn.close()
            return jsonify({"errore": f"Stato ordine non valido: {ordine['stato']}"}), 409

        # Aggiorna stato
        cur.execute("UPDATE ordini SET stato = 'consegnato' WHERE id = %s", (id_ordine,))
        conn.commit()

        id_cliente = ordine["id_utente"]
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"errore": f"Errore DB: {e}"}), 500

    # Notifica cliente via WebSocket
    try:
        from app import socketio
        socketio.emit("ordine_consegnato", {
            "id_ordine": id_ordine,
            "messaggio": "Il tuo ordine è stato consegnato! 🎉"
        }, room=f"cliente_{id_cliente}")
    except Exception:
        pass

    return jsonify({"messaggio": "Ordine segnato come consegnato!", "id_ordine": id_ordine})
