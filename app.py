"""CritiQuest Gradio MVP — Socratic critical-thinking coach for ages 8–14."""

from __future__ import annotations

import gradio as gr

from prompts import topic_titles, TOPIC_SEEDS
from socratic_engine import (
    SessionState,
    opening_message,
    respond,
    teacher_summary,
)

AGE_CHOICES = ["8-10", "11-12", "13-14"]
TOPICS = topic_titles() + ["Free exploration — type your own question"]
DISCLOSURE = "I am an AI that helps you think by asking questions."


def _fmt_skills(skills: dict) -> str:
    if not skills:
        skills = {"curiosity": 0, "evidence": 0, "perspective": 0, "reflection": 0}
    lines = [f"- **{k.title()}:** {v}" for k, v in skills.items()]
    return "### Thinking skills (mock)\n" + "\n".join(lines)


def _fmt_phase(phase: str, index: int) -> str:
    return f"### Socratic phase\n**{phase}** ({index + 1}/6)"


def start_session(age: str, topic: str, custom: str):
    if topic.startswith("Free exploration") and custom.strip():
        topic_use = custom.strip()
    elif topic.startswith("Free exploration"):
        topic_use = "What should we think carefully about today?"
    else:
        topic_use = topic

    st = SessionState(age_band=age, topic=topic_use)
    opener = opening_message(age, topic_use)
    st.history = [{"role": "assistant", "content": opener}]
    chat = [{"role": "assistant", "content": opener}]
    return (
        chat,
        st.to_dict(),
        _fmt_phase(st.phase, st.phase_index),
        _fmt_skills(st.skills),
        teacher_summary(st),
        f"**Topic:** {topic_use}  |  **Age:** {age}\n\n_{DISCLOSURE}_",
    )


def chat_turn(message: str, history: list, state: dict, age: str, topic_label: str, custom: str):
    if not message or not message.strip():
        return history, state, gr.update(), gr.update(), gr.update(), ""

    st = SessionState.from_dict(state)
    # Keep age/topic in sync with controls if session already started
    st.age_band = age or st.age_band
    if topic_label and not topic_label.startswith("Free exploration"):
        st.topic = topic_label
    elif custom.strip():
        st.topic = custom.strip()

    reply, st = respond(message.strip(), st)
    history = list(history or [])
    history.append({"role": "user", "content": message.strip()})
    history.append({"role": "assistant", "content": reply})
    return (
        history,
        st.to_dict(),
        _fmt_phase(st.phase, st.phase_index),
        _fmt_skills(st.skills),
        teacher_summary(st),
        "",
    )


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="CritiQuest") as demo:
        gr.Markdown(
            f"""# CritiQuest
**Socratic critical-thinking coach for ages 8–14**

_{DISCLOSURE}_

Personal portfolio MVP — zero paid APIs. Local Ollama preferred; optional Groq (`GROQ_API_KEY`); heuristic fallback if neither is available.
"""
        )
        state = gr.State({})

        with gr.Row():
            with gr.Column(scale=3):
                with gr.Row():
                    age = gr.Radio(AGE_CHOICES, value="11-12", label="Age band")
                    topic = gr.Dropdown(TOPICS, value=TOPICS[0], label="Topic")
                custom = gr.Textbox(
                    label="Custom question (for free exploration)",
                    placeholder="e.g. Why do people believe rumors?",
                )
                header = gr.Markdown("")
                start_btn = gr.Button("Start / reset conversation", variant="primary")
                chatbot = gr.Chatbot(label="Conversation", height=420)
                with gr.Row():
                    msg = gr.Textbox(
                        label="Your message",
                        placeholder="Share an idea… CritiQuest will ask a question back.",
                        scale=4,
                    )
                    send = gr.Button("Send", variant="secondary", scale=1)

            with gr.Column(scale=1):
                phase_md = gr.Markdown("### Socratic phase\n—")
                skills_md = gr.Markdown("### Thinking skills (mock)\n—")
                teacher_toggle = gr.Checkbox(label="Teacher view (mock)", value=False)
                teacher_md = gr.Markdown(visible=False)

        gr.Markdown(
            "### Topics in this MVP\n"
            + "\n".join(f"- {t['title']} _(_{t['domain']}_)_" for t in TOPIC_SEEDS)
        )

        start_btn.click(
            start_session,
            inputs=[age, topic, custom],
            outputs=[chatbot, state, phase_md, skills_md, teacher_md, header],
        )
        send.click(
            chat_turn,
            inputs=[msg, chatbot, state, age, topic, custom],
            outputs=[chatbot, state, phase_md, skills_md, teacher_md, msg],
        )
        msg.submit(
            chat_turn,
            inputs=[msg, chatbot, state, age, topic, custom],
            outputs=[chatbot, state, phase_md, skills_md, teacher_md, msg],
        )

        def _toggle(show: bool):
            return gr.update(visible=show)

        teacher_toggle.change(_toggle, inputs=[teacher_toggle], outputs=[teacher_md])

    return demo


demo = build_demo()

if __name__ == "__main__":
    demo.launch()
