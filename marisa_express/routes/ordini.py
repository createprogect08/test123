import stripe
import os
import requests as req_ext
from flask import Blueprint, request, jsonify
from utils.db import query
from utils.auth import token_required, solo_rider, solo_ristoratore

ordini_bp = Blueprint("ordini", __name__, url_prefix="/api/ordini")


def notifica_nuovo_ordine(id_ordine, id_ristorante):
    """Notifica il marisa_ristoratore di un nuovo ordine via HTTP interno."""
    try:
        req_ext.post(
            "http://marisa-ristoratore:5002/interno/nuovo_ordine",
            json={"id_ordine": id_ordine, "id_ristorante": id_ristorante},
            timeout=2
        )
    except Exception:
        pass


# ── POST /api/ordini ──────────────────────────────────────────────────────────
@ordini_bp.route("", methods=["POST"])
@token_required
def crea_ordine():
    d = request.get_json(silent=True) or {}
    required = ["id_ristorante", "indirizzo_consegna", "lat_consegna",
                "lng_consegna", "items"]
    for campo in required:
        if d.get(campo) is None or d.get(campo) == "":
            return jsonify({"errore": f"Campo obbligatorio mancante: {campo}"}), 400

    if not isinstance(d["items"], list) or len(d["items"]) == 0:
        return jsonify({"errore": "items deve essere una lista non vuota"}), 400

    ristorante = query(
        "SELECT id FROM ristoranti WHERE id=%s",
        (d["id_ristorante"],), fetchone=True
    )
    if not ristorante:
        return jsonify({"errore": "Ristorante non trovato"}), 404

    totale = 0.0
    items_validati = []
    for item in d["items"]:
        if not item.get("id_menu_item") or not item.get("quantita"):
            return jsonify({"errore": "Ogni item deve avere id_menu_item e quantita"}), 400

        menu_item = query(
            "SELECT id, prezzo, disponibile, nome FROM menu_items WHERE id=%s AND id_ristorante=%s",
            (item["id_menu_item"], d["id_ristorante"]), fetchone=True
        )
        if not menu_item:
            return jsonify({"errore": f"Item {item['id_menu_item']} non trovato in questo ristorante"}), 404
        if not menu_item["disponibile"]:
            return jsonify({"errore": f"Item {item['id_menu_item']} non disponibile"}), 400

        prezzo_unitario = float(menu_item["prezzo"])
        totale += prezzo_unitario * int(item["quantita"])
        items_validati.append({
            "id_menu_item"   : menu_item["id"],
            "nome"           : menu_item["nome"],
            "quantita"       : int(item["quantita"]),
            "prezzo_unitario": prezzo_unitario
        })

    metodo = d.get("metodo_pagamento", "crediti")

    if metodo == "stripe":
        stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
        if not stripe.api_key:
            return jsonify({"errore": "Stripe non configurato sul server"}), 500

        id_ordine = query(
            """INSERT INTO ordini
               (id_utente, id_ristorante, stato, totale,
                indirizzo_consegna, lat_consegna, lng_consegna)
               VALUES (%s,%s,'pending_stripe',%s,%s,%s,%s)""",
            (request.utente_id, d["id_ristorante"], totale,
             d["indirizzo_consegna"], d["lat_consegna"], d["lng_consegna"]),
            commit=True
        )
        for item in items_validati:
            query(
                "INSERT INTO ordini_items (id_ordine, id_menu_item, quantita, prezzo_unitario) "
                "VALUES (%s,%s,%s,%s)",
                (id_ordine, item["id_menu_item"], item["quantita"], item["prezzo_unitario"]),
                commit=True
            )

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "eur",
                        "product_data": {"name": f"Ordine Marisa Express #{id_ordine}"},
                        "unit_amount": int(totale * 100),
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=f"https://reimagined-orbit-r44jxj94649qhpv6-3000.app.github.dev/order/{id_ordine}?stripe=ok",
                cancel_url=f"https://reimagined-orbit-r44jxj94649qhpv6-3000.app.github.dev/checkout?stripe=cancel",
                metadata={"id_ordine": str(id_ordine), "id_utente": str(request.utente_id)}
            )
        except Exception as e:
            query("UPDATE ordini SET stato='annullato' WHERE id=%s", (id_ordine,), commit=True)
            return jsonify({"errore": f"Errore Stripe: {str(e)}"}), 500

        return jsonify({
            "messaggio": "Sessione Stripe creata",
            "id": id_ordine,
            "totale": totale,
            "stripe_url": session.url
        }), 201

    # ── CREDITI ───────────────────────────────────────────────────────────────
    utente = query(
        "SELECT crediti, nome FROM utenti WHERE id=%s",
        (request.utente_id,), fetchone=True
    )
    if float(utente["crediti"]) < totale:
        return jsonify({"errore": "Crediti insufficienti", "crediti": float(utente["crediti"]), "totale": totale}), 400

    id_ordine = query(
        """INSERT INTO ordini
           (id_utente, id_ristorante, stato, totale,
            indirizzo_consegna, lat_consegna, lng_consegna)
           VALUES (%s,%s,'in_attesa',%s,%s,%s,%s)""",
        (request.utente_id, d["id_ristorante"], totale,
         d["indirizzo_consegna"], d["lat_consegna"], d["lng_consegna"]),
        commit=True
    )
    for item in items_validati:
        query(
            "INSERT INTO ordini_items (id_ordine, id_menu_item, quantita, prezzo_unitario) "
            "VALUES (%s,%s,%s,%s)",
            (id_ordine, item["id_menu_item"], item["quantita"], item["prezzo_unitario"]),
            commit=True
        )
    query("UPDATE utenti SET crediti = crediti - %s WHERE id=%s", (totale, request.utente_id), commit=True)
    query("INSERT INTO wallet_transazioni (id_utente, importo, tipo) VALUES (%s,%s,'pagamento')",
          (request.utente_id, totale), commit=True)

    # Notifica WebSocket al ristoratore
    notifica_nuovo_ordine(id_ordine, d["id_ristorante"])

    return jsonify({"messaggio": "Ordine creato", "id": id_ordine, "totale": totale}), 201


