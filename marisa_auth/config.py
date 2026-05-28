# config.py
import os

class Config:
    # --- Database (stesso del main backend) ---
    DB_HOST     = os.getenv("DB_HOST", "localhost")
    DB_PORT     = int(os.getenv("DB_PORT", 3306))
    DB_USER     = os.getenv("DB_USER", "marisa")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "MarisaExpress2024")
    DB_NAME     = os.getenv("DB_NAME", "marisa_express_db")

    # --- Flask ---
    SECRET_KEY = os.getenv("SECRET_KEY", "marisa-secret-key-cambiami-in-produzione")
    DEBUG       = os.getenv("DEBUG", "true").lower() == "true"

    # --- JWT ---
    JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", 24))

    # --- Main backend ---
    MAIN_BACKEND_URL = os.getenv("MAIN_BACKEND_URL", "http://localhost:5000")

    # --- Redirect URLs per tipo utente ---
    REDIRECT_UTENTE      = os.getenv("REDIRECT_UTENTE",      "https://reimagined-orbit-r44jxj94649qhpv6-3000.app.github.dev")
    REDIRECT_RISTORATORE = os.getenv("REDIRECT_RISTORATORE", "https://reimagined-orbit-r44jxj94649qhpv6-3002.app.github.dev")
    REDIRECT_RIDER       = os.getenv("REDIRECT_RIDER",       "https://reimagined-orbit-r44jxj94649qhpv6-3003.app.github.dev")
# Alias per import diretti
SECRET_KEY   = Config.SECRET_KEY
DEBUG        = Config.DEBUG
PORT         = int(os.getenv("PORT", 5001))
