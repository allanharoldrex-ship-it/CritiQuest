# CritiQuest

**Personal portfolio product** — a zero-cost Socratic critical-thinking chatbot for ages **8–14** (school / tablet / mobile-web).  
Built by **Allan Harold Rex** (Senior Conversational Experience Designer, IBM) as ownership evidence for a GenAI / Conversational AI Product Manager transition.

> CritiQuest is **not a company**. No revenue claims. No fabricated user counts or traction metrics.

---

## Problem

Homework helpers and chatbots often **answer for** students. That undermines the skill schools actually need: **reasoning under uncertainty** — clarifying claims, checking evidence, weighing viewpoints, and reflecting.

## Users

| Persona | Need |
|--------|------|
| Students 8–14 | Practice thinking without being handed answers |
| Teachers | Oversight: what was discussed, safety flags, skill signals (mocked in MVP) |
| School admin (later) | Policy, accounts, reporting — **out of scope** for MVP (story only) |

## Design principles (Socratic CX)

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

# Optional: Ollama with a small model
# ollama pull llama3.2:3b

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
# or without pytest:
python tests/test_safety_engine.py  # import checks via pytest recommended
```

## Hugging Face Spaces

1. Create a Gradio Space; upload this folder (`app.py` at root of the Space or adjust path).
2. Set `requirements.txt` as above.
3. Optional: add `GROQ_API_KEY` as a Space secret for free Llama inference.
4. App entry: `app.py` exposes `demo` for Spaces; locally use `python app.py`.

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
| Gradio + HF | Free public demo, mobile browser | Cold starts; limited branding |

## Next phase (with a team)

Curriculum-aligned topic packs, real teacher auth, evaluation rubrics for reasoning moves, district privacy review, and A/B on phase timing — still **questions-first**.

## Walkthrough script (2–3 min Loom)

1. Disclosure + age 11–12 + topic “Is every YouTube video true?”  
2. Student says videos “look real” → show evidence-phase question.  
3. Toggle teacher view (phase + mock skills + flags).  
4. Try “just tell me the answer” → jailbreak refusal.  
5. Close on principles: ownership of CX + safety + zero-cost stack.

---

### Portfolio note

IBM remains primary professional proof. CritiQuest is **ownership** proof for conversational / GenAI PM interviews. Do not list CritiQuest as an employer on LinkedIn.
