# routes/ristoranti.py
from flask import Blueprint, request, jsonify
from utils.db import query
from utils.auth import token_required, solo_ristoratore

ristoranti_bp = Blueprint("ristoranti", __name__, url_prefix="/api/ristoranti")

@ristoranti_bp.route("", methods=["POST"])
@solo_ristoratore
def crea_ristorante():
    d = request.get_json(silent=True) or {}
    required = ["nome", "via", "lat", "lng"]
    for campo in required:
        if not d.get(campo):
            return jsonify({"errore": f"Campo obbligatorio mancante: {campo}"}), 400
    nuovo_id = query(
        """INSERT INTO ristoranti (id_utente, nome, descrizione, via, lat, lng, partita_iva, categoria)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
        (request.utente_id, d["nome"], d.get("descrizione"), d["via"],
         d["lat"], d["lng"], d.get("partita_iva"), d.get("categoria")),
        commit=True
    )
    return jsonify({"messaggio": "Ristorante creato", "id": nuovo_id}), 201

@ristoranti_bp.route("", methods=["GET"])
def lista_ristoranti():
    risultati = query("SELECT id, nome, descrizione, via, lat, lng, partita_iva, categoria FROM ristoranti")
    for r in risultati:
        r["lat"] = float(r["lat"]) if r["lat"] else None
        r["lng"] = float(r["lng"]) if r["lng"] else None
    return jsonify(risultati)

@ristoranti_bp.route("/vicini", methods=["GET"])
def ristoranti_vicini():
    try:
        lat    = float(request.args["lat"])
        lng    = float(request.args["lng"])
        raggio = float(request.args.get("raggio", 30))
    except (KeyError, ValueError):
        return jsonify({"errore": "Parametri lat e lng obbligatori e numerici"}), 400
    sql = """
        SELECT id, nome, descrizione, via, lat, lng, partita_iva, categoria,
            ROUND(6371 * 2 * ASIN(SQRT(
                POWER(SIN(RADIANS(lat - %s) / 2), 2) +
                COS(RADIANS(%s)) * COS(RADIANS(lat)) *
                POWER(SIN(RADIANS(lng - %s) / 2), 2)
            )), 2) AS distanza_km
        FROM ristoranti
        HAVING distanza_km <= %s
        ORDER BY distanza_km ASC
    """
    risultati = query(sql, (lat, lat, lng, raggio))
    for r in risultati:
        r["lat"]         = float(r["lat"]) if r["lat"] else None
        r["lng"]         = float(r["lng"]) if r["lng"] else None
        r["distanza_km"] = float(r["distanza_km"]) if r["distanza_km"] else None
    return jsonify(risultati)

@ristoranti_bp.route("/<int:rid>", methods=["GET"])
def get_ristorante(rid):
    ristorante = query("SELECT * FROM ristoranti WHERE id=%s", (rid,), fetchone=True)
    if not ristorante:
        return jsonify({"errore": "Ristorante non trovato"}), 404
    ristorante["lat"] = float(ristorante["lat"]) if ristorante["lat"] else None
    ristorante["lng"] = float(ristorante["lng"]) if ristorante["lng"] else None
    return jsonify(ristorante)

@ristoranti_bp.route("/<int:rid>", methods=["PUT"])
@solo_ristoratore
def update_ristorante(rid):
    ristorante = query("SELECT id, id_utente FROM ristoranti WHERE id=%s", (rid,), fetchone=True)
    if not ristorante:
        return jsonify({"errore": "Ristorante non trovato"}), 404
    if ristorante["id_utente"] != request.utente_id:
        return jsonify({"errore": "Non autorizzato"}), 403
    d = request.get_json(silent=True) or {}
    campi = ["nome", "descrizione", "via", "lat", "lng", "partita_iva", "categoria"]
    aggiornamenti = {k: v for k, v in d.items() if k in campi}
    if not aggiornamenti:
        return jsonify({"errore": "Nessun campo valido da aggiornare"}), 400
    set_clause = ", ".join(f"{k}=%s" for k in aggiornamenti)
    valori = list(aggiornamenti.values()) + [rid]
    query(f"UPDATE ristoranti SET {set_clause} WHERE id=%s", valori, commit=True)
    return jsonify({"messaggio": "Ristorante aggiornato"})

@ristoranti_bp.route("/<int:rid>", methods=["DELETE"])
@solo_ristoratore
def delete_ristorante(rid):
    ristorante = query("SELECT id, id_utente FROM ristoranti WHERE id=%s", (rid,), fetchone=True)
    if not ristorante:
        return jsonify({"errore": "Ristorante non trovato"}), 404
    if ristorante["id_utente"] != request.utente_id:
        return jsonify({"errore": "Non autorizzato"}), 403
    query("DELETE FROM ristoranti WHERE id=%s", (rid,), commit=True)
    return jsonify({"messaggio": "Ristorante eliminato"})
