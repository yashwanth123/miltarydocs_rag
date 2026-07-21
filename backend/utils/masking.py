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

JUNK_MARKERS = (
    "source: http://assist.dla.mil",
    "downloaded:",
    "check the source to verify that this is the current version",
)


def is_low_quality_chunk(text: str) -> bool:
    cleaned = text.strip()
    if len(cleaned) < 80:
        return True

    lowered = cleaned.lower()
    marker_hits = sum(1 for marker in JUNK_MARKERS if marker in lowered)
    if marker_hits >= 2:
        return True
    if marker_hits == 1 and len(cleaned) < 220:
        return True

    return False


def filter_documents(documents: list) -> list:
    filtered = []
    for doc in documents:
        content = doc.page_content if hasattr(doc, "page_content") else str(doc)
        if not is_low_quality_chunk(content):
            filtered.append(doc)
    return filtered


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
                "branch": metadata.get("branch"),
                "topic": metadata.get("topic"),
                "title": metadata.get("title"),
                "source_url": metadata.get("source_url"),
            }
        )
    return results
