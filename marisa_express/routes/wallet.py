# routes/wallet.py
from flask import Blueprint, request, jsonify
from utils.db import query
from utils.auth import token_required

wallet_bp = Blueprint("wallet", __name__, url_prefix="/api/wallet")

# ── GET /api/wallet/saldo ─────────────────────────────────────────────────────
@wallet_bp.route("/saldo", methods=["GET"])
@token_required
def saldo():
    utente = query(
        "SELECT crediti FROM utenti WHERE id=%s",
        (request.utente_id,), fetchone=True
    )
    if not utente:
        return jsonify({"errore": "Utente non trovato"}), 404
    return jsonify({"saldo": float(utente["crediti"])})


# ── POST /api/wallet/ricarica ─────────────────────────────────────────────────
@wallet_bp.route("/ricarica", methods=["POST"])
@token_required
def ricarica():
    d = request.get_json(silent=True) or {}
    try:
        importo = float(d.get("importo", 0))
    except (TypeError, ValueError):
        return jsonify({"errore": "Importo non valido"}), 400

    if importo <= 0:
        return jsonify({"errore": "L'importo deve essere maggiore di zero"}), 400
    if importo > 500:
        return jsonify({"errore": "Importo massimo per ricarica: €500"}), 400

    # Aggiorna crediti
    query(
        "UPDATE utenti SET crediti = crediti + %s WHERE id=%s",
        (importo, request.utente_id), commit=True
    )

    # Registra transazione
    query(
        "INSERT INTO wallet_transazioni (id_utente, importo, tipo) "
        "VALUES (%s, %s, 'ricarica')",
        (request.utente_id, importo), commit=True
    )

    # Restituisce nuovo saldo
    utente = query(
        "SELECT crediti FROM utenti WHERE id=%s",
        (request.utente_id,), fetchone=True
    )
    return jsonify({
        "messaggio" : "Ricarica effettuata",
        "importo"   : importo,
        "nuovo_saldo": float(utente["crediti"])
    }), 201


# ── GET /api/wallet/transazioni ───────────────────────────────────────────────
@wallet_bp.route("/transazioni", methods=["GET"])
@token_required
def lista_transazioni():
    # Paginazione opzionale
    try:
        pagina = int(request.args.get("pagina", 1))
        per_pagina = int(request.args.get("per_pagina", 20))
    except ValueError:
        return jsonify({"errore": "Parametri di paginazione non validi"}), 400

    if pagina < 1 or per_pagina < 1 or per_pagina > 100:
        return jsonify({"errore": "Parametri di paginazione fuori range"}), 400

    offset = (pagina - 1) * per_pagina

    # Totale record
    totale = query(
        "SELECT COUNT(*) AS tot FROM wallet_transazioni WHERE id_utente=%s",
        (request.utente_id,), fetchone=True
    )["tot"]

    transazioni = query(
        "SELECT id, importo, tipo, created_at FROM wallet_transazioni "
        "WHERE id_utente=%s ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (request.utente_id, per_pagina, offset)
    )
    for t in transazioni:
        t["importo"] = float(t["importo"])

    return jsonify({
        "transazioni" : transazioni,
        "pagina"      : pagina,
        "per_pagina"  : per_pagina,
        "totale"      : totale,
        "pagine_totali": -(-totale // per_pagina)  # ceiling division
    })


# ── GET /api/wallet/transazioni/<id> ─────────────────────────────────────────
@wallet_bp.route("/transazioni/<int:tid>", methods=["GET"])
@token_required
def get_transazione(tid):
    transazione = query(
        "SELECT * FROM wallet_transazioni WHERE id=%s AND id_utente=%s",
        (tid, request.utente_id), fetchone=True
    )
    if not transazione:
        return jsonify({"errore": "Transazione non trovata"}), 404
    transazione["importo"] = float(transazione["importo"])
    return jsonify(transazione)

# ── POST /api/wallet/ricarica-stripe ─────────────────────────────────────────
@wallet_bp.route("/ricarica-stripe", methods=["POST"])
@token_required
def ricarica_stripe():
    import stripe, os
    d = request.get_json(silent=True) or {}
    try:
        importo = float(d.get("importo", 0))
    except (TypeError, ValueError):
        return jsonify({"errore": "Importo non valido"}), 400

    if importo < 1 or importo > 500:
        return jsonify({"errore": "Importo tra €1 e €500"}), 400

    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not stripe.api_key or "INSERISCI" in stripe.api_key:
        return jsonify({"errore": "Stripe non configurato"}), 500

    # Salva importo e utente pendente in DB
    id_utente = request.utente_id
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": f"Ricarica Wallet Marisa Express €{importo:.2f}"},
                    "unit_amount": int(importo * 100),
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="https://reimagined-orbit-r44jxj94649qhpv6-3000.app.github.dev/wallet?ricarica=ok&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=f"https://reimagined-orbit-r44jxj94649qhpv6-3000.app.github.dev/wallet?ricarica=cancel",
            metadata={"id_utente": str(id_utente), "importo": str(importo), "tipo": "ricarica"}
        )
    except Exception as e:
        return jsonify({"errore": f"Errore Stripe: {str(e)}"}), 500

    return jsonify({"stripe_url": session.url}), 201


# ── POST /api/wallet/verifica-ricarica ───────────────────────────────────────
@wallet_bp.route("/verifica-ricarica", methods=["POST"])
@token_required
def verifica_ricarica():
    import stripe, os
    d = request.get_json(silent=True) or {}
    session_id = d.get("session_id")
    if not session_id:
        return jsonify({"errore": "session_id mancante"}), 400

    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        return jsonify({"errore": str(e)}), 500

    if session.payment_status != "paid":
        return jsonify({"errore": "Pagamento non completato"}), 400

    raw = session.metadata
    meta = raw.to_dict() if raw else {}
    if meta.get("tipo") != "ricarica":
        return jsonify({"errore": "Sessione non valida"}), 400

    id_utente = request.utente_id
    importo = float(meta.get("importo", 0))

    # Controlla se già processato
    già = query("SELECT id FROM wallet_transazioni WHERE id_utente=%s AND tipo='ricarica' AND stripe_session_id=%s",
                (id_utente, session_id), fetchone=True)
    if già:
        saldo = query("SELECT crediti FROM utenti WHERE id=%s", (id_utente,), fetchone=True)
        return jsonify({"messaggio": "Già processato", "saldo": float(saldo["crediti"])}), 200

    # Accredita
    query("UPDATE utenti SET crediti = crediti + %s WHERE id=%s", (importo, id_utente), commit=True)
    query("INSERT INTO wallet_transazioni (id_utente, importo, tipo, stripe_session_id) VALUES (%s,%s,'ricarica',%s)",
          (id_utente, importo, session_id), commit=True)

    saldo = query("SELECT crediti FROM utenti WHERE id=%s", (id_utente,), fetchone=True)
    return jsonify({"messaggio": "Ricarica completata", "saldo": float(saldo["crediti"])}), 200
