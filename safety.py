"""CritiQuest safety: input/output filters for child-safe Socratic chat."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SafetyResult:
    ok: bool
    category: str = ""
    message: str = ""
    flags: list[str] | None = None

    def __post_init__(self) -> None:
        if self.flags is None:
            self.flags = []


# Harm / distress / sexual / PII / jailbreak patterns (keyword + light regex).
_BLOCK_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "self_harm",
        re.compile(
            r"\b(kill\s+myself|suicide|self[-\s]?harm|cut\s+myself|want\s+to\s+die|"
            r"end\s+my\s+life)\b",
            re.I,
        ),
        (
            "I'm really glad you said something. I'm not the right helper for hard feelings "
            "like that. Please talk to a trusted adult, or a parent/guardian, right away. "
            "If you're in the U.S., you can also call or text 988. "
            "When you're ready, we can explore a thinking topic together."
        ),
    ),
    (
        "violence",
        re.compile(
            r"\b(how\s+to\s+(make\s+a\s+bomb|hurt|kill|stab|shoot)|"
            r"bring\s+a\s+(gun|knife)\s+to\s+school)\b",
            re.I,
        ),
        (
            "I can't help with anything that could hurt people. "
            "Want to pick a thinking topic instead, like fairness, science, or media literacy?"
        ),
    ),
    (
        "sexual",
        re.compile(
            r"\b(sex|porn|nude|naked|hook\s*up|sexual)\b",
            re.I,
        ),
        (
            "That's not a topic I discuss. CritiQuest is for thinking skills: "
            "science, fairness, media literacy, and similar school-safe questions."
        ),
    ),
    (
        "pii_fishing",
        re.compile(
            r"\b(what('s| is)\s+your\s+(address|phone|password|real\s+name)|"
            r"where\s+do\s+you\s+live|give\s+me\s+your\s+(email|phone)|"
            r"social\s+security|credit\s+card)\b",
            re.I,
        ),
        (
            "I don't share or ask for private personal details. "
            "Let's keep exploring ideas. What's a claim you're curious about?"
        ),
    ),
    (
        "companion_seek",
        re.compile(
            r"\b(be\s+my\s+(best\s+)?friend|are\s+you\s+my\s+(best\s+)?friend|"
            r"do\s+you\s+love\s+me|will\s+you\s+be\s+my|"
            r"i\s+love\s+you|boyfriend|girlfriend|marry\s+me)\b",
            re.I,
        ),
        (
            "I'm CritiQuest. I help you think by asking questions, not by being a friend or companion. "
            "What idea about the topic do you want to examine first?"
        ),
    ),
    (
        "jailbreak",
        re.compile(
            r"(ignore\s+(all\s+)?(previous|prior|your)\s+(instructions|rules)|"
            r"dan\s+mode|jailbreak|developer\s+mode|"
            r"just\s+tell\s+me\s+the\s+answer|"
            r"don'?t\s+ask\s+questions|"
            r"stop\s+asking\s+questions|"
            r"give\s+me\s+the\s+(answer|solution)\s+directly|"
            r"pretend\s+you\s+(are|can)|"
            r"bypass\s+(safety|filter))",
            re.I,
        ),
        (
            "I'm built to help you think by asking questions, not to skip to answers "
            "or ignore safety. What part of the topic are you most unsure about?"
        ),
    ),
]

_COMPANION_OUT = re.compile(
    r"\b(i\s+love\s+you|i'?m\s+your\s+(best\s+)?friend|we'?ll\s+be\s+together|"
    r"i'?m\s+lonely|call\s+me\s+(tonight|baby)|romantic)\b",
    re.I,
)

_DIRECT_ANSWER_DUMP = re.compile(
    r"(the\s+correct\s+answer\s+is|here\s+is\s+the\s+full\s+answer|"
    r"you\s+should\s+conclude\s+that|definitively,?\s+the\s+answer)",
    re.I,
)


def check_input(text: str) -> SafetyResult:
    """Filter user input. Returns ok=False with a child-safe redirect message."""
    if not text or not text.strip():
        return SafetyResult(ok=False, category="empty", message="Say a little more so I can ask a good question.")

    flags: list[str] = []
    for category, pattern, message in _BLOCK_PATTERNS:
        if pattern.search(text):
            flags.append(category)
            return SafetyResult(ok=False, category=category, message=message, flags=flags)

    return SafetyResult(ok=True, flags=flags)


def check_output(text: str) -> SafetyResult:
    """Second-pass on model output: block companion tone / blunt answer dumps."""
    if not text:
        return SafetyResult(ok=False, category="empty", message="Let's try that again. What do you think so far?")

    flags: list[str] = []
    if _COMPANION_OUT.search(text):
        flags.append("companion_tone")
        return SafetyResult(
            ok=False,
            category="companion_tone",
            message=(
                "I'm CritiQuest. I help you think by asking questions, not by giving the answer. "
                "What evidence would make you more confident in your idea?"
            ),
            flags=flags,
        )
    if _DIRECT_ANSWER_DUMP.search(text):
        flags.append("direct_answer")
        return SafetyResult(
            ok=False,
            category="direct_answer",
            message=(
                "Instead of handing you the answer: what would you check first, "
                "and whose viewpoint might you be missing?"
            ),
            flags=flags,
        )

    # Soft check: prefer ending with a question mark for Socratic UX
    if "?" not in text:
        flags.append("no_question")

    return SafetyResult(ok=True, flags=flags)
