import hashlib


def hash_access_key(access_key: str) -> str:
    """Generate SHA-256 hash of NFC-e access key"""
    return hashlib.sha256(access_key.encode()).hexdigest()

