"""Database connection and initialization for Know Thy Taste."""

import os
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from ktt.core.models import Base

_engine = None
_SessionLocal = None


def get_data_dir() -> Path:
    """Get the data directory for Know Thy Taste."""
    # Use XDG_DATA_HOME on Linux, or app-specific location
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif os.name == "posix":
        if "darwin" in os.uname().sysname.lower():  # macOS
            base = Path.home() / "Library" / "Application Support"
        else:  # Linux
            base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    else:
        base = Path.home()

    data_dir = base / "know-thy-taste"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_db_path() -> Path:
    """Get the database file path."""
    return get_data_dir() / "ktt.db"


def init_db(passphrase: str) -> None:
    """Initialize the database with the given passphrase."""
    global _engine, _SessionLocal

    db_path = get_db_path()
    db_url = f"sqlite:///{db_path}"

    _engine = create_engine(db_url, echo=False)
    _SessionLocal = sessionmaker(bind=_engine)

    # Create all tables
    Base.metadata.create_all(_engine)

    # Store that we're initialized (passphrase verified elsewhere)
    (get_data_dir() / ".initialized").touch()


def connect_db() -> bool:
    """Connect to an existing database. Returns True if successful."""
    global _engine, _SessionLocal

    db_path = get_db_path()
    if not db_path.exists():
        return False

    db_url = f"sqlite:///{db_path}"
    _engine = create_engine(db_url, echo=False)
    _SessionLocal = sessionmaker(bind=_engine)
    return True


def is_initialized() -> bool:
    """Check if the database is initialized."""
    return get_db_path().exists() and (get_data_dir() / ".initialized").exists()


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session context manager."""
    if _SessionLocal is None:
        if not connect_db():
            raise RuntimeError("Database not initialized. Run 'ktt init' first.")

    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def delete_database() -> None:
    """Delete the database and all data."""
    global _engine, _SessionLocal

    if _engine:
        _engine.dispose()
        _engine = None
        _SessionLocal = None

    data_dir = get_data_dir()
    db_path = get_db_path()

    if db_path.exists():
        db_path.unlink()

    init_marker = data_dir / ".initialized"
    if init_marker.exists():
        init_marker.unlink()
