import re

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "what", "who", "why", "how",
    "when", "where", "can", "could", "would", "should", "about", "this", "that",
    "these", "those", "and", "or", "for", "with", "from", "into", "your", "you",
    "me", "my", "i", "it", "in", "on", "at", "to", "of", "do", "does", "did",
}

HEADER_ONLY_PATTERNS = (
    r"^military chain of command overview$",
    r"^military references cited in this document:?$",
    r"^contact example .*$",
    r"^classification reminder:?$",
    r"^operational note:?$",
    r"^key principles:?$",
    r"^example chain of command .*$",
)


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in STOPWORDS
    }


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    sentences = []
    for part in parts:
        cleaned = part.strip(" •-\t")
        if len(cleaned) >= 50 and not is_header_only_sentence(cleaned):
            sentences.append(cleaned)
    return sentences


def is_header_only_sentence(sentence: str) -> bool:
    cleaned = sentence.strip().lower()
    if any(re.match(pattern, cleaned) for pattern in HEADER_ONLY_PATTERNS):
        return True
    if len(cleaned) < 70 and cleaned.endswith(":"):
        return True
    if len(cleaned) < 55 and not any(ch in cleaned for ch in ".!?"):
        return True
    return False


def is_vague_question(question: str) -> bool:
    q = question.lower().strip()
    words = re.findall(r"[a-z0-9']+", q)

    if len(words) <= 1:
        return True
    if len(words) == 2 and len(q) < 16:
        return True
    if q in {"whats this", "what's this", "what is this", "where", "who", "why", "how"}:
        return True
    return False


def is_meta_question(question: str) -> bool:
    q = question.lower().strip()
    patterns = (
        "what can i ask",
        "what should i ask",
        "what is this about",
        "what is this",
        "whats this",
        "what's this",
        "help me",
        "how does this work",
        "hello",
        "hi there",
    )
    return any(pattern in q for pattern in patterns) or q in {"hi", "hello", "help"}


def is_summarize_intent(question: str) -> bool:
    q = question.lower()
    return any(word in q for word in ("summarize", "summary", "overview", "main topics", "key points"))


def is_identity_question(question: str) -> bool:
    q = question.lower()
    return "who am i" in q or "who is yashwanth" in q or q.startswith("who is ")


def build_vague_answer() -> str:
    return (
        "That question is too broad for document search.\n\n"
        "Please ask something specific, for example:\n"
        "• What is the military chain of command?\n"
        "• Summarize the sample chain-of-command document\n"
        "• What skills are mentioned in my resume?\n"
        "• Which MIL-STD references appear in the documents?"
    )


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
            f"I can search {document_count} indexed chunks from {file_hint}.\n\n"
            "Strong questions look like:\n"
            "• What is the military chain of command?\n"
            "• Summarize the indexed documents\n"
            "• What experience is listed in the resume?\n"
            "• Which MIL-STD standards are referenced?"
        )

    if any(p in question.lower() for p in ("what is this about", "what is this", "whats this", "what's this")):
        if sources:
            return (
                f"Your indexed library currently includes: {', '.join(sources)}.\n\n"
                "Ask about facts, summaries, people, standards, or procedures contained in those files."
            )

    if sources:
        return (
            f"This assistant searches {document_count} chunks across {', '.join(sources)}.\n\n"
            "Ask a focused question about content inside those documents."
        )

    return build_vague_answer()


def build_summary_answer(documents: list) -> str:
    ranked: list[tuple[float, str]] = []

    for doc in documents:
        for sentence in _split_sentences(doc.page_content):
            score = min(len(sentence), 220) / 220
            if any(token in sentence.lower() for token in ("president", "command", "orders", "mil-std", "principle", "experience", "engineer")):
                score += 0.35
            ranked.append((score, sentence))

    ranked.sort(key=lambda item: item[0], reverse=True)

    chosen: list[str] = []
    seen: set[str] = set()
    for _, sentence in ranked:
        key = sentence.lower()
        if key in seen:
            continue
        seen.add(key)
        chosen.append(sentence)
        if len(chosen) >= 5:
            break

    if not chosen:
        return (
            "I found indexed content, but not enough substantive text to build a summary. "
            "Try adding richer PDF, DOCX, or TXT files to data/ and re-running ingestion."
        )

    intro = "Here is a concise summary based on your indexed documents:\n\n"
    return intro + "\n\n".join(f"• {sentence}" for sentence in chosen)


def build_identity_answer(documents: list) -> str:
    name_patterns = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b")
    role_patterns = re.compile(r"\b(engineer|developer|scientist|manager|analyst|experience|skills)\b", re.I)

    hits: list[str] = []
    for doc in documents:
        for sentence in _split_sentences(doc.page_content):
            if role_patterns.search(sentence) or "resume" in doc.metadata.get("source", "").lower():
                hits.append(sentence)
            elif name_patterns.search(sentence) and len(sentence) > 40:
                hits.append(sentence)

    if hits:
        unique = []
        seen = set()
        for hit in hits[:4]:
            if hit.lower() not in seen:
                seen.add(hit.lower())
                unique.append(hit)
        return (
            "Based on the indexed documents, here is what I found about you:\n\n"
            + "\n\n".join(f"• {line}" for line in unique)
        )

    return (
        "I don't see personal identity details in the currently indexed documents.\n\n"
        "If you want answers about yourself, add your resume PDF or DOCX to data/ and run:\n"
        "python scripts/ingest_documents.py --reset"
    )


def score_sentence(sentence: str, question_tokens: set[str]) -> float:
    if is_header_only_sentence(sentence):
        return 0.0

    sentence_tokens = _tokens(sentence)
    if not sentence_tokens:
        return 0.0

    overlap = len(question_tokens & sentence_tokens)
    if not question_tokens:
        return 0.0

    overlap_score = overlap / max(len(question_tokens), 1)
    if overlap == 0:
        return 0.0

    length_bonus = min(len(sentence), 180) / 180
    return overlap_score * 0.75 + length_bonus * 0.25


def build_extractive_answer(question: str, documents: list) -> str:
    question_tokens = _tokens(question)
    ranked_sentences: list[tuple[float, str]] = []

    for doc in documents:
        for sentence in _split_sentences(doc.page_content):
            score = score_sentence(sentence, question_tokens)
            if score > 0.15:
                ranked_sentences.append((score, sentence))

    ranked_sentences.sort(key=lambda item: item[0], reverse=True)

    chosen: list[str] = []
    seen: set[str] = set()
    for _, sentence in ranked_sentences:
        normalized = sentence.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        chosen.append(sentence)
        if len(chosen) >= 4:
            break

    if not chosen:
        return build_vague_answer()

    if len(chosen) == 1:
        return chosen[0]

    return "\n\n".join(f"• {sentence}" for sentence in chosen)


def is_weak_model_answer(answer: str) -> bool:
    cleaned = answer.strip()
    if not cleaned or len(cleaned) < 24:
        return True
    if cleaned.lower() in {"the military document", "military document", "document"}:
        return True
    if "[PHONE REDACTED]" in cleaned or "[EMAIL REDACTED]" in cleaned:
        return True
    return False
