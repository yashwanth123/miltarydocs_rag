import re
from enum import Enum


class Intent(str, Enum):
    GREETING = "greeting"
    CHAT = "chat"
    HELP = "help"
    SUMMARIZE = "summarize"
    CHAIN_OF_COMMAND = "chain_of_command"
    TRAINING = "training"
    STANDARDS = "standards"
    LIST = "list"
    GENERAL = "general"
    UNKNOWN = "unknown"


CONTRACTIONS = {
    "whats": "what is",
    "what's": "what is",
    "whos": "who is",
    "who's": "who is",
    "wheres": "where is",
    "where's": "where is",
    "hows": "how is",
    "how's": "how is",
    "dont": "do not",
    "doesnt": "does not",
    "cant": "can not",
    "im": "i am",
    "i'm": "i am",
    "youre": "you are",
    "you're": "you are",
}

INTENT_RULES: list[tuple[Intent, list[str]]] = [
    (Intent.GREETING, [
        r"^(hi|hello|hey|good morning|good afternoon|good evening)\b",
        r"^(howdy|greetings)\b",
    ]),
    (Intent.HELP, [
        r"what can i ask",
        r"what should i ask",
        r"what (can|could) (you|u) (answer|do|help)",
        r"what can you help",
        r"how does this work",
        r"how (do|can) i use",
        r"^(help|help me)\b",
        r"example questions",
        r"give me examples",
        r"what (is this|are these) (for|about)",
        r"what(s| is) this about",
        r"what is this (app|tool|system|chatbot)",
    ]),
    (Intent.SUMMARIZE, [
        r"summarize",
        r"summary",
        r"give me (a |an )?(quick )?(summary|overview|recap)",
        r"brief me",
        r"brief(ly)? (on|about|explain|describe)",
        r"main (points|topics|ideas|takeaways)",
        r"key (points|topics|ideas|takeaways)",
        r"\btldr\b",
        r"high level (view|overview)",
        r"what are these documents about",
        r"what do (the|these|my) documents (say|cover|contain)",
    ]),
    (Intent.CHAIN_OF_COMMAND, [
        r"chain of command",
        r"command hierarchy",
        r"order of authority",
        r"line of authority",
        r"leadership structure",
        r"unity of command",
        r"span of control",
        r"who reports to whom",
        r"reporting structure",
        r"levels of command",
        r"military hierarchy",
        r"explain (the )?hierarchy",
        r"how (does|do) orders flow",
    ]),
    (Intent.TRAINING, [
        r"\btraining\b",
        r"\bqualifications\b",
        r"military training",
        r"required training",
        r"technical manual",
        r"field manual",
        r"what (does|do) the (manual|document|regulation)",
    ]),
    (Intent.STANDARDS, [
        r"mil-std",
        r"mil-prf",
        r"military standard",
        r"military reference",
        r"which standards",
        r"referenced standards",
        r"what standards",
    ]),
    (Intent.LIST, [
        r"^list\b",
        r"enumerate",
        r"what are the (steps|levels|principles|items)",
        r"give me (all|the) (steps|levels|principles)",
    ]),
]

TOPIC_SEARCH_EXPANSIONS = {
    Intent.CHAIN_OF_COMMAND: [
        "military chain of command authority responsibility orders",
        "unity of command span of control delegation president secretary defense",
    ],
    Intent.TRAINING: [
        "military training qualifications requirements procedures doctrine",
    ],
    Intent.STANDARDS: [
        "MIL-STD MIL-PRF military references standards specifications",
    ],
    Intent.SUMMARIZE: [
        "main topics key points overview summary military document content doctrine",
    ],
}

TOKEN_SYNONYMS = {
    "command": {"chain", "hierarchy", "authority", "leadership", "orders", "superior"},
    "summarize": {"summary", "overview", "recap", "brief", "tldr", "gist"},
    "training": {"qualification", "requirements", "procedure", "doctrine", "manual"},
    "standard": {"standards", "mil", "reference", "specification"},
    "document": {"documents", "file", "files", "pdf", "content", "text"},
    "military": {"army", "defense", "doctrine", "service"},
}

