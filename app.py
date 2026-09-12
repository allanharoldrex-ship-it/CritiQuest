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
TOPICS = topic_titles() + ["I have my own question"]
DISCLOSURE = "I am an AI that helps you think by asking questions."

# Modern learning-app shell (overrides Gradio chrome heavily)
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,500;0,9..40,600;0,9..40,700;0,9..40,800;1,9..40,500&family=Fraunces:opsz,wght@9..144,700;9..144,800&display=swap');

html, body, .gradio-container {
  font-family: 'DM Sans', ui-sans-serif, system-ui, sans-serif !important;
  background: #0b1020 !important;
  color: #e8ecf8 !important;
}

.gradio-container {
  max-width: 1080px !important;
  margin: 0 auto !important;
  padding: 28px 16px 48px !important;
}

/* Kill Gradio gray chrome */
.main, .wrap, .contain, .panel, .block {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

footer, .footer, .svelte-1ipelgc { display: none !important; }

#cq-shell {
  background:
    radial-gradient(1200px 500px at 10% -10%, rgba(99,102,241,.35), transparent 55%),
    radial-gradient(900px 420px at 100% 0%, rgba(45,212,191,.22), transparent 50%),
    linear-gradient(180deg, #121833 0%, #0b1020 60%);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 28px;
  padding: 22px;
  box-shadow: 0 30px 80px rgba(0,0,0,.45);
}

#cq-top {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 18px;
  flex-wrap: wrap;
}

#cq-brand h1 {
  font-family: Fraunces, Georgia, serif !important;
  font-size: clamp(1.8rem, 3vw, 2.4rem) !important;
  font-weight: 800 !important;
  letter-spacing: -0.03em;
  margin: 0 0 6px !important;
  background: linear-gradient(90deg, #fff 0%, #c7d2fe 50%, #99f6e4 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent !important;
}

#cq-brand p {
  margin: 0;
  color: #a9b4d0 !important;
  font-size: 0.98rem;
  line-height: 1.45;
  max-width: 46ch;
}

#cq-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.1);
  color: #c7d2fe !important;
  font-size: 0.85rem;
  font-weight: 600;
  white-space: nowrap;
}

.cq-panel {
  background: rgba(255,255,255,.04) !important;
  border: 1px solid rgba(255,255,255,.08) !important;
  border-radius: 22px !important;
  padding: 14px !important;
  backdrop-filter: blur(10px);
}

label, .label-wrap span, span.svelte-1gfkn6j {
  color: #9aa6c4 !important;
  font-weight: 650 !important;
  font-size: 0.82rem !important;
  letter-spacing: 0.02em;
  text-transform: none !important;
}

input, textarea, select, .wrap-inner, .secondary-wrap {
  background: rgba(8,12,28,.65) !important;
  border: 1px solid rgba(255,255,255,.1) !important;
  border-radius: 14px !important;
  color: #f4f6ff !important;
}

.form, .block {
  padding: 0 !important;
}

/* Age radios as modern chips */
#cq-age label {
  background: rgba(255,255,255,.04) !important;
  border: 1px solid rgba(255,255,255,.1) !important;
  border-radius: 999px !important;
  padding: 10px 14px !important;
  margin-right: 8px !important;
  color: #dbe3ff !important;
}
#cq-age input:checked + span,
#cq-age label:has(input:checked) {
  background: linear-gradient(135deg, #6366f1, #22d3ee) !important;
  border-color: transparent !important;
  color: #0b1020 !important;
  font-weight: 800 !important;
}

button {
  border-radius: 999px !important;
  font-weight: 750 !important;
  letter-spacing: 0.01em;
  transition: transform .15s ease, box-shadow .15s ease !important;
}
button:hover { transform: translateY(-1px); }

button.primary {
  background: linear-gradient(135deg, #818cf8 0%, #22d3ee 100%) !important;
  color: #07101f !important;
  border: none !important;
  min-height: 48px !important;
  box-shadow: 0 10px 28px rgba(34,211,238,.25) !important;
  font-size: 1.02rem !important;
}

button.secondary {
  background: rgba(255,255,255,.06) !important;
  color: #e8ecf8 !important;
  border: 1px solid rgba(255,255,255,.12) !important;
  min-height: 46px !important;
}

#cq-chatbot, #cq-chatbot .bubble-wrap, #cq-chatbot .wrapper {
  background: rgba(5,8,20,.55) !important;
  border: 1px solid rgba(255,255,255,.08) !important;
  border-radius: 20px !important;
}

#cq-chatbot .message {
  border-radius: 16px !important;
  font-size: 1.02rem !important;
  line-height: 1.5 !important;
}

