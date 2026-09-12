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
OWN_QUESTION = "I have my own question"

# Calm 2025 learning-app shell — phone-first, soft premium education (not Gradio chrome)
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700;9..144,800&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

:root {
  --cq-bg: #f3f0ea;
  --cq-ink: #1c2434;
  --cq-muted: #5b6578;
  --cq-card: #ffffff;
  --cq-line: rgba(28, 36, 52, 0.08);
  --cq-indigo: #4f46e5;
  --cq-indigo-soft: #eef2ff;
  --cq-teal: #0f766e;
  --cq-teal-soft: #ecfdf8;
  --cq-shadow: 0 10px 30px rgba(28, 36, 52, 0.08);
  --cq-radius: 22px;
}

html, body, .gradio-container {
  font-family: 'Plus Jakarta Sans', ui-sans-serif, system-ui, sans-serif !important;
  background: var(--cq-bg) !important;
  color: var(--cq-ink) !important;
}

.gradio-container {
  max-width: 920px !important;
  margin: 0 auto !important;
  padding: 16px 14px 40px !important;
}

/* Strip Gradio chrome */
.main, .wrap, .contain, .panel, .block,
.form, .svelte-1ipelgc {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}
footer, .footer, footer.svelte-1ipelgc, .icon-button-wrapper.top-panel {
  display: none !important;
}
.gap { gap: 12px !important; }

#cq-shell {
  background:
    radial-gradient(900px 420px at 0% -10%, rgba(79, 70, 229, 0.12), transparent 55%),
    radial-gradient(700px 360px at 100% 0%, rgba(15, 118, 110, 0.10), transparent 50%),
    linear-gradient(180deg, #faf8f4 0%, var(--cq-bg) 55%);
  border: 1px solid var(--cq-line);
  border-radius: 28px;
  padding: 18px 16px 20px;
  box-shadow: var(--cq-shadow);
}

#cq-hero {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 14px;
}

#cq-brand-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

#cq-brand h1 {
  font-family: Fraunces, Georgia, serif !important;
  font-size: clamp(1.85rem, 5vw, 2.35rem) !important;
  font-weight: 800 !important;
  letter-spacing: -0.03em;
  line-height: 1.1 !important;
  margin: 0 0 6px !important;
  color: var(--cq-ink) !important;
}

#cq-brand p {
  margin: 0;
  color: var(--cq-muted) !important;
  font-size: 0.98rem;
  line-height: 1.45;
  max-width: 42ch;
  font-weight: 500;
}

#cq-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 999px;
  background: var(--cq-indigo-soft);
  color: var(--cq-indigo) !important;
  font-size: 0.82rem;
  font-weight: 700;
  white-space: nowrap;
  border: 1px solid rgba(79, 70, 229, 0.15);
}

.cq-card {
  background: var(--cq-card) !important;
  border: 1px solid var(--cq-line) !important;
  border-radius: var(--cq-radius) !important;
  padding: 14px !important;
  box-shadow: 0 4px 16px rgba(28, 36, 52, 0.04) !important;
}

label, .label-wrap span, span.svelte-1gfkn6j {
  color: var(--cq-muted) !important;
  font-weight: 700 !important;
  font-size: 0.8rem !important;
  letter-spacing: 0.01em;
  text-transform: none !important;
}

input, textarea, select, .wrap-inner, .secondary-wrap, .scroll-hide {
  background: #f8fafc !important;
  border: 1px solid var(--cq-line) !important;
  border-radius: 16px !important;
  color: var(--cq-ink) !important;
  min-height: 48px !important;
  font-size: 1rem !important;
}

.form, .block { padding: 0 !important; margin: 0 !important; }

/* Age chips */
#cq-age {
  margin-bottom: 4px !important;
}
#cq-age .wrap {
  display: flex !important;
  flex-wrap: wrap !important;
  gap: 8px !important;
}
#cq-age label {
  background: #f8fafc !important;
  border: 1.5px solid var(--cq-line) !important;
  border-radius: 999px !important;
  padding: 11px 16px !important;
  margin: 0 !important;
  color: var(--cq-ink) !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
  cursor: pointer !important;
  min-height: 44px !important;
  display: inline-flex !important;
  align-items: center !important;
}
#cq-age label:has(input:checked),
#cq-age input:checked + span {
  background: var(--cq-indigo) !important;
  border-color: var(--cq-indigo) !important;
  color: #fff !important;
}

button {
  border-radius: 999px !important;
  font-weight: 800 !important;
  letter-spacing: 0.01em;
  transition: transform .12s ease, box-shadow .12s ease, filter .12s ease !important;
  min-height: 48px !important;
  font-size: 1.02rem !important;
}
button:hover { transform: translateY(-1px); filter: brightness(1.02); }
button:focus-visible {
  outline: 3px solid rgba(79, 70, 229, 0.35) !important;
  outline-offset: 2px !important;
}

button.primary, #cq-start button {
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 55%, #0d9488 140%) !important;
  color: #fff !important;
  border: none !important;
  box-shadow: 0 12px 28px rgba(79, 70, 229, 0.28) !important;
  width: 100% !important;
}

button.secondary {
  background: var(--cq-indigo-soft) !important;
  color: var(--cq-indigo) !important;
  border: 1px solid rgba(79, 70, 229, 0.18) !important;
  min-width: 88px !important;
}

#cq-chatbot, #cq-chatbot .bubble-wrap, #cq-chatbot .wrapper,
#cq-chatbot > .wrap {
  background: #fbfaf7 !important;
  border: 1px solid var(--cq-line) !important;
  border-radius: 20px !important;
  min-height: 320px !important;
}