CASUAL_EXACT = {
    "ok", "okay", "k", "cool", "nice", "yep", "yeah", "ya", "yup",
    "sup", "thanks", "thank you", "ty", "hype", "lol", "haha", "heee",
    "hii", "hiii", "sure", "alright", "bet", "word",
}

NO_RETRIEVAL_INTENTS = {Intent.GREETING, Intent.CHAT, Intent.HELP}

OUT_OF_SCOPE_PATTERNS = (
    "who am i",
    "about me",
    "my resume",
    "my profile",
    "tell me about myself",
    "my background",
)


def is_out_of_scope(question: str) -> bool:
    normalized = normalize_question(question)
    return any(pattern in normalized for pattern in OUT_OF_SCOPE_PATTERNS)


def normalize_question(question: str) -> str:
    q = question.strip().lower()
    q = re.sub(r"[^\w\s'?-]", " ", q)
    q = re.sub(r"\s+", " ", q)

    for src, dst in CONTRACTIONS.items():
        q = re.sub(rf"\b{re.escape(src)}\b", dst, q)

    return q.strip()


def classify_intent(question: str) -> Intent:
    normalized = normalize_question(question)

    if not normalized:
        return Intent.UNKNOWN

    if is_casual_chat(normalized):
        return Intent.CHAT

    if len(normalized.split()) <= 1 and normalized in {"where", "who", "why", "how", "what"}:
        return Intent.UNKNOWN

    best_intent = Intent.GENERAL
    best_score = 0

    for intent, patterns in INTENT_RULES:
        score = 0
        for pattern in patterns:
            if re.search(pattern, normalized):
                score += 2 if pattern.startswith("^") else 1
        if score > best_score:
            best_score = score
            best_intent = intent

    if best_score == 0:
        if any(word in normalized for word in ("explain", "describe", "define", "tell me about", "what is", "what are")):
            return Intent.GENERAL
        return Intent.GENERAL

    return best_intent


def is_casual_chat(normalized: str) -> bool:
    if normalized in {"hi", "hello", "hey", "howdy", "greetings"}:
        return False
    if normalized in CASUAL_EXACT:
        return True
    if re.match(r"^(ha+|he+|lol+|wow+|yes+|no+|hii+)$", normalized):
        return True
    if len(normalized) <= 5 and normalized.isalpha() and normalized not in {
        "where", "who", "what", "when", "why", "how",
    }:
        return True
    return False


def is_vague_question(question: str, intent: Intent) -> bool:
    if intent not in {Intent.UNKNOWN, Intent.GENERAL}:
        return False

    normalized = normalize_question(question)
    if is_casual_chat(normalized):
        return False
    words = normalized.split()

    if len(words) <= 1:
        return True
    if len(words) == 2 and len(normalized) < 14:
        return True
    return normalized in {"where", "who", "why", "how", "what", "when"}


def expand_retrieval_queries(question: str, intent: Intent) -> list[str]:
    queries = [question.strip()]
    normalized = normalize_question(question)

    expansions = TOPIC_SEARCH_EXPANSIONS.get(intent, [])
    queries.extend(expansions)

    if intent == Intent.GENERAL:
        if "command" in normalized or "hierarchy" in normalized:
            queries.extend(TOPIC_SEARCH_EXPANSIONS[Intent.CHAIN_OF_COMMAND])
        if "training" in normalized or "manual" in normalized or "regulation" in normalized:
            queries.extend(TOPIC_SEARCH_EXPANSIONS[Intent.TRAINING])

    seen = set()
    unique = []
    for query in queries:
        key = query.lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(query)
    return unique


def expand_tokens(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    for token in list(tokens):
        for root, synonyms in TOKEN_SYNONYMS.items():
            if token == root or token in synonyms:
                expanded.add(root)
                expanded.update(synonyms)
    return expanded
