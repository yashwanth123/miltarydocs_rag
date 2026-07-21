import re

DISCLAIMER = (
    "\n\n---\n"
    "Disclaimer: Answers are generated from indexed public documents only. "
    "This is not official DoD guidance. For enlistment decisions, medical questions, "
    "or contract terms, consult a qualified recruiter or official source."
)

RECRUITER_TOPICS = (
    r"\benlist",
    r"\bjoin (the )?(army|navy|marines|air force|coast guard|space force|military)\b",
    r"\bmeps\b",
    r"\basvab\b",
    r"\bgi bill\b",
    r"\bbenefits\b",
    r"\bcontract\b",
    r"\bwaiv",
    r"\bmedical (disqual|standards|exam)\b",
)

SENSITIVE_PATTERNS = (
    r"\bmedical (advice|diagnosis|condition)\b",
    r"\bam i (eligible|qualified|fit)\b",
    r"\bwill i pass\b",
    r"\blegal advice\b",
)


def needs_recruiter_reminder(question: str) -> bool:
    normalized = question.lower()
    return any(re.search(pattern, normalized) for pattern in RECRUITER_TOPICS)


def is_sensitive_question(question: str) -> bool:
    normalized = question.lower()
    return any(re.search(pattern, normalized) for pattern in SENSITIVE_PATTERNS)


def apply_answer_guardrails(question: str, answer: str) -> str:
    if not answer.strip():
        return answer

    extra = []
    if is_sensitive_question(question):
        extra.append(
            "Important: I cannot provide medical or eligibility determinations. "
            "Only a MEPS medical review and a service recruiter can confirm your status."
        )

    if needs_recruiter_reminder(question) and "recruiter" not in answer.lower():
        extra.append(
            "Next step: verify details with an official recruiter — requirements change by branch and role."
        )

    combined = answer
    if extra:
        combined = answer + "\n\n" + "\n".join(extra)

    if needs_recruiter_reminder(question) or is_sensitive_question(question):
        if "Disclaimer:" not in combined:
            combined += DISCLAIMER

    return combined
