from flask import Flask, jsonify
from flask_cors import CORS
from flask_cors import CORS
from config import SECRET_KEY, DEBUG, PORT
from utils.db import query
from routes.auth import auth_bp

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

CORS(app, resources={r"/auth/*": {"origins": "*"}})

app.register_blueprint(auth_bp)

@app.route("/health")
def health():
    try:
        query("SELECT 1", fetchone=True)
        db_status = "ok"
    except Exception:
        db_status = "error"

    return jsonify({
        "app"    : "Marisa Auth",
        "version": "1.0.0",
        "status" : "ok" if db_status == "ok" else "degraded",
        "db"     : db_status
    }), 200 if db_status == "ok" else 503

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
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
