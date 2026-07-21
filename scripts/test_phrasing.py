"""Smoke tests for natural-language query handling."""

from backend.services.embedding_service import ask_question
from backend.services.query_intent import Intent, classify_intent

PHRASING_CASES = [
    ("what is the chain of command", Intent.CHAIN_OF_COMMAND),
    ("explain hierarchy in military", Intent.CHAIN_OF_COMMAND),
    ("who reports to whom", Intent.CHAIN_OF_COMMAND),
    ("give me an overview of the docs", Intent.SUMMARIZE),
    ("brief me on the documents", Intent.SUMMARIZE),
    ("mil-std references", Intent.STANDARDS),
    ("what can you help with", Intent.HELP),
    ("how does this work", Intent.HELP),
    ("hi", Intent.GREETING),
    ("whats this about", Intent.HELP),
]


def test_intent_classification() -> None:
    for question, expected in PHRASING_CASES:
        actual = classify_intent(question)
        assert actual == expected, f"{question!r} -> {actual}, expected {expected}"


def test_answers_are_substantive() -> None:
    for question, _intent in PHRASING_CASES:
        result = ask_question(question)
        assert len(result["answer"]) >= 40, f"Answer too short for {question!r}"
        assert "intent" in result


def test_out_of_scope_personal_questions() -> None:
    result = ask_question("who am i")
    assert result["intent"] == "out_of_scope"
    assert "military documents" in result["answer"].lower()


if __name__ == "__main__":
    test_intent_classification()
    test_answers_are_substantive()
    test_out_of_scope_personal_questions()
    print("All phrasing tests passed.")
