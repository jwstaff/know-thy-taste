"""Data export functionality for Know Thy Taste."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ktt.core.database import get_session, get_data_dir
from ktt.core.models import User, Movie, Session, Response, Pattern, TasteElement
from ktt.core.encryption import decrypt_response, decrypt_json
from ktt.privacy.consent import has_consent
from ktt.cli.ui import print_warning, print_info


def export_data(user: User, format: str, output_path: Optional[Path] = None) -> Path:
    """Export all user data in the specified format."""
    if not has_consent(user, "enable_export"):
        print_warning("Export is not enabled. Run 'ktt privacy review' to enable it.")
        raise ValueError("Export consent not given")

    if format == "json":
        return export_json(user, output_path)
    elif format == "markdown":
        return export_markdown(user, output_path)
    else:
        raise ValueError(f"Unknown format: {format}")


def export_json(user: User, output_path: Optional[Path] = None) -> Path:
    """Export data as JSON."""
    export_dir = get_data_dir() / "exports"
    export_dir.mkdir(exist_ok=True)

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = export_dir / f"ktt_export_{timestamp}.json"

    data = gather_export_data(user)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

    return output_path


def export_markdown(user: User, output_path: Optional[Path] = None) -> Path:
    """Export data as Markdown."""
    export_dir = get_data_dir() / "exports"
    export_dir.mkdir(exist_ok=True)

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = export_dir / f"ktt_export_{timestamp}.md"

    data = gather_export_data(user)
    markdown = generate_markdown(data)

    with open(output_path, "w") as f:
        f.write(markdown)

    return output_path


def gather_export_data(user: User) -> dict:
    """Gather all user data for export."""
    with get_session() as db:
        # Get user's movies
        movies = db.query(Movie).filter(Movie.user_id == user.id).all()
        movie_data = []

        for movie in movies:
            movie_dict = {
                "id": movie.id,
                "title": movie.title,
                "year": movie.year,
                "genres": movie.genres,
                "watch_date": movie.watch_date.isoformat() if movie.watch_date else None,
                "watch_context": movie.watch_context,
                "created_at": movie.created_at.isoformat() if movie.created_at else None,
                "responses": [],
            }

            # Get responses for this movie
            responses = db.query(Response).filter(Response.movie_id == movie.id).all()
            for resp in responses:
                try:
                    response_text = decrypt_response(resp.response_text)
                except Exception:
                    response_text = "[Unable to decrypt]"

                movie_dict["responses"].append({
                    "question": resp.question_text,
                    "response": response_text,
                    "confidence": resp.confidence,
                    "is_new_insight": resp.is_new_insight,
                    "created_at": resp.created_at.isoformat() if resp.created_at else None,
                })

            movie_data.append(movie_dict)

        # Get patterns
        patterns = db.query(Pattern).filter(Pattern.user_id == user.id).all()
        pattern_data = []

        for pattern in patterns:
            # Get supporting movie titles
            supporting_movies = db.query(Movie).filter(
                Movie.id.in_(pattern.supporting_movie_ids or [])
            ).all()

            pattern_data.append({
                "type": pattern.pattern_type,
                "description": pattern.description,
                "confidence": pattern.confidence,
                "supporting_movies": [m.title for m in supporting_movies],
                "validated": pattern.validated_by_user,
                "first_detected": pattern.first_detected.isoformat() if pattern.first_detected else None,
            })

        # Get taste elements
        elements = db.query(TasteElement).filter(TasteElement.user_id == user.id).all()
        element_data = [
            {
                "type": e.element_type,
                "name": e.element_name,
                "importance": e.importance_score,
                "mention_count": e.mention_count,
            }
            for e in elements
        ]

        # Get session history
        sessions = db.query(Session).filter(Session.user_id == user.id).all()
        session_data = [
            {
                "type": s.session_type,
                "status": s.status,
                "start_time": s.start_time.isoformat() if s.start_time else None,
                "end_time": s.end_time.isoformat() if s.end_time else None,
            }
            for s in sessions
        ]

    return {
        "export_date": datetime.now().isoformat(),
        "privacy_notice": "This file contains your personal reflections. Handle with care.",
        "movies": movie_data,
        "patterns": pattern_data,
        "taste_elements": element_data,
        "sessions": session_data,
    }


def generate_markdown(data: dict) -> str:
    """Generate a Markdown document from export data."""
    lines = [
        "# Know Thy Taste - Export",
        "",
        f"*Exported: {data['export_date'][:10]}*",
        "",
        "---",
        "",
    ]

    # Summary
    lines.extend([
        "## Summary",
        "",
        f"- **Movies analyzed:** {len(data['movies'])}",
        f"- **Patterns detected:** {len(data['patterns'])}",
        f"- **Sessions completed:** {len([s for s in data['sessions'] if s['status'] == 'completed'])}",
        "",
    ])

    # Patterns
    if data["patterns"]:
        lines.extend([
            "## Detected Patterns",
            "",
        ])
        for pattern in data["patterns"]:
            validated = "✓" if pattern["validated"] else "?" if pattern["validated"] is None else "✗"
            lines.extend([
                f"### {pattern['type'].title()} [{validated}]",
                "",
                f"**{pattern['description']}**",
                "",
                f"- Confidence: {pattern['confidence']:.0%}",
                f"- Supporting films: {', '.join(pattern['supporting_movies'])}",
                "",
            ])

    # Taste Elements
    if data["taste_elements"]:
        lines.extend([
            "## Taste Elements",
            "",
        ])
        for elem in sorted(data["taste_elements"], key=lambda x: -x["importance"]):
            lines.append(f"- **{elem['name']}** ({elem['type']}) - mentioned {elem['mention_count']}x")
        lines.append("")

    # Movies and Reflections
    lines.extend([
        "## Movies & Reflections",
        "",
    ])

    for movie in data["movies"]:
        year = f" ({movie['year']})" if movie["year"] else ""
        lines.extend([
            f"### {movie['title']}{year}",
            "",
        ])

        if movie["genres"]:
            lines.append(f"*Genres: {', '.join(movie['genres'])}*")
            lines.append("")

        if movie["responses"]:
            for resp in movie["responses"]:
                lines.extend([
                    f"**Q: {resp['question']}**",
                    "",
                    f"> {resp['response']}",
                    "",
                ])
                if resp["confidence"]:
                    lines.append(f"*Confidence: {resp['confidence']}/5*")
                lines.append("")
        else:
            lines.append("*No reflections recorded yet.*")
            lines.append("")

    # Footer
    lines.extend([
        "---",
        "",
        "*Generated by Know Thy Taste*",
    ])

    return "\n".join(lines)
