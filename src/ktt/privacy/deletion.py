"""Data deletion functionality for Know Thy Taste."""

import shutil
from pathlib import Path

from ktt.core.database import get_data_dir, delete_database
from ktt.core.encryption import clear_encryption_key
from ktt.cli.ui import print_info


def delete_all_data() -> None:
    """Delete all user data permanently."""
    # Clear encryption key
    clear_encryption_key()

    # Delete database
    delete_database()

    # Remove any exports
    data_dir = get_data_dir()
    exports_dir = data_dir / "exports"
    if exports_dir.exists():
        shutil.rmtree(exports_dir)

    # Remove any remaining files in data directory
    for item in data_dir.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)

    print_info("All data has been permanently deleted.")


def delete_movie_data(user_id: str, movie_id: str) -> None:
    """Delete all data associated with a specific movie."""
    from ktt.core.database import get_session
    from ktt.core.models import Movie, Response

    with get_session() as db:
        # Delete responses
        db.query(Response).filter(Response.movie_id == movie_id).delete()

        # Delete movie
        db.query(Movie).filter(
            Movie.id == movie_id,
            Movie.user_id == user_id
        ).delete()

        db.commit()


def delete_session_data(user_id: str, session_id: str) -> None:
    """Delete all data associated with a specific session."""
    from ktt.core.database import get_session
    from ktt.core.models import Session, Response

    with get_session() as db:
        # Delete responses from this session
        db.query(Response).filter(Response.session_id == session_id).delete()

        # Delete session
        db.query(Session).filter(
            Session.id == session_id,
            Session.user_id == user_id
        ).delete()

        db.commit()
