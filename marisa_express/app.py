# app.py
import logging
from flask import Flask, jsonify, send_from_directory
import os
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from config import Config
from routes.utenti import utenti_bp, bcrypt as utenti_bcrypt
from routes.ristoranti import ristoranti_bp
from routes.menu_items import menu_bp
from routes.ordini import ordini_bp
from routes.wallet import wallet_bp
from routes.rider_posizioni import rider_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, origins=["https://reimagined-orbit-r44jxj94649qhpv6-3000.app.github.dev", "https://reimagined-orbit-r44jxj94649qhpv6-3001.app.github.dev", "https://reimagined-orbit-r44jxj94649qhpv6-3002.app.github.dev"], methods=["GET","POST","PUT","DELETE","OPTIONS"], allow_headers=["Content-Type","Authorization"])

    # ── Bcrypt ────────────────────────────────────────────────────────────────
    utenti_bcrypt.init_app(app)

    # ── Blueprint registration ────────────────────────────────────────────────
    app.register_blueprint(utenti_bp)
    app.register_blueprint(ristoranti_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(ordini_bp)
    app.register_blueprint(wallet_bp)
    app.register_blueprint(rider_bp)

    # ── Error handlers ────────────────────────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"errore": "Richiesta non valida", "dettaglio": str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"errore": "Non autenticato"}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"errore": "Accesso negato"}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"errore": "Risorsa non trovata"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"errore": "Metodo non consentito"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        logging.exception("Errore interno: %s", e)
        return jsonify({"errore": "Errore interno del server"}), 500

    # ── Health check ──────────────────────────────────────────────────────────
    @app.route("/api/health", methods=["GET"])
    def health():
        from utils.db import query
        try:
            query("SELECT 1", fetchone=True)
            db_status = "ok"
        except Exception as e:
            db_status = f"errore: {str(e)}"
        return jsonify({
            "status" : "ok",
            "app"    : "Marisa Express",
            "version": "1.0.0",
            "db"     : db_status
        })

    # ── Riepilogo route ───────────────────────────────────────────────────────
    @app.route("/api/routes", methods=["GET"])
    def lista_route():
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != "static":
                routes.append({
                    "endpoint": rule.endpoint,
                    "metodi"  : sorted([m for m in rule.methods if m not in ("HEAD","OPTIONS")]),
                    "path"    : str(rule)
                })
        return jsonify(sorted(routes, key=lambda x: x["path"]))

    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    @app.route("/static/uploads/<path:filename>")
    def serve_upload(filename):
        return send_from_directory(UPLOAD_FOLDER, filename)

    return app


if __name__ == "__main__":
    app = create_app()
    logging.basicConfig(level=logging.INFO)
    app.run(
        debug=Config.DEBUG,
        host="0.0.0.0",
        port=5000
    )

