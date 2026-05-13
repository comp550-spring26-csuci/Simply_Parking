import hashlib


def hash_password(password: str) -> str:
    """Simple deterministic hash used by the class project login system."""
    return hashlib.sha256((password or '').encode('utf-8')).hexdigest()
