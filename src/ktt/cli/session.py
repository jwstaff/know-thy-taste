"""Session flow orchestration for Know Thy Taste."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import questionary
from rich.console import Console
from rich.panel import Panel
from rich import box

from ktt.core.database import get_session as get_db_session
from ktt.core.models import User, Movie, Session, Response
from ktt.core.encryption import encrypt_response
from ktt.questions.bank import Question, format_question, get_questions_for_phase
from ktt.questions.scaffolds import (
    QuestionSequencer,
    get_scaffold_level,
    get_phase_description,
    get_sentence_starters,
)
from ktt.questions.followups import (
    analyze_response,
    get_follow_up_for_attempt,
    should_accept_response,
    get_encouragement,
    get_acceptance_message,
    MAX_FOLLOW_UP_ATTEMPTS,
)
from ktt.questions.metacognitive import (
    get_random_prompt,
    get_phase_transition_prompt,
    get_confidence_description,
    CONFIDENCE_SCALE,
)
from ktt.cli.ui import (
    console,
    print_header,
    print_success,
    print_error,
    print_info,
    print_warning,
    print_hint,
    print_question,
    print_metacognitive_prompt,
    print_phase_header,
)
from ktt.privacy.consent import has_consent

SESSION_TYPES = {
    "deep-dive": "Intensive analysis of 1-2 films",
    "pattern-hunt": "Compare 3-4 similar films to find differentiators",
    "temporal": "Compare your reaction to a rewatched film vs. first viewing",
}


def run_session(user: User, session_type: Optional[str] = None) -> None:
    """Run a discovery session."""
    # Count existing sessions for scaffolding level
    with get_db_session() as db:
        session_count = db.query(Session).filter(
            Session.user_id == user.id,
            Session.status == "completed"
        ).count()

    scaffold = get_scaffold_level(session_count)

    # Select session type if not provided
    if session_type is None:
        session_type = select_session_type()
        if session_type is None:
            return

    print_header(f"Starting {session_type.replace('-', ' ').title()} Session")

    # Show session intro
    show_session_intro(session_type, scaffold.level)

    # Select movies for the session
    movies = select_movies_for_session(user, session_type)
    if not movies:
        print_info("No movies selected. Session cancelled.")
        return

    # Create session record
    with get_db_session() as db:
        session = Session(
            user_id=user.id,
            session_type=session_type,
            status="active",
            movie_ids=[m.id for m in movies],
        )
        db.add(session)
        db.commit()
        session_id = session.id

    # Run the questioning flow
    try:
        run_questioning_flow(user, session_id, movies, scaffold.level)

        # Mark session complete
        with get_db_session() as db:
            session = db.query(Session).filter(Session.id == session_id).first()
            session.status = "completed"
            session.end_time = datetime.utcnow()
            db.commit()

        # Session wrap-up
        show_session_summary(session_id)

        # Run pattern detection if consented
        if has_consent(user, "enable_pattern_analysis"):
            from ktt.analysis.patterns import detect_patterns
            detect_patterns(user)

    except KeyboardInterrupt:
        print_warning("\nSession paused. Use 'ktt session resume' to continue.")
        with get_db_session() as db:
            session = db.query(Session).filter(Session.id == session_id).first()
            session.status = "paused"
            db.commit()


def select_session_type() -> Optional[str]:
    """Interactive session type selection."""
    choices = [
        questionary.Choice(f"{name}: {desc}", value=name)
        for name, desc in SESSION_TYPES.items()
    ]

    return questionary.select(
        "What kind of session would you like?",
        choices=choices,
    ).ask()


def show_session_intro(session_type: str, scaffold_level: int) -> None:
    """Show an introduction for the session type."""
    intros = {
        "deep-dive": (
            "We'll explore one or two films in depth. The goal is to understand "
            "not just that you liked it, but *why* at a granular level."
        ),
        "pattern-hunt": (
            "We'll compare several films to find what differentiates them for you. "
            "What makes one work better than another similar film?"
        ),
        "temporal": (
            "We'll explore how your relationship with a film has changed over time. "
            "What's different now from when you first watched it?"
        ),
    }

    console.print(Panel(
        intros.get(session_type, "Let's explore your movie taste."),
        box=box.ROUNDED,
        border_style="cyan",
    ))

    if scaffold_level == 1:
        print_hint("This is one of your first sessions. I'll provide guidance and examples.")
    console.print()


def select_movies_for_session(user: User, session_type: str) -> list[Movie]:
    """Select movies for the session."""
    # Get user's existing movies
    with get_db_session() as db:
        existing_movies = db.query(Movie).filter(Movie.user_id == user.id).all()
        movie_choices = [
            questionary.Choice(f"{m.title} ({m.year})" if m.year else m.title, value=m.id)
            for m in existing_movies
        ]

    # Determine how many movies we need
    if session_type == "deep-dive":
        count_hint = "1-2 films"
        max_count = 2
    elif session_type == "pattern-hunt":
        count_hint = "3-4 similar films"
        max_count = 4
    else:  # temporal
        count_hint = "1 film you've seen multiple times"
        max_count = 1

    console.print(f"\n[bold]Select {count_hint} to analyze:[/bold]")

    selected_ids = []

    while len(selected_ids) < max_count:
        # Option to add new movie
        choices = [
            questionary.Choice("+ Add a new movie", value="__new__"),
            *[c for c in movie_choices if c.value not in selected_ids],
        ]

        if selected_ids:
            choices.append(questionary.Choice("Done selecting", value="__done__"))

        selection = questionary.select(
            f"Select movie ({len(selected_ids) + 1}/{max_count}):",
            choices=choices,
        ).ask()

        if selection is None:
            return []
        if selection == "__done__":
            break
        if selection == "__new__":
            new_movie = add_movie_interactive(user)
            if new_movie:
                selected_ids.append(new_movie.id)
                movie_choices.append(
                    questionary.Choice(
                        f"{new_movie.title} ({new_movie.year})" if new_movie.year else new_movie.title,
                        value=new_movie.id
                    )
                )
        else:
            selected_ids.append(selection)

    # Return movie objects
    with get_db_session() as db:
        movies = db.query(Movie).filter(Movie.id.in_(selected_ids)).all()
        # Detach from session
        for m in movies:
            db.expunge(m)
        return movies


def add_movie_interactive(user: User) -> Optional[Movie]:
    """Interactively add a new movie."""
    print_header("Add a Movie")

    title = questionary.text(
        "Movie title:",
        validate=lambda t: len(t.strip()) > 0 or "Title required",
    ).ask()

    if not title:
        return None

    year_str = questionary.text(
        "Year (optional):",
    ).ask()

    year = None
    if year_str and year_str.strip().isdigit():
        year = int(year_str.strip())

    # Try TMDB lookup if available
    tmdb_id = None
    genres = []

    try:
        from ktt.integrations.tmdb import search_movie, get_movie_details

        results = search_movie(title, year)
        if results:
            console.print("\n[dim]Found on TMDB:[/dim]")
            choices = [
                questionary.Choice(
                    f"{r['title']} ({r['year']}) - {r['overview'][:60]}...",
                    value=r
                )
                for r in results[:5]
            ]
            choices.append(questionary.Choice("None of these / Enter manually", value=None))

            selected = questionary.select(
                "Is one of these your movie?",
                choices=choices,
            ).ask()

            if selected:
                tmdb_id = selected["id"]
                title = selected["title"]
                year = selected["year"]
                details = get_movie_details(tmdb_id)
                if details:
                    genres = details.get("genres", [])

    except ImportError:
        pass  # TMDB not configured
    except Exception:
        pass  # TMDB lookup failed, continue without it

    # Watch context
    context = questionary.select(
        "Where did you watch it?",
        choices=[
            questionary.Choice("Theater", value="theater"),
            questionary.Choice("Home (streaming/disc)", value="home"),
            questionary.Choice("Flight / Travel", value="travel"),
            questionary.Choice("Other", value="other"),
        ],
    ).ask()

    # Create movie
    with get_db_session() as db:
        movie = Movie(
            user_id=user.id,
            title=title.strip(),
            year=year,
            genres=genres,
            watch_context=context,
            tmdb_id=tmdb_id,
        )
        db.add(movie)
        db.commit()
        db.refresh(movie)
        db.expunge(movie)

    print_success(f"Added: {movie.title}")
    return movie


def run_questioning_flow(user: User, session_id: str, movies: list[Movie], scaffold_level: int) -> None:
    """Run the main questioning flow for a session."""
    scaffold = get_scaffold_level(scaffold_level - 1)  # Convert level to count-based
    sequencer = QuestionSequencer("deep-dive", scaffold)

    questions = sequencer.get_questions_for_session_type()
    current_phase = None
    used_prompts = []

    for movie in movies:
        console.print(f"\n[bold cyan]── Analyzing: {movie.title} ──[/bold cyan]\n")

        for question in questions:
            # Show phase header if changed
            if question.phase != current_phase:
                if current_phase:
                    # Show transition prompt
                    transition = get_phase_transition_prompt(current_phase, question.phase)
                    if transition:
                        print_metacognitive_prompt(transition.text)

                current_phase = question.phase
                phase_info = get_phase_description(current_phase)
                print_phase_header(phase_info["name"], phase_info["description"])

            # Occasionally show metacognitive prompt before question
            if sequencer.should_show_hint() and len(used_prompts) < 3:
                prompt = get_random_prompt("before_question", used_prompts)
                if prompt and question.phase == "monitoring":
                    print_metacognitive_prompt(prompt.text)
                    used_prompts.append(prompt.key)

            # Ask the question
            response_text, confidence, is_new = ask_question(
                question,
                movie.title,
                sequencer,
            )

            if response_text is None:
                # User skipped or cancelled
                continue

            # Save response
            save_response(
                session_id=session_id,
                movie_id=movie.id,
                question=question,
                response_text=response_text,
                confidence=confidence,
                is_new_insight=is_new,
            )

        # Update movie's last_analyzed
        with get_db_session() as db:
            db_movie = db.query(Movie).filter(Movie.id == movie.id).first()
            db_movie.last_analyzed = datetime.utcnow()
            db.commit()


def ask_question(question: Question, movie_title: str, sequencer: QuestionSequencer) -> tuple[Optional[str], Optional[int], bool]:
    """Ask a single question and handle follow-ups. Returns (response, confidence, is_new_insight)."""
    formatted = format_question(question, movie_title)

    # Show question with optional hint
    print_question(
        formatted,
        hint=question.hint if sequencer.should_show_hint() else None
    )

    # Show example if heavy scaffolding
    if sequencer.should_show_example() and question.example_good:
        console.print("[dim]Example of a specific response:[/dim]")
        console.print(f"[dim italic]\"{question.example_good}\"[/dim italic]\n")

    # Show sentence starters if heavy scaffolding
    if sequencer.should_provide_starters():
        starters = get_sentence_starters(question.category)
        if starters:
            console.print("[dim]You might start with:[/dim]")
            for starter in starters[:2]:
                console.print(f"  [dim]• {starter}[/dim]")
            console.print()

    # Get response with follow-up loop
    attempt = 0
    response_text = None

    while attempt <= MAX_FOLLOW_UP_ATTEMPTS:
        response = questionary.text(
            "Your response:",
            multiline=True,
        ).ask()

        if response is None:
            # User cancelled
            return None, None, False

        if response.strip().lower() in ["skip", "pass", "s"]:
            print_info("Skipping this question.")
            return None, None, False

        response_text = response.strip()

        # Analyze for vagueness
        if sequencer.should_validate_responses():
            analysis = analyze_response(response_text)

            if should_accept_response(analysis, attempt):
                if analysis.specificity_score >= 0.6:
                    console.print(f"[green]{get_encouragement()}[/green]")
                elif attempt > 0:
                    console.print(f"[dim]{get_acceptance_message()}[/dim]")
                break
            else:
                # Ask for more specificity
                follow_up = get_follow_up_for_attempt(analysis, attempt)
                if follow_up:
                    console.print(f"\n[yellow]{follow_up}[/yellow]\n")
                attempt += 1
        else:
            break

    # Ask for confidence rating
    confidence = None
    if response_text:
        confidence_choices = [
            questionary.Choice(f"{level}: {desc}", value=level)
            for level, desc in CONFIDENCE_SCALE.items()
        ]
        confidence_choices.append(questionary.Choice("Skip rating", value=None))

        confidence = questionary.select(
            "How confident are you in this response?",
            choices=confidence_choices,
        ).ask()

    # Ask if this is a new insight
    is_new = False
    if response_text:
        meta_prompt = get_random_prompt("after_response")
        if meta_prompt and meta_prompt.key == "new_insight":
            is_new = questionary.confirm(
                "Is this a new realization, or something you've known?",
                default=False,
            ).ask() or False

    return response_text, confidence, is_new


def save_response(
    session_id: str,
    movie_id: str,
    question: Question,
    response_text: str,
    confidence: Optional[int],
    is_new_insight: bool,
) -> None:
    """Save a response to the database."""
    analysis = analyze_response(response_text)

    with get_db_session() as db:
        response = Response(
            session_id=session_id,
            movie_id=movie_id,
            question_key=question.key,
            question_text=question.text,
            response_text=encrypt_response(response_text),
            confidence=confidence,
            is_new_insight=is_new_insight,
            specificity_score=analysis.specificity_score,
        )
        db.add(response)
        db.commit()


def show_session_summary(session_id: str) -> None:
    """Show a summary at the end of a session."""
    print_header("Session Complete")

    with get_db_session() as db:
        session = db.query(Session).filter(Session.id == session_id).first()
        response_count = db.query(Response).filter(Response.session_id == session_id).count()

        # Calculate average specificity
        responses = db.query(Response).filter(Response.session_id == session_id).all()
        if responses:
            avg_specificity = sum(r.specificity_score or 0 for r in responses) / len(responses)
        else:
            avg_specificity = 0

    console.print(Panel(
        f"[cyan]Reflections captured:[/cyan] {response_count}\n"
        f"[cyan]Average specificity:[/cyan] {avg_specificity:.0%}\n"
        f"[cyan]Duration:[/cyan] {format_duration(session.start_time, session.end_time or datetime.utcnow())}",
        title="Summary",
        box=box.ROUNDED,
    ))

    # End-of-session metacognitive prompt
    prompt = get_random_prompt("session_end")
    if prompt:
        print_metacognitive_prompt(prompt.text)
        questionary.text("Your reflection (optional):").ask()

    print_success("Session saved. Run 'ktt patterns show' to see detected patterns.")


def format_duration(start: datetime, end: datetime) -> str:
    """Format a duration nicely."""
    delta = end - start
    minutes = int(delta.total_seconds() / 60)
    if minutes < 60:
        return f"{minutes} minutes"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"


def resume_session(user: User) -> None:
    """Resume a paused session."""
    with get_db_session() as db:
        paused_sessions = db.query(Session).filter(
            Session.user_id == user.id,
            Session.status == "paused"
        ).all()

        if not paused_sessions:
            print_info("No paused sessions to resume.")
            return

        # Select session to resume
        choices = [
            questionary.Choice(
                f"{s.session_type} - {s.start_time.strftime('%Y-%m-%d %H:%M')}",
                value=s.id
            )
            for s in paused_sessions
        ]

        session_id = questionary.select(
            "Which session would you like to resume?",
            choices=choices,
        ).ask()

        if not session_id:
            return

        session = db.query(Session).filter(Session.id == session_id).first()
        movies = db.query(Movie).filter(Movie.id.in_(session.movie_ids)).all()

        # Get already answered questions
        answered = db.query(Response.question_key).filter(
            Response.session_id == session_id
        ).all()
        answered_keys = {r[0] for r in answered}

    print_info(f"Resuming session. {len(answered_keys)} questions already answered.")

    # Continue the session (simplified - would need more sophisticated tracking)
    session.status = "active"
    run_session(user, session.session_type)
