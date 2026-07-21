import re
from collections import Counter

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "what", "who", "why", "how",
    "when", "where", "can", "could", "would", "should", "about", "this", "that",
    "these", "those", "and", "or", "for", "with", "from", "into", "your", "you",
    "me", "my", "i", "it", "in", "on", "at", "to", "of", "do", "does", "did",
}


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in STOPWORDS
    }


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [part.strip() for part in parts if len(part.strip()) > 40]


def is_meta_question(question: str) -> bool:
    q = question.lower().strip()
    patterns = (
        "what can i ask",
        "what should i ask",
        "what is this about",
        "what is this",
        "help me",
        "how does this work",
        "hello",
        "hi there",
    )
    return any(pattern in q for pattern in patterns) or q in {"hi", "hello", "help"}


def build_meta_answer(question: str, documents: list, document_count: int) -> str:
    sources = sorted(
        {
            doc.metadata.get("source", "unknown")
            for doc in documents
            if getattr(doc, "metadata", None)
        }
    )

    if "what can i ask" in question.lower() or "what should i ask" in question.lower():
        file_hint = ", ".join(sources[:3]) if sources else "your uploaded files"
        return (
            f"I searched {document_count} indexed chunks from documents like {file_hint}.\n\n"
            "Try questions such as:\n"
            "• What is the military chain of command?\n"
            "• Summarize the main topics in the indexed documents\n"
            "• What skills or experience are listed in the resume?\n"
            "• Which MIL-STD or military references are mentioned?"
        )

    if "what is this about" in question.lower() or question.lower() in {"what is this", "what's this about"}:
        if sources:
            return (
                f"These documents cover material from: {', '.join(sources)}.\n\n"
                "Based on the indexed content, you can ask for summaries, definitions, "
                "chain-of-command details, referenced standards (MIL-STD), or specific facts "
                "from any uploaded file."
            )
        return (
            f"This assistant searches {document_count} indexed document chunks and answers from retrieved passages.\n\n"
            "Ask specific questions about topics, summaries, people, skills, or standards in your files."
        )

    if sources:
        return (
            f"This assistant answers questions from your indexed documents ({document_count} chunks).\n\n"
            f"Currently indexed files include: {', '.join(sources)}.\n\n"
            "Ask about topics, summaries, definitions, or specific facts contained in those files."
        )


def score_sentence(sentence: str, question_tokens: set[str]) -> float:
    sentence_tokens = _tokens(sentence)
    if not sentence_tokens:
        return 0.0

    overlap = len(question_tokens & sentence_tokens)
    overlap_score = overlap / max(len(question_tokens), 1)
    length_penalty = 1.0 if len(sentence) < 320 else 0.85
    return overlap_score * length_penalty


def build_extractive_answer(question: str, documents: list) -> str:
    question_tokens = _tokens(question)
    ranked_sentences: list[tuple[float, str, str]] = []

    for doc in documents:
        source = doc.metadata.get("source", "unknown") if getattr(doc, "metadata", None) else "unknown"
        for sentence in _split_sentences(doc.page_content):
            score = score_sentence(sentence, question_tokens)
            if score > 0:
                ranked_sentences.append((score, sentence, source))

    ranked_sentences.sort(key=lambda item: item[0], reverse=True)

    chosen: list[str] = []
    seen: set[str] = set()
    for _, sentence, _source in ranked_sentences:
        normalized = sentence.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        chosen.append(sentence)
        if len(chosen) >= 4:
            break

    if not chosen:
        for doc in documents[:2]:
            snippet = doc.page_content.strip().split("\n")[0][:260]
            if snippet:
                chosen.append(snippet)
        if not chosen:
            return "I could not find enough relevant content to answer that question."

    if len(chosen) == 1:
        return chosen[0]

    return "\n\n".join(f"• {sentence}" for sentence in chosen)


def is_weak_model_answer(answer: str) -> bool:
    cleaned = answer.strip()
    if not cleaned:
        return True
    if len(cleaned) < 24:
        return True
    if cleaned.lower() in {"the military document", "military document", "document"}:
        return True
    if "[PHONE REDACTED]" in cleaned or "[EMAIL REDACTED]" in cleaned:
        return True
    return False