# ── GET /api/ordini ───────────────────────────────────────────────────────────
@ordini_bp.route("", methods=["GET"])
@token_required
def lista_ordini():
    tipo = request.utente_tipo

    if tipo == "utente":
        ordini = query(
            "SELECT o.*, r.nome AS nome_ristorante FROM ordini o "
            "JOIN ristoranti r ON r.id = o.id_ristorante "
            "WHERE o.id_utente=%s ORDER BY o.created_at DESC",
            (request.utente_id,)
        )
    elif tipo == "rider":
        ordini = query(
            "SELECT o.*, r.nome AS nome_ristorante FROM ordini o "
            "JOIN ristoranti r ON r.id = o.id_ristorante "
            "WHERE o.id_rider=%s OR (o.stato='accettato' AND o.id_rider IS NULL) "
            "ORDER BY o.created_at DESC",
            (request.utente_id,)
        )
    elif tipo == "ristoratore":
        ordini = query(
            "SELECT o.*, r.nome AS nome_ristorante FROM ordini o "
            "JOIN ristoranti r ON r.id = o.id_ristorante "
            "WHERE r.id_utente=%s ORDER BY o.created_at DESC",
            (request.utente_id,)
        )
    else:
        ordini = []

    for o in ordini:
        o["totale"]       = float(o["totale"])
        o["lat_consegna"] = float(o["lat_consegna"]) if o["lat_consegna"] else None
        o["lng_consegna"] = float(o["lng_consegna"]) if o["lng_consegna"] else None
    return jsonify(ordini)


