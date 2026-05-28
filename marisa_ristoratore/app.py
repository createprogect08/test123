from flask import Flask, jsonify, request
from flask_cors import CORS
from config import SECRET_KEY, DEBUG, PORT, UPLOAD_FOLDER
from routes.ws import socketio
from routes.me import me_bp
from routes.ordini import ordini_bp
from routes.menu import menu_bp
import os

app = Flask(__name__)
app.config["SECRET_KEY"]         = SECRET_KEY
app.config["UPLOAD_FOLDER"]      = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

CORS(app, resources={r"/*": {"origins": "*"}})

app.register_blueprint(me_bp)
app.register_blueprint(ordini_bp)
app.register_blueprint(menu_bp)

socketio.init_app(app, cors_allowed_origins="*")

@app.route("/interno/nuovo_ordine", methods=["POST"])
def interno_nuovo_ordine():
    d = request.get_json(silent=True) or {}
    id_ordine     = d.get("id_ordine")
    id_ristorante = d.get("id_ristorante")
    if id_ordine and id_ristorante:
        socketio.emit("nuovo_ordine", {
            "ordine": {"id": id_ordine, "id_ristorante": id_ristorante}
        }, room=f"ristorante_{id_ristorante}")
    return jsonify({"ok": True})

@app.route("/interno/ordine_annullato", methods=["POST"])
def interno_ordine_annullato():
    d = request.get_json(silent=True) or {}
    id_ordine     = d.get("id_ordine")
    id_ristorante = d.get("id_ristorante")
    if id_ordine and id_ristorante:
        socketio.emit("ordine_annullato", {
            "id_ordine": id_ordine
        }, room=f"ristorante_{id_ristorante}")
    return jsonify({"ok": True})

@app.route("/health")
def health():
    return jsonify({"app": "Marisa Ristoratore", "version": "1.0.0", "status": "ok", "porta": PORT})

@app.errorhandler(404)
def not_found(e):
    return jsonify({"errore": "Endpoint non trovato"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"errore": "Metodo non consentito"}), 405

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"errore": "Errore interno del server"}), 500

if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    socketio.run(app, host="0.0.0.0", port=PORT, debug=False, allow_unsafe_werkzeug=True)
