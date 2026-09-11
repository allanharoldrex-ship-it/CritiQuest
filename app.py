"""CritiQuest Gradio MVP — Socratic critical-thinking coach for ages 8–14."""

from __future__ import annotations

import os

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

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@500;700;800&display=swap');

:root {
  --cq-bg: #f3f7ff;
  --cq-card: #ffffff;
  --cq-ink: #1f2a44;
  --cq-muted: #5b6b8c;
  --cq-accent: #5b7cfa;
  --cq-accent-2: #34d399;
  --cq-warm: #fbbf24;
}

body, .gradio-container {
  font-family: 'Nunito', system-ui, sans-serif !important;
  background: linear-gradient(165deg, #eef4ff 0%, #f8fbff 45%, #eefbf5 100%) !important;
  color: var(--cq-ink) !important;
}

.gradio-container {
  max-width: 1100px !important;
  margin: 0 auto !important;
}

#cq-hero {
  background: linear-gradient(120deg, #5b7cfa 0%, #7c5cff 55%, #34d399 100%);
  color: white !important;
  border-radius: 24px !important;
  padding: 22px 24px !important;
  box-shadow: 0 12px 30px rgba(91, 124, 250, 0.28);
  margin-bottom: 8px;
}

#cq-hero h1 {
  font-size: 2rem !important;
  font-weight: 800 !important;
  margin: 0 0 6px 0 !important;
  color: white !important;
}

#cq-hero p, #cq-hero * {
  color: rgba(255,255,255,0.95) !important;
}

.cq-card {
  background: var(--cq-card) !important;
  border: 1px solid rgba(91, 124, 250, 0.12) !important;
  border-radius: 20px !important;
  padding: 14px !important;
  box-shadow: 0 8px 24px rgba(31, 42, 68, 0.06) !important;
}

button.primary, .primary {
  border-radius: 999px !important;
  font-weight: 800 !important;
  font-size: 1.05rem !important;
  min-height: 48px !important;
}

button.secondary {
  border-radius: 999px !important;
  font-weight: 700 !important;
  min-height: 44px !important;
}

#cq-chatbot, #cq-chatbot .wrapper {
  border-radius: 18px !important;
  border: 1px solid rgba(91, 124, 250, 0.15) !important;
  background: #fff !important;
}

#cq-side h3 {
  font-size: 1.05rem !important;
  font-weight: 800 !important;
}

label, .label-wrap span {
  font-weight: 700 !important;
  color: var(--cq-muted) !important;
}

footer, .footer {
  display: none !important;
}
"""


def _fmt_skills(skills: dict) -> str:
    if not skills:
        skills = {"curiosity": 0, "evidence": 0, "perspective": 0, "reflection": 0}
    icons = {
        "curiosity": "🔍",
        "evidence": "🧪",
        "perspective": "👀",
        "reflection": "💭",
    }
    lines = [
        f"- {icons.get(k, '⭐')} **{k.title()}:** {v}"
        for k, v in skills.items()
    ]
    return "### Your thinking powers\n" + "\n".join(lines)


def _fmt_phase(phase: str, index: int) -> str:
    steps = [
        "Clarify",
        "Assumptions",
        "Evidence",
        "Alternatives",
        "Implications",
        "Reflect",
    ]
    dots = "".join("●" if i <= index else "○" for i in range(len(steps)))
    return f"### Where we are\n**{phase}**\n\n{dots}\n\nStep {index + 1} of 6"


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
        f"### Let's think about\n**{topic_use}**  ·  ages **{age}**\n\n_{DISCLOSURE}_",
    )


def chat_turn(message: str, history: list, state: dict, age: str, topic_label: str, custom: str):
    if not message or not message.strip():
        return history, state, gr.update(), gr.update(), gr.update(), ""

    st = SessionState.from_dict(state)
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
    theme = gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="emerald",
        neutral_hue="slate",
        font=gr.themes.GoogleFont("Nunito"),
        font_mono=gr.themes.GoogleFont("Nunito"),
        radius_size="lg",
    ).set(
        button_primary_background_fill="#5b7cfa",
        button_primary_background_fill_hover="#4a6aef",
        button_primary_text_color="#ffffff",
        block_title_text_weight="700",
        body_text_color="#1f2a44",
    )

    with gr.Blocks(title="CritiQuest", theme=theme, css=CUSTOM_CSS) as demo:
        gr.HTML(
            """
            <div id="cq-hero">
              <h1>🧠 CritiQuest</h1>
              <p>A friendly thinking coach for ages 8–14. I ask questions so <b>you</b> can figure things out.</p>
              <p style="opacity:0.9;margin:0"><i>I am an AI that helps you think by asking questions.</i></p>
            </div>
            """
        )

        state = gr.State({})

        with gr.Row():
            with gr.Column(scale=3, elem_classes=["cq-card"]):
                with gr.Row():
                    age = gr.Radio(
                        AGE_CHOICES,
                        value="11-12",
                        label="How old are you?",
                    )
                    topic = gr.Dropdown(
                        TOPICS,
                        value=TOPICS[0],
                        label="Pick a thinking puzzle",
                    )
                custom = gr.Textbox(
                    label="Or type your own puzzle",
                    placeholder="Example: Why do people believe rumors?",
                )
                header = gr.Markdown("")
                start_btn = gr.Button("✨ Let's think!", variant="primary")
                chatbot = gr.Chatbot(
                    label="Our chat",
                    height=440,
                    type="messages",
                    elem_id="cq-chatbot",
                    show_label=True,
                    avatar_images=(None, None),
                    bubble_full_width=False,
                )
                with gr.Row():
                    msg = gr.Textbox(
                        label="Your idea",
                        placeholder="Type your thought… I’ll ask a question back.",
                        scale=4,
                        lines=1,
                    )
                    send = gr.Button("Send →", variant="secondary", scale=1)

            with gr.Column(scale=1, elem_classes=["cq-card"], elem_id="cq-side"):
                phase_md = gr.Markdown("### Where we are\nTap **Let's think!** to begin.")
                skills_md = gr.Markdown("### Your thinking powers\n—")
                teacher_toggle = gr.Checkbox(
                    label="Teacher view (for grown-ups)",
                    value=False,
                )
                teacher_md = gr.Markdown(visible=False)

        with gr.Accordion("Puzzle ideas in this demo", open=False):
            gr.Markdown(
                "\n".join(f"- **{t['title']}** — {t['domain']}" for t in TOPIC_SEEDS)
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
    port = int(os.environ.get("PORT", "7860"))
    demo.launch(server_name="0.0.0.0", server_port=port)
