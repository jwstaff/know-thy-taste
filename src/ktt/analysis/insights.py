"""Insight generation for Know Thy Taste.

Generates human-readable insights from patterns and responses.
"""

from __future__ import annotations

from typing import Optional

from ktt.core.database import get_session as get_db_session
from ktt.core.models import User, Pattern, TasteElement, Movie


def generate_profile_insights(user: User) -> list[str]:
    """Generate natural language insights about the user's taste."""
    insights = []

    with get_db_session() as db:
        # Get validated patterns
        patterns = db.query(Pattern).filter(
            Pattern.user_id == user.id,
            Pattern.validated_by_user == True
        ).order_by(Pattern.confidence.desc()).all()

        # Get top taste elements
        elements = db.query(TasteElement).filter(
            TasteElement.user_id == user.id
        ).order_by(TasteElement.importance_score.desc()).limit(5).all()

        # Get movie count
        movie_count = db.query(Movie).filter(Movie.user_id == user.id).count()

    if not patterns and not elements:
        return ["Complete more sessions to discover patterns in your taste."]

    # Generate insights from patterns
    if patterns:
        top_pattern = patterns[0]
        insights.append(f"Your most distinctive trait: {top_pattern.description.lower()}")

        if len(patterns) >= 2:
            # Find thematic patterns
            thematic = [p for p in patterns if p.pattern_type == "thematic"]
            if thematic:
                insights.append(f"Themes that resonate: {thematic[0].description.split('themes of ')[-1] if 'themes of' in thematic[0].description else 'various emotional themes'}")

            # Find technical patterns
            technical = [p for p in patterns if p.pattern_type in ["visual", "auditory", "structural"]]
            if technical:
                insights.append(f"You're particularly attuned to {technical[0].pattern_type} elements in films.")

    # Generate insights from taste elements
    if elements:
        top_elements = [e.element_name for e in elements[:3]]
        if top_elements:
            insights.append(f"Elements you frequently notice: {', '.join(top_elements)}")

    # Add comparative insights
    if movie_count >= 5:
        insights.append(f"Based on {movie_count} films analyzed, your taste profile is taking shape.")

    return insights


def generate_session_insights(session_id: str) -> list[str]:
    """Generate insights specific to a session."""
    from ktt.core.models import Session, Response
    from ktt.core.encryption import decrypt_response

    insights = []

    with get_db_session() as db:
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            return insights

        responses = db.query(Response).filter(Response.session_id == session_id).all()

        # Calculate stats
        total_responses = len(responses)
        high_confidence = len([r for r in responses if r.confidence and r.confidence >= 4])
        new_insights_count = len([r for r in responses if r.is_new_insight])
        avg_specificity = sum(r.specificity_score or 0 for r in responses) / total_responses if total_responses else 0

    if total_responses == 0:
        return ["No responses recorded in this session."]

    # Confidence insight
    if high_confidence / total_responses > 0.5:
        insights.append("You expressed high confidence in most of your responses—you know your taste well.")
    elif high_confidence / total_responses < 0.2:
        insights.append("Many responses had lower confidence—you may be discovering new aspects of your taste.")

    # New insights
    if new_insights_count > 0:
        insights.append(f"You identified {new_insights_count} new insight{'s' if new_insights_count > 1 else ''} about yourself.")

    # Specificity
    if avg_specificity > 0.6:
        insights.append("Your responses were notably specific—great for understanding your taste.")
    elif avg_specificity < 0.4:
        insights.append("Consider being more specific in future sessions for richer insights.")

    return insights


def compare_movies(user: User, movie_ids: list[str]) -> Optional[str]:
    """Generate a comparison insight between movies."""
    from ktt.core.models import Movie, Response
    from ktt.core.encryption import decrypt_response
    from ktt.analysis.specificity import extract_specific_elements

    with get_db_session() as db:
        movies = db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
        if len(movies) < 2:
            return None

        # Get elements for each movie
        movie_elements = {}
        for movie in movies:
            responses = db.query(Response).filter(Response.movie_id == movie.id).all()
            elements = set()
            for r in responses:
                try:
                    text = decrypt_response(r.response_text)
                    elements.update(extract_specific_elements(text))
                except Exception:
                    continue
            movie_elements[movie.title] = elements

    # Find common and unique elements
    all_elements = set()
    for elements in movie_elements.values():
        all_elements.update(elements)

    common = all_elements.copy()
    for elements in movie_elements.values():
        common &= elements

    if common:
        return f"These films share your attention to: {', '.join(list(common)[:3])}"

    # Find distinguishing elements
    for title, elements in movie_elements.items():
        unique = elements - set().union(*[e for t, e in movie_elements.items() if t != title])
        if unique:
            return f"{title} uniquely engaged your {list(unique)[0]} sensibilities."

    return "These films appealed to different aspects of your taste."