# ── GET /api/ordini/<id> ──────────────────────────────────────────────────────
@ordini_bp.route("/<int:oid>", methods=["GET"])
@token_required
def get_ordine(oid):
    ordine = query(
        "SELECT o.*, r.nome AS nome_ristorante FROM ordini o "
        "JOIN ristoranti r ON r.id = o.id_ristorante "
        "WHERE o.id=%s",
        (oid,), fetchone=True
    )
    if not ordine:
        return jsonify({"errore": "Ordine non trovato"}), 404

    if (request.utente_tipo == "utente" and ordine["id_utente"] != request.utente_id and
            ordine["id_rider"] != request.utente_id):
        return jsonify({"errore": "Non autorizzato"}), 403

    items = query(
        "SELECT oi.*, mi.nome FROM ordini_items oi "
        "JOIN menu_items mi ON mi.id = oi.id_menu_item "
        "WHERE oi.id_ordine=%s",
        (oid,)
    )
    for item in items:
        item["prezzo_unitario"] = float(item["prezzo_unitario"])

    ordine["totale"]       = float(ordine["totale"])
    ordine["lat_consegna"] = float(ordine["lat_consegna"]) if ordine["lat_consegna"] else None
    ordine["lng_consegna"] = float(ordine["lng_consegna"]) if ordine["lng_consegna"] else None
    ordine["items"]        = items
    return jsonify(ordine)


# ── PUT /api/ordini/<id>/stato ────────────────────────────────────────────────
@ordini_bp.route("/<int:oid>/stato", methods=["PUT"])
@token_required
def aggiorna_stato(oid):
    ordine = query(
        "SELECT o.*, r.id_utente AS id_ristoratore FROM ordini o "
        "JOIN ristoranti r ON r.id = o.id_ristorante "
        "WHERE o.id=%s",
        (oid,), fetchone=True
    )
    if not ordine:
        return jsonify({"errore": "Ordine non trovato"}), 404

    d = request.get_json(silent=True) or {}
    nuovo_stato = d.get("stato")

    stati_validi = ("in_attesa", "accettato", "in_consegna", "consegnato", "rifiutato")
    if nuovo_stato not in stati_validi:
        return jsonify({"errore": f"Stato non valido. Valori: {stati_validi}"}), 400

    tipo = request.utente_tipo

    if tipo == "ristoratore":
        if ordine["id_ristoratore"] != request.utente_id:
            return jsonify({"errore": "Non autorizzato"}), 403
        if nuovo_stato not in ("accettato", "rifiutato"):
            return jsonify({"errore": "Il ristoratore può solo accettare o rifiutare"}), 400
        if nuovo_stato == "rifiutato":
            query("UPDATE utenti SET crediti = crediti + %s WHERE id=%s",
                  (ordine["totale"], ordine["id_utente"]), commit=True)
            query("INSERT INTO wallet_transazioni (id_utente, importo, tipo) VALUES (%s,%s,'rimborso')",
                  (ordine["id_utente"], ordine["totale"]), commit=True)
    elif tipo == "rider":
        if nuovo_stato == "in_consegna":
            query("UPDATE ordini SET stato=%s, id_rider=%s WHERE id=%s",
                  (nuovo_stato, request.utente_id, oid), commit=True)
            return jsonify({"messaggio": "Stato aggiornato"})
        elif nuovo_stato == "consegnato":
            if ordine["id_rider"] != request.utente_id:
                return jsonify({"errore": "Non autorizzato"}), 403
        else:
            return jsonify({"errore": "Il rider può solo impostare in_consegna o consegnato"}), 400
    else:
        return jsonify({"errore": "Non autorizzato"}), 403

    query("UPDATE ordini SET stato=%s WHERE id=%s", (nuovo_stato, oid), commit=True)
    return jsonify({"messaggio": "Stato aggiornato"})


