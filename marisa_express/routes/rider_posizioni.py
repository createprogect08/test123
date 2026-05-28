# routes/rider_posizioni.py
from flask import Blueprint, request, jsonify
from utils.db import query
from utils.auth import token_required, solo_rider

rider_bp = Blueprint("rider", __name__, url_prefix="/api/rider")

# ── PUT /api/rider/posizione ──────────────────────────────────────────────────
# Il rider aggiorna la propria posizione (upsert)
@rider_bp.route("/posizione", methods=["PUT"])
@solo_rider
def aggiorna_posizione():
    d = request.get_json(silent=True) or {}
    try:
        lat = float(d["lat"])
        lng = float(d["lng"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"errore": "Campi lat e lng obbligatori e numerici"}), 400

    # UPSERT — inserisce o aggiorna se il rider esiste già
    query(
        """INSERT INTO rider_posizioni (id_rider, lat, lng)
           VALUES (%s, %s, %s)
           ON DUPLICATE KEY UPDATE lat=%s, lng=%s, updated_at=NOW()""",
        (request.utente_id, lat, lng, lat, lng),
        commit=True
    )
    return jsonify({
        "messaggio"  : "Posizione aggiornata",
        "id_rider"   : request.utente_id,
        "lat"        : lat,
        "lng"        : lng
    })


# ── GET /api/rider/posizione ──────────────────────────────────────────────────
# Il rider vede la propria posizione corrente
@rider_bp.route("/posizione", methods=["GET"])
@solo_rider
def get_posizione_propria():
    pos = query(
        "SELECT * FROM rider_posizioni WHERE id_rider=%s",
        (request.utente_id,), fetchone=True
    )
    if not pos:
        return jsonify({"errore": "Posizione non ancora registrata"}), 404
    pos["lat"] = float(pos["lat"])
    pos["lng"] = float(pos["lng"])
    return jsonify(pos)


# ── GET /api/rider/posizione/<id_rider> ───────────────────────────────────────
# Ristoratore o utente vede la posizione di un rider specifico
@rider_bp.route("/posizione/<int:id_rider>", methods=["GET"])
@token_required
def get_posizione_rider(id_rider):
    # Solo ristoratori e utenti con ordine attivo possono vedere la posizione
    if request.utente_tipo == "rider" and request.utente_id != id_rider:
        return jsonify({"errore": "Non autorizzato"}), 403

    pos = query(
        """SELECT rp.*, u.nome AS nome_rider
           FROM rider_posizioni rp
           JOIN utenti u ON u.id = rp.id_rider
           WHERE rp.id_rider=%s""",
        (id_rider,), fetchone=True
    )
    if not pos:
        return jsonify({"errore": "Posizione rider non trovata"}), 404
    pos["lat"] = float(pos["lat"])
    pos["lng"] = float(pos["lng"])
    return jsonify(pos)


# ── GET /api/rider/vicini?lat=xx&lng=yy&raggio=10 ────────────────────────────
# Trova rider attivi nelle vicinanze (utile per assegnazione ordini)
@rider_bp.route("/vicini", methods=["GET"])
@token_required
def rider_vicini():
    try:
        lat    = float(request.args["lat"])
        lng    = float(request.args["lng"])
        raggio = float(request.args.get("raggio", 10))
    except (KeyError, ValueError):
        return jsonify({"errore": "Parametri lat e lng obbligatori e numerici"}), 400

    sql = """
        SELECT
            rp.id_rider,
            u.nome AS nome_rider,
            rp.lat, rp.lng,
            rp.updated_at,
            ROUND(
                6371 * 2 * ASIN(SQRT(
                    POWER(SIN(RADIANS(rp.lat - %s) / 2), 2) +
                    COS(RADIANS(%s)) * COS(RADIANS(rp.lat)) *
                    POWER(SIN(RADIANS(rp.lng - %s) / 2), 2)
                )), 2
            ) AS distanza_km
        FROM rider_posizioni rp
        JOIN utenti u ON u.id = rp.id_rider
        HAVING distanza_km <= %s
        ORDER BY distanza_km ASC
    """
    risultati = query(sql, (lat, lat, lng, raggio))
    for r in risultati:
        r["lat"]         = float(r["lat"])
        r["lng"]         = float(r["lng"])
        r["distanza_km"] = float(r["distanza_km"])
    return jsonify(risultati)


# ── GET /api/rider/ordini-disponibili ─────────────────────────────────────────
# Il rider vede gli ordini accettati dai ristoranti ancora senza rider
@rider_bp.route("/ordini-disponibili", methods=["GET"])
@solo_rider
def ordini_disponibili():
    ordini = query(
        """SELECT o.id, o.totale, o.indirizzo_consegna,
                  o.lat_consegna, o.lng_consegna, o.created_at,
                  r.nome AS nome_ristorante, r.via AS via_ristorante,
                  r.lat AS lat_ristorante, r.lng AS lng_ristorante
           FROM ordini o
           JOIN ristoranti r ON r.id = o.id_ristorante
           WHERE o.stato = 'accettato' AND o.id_rider IS NULL
           ORDER BY o.created_at ASC"""
    )
    for o in ordini:
        o["totale"]          = float(o["totale"])
        o["lat_consegna"]    = float(o["lat_consegna"]) if o["lat_consegna"] else None
        o["lng_consegna"]    = float(o["lng_consegna"]) if o["lng_consegna"] else None
        o["lat_ristorante"]  = float(o["lat_ristorante"]) if o["lat_ristorante"] else None
        o["lng_ristorante"]  = float(o["lng_ristorante"]) if o["lng_ristorante"] else None
    return jsonify(ordini)