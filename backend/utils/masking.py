import re
from typing import Iterable

DEFAULT_PATTERNS: list[tuple[str, str]] = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN REDACTED]"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[EMAIL REDACTED]"),
    (r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s-]?\d{4}", "[PHONE REDACTED]"),
    (
        r"\b(?:TOP\s+SECRET|SECRET|CONFIDENTIAL|UNCLASSIFIED(?:\s*//\s*FOUO)?)\b",
        "[CLASSIFICATION REDACTED]",
    ),
    (r"\b[A-Z]{2}\d{6,}\b", "[UNIT-ID REDACTED]"),
]


def mask_text(text: str, enabled: bool = True, patterns: Iterable[tuple[str, str]] | None = None) -> str:
    if not enabled or not text:
        return text

    masked = text
    for pattern, replacement in patterns or DEFAULT_PATTERNS:
        masked = re.sub(pattern, replacement, masked, flags=re.IGNORECASE)
    return masked


def mask_documents(documents: list, enabled: bool = True) -> list[dict]:
    results = []
    for doc in documents:
        content = doc.page_content if hasattr(doc, "page_content") else str(doc)
        metadata = dict(getattr(doc, "metadata", {}) or {})
        results.append(
            {
                "content": mask_text(content, enabled=enabled),
                "source": metadata.get("source", "unknown"),
                "page": metadata.get("page"),
            }
        )
    return results
