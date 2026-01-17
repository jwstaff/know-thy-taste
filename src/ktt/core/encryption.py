"""AES-256 encryption utilities for Know Thy Taste."""

from __future__ import annotations

import os
import base64
import json
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Module-level encryption key (set after authentication)
_encryption_key: bytes | None = None


def generate_salt() -> bytes:
    """Generate a random salt for key derivation."""
    return os.urandom(32)


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive an encryption key from a passphrase and salt using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,  # OWASP 2023 recommendation
    )
    key = kdf.derive(passphrase.encode())
    return base64.urlsafe_b64encode(key)


def set_encryption_key(key: bytes) -> None:
    """Set the module-level encryption key after authentication."""
    global _encryption_key
    _encryption_key = key


def get_encryption_key() -> bytes | None:
    """Get the current encryption key."""
    return _encryption_key


def clear_encryption_key() -> None:
    """Clear the encryption key (for session timeout)."""
    global _encryption_key
    _encryption_key = None


def encrypt_string(plaintext: str) -> bytes:
    """Encrypt a string and return encrypted bytes."""
    if _encryption_key is None:
        raise RuntimeError("Encryption key not set. User must authenticate first.")

    f = Fernet(_encryption_key)
    return f.encrypt(plaintext.encode())


def decrypt_string(ciphertext: bytes) -> str:
    """Decrypt bytes and return the original string."""
    if _encryption_key is None:
        raise RuntimeError("Encryption key not set. User must authenticate first.")

    f = Fernet(_encryption_key)
    return f.decrypt(ciphertext).decode()


def encrypt_json(data: Any) -> bytes:
    """Encrypt a JSON-serializable object and return encrypted bytes."""
    json_str = json.dumps(data)
    return encrypt_string(json_str)


def decrypt_json(ciphertext: bytes) -> Any:
    """Decrypt bytes and return the original JSON object."""
    json_str = decrypt_string(ciphertext)
    return json.loads(json_str)


def encrypt_response(text: str) -> bytes:
    """Encrypt a response text. Convenience wrapper with clear naming."""
    return encrypt_string(text)


def decrypt_response(ciphertext: bytes) -> str:
    """Decrypt a response text. Convenience wrapper with clear naming."""
    return decrypt_string(ciphertext)
