# routes/menu_items.py
from flask import Blueprint, request, jsonify
from utils.db import query
from utils.auth import token_required, solo_ristoratore

menu_bp = Blueprint("menu", __name__, url_prefix="/api/menu")

def _ristorante_di_proprieta(id_ristorante, utente_id):
    """Verifica che il ristorante appartenga all'utente loggato."""
    return query(
        "SELECT id FROM ristoranti WHERE id=%s AND id_utente=%s",
        (id_ristorante, utente_id), fetchone=True
    )

# ── POST /api/menu/<id_ristorante>/items ──────────────────────────────────────
@menu_bp.route("/<int:id_ristorante>/items", methods=["POST"])
@solo_ristoratore
def crea_item(id_ristorante):
    if not _ristorante_di_proprieta(id_ristorante, request.utente_id):
        return jsonify({"errore": "Non autorizzato"}), 403

    d = request.get_json(silent=True) or {}
    if not d.get("nome") or not d.get("prezzo"):
        return jsonify({"errore": "Campi obbligatori: nome, prezzo"}), 400

    nuovo_id = query(
        """INSERT INTO menu_items
           (id_ristorante, nome, descrizione, prezzo, foto, categoria, disponibile)
           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (id_ristorante, d["nome"], d.get("descrizione"),
         d["prezzo"], d.get("foto"), d.get("categoria"), d.get("disponibile", 1)),
        commit=True
    )
    return jsonify({"messaggio": "Item creato", "id": nuovo_id}), 201


# ── GET /api/menu/<id_ristorante>/items ───────────────────────────────────────
@menu_bp.route("/<int:id_ristorante>/items", methods=["GET"])
def lista_items(id_ristorante):
    ristorante = query(
        "SELECT id FROM ristoranti WHERE id=%s", (id_ristorante,), fetchone=True
    )
    if not ristorante:
        return jsonify({"errore": "Ristorante non trovato"}), 404

    solo_disponibili = request.args.get("disponibile", "0") == "1"
    sql = "SELECT * FROM menu_items WHERE id_ristorante=%s"
    params = [id_ristorante]
    if solo_disponibili:
        sql += " AND disponibile=1"

    items = query(sql, params)
    for item in items:
        item["prezzo"]      = float(item["prezzo"])
        item["disponibile"] = bool(item["disponibile"])
    return jsonify(items)


# ── GET /api/menu/items/<id> ──────────────────────────────────────────────────
@menu_bp.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = query(
        "SELECT * FROM menu_items WHERE id=%s", (item_id,), fetchone=True
    )
    if not item:
        return jsonify({"errore": "Item non trovato"}), 404
    item["prezzo"]      = float(item["prezzo"])
    item["disponibile"] = bool(item["disponibile"])
    return jsonify(item)


# ── PUT /api/menu/items/<id> ──────────────────────────────────────────────────
@menu_bp.route("/items/<int:item_id>", methods=["PUT"])
@solo_ristoratore
def update_item(item_id):
    item = query(
        "SELECT mi.*, r.id_utente FROM menu_items mi "
        "JOIN ristoranti r ON r.id = mi.id_ristorante "
        "WHERE mi.id=%s",
        (item_id,), fetchone=True
    )
    if not item:
        return jsonify({"errore": "Item non trovato"}), 404
    if item["id_utente"] != request.utente_id:
        return jsonify({"errore": "Non autorizzato"}), 403

    d = request.get_json(silent=True) or {}
    campi = ["nome", "descrizione", "prezzo", "foto", "categoria", "disponibile"]
    aggiornamenti = {k: v for k, v in d.items() if k in campi}
    if not aggiornamenti:
        return jsonify({"errore": "Nessun campo valido da aggiornare"}), 400

    set_clause = ", ".join(f"{k}=%s" for k in aggiornamenti)
    valori = list(aggiornamenti.values()) + [item_id]
    query(f"UPDATE menu_items SET {set_clause} WHERE id=%s", valori, commit=True)
    return jsonify({"messaggio": "Item aggiornato"})


# ── DELETE /api/menu/items/<id> ───────────────────────────────────────────────
@menu_bp.route("/items/<int:item_id>", methods=["DELETE"])
@solo_ristoratore
def delete_item(item_id):
    item = query(
        "SELECT mi.*, r.id_utente FROM menu_items mi "
        "JOIN ristoranti r ON r.id = mi.id_ristorante "
        "WHERE mi.id=%s",
        (item_id,), fetchone=True
    )
    if not item:
        return jsonify({"errore": "Item non trovato"}), 404
    if item["id_utente"] != request.utente_id:
        return jsonify({"errore": "Non autorizzato"}), 403

    query("DELETE FROM menu_items WHERE id=%s", (item_id,), commit=True)
    return jsonify({"messaggio": "Item eliminato"})