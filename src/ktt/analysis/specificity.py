"""Response specificity scoring for Know Thy Taste."""

from __future__ import annotations

import re
from typing import Optional


def calculate_specificity_score(response: str) -> float:
    """
    Calculate a specificity score for a response (0-1).

    Higher scores indicate more specific, detailed responses.
    """
    if not response or not response.strip():
        return 0.0

    score = 0.5  # Start at neutral

    # Length factors
    word_count = len(response.split())
    if word_count < 10:
        score -= 0.2
    elif word_count > 50:
        score += 0.1
    elif word_count > 100:
        score += 0.15

    # Positive indicators (increase score)
    positive_patterns = [
        (r"\bwhen\b.*\b(was|were|did)\b", 0.08),  # Temporal specificity
        (r"\bthe scene where\b|\bin the scene\b", 0.12),  # Scene reference
        (r"\bspecifically\b|\bexactly\b|\bprecisely\b", 0.08),
        (r"\bi remember\b|\bi recall\b", 0.08),  # Memory marker
        (r"\bthe moment\b|\bthat moment\b", 0.1),  # Moment reference
        (r'"[^"]{5,}?"', 0.12),  # Quoted dialogue (min 5 chars)
        (r"'[^']{5,}?'", 0.1),  # Single-quoted text
        (r"\bfirst\b.*\bthen\b|\bafter\b.*\bbefore\b", 0.08),  # Sequence
        (r"\b(face|eyes|hands|voice|expression)\b", 0.08),  # Body/performance
        (r"\b(shot|frame|cut|angle|camera)\b", 0.1),  # Technical terms
        (r"\b(lighting|color|shadow|contrast)\b", 0.08),  # Visual terms
        (r"\b(score|soundtrack|music|sound|silence)\b", 0.06),  # Audio terms
        (r"\bbecause\b", 0.06),  # Causal reasoning
        (r"\bfor example\b|\bfor instance\b", 0.1),  # Examples
        (r"\b(felt|feeling|emotion)\b.*\b(when|during|as)\b", 0.08),  # Emotional specificity
    ]

    for pattern, bonus in positive_patterns:
        if re.search(pattern, response, re.IGNORECASE):
            score += bonus

    # Negative indicators (decrease score)
    negative_patterns = [
        (r"\bkind of\b|\bsort of\b", -0.08),  # Hedging
        (r"\bi guess\b|\bmaybe\b|\bprobably\b", -0.08),  # Uncertainty
        (r"\bin general\b|\boverall\b|\bmostly\b", -0.1),  # Generalization
        (r"\bjust\b.*\breally\b|\breally\b.*\bjust\b", -0.08),  # Filler
        (r"\bgood\b|\bgreat\b|\bnice\b(?! [a-z]+ because)", -0.06),  # Generic praise
        (r"\binteresting\b(?! because)(?! in that)", -0.06),  # Vague positive
        (r"\bi don't know\b|\bi'm not sure\b", -0.1),  # Explicit uncertainty
    ]

    for pattern, penalty in negative_patterns:
        if re.search(pattern, response, re.IGNORECASE):
            score += penalty

    # Sentence variety bonus
    sentences = re.split(r'[.!?]+', response)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) >= 3:
        score += 0.05

    # Clamp to 0-1
    return max(0.0, min(1.0, score))


def extract_specific_elements(response: str) -> list[str]:
    """Extract specific elements mentioned in a response."""
    elements = []

    # Technical elements
    technical_patterns = [
        (r"\b(cinematography|lighting|framing|composition)\b", "visual"),
        (r"\b(score|soundtrack|music|sound design)\b", "audio"),
        (r"\b(editing|cuts?|pacing|rhythm)\b", "editing"),
        (r"\b(dialogue|script|writing)\b", "writing"),
        (r"\b(performance|acting|delivery)\b", "performance"),
        (r"\b(color|palette|tone)\b", "color"),
    ]

    for pattern, category in technical_patterns:
        if re.search(pattern, response, re.IGNORECASE):
            elements.append(category)

    # Thematic elements (simplified extraction)
    thematic_patterns = [
        (r"\b(loss|grief|mourning)\b", "loss"),
        (r"\b(love|romance|relationship)\b", "love"),
        (r"\b(isolation|loneliness|alone)\b", "isolation"),
        (r"\b(hope|redemption|healing)\b", "hope"),
        (r"\b(nostalgia|memory|past)\b", "nostalgia"),
        (r"\b(identity|self|who I am)\b", "identity"),
        (r"\b(family|parent|child)\b", "family"),
        (r"\b(mortality|death|dying)\b", "mortality"),
    ]

    for pattern, theme in thematic_patterns:
        if re.search(pattern, response, re.IGNORECASE):
            elements.append(f"theme:{theme}")

    return list(set(elements))


def get_specificity_feedback(score: float) -> Optional[str]:
    """Get feedback message based on specificity score."""
    if score >= 0.7:
        return None  # Good response, no feedback needed
    elif score >= 0.5:
        return "That's a good start. Can you add a specific example or moment?"
    elif score >= 0.3:
        return "Try to be more specific. Describe what you saw, heard, or felt in detail."
    else:
        return "I need more detail. Can you describe a specific scene or moment?"
