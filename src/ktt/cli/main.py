"""Main CLI entry point for Know Thy Taste."""

import typer
from typing import Optional
from pathlib import Path

from ktt.cli.ui import (
    console,
    print_welcome,
    print_success,
    print_error,
    print_info,
    print_warning,
    print_header,
    create_movie_table,
)

app = typer.Typer(
    name="ktt",
    help="Know Thy Taste - Discover why you love the movies you love.",
    no_args_is_help=True,
)

# Sub-command groups
session_app = typer.Typer(help="Manage discovery sessions")
movies_app = typer.Typer(help="Manage your movie collection")
patterns_app = typer.Typer(help="View and validate detected patterns")
privacy_app = typer.Typer(help="Privacy controls and data management")

app.add_typer(session_app, name="session")
app.add_typer(movies_app, name="movies")
app.add_typer(patterns_app, name="patterns")
app.add_typer(privacy_app, name="privacy")


@app.command()
def init() -> None:
    """Initialize Know Thy Taste for first-time use."""
    from ktt.core.database import get_data_dir, init_db, get_session as get_db_session
    from ktt.privacy.consent import run_initial_consent, apply_pending_consent
    from ktt.core.auth import setup_passphrase
    from ktt.core.models import User

    print_welcome()
    print_header("First-Time Setup")

    # Check if already initialized
    data_dir = get_data_dir()
    if (data_dir / "ktt.db").exists():
        print_info("Know Thy Taste is already initialized.")
        if not typer.confirm("Do you want to reset and start fresh?"):
            raise typer.Exit()
        # Delete existing data
        import shutil
        shutil.rmtree(data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)

    # Run consent flow
    consent_given = run_initial_consent()
    if not consent_given:
        print_error("Setup cancelled. You must accept the privacy policy to continue.")
        raise typer.Exit(1)

    # Setup passphrase (this creates the user and initializes the DB)
    passphrase = setup_passphrase()
    if not passphrase:
        print_error("Setup cancelled.")
        raise typer.Exit(1)

    # Apply pending consent to the user
    with get_db_session() as db:
        user = db.query(User).first()
        if user:
            apply_pending_consent(user.id)

    print_success("Know Thy Taste is ready!")
    print_info("Run 'ktt session start' to begin your first discovery session.")


@app.command()
def profile() -> None:
    """View your taste profile summary."""
    from ktt.core.auth import require_auth
    from ktt.core.database import get_session as get_db_session
    from ktt.core.models import Movie, Pattern, Response
    from rich.panel import Panel
    from rich import box

    user = require_auth()
    if not user:
        raise typer.Exit(1)

    with get_db_session() as db:
        movie_count = db.query(Movie).filter(Movie.user_id == user.id).count()
        response_count = db.query(Response).join(Movie).filter(Movie.user_id == user.id).count()
        pattern_count = db.query(Pattern).filter(Pattern.user_id == user.id).count()
        validated_patterns = db.query(Pattern).filter(
            Pattern.user_id == user.id,
            Pattern.validated_by_user == True
        ).count()

    print_header("Your Taste Profile")

    console.print(Panel(
        f"[cyan]Movies analyzed:[/cyan] {movie_count}\n"
        f"[cyan]Reflections captured:[/cyan] {response_count}\n"
        f"[cyan]Patterns detected:[/cyan] {pattern_count}\n"
        f"[cyan]Patterns validated:[/cyan] {validated_patterns}",
        title="Statistics",
        box=box.ROUNDED,
    ))

    if pattern_count == 0:
        print_info("Complete a few sessions to start detecting patterns in your taste.")
    else:
        print_info("Run 'ktt patterns show' to explore your detected patterns.")


