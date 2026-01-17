"""Optional TMDB (The Movie Database) integration.

Provides movie search and metadata fetching when user has a TMDB API key.
Works gracefully when offline or without an API key.
"""

from __future__ import annotations

import os
from typing import Optional
from pathlib import Path

import httpx

from ktt.core.database import get_data_dir

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TIMEOUT = 10.0  # seconds


def get_api_key() -> Optional[str]:
    """Get the TMDB API key from environment or config file."""
    # First check environment variable
    key = os.environ.get("TMDB_API_KEY")
    if key:
        return key

    # Then check config file
    config_path = get_data_dir() / "tmdb_key"
    if config_path.exists():
        return config_path.read_text().strip()

    return None


def save_api_key(key: str) -> None:
    """Save the TMDB API key to config file."""
    config_path = get_data_dir() / "tmdb_key"
    config_path.write_text(key)


def remove_api_key() -> None:
    """Remove the stored TMDB API key."""
    config_path = get_data_dir() / "tmdb_key"
    if config_path.exists():
        config_path.unlink()


def is_configured() -> bool:
    """Check if TMDB is configured with an API key."""
    return get_api_key() is not None


def search_movie(title: str, year: Optional[int] = None) -> list[dict]:
    """
    Search for a movie by title.

    Returns a list of results with keys: id, title, year, overview
    Returns empty list if TMDB is not configured or request fails.
    """
    api_key = get_api_key()
    if not api_key:
        return []

    params = {
        "api_key": api_key,
        "query": title,
        "include_adult": "false",
    }

    if year:
        params["year"] = str(year)

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(f"{TMDB_BASE_URL}/search/movie", params=params)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", [])[:10]:
                release_date = item.get("release_date", "")
                movie_year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None

                results.append({
                    "id": item["id"],
                    "title": item["title"],
                    "year": movie_year,
                    "overview": item.get("overview", "")[:200],
                })

            return results

    except (httpx.HTTPError, httpx.TimeoutException, KeyError, ValueError):
        return []


def get_movie_details(tmdb_id: int) -> Optional[dict]:
    """
    Get detailed information about a movie.

    Returns dict with keys: title, year, genres, overview, runtime, tagline
    Returns None if TMDB is not configured or request fails.
    """
    api_key = get_api_key()
    if not api_key:
        return None

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(
                f"{TMDB_BASE_URL}/movie/{tmdb_id}",
                params={"api_key": api_key}
            )
            response.raise_for_status()
            data = response.json()

            release_date = data.get("release_date", "")
            year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None

            return {
                "title": data.get("title"),
                "year": year,
                "genres": [g["name"] for g in data.get("genres", [])],
                "overview": data.get("overview"),
                "runtime": data.get("runtime"),
                "tagline": data.get("tagline"),
            }

    except (httpx.HTTPError, httpx.TimeoutException, KeyError, ValueError):
        return None


def get_movie_credits(tmdb_id: int) -> Optional[dict]:
    """
    Get cast and crew information for a movie.

    Returns dict with keys: director, cast (list of names)
    Returns None if TMDB is not configured or request fails.
    """
    api_key = get_api_key()
    if not api_key:
        return None

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(
                f"{TMDB_BASE_URL}/movie/{tmdb_id}/credits",
                params={"api_key": api_key}
            )
            response.raise_for_status()
            data = response.json()

            # Get director from crew
            director = None
            for crew_member in data.get("crew", []):
                if crew_member.get("job") == "Director":
                    director = crew_member.get("name")
                    break

            # Get top cast
            cast = [
                member.get("name")
                for member in data.get("cast", [])[:5]
            ]

            return {
                "director": director,
                "cast": cast,
            }

    except (httpx.HTTPError, httpx.TimeoutException, KeyError, ValueError):
        return None


def validate_api_key(key: str) -> bool:
    """Validate that an API key works with TMDB."""
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(
                f"{TMDB_BASE_URL}/configuration",
                params={"api_key": key}
            )
            return response.status_code == 200
    except (httpx.HTTPError, httpx.TimeoutException):
        return False


def setup_tmdb_interactive() -> bool:
    """Interactive setup for TMDB API key."""
    import questionary
    from ktt.cli.ui import print_success, print_error, print_info

    print_info("TMDB integration allows auto-fetching movie metadata.")
    print_info("Get a free API key at: https://www.themoviedb.org/settings/api")

    key = questionary.text(
        "Enter your TMDB API key (or press Enter to skip):",
    ).ask()

    if not key or not key.strip():
        print_info("TMDB integration skipped. You can set it up later.")
        return False

    key = key.strip()

    print_info("Validating API key...")
    if validate_api_key(key):
        save_api_key(key)
        print_success("TMDB configured successfully!")
        return True
    else:
        print_error("Invalid API key. TMDB integration not configured.")
        return False