#cq-chatbot .message, #cq-chatbot .bot, #cq-chatbot .user {
  border-radius: 18px !important;
  font-size: 1.04rem !important;
  line-height: 1.55 !important;
  font-weight: 500 !important;
}

#cq-empty {
  text-align: center;
  padding: 28px 16px 8px;
  color: var(--cq-muted);
}
#cq-empty strong {
  display: block;
  font-family: Fraunces, Georgia, serif;
  font-size: 1.2rem;
  color: var(--cq-ink);
  margin-bottom: 6px;
  font-weight: 700;
}

#cq-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 4px;
}
.cq-stat {
  background: var(--cq-teal-soft);
  border: 1px solid rgba(15, 118, 110, 0.12);
  border-radius: 18px;
  padding: 12px 14px;
}
.cq-stat.alt {
  background: var(--cq-indigo-soft);
  border-color: rgba(79, 70, 229, 0.12);
}
#cq-side h3, #cq-side .prose h3, .cq-stat h3, .prose h3 {
  font-family: Fraunces, Georgia, serif !important;
  color: var(--cq-ink) !important;
  font-size: 1.05rem !important;
  margin: 0 0 6px !important;
  font-weight: 700 !important;
}
#cq-side .prose, #cq-side p, #cq-side li, .cq-stat p, .cq-stat li {
  color: var(--cq-muted) !important;
  font-size: 0.92rem !important;
}

.accordion {
  background: var(--cq-card) !important;
  border: 1px solid var(--cq-line) !important;
  border-radius: 18px !important;
  margin-top: 8px !important;
}

#cq-composer {
  display: flex;
  gap: 8px;
  align-items: stretch;
}

@media (max-width: 720px) {
  .gradio-container { padding: 10px 8px 28px !important; }
  #cq-shell { padding: 14px 12px 16px; border-radius: 22px; }
  #cq-stats { grid-template-columns: 1fr; }
  #cq-chatbot { min-height: 280px !important; }
  button.primary { min-height: 52px !important; font-size: 1.06rem !important; }
}

@media (min-width: 860px) {
  .gradio-container { padding: 24px 18px 48px !important; }
  #cq-shell { padding: 22px; }
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
        gr.update(visible=False),  # hide empty state once quest starts
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


def _toggle_custom(topic: str):
    return gr.update(visible=topic.startswith("I have my own"))


THEME = gr.themes.Base(
    font=gr.themes.GoogleFont("Plus Jakarta Sans"),
    font_mono=gr.themes.GoogleFont("Plus Jakarta Sans"),
    primary_hue="indigo",
    secondary_hue="teal",
    neutral_hue="slate",
    radius_size="lg",
    text_size="lg",
).set(
    body_background_fill="#f3f0ea",
    body_text_color="#1c2434",
    block_background_fill="#ffffff",
    block_border_color="rgba(28,36,52,0.08)",
    block_label_text_color="#5b6578",
    border_color_primary="rgba(28,36,52,0.08)",
    button_primary_background_fill="#4f46e5",
    button_primary_text_color="#ffffff",
    button_secondary_background_fill="#eef2ff",
    button_secondary_text_color="#4f46e5",
    shadow_drop="none",
    shadow_drop_lg="none",
)


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="CritiQuest", theme=THEME, css=CUSTOM_CSS, fill_height=False) as demo:
        with gr.Column(elem_id="cq-shell"):
            gr.HTML(
                """
                <div id="cq-hero">
                  <div id="cq-brand-row">
                    <div id="cq-brand">
                      <h1>CritiQuest</h1>
                      <p>A calm thinking coach for ages 8–14. Pick a quest — I’ll ask questions so <b>you</b> figure it out.</p>
                    </div>
                    <div id="cq-pill">Questions over answers</div>
                  </div>
                </div>
                """
            )

            state = gr.State({})

            with gr.Column(elem_classes=["cq-card"]):
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
                    visible=False,
                )
                header = gr.Markdown("")
                start_btn = gr.Button("Start quest", variant="primary", elem_id="cq-start")

            empty = gr.HTML(
                """
                <div id="cq-empty">
                  <strong>Ready when you are</strong>
                  Pick your age and a quest, then tap <b>Start quest</b>.
                  I’ll ask curious questions — you bring the ideas.
                </div>
                """,
                visible=True,
            )

            with gr.Column(elem_classes=["cq-card"]):
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=420,
                    type="messages",
                    elem_id="cq-chatbot",
                    show_copy_button=False,
                    render_markdown=True,
                    allow_tags=False,
                )
                with gr.Row(elem_id="cq-composer"):
                    msg = gr.Textbox(
                        label="Your thought",
                        placeholder="Share an idea…",
                        scale=5,
                        container=True,
                        show_label=True,
                    )
                    send = gr.Button("Send", variant="secondary", scale=1)

            with gr.Row(elem_id="cq-stats"):
                with gr.Column(elem_classes=["cq-card"], elem_id="cq-side", scale=1):
                    phase_md = gr.Markdown("### Quest step\nPress **Start quest**.")
                with gr.Column(elem_classes=["cq-card"], scale=1):
                    skills_md = gr.Markdown("### Thinking powers\n—")

            with gr.Column(elem_classes=["cq-card"]):
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

            topic.change(_toggle_custom, inputs=[topic], outputs=[custom])

            start_btn.click(
                start_session,
                inputs=[age, topic, custom],
                outputs=[chatbot, state, phase_md, skills_md, teacher_md, header, empty],
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
