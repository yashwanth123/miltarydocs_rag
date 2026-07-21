import re
from pathlib import Path

DEFAULT_METADATA = {
    "branch": "general",
    "topic": "general",
    "doc_type": "guide",
    "source_url": "",
    "title": "",
}

BRANCH_ALIASES = {
    "air-force": "air_force",
    "air_force": "air_force",
    "coast-guard": "coast_guard",
    "coast_guard": "coast_guard",
    "space-force": "space_force",
    "space_force": "space_force",
    "army": "army",
    "navy": "navy",
    "marines": "marines",
    "general": "general",
}

TOPIC_FROM_NAME = {
    "joining": "joining",
    "meps": "meps",
    "ranks": "ranks",
    "pay": "ranks",
    "benefits": "benefits",
    "gi_bill": "benefits",
    "asvab": "asvab",
    "overview": "overview",
    "chain_of_command": "doctrine",
    "command": "doctrine",
}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    metadata = dict(DEFAULT_METADATA)
    body = text

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, flags=re.DOTALL)
    if not match:
        return metadata, body

    block = match.group(1)
    body = text[match.end() :]

    for line in block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip().strip('"').strip("'")
        if key in DEFAULT_METADATA:
            metadata[key] = value

    if metadata["branch"] in BRANCH_ALIASES:
        metadata["branch"] = BRANCH_ALIASES[metadata["branch"]]

    return metadata, body


def infer_metadata_from_path(file_path: Path) -> dict:
    metadata = dict(DEFAULT_METADATA)
    metadata["title"] = file_path.stem.replace("_", " ").title()

    parts = [part.lower() for part in file_path.parts]
    if "public" in parts:
        public_idx = parts.index("public")
        if public_idx + 1 < len(parts):
            folder = parts[public_idx + 1]
            metadata["branch"] = BRANCH_ALIASES.get(folder, "general")

    stem = file_path.stem.lower()
    for token, topic in TOPIC_FROM_NAME.items():
        if token in stem:
            metadata["topic"] = topic
            break

    return metadata


def build_chunk_metadata(file_path: Path, page_num: int, refs: list[str], frontmatter: dict) -> dict:
    path_meta = infer_metadata_from_path(file_path)
    merged = {**path_meta, **{k: v for k, v in frontmatter.items() if v}}

    return {
        "source": str(file_path.relative_to(Path("data"))),
        "page": page_num,
        "references": ", ".join(refs) if refs else "",
        "branch": merged.get("branch", "general"),
        "topic": merged.get("topic", "general"),
        "doc_type": merged.get("doc_type", "guide"),
        "source_url": merged.get("source_url", ""),
        "title": merged.get("title", file_path.stem),
    }
