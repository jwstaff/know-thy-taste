"""Rich console helpers for Know Thy Taste."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich import box

console = Console()


def print_header(text: str) -> None:
    """Print a styled header."""
    console.print()
    console.print(Panel(text, style="bold cyan", box=box.DOUBLE))
    console.print()


def print_welcome() -> None:
    """Print the welcome banner."""
    banner = """
╭─────────────────────────────────────────╮
│         KNOW THY TASTE                  │
│   Discover why you love what you love   │
╰─────────────────────────────────────────╯
    """
    console.print(banner, style="bold cyan")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]✗[/red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]![/yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[blue]i[/blue] {message}")


def print_hint(message: str) -> None:
    """Print a hint/tip message."""
    console.print(f"[dim italic]{message}[/dim italic]")


def print_question(question: str, hint: str | None = None) -> None:
    """Print a question with optional hint."""
    console.print()
    console.print(f"[bold]{question}[/bold]")
    if hint:
        print_hint(hint)
    console.print()


def print_metacognitive_prompt(prompt: str) -> None:
    """Print a metacognitive reflection prompt."""
    console.print()
    console.print(Panel(
        prompt,
        title="[dim]Pause and reflect[/dim]",
        border_style="dim cyan",
        box=box.ROUNDED,
    ))
    console.print()


def print_phase_header(phase: str, description: str) -> None:
    """Print a phase header during sessions."""
    console.print()
    console.print(f"[bold magenta]─── {phase.upper()} ───[/bold magenta]")
    console.print(f"[dim]{description}[/dim]")
    console.print()


def print_pattern(pattern_type: str, description: str, confidence: float, movies: list[str]) -> None:
    """Print a detected pattern."""
    confidence_color = "green" if confidence > 0.7 else "yellow" if confidence > 0.4 else "red"
    console.print(Panel(
        f"[bold]{description}[/bold]\n\n"
        f"Confidence: [{confidence_color}]{confidence:.0%}[/{confidence_color}]\n"
        f"Supporting films: {', '.join(movies)}",
        title=f"[cyan]{pattern_type}[/cyan]",
        box=box.ROUNDED,
    ))


def create_movie_table(movies: list[dict]) -> Table:
    """Create a table of movies."""
    table = Table(box=box.SIMPLE)
    table.add_column("Title", style="cyan")
    table.add_column("Year", style="dim")
    table.add_column("Analyzed", style="green")
    table.add_column("Added", style="dim")

    for movie in movies:
        table.add_row(
            movie.get("title", ""),
            str(movie.get("year", "")),
            "✓" if movie.get("analyzed") else "",
            movie.get("created_at", "")[:10] if movie.get("created_at") else "",
        )

    return table


def create_progress() -> Progress:
    """Create a progress indicator for long operations."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )
