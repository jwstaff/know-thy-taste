"""SQLAlchemy data models for Know Thy Taste."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON,
    LargeBinary,
)
from sqlalchemy.orm import DeclarativeBase, relationship


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid4())


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class User(Base):
    """User model - single user per installation, but supports structure."""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.utcnow)
    password_hash = Column(LargeBinary, nullable=False)
    encryption_salt = Column(LargeBinary, nullable=False)
    consent_flags = Column(JSON, default=dict)
    settings = Column(JSON, default=dict)
    last_privacy_review = Column(DateTime)

    # Relationships
    movies = relationship("Movie", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    patterns = relationship("Pattern", back_populates="user", cascade="all, delete-orphan")
    taste_elements = relationship("TasteElement", back_populates="user", cascade="all, delete-orphan")


class Movie(Base):
    """Movie that the user has watched and may analyze."""
    __tablename__ = "movies"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    year = Column(Integer)
    genres = Column(JSON, default=list)  # List of genre strings
    watch_date = Column(DateTime)
    watch_context = Column(String)  # "theater", "home", "flight", etc.
    tmdb_id = Column(Integer)  # Optional TMDB reference
    created_at = Column(DateTime, default=datetime.utcnow)
    last_analyzed = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="movies")
    responses = relationship("Response", back_populates="movie", cascade="all, delete-orphan")


class Session(Base):
    """A discovery session where user analyzes one or more movies."""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_type = Column(String, nullable=False)  # "deep-dive", "pattern-hunt", "temporal"
    status = Column(String, default="active")  # "active", "completed", "abandoned"
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    movie_ids = Column(JSON, default=list)  # List of movie IDs in this session
    current_phase = Column(String, default="planning")  # "planning", "monitoring", "evaluation"
    current_question_index = Column(Integer, default=0)
    reflections = Column(LargeBinary)  # Encrypted JSON

    # Relationships
    user = relationship("User", back_populates="sessions")
    responses = relationship("Response", back_populates="session", cascade="all, delete-orphan")


class Response(Base):
    """A single response to a question during a session."""
    __tablename__ = "responses"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    movie_id = Column(String, ForeignKey("movies.id"), nullable=False)
    question_key = Column(String, nullable=False)  # Reference to question bank
    question_text = Column(Text, nullable=False)  # Actual question asked
    response_text = Column(LargeBinary, nullable=False)  # Encrypted
    confidence = Column(Integer)  # 1-5 scale
    is_new_insight = Column(Boolean, default=False)
    specificity_score = Column(Float)  # Computed score 0-1
    follow_up_count = Column(Integer, default=0)  # How many follow-ups were needed
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("Session", back_populates="responses")
    movie = relationship("Movie", back_populates="responses")


class Pattern(Base):
    """A detected pattern in the user's taste."""
    __tablename__ = "patterns"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    pattern_type = Column(String, nullable=False)  # "visual", "narrative", "thematic", etc.
    description = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)  # 0-1
    supporting_movie_ids = Column(JSON, default=list)
    supporting_evidence = Column(LargeBinary)  # Encrypted JSON of response excerpts
    validated_by_user = Column(Boolean)  # None = not validated, True/False = user response
    first_detected = Column(DateTime, default=datetime.utcnow)
    last_confirmed = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="patterns")


class TasteElement(Base):
    """An identified element of the user's taste (accumulated across sessions)."""
    __tablename__ = "taste_elements"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    element_type = Column(String, nullable=False)  # "visual", "narrative", "thematic", etc.
    element_name = Column(String, nullable=False)  # e.g., "natural lighting", "unreliable narrator"
    importance_score = Column(Float, default=0.5)  # Learned over time
    first_mentioned = Column(DateTime, default=datetime.utcnow)
    mention_count = Column(Integer, default=1)

    # Relationships
    user = relationship("User", back_populates="taste_elements")
