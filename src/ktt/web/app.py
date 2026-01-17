"""FastAPI application for Know Thy Taste web interface."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Get the web module directory
WEB_DIR = Path(__file__).parent
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"

app = FastAPI(
    title="Know Thy Taste",
    description="Discover why you love the movies you love",
)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Set up templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main SPA."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/questions")
async def get_questions():
    """Return the question bank as JSON for the client."""
    from ktt.questions.bank import QUESTIONS_BY_PHASE, Question

    def question_to_dict(q: Question) -> dict:
        return {
            "key": q.key,
            "text": q.text,
            "phase": q.phase,
            "category": q.category,
            "hint": q.hint,
            "exampleGood": q.example_good,
            "exampleVague": q.example_vague,
            "requiresSpecificity": q.requires_specificity,
        }

    questions = {
        phase: [question_to_dict(q) for q in phase_questions]
        for phase, phase_questions in QUESTIONS_BY_PHASE.items()
    }

    return JSONResponse(content=questions)


@app.get("/api/vague-patterns")
async def get_vague_patterns():
    """Return vague response patterns for client-side detection."""
    from ktt.questions.followups import VAGUE_PATTERNS

    patterns = [
        {
            "pattern": p.pattern,
            "category": p.category,
            "followUps": p.follow_ups,
        }
        for p in VAGUE_PATTERNS
    ]

    return JSONResponse(content=patterns)


def run():
    """Run the web server."""
    import uvicorn

    print("\n  Know Thy Taste - Web Interface")
    print("  ================================")
    print("  Open http://localhost:8000 in your browser")
    print("  Press Ctrl+C to stop\n")

    uvicorn.run(
        "ktt.web.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    run()
