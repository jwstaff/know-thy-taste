"""Question bank for Know Thy Taste.

Questions are organized by phase (Planning, Monitoring, Evaluation) and category.
Each question includes hints and example good responses.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Question:
    """A question in the bank."""
    key: str
    text: str
    phase: str  # "planning", "monitoring", "evaluation"
    category: str  # "sensory", "emotional", "narrative", "thematic", "technical"
    hint: Optional[str] = None
    example_good: Optional[str] = None
    example_vague: Optional[str] = None
    requires_specificity: bool = True


# PLANNING PHASE - What did you notice?
PLANNING_QUESTIONS = [
    Question(
        key="first_memory",
        text="Before we analyze this film, what's the first specific moment or scene that comes to mind when you think of {movie}?",
        phase="planning",
        category="sensory",
        hint="Try to recall a specific image, sound, or moment—not the plot summary.",
        example_good="The scene where she walks into the empty apartment and just stands there, looking at the dust floating in the light from the window.",
        example_vague="The ending was good.",
    ),
    Question(
        key="expectations",
        text="What were you hoping for or expecting when you started watching {movie}?",
        phase="planning",
        category="emotional",
        hint="Think about what drew you to watch it, what you anticipated.",
    ),
    Question(
        key="attention_focus",
        text="Can you identify one specific element you found yourself paying attention to while watching?",
        phase="planning",
        category="sensory",
        hint="Was it the dialogue? The faces? The colors? The music? What kept catching your eye or ear?",
    ),
    Question(
        key="initial_feeling",
        text="What did you feel immediately after the film ended, before you had time to think about it?",
        phase="planning",
        category="emotional",
        hint="Not what you think about it now—what was the raw, immediate feeling?",
    ),
    Question(
        key="watch_context",
        text="Where and how did you watch {movie}? Were you alone? What was your state of mind?",
        phase="planning",
        category="thematic",
        hint="Context shapes experience. Theater vs. laptop, alone vs. with someone, tired vs. alert.",
    ),
]

# MONITORING PHASE - How did you engage?
MONITORING_QUESTIONS = [
    Question(
        key="attention_captured",
        text="Think about a moment when your attention was most completely captured. What was happening in that exact scene?",
        phase="monitoring",
        category="sensory",
        hint="Describe it like you're setting up the scene for someone who hasn't seen it.",
        example_good="When the camera slowly pushed in on his face as he read the letter, and you could see his expression shift from confusion to devastation—no dialogue, just that face.",
        example_vague="The dramatic scenes were engaging.",
    ),
    Question(
        key="disconnection",
        text="Were there points where you felt disconnected or your mind wandered? What was happening when that occurred?",
        phase="monitoring",
        category="emotional",
        hint="It's valuable to identify what doesn't work for you too.",
    ),
    Question(
        key="predictions",
        text="Did you notice yourself making predictions about what would happen? Were they right?",
        phase="monitoring",
        category="narrative",
        hint="We're constantly predicting. What did you expect, and how did the film respond?",
    ),
    Question(
        key="comparisons",
        text="While watching, did you find yourself comparing this to other films, books, or experiences? To what?",
        phase="monitoring",
        category="thematic",
        hint="These automatic comparisons reveal your mental library and what patterns you recognize.",
    ),
    Question(
        key="physical_response",
        text="Did you have any physical responses? Tension, tears, laughter, leaning forward, looking away?",
        phase="monitoring",
        category="emotional",
        hint="Our bodies often respond before our minds catch up. What did yours do?",
    ),
    Question(
        key="rewatch_impulse",
        text="Were there moments you wanted to rewind or see again? Which ones?",
        phase="monitoring",
        category="sensory",
        hint="The urge to revisit something immediately is a strong signal.",
    ),
    Question(
        key="time_perception",
        text="How did time feel during the film? Did it fly by, drag, or did certain sections feel different?",
        phase="monitoring",
        category="narrative",
        hint="Time perception reveals engagement. When did the film earn your full presence?",
    ),
]

# EVALUATION PHASE - Why did it matter?
EVALUATION_QUESTIONS = [
    Question(
        key="emotional_impact",
        text="Looking back, what element had the most emotional impact on you—and what specifically about it?",
        phase="evaluation",
        category="emotional",
        hint="'The score' is too vague. Which part of the score? What did it do?",
        example_good="The recurring piano motif that played during her memories. The first few times it felt nostalgic, but by the end, when it played over her empty chair, it felt like loss.",
        example_vague="The emotional parts were moving.",
    ),
    Question(
        key="removal_test",
        text="If you removed one element (the score, the cinematography, the dialogue style, the lead performance), would your experience be fundamentally different? Which one?",
        phase="evaluation",
        category="technical",
        hint="This reveals what you consider essential to the film's effect.",
    ),
    Question(
        key="self_reflection",
        text="What does your reaction to this film tell you about what you value in storytelling?",
        phase="evaluation",
        category="thematic",
        hint="Step back. What does loving (or not loving) this film say about you?",
    ),
    Question(
        key="lasting_image",
        text="What image or moment do you think will stay with you longest? Why that one?",
        phase="evaluation",
        category="sensory",
        hint="Of everything in the film, what has lodged itself in your memory?",
    ),
    Question(
        key="recommendation",
        text="If you were to recommend this film to someone, what kind of person would appreciate it most? Why?",
        phase="evaluation",
        category="thematic",
        hint="Imagining the ideal audience reveals what you think the film offers.",
    ),
    Question(
        key="changed_view",
        text="Did this film change how you think about anything—films, life, a topic it addressed?",
        phase="evaluation",
        category="thematic",
        hint="Films can shift perspectives. Did this one move anything in you?",
    ),
    Question(
        key="craft_appreciation",
        text="Is there a specific craft element (editing, sound design, production design, etc.) that you noticed more than usual?",
        phase="evaluation",
        category="technical",
        hint="Sometimes a film teaches us to see filmmaking differently.",
    ),
    Question(
        key="narrative_structure",
        text="How did the structure of the story affect your experience? Did the way it was told enhance or diminish the material?",
        phase="evaluation",
        category="narrative",
        hint="Not just what happened, but how it was revealed to you.",
    ),
]

# Organize questions by phase
QUESTIONS_BY_PHASE = {
    "planning": PLANNING_QUESTIONS,
    "monitoring": MONITORING_QUESTIONS,
    "evaluation": EVALUATION_QUESTIONS,
}

# All questions indexed by key
ALL_QUESTIONS = {q.key: q for phase in QUESTIONS_BY_PHASE.values() for q in phase}


def get_questions_for_phase(phase: str) -> list[Question]:
    """Get all questions for a specific phase."""
    return QUESTIONS_BY_PHASE.get(phase, [])


def get_question(key: str) -> Optional[Question]:
    """Get a specific question by key."""
    return ALL_QUESTIONS.get(key)


def format_question(question: Question, movie_title: str) -> str:
    """Format a question with the movie title inserted."""
    return question.text.format(movie=movie_title)