#cq-side h3, #cq-side .prose h3 {
  font-family: Fraunces, Georgia, serif !important;
  color: #f8fafc !important;
  font-size: 1.15rem !important;
  margin-top: 0 !important;
}

#cq-side .prose, #cq-side p, #cq-side li {
  color: #b7c0db !important;
}

.accordion {
  background: rgba(255,255,255,.03) !important;
  border: 1px solid rgba(255,255,255,.08) !important;
  border-radius: 16px !important;
}

@media (max-width: 768px) {
  .gradio-container { padding: 12px 10px 28px !important; }
  #cq-shell { padding: 14px; border-radius: 20px; }
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
    lines = [f"- {icons.get(k, '⭐')} **{k.title()}** · {v}" for k, v in skills.items()]
    return "### Thinking powers\n" + "\n".join(lines)


def _fmt_phase(phase: str, index: int) -> str:
    track = "".join("●" if i <= index else "○" for i in range(6))
    return f"### Quest step\n**{phase}**\n\n`{track}`  {index + 1}/6"


def start_session(age: str, topic: str, custom: str):
    if topic.startswith("I have my own") and custom.strip():
        topic_use = custom.strip()
    elif topic.startswith("I have my own"):
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
        f"**Quest:** {topic_use}  ·  ages **{age}**\n\n_{DISCLOSURE}_",
    )


def chat_turn(message: str, history: list, state: dict, age: str, topic_label: str, custom: str):
    if not message or not message.strip():
        return history, state, gr.update(), gr.update(), gr.update(), ""

    st = SessionState.from_dict(state)
    st.age_band = age or st.age_band
    if topic_label and not topic_label.startswith("I have my own"):
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
    # Minimal theme — visual system lives in CSS
    theme = gr.themes.Base(
        font=gr.themes.GoogleFont("DM Sans"),
        font_mono=gr.themes.GoogleFont("DM Sans"),
        primary_hue="indigo",
        neutral_hue="slate",
        radius_size="lg",
    ).set(
        body_background_fill="#0b1020",
        body_text_color="#e8ecf8",
        block_background_fill="transparent",
        border_color_primary="rgba(255,255,255,0.08)",
        button_primary_background_fill="#818cf8",
        button_primary_text_color="#07101f",
    )

    with gr.Blocks(title="CritiQuest", theme=theme, css=CUSTOM_CSS, fill_height=False) as demo:
        with gr.Column(elem_id="cq-shell"):
            gr.HTML(
                """
                <div id="cq-top">
                  <div id="cq-brand">
                    <h1>CritiQuest</h1>
                    <p>A calm thinking coach for ages 8–14. Ask anything curious — I’ll ask questions back so <b>you</b> figure it out.</p>
                  </div>
                  <div id="cq-pill">✨ Questions over answers</div>
                </div>
                """
            )

            state = gr.State({})

            with gr.Row(equal_height=False):
                with gr.Column(scale=3, elem_classes=["cq-panel"]):
                    age = gr.Radio(
                        AGE_CHOICES,
                        value="11-12",
                        label="Your age group",
                        elem_id="cq-age",
                    )
                    topic = gr.Dropdown(
                        TOPICS,
                        value=TOPICS[0],
                        label="Choose a quest",
                    )
                    custom = gr.Textbox(
                        label="Your own question",
                        placeholder="Why do people believe rumors?",
                        lines=1,
                    )
                    header = gr.Markdown("")
                    start_btn = gr.Button("Start quest", variant="primary")
                    chatbot = gr.Chatbot(
                        label="Conversation",
                        height=460,
                        type="messages",
                        elem_id="cq-chatbot",
                        show_copy_button=False,
                        bubble_full_width=False,
                        render_markdown=True,
                    )
                    with gr.Row():
                        msg = gr.Textbox(
                            label="Your thought",
                            placeholder="Share an idea…",
                            scale=5,
                            container=True,
                        )
                        send = gr.Button("Send", variant="secondary", scale=1)

                with gr.Column(scale=1, elem_classes=["cq-panel"], elem_id="cq-side"):
                    phase_md = gr.Markdown("### Quest step\nPress **Start quest**.")
                    skills_md = gr.Markdown("### Thinking powers\n—")
                    teacher_toggle = gr.Checkbox(
                        label="Teacher view",
                        value=False,
                        info="For grown-ups reviewing the chat",
                    )
                    teacher_md = gr.Markdown(visible=False)

            with gr.Accordion("All quest ideas", open=False):
                gr.Markdown(
                    "\n".join(f"- **{t['title']}** — _{t['domain']}_" for t in TOPIC_SEEDS)
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
