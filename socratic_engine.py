"""CritiQuest Socratic engine: phase machine + Ollama/Groq/heuristic callers."""

from __future__ import annotations

import os
import random
import re
from dataclasses import dataclass, field, asdict
from typing import Any

import requests

from prompts import (
    PHASES,
    TOPIC_SEEDS,
    build_messages,
    get_topic_by_title,
)
from safety import check_input, check_output


SKILL_KEYS = ("curiosity", "evidence", "perspective", "reflection")


@dataclass
class SessionState:
    age_band: str = "11-12"
    topic: str = TOPIC_SEEDS[0]["title"]
    phase: str = "clarify"
    phase_index: int = 0
    turn: int = 0
    history: list[dict[str, str]] = field(default_factory=list)
    skills: dict[str, int] = field(
        default_factory=lambda: {k: 0 for k in SKILL_KEYS}
    )
    flags: list[str] = field(default_factory=list)
    backend: str = "heuristic"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "SessionState":
        if not data:
            return cls()
        return cls(
            age_band=data.get("age_band", "11-12"),
            topic=data.get("topic", TOPIC_SEEDS[0]["title"]),
            phase=data.get("phase", "clarify"),
            phase_index=int(data.get("phase_index", 0)),
            turn=int(data.get("turn", 0)),
            history=list(data.get("history") or []),
            skills=dict(data.get("skills") or {k: 0 for k in SKILL_KEYS}),
            flags=list(data.get("flags") or []),
            backend=data.get("backend", "heuristic"),
        )


# Heuristic question banks by phase (used when no LLM available).
_HEURISTIC: dict[str, list[str]] = {
    "clarify": [
        "What part of '{topic}' matters most to you right now?",
        "If you had to explain '{topic}' to a classmate, what would you say first?",
        "What are you most unsure about in '{topic}'?",
    ],
    "assumptions": [
        "What are you taking for granted when you say that?",
        "What would have to be true for your idea to work?",
        "Is there a hidden 'always' or 'never' in your thinking about '{topic}'?",
    ],
    "evidence": [
        "What evidence would convince you — and what wouldn't?",
        "Where did that idea come from, and how could you check it?",
        "What's one thing you could measure or compare about '{topic}'?",
    ],
    "alternatives": [
        "Who might disagree with you, and why?",
        "What's another explanation that could also fit?",
        "If someone else saw the same facts, what else might they conclude?",
    ],
    "implications": [
        "If your idea were true, what would change next?",
        "Who would be helped or hurt if everyone believed that?",
        "What's a possible downside you haven't looked at yet?",
    ],
    "reflect": [
        "How has your thinking shifted since we started on '{topic}'?",
        "What question would you ask next on your own?",
        "Which mattered more just now — evidence, another viewpoint, or clarifying the question?",
    ],
}

# Cue-specific follow-ups (topic-aware Socratic moves).
_CUE_QUESTIONS: list[tuple[str, str, str]] = [
    # regex, skill, question
    (r"\b(pot|pots|sunlight|light|water|variable|control|fertilizer|taller|measure)\b", "evidence",
     "If those things were different on purpose, what would that do to a fair test?"),
    (r"\b(video|youtube|professional|views|click|creator|headline|ad|ads)\b", "evidence",
     "What would you check beyond how it looks or how popular it is?"),
    (r"\b(rule|rules|fair|mean|meanies|allowed|should)\b", "perspective",
     "Fair for whom — and who might say that rule isn't fair?"),
    (r"\b(source|sources|research|researched|prove|proof|evidence)\b", "evidence",
     "What would count as strong evidence here, not just a confident voice?"),
    (r"\b(exaggerate|rumor|true|false|believe|trust)\b", "perspective",
     "What's a different reason the same message might be shared?"),
]


def _ensure_question(text: str) -> str:
    text = text.strip()
    if not text.endswith("?"):
        text = text.rstrip(".!") + "?"
    return text


def _ollama_chat(messages: list[dict[str, str]], model: str) -> str | None:
    try:
        r = requests.post(
            "http://127.0.0.1:11434/api/chat",
            json={"model": model, "messages": messages, "stream": False},
            timeout=45,
        )
        if r.status_code != 200:
            return None
        return (r.json().get("message") or {}).get("content")
    except Exception:
        return None


def _groq_chat(messages: list[dict[str, str]]) -> str | None:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        return None
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant"),
                "messages": messages,
                "temperature": 0.6,
                "max_tokens": 220,
            },
            timeout=45,
        )
        if r.status_code != 200:
            return None
        choices = r.json().get("choices") or []
        if not choices:
            return None
        return choices[0]["message"]["content"]
    except Exception:
        return None


def _call_llm(messages: list[dict[str, str]]) -> tuple[str | None, str]:
    """Try Ollama models, then Groq. Returns (text, backend_name)."""
    for model in (
        os.environ.get("OLLAMA_MODEL", "llama3.1:8b"),
        "llama3.2:3b",
        "phi3",
    ):
        text = _ollama_chat(messages, model)
        if text:
            return text, f"ollama:{model}"
    text = _groq_chat(messages)
    if text:
        return text, "groq"
    return None, "heuristic"


def _age_prefix(age_band: str, kind: str) -> str:
    table = {
        "8-10": {
            "default": "Nice thinking.",
            "confident": "You sound pretty sure.",
            "unsure": "It's okay not to know yet.",
            "reasons": "You're looking for reasons.",
            "people": "You're thinking about other people.",
        },
        "11-12": {
            "default": "Good catch.",
            "confident": "You're pretty confident.",
            "unsure": "Uncertainty is useful here.",
            "reasons": "You're reaching for reasons.",
            "people": "You're considering other viewpoints.",
        },
        "13-14": {
            "default": "Noted.",
            "confident": "Strong claim.",
            "unsure": "Holding uncertainty helps.",
            "reasons": "You're weighing reasons.",
            "people": "You're testing other perspectives.",
        },
    }
    band = table.get(age_band, table["11-12"])
    return band.get(kind, band["default"])