# ── DELETE /api/ordini/<id> ───────────────────────────────────────────────────
@ordini_bp.route("/<int:oid>", methods=["DELETE"])
@token_required
def annulla_ordine(oid):
    ordine = query(
        "SELECT * FROM ordini WHERE id=%s AND id_utente=%s",
        (oid, request.utente_id), fetchone=True
    )
    if not ordine:
        return jsonify({"errore": "Ordine non trovato"}), 404

    stati_annullabili = ("in_attesa", "accettato")
    if ordine["stato"] not in stati_annullabili:
        return jsonify({"errore": "Non puoi annullare un ordine già in consegna o consegnato"}), 400

    query("UPDATE utenti SET crediti = crediti + %s WHERE id=%s",
          (ordine["totale"], request.utente_id), commit=True)
    query("INSERT INTO wallet_transazioni (id_utente, importo, tipo) VALUES (%s,%s,'rimborso')",
          (request.utente_id, ordine["totale"]), commit=True)
    query("UPDATE ordini SET stato='annullato' WHERE id=%s", (oid,), commit=True)
    try:
        import requests as _r
        _r.post(
            "http://marisa-ristoratore:5002/interno/ordine_annullato",
            json={"id_ordine": oid, "id_ristorante": ordine["id_ristorante"]},
            timeout=2
        )
    except Exception:
        pass
    return jsonify({"messaggio": "Ordine annullato e crediti rimborsati", "rimborso": float(ordine["totale"])})


# ── POST /api/ordini/<id>/conferma_token ─────────────────────────────────────
@ordini_bp.route("/<int:oid>/conferma_token", methods=["POST"])
@token_required
def conferma_token(oid):
    import secrets
    d = request.get_json(silent=True) or {}
    token_input = str(d.get("token", "")).strip().upper()

    ordine = query(
        "SELECT * FROM ordini WHERE id=%s AND id_utente=%s",
        (oid, request.utente_id), fetchone=True
    )
    if not ordine:
        return jsonify({"errore": "Ordine non trovato"}), 404

    if ordine["stato"] != "sotto_casa":
        return jsonify({"errore": "L'ordine non è nello stato corretto"}), 400

    token_atteso = str(ordine.get("token_consegna") or "").strip().upper()
    if not token_atteso or not secrets.compare_digest(token_input, token_atteso):
        return jsonify({"errore": "Token non valido"}), 400

    query("UPDATE ordini SET stato='consegnato' WHERE id=%s", (oid,), commit=True)

    try:
        req_ext.post(f"http://marisa-rider:5003/interno/ordine_completato",
                     json={"id_ordine": oid}, timeout=2)
    except Exception:
        pass

    return jsonify({"messaggio": "Ordine confermato e completato"})


# ── POST /api/ordini/stripe_webhook ──────────────────────────────────────────
@ordini_bp.route("/stripe_webhook", methods=["POST"])
def stripe_webhook():
    import stripe, os
    from flask import request as req
    payload = req.get_data()
    sig_header = req.headers.get("Stripe-Signature", "")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            event = stripe.Event.construct_from(
                __import__('json').loads(payload), stripe.api_key
            )
    except Exception as e:
        return jsonify({"errore": str(e)}), 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        meta      = session.get("metadata", {})
        id_ordine = meta.get("id_ordine")
        id_utente = meta.get("id_utente")
        tipo      = meta.get("tipo", "ordine")
        importo   = (session.get("amount_total") or 0) / 100

        if tipo == "ricarica" and id_utente and importo > 0:
            from utils.db import query as _q
            _q("UPDATE utenti SET crediti = crediti + %s WHERE id=%s",
               (importo, id_utente), commit=True)
            _q("INSERT INTO wallet_transazioni (id_utente, importo, tipo) VALUES (%s,%s,'ricarica')",
               (id_utente, importo), commit=True)
        elif id_ordine:
            query("UPDATE ordini SET stato='in_attesa' WHERE id=%s AND stato='pending_stripe'",
                  (id_ordine,), commit=True)
            # Notifica ristoratore dopo pagamento Stripe
            ordine = query("SELECT id_ristorante FROM ordini WHERE id=%s", (id_ordine,), fetchone=True)
            if ordine:
                notifica_nuovo_ordine(id_ordine, ordine["id_ristorante"])
            if id_utente and importo > 0:
                query("INSERT INTO wallet_transazioni (id_utente, importo, tipo) VALUES (%s,%s,'pagamento')",
                      (id_utente, importo), commit=True)

    return jsonify({"received": True})
