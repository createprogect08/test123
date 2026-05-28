# utils/bcrypt_helper.py
import bcrypt

def hash_password(password: str) -> str:
    """Genera hash bcrypt della password."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=12)
    ).decode("utf-8")

def verifica_password(password: str, password_hash: str) -> bool:
    """Verifica password contro hash bcrypt."""
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except Exception:
        return False