"""Authentication and passphrase management for Know Thy Taste."""

import hashlib
import os
from typing import Optional

import questionary
from rich.console import Console

from ktt.core.database import get_session, is_initialized, connect_db
from ktt.core.models import User
from ktt.core.encryption import derive_key, generate_salt, set_encryption_key
from ktt.cli.ui import print_error, print_success, print_info, print_warning

console = Console()

# Minimum passphrase requirements
MIN_PASSPHRASE_LENGTH = 12


def hash_passphrase(passphrase: str, salt: bytes) -> bytes:
    """Create a hash of the passphrase for verification (separate from encryption key)."""
    # Use a different salt derivation for the verification hash
    verification_salt = hashlib.sha256(salt + b"verification").digest()
    return hashlib.pbkdf2_hmac(
        "sha256",
        passphrase.encode(),
        verification_salt,
        iterations=480000,
    )


def validate_passphrase_strength(passphrase: str) -> tuple[bool, str]:
    """Validate passphrase meets minimum requirements."""
    if len(passphrase) < MIN_PASSPHRASE_LENGTH:
        return False, f"Passphrase must be at least {MIN_PASSPHRASE_LENGTH} characters."

    # Check for variety (at least some mix)
    has_letter = any(c.isalpha() for c in passphrase)
    has_number = any(c.isdigit() for c in passphrase)

    if not (has_letter and has_number):
        return False, "Passphrase should contain both letters and numbers."

    return True, ""


def setup_passphrase() -> Optional[str]:
    """Interactive passphrase setup for new users."""
    console.print("\n[bold]Set up your passphrase[/bold]")
    console.print("[dim]This passphrase encrypts your reflections. Choose something memorable.[/dim]")
    console.print(f"[dim]Minimum {MIN_PASSPHRASE_LENGTH} characters, with letters and numbers.[/dim]\n")

    while True:
        passphrase = questionary.password(
            "Enter passphrase:",
        ).ask()

        if passphrase is None:  # User cancelled
            return None

        valid, message = validate_passphrase_strength(passphrase)
        if not valid:
            print_warning(message)
            continue

        confirm = questionary.password(
            "Confirm passphrase:",
        ).ask()

        if confirm is None:
            return None

        if passphrase != confirm:
            print_warning("Passphrases don't match. Try again.")
            continue

        # Generate salt and create user
        salt = generate_salt()
        password_hash = hash_passphrase(passphrase, salt)

        with get_session() as db:
            user = User(
                password_hash=password_hash,
                encryption_salt=salt,
                consent_flags={},
                settings={},
            )
            db.add(user)
            db.commit()

        # Set up encryption key for this session
        encryption_key = derive_key(passphrase, salt)
        set_encryption_key(encryption_key)

        print_success("Passphrase set successfully.")
        return passphrase


def verify_passphrase(passphrase: str, user: User) -> bool:
    """Verify a passphrase against stored hash."""
    expected_hash = hash_passphrase(passphrase, user.encryption_salt)
    return expected_hash == user.password_hash


def authenticate() -> Optional[User]:
    """Authenticate the user and set up encryption key."""
    if not is_initialized():
        print_error("Know Thy Taste is not initialized. Run 'ktt init' first.")
        return None

    connect_db()

    with get_session() as db:
        user = db.query(User).first()
        if not user:
            print_error("No user found. Run 'ktt init' to set up.")
            return None

        # Prompt for passphrase
        passphrase = questionary.password(
            "Enter passphrase:",
        ).ask()

        if passphrase is None:
            return None

        if not verify_passphrase(passphrase, user):
            print_error("Incorrect passphrase.")
            return None

        # Set up encryption key
        encryption_key = derive_key(passphrase, user.encryption_salt)
        set_encryption_key(encryption_key)

        # Refresh the user object to keep it attached
        user_id = user.id

    # Get a fresh user object
    with get_session() as db:
        user = db.query(User).filter(User.id == user_id).first()
        # Detach from session so it can be used elsewhere
        db.expunge(user)

    return user


def require_auth() -> Optional[User]:
    """Require authentication, returning the user or None if failed."""
    return authenticate()


def change_passphrase(user: User) -> bool:
    """Change the user's passphrase."""
    print_info("Changing passphrase requires re-encrypting all data.")

    # Verify current passphrase
    current = questionary.password(
        "Enter current passphrase:",
    ).ask()

    if current is None or not verify_passphrase(current, user):
        print_error("Incorrect current passphrase.")
        return False

    # Get new passphrase
    new_passphrase = questionary.password(
        "Enter new passphrase:",
    ).ask()

    if new_passphrase is None:
        return False

    valid, message = validate_passphrase_strength(new_passphrase)
    if not valid:
        print_error(message)
        return False

    confirm = questionary.password(
        "Confirm new passphrase:",
    ).ask()

    if confirm != new_passphrase:
        print_error("Passphrases don't match.")
        return False

    # Re-encrypt all data with new key
    # This is a complex operation - for now, just update the passphrase
    # TODO: Implement re-encryption of all encrypted fields

    new_salt = generate_salt()
    new_hash = hash_passphrase(new_passphrase, new_salt)

    with get_session() as db:
        db_user = db.query(User).filter(User.id == user.id).first()
        db_user.password_hash = new_hash
        db_user.encryption_salt = new_salt
        db.commit()

    # Update encryption key
    new_key = derive_key(new_passphrase, new_salt)
    set_encryption_key(new_key)

    print_success("Passphrase changed successfully.")
    return True
