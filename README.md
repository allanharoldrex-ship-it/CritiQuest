---
title: CritiQuest
emoji: 🧠
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
short_description: Socratic critical-thinking coach for ages 8-14 (portfolio demo)
---

# CritiQuest

A **zero-cost** Socratic critical-thinking chatbot for ages **8–14** (school / tablet / mobile-web).

CritiQuest coaches students by asking questions — it is not a homework answer engine.

> Personal portfolio product. Not a company. No revenue claims. No fabricated user counts.

---

## Problem

Homework helpers and chatbots often **answer for** students. That undermines the skill schools actually need: **reasoning under uncertainty** — clarifying claims, checking evidence, weighing viewpoints, and reflecting.

## Users

| Persona | Need |
|--------|------|
| Students 8–14 | Practice thinking without being handed answers |
| Teachers | Oversight: what was discussed, safety flags, skill signals (mocked in MVP) |
| School admin (later) | Policy, accounts, reporting — **out of scope** for MVP |

## Design principles

1. **Questions over answers** — most turns end in a question; never default to the solution.
2. **Scaffolded phases** — Clarify → Assumptions → Evidence → Alternatives → Implications → Reflect.
3. **Age-banded tone** — 8–10 / 11–12 / 13–14 system prompts.
4. **Child-safe** — no companion/romantic tone; harm topics redirect to a trusted adult; jailbreaks refused.
5. **Disclosure** — “I am an AI that helps you think by asking questions.”
6. **Teacher-in-the-loop** — mock summary + flags for classroom oversight demos.

## Architecture (zero-cost)

```
critiquest/
  app.py               # Gradio Blocks UI
  socratic_engine.py   # Phase machine + Ollama / Groq / heuristic
  prompts.py           # Age + phase prompts, topic seeds
  safety.py            # Keyword filters + output second-pass
  requirements.txt
  README.md            # This case study
```

**Runtime order:** try local **Ollama** (`llama3.1:8b`, then `llama3.2:3b` / `phi3`) → optional **Groq** free tier if `GROQ_API_KEY` is set → **heuristic** question templates (demo always works with zero keys).

**Deliberately not included:** native apps, real district SSO/LMS, paid LLMs, persistent student data training claims.

## Safety & privacy posture

- Input blocklist: self-harm (redirect + 988 mention for U.S.), violence how-tos, sexual content, PII fishing, jailbreaks (“just tell me the answer”).
- Output second-pass: companion language and blunt “the answer is…” dumps.
- MVP stores session state **in the Gradio session only** — no remote student datastore.
- School-account / FERPA-style story belongs in a later team phase, not this personal demo.

## How to run locally

```bash
cd critiquest
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Optional public LLM path:

```bash
export GROQ_API_KEY=...   # free tier
python app.py
```

Tests:

```bash
python -m pytest tests/ -q
# or:
python tests/test_safety_engine.py
```

## Deploy (free)

- **Render free web service:** set start command to `python app.py` (listens on `$PORT`).
- Optional: set `GROQ_API_KEY` as an environment variable for free Llama inference.

## Metrics we *would* track (not claimed as live KPIs)

- % of turns ending in a question
- Phase progression depth per session
- Safety flag rate (by category)
- Teacher-view open rate (if shipped)
- Qualitative: “did this help me think?” exit pulse

## Trade-offs

| Choice | Why | Cost |
|--------|-----|------|
| Heuristic fallback | Reliable zero-key demo | Less flexible than a strong LLM |
| Keyword safety | Transparent, free, fast | Needs ongoing list maintenance; not a full classifier |
| Mock teacher view | Shows oversight story without SSO | Not real classroom analytics |
| Free hosting | Public demo on a budget | Cold starts; limited branding |

## Next phase (with a team)

Curriculum-aligned topic packs, real teacher auth, evaluation rubrics for reasoning moves, district privacy review, and A/B on phase timing — still **questions-first**.

## Walkthrough script (2–3 min)

1. Disclosure + age 11–12 + topic “Is every YouTube video true?”
2. Student says videos “look real” → show evidence-phase question.
3. Toggle teacher view (phase + mock skills + flags).
4. Try “just tell me the answer” → jailbreak refusal.
5. Close on product principles: questions-first, child safety, zero-cost stack.
