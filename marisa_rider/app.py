import eventlet
eventlet.monkey_patch()

from flask import Flask, jsonify
from flask_cors import CORS
from flask_cors import CORS

from config import SECRET_KEY, DEBUG, PORT, UPLOAD_FOLDER
from routes.ws import socketio
from routes.me import me_bp
from routes.ordini import ordini_bp
from routes.posizione import posizione_bp

import os

app = Flask(__name__)
app.config["SECRET_KEY"]         = SECRET_KEY
app.config["UPLOAD_FOLDER"]      = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

CORS(app, resources={r"/*": {"origins": "*"}})

app.register_blueprint(me_bp)
app.register_blueprint(ordini_bp)
app.register_blueprint(posizione_bp)

socketio.init_app(app)

@app.route("/health")
def health():
    return jsonify({
        "app"    : "Marisa Rider",
        "version": "1.0.0",
        "status" : "ok",
        "porta"  : PORT
    })

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
    socketio.run(app, host="0.0.0.0", port=PORT, debug=DEBUG)