def _heuristic_reply(state: SessionState, user_message: str) -> str:
    lower = user_message.lower()
    kind = "default"
    if re.search(r"\b(yes|yeah|true|always|must be|definitely)\b", lower):
        kind = "confident"
        state.skills["curiosity"] = state.skills.get("curiosity", 0) + 1
    elif re.search(r"\b(no|never|false|not sure|maybe|idk|i don't know)\b", lower):
        kind = "unsure"
        state.skills["curiosity"] = state.skills.get("curiosity", 0) + 1
    elif re.search(r"\b(because|since|evidence|proof|source|video|article|measure|compare)\b", lower):
        kind = "reasons"
        state.skills["evidence"] = state.skills.get("evidence", 0) + 1
    elif re.search(r"\b(other|someone|they|perspective|disagree|fair for)\b", lower):
        kind = "people"
        state.skills["perspective"] = state.skills.get("perspective", 0) + 1

    if state.phase == "reflect":
        state.skills["reflection"] = state.skills.get("reflection", 0) + 1

    prefix = _age_prefix(state.age_band, kind)

    # Prefer cue-specific follow-up when it matches the learner's words.
    q = None
    for pattern, skill, question in _CUE_QUESTIONS:
        if re.search(pattern, lower):
            q = question
            state.skills[skill] = state.skills.get(skill, 0) + 1
            break

    if not q:
        bank = list(_HEURISTIC.get(state.phase, _HEURISTIC["clarify"]))
        # Avoid repeating the last assistant question when possible.
        last_assts = [h["content"] for h in state.history if h.get("role") == "assistant"]
        random.shuffle(bank)
        for template in bank:
            candidate = template.format(topic=state.topic)
            if not last_assts or candidate not in last_assts[-1]:
                q = candidate
                break
        if not q:
            q = bank[0].format(topic=state.topic)

    return _ensure_question(f"{prefix} {q}")


def advance_phase(state: SessionState, force: bool = False) -> SessionState:
    """Advance every 2 learner turns, or when force=True."""
    if force or (state.turn > 0 and state.turn % 2 == 0):
        state.phase_index = min(state.phase_index + 1, len(PHASES) - 1)
        state.phase = PHASES[state.phase_index]
    return state


def opening_message(age_band: str, topic: str) -> str:
    meta = get_topic_by_title(topic)
    seed = meta["seed"] if meta else f"Exploring: {topic}"
    disclosure = "I'm CritiQuest — an AI that helps you think by asking questions."
    if age_band == "8-10":
        return (
            f"{disclosure} Today we're exploring: **{topic}**. "
            f"{seed.split('.')[0]}. What do you already think about this?"
        )
    return (
        f"{disclosure} Topic: **{topic}**. {seed} "
        "What's your first take — and what makes you think that?"
    )


def teacher_summary(state: SessionState) -> str:
    skills = ", ".join(f"{k}={v}" for k, v in state.skills.items())
    flag_txt = ", ".join(state.flags) if state.flags else "none"
    turns = len([h for h in state.history if h.get("role") == "user"])
    return (
        f"**Teacher view (mock)**\n"
        f"- Topic: {state.topic}\n"
        f"- Age band: {state.age_band}\n"
        f"- Phase: {state.phase} ({state.phase_index + 1}/{len(PHASES)})\n"
        f"- Learner turns: {turns}\n"
        f"- Thinking-skill counters (mock): {skills}\n"
        f"- Safety flags this session: {flag_txt}\n"
        f"- Backend: {state.backend}\n"
        f"- Note: summary is generated for oversight demos; no student data is stored remotely by this MVP."
    )


def respond(
    user_message: str,
    state: SessionState | dict | None = None,
    age_band: str | None = None,
    topic: str | None = None,
) -> tuple[str, SessionState]:
    """Main turn handler. Returns (assistant_text, updated_state)."""
    st = state if isinstance(state, SessionState) else SessionState.from_dict(state)
    if age_band:
        st.age_band = age_band
    if topic:
        st.topic = topic

    safety_in = check_input(user_message)
    if not safety_in.ok:
        st.flags = list(set(st.flags + (safety_in.flags or [safety_in.category])))
        st.history.append({"role": "user", "content": user_message})
        st.history.append({"role": "assistant", "content": safety_in.message})
        return safety_in.message, st

    messages = build_messages(st.age_band, st.phase, st.topic, st.history, user_message)
    llm_text, backend = _call_llm(messages)
    st.backend = backend

    if llm_text:
        reply = llm_text.strip()
    else:
        reply = _heuristic_reply(st, user_message)

    safety_out = check_output(reply)
    if not safety_out.ok:
        st.flags = list(set(st.flags + (safety_out.flags or [safety_out.category])))
        reply = safety_out.message
    else:
        reply = _ensure_question(reply)
        # Heuristic skill bumps when LLM path used
        if backend != "heuristic":
            st.skills["curiosity"] = st.skills.get("curiosity", 0) + 1
            if st.phase == "evidence":
                st.skills["evidence"] = st.skills.get("evidence", 0) + 1
            if st.phase == "alternatives":
                st.skills["perspective"] = st.skills.get("perspective", 0) + 1
            if st.phase == "reflect":
                st.skills["reflection"] = st.skills.get("reflection", 0) + 1

    st.history.append({"role": "user", "content": user_message})
    st.history.append({"role": "assistant", "content": reply})
    st.turn += 1
    advance_phase(st)
    return reply, st
