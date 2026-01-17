"""Scaffolding support for question progression.

Implements adaptive scaffolding based on adult learning principles:
- Early sessions: Heavy guidance and examples
- Middle sessions: Occasional prompts
- Advanced sessions: Light touch, open-ended
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ktt.questions.bank import Question, get_questions_for_phase


@dataclass
class ScaffoldLevel:
    """A scaffolding level with its characteristics."""
    level: int  # 1-3, where 1 is heavy and 3 is light
    show_hints: bool
    show_examples: bool
    provide_starters: bool
    validate_responses: bool


# Scaffolding levels
HEAVY_SCAFFOLD = ScaffoldLevel(
    level=1,
    show_hints=True,
    show_examples=True,
    provide_starters=True,
    validate_responses=True,
)

MEDIUM_SCAFFOLD = ScaffoldLevel(
    level=2,
    show_hints=True,
    show_examples=False,
    provide_starters=False,
    validate_responses=True,
)

LIGHT_SCAFFOLD = ScaffoldLevel(
    level=3,
    show_hints=False,
    show_examples=False,
    provide_starters=False,
    validate_responses=False,
)


def get_scaffold_level(session_count: int) -> ScaffoldLevel:
    """Determine scaffolding level based on user's session count."""
    if session_count <= 3:
        return HEAVY_SCAFFOLD
    elif session_count <= 8:
        return MEDIUM_SCAFFOLD
    else:
        return LIGHT_SCAFFOLD


# Sentence starters for heavy scaffolding
SENTENCE_STARTERS = {
    "sensory": [
        "The moment that comes to mind is...",
        "I remember seeing...",
        "I can still hear...",
        "What struck me visually was...",
    ],
    "emotional": [
        "I felt...",
        "It made me...",
        "I was surprised to find myself...",
        "My immediate reaction was...",
    ],
    "narrative": [
        "The story worked because...",
        "I was drawn in when...",
        "The structure made me...",
        "What kept me watching was...",
    ],
    "thematic": [
        "This connects to...",
        "I found myself thinking about...",
        "It reminded me of...",
        "What resonated was...",
    ],
    "technical": [
        "I noticed the way...",
        "The [element] made me...",
        "What stood out technically was...",
        "I was aware of...",
    ],
}


def get_sentence_starters(category: str) -> list[str]:
    """Get sentence starters for a question category."""
    return SENTENCE_STARTERS.get(category, [])


# Multiple choice priming questions
PRIMING_QUESTIONS = {
    "sensory": {
        "prompt": "Was the moment that struck you primarily:",
        "options": [
            ("visual", "Something you saw (a shot, a face, a color)"),
            ("auditory", "Something you heard (dialogue, music, silence)"),
            ("kinetic", "Movement or action (choreography, pacing)"),
            ("atmospheric", "A feeling or mood in a scene"),
        ],
    },
    "emotional": {
        "prompt": "Your emotional response was mostly:",
        "options": [
            ("visceral", "Physical—tears, laughter, tension"),
            ("contemplative", "Thoughtful—made you reflect"),
            ("nostalgic", "Connected to your own memories"),
            ("unsettling", "Uncomfortable in an interesting way"),
        ],
    },
}


def get_priming_question(category: str) -> Optional[dict]:
    """Get a priming multiple-choice question for a category."""
    return PRIMING_QUESTIONS.get(category)


# Phase descriptions for users
PHASE_DESCRIPTIONS = {
    "planning": {
        "name": "Planning / Awareness",
        "description": "Let's start by noticing what stayed with you from this film.",
        "goal": "Capture initial impressions and expectations.",
    },
    "monitoring": {
        "name": "Monitoring / Engagement",
        "description": "Now let's explore how you engaged with the film while watching.",
        "goal": "Understand your moment-to-moment experience.",
    },
    "evaluation": {
        "name": "Evaluation / Meaning",
        "description": "Finally, let's reflect on what this film means to you.",
        "goal": "Extract insights about your taste and values.",
    },
}


def get_phase_description(phase: str) -> dict:
    """Get the description for a phase."""
    return PHASE_DESCRIPTIONS.get(phase, {"name": phase, "description": "", "goal": ""})


class QuestionSequencer:
    """Manages the sequence of questions in a session."""

    def __init__(self, session_type: str, scaffold_level: ScaffoldLevel):
        self.session_type = session_type
        self.scaffold = scaffold_level
        self.current_phase = "planning"
        self.phase_index = 0
        self.phases = ["planning", "monitoring", "evaluation"]

    def get_current_phase(self) -> str:
        """Get the current phase."""
        return self.current_phase

    def get_next_question(self) -> Optional[Question]:
        """Get the next question in the sequence."""
        questions = get_questions_for_phase(self.current_phase)

        if self.phase_index >= len(questions):
            # Move to next phase
            current_phase_idx = self.phases.index(self.current_phase)
            if current_phase_idx < len(self.phases) - 1:
                self.current_phase = self.phases[current_phase_idx + 1]
                self.phase_index = 0
                questions = get_questions_for_phase(self.current_phase)
            else:
                return None  # Session complete

        if self.phase_index < len(questions):
            question = questions[self.phase_index]
            self.phase_index += 1
            return question

        return None

    def get_questions_for_session_type(self) -> list[Question]:
        """Get a curated list of questions based on session type."""
        if self.session_type == "deep-dive":
            # Full sequence for one movie
            return (
                get_questions_for_phase("planning")[:3] +
                get_questions_for_phase("monitoring")[:4] +
                get_questions_for_phase("evaluation")[:4]
            )
        elif self.session_type == "pattern-hunt":
            # Focus on comparison questions
            return [
                q for q in (
                    get_questions_for_phase("monitoring") +
                    get_questions_for_phase("evaluation")
                )
                if "compar" in q.text.lower() or "different" in q.text.lower() or "remov" in q.text.lower()
            ][:6]
        elif self.session_type == "temporal":
            # Focus on change over time
            return [
                q for q in get_questions_for_phase("evaluation")
                if "change" in q.text.lower() or "last" in q.text.lower() or "stay" in q.text.lower()
            ][:4]
        else:
            # Default: balanced selection
            return (
                get_questions_for_phase("planning")[:2] +
                get_questions_for_phase("monitoring")[:3] +
                get_questions_for_phase("evaluation")[:3]
            )

    def should_show_hint(self) -> bool:
        """Whether to show hints for current scaffold level."""
        return self.scaffold.show_hints

    def should_show_example(self) -> bool:
        """Whether to show examples for current scaffold level."""
        return self.scaffold.show_examples

    def should_provide_starters(self) -> bool:
        """Whether to provide sentence starters."""
        return self.scaffold.provide_starters

    def should_validate_responses(self) -> bool:
        """Whether to validate response specificity."""
        return self.scaffold.validate_responses
