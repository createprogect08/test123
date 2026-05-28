import os

# ── Porte servizi ─────────────────────────────────────────────────────────────
MAIN_BACKEND  = os.getenv("MAIN_BACKEND",  "http://marisa-express:5000")
AUTH_BACKEND  = os.getenv("AUTH_BACKEND",  "http://marisa-auth:5001")
PORT          = int(os.getenv("PORT", 5002))
DEBUG         = os.getenv("DEBUG", "false").lower() == "true"

# ── Database ──────────────────────────────────────────────────────────────────
DB_HOST = os.getenv("DB_HOST", "mysql")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "marisa2")
DB_PASS = os.getenv("DB_PASSWORD", os.getenv("DB_PASS", "MarisaExpress2025!"))
DB_NAME = os.getenv("DB_NAME", "marisa_express_db")

# ── Upload foto ───────────────────────────────────────────────────────────────
UPLOAD_FOLDER      = os.path.join(os.path.dirname(__file__), "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB

# ── Secret key Flask ──────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "marisa-secret-key-cambiami-in-produzione")
