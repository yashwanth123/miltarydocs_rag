import re

from backend.services.query_intent import Intent, expand_tokens, normalize_question

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "what", "who", "why", "how",
    "when", "where", "can", "could", "would", "should", "about", "this", "that",
    "these", "those", "and", "or", "for", "with", "from", "into", "your", "you",
    "me", "my", "i", "it", "in", "on", "at", "to", "of", "do", "does", "did",
    "tell", "explain", "describe", "give", "show", "please",
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
    normalized = normalize_question(text)
    return {
        token
        for token in re.findall(r"[a-z0-9]+", normalized)
        if len(token) > 2 and token not in STOPWORDS
    }


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    sentences = []
    for part in parts:
        cleaned = part.strip(" •-\t")
        if len(cleaned) >= 45 and not is_header_only_sentence(cleaned):
            sentences.append(cleaned)
    return sentences


def _split_lines(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        cleaned = line.strip(" •-\t")
        if len(cleaned) >= 20 and not is_header_only_sentence(cleaned):
            lines.append(cleaned)
    return lines


def is_header_only_sentence(sentence: str) -> bool:
    cleaned = sentence.strip().lower()
    if any(re.match(pattern, cleaned) for pattern in HEADER_ONLY_PATTERNS):
        return True
    if len(cleaned) < 70 and cleaned.endswith(":"):
        return True
    if len(cleaned) < 50 and not any(ch in cleaned for ch in ".!?"):
        return True
    return False


def build_vague_answer(intent: Intent | None = None) -> str:
    if intent == Intent.UNKNOWN:
        return (
            "I need a bit more detail to search your documents effectively.\n\n"
            "Try asking in any of these ways:\n"
            "• Explain the chain of command\n"
            "• Give me a summary of the documents\n"
            "• What skills or experience are listed?\n"
            "• Which MIL-STD references are mentioned?"
        )

    return (
        "I couldn't find a strong match in the indexed content.\n\n"
        "Rephrase your question or try:\n"
        "• What is the military chain of command?\n"
        "• Summarize the indexed documents\n"
        "• What experience appears in the resume?\n"
        "• List the military standards referenced"
    )


def build_greeting_answer(document_count: int) -> str:
    return (
        f"Hello. I am ready to answer questions from your indexed documents ({document_count} chunks).\n\n"
        "You can ask naturally — for example:\n"
        "• Explain the chain of command\n"
        "• Brief me on the documents\n"
        "• What skills are mentioned?\n"
        "• What can you help me with?"
    )


def build_meta_answer(question: str, documents: list, document_count: int) -> str:
    sources = sorted(
        {
            doc.metadata.get("source", "unknown")
            for doc in documents
            if getattr(doc, "metadata", None)
        }
    )
    file_hint = ", ".join(sources[:4]) if sources else "your uploaded files"

    return (
        f"I search {document_count} chunks from {file_hint} and answer from retrieved passages.\n\n"
        "You can ask in many ways, such as:\n"
        "• Explain / describe / define …\n"
        "• Summarize / give overview / main points\n"
        "• Who am I / what is my experience\n"
        "• Chain of command / hierarchy / who reports to whom\n"
        "• MIL-STD / military standards referenced"
    )


def build_summary_answer(documents: list) -> str:
    ranked: list[tuple[float, str]] = []

    for doc in documents:
        for sentence in _split_sentences(doc.page_content):
            score = min(len(sentence), 220) / 220
            keywords = (
                "president", "command", "orders", "mil-std", "principle",
                "experience", "engineer", "responsibility", "delegation", "soldier",
            )
            if any(token in sentence.lower() for token in keywords):
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
        return build_vague_answer()

    return "Here is a concise summary based on your indexed documents:\n\n" + "\n\n".join(
        f"• {sentence}" for sentence in chosen
    )


def build_identity_answer(documents: list) -> str:
    role_patterns = re.compile(
        r"\b(engineer|developer|scientist|manager|analyst|experience|skills|machine learning|software)\b",
        re.I,
    )

    hits: list[str] = []
    for doc in documents:
        source = doc.metadata.get("source", "").lower() if getattr(doc, "metadata", None) else ""
        for sentence in _split_sentences(doc.page_content):
            if "resume" in source or role_patterns.search(sentence):
                hits.append(sentence)

    if hits:
        unique: list[str] = []
        seen: set[str] = set()
        for hit in hits[:5]:
            if hit.lower() not in seen:
                seen.add(hit.lower())
                unique.append(hit)
        return "Based on the indexed documents, here is what I found:\n\n" + "\n\n".join(
            f"• {line}" for line in unique
        )

    return (
        "I do not see personal profile details in the indexed documents yet.\n\n"
        "Add your resume PDF or DOCX to data/ and run:\n"
        "python scripts/ingest_documents.py --reset"
    )


def build_chain_of_command_answer(documents: list) -> str:
    bullets: list[str] = []
    seen: set[str] = set()

    for doc in documents:
        for line in _split_lines(doc.page_content):
            if re.match(r"^\d+\.\s+", line):
                if line.lower() not in seen:
                    seen.add(line.lower())
                    bullets.append(line)
            elif any(k in line.lower() for k in ("chain of command", "unity of command", "span of control", "delegation of authority", "orders flow", "accountability flows")):
                if line.lower() not in seen:
                    seen.add(line.lower())
                    bullets.append(line)

    if bullets:
        intro = "Here is the chain-of-command information found in your documents:\n\n"
        return intro + "\n\n".join(f"• {item.lstrip('•').strip()}" for item in bullets[:8])

    return build_extractive_answer("military chain of command authority responsibility", documents)


def build_skills_answer(documents: list) -> str:
    hits: list[str] = []
    seen: set[str] = set()

    skill_markers = ("skill", "experience", "technology", "engineer", "python", "machine learning", "developed", "built")

    for doc in documents:
        for sentence in _split_sentences(doc.page_content):
            lower = sentence.lower()
            if any(marker in lower for marker in skill_markers) and sentence.lower() not in seen:
                seen.add(sentence.lower())
                hits.append(sentence)

    if hits:
        return "Skills and experience mentioned in the documents:\n\n" + "\n\n".join(
            f"• {line}" for line in hits[:5]
        )

    return build_vague_answer()


def build_standards_answer(documents: list) -> str:
    hits: list[str] = []
    seen: set[str] = set()

    for doc in documents:
        refs = re.findall(r"MIL-[A-Z]+-\d+", doc.page_content)
        for ref in refs:
            if ref not in seen:
                seen.add(ref)
                hits.append(ref)
        for sentence in _split_sentences(doc.page_content):
            if "mil-" in sentence.lower() and sentence.lower() not in seen:
                seen.add(sentence.lower())
                hits.append(sentence)

    if hits:
        return "Military standards and references found:\n\n" + "\n\n".join(f"• {item}" for item in hits[:6])

    return "No MIL-STD or military reference identifiers were found in the indexed content."


def build_list_answer(question: str, documents: list) -> str:
    items: list[str] = []
    seen: set[str] = set()

    for doc in documents:
        for line in _split_lines(doc.page_content):
            if re.match(r"^\d+\.\s+|^[-•]\s+", line):
                cleaned = re.sub(r"^\d+\.\s+|^[-•]\s+", "", line).strip()
                if cleaned and cleaned.lower() not in seen:
                    seen.add(cleaned.lower())
                    items.append(cleaned)

    if items:
        return "Here are the listed items found in your documents:\n\n" + "\n\n".join(
            f"• {item}" for item in items[:10]
        )

    return build_extractive_answer(question, documents)


def score_sentence(sentence: str, question_tokens: set[str]) -> float:
    if is_header_only_sentence(sentence):
        return 0.0

    sentence_tokens = _tokens(sentence)
    if not sentence_tokens or not question_tokens:
        return 0.0

    expanded = expand_tokens(question_tokens)
    overlap = len(expanded & sentence_tokens)
    if overlap == 0:
        partial = sum(1 for q in expanded if any(q in s for s in sentence_tokens))
        if partial == 0:
            return 0.0
        overlap = partial * 0.5

    overlap_score = overlap / max(len(expanded), 1)
    length_bonus = min(len(sentence), 180) / 180
    return overlap_score * 0.75 + length_bonus * 0.25


def build_extractive_answer(question: str, documents: list) -> str:
    question_tokens = _tokens(question)
    ranked_sentences: list[tuple[float, str]] = []

    for doc in documents:
        for sentence in _split_sentences(doc.page_content):
            score = score_sentence(sentence, question_tokens)
            if score > 0.12:
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


def build_answer_for_intent(intent: Intent, question: str, documents: list, document_count: int) -> str:
    if intent == Intent.GREETING:
        return build_greeting_answer(document_count)
    if intent == Intent.HELP:
        return build_meta_answer(question, documents, document_count)
    if intent == Intent.SUMMARIZE:
        return build_summary_answer(documents)
    if intent == Intent.IDENTITY:
        return build_identity_answer(documents)
    if intent == Intent.CHAIN_OF_COMMAND:
        return build_chain_of_command_answer(documents)
    if intent == Intent.SKILLS:
        return build_skills_answer(documents)
    if intent == Intent.STANDARDS:
        return build_standards_answer(documents)
    if intent == Intent.LIST:
        return build_list_answer(question, documents)
    return build_extractive_answer(question, documents)


def is_weak_model_answer(answer: str) -> bool:
    cleaned = answer.strip()
    if not cleaned or len(cleaned) < 24:
        return True
    if cleaned.lower() in {"the military document", "military document", "document"}:
        return True
    if "[PHONE REDACTED]" in cleaned or "[EMAIL REDACTED]" in cleaned:
        return True
    return False
