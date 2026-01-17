"""Tests for the question bank and scaffolding system."""

import pytest

from ktt.questions.bank import (
    get_questions_for_phase,
    get_question,
    format_question,
    ALL_QUESTIONS,
)
from ktt.questions.scaffolds import (
    get_scaffold_level,
    QuestionSequencer,
    HEAVY_SCAFFOLD,
    MEDIUM_SCAFFOLD,
    LIGHT_SCAFFOLD,
)
from ktt.questions.followups import (
    analyze_response,
    calculate_specificity_score,
    should_accept_response,
)


class TestQuestionBank:
    """Tests for the question bank."""

    def test_all_questions_have_required_fields(self):
        """Every question should have key, text, phase, and category."""
        for key, question in ALL_QUESTIONS.items():
            assert question.key == key
            assert question.text
            assert question.phase in ["planning", "monitoring", "evaluation"]
            assert question.category

    def test_get_questions_for_phase(self):
        """Should return questions for each phase."""
        for phase in ["planning", "monitoring", "evaluation"]:
            questions = get_questions_for_phase(phase)
            assert len(questions) > 0
            assert all(q.phase == phase for q in questions)

    def test_format_question_replaces_movie(self):
        """Format question should insert movie title."""
        question = get_question("first_memory")
        formatted = format_question(question, "Blade Runner")
        assert "Blade Runner" in formatted
        assert "{movie}" not in formatted


class TestScaffolding:
    """Tests for scaffolding levels."""

    def test_scaffold_level_progression(self):
        """Scaffolding should decrease with more sessions."""
        assert get_scaffold_level(1).level == 1  # Heavy
        assert get_scaffold_level(3).level == 1  # Still heavy
        assert get_scaffold_level(5).level == 2  # Medium
        assert get_scaffold_level(10).level == 3  # Light

    def test_heavy_scaffold_shows_everything(self):
        """Heavy scaffold should show all support."""
        assert HEAVY_SCAFFOLD.show_hints
        assert HEAVY_SCAFFOLD.show_examples
        assert HEAVY_SCAFFOLD.provide_starters
        assert HEAVY_SCAFFOLD.validate_responses

    def test_light_scaffold_minimal_support(self):
        """Light scaffold should be minimal."""
        assert not LIGHT_SCAFFOLD.show_hints
        assert not LIGHT_SCAFFOLD.show_examples
        assert not LIGHT_SCAFFOLD.provide_starters
        assert not LIGHT_SCAFFOLD.validate_responses


class TestAntiGeneric:
    """Tests for anti-generic detection."""

    def test_detects_vague_acting_response(self):
        """Should flag 'good acting' as vague."""
        # Use a longer response to test acting-specific detection
        analysis = analyze_response("I really enjoyed the film because the acting was good throughout the entire movie.")
        assert analysis.is_vague
        assert analysis.vagueness_type == "acting"
        assert len(analysis.suggested_follow_ups) > 0

    def test_detects_short_response(self):
        """Should flag very short responses."""
        analysis = analyze_response("I liked it.")
        assert analysis.is_vague
        assert analysis.vagueness_type == "too_short"

    def test_accepts_specific_response(self):
        """Should accept detailed, specific responses."""
        response = (
            "The scene where she walks into the empty apartment and stands "
            "there in silence, with dust floating in the light from the window - "
            "that moment captured the feeling of returning to a place that used "
            "to be home but isn't anymore. The way the camera held on her face "
            "as her expression shifted from hope to resignation told the whole story."
        )
        analysis = analyze_response(response)
        assert not analysis.is_vague or analysis.specificity_score >= 0.5

    def test_specificity_score_range(self):
        """Specificity score should be between 0 and 1."""
        test_responses = [
            "Good.",
            "It was interesting.",
            "The cinematography in the opening sequence used natural light.",
            "When the camera slowly pushed in on his face as he read the letter, "
            "you could see his expression shift from confusion to devastation.",
        ]

        for response in test_responses:
            score = calculate_specificity_score(response)
            assert 0 <= score <= 1

    def test_accept_after_max_attempts(self):
        """Should accept vague response after max attempts."""
        analysis = analyze_response("It was good.")
        assert not should_accept_response(analysis, 0)
        assert not should_accept_response(analysis, 1)
        assert should_accept_response(analysis, 3)  # Max attempts