@app.command()
def export(
    format: str = typer.Option("json", "--format", "-f", help="Export format: json or markdown"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Export your data."""
    from ktt.core.auth import require_auth
    from ktt.privacy.export import export_data

    user = require_auth()
    if not user:
        raise typer.Exit(1)

    if format not in ["json", "markdown", "md"]:
        print_error(f"Unknown format: {format}. Use 'json' or 'markdown'.")
        raise typer.Exit(1)

    fmt = "markdown" if format == "md" else format
    result_path = export_data(user, fmt, output)
    print_success(f"Data exported to: {result_path}")


# Session commands
@session_app.command("start")
def session_start(
    session_type: str = typer.Option(
        None, "--type", "-t",
        help="Session type: deep-dive, pattern-hunt, or temporal"
    ),
) -> None:
    """Start a new discovery session."""
    from ktt.core.auth import require_auth
    from ktt.cli.session import run_session

    user = require_auth()
    if not user:
        raise typer.Exit(1)

    run_session(user, session_type)


@session_app.command("resume")
def session_resume() -> None:
    """Resume an interrupted session."""
    from ktt.core.auth import require_auth
    from ktt.cli.session import resume_session

    user = require_auth()
    if not user:
        raise typer.Exit(1)

    resume_session(user)


# Movies commands
@movies_app.command("add")
def movies_add() -> None:
    """Add a movie to your collection."""
    from ktt.core.auth import require_auth
    from ktt.cli.session import add_movie_interactive

    user = require_auth()
    if not user:
        raise typer.Exit(1)

    add_movie_interactive(user)


@movies_app.command("list")
def movies_list() -> None:
    """List all movies in your collection."""
    from ktt.core.auth import require_auth
    from ktt.core.database import get_session as get_db_session
    from ktt.core.models import Movie

    user = require_auth()
    if not user:
        raise typer.Exit(1)

    with get_db_session() as db:
        movies = db.query(Movie).filter(Movie.user_id == user.id).all()

        if not movies:
            print_info("No movies yet. Run 'ktt movies add' to add your first movie.")
            return

        movie_data = [
            {
                "title": m.title,
                "year": m.year,
                "analyzed": m.last_analyzed is not None,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in movies
        ]

    table = create_movie_table(movie_data)
    console.print(table)


# Patterns commands
@patterns_app.command("show")
def patterns_show() -> None:
    """Show detected patterns in your taste."""
    from ktt.core.auth import require_auth
    from ktt.core.database import get_session as get_db_session
    from ktt.core.models import Pattern, Movie
    from ktt.cli.ui import print_pattern

    user = require_auth()
    if not user:
        raise typer.Exit(1)

    print_header("Detected Patterns")

    with get_db_session() as db:
        patterns = db.query(Pattern).filter(Pattern.user_id == user.id).all()

        if not patterns:
            print_info("No patterns detected yet. Complete more sessions to find patterns.")
            return

        for p in patterns:
            # Get supporting movie titles
            movie_ids = p.supporting_movie_ids or []
            movies = db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
            movie_titles = [m.title for m in movies]

            print_pattern(
                p.pattern_type,
                p.description,
                p.confidence,
                movie_titles,
            )
            console.print()


@patterns_app.command("validate")
def patterns_validate(
    pattern_id: str = typer.Argument(..., help="Pattern ID to validate"),
) -> None:
    """Validate or reject a detected pattern."""
    from ktt.core.auth import require_auth
    from ktt.core.database import get_session as get_db_session
    from ktt.core.models import Pattern

    user = require_auth()
    if not user:
        raise typer.Exit(1)

    with get_db_session() as db:
        pattern = db.query(Pattern).filter(
            Pattern.id == pattern_id,
            Pattern.user_id == user.id,
        ).first()

        if not pattern:
            print_error(f"Pattern not found: {pattern_id}")
            raise typer.Exit(1)

        console.print(f"\n[bold]{pattern.description}[/bold]")
        console.print(f"[dim]Confidence: {pattern.confidence:.0%}[/dim]\n")

        valid = typer.confirm("Does this pattern resonate with you?")
        pattern.validated_by_user = valid
        db.commit()

        if valid:
            print_success("Pattern confirmed!")
        else:
            print_info("Pattern marked as not resonant. It will be reconsidered with more data.")


# Privacy commands
@privacy_app.command("review")
def privacy_review() -> None:
    """Review your privacy settings and consents."""
    from ktt.core.auth import require_auth
    from ktt.privacy.consent import show_consent_status

    user = require_auth()
    if not user:
        raise typer.Exit(1)

    show_consent_status(user)


@privacy_app.command("withdraw")
def privacy_withdraw(
    consent_type: str = typer.Argument(..., help="Consent type to withdraw"),
) -> None:
    """Withdraw a specific consent."""
    from ktt.core.auth import require_auth
    from ktt.privacy.consent import withdraw_consent

    user = require_auth()
    if not user:
        raise typer.Exit(1)

    withdraw_consent(user, consent_type)


@privacy_app.command("delete-all")
def privacy_delete_all() -> None:
    """Delete all your data permanently."""
    from ktt.privacy.deletion import delete_all_data

    print_warning("This will permanently delete ALL your data.")
    print_warning("This action cannot be undone.")

    if not typer.confirm("Are you sure you want to delete everything?"):
        print_info("Deletion cancelled.")
        raise typer.Exit()

    # Double confirmation
    confirm_text = typer.prompt("Type 'DELETE' to confirm")
    if confirm_text != "DELETE":
        print_info("Deletion cancelled.")
        raise typer.Exit()

    delete_all_data()
    print_success("All data has been deleted.")


if __name__ == "__main__":
    app()
