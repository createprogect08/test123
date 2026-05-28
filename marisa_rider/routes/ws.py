import requests
from flask_socketio import SocketIO, emit, join_room, leave_room
from config import AUTH_BACKEND

socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")


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
    token = freq.args.get("token") or \
            freq.headers.get("Authorization", "").replace("Bearer ", "") or None

    if not token:
        return False

    utente = verifica_token_ws(token)
    if not utente:
        return False

    # Rider entra nella sua room personale
    if utente.get("tipo") == "rider":
        join_room(f"rider_{utente['id']}")
        emit("connesso", {
            "messaggio": f"Connesso come rider_{utente['id']}",
            "utente"   : utente.get("nome")
        })
    # Cliente entra nella sua room per ricevere aggiornamenti
    elif utente.get("tipo") == "utente":
        join_room(f"cliente_{utente['id']}")
        emit("connesso", {
            "messaggio": f"Connesso come cliente_{utente['id']}",
            "utente"   : utente.get("nome")
        })
    else:
        return False


@socketio.on("disconnect")
def on_disconnect():
    pass


@socketio.on("join_ordine")
def on_join_ordine(data):
    """Permette al cliente di seguire un ordine specifico."""
    id_ordine = data.get("id_ordine")
    if id_ordine:
        join_room(f"ordine_{id_ordine}")
        emit("connesso", {"messaggio": f"Tracciamento ordine_{id_ordine} attivo"})


@socketio.on("leave_ordine")
def on_leave_ordine(data):
    id_ordine = data.get("id_ordine")
    if id_ordine:
        leave_room(f"ordine_{id_ordine}")


def notifica_nuova_consegna(id_rider, ordine):
    """Notifica un rider di una nuova richiesta di consegna."""
    socketio.emit("nuova_consegna", {
        "id_rider": id_rider,
        "ordine"  : ordine
    }, room=f"rider_{id_rider}")
