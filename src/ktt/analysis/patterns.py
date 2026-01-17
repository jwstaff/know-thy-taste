"""Pattern detection engine for Know Thy Taste.

Analyzes responses across movies to detect patterns in the user's taste.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from typing import Optional

from ktt.core.database import get_session as get_db_session
from ktt.core.models import User, Movie, Response, Pattern, TasteElement
from ktt.core.encryption import decrypt_response, encrypt_json
from ktt.analysis.specificity import extract_specific_elements
from ktt.cli.ui import console, print_info

# Minimum movies needed for pattern detection
MIN_MOVIES_FOR_PATTERNS = 3

# Minimum confidence threshold for storing a pattern
MIN_PATTERN_CONFIDENCE = 0.4


def detect_patterns(user: User) -> list[Pattern]:
    """Detect patterns in user's responses and store them."""
    with get_db_session() as db:
        # Get all movies with responses
        movies = db.query(Movie).filter(Movie.user_id == user.id).all()
        if len(movies) < MIN_MOVIES_FOR_PATTERNS:
            return []

        # Get all responses
        all_responses = []
        for movie in movies:
            responses = db.query(Response).filter(Response.movie_id == movie.id).all()
            for r in responses:
                try:
                    text = decrypt_response(r.response_text)
                    all_responses.append({
                        "movie_id": movie.id,
                        "movie_title": movie.title,
                        "question_key": r.question_key,
                        "text": text,
                        "confidence": r.confidence,
                    })
                except Exception:
                    continue

        if not all_responses:
            return []

        # Extract elements from all responses
        element_counts = Counter()
        element_movies = {}  # element -> list of movie_ids

        for resp in all_responses:
            elements = extract_specific_elements(resp["text"])
            for elem in elements:
                element_counts[elem] += 1
                if elem not in element_movies:
                    element_movies[elem] = set()
                element_movies[elem].add(resp["movie_id"])

        # Find patterns (elements appearing in multiple movies)
        detected_patterns = []
        total_movies = len(movies)

        for element, count in element_counts.most_common(20):
            movie_ids = list(element_movies[element])
            movie_coverage = len(movie_ids) / total_movies

            # Calculate confidence based on coverage and mention count
            confidence = min(0.95, movie_coverage * 0.7 + (count / (len(all_responses) * 0.5)) * 0.3)

            if confidence >= MIN_PATTERN_CONFIDENCE and len(movie_ids) >= 2:
                # Determine pattern type
                if element.startswith("theme:"):
                    pattern_type = "thematic"
                    description = f"You consistently respond to themes of {element.replace('theme:', '')}"
                elif element in ["visual", "color", "lighting"]:
                    pattern_type = "visual"
                    description = f"You pay close attention to {element} elements"
                elif element in ["audio", "score", "sound"]:
                    pattern_type = "auditory"
                    description = f"Sound and music ({element}) significantly impact your experience"
                elif element in ["editing", "pacing"]:
                    pattern_type = "structural"
                    description = f"You notice and value {element} in storytelling"
                elif element in ["performance", "acting"]:
                    pattern_type = "performance"
                    description = f"Strong {element} is a key factor in your enjoyment"
                else:
                    pattern_type = "general"
                    description = f"You frequently mention {element} in your responses"

                detected_patterns.append({
                    "type": pattern_type,
                    "description": description,
                    "confidence": confidence,
                    "movie_ids": movie_ids,
                    "element": element,
                })

        # Also analyze high-confidence responses for insights
        high_confidence_responses = [r for r in all_responses if r.get("confidence", 0) and r["confidence"] >= 4]

        # Look for repeated phrases or concepts
        phrase_patterns = extract_phrase_patterns(high_confidence_responses)
        detected_patterns.extend(phrase_patterns)

        # Store patterns in database
        stored_patterns = []
        for p in detected_patterns:
            # Check if similar pattern exists
            existing = db.query(Pattern).filter(
                Pattern.user_id == user.id,
                Pattern.pattern_type == p["type"],
                Pattern.description == p["description"],
            ).first()

            if existing:
                # Update confidence and supporting movies
                existing.confidence = max(existing.confidence, p["confidence"])
                existing.supporting_movie_ids = list(set(existing.supporting_movie_ids or []) | set(p["movie_ids"]))
                existing.last_confirmed = datetime.utcnow()
                stored_patterns.append(existing)
            else:
                # Create new pattern
                pattern = Pattern(
                    user_id=user.id,
                    pattern_type=p["type"],
                    description=p["description"],
                    confidence=p["confidence"],
                    supporting_movie_ids=p["movie_ids"],
                )
                db.add(pattern)
                stored_patterns.append(pattern)

        db.commit()

        # Update taste elements
        update_taste_elements(user, element_counts, element_movies, db)

        return stored_patterns


