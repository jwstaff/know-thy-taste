"""Metacognitive reflection prompts for Know Thy Taste.

These prompts help users develop awareness of their own thinking processes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import random


@dataclass
class MetacognitivePrompt:
    """A metacognitive reflection prompt."""
    key: str
    text: str
    timing: str  # "before_question", "after_response", "phase_transition", "session_end"
    category: str  # "awareness", "strategy", "confidence", "insight"


# Prompts to show BEFORE a question
BEFORE_QUESTION_PROMPTS = [
    MetacognitivePrompt(
        key="notice_first",
        text="Before answering, pause for a moment. What comes to mind first?",
        timing="before_question",
        category="awareness",
    ),
    MetacognitivePrompt(
        key="feeling_check",
        text="How are you feeling about analyzing this film? Excited? Resistant? Neutral?",
        timing="before_question",
        category="awareness",
    ),
    MetacognitivePrompt(
        key="memory_strategy",
        text="What strategy are you using to recall these details? Replaying scenes? Remembering feelings?",
        timing="before_question",
        category="strategy",
    ),
]

# Prompts to show AFTER a response
AFTER_RESPONSE_PROMPTS = [
    MetacognitivePrompt(
        key="new_insight",
        text="Was that something you've thought about before, or did articulating it reveal something new?",
        timing="after_response",
        category="insight",
    ),
    MetacognitivePrompt(
        key="confidence_check",
        text="How confident are you in that response? Solid ground or still exploring?",
        timing="after_response",
        category="confidence",
    ),
    MetacognitivePrompt(
        key="authentic_check",
        text="Are you describing what you actually experienced, or what you think you should have experienced?",
        timing="after_response",
        category="awareness",
    ),
    MetacognitivePrompt(
        key="articulation_quality",
        text="If you explained this to a friend, would they understand exactly what you mean?",
        timing="after_response",
        category="strategy",
    ),
]

# Prompts for PHASE TRANSITIONS
PHASE_TRANSITION_PROMPTS = {
    "planning_to_monitoring": [
        MetacognitivePrompt(
            key="transition_1",
            text="You've captured your initial impressions. Now let's go deeper into how you actually engaged with the film.",
            timing="phase_transition",
            category="awareness",
        ),
    ],
    "monitoring_to_evaluation": [
        MetacognitivePrompt(
            key="transition_2",
            text="You've explored your experience. Now let's step back and reflect on what it all means.",
            timing="phase_transition",
            category="awareness",
        ),
    ],
}

# Prompts for SESSION END
SESSION_END_PROMPTS = [
    MetacognitivePrompt(
        key="session_learning",
        text="What did you learn about your taste from this session?",
        timing="session_end",
        category="insight",
    ),
    MetacognitivePrompt(
        key="session_surprise",
        text="Was anything surprising in what you discovered?",
        timing="session_end",
        category="insight",
    ),
    MetacognitivePrompt(
        key="session_feeling",
        text="How do you feel about this depth of analysis? Energizing? Exhausting? Illuminating?",
        timing="session_end",
        category="awareness",
    ),
]

# Confidence calibration scale
CONFIDENCE_SCALE = {
    1: "Just guessing—not sure at all",
    2: "Uncertain—might change my mind",
    3: "Moderate—seems right but I'm open",
    4: "Confident—this feels solid",
    5: "Very confident—I know this about myself",
}


def get_random_prompt(timing: str, exclude_keys: list[str] = None) -> Optional[MetacognitivePrompt]:
    """Get a random metacognitive prompt for a specific timing."""
    if exclude_keys is None:
        exclude_keys = []

    if timing == "before_question":
        prompts = [p for p in BEFORE_QUESTION_PROMPTS if p.key not in exclude_keys]
    elif timing == "after_response":
        prompts = [p for p in AFTER_RESPONSE_PROMPTS if p.key not in exclude_keys]
    elif timing == "session_end":
        prompts = [p for p in SESSION_END_PROMPTS if p.key not in exclude_keys]
    else:
        return None

    if prompts:
        return random.choice(prompts)
    return None


def get_phase_transition_prompt(from_phase: str, to_phase: str) -> Optional[MetacognitivePrompt]:
    """Get a prompt for transitioning between phases."""
    key = f"{from_phase}_to_{to_phase}"
    prompts = PHASE_TRANSITION_PROMPTS.get(key, [])
    if prompts:
        return prompts[0]
    return None


def get_confidence_description(level: int) -> str:
    """Get the description for a confidence level."""
    return CONFIDENCE_SCALE.get(level, "Unknown")


# Pattern reflection prompts (shown after pattern detection)
PATTERN_REFLECTION_PROMPTS = [
    "You've identified patterns in {count} films now. What surprises you about what you're discovering?",
    "Your responses suggest you value {element}. Does that resonate, or does it feel incomplete?",
    "Three of your favorite moments involved {pattern}. Interesting pattern or coincidence?",
    "I notice you keep mentioning {element}. Is this something you've always known about yourself?",
]


def get_pattern_reflection(count: int = None, element: str = None, pattern: str = None) -> str:
    """Get a pattern reflection prompt with variables filled in."""
    if count is not None:
        return PATTERN_REFLECTION_PROMPTS[0].format(count=count)
    elif element is not None:
        return random.choice([
            PATTERN_REFLECTION_PROMPTS[1],
            PATTERN_REFLECTION_PROMPTS[3],
        ]).format(element=element)
    elif pattern is not None:
        return PATTERN_REFLECTION_PROMPTS[2].format(pattern=pattern)
    else:
        return PATTERN_REFLECTION_PROMPTS[0].format(count="several")
