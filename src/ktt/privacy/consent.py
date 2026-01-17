"""Consent management for Know Thy Taste."""

from datetime import datetime
from typing import Optional

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box

from ktt.cli.ui import print_success, print_warning, print_info, print_header
from ktt.core.database import get_session
from ktt.core.models import User

console = Console()

# Consent types with descriptions
CONSENT_TYPES = {
    "store_movie_titles": {
        "name": "Store Movie Titles",
        "description": "Store the titles and basic metadata of movies you analyze.",
        "required": True,  # Can't function without this
    },
    "store_reflections": {
        "name": "Store Written Reflections",
        "description": "Store your written responses to questions (encrypted).",
        "required": True,
    },
    "store_temporal_data": {
        "name": "Store Temporal Data",
        "description": "Store when you watched movies and when you wrote reflections.",
        "required": False,
    },
    "enable_pattern_analysis": {
        "name": "Enable Pattern Analysis",
        "description": "Analyze your responses to detect patterns in your taste.",
        "required": False,
    },
    "enable_export": {
        "name": "Enable Data Export",
        "description": "Allow exporting your data as JSON or Markdown.",
        "required": False,
    },
}

PRIVACY_POLICY = """
# Know Thy Taste Privacy Policy

## What We Store
- **Movie titles and metadata**: The films you analyze and their basic info
- **Your reflections**: Your written responses to questions (encrypted with your passphrase)
- **Detected patterns**: Insights about your taste derived from your responses
- **Session data**: When you use the app (if you consent)

## What We DON'T Store or Collect
- No IP addresses or device identifiers
- No location data
- No usage telemetry (unless you explicitly opt in)
- No data is ever sent to external servers
- Your data never leaves your machine

## Encryption
All sensitive data (your written reflections) is encrypted using AES-256 encryption.
The encryption key is derived from your passphrase—we never store your passphrase.

## Your Rights
- **Access**: Export all your data at any time
- **Deletion**: Delete all your data with one command
- **Portability**: Export in standard formats (JSON, Markdown)
- **Withdraw consent**: Change your consent choices at any time

## Data Security
- All data stored locally on your machine
- Sensitive text encrypted at rest
- No cloud sync (your data stays with you)
- No third-party access ever

## Important Note
This app may prompt you with questions that elicit personal reflections.
You control what you share—feel free to be as private or open as you like.
"""


def display_privacy_policy() -> None:
    """Display the privacy policy."""
    console.print(Panel(
        Markdown(PRIVACY_POLICY),
        title="[bold]Privacy Policy[/bold]",
        box=box.DOUBLE,
        expand=True,
    ))


def run_initial_consent() -> bool:
    """Run the initial consent flow. Returns True if consent is given."""
    display_privacy_policy()

    console.print()
    accept = questionary.confirm(
        "Do you accept this privacy policy?",
        default=True,
    ).ask()

    if not accept:
        return False

    console.print()
    print_header("Data Consent Choices")
    console.print("[dim]Choose what data to store. Required items are pre-selected.[/dim]\n")

    consent_flags = {}

    for key, info in CONSENT_TYPES.items():
        if info["required"]:
            console.print(f"[green]✓[/green] {info['name']} [dim](required)[/dim]")
            console.print(f"  [dim]{info['description']}[/dim]")
            consent_flags[key] = True
        else:
            choice = questionary.confirm(
                f"{info['name']}?\n  {info['description']}",
                default=True,
            ).ask()

            if choice is None:  # User cancelled
                return False

            consent_flags[key] = choice

        console.print()

    # Store consent flags (will be saved to user after passphrase setup)
    # For now, store temporarily
    import ktt.privacy.consent as consent_module
    consent_module._pending_consent = consent_flags

    print_success("Consent preferences saved.")
    return True


def apply_pending_consent(user_id: str) -> None:
    """Apply pending consent flags to a user."""
    import ktt.privacy.consent as consent_module

    pending = getattr(consent_module, "_pending_consent", None)
    if not pending:
        return

    with get_session() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.consent_flags = pending
            user.last_privacy_review = datetime.utcnow()
            db.commit()

    consent_module._pending_consent = None


def show_consent_status(user: User) -> None:
    """Show current consent status."""
    print_header("Privacy Settings")

    with get_session() as db:
        db_user = db.query(User).filter(User.id == user.id).first()
        flags = db_user.consent_flags or {}
        last_review = db_user.last_privacy_review

    console.print("[bold]Current Consent Choices:[/bold]\n")

    for key, info in CONSENT_TYPES.items():
        status = flags.get(key, False)
        status_icon = "[green]✓[/green]" if status else "[red]✗[/red]"
        required_note = " [dim](required)[/dim]" if info["required"] else ""

        console.print(f"{status_icon} {info['name']}{required_note}")
        console.print(f"  [dim]{info['description']}[/dim]")
        console.print()

    if last_review:
        console.print(f"[dim]Last reviewed: {last_review.strftime('%Y-%m-%d')}[/dim]")

    console.print()
    print_info("Use 'ktt privacy withdraw <consent-type>' to change a consent.")
    print_info("Use 'ktt privacy delete-all' to delete all data.")


def withdraw_consent(user: User, consent_type: str) -> bool:
    """Withdraw a specific consent."""
    if consent_type not in CONSENT_TYPES:
        console.print(f"[red]Unknown consent type: {consent_type}[/red]")
        console.print("[dim]Available types:[/dim]")
        for key in CONSENT_TYPES:
            console.print(f"  - {key}")
        return False

    info = CONSENT_TYPES[consent_type]

    if info["required"]:
        print_warning(f"'{consent_type}' is required for the app to function.")
        print_info("To stop using the app, use 'ktt privacy delete-all'.")
        return False

    with get_session() as db:
        db_user = db.query(User).filter(User.id == user.id).first()
        flags = db_user.consent_flags or {}

        if not flags.get(consent_type, False):
            print_info(f"'{consent_type}' is already withdrawn.")
            return True

        # Confirm withdrawal
        console.print(f"\n[bold]Withdrawing consent: {info['name']}[/bold]")
        console.print(f"[dim]{info['description']}[/dim]\n")

        if consent_type == "enable_pattern_analysis":
            print_warning("This will delete all detected patterns.")
        elif consent_type == "store_temporal_data":
            print_warning("This will remove timestamps from your data.")

        if not questionary.confirm("Proceed with withdrawal?").ask():
            print_info("Withdrawal cancelled.")
            return False

        # Update consent
        flags[consent_type] = False
        db_user.consent_flags = flags
        db.commit()

        # Clean up associated data if needed
        if consent_type == "enable_pattern_analysis":
            from ktt.core.models import Pattern
            db.query(Pattern).filter(Pattern.user_id == user.id).delete()
            db.commit()

    print_success(f"Consent for '{consent_type}' has been withdrawn.")
    return True


def has_consent(user: User, consent_type: str) -> bool:
    """Check if user has given consent for a specific type."""
    with get_session() as db:
        db_user = db.query(User).filter(User.id == user.id).first()
        flags = db_user.consent_flags or {}
        return flags.get(consent_type, False)