def extract_phrase_patterns(responses: list[dict]) -> list[dict]:
    """Extract repeated phrases or concepts from responses."""
    patterns = []

    # Combine all response text
    all_text = " ".join(r["text"].lower() for r in responses)

    # Look for repeated meaningful phrases (simple approach)
    concept_patterns = [
        (r"\b(intimate|intimacy)\b", "You value intimate, close moments in films"),
        (r"\b(quiet|silence|stillness)\b", "Quiet, still moments resonate with you"),
        (r"\b(unexpected|surprise|surprising)\b", "You appreciate the unexpected"),
        (r"\b(authentic|real|genuine)\b", "Authenticity matters deeply to you"),
        (r"\b(beautiful|beauty)\b", "Visual beauty captures your attention"),
        (r"\b(tension|tense|suspense)\b", "You engage with tension and suspense"),
        (r"\b(subtle|subtlety|understated)\b", "You appreciate subtlety over obviousness"),
    ]

    for pattern, description in concept_patterns:
        matches = re.findall(pattern, all_text)
        if len(matches) >= 3:
            # Find which movies these appear in
            movie_ids = set()
            for r in responses:
                if re.search(pattern, r["text"].lower()):
                    movie_ids.add(r["movie_id"])

            if len(movie_ids) >= 2:
                patterns.append({
                    "type": "conceptual",
                    "description": description,
                    "confidence": min(0.9, len(matches) / 10 + len(movie_ids) / len(responses)),
                    "movie_ids": list(movie_ids),
                    "element": pattern,
                })

    return patterns


def update_taste_elements(user: User, element_counts: Counter, element_movies: dict, db) -> None:
    """Update the taste elements based on detected patterns."""
    for element, count in element_counts.most_common(30):
        # Parse element type
        if element.startswith("theme:"):
            elem_type = "thematic"
            elem_name = element.replace("theme:", "")
        elif element in ["visual", "color", "lighting", "framing"]:
            elem_type = "visual"
            elem_name = element
        elif element in ["audio", "score", "sound"]:
            elem_type = "auditory"
            elem_name = element
        else:
            elem_type = "general"
            elem_name = element

        # Calculate importance score
        movie_count = len(element_movies.get(element, []))
        importance = min(1.0, count * 0.1 + movie_count * 0.15)

        # Update or create taste element
        existing = db.query(TasteElement).filter(
            TasteElement.user_id == user.id,
            TasteElement.element_name == elem_name,
        ).first()

        if existing:
            existing.mention_count = count
            existing.importance_score = max(existing.importance_score, importance)
        else:
            element_record = TasteElement(
                user_id=user.id,
                element_type=elem_type,
                element_name=elem_name,
                importance_score=importance,
                mention_count=count,
            )
            db.add(element_record)


def get_user_patterns(user: User) -> list[Pattern]:
    """Get all patterns for a user."""
    with get_db_session() as db:
        return db.query(Pattern).filter(
            Pattern.user_id == user.id
        ).order_by(Pattern.confidence.desc()).all()


def get_taste_summary(user: User) -> dict:
    """Generate a taste summary for a user."""
    with get_db_session() as db:
        patterns = db.query(Pattern).filter(Pattern.user_id == user.id).all()
        elements = db.query(TasteElement).filter(
            TasteElement.user_id == user.id
        ).order_by(TasteElement.importance_score.desc()).limit(10).all()

        # Group patterns by type
        patterns_by_type = {}
        for p in patterns:
            if p.pattern_type not in patterns_by_type:
                patterns_by_type[p.pattern_type] = []
            patterns_by_type[p.pattern_type].append({
                "description": p.description,
                "confidence": p.confidence,
                "validated": p.validated_by_user,
            })

        return {
            "patterns": patterns_by_type,
            "top_elements": [
                {"name": e.element_name, "type": e.element_type, "importance": e.importance_score}
                for e in elements
            ],
            "pattern_count": len(patterns),
            "validated_count": len([p for p in patterns if p.validated_by_user]),
        }
