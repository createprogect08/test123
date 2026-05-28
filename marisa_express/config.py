# config.py
import os

class Config:
    # --- Database ---
    DB_HOST     = os.getenv("DB_HOST", "localhost")
    DB_PORT     = int(os.getenv("DB_PORT", 3306))
    DB_USER     = os.getenv("DB_USER", "marisa")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "MarisaExpress2024")
    DB_NAME     = os.getenv("DB_NAME", "marisa_express_db")

    # --- Flask ---
    SECRET_KEY  = os.getenv("SECRET_KEY", "marisa-secret-key-cambiami-in-produzione")
    DEBUG       = os.getenv("DEBUG", "true").lower() == "true"

    # --- JWT ---
    JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", 24))
