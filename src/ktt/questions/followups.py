"""Anti-generic detection and follow-up question generation.

Detects vague responses and provides targeted follow-ups to elicit specificity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class VaguePattern:
    """A pattern that indicates a vague response."""
    pattern: str  # regex pattern
    category: str  # what type of vagueness
    follow_ups: list[str]  # follow-up questions to ask


# Patterns that indicate vague responses
VAGUE_PATTERNS = [
    VaguePattern(
        pattern=r"\bgood acting\b|\bgreat acting\b|\bacting was good\b",
        category="acting",
        follow_ups=[
            "Which actor specifically?",
            "Can you describe a moment where their performance stood out?",
            "What exactly were they doing that worked?",
            "How was their approach different from what you typically see?",
        ],
    ),
    VaguePattern(
        pattern=r"\binteresting\b(?! because)(?! in that)(?! how)",
        category="vague_positive",
        follow_ups=[
            "What made it interesting, specifically?",
            "Interesting compared to what?",
            "Can you point to the exact moment that felt interesting?",
            "Interesting in what way—surprising? Unusual? Thought-provoking?",
        ],
    ),
    VaguePattern(
        pattern=r"\bbeautiful cinematography\b|\bgreat cinematography\b|\bvisually stunning\b",
        category="cinematography",
        follow_ups=[
            "Can you describe one specific shot that struck you?",
            "Was it the framing, the lighting, the movement, or something else?",
            "What made it beautiful—the composition, colors, or mood?",
            "Close your eyes and describe one image from the film.",
        ],
    ),
    VaguePattern(
        pattern=r"\bgreat soundtrack\b|\bgood music\b|\bmusic was great\b|\bamazing score\b",
        category="music",
        follow_ups=[
            "Can you hum or describe a specific piece from the score?",
            "When in the film did the music most affect you?",
            "What did the music add that wouldn't be there without it?",
            "Was it the melody, the instruments, or how it interacted with the scene?",
        ],
    ),
    VaguePattern(
        pattern=r"\bwell written\b|\bgood writing\b|\bgreat dialogue\b",
        category="writing",
        follow_ups=[
            "Can you quote or paraphrase a line that stuck with you?",
            "What made the writing effective—naturalistic? Witty? Poetic?",
            "Was there a conversation or monologue that particularly worked?",
            "How would you describe the voice of this screenplay?",
        ],
    ),
    VaguePattern(
        pattern=r"\bi liked it\b|\bit was good\b|\treally enjoyed it\b",
        category="generic_positive",
        follow_ups=[
            "What specifically did you like about it?",
            "If you had to pick one element that made it work, what would it be?",
            "What kept you engaged?",
            "What would you tell a friend about why they should watch it?",
        ],
    ),
    VaguePattern(
        pattern=r"\bpowerful\b(?! because)|\bmoving\b(?! because)|\bemotional\b(?! because)",
        category="emotional_vague",
        follow_ups=[
            "What specifically made it powerful/moving?",
            "Which scene hit you the hardest?",
            "What were you feeling in that moment?",
            "Was it the content, the execution, or both?",
        ],
    ),
    VaguePattern(
        pattern=r"\bthe ending\b(?! where)(?! when)|\bthe beginning\b(?! where)(?! when)",
        category="structural_vague",
        follow_ups=[
            "What about the ending specifically?",
            "Describe the moment in the ending that affected you.",
            "What did the ending make you feel, and why?",
            "How did it land differently than you expected?",
        ],
    ),
    VaguePattern(
        pattern=r"\brelatable\b|\brelateable\b",
        category="relatable",
        follow_ups=[
            "What specifically did you relate to?",
            "Was it a character, a situation, or a feeling?",
            "What from your own experience connected to this?",
            "Can you describe the moment you felt that connection?",
        ],
    ),
    VaguePattern(
        pattern=r"\bperfect\b|\bflawless\b|\bmasterpiece\b",
        category="hyperbole",
        follow_ups=[
            "What made it so effective for you?",
            "Which elements came together particularly well?",
            "Was there anything that almost didn't work but somehow did?",
            "What sets it apart from other films you've loved?",
        ],
    ),
]

# Short response threshold
MIN_RESPONSE_LENGTH = 50  # characters


@dataclass
class VagueAnalysis:
    """Result of analyzing a response for vagueness."""
    is_vague: bool
    vagueness_type: Optional[str]
    suggested_follow_ups: list[str]
    specificity_score: float  # 0-1, where 1 is highly specific


def analyze_response(response: str) -> VagueAnalysis:
    """Analyze a response for vagueness and generate follow-ups."""
    response_lower = response.lower().strip()

    # Check for short responses
    if len(response) < MIN_RESPONSE_LENGTH:
        return VagueAnalysis(
            is_vague=True,
            vagueness_type="too_short",
            suggested_follow_ups=[
                "Can you elaborate on that?",
                "Tell me more—what specifically do you mean?",
                "I'd like to understand this better. Can you expand?",
            ],
            specificity_score=0.2,
        )

    # Check for pattern matches
    for pattern in VAGUE_PATTERNS:
        if re.search(pattern.pattern, response_lower):
            return VagueAnalysis(
                is_vague=True,
                vagueness_type=pattern.category,
                suggested_follow_ups=pattern.follow_ups,
                specificity_score=0.3,
            )

    # Calculate specificity score based on indicators
    score = calculate_specificity_score(response)

    if score < 0.5:
        return VagueAnalysis(
            is_vague=True,
            vagueness_type="low_specificity",
            suggested_follow_ups=[
                "Can you be more specific? Describe a particular moment.",
                "Give me the details—what exactly happened in that scene?",
                "I want to see it through your eyes. Describe it like I haven't seen the film.",
            ],
            specificity_score=score,
        )

    return VagueAnalysis(
        is_vague=False,
        vagueness_type=None,
        suggested_follow_ups=[],
        specificity_score=score,
    )


def calculate_specificity_score(response: str) -> float:
    """Calculate a specificity score for a response (0-1)."""
    score = 0.5  # Start at neutral

    # Positive indicators (increase score)
    positive_indicators = [
        (r"\bwhen\b.*\bwas\b", 0.1),  # Temporal specificity
        (r"\bthe scene where\b", 0.15),  # Scene reference
        (r"\bspecifically\b", 0.1),
        (r"\bexactly\b", 0.1),
        (r"\bi remember\b", 0.1),  # Memory marker
        (r"\bthe moment\b", 0.1),  # Moment reference
        (r'"[^"]+?"', 0.15),  # Quoted dialogue
        (r'\d+', 0.05),  # Numbers (often indicate specificity)
        (r"\bfirst\b|\bthen\b|\bafter\b|\bbefore\b", 0.1),  # Sequence words
        (r"\b(face|eyes|hands|voice)\b", 0.1),  # Body/performance details
        (r"\b(shot|frame|cut|angle)\b", 0.1),  # Technical terms
    ]

    for pattern, bonus in positive_indicators:
        if re.search(pattern, response, re.IGNORECASE):
            score += bonus

    # Negative indicators (decrease score)
    negative_indicators = [
        (r"\bkind of\b|\bsort of\b", -0.1),
        (r"\bi guess\b|\bmaybe\b", -0.1),
        (r"\bin general\b|\boverall\b", -0.1),
        (r"\bjust\b.*\breally\b", -0.1),  # Hedging
    ]

    for pattern, penalty in negative_indicators:
        if re.search(pattern, response, re.IGNORECASE):
            score += penalty

    # Length bonus (longer responses tend to be more specific)
    if len(response) > 200:
        score += 0.1
    if len(response) > 400:
        score += 0.1

    # Clamp to 0-1
    return max(0.0, min(1.0, score))


def get_follow_up_for_attempt(analysis: VagueAnalysis, attempt: int) -> Optional[str]:
    """Get the appropriate follow-up question based on attempt number."""
    if not analysis.suggested_follow_ups:
        return None

    # Cycle through follow-ups, getting more direct with each attempt
    idx = min(attempt, len(analysis.suggested_follow_ups) - 1)
    return analysis.suggested_follow_ups[idx]


# Maximum follow-up attempts before accepting response
MAX_FOLLOW_UP_ATTEMPTS = 3


def should_accept_response(analysis: VagueAnalysis, attempt_count: int) -> bool:
    """Determine if we should accept the response despite vagueness."""
    if not analysis.is_vague:
        return True

    # Accept after max attempts
    if attempt_count >= MAX_FOLLOW_UP_ATTEMPTS:
        return True

    # Accept if score is borderline and we've tried once
    if analysis.specificity_score >= 0.4 and attempt_count >= 1:
        return True

    return False


# Encouragement messages for good responses
ENCOURAGEMENT_MESSAGES = [
    "That's exactly the kind of detail that helps.",
    "Good—I can see that scene now.",
    "That specificity is valuable.",
    "This is helpful for understanding your taste.",
]

# Messages for accepting despite vagueness
ACCEPTANCE_MESSAGES = [
    "I'll note that as you've described it.",
    "Sometimes that's as specific as a feeling gets. Noted.",
    "Let's move on—we can always come back to this.",
]


def get_encouragement() -> str:
    """Get a random encouragement message."""
    import random
    return random.choice(ENCOURAGEMENT_MESSAGES)


def get_acceptance_message() -> str:
    """Get a message for accepting a vague response."""
    import random
    return random.choice(ACCEPTANCE_MESSAGES)
