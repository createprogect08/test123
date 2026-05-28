import requests
from flask_socketio import SocketIO, emit, join_room, leave_room
from config import AUTH_BACKEND

socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading",
    ping_timeout=60,
    ping_interval=25,
    manage_session=False,
    logger=True,
    engineio_logger=True
)


def verifica_token_ws(token):
    try:
        r = requests.get(
            f"{AUTH_BACKEND}/auth/verify",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if r.status_code == 200:
            dati = r.json()
            if dati.get("valido"):
                return dati.get("utente")
    except requests.exceptions.ConnectionError:
        pass
    return None


@socketio.on("connect")
def on_connect():
    from flask import request as freq
    print("=== WS CONNECT ===", flush=True)
    token = freq.args.get("token")
    id_ristorante = freq.args.get("id_ristorante")
    print(f"token presente: {bool(token)}, id_ristorante: {id_ristorante}", flush=True)

    if not token:
        print("RIFIUTATO: token mancante", flush=True)
        return False

    utente = verifica_token_ws(token)
    if not utente:
        print("RIFIUTATO: token non valido", flush=True)
        return False

    if utente.get("tipo") != "ristoratore":
        print("RIFIUTATO: non ristoratore", flush=True)
        return False

    if id_ristorante:
        join_room(f"ristorante_{id_ristorante}")
        emit("connesso", {
            "messaggio": f"Connesso alla room ristorante_{id_ristorante}",
            "utente": utente.get("nome")
        })
        print(f"OK - JOIN room ristorante_{id_ristorante}", flush=True)


@socketio.on("disconnect")
def on_disconnect():
    print("=== WS DISCONNECT ===", flush=True)


@socketio.on("join_ristorante")
def on_join(data):
    id_ristorante = data.get("id_ristorante")
    if id_ristorante:
        join_room(f"ristorante_{id_ristorante}")
        emit("connesso", {"messaggio": f"Room ristorante_{id_ristorante} joined"})


@socketio.on("leave_ristorante")
def on_leave(data):
    id_ristorante = data.get("id_ristorante")
    if id_ristorante:
        leave_room(f"ristorante_{id_ristorante}")


def notifica_nuovo_ordine(id_ristorante, ordine):
    socketio.emit("nuovo_ordine", {
        "id_ristorante": id_ristorante,
        "ordine": ordine
    }, room=f"ristorante_{id_ristorante}")
