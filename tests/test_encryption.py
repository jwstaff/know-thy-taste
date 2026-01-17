"""Tests for encryption utilities."""

import pytest

from ktt.core.encryption import (
    generate_salt,
    derive_key,
    encrypt_string,
    decrypt_string,
    encrypt_json,
    decrypt_json,
    set_encryption_key,
    clear_encryption_key,
)


class TestEncryption:
    """Tests for encryption utilities."""

    @pytest.fixture(autouse=True)
    def setup_encryption(self):
        """Set up encryption key for tests."""
        salt = generate_salt()
        key = derive_key("test_passphrase_123", salt)
        set_encryption_key(key)
        yield
        clear_encryption_key()

    def test_salt_generation(self):
        """Salt should be unique and correct length."""
        salt1 = generate_salt()
        salt2 = generate_salt()
        assert len(salt1) == 32
        assert salt1 != salt2

    def test_key_derivation_deterministic(self):
        """Same passphrase + salt should produce same key."""
        salt = generate_salt()
        key1 = derive_key("test_passphrase", salt)
        key2 = derive_key("test_passphrase", salt)
        assert key1 == key2

    def test_key_derivation_different_salts(self):
        """Different salts should produce different keys."""
        salt1 = generate_salt()
        salt2 = generate_salt()
        key1 = derive_key("test_passphrase", salt1)
        key2 = derive_key("test_passphrase", salt2)
        assert key1 != key2

    def test_string_encryption_roundtrip(self):
        """Encrypting and decrypting should return original string."""
        original = "This is a test reflection about a movie."
        encrypted = encrypt_string(original)
        decrypted = decrypt_string(encrypted)
        assert decrypted == original
        assert encrypted != original.encode()

    def test_json_encryption_roundtrip(self):
        """Encrypting and decrypting JSON should return original data."""
        original = {
            "movie": "Blade Runner",
            "rating": 5,
            "themes": ["identity", "humanity"],
        }
        encrypted = encrypt_json(original)
        decrypted = decrypt_json(encrypted)
        assert decrypted == original

    def test_encryption_requires_key(self):
        """Encryption should fail without a key set."""
        clear_encryption_key()
        with pytest.raises(RuntimeError):
            encrypt_string("test")

    def test_decryption_requires_key(self):
        """Decryption should fail without a key set."""
        # First encrypt with key
        salt = generate_salt()
        key = derive_key("test", salt)
        set_encryption_key(key)
        encrypted = encrypt_string("test")

        # Then try to decrypt without key
        clear_encryption_key()
        with pytest.raises(RuntimeError):
            decrypt_string(encrypted)
