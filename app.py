"""CritiQuest Gradio MVP. Socratic critical-thinking coach."""

from __future__ import annotations

import os

import gradio as gr

from prompts import topic_titles, TOPIC_SEEDS, topics_for_segment, is_under18
from socratic_engine import (
    SessionState,
    opening_message,
    respond,
    teacher_summary,
)

SEGMENT_IDS = ("middle", "teens", "early_adult", "adult", "unhurried")

SEGMENTS = {
    "middle": {
        "label": "Middle school · 8-12",
        "short": "Middle school",
        "hero": "Pick a topic. I ask. You think.",
        "pill": "I ask. You think.",
        "cta": "Let's begin",
        "empty": "Pick a topic.",
        "show_age": True,
        "age_choices": ["8-10", "11-12"],
        "age_default": "11-12",
        "engine_age": None,
    },
    "teens": {
        "label": "Teens · 13-17",
        "short": "Teens",
        "hero": "Bring a claim. I'll press.",
        "pill": "Questions first.",
        "cta": "Start thinking",
        "empty": "Pick a topic.",
        "show_age": True,
        "age_choices": ["13-14", "15-17"],
        "age_default": "13-14",
        "engine_age": None,
    },
    "early_adult": {
        "label": "Early adult · 18-24",
        "short": "Early adult",
        "hero": "A messy question. No handed answer.",
        "pill": "Think it through.",
        "cta": "Start",
        "empty": "Pick a topic.",
        "show_age": False,
        "age_choices": ["18-24"],
        "age_default": "18-24",
        "engine_age": "18-24",
    },
    "adult": {
        "label": "Adult · 25-64",
        "short": "Adult",
        "hero": "Clarify the decision. I ask. You decide.",
        "pill": "Clarity over noise.",
        "cta": "Begin",
        "empty": "Pick a topic.",
        "show_age": False,
        "age_choices": ["25-64"],
        "age_default": "25-64",
        "engine_age": "25-64",
    },
    "unhurried": {
        "label": "Unhurried · 65+",
        "short": "Unhurried",
        "hero": "One question at a time. Clear words. No rush.",
        "pill": "Steady questions.",
        "cta": "Begin",
        "empty": "Pick a topic.",
        "show_age": False,
        "age_choices": ["65+"],
        "age_default": "65+",
        "engine_age": "65+",
    },
}

AGE_CHOICES_ALL = ["8-10", "11-12", "13-14", "15-17", "18-24", "25-64", "65+"]
TOPICS = topic_titles() + ["I have my own question"]
DISCLOSURE = (
    "I help you think by asking questions, not by giving the answer."
)
CHIP_DISCLOSURE = "Questions, not answers."
CLARIFY_TOPIC = "What question do you want to explore?"
PRIDE_LINE = "Nice thinking. You stayed with the hard questions."
DONE_MESSAGE = "Nice thinking today. Come back anytime."
RETURN_EMPTY = "Pick a new topic, or the same one and go deeper."
LAND_HERO = "Who is this for?"
LAND_PILL = "One tap sets the look and the tone."
LAND_HELPER = "One tap sets the look and the tone."

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@500;600;700;800&family=Fraunces:opsz,wght@9..144,600;9..144,700;9..144,800&family=Inter:wght@400;500;600;700&family=Literata:opsz,wght@7..72,500;7..72,600;7..72,700&family=Nunito:wght@600;700;800&family=Space+Grotesk:wght@500;600;700&family=Space+Mono:wght@400;700&display=swap');

:root {
  --cq-bg: #efe6da;
  --cq-ink: #2c1f18;
  --cq-muted: #6b5346;
  --cq-card: #fff9f2;
  --cq-line: rgba(139, 90, 60, 0.14);
  --cq-indigo: #c46f48;
  --cq-indigo-soft: #fff8f0;
  --cq-teal: #a85736;
  --cq-teal-soft: #f5e6d6;
  --cq-shadow: 0 16px 40px rgba(139, 90, 60, 0.12);
  --cq-card-shadow: 0 8px 20px rgba(139, 90, 60, 0.10);
  --cq-radius: 28px;
  --cq-btn-radius: 999px;
  --cq-card-radius: 24px;
  --cq-font-scale: 1;
  --cq-body: 1rem;
  --cq-tap: 48px;
  --cq-pad: 22px;
  --cq-gap: 14px;
  --cq-land-min: 56px;
  --cq-land-radius: 18px;
  --cq-land-pad: 16px 18px;
  --cq-land-size: 1.02rem;
  --cq-chip-radius: 999px;
  --cq-chip-pad: 8px 12px;
  --cq-chip-size: 0.84rem;
  --cq-label-size: 0.78rem;
  --cq-density: 16px;
  --cq-font: 'Nunito', ui-sans-serif, system-ui, sans-serif;
  --cq-display: Fraunces, Georgia, serif;
  --cq-max: 920px;
  --cq-ease: cubic-bezier(.22,.8,.24,1);
  --cq-focus: 0 0 0 3px color-mix(in srgb, var(--cq-indigo) 35%, transparent);
}

html, body, .gradio-container {
  font-family: var(--cq-font) !important;
  background: var(--cq-bg) !important;
  color: var(--cq-ink) !important;
}
.gradio-container {
  max-width: var(--cq-max) !important;
  margin: 0 auto !important;
  padding: 18px 14px 48px !important;
}

/* ---- Nuclear Gradio chrome kill ---- */
footer, .footer, footer.svelte-1ipelgc,
.icon-button-wrapper.top-panel,
.fixed.bottom-0, .settings-panel,
.generating, .progress-bar,
.toast-wrap {
  display: none !important;
}
.main, .wrap, .contain, .panel, .block, .form,
.svelte-1ipelgc, .padded, .border, .hide-container,
div.svelte-90ou0b, .block.padded {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}
.block, .form, .panel { padding: 0 !important; margin: 0 !important; }
.gap { gap: var(--cq-gap) !important; }
.gradio-container .prose { max-width: none !important; }
label.svelte-1b6s6s4 .svelte-1b6s6s4 { background: transparent !important; }

#cq-shell {
  background:
    radial-gradient(ellipse 280px 200px at 12% 18%, rgba(196,112,74,.18), transparent 70%),
    radial-gradient(ellipse 240px 180px at 88% 12%, rgba(232,196,120,.22), transparent 65%),
    radial-gradient(ellipse 200px 160px at 70% 78%, rgba(120,150,110,.12), transparent 60%),
    linear-gradient(165deg, #f7f1e8 0%, #efe6da 45%, #e8ddd0 100%);
  border: 1px solid var(--cq-line);
  border-radius: var(--cq-radius);
  padding: var(--cq-pad) 18px 22px;
  box-shadow: var(--cq-shadow);
  font-size: calc(var(--cq-body) * var(--cq-font-scale));
  font-family: var(--cq-font) !important;
  position: relative;
  overflow: visible;
  color: var(--cq-ink) !important;
}
#cq-shell::before,
#cq-shell::after {
  content: "";
  position: absolute;
  pointer-events: none;
  z-index: 0;
  display: none;
}
#cq-shell > * { position: relative; z-index: 1; }
.gradio-container:has(#cq-shell.seg-middle),
.gradio-container:has(#cq-shell.seg-teens),
.gradio-container:has(#cq-shell.seg-early_adult),
.gradio-container:has(#cq-shell.seg-adult),
.gradio-container:has(#cq-shell.seg-unhurried) {
  background: var(--cq-bg) !important;
}

/* ============================================================
   MIDDLE: Soft clay / bubble (terracotta + cream)
   ============================================================ */
#cq-shell.seg-middle {
  --cq-bg: #f0e2d4; --cq-ink: #2c1f18; --cq-muted: #5a4338;
  --cq-indigo: #b8623c; --cq-indigo-soft: #fff8f0;
  --cq-teal: #8f4a2e; --cq-teal-soft: #f5e6d6;
  --cq-card: #fff9f2; --cq-line: rgba(139, 90, 60, 0.28);
  --cq-shadow: 0 16px 40px rgba(139, 90, 60, 0.14);
  --cq-card-shadow: 0 8px 20px rgba(139, 90, 60, 0.10), inset 0 1px 0 rgba(255,255,255,.7);
  --cq-radius: 28px; --cq-btn-radius: 999px; --cq-card-radius: 24px;
  --cq-font-scale: 1.02; --cq-body: 1.02rem; --cq-tap: 52px;
  --cq-pad: 22px; --cq-gap: 14px; --cq-density: 18px;
  --cq-land-min: 68px; --cq-land-radius: 28px; --cq-land-pad: 14px 16px; --cq-land-size: 1.06rem;
  --cq-chip-radius: 999px; --cq-chip-pad: 8px 14px; --cq-chip-size: 0.88rem; --cq-label-size: 0.8rem;
  --cq-font: 'Nunito', ui-sans-serif, system-ui, sans-serif;
  --cq-display: Fraunces, Georgia, serif; --cq-max: 920px;
  --cq-focus: 0 0 0 3px rgba(196, 111, 72, 0.35);
  background:
    radial-gradient(ellipse 220px 180px at 85% 8%, rgba(232,170,120,.45), transparent 70%),
    radial-gradient(ellipse 260px 200px at 5% 55%, rgba(196,112,74,.2), transparent 65%),
    radial-gradient(ellipse 180px 140px at 70% 90%, rgba(240,210,160,.35), transparent 60%),
    linear-gradient(180deg, #faf3ea 0%, #f0e2d4 100%);
  border-color: rgba(139, 90, 60, 0.18);
  font-family: var(--cq-font) !important;
  color: var(--cq-ink) !important;
  overflow: visible;
}
#cq-shell.seg-middle::before {
  display: block;
  width: 140px; height: 120px;
  background: rgba(232,180,140,.45);
  top: 70px; right: -36px;
  border-radius: 55% 45% 40% 60%;
  filter: blur(0.2px);
}
#cq-shell.seg-middle::after {
  display: block;
  width: 100px; height: 90px;
  background: rgba(200,120,80,.22);
  bottom: 140px; left: -32px;
  border-radius: 45% 55% 60% 40%;
}
#cq-shell.seg-middle #cq-brand h1 {
  font-family: var(--cq-display) !important;
  color: #8b5a3c !important;
  font-weight: 700 !important;
  font-size: clamp(1.1rem, 3vw, 1.25rem) !important;
  letter-spacing: 0.02em;
}
#cq-shell.seg-middle #cq-brand p {
  font-family: var(--cq-display) !important;
  font-weight: 800 !important;
  font-size: clamp(1.55rem, 4.5vw, 1.95rem) !important;
  color: #2c1f18 !important;
  letter-spacing: -0.02em;
  line-height: 1.18 !important;
  max-width: 22ch;
}
#cq-shell.seg-middle #cq-pill {
  background: #fff8f0 !important;
  color: #6b3f28 !important;
  border: 2px solid rgba(139,90,60,.25) !important;
  box-shadow: 0 6px 16px rgba(139,90,60,.12), inset 0 1px 0 #fff !important;
  font-weight: 800 !important;
}
#cq-shell.seg-middle #cq-disclosure,
#cq-shell.seg-middle #cq-session-chip {
  background: #fff8f0 !important;
  border: 2px solid rgba(139,90,60,.22) !important;
  border-radius: 999px !important;
  box-shadow: 0 4px 14px rgba(139,90,60,.10) !important;
  color: #3a2a22 !important;
}
#cq-shell.seg-middle #cq-session-chip::before { background: #e8b48a !important; }
#cq-shell.seg-middle .cq-card {
  background: linear-gradient(145deg, #fff9f2, #f5e6d6) !important;
  border: none !important;
  border-radius: 24px !important;
  box-shadow: 0 8px 20px rgba(139,90,60,.10), inset 0 1px 0 rgba(255,255,255,.7) !important;
}
#cq-shell.seg-middle #cq-chatbot,
#cq-shell.seg-middle #cq-chatbot .bubble-wrap,
#cq-shell.seg-middle #cq-chatbot .wrapper,
#cq-shell.seg-middle #cq-chatbot > .wrap {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}
#cq-shell.seg-middle #cq-chatbot .bot,
#cq-shell.seg-middle #cq-chatbot .assistant,
#cq-shell.seg-middle #cq-chatbot [data-testid="bot"],
#cq-shell.seg-middle .message.bot,
#cq-shell.seg-middle .bubble.bot {
  background: linear-gradient(145deg, #fff9f2, #f5e6d6) !important;
  color: #2c1f18 !important;
  border: none !important;
  border-radius: 22px 22px 22px 8px !important;
  box-shadow: 0 8px 20px rgba(139,90,60,.12), inset 0 1px 0 #fff !important;
  font-weight: 700 !important;
}
#cq-shell.seg-middle #cq-chatbot .user,
#cq-shell.seg-middle #cq-chatbot [data-testid="user"],
#cq-shell.seg-middle .message.user,
#cq-shell.seg-middle .bubble.user {
  background: linear-gradient(145deg, #c46f48, #a85736) !important;
  color: #fffaf5 !important;
  border: none !important;
  border-radius: 22px 22px 8px 22px !important;
  box-shadow: 0 8px 18px rgba(168,87,54,.28) !important;
  font-weight: 700 !important;
}
#cq-shell.seg-middle input,
#cq-shell.seg-middle textarea,
#cq-shell.seg-middle select,
#cq-shell.seg-middle .wrap-inner,
#cq-shell.seg-middle .secondary-wrap,
#cq-shell.seg-middle .scroll-hide,
#cq-shell.seg-middle #cq-age label {
  background: #fff8f0 !important;
  color: #2c1f18 !important;
  border: 2px solid rgba(139,90,60,.22) !important;
  border-radius: 999px !important;
  box-shadow: 0 6px 16px rgba(139,90,60,.10), inset 0 1px 0 #fff !important;
}
#cq-shell.seg-middle #cq-age label:has(input:checked),
#cq-shell.seg-middle #cq-age input:checked + span,
#cq-shell.seg-middle #cq-age label:has(input:checked) span {
  background: linear-gradient(145deg, #e8b48a, #d9966c) !important;
  color: #2c1a12 !important;
  border: none !important;
  box-shadow: 0 10px 22px rgba(180,90,40,.22), inset 0 1px 0 rgba(255,255,255,.35) !important;
}
#cq-shell.seg-middle button.primary,
#cq-shell.seg-middle #cq-start,
#cq-shell.seg-middle #cq-start button,
#cq-shell.seg-middle #cq-composer button.primary {
  background: linear-gradient(145deg, #c46f48, #a85736) !important;
  color: #fffaf5 !important;
  border: 2px solid #8f4a2e !important;
  border-radius: 999px !important;
  box-shadow: 0 12px 28px rgba(168,87,54,.35), inset 0 1px 0 rgba(255,255,255,.25) !important;
  font-weight: 800 !important;
  overflow: visible !important;
  white-space: normal !important;
  height: auto !important;
  min-height: var(--cq-tap) !important;
  padding: 12px 20px !important;
  line-height: 1.25 !important;
}
#cq-shell.seg-middle button.secondary {
  background: #fff8f0 !important;
  color: #6b3f28 !important;
  border: 2px solid rgba(139,90,60,.28) !important;
  border-radius: 999px !important;
  box-shadow: 0 6px 16px rgba(139,90,60,.1), inset 0 1px 0 #fff !important;
}
#cq-shell.seg-middle #cq-composer {
  background: #fff8f0 !important;
  border: 2px solid rgba(139,90,60,.22) !important;
  border-radius: 999px !important;
  padding: 8px 8px 8px 14px !important;
  box-shadow: 0 8px 22px rgba(139,90,60,.12), inset 0 1px 0 #fff !important;
  gap: 8px !important;
  overflow: visible !important;
  align-items: stretch !important;
}
#cq-shell.seg-middle #cq-composer input,
#cq-shell.seg-middle #cq-composer textarea,
#cq-shell.seg-middle #cq-composer .wrap-inner {
  background: transparent !important;
  box-shadow: none !important;
  border: none !important;
}
#cq-shell.seg-middle #cq-wrap-card {
  background: linear-gradient(145deg, #fff9f2, #f5e6d6) !important;
  border: none !important;
  border-radius: 32px !important;
  box-shadow: 0 16px 40px rgba(139,90,60,.16), inset 0 1px 0 #fff !important;
}
#cq-shell.seg-middle #cq-empty strong,
#cq-shell.seg-middle #cq-land-title,
#cq-shell.seg-middle #cq-wrap-card .cq-pride {
  font-family: Fraunces, Georgia, serif !important;
  color: #2c1f18 !important;
}
#cq-shell.seg-middle #cq-phase-pill {
  background: #fff8f0 !important;
  border: none !important;
  color: #8b5a3c !important;
  box-shadow: 0 4px 12px rgba(139,90,60,.08) !important;
}

/* ============================================================
   TEENS: Neo-brutal (thick borders, hard offsets, yellow/magenta)
   ============================================================ */
#cq-shell.seg-teens {
  --cq-bg: #f4f0e8; --cq-ink: #0a0a0a; --cq-muted: #0a0a0a;
  --cq-indigo: #ff2d95; --cq-indigo-soft: #ffe600;
  --cq-teal: #0a0a0a; --cq-teal-soft: #fff;
  --cq-card: #ffffff; --cq-line: #0a0a0a;
  --cq-shadow: 5px 5px 0 #0a0a0a;
  --cq-card-shadow: 4px 4px 0 #0a0a0a;
  --cq-radius: 0; --cq-btn-radius: 0; --cq-card-radius: 0;
  --cq-font-scale: 0.98; --cq-body: 0.95rem; --cq-tap: 52px;
  --cq-pad: 16px; --cq-gap: 12px; --cq-density: 14px;
  --cq-land-min: 68px; --cq-land-radius: 0; --cq-land-pad: 12px 14px; --cq-land-size: 0.95rem;
  --cq-chip-radius: 0; --cq-chip-pad: 6px 10px; --cq-chip-size: 0.78rem; --cq-label-size: 0.72rem;
  --cq-font: 'Space Grotesk', ui-sans-serif, system-ui, sans-serif;
  --cq-display: 'Space Mono', ui-monospace, monospace;
  --cq-max: 880px;
  --cq-focus: 0 0 0 3px #ffe600;
  background: #f4f0e8;
  background-image:
    linear-gradient(#0a0a0a 1px, transparent 1px),
    linear-gradient(90deg, #0a0a0a 1px, transparent 1px);
  background-size: 28px 28px;
  background-position: -1px -1px;
  border: 3px solid #0a0a0a;
  box-shadow: 6px 6px 0 #0a0a0a;
  font-family: var(--cq-font) !important;
  color: #0a0a0a !important;
}
#cq-shell.seg-teens #cq-brand h1 {
  font-family: 'Space Mono', monospace !important;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-size: 0.78rem !important;
  font-weight: 700 !important;
  background: #0a0a0a !important;
  color: #ffe600 !important;
  display: inline-block !important;
  padding: 6px 10px !important;
  margin-bottom: 10px !important;
}
#cq-shell.seg-teens #cq-brand p {
  font-family: 'Space Mono', monospace !important;
  font-weight: 700 !important;
  font-size: clamp(1.35rem, 4vw, 1.7rem) !important;
  text-transform: uppercase;
  letter-spacing: -0.04em;
  color: #0a0a0a !important;
  line-height: 1.15 !important;
  max-width: 22ch;
}
#cq-shell.seg-teens #cq-pill {
  background: #ff2d95 !important;
  color: #fff !important;
  border: 3px solid #0a0a0a !important;
  border-radius: 0 !important;
  box-shadow: 3px 3px 0 #0a0a0a !important;
  font-family: 'Space Mono', monospace !important;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-size: 0.72rem !important;
}
#cq-shell.seg-teens #cq-disclosure {
  background: #fff !important;
  border: 2px solid #0a0a0a !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  color: #0a0a0a !important;
  font-weight: 600 !important;
}
#cq-shell.seg-teens #cq-session-chip {
  background: #ffe600 !important;
  border: 3px solid #0a0a0a !important;
  border-radius: 0 !important;
  box-shadow: 3px 3px 0 #0a0a0a !important;
  color: #0a0a0a !important;
  font-family: 'Space Mono', monospace !important;
  font-size: 0.72rem !important;
  font-weight: 700 !important;
}
#cq-shell.seg-teens #cq-session-chip::before {
  width: auto; height: auto; border-radius: 0;
  background: #ff2d95 !important;
  color: #fff; border: 2px solid #0a0a0a;
  content: "";
  display: none;
}
#cq-shell.seg-teens #cq-session-chip .cq-chip-meta {
  background: #ff2d95 !important;
  color: #fff !important;
  border: 2px solid #0a0a0a !important;
  padding: 2px 8px !important;
  text-transform: uppercase;
  font-weight: 700 !important;
}
#cq-shell.seg-teens .cq-card {
  background: #fff !important;
  border: 3px solid #0a0a0a !important;
  border-radius: 0 !important;
  box-shadow: 4px 4px 0 #0a0a0a !important;
}
#cq-shell.seg-teens #cq-chatbot,
#cq-shell.seg-teens #cq-chatbot .bubble-wrap,
#cq-shell.seg-teens #cq-chatbot .wrapper,
#cq-shell.seg-teens #cq-chatbot > .wrap {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}
#cq-shell.seg-teens #cq-chatbot .bot,
#cq-shell.seg-teens #cq-chatbot .assistant,
#cq-shell.seg-teens #cq-chatbot [data-testid="bot"],
#cq-shell.seg-teens .message.bot,
#cq-shell.seg-teens .bubble.bot {
  background: #fff !important;
  color: #0a0a0a !important;
  border: 3px solid #0a0a0a !important;
  border-radius: 0 !important;
  box-shadow: 4px 4px 0 #0a0a0a !important;
  font-weight: 700 !important;
}
#cq-shell.seg-teens #cq-chatbot .user,
#cq-shell.seg-teens #cq-chatbot [data-testid="user"],
#cq-shell.seg-teens .message.user,
#cq-shell.seg-teens .bubble.user {
  background: #ff2d95 !important;
  color: #fff !important;
  border: 3px solid #0a0a0a !important;
  border-radius: 0 !important;
  box-shadow: 4px 4px 0 #0a0a0a !important;
  font-weight: 700 !important;
}
#cq-shell.seg-teens input,
#cq-shell.seg-teens textarea,
#cq-shell.seg-teens select,
#cq-shell.seg-teens .wrap-inner,
#cq-shell.seg-teens .secondary-wrap,
#cq-shell.seg-teens .scroll-hide,
#cq-shell.seg-teens #cq-age label {
  background: #fff !important;
  color: #0a0a0a !important;
  border: 3px solid #0a0a0a !important;
  border-radius: 0 !important;
  box-shadow: 4px 4px 0 #0a0a0a !important;
}
#cq-shell.seg-teens #cq-age label:has(input:checked),
#cq-shell.seg-teens #cq-age input:checked + span,
#cq-shell.seg-teens #cq-age label:has(input:checked) span {
  background: #ffe600 !important;
  color: #0a0a0a !important;
  border: 3px solid #0a0a0a !important;
  box-shadow: 4px 4px 0 #0a0a0a !important;
}
#cq-shell.seg-teens button.primary,
#cq-shell.seg-teens #cq-start,
#cq-shell.seg-teens #cq-start button,
#cq-shell.seg-teens #cq-composer button.primary {
  background: #ff2d95 !important;
  color: #fff !important;
  border: 3px solid #0a0a0a !important;
  border-radius: 0 !important;
  box-shadow: 5px 5px 0 #0a0a0a !important;
  font-family: 'Space Mono', monospace !important;
  text-transform: uppercase;
  letter-spacing: -0.02em;
  font-weight: 700 !important;
  overflow: visible !important;
  white-space: normal !important;
  height: auto !important;
  min-height: var(--cq-tap) !important;
  padding: 12px 16px !important;
  line-height: 1.2 !important;
}
#cq-shell.seg-teens button.secondary {
  background: #fff !important;
  color: #0a0a0a !important;
  border: 3px solid #0a0a0a !important;
  border-radius: 0 !important;
  box-shadow: 4px 4px 0 #0a0a0a !important;
}
#cq-shell.seg-teens #cq-composer {
  border: 3px solid #0a0a0a !important;
  background: #fff !important;
  box-shadow: 4px 4px 0 #0a0a0a !important;
  border-radius: 0 !important;
  gap: 0 !important;
  padding: 0 !important;
  overflow: visible !important;
  align-items: stretch !important;
}
#cq-shell.seg-teens #cq-composer input,
#cq-shell.seg-teens #cq-composer textarea,
#cq-shell.seg-teens #cq-composer .wrap-inner {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 0 !important;
}
#cq-shell.seg-teens #cq-composer button.primary {
  border: none !important;
  border-left: 3px solid #0a0a0a !important;
  background: #0a0a0a !important;
  color: #ffe600 !important;
  box-shadow: none !important;
  min-width: 108px !important;
  border-radius: 0 !important;
  padding: 12px 16px !important;
  overflow: visible !important;
  white-space: nowrap !important;
  flex: 0 0 auto !important;
  height: auto !important;
  min-height: var(--cq-tap) !important;
}
#cq-shell.seg-teens #cq-wrap-card {
  background: #fff !important;
  border: 3px solid #0a0a0a !important;
  border-radius: 0 !important;
  box-shadow: 5px 5px 0 #0a0a0a !important;
}
#cq-shell.seg-teens #cq-empty strong,
#cq-shell.seg-teens #cq-land-title,
#cq-shell.seg-teens #cq-wrap-card .cq-pride {
  font-family: 'Space Mono', monospace !important;
  text-transform: uppercase;
  letter-spacing: -0.03em;
  color: #0a0a0a !important;
}
#cq-shell.seg-teens #cq-empty,
#cq-shell.seg-teens #cq-empty .cq-empty-body,
#cq-shell.seg-teens label,
#cq-shell.seg-teens .label-wrap span {
  color: #0a0a0a !important;
}
#cq-shell.seg-teens #cq-phase-pill {
  background: #ffe600 !important;
  border: 3px solid #0a0a0a !important;
  border-radius: 0 !important;
  color: #0a0a0a !important;
  box-shadow: 3px 3px 0 #0a0a0a !important;
  font-family: 'Space Mono', monospace !important;
}
#cq-shell.seg-teens button:hover { transform: translate(-1px, -1px) !important; }
#cq-shell.seg-teens button:active { transform: translate(1px, 1px) !important; }

/* ============================================================
   EARLY ADULT: Glassmorphism (frosted, cyan/violet)
   ============================================================ */
#cq-shell.seg-early_adult {
  --cq-bg: #0b1220; --cq-ink: #f8fafc; --cq-muted: #cbd5e1;
  --cq-indigo: #38bdf8; --cq-indigo-soft: rgba(125,211,252,.22);
  --cq-teal: #a5b4fc; --cq-teal-soft: rgba(129,140,248,.22);
  --cq-card: rgba(255,255,255,.14); --cq-line: rgba(255,255,255,.38);
  --cq-shadow: 0 12px 40px rgba(0,0,0,.25);
  --cq-card-shadow: 0 12px 40px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,255,255,.25);
  --cq-radius: 22px; --cq-btn-radius: 999px; --cq-card-radius: 16px;
  --cq-font-scale: 1; --cq-body: 1rem; --cq-tap: 52px;
  --cq-pad: 20px; --cq-gap: 14px; --cq-density: 18px;
  --cq-land-min: 68px; --cq-land-radius: 16px; --cq-land-pad: 14px 16px; --cq-land-size: 1rem;
  --cq-chip-radius: 999px; --cq-chip-pad: 6px 12px; --cq-chip-size: 0.8rem; --cq-label-size: 0.74rem;
  --cq-font: 'Inter', ui-sans-serif, system-ui, sans-serif;
  --cq-display: 'Inter', ui-sans-serif, system-ui, sans-serif;
  --cq-max: 960px;
  --cq-focus: 0 0 0 3px rgba(56,189,248,.4);
  background:
    radial-gradient(ellipse 280px 240px at 10% 0%, rgba(56,189,248,.55), transparent 55%),
    radial-gradient(ellipse 260px 220px at 95% 30%, rgba(167,139,250,.45), transparent 50%),
    radial-gradient(ellipse 300px 260px at 40% 100%, rgba(34,211,238,.35), transparent 55%),
    linear-gradient(160deg, #0b1220 0%, #132038 40%, #1a2744 100%);
  border: 1px solid rgba(255,255,255,.16);
  box-shadow: 0 16px 48px rgba(0,0,0,.35);
  font-family: var(--cq-font) !important;
  color: #e8eef8 !important;
}
#cq-shell.seg-early_adult #cq-brand h1 {
  font-family: var(--cq-display) !important;
  font-weight: 600 !important;
  letter-spacing: 0.04em;
  color: #e2e8f0 !important;
  font-size: 0.85rem !important;
}
#cq-shell.seg-early_adult #cq-brand p {
  font-weight: 650 !important;
  font-size: clamp(1.45rem, 4vw, 1.85rem) !important;
  letter-spacing: -0.03em;
  color: #f8fafc !important;
  line-height: 1.2 !important;
  max-width: 22ch;
}
#cq-shell.seg-early_adult #cq-pill {
  background: rgba(125,211,252,.18) !important;
  color: #e0f2fe !important;
  border: 2px solid rgba(125,211,252,.55) !important;
  border-radius: 999px !important;
  box-shadow: none !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em;
}
#cq-shell.seg-early_adult #cq-brand-row,
#cq-shell.seg-early_adult #cq-hero {
  background: rgba(255,255,255,.10) !important;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,.22) !important;
  border-radius: 22px !important;
  box-shadow: 0 12px 40px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,255,255,.25) !important;
  padding: 18px 16px !important;
}
#cq-shell.seg-early_adult #cq-disclosure {
  background: rgba(255,255,255,.06) !important;
  border: 1px solid rgba(255,255,255,.14) !important;
  color: #e2e8f0 !important;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: none !important;
}
#cq-shell.seg-early_adult #cq-session-chip {
  background: rgba(255,255,255,.14) !important;
  border: 2px solid rgba(255,255,255,.32) !important;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  color: #f8fafc !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.2) !important;
}
#cq-shell.seg-early_adult #cq-session-chip::before { background: #38bdf8 !important; }
#cq-shell.seg-early_adult .cq-card {
  background: rgba(255,255,255,.12) !important;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 2px solid rgba(255,255,255,.28) !important;
  border-radius: 16px !important;
  box-shadow: 0 8px 24px rgba(0,0,0,.2), inset 0 1px 0 rgba(255,255,255,.18) !important;
  color: #e2e8f0 !important;
}
#cq-shell.seg-early_adult #cq-chatbot,
#cq-shell.seg-early_adult #cq-chatbot .bubble-wrap,
#cq-shell.seg-early_adult #cq-chatbot .wrapper,
#cq-shell.seg-early_adult #cq-chatbot > .wrap {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}
#cq-shell.seg-early_adult #cq-chatbot .bot,
#cq-shell.seg-early_adult #cq-chatbot .assistant,
#cq-shell.seg-early_adult #cq-chatbot [data-testid="bot"],
#cq-shell.seg-early_adult .message.bot,
#cq-shell.seg-early_adult .bubble.bot {
  background: rgba(255,255,255,.10) !important;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  color: #f8fafc !important;
  border: 2px solid rgba(255,255,255,.28) !important;
  border-radius: 16px !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.2) !important;
}
#cq-shell.seg-early_adult #cq-chatbot .user,
#cq-shell.seg-early_adult #cq-chatbot [data-testid="user"],
#cq-shell.seg-early_adult .message.user,
#cq-shell.seg-early_adult .bubble.user {
  background: rgba(125,211,252,.28) !important;
  color: #f8fafc !important;
  border: 2px solid rgba(125,211,252,.6) !important;
  border-radius: 16px !important;
  box-shadow: 0 0 0 1px rgba(125,211,252,.2), 0 8px 24px rgba(14,165,233,.15) !important;
}
#cq-shell.seg-early_adult input,
#cq-shell.seg-early_adult textarea,
#cq-shell.seg-early_adult select,
#cq-shell.seg-early_adult .wrap-inner,
#cq-shell.seg-early_adult .secondary-wrap,
#cq-shell.seg-early_adult .scroll-hide,
#cq-shell.seg-early_adult #cq-age label {
  background: rgba(255,255,255,.12) !important;
  color: #f8fafc !important;
  border: 2px solid rgba(255,255,255,.32) !important;
  border-radius: 16px !important;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}
#cq-shell.seg-early_adult #cq-age label:has(input:checked),
#cq-shell.seg-early_adult #cq-age input:checked + span,
#cq-shell.seg-early_adult #cq-age label:has(input:checked) span {
  background: rgba(125,211,252,.18) !important;
  border-color: rgba(125,211,252,.45) !important;
  color: #f0f9ff !important;
}
#cq-shell.seg-early_adult button.primary,
#cq-shell.seg-early_adult #cq-start,
#cq-shell.seg-early_adult #cq-start button,
#cq-shell.seg-early_adult #cq-composer button.primary {
  background: linear-gradient(135deg, #38bdf8, #818cf8) !important;
  color: #0b1220 !important;
  border: 2px solid rgba(224,242,254,.7) !important;
  border-radius: 999px !important;
  box-shadow: 0 12px 32px rgba(56,189,248,.35), inset 0 1px 0 rgba(255,255,255,.4) !important;
  font-weight: 700 !important;
  overflow: visible !important;
  white-space: normal !important;
  height: auto !important;
  min-height: var(--cq-tap) !important;
  padding: 12px 20px !important;
  line-height: 1.25 !important;
}
#cq-shell.seg-early_adult button.secondary {
  background: rgba(255,255,255,.12) !important;
  color: #f8fafc !important;
  border: 2px solid rgba(255,255,255,.35) !important;
  border-radius: 999px !important;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}
#cq-shell.seg-early_adult #cq-composer {
  background: rgba(255,255,255,.12) !important;
  border: 2px solid rgba(255,255,255,.32) !important;
  border-radius: 999px !important;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  padding: 8px 8px 8px 14px !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.15) !important;
  overflow: visible !important;
  align-items: stretch !important;
}
#cq-shell.seg-early_adult #cq-composer input,
#cq-shell.seg-early_adult #cq-composer textarea,
#cq-shell.seg-early_adult #cq-composer .wrap-inner {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: #f8fafc !important;
}
#cq-shell.seg-early_adult #cq-wrap-card {
  background: rgba(255,255,255,.10) !important;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,.22) !important;
  border-radius: 22px !important;
  box-shadow: 0 12px 40px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,255,255,.25) !important;
}
#cq-shell.seg-early_adult #cq-empty,
#cq-shell.seg-early_adult #cq-empty strong,
#cq-shell.seg-early_adult #cq-wrap-card .cq-pride,
#cq-shell.seg-early_adult label,
#cq-shell.seg-early_adult .label-wrap span {
  color: #f8fafc !important;
}
#cq-shell.seg-early_adult #cq-empty .cq-empty-body,
#cq-shell.seg-early_adult #cq-session-chip .cq-chip-meta {
  color: #cbd5e1 !important;
}
#cq-shell.seg-early_adult #cq-empty strong,
#cq-shell.seg-early_adult #cq-land-title,
#cq-shell.seg-early_adult #cq-wrap-card .cq-pride {
  font-family: 'Inter', sans-serif !important;
}
#cq-shell.seg-early_adult #cq-phase-pill {
  background: rgba(125,211,252,.12) !important;
  color: #e0f2fe !important;
  border: 2px solid rgba(125,211,252,.5) !important;
}
#cq-shell.seg-early_adult #cq-change-seg button,
#cq-shell.seg-early_adult button#cq-change-seg,
#cq-shell.seg-early_adult .accordion > .label-wrap,
#cq-shell.seg-early_adult .accordion .label-wrap {
  color: #cbd5e1 !important;
}
.gradio-container:has(#cq-shell.seg-early_adult) {
  background: #0b1220 !important;
}

/* ============================================================
   ADULT: Swiss flat (B/W + red hairlines)
   ============================================================ */
#cq-shell.seg-adult {
  --cq-bg: #fafafa; --cq-ink: #111; --cq-muted: #333;
  --cq-indigo: #111; --cq-indigo-soft: #f0f0f0;
  --cq-teal: #e11d48; --cq-teal-soft: #fff1f2;
  --cq-card: #ffffff; --cq-line: #111;
  --cq-shadow: none; --cq-card-shadow: none;
  --cq-radius: 0; --cq-btn-radius: 0; --cq-card-radius: 0;
  --cq-font-scale: 0.98; --cq-body: 0.95rem; --cq-tap: 48px;
  --cq-pad: 18px; --cq-gap: 10px; --cq-density: 12px;
  --cq-land-min: 68px; --cq-land-radius: 0; --cq-land-pad: 14px 12px; --cq-land-size: 0.95rem;
  --cq-chip-radius: 0; --cq-chip-pad: 5px 0; --cq-chip-size: 0.76rem; --cq-label-size: 0.7rem;
  --cq-font: 'Inter', Helvetica, Arial, sans-serif;
  --cq-display: 'Inter', Helvetica, Arial, sans-serif;
  --cq-max: 860px;
  --cq-focus: 0 0 0 2px #e11d48;
  background: #fafafa;
  border: none;
  box-shadow: none;
  border-radius: 0;
  font-family: var(--cq-font) !important;
  color: #111 !important;
}
#cq-shell.seg-adult #cq-brand-row {
  border-bottom: 2px solid #111;
  padding-bottom: 12px;
  margin-bottom: 8px;
  align-items: end !important;
}
#cq-shell.seg-adult #cq-brand h1 {
  font-family: var(--cq-display) !important;
  font-size: 0.82rem !important;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-weight: 700 !important;
  color: #111 !important;
}
#cq-shell.seg-adult #cq-brand p {
  font-weight: 600 !important;
  font-size: clamp(1.55rem, 4.2vw, 2rem) !important;
  letter-spacing: -0.04em;
  color: #111 !important;
  line-height: 1.12 !important;
  max-width: 20ch;
}
#cq-shell.seg-adult #cq-pill {
  background: transparent !important;
  color: #e11d48 !important;
  border: none !important;
  box-shadow: none !important;
  font-size: 0.72rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 0 !important;
}
#cq-shell.seg-adult #cq-disclosure {
  background: transparent !important;
  border: none !important;
  border-top: 1px solid #ddd !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  color: #333 !important;
  padding: 14px 0 0 !important;
}
#cq-shell.seg-adult #cq-session-chip {
  background: transparent !important;
  border: none !important;
  border-bottom: 2px solid #111 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  padding: 0 0 10px !important;
  color: #111 !important;
  font-weight: 500 !important;
}
#cq-shell.seg-adult #cq-session-chip::before { display: none !important; }
#cq-shell.seg-adult #cq-session-chip .cq-chip-meta {
  color: #e11d48 !important;
  font-weight: 600 !important;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-size: 0.72rem !important;
}
#cq-shell.seg-adult .cq-card {
  background: transparent !important;
  border: none !important;
  border-top: 1px solid #111 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
}
#cq-shell.seg-adult #cq-chatbot,
#cq-shell.seg-adult #cq-chatbot .bubble-wrap,
#cq-shell.seg-adult #cq-chatbot .wrapper,
#cq-shell.seg-adult #cq-chatbot > .wrap {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 0 !important;
}
#cq-shell.seg-adult #cq-chatbot .bot,
#cq-shell.seg-adult #cq-chatbot .assistant,
#cq-shell.seg-adult #cq-chatbot [data-testid="bot"],
#cq-shell.seg-adult .message.bot,
#cq-shell.seg-adult .bubble.bot {
  background: transparent !important;
  color: #111 !important;
  border: none !important;
  border-left: 3px solid #e11d48 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  padding-left: 16px !important;
  font-weight: 500 !important;
  font-size: calc(1.15rem * var(--cq-font-scale)) !important;
  letter-spacing: -0.02em;
}
#cq-shell.seg-adult #cq-chatbot .user,
#cq-shell.seg-adult #cq-chatbot [data-testid="user"],
#cq-shell.seg-adult .message.user,
#cq-shell.seg-adult .bubble.user {
  background: #111 !important;
  color: #fff !important;
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  font-weight: 400 !important;
}
#cq-shell.seg-adult input,
#cq-shell.seg-adult textarea,
#cq-shell.seg-adult select,
#cq-shell.seg-adult .wrap-inner,
#cq-shell.seg-adult .secondary-wrap,
#cq-shell.seg-adult .scroll-hide {
  background: transparent !important;
  color: #111 !important;
  border: none !important;
  border-bottom: 1px solid #111 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  min-height: 44px !important;
}
#cq-shell.seg-adult #cq-age label {
  background: transparent !important;
  border: none !important;
  border-bottom: 1px solid #111 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  justify-content: space-between !important;
}
#cq-shell.seg-adult #cq-age label:has(input:checked),
#cq-shell.seg-adult #cq-age input:checked + span,
#cq-shell.seg-adult #cq-age label:has(input:checked) span {
  background: transparent !important;
  color: #111 !important;
  font-weight: 600 !important;
  border-color: #111 !important;
}
#cq-shell.seg-adult button.primary,
#cq-shell.seg-adult #cq-start,
#cq-shell.seg-adult #cq-start button,
#cq-shell.seg-adult #cq-composer button.primary {
  background: #111 !important;
  color: #fff !important;
  border: 2px solid #111 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-size: 0.88rem !important;
  font-weight: 600 !important;
  overflow: visible !important;
  white-space: normal !important;
  height: auto !important;
  min-height: var(--cq-tap) !important;
  padding: 12px 18px !important;
  line-height: 1.25 !important;
}
#cq-shell.seg-adult button.secondary {
  background: transparent !important;
  color: #111 !important;
  border: 2px solid #111 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-size: 0.82rem !important;
}
#cq-shell.seg-adult #cq-composer {
  border-top: 2px solid #111 !important;
  border-radius: 0 !important;
  padding-top: 12px !important;
  gap: 8px !important;
  background: transparent !important;
  overflow: visible !important;
  align-items: stretch !important;
}
#cq-shell.seg-adult #cq-composer input,
#cq-shell.seg-adult #cq-composer textarea,
#cq-shell.seg-adult #cq-composer .wrap-inner {
  border: none !important;
  background: transparent !important;
}
#cq-shell.seg-adult #cq-wrap-card {
  background: #fff !important;
  border: 1px solid #111 !important;
  border-left: 4px solid #e11d48 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
}
#cq-shell.seg-adult #cq-empty strong,
#cq-shell.seg-adult #cq-land-title,
#cq-shell.seg-adult #cq-wrap-card .cq-pride {
  font-family: 'Inter', Helvetica, Arial, sans-serif !important;
  letter-spacing: -0.03em;
}
#cq-shell.seg-adult #cq-phase-pill {
  background: transparent !important;
  border: none !important;
  border-bottom: 1px solid #111 !important;
  border-radius: 0 !important;
  color: #e11d48 !important;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-size: 0.72rem !important;
  padding: 0 0 8px !important;
}
#cq-shell.seg-adult #cq-phase-pill > span:first-child { color: #666 !important; }

/* ============================================================
   UNHURRIED: Soft neumorphism (sage, large type)
   ============================================================ */
#cq-shell.seg-unhurried {
  --cq-bg: #e6e9e1; --cq-ink: #1f2c24; --cq-muted: #2f3d32;
  --cq-indigo: #2f3d32; --cq-indigo-soft: #e6e9e1;
  --cq-teal: #2f3d32; --cq-teal-soft: #dfe4d8;
  --cq-card: #e6e9e1; --cq-line: rgba(31,44,36,.22);
  --cq-shadow: 8px 8px 18px #c4cbc0, -8px -8px 18px #ffffff;
  --cq-card-shadow: 7px 7px 16px #c4cbc0, -7px -7px 16px #ffffff;
  --cq-radius: 22px; --cq-btn-radius: 999px; --cq-card-radius: 20px;
  --cq-font-scale: 1.22; --cq-body: 1.2rem; --cq-tap: 60px;
  --cq-pad: 24px; --cq-gap: 16px; --cq-density: 20px;
  --cq-land-min: 72px; --cq-land-radius: 22px; --cq-land-pad: 18px 20px; --cq-land-size: 1.15rem;
  --cq-chip-radius: 999px; --cq-chip-pad: 12px 18px; --cq-chip-size: 1rem; --cq-label-size: 1rem;
  --cq-font: 'DM Sans', ui-sans-serif, system-ui, sans-serif;
  --cq-display: Literata, Georgia, serif;
  --cq-max: 720px;
  --cq-focus: 0 0 0 3px rgba(61, 82, 68, 0.28);
  background: #e6e9e1;
  border: none;
  box-shadow: none;
  font-family: var(--cq-font) !important;
  color: #2f3d32 !important;
}
#cq-shell.seg-unhurried #cq-brand h1 {
  font-family: Literata, Georgia, serif !important;
  font-size: clamp(1.15rem, 3vw, 1.35rem) !important;
  font-weight: 600 !important;
  color: #3d5244 !important;
  letter-spacing: 0;
}
#cq-shell.seg-unhurried #cq-brand p {
  font-family: Literata, Georgia, serif !important;
  font-weight: 600 !important;
  font-size: clamp(1.7rem, 5vw, 2.1rem) !important;
  line-height: 1.25 !important;
  color: #2a382e !important;
  max-width: 22ch;
}
#cq-shell.seg-unhurried #cq-brand p,
#cq-shell.seg-unhurried #cq-disclosure,
#cq-shell.seg-unhurried #cq-chatbot .message,
#cq-shell.seg-unhurried #cq-land-sub,
#cq-shell.seg-unhurried #cq-empty {
  font-size: 1.15rem !important;
  line-height: 1.55 !important;
}
#cq-shell.seg-unhurried #cq-pill {
  background: #e6e9e1 !important;
  color: #1f2c24 !important;
  border: 2px solid rgba(31,44,36,.2) !important;
  border-radius: 999px !important;
  box-shadow: 6px 6px 14px #c4cbc0, -6px -6px 14px #ffffff !important;
  font-size: 0.95rem !important;
  font-weight: 600 !important;
  padding: 12px 18px !important;
}
#cq-shell.seg-unhurried #cq-disclosure,
#cq-shell.seg-unhurried #cq-session-chip {
  background: #e6e9e1 !important;
  border: 2px solid rgba(31,44,36,.2) !important;
  border-radius: 20px !important;
  box-shadow: 6px 6px 14px #c4cbc0, -6px -6px 14px #ffffff !important;
  color: #1f2c24 !important;
}
#cq-shell.seg-unhurried #cq-session-chip::before { background: #4a6354 !important; }
#cq-shell.seg-unhurried label,
#cq-shell.seg-unhurried .label-wrap span,
#cq-shell.seg-unhurried span.svelte-1gfkn6j {
  font-size: 1rem !important;
  letter-spacing: 0 !important;
}
#cq-shell.seg-unhurried button { min-height: 60px !important; font-size: 1.12rem !important; }
#cq-shell.seg-unhurried #cq-pill,
#cq-shell.seg-unhurried .cq-chip-meta { font-size: 1rem !important; }
#cq-shell.seg-unhurried .cq-card {
  background: #e6e9e1 !important;
  border: none !important;
  border-radius: 20px !important;
  box-shadow: 7px 7px 16px #c4cbc0, -7px -7px 16px #ffffff !important;
  padding: 22px !important;
}
#cq-shell.seg-unhurried #cq-chatbot,
#cq-shell.seg-unhurried #cq-chatbot .bubble-wrap,
#cq-shell.seg-unhurried #cq-chatbot .wrapper,
#cq-shell.seg-unhurried #cq-chatbot > .wrap {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}
#cq-shell.seg-unhurried #cq-chatbot .bot,
#cq-shell.seg-unhurried #cq-chatbot .assistant,
#cq-shell.seg-unhurried #cq-chatbot [data-testid="bot"],
#cq-shell.seg-unhurried .message.bot,
#cq-shell.seg-unhurried .bubble.bot {
  background: #e6e9e1 !important;
  color: #2f3d32 !important;
  border: none !important;
  border-radius: 20px !important;
  box-shadow: 7px 7px 16px #c4cbc0, -7px -7px 16px #ffffff !important;
  font-size: 1.15rem !important;
}
#cq-shell.seg-unhurried #cq-chatbot .user,
#cq-shell.seg-unhurried #cq-chatbot [data-testid="user"],
#cq-shell.seg-unhurried .message.user,
#cq-shell.seg-unhurried .bubble.user {
  background: #e6e9e1 !important;
  color: #1f2c24 !important;
  border: none !important;
  border-radius: 20px !important;
  box-shadow: inset 5px 5px 12px #c4cbc0, inset -5px -5px 12px #ffffff !important;
  font-weight: 600 !important;
}
#cq-shell.seg-unhurried input,
#cq-shell.seg-unhurried textarea,
#cq-shell.seg-unhurried select,
#cq-shell.seg-unhurried .wrap-inner,
#cq-shell.seg-unhurried .secondary-wrap,
#cq-shell.seg-unhurried .scroll-hide,
#cq-shell.seg-unhurried #cq-age label {
  background: #e6e9e1 !important;
  color: #2f3d32 !important;
  border: none !important;
  border-radius: 20px !important;
  box-shadow: 7px 7px 16px #c4cbc0, -7px -7px 16px #ffffff !important;
  font-size: 1.1rem !important;
}
#cq-shell.seg-unhurried #cq-age label:has(input:checked),
#cq-shell.seg-unhurried #cq-age input:checked + span,
#cq-shell.seg-unhurried #cq-age label:has(input:checked) span {
  background: #e6e9e1 !important;
  color: #1f2c24 !important;
  box-shadow: inset 5px 5px 12px #c4cbc0, inset -5px -5px 12px #ffffff !important;
  border: none !important;
  font-weight: 600 !important;
}
#cq-shell.seg-unhurried button.primary,
#cq-shell.seg-unhurried #cq-start,
#cq-shell.seg-unhurried #cq-start button,
#cq-shell.seg-unhurried #cq-composer button.primary {
  background: #e6e9e1 !important;
  color: #1f2c24 !important;
  border: 2px solid rgba(31,44,36,.22) !important;
  border-radius: 999px !important;
  box-shadow: 8px 8px 18px #c4cbc0, -8px -8px 18px #ffffff !important;
  min-height: 60px !important;
  font-weight: 700 !important;
  overflow: visible !important;
  white-space: normal !important;
  height: auto !important;
  padding: 14px 22px !important;
  line-height: 1.25 !important;
}
#cq-shell.seg-unhurried button.secondary {
  background: #e6e9e1 !important;
  color: #1f2c24 !important;
  border: 2px solid rgba(31,44,36,.22) !important;
  border-radius: 999px !important;
  box-shadow: 6px 6px 14px #c4cbc0, -6px -6px 14px #ffffff !important;
}
#cq-shell.seg-unhurried #cq-composer {
  background: #e6e9e1 !important;
  border: 2px solid rgba(31,44,36,.2) !important;
  border-radius: 999px !important;
  box-shadow: 8px 8px 18px #c4cbc0, -8px -8px 18px #ffffff !important;
  padding: 8px 8px 8px 18px !important;
  overflow: visible !important;
  align-items: stretch !important;
}
#cq-shell.seg-unhurried #cq-composer input,
#cq-shell.seg-unhurried #cq-composer textarea,
#cq-shell.seg-unhurried #cq-composer .wrap-inner {
  background: transparent !important;
  box-shadow: none !important;
  border: none !important;
}
#cq-shell.seg-unhurried #cq-wrap-card {
  background: #e6e9e1 !important;
  border: none !important;
  border-radius: 28px !important;
  box-shadow: 10px 10px 22px #c4cbc0, -10px -10px 22px #ffffff !important;
}
#cq-shell.seg-unhurried #cq-empty strong,
#cq-shell.seg-unhurried #cq-land-title,
#cq-shell.seg-unhurried #cq-wrap-card .cq-pride {
  font-family: Literata, Georgia, serif !important;
  color: #2a382e !important;
}
#cq-shell.seg-unhurried #cq-phase-pill {
  background: #e6e9e1 !important;
  border: 2px solid rgba(31,44,36,.2) !important;
  color: #1f2c24 !important;
  box-shadow: 5px 5px 12px #c4cbc0, -5px -5px 12px #ffffff !important;
  font-size: 1rem !important;
}
.gradio-container:has(#cq-shell.seg-unhurried) { max-width: 720px !important; background: #e6e9e1 !important; }

/* ============================================================
   LAND: editorial chip mosaic (only surface before tap)
   ============================================================ */
#cq-land {
  display: grid !important;
  grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  gap: 12px !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 4px 0 0 !important;
  margin: 0 !important;
}
#cq-land > .form,
#cq-land > .block,
#cq-land > div:not(#cq-land-head) {
  width: 100% !important;
  margin: 0 !important;
  min-width: 0 !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}
#cq-land-head {
  grid-column: 1 / -1 !important;
  margin: 0 0 6px !important;
  padding: 8px 2px 10px !important;
}
#cq-land-title {
  font-family: var(--cq-display);
  font-size: clamp(1.85rem, 5vw, 2.45rem);
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.12;
  color: #2c1f18;
  margin: 0 0 8px;
}
#cq-land-sub {
  color: #3a2a22;
  font-size: 1.02rem;
  font-weight: 600;
  margin: 0;
  line-height: 1.45;
  max-width: 36ch;
}
#cq-land button,
#cq-land .cq-land-chip {
  width: 100% !important;
  min-height: max(68px, var(--cq-land-min)) !important;
  height: auto !important;
  max-height: none !important;
  margin: 0 !important;
  border-radius: var(--cq-land-radius) !important;
  font-weight: 700 !important;
  font-size: var(--cq-land-size) !important;
  text-align: left !important;
  justify-content: flex-start !important;
  align-items: flex-start !important;
  padding: var(--cq-land-pad) !important;
  transition:
    transform .18s var(--cq-ease),
    box-shadow .18s var(--cq-ease),
    border-color .18s var(--cq-ease),
    background .18s var(--cq-ease),
    color .18s var(--cq-ease) !important;
  box-shadow: var(--cq-card-shadow) !important;
  position: relative !important;
  overflow: visible !important;
  white-space: normal !important;
  line-height: 1.25 !important;
  text-overflow: clip !important;
  flex-shrink: 0 !important;
}
#cq-land button span,
#cq-land .cq-land-chip span,
#cq-land button > * {
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: clip !important;
  height: auto !important;
  max-height: none !important;
  line-height: 1.25 !important;
  flex-shrink: 1 !important;
}
#cq-land button:hover {
  transform: translateY(-2px) !important;
  filter: none !important;
}
#cq-land button:active {
  transform: translateY(0) scale(0.985) !important;
}
#cq-land button:focus-visible {
  outline: none !important;
  box-shadow: var(--cq-focus), var(--cq-card-shadow) !important;
}

/* Identity chips on land (each previews its world) */
#cq-seg-middle {
  border-radius: 28px 32px 26px 30px !important;
  background: linear-gradient(145deg, #f3d9c4, #e8c4a8) !important;
  color: #3a2a22 !important;
  border: 2px solid rgba(74,46,32,.25) !important;
  box-shadow: 0 10px 24px rgba(139,90,60,.18), inset 0 1px 0 rgba(255,255,255,.55) !important;
  font-family: 'Nunito', sans-serif !important;
  font-weight: 800 !important;
  text-align: left !important;
  justify-content: center !important;
  min-height: 72px !important;
  height: auto !important;
  overflow: visible !important;
  white-space: normal !important;
  line-height: 1.25 !important;
}
#cq-seg-middle::before {
  content: "" !important;
  position: absolute !important;
  right: -18px !important;
  top: -22px !important;
  width: 70px !important;
  height: 70px !important;
  border-radius: 60% 40% 55% 45% !important;
  background: rgba(255,255,255,.28) !important;
  pointer-events: none !important;
}
#cq-seg-middle:hover,
#cq-seg-middle:focus-visible {
  background: linear-gradient(145deg, #e8c4a8, #dcb08e) !important;
  color: #3a2a22 !important;
  border: none !important;
}
#cq-seg-teens {
  border-radius: 0 !important;
  background: #ffe600 !important;
  color: #0a0a0a !important;
  border: 3px solid #0a0a0a !important;
  box-shadow: 5px 5px 0 #0a0a0a !important;
  font-family: 'Space Mono', monospace !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: -0.03em;
  transform: rotate(-0.4deg);
  min-height: 72px !important;
  height: auto !important;
  overflow: visible !important;
  white-space: normal !important;
  line-height: 1.2 !important;
}
#cq-seg-teens:hover,
#cq-seg-teens:focus-visible {
  background: #ff2d95 !important;
  color: #fff !important;
  border-color: #0a0a0a !important;
  transform: rotate(0deg) translateY(-2px) !important;
}
#cq-seg-early_adult {
  border-radius: 18px !important;
  background: linear-gradient(135deg, rgba(14,165,233,.35), rgba(255,255,255,.55)) !important;
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  color: #0f172a !important;
  border: 2px solid rgba(15,23,42,.35) !important;
  box-shadow: 0 8px 32px rgba(40,70,120,.10), inset 0 1px 0 rgba(255,255,255,.7) !important;
  font-family: 'Inter', system-ui, sans-serif !important;
  font-weight: 650 !important;
  text-align: left !important;
  justify-content: center !important;
  min-height: 72px !important;
  height: auto !important;
  overflow: visible !important;
  white-space: normal !important;
  line-height: 1.25 !important;
  letter-spacing: -0.02em;
}
#cq-seg-early_adult:hover,
#cq-seg-early_adult:focus-visible {
  background: linear-gradient(135deg, rgba(125,211,252,.4), rgba(255,255,255,.5)) !important;
  border-color: rgba(3,105,161,.35) !important;
  color: #0369a1 !important;
}
#cq-seg-adult {
  border-radius: 0 !important;
  background: #fff !important;
  color: #111 !important;
  border: 2px solid #111 !important;
  border-left: 4px solid #e11d48 !important;
  box-shadow: none !important;
  font-family: 'Inter', Helvetica, Arial, sans-serif !important;
  font-weight: 600 !important;
  min-height: 72px !important;
  height: auto !important;
  overflow: visible !important;
  white-space: normal !important;
  line-height: 1.25 !important;
  letter-spacing: -0.03em;
  padding: 14px 12px !important;
}
#cq-seg-adult:hover,
#cq-seg-adult:focus-visible {
  background: #111 !important;
  color: #fff !important;
  border-color: #111 !important;
  border-left-color: #e11d48 !important;
}
#cq-seg-unhurried {
  grid-column: 1 / -1 !important;
  border-radius: 22px !important;
  background: #e8ebe3 !important;
  color: #1f2c24 !important;
  border: 2px solid rgba(31,44,36,.22) !important;
  box-shadow: 8px 8px 18px #c5cbc0, -8px -8px 18px #ffffff !important;
  font-family: Literata, Georgia, serif !important;
  font-weight: 600 !important;
  font-size: 1.12rem !important;
  min-height: 76px !important;
  height: auto !important;
  overflow: visible !important;
  white-space: normal !important;
  line-height: 1.3 !important;
  margin-top: 2px !important;
}
#cq-seg-unhurried:hover,
#cq-seg-unhurried:focus-visible {
  background: #e8ebe3 !important;
  color: #1f2c24 !important;
  box-shadow: inset 5px 5px 12px #c5cbc0, inset -5px -5px 12px #ffffff !important;
  border: none !important;
}
@media (max-width: 560px) {
  #cq-land { grid-template-columns: 1fr !important; gap: 10px !important; }
  #cq-seg-unhurried { grid-column: 1 !important; }
  #cq-seg-teens { transform: none; }
}

/* ============================================================
   Shared chrome: hero, cards, controls
   ============================================================ */
#cq-hero {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 12px;
}
#cq-brand-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
#cq-brand h1 {
  font-family: var(--cq-display) !important;
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
  font-size: calc(1.02rem * var(--cq-font-scale));
  line-height: 1.45;
  max-width: 40ch;
  font-weight: 500;
}
#cq-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  border-radius: var(--cq-chip-radius);
  background: var(--cq-indigo-soft);
  color: var(--cq-indigo) !important;
  font-size: calc(0.8rem * var(--cq-font-scale));
  font-weight: 700;
  white-space: nowrap;
  border: 1px solid color-mix(in srgb, var(--cq-indigo) 18%, transparent);
  letter-spacing: 0.01em;
}
#cq-disclosure {
  margin: 2px 0 10px;
  padding: 10px 14px;
  border-radius: calc(var(--cq-card-radius) - 8px);
  background: color-mix(in srgb, var(--cq-card) 78%, transparent);
  border: 1px solid var(--cq-line);
  color: var(--cq-muted) !important;
  font-size: calc(0.9rem * var(--cq-font-scale));
  font-weight: 500;
  line-height: 1.45;
}
.cq-card {
  background: var(--cq-card) !important;
  border: 1px solid var(--cq-line) !important;
  border-radius: var(--cq-card-radius) !important;
  padding: var(--cq-density) !important;
  box-shadow: var(--cq-card-shadow) !important;
}
label, .label-wrap span, span.svelte-1gfkn6j {
  color: var(--cq-muted) !important;
  font-weight: 700 !important;
  font-size: var(--cq-label-size) !important;
  letter-spacing: 0.01em;
  text-transform: none !important;
}
input, textarea, select, .wrap-inner, .secondary-wrap, .scroll-hide {
  background: color-mix(in srgb, var(--cq-card) 90%, var(--cq-bg)) !important;
  border: 1px solid var(--cq-line) !important;
  border-radius: calc(var(--cq-card-radius) - 8px) !important;
  color: var(--cq-ink) !important;
  min-height: var(--cq-tap) !important;
  font-size: calc(1rem * var(--cq-font-scale)) !important;
}
input:focus-visible, textarea:focus-visible, select:focus-visible {
  outline: none !important;
  box-shadow: var(--cq-focus) !important;
  border-color: var(--cq-indigo) !important;
}

/* Age radios as chips, kill default radio dots */
#cq-age { margin-bottom: 6px !important; }
#cq-age .wrap {
  display: flex !important;
  flex-wrap: wrap !important;
  gap: 8px !important;
}
#cq-age input[type="radio"] {
  position: absolute !important;
  opacity: 0 !important;
  pointer-events: none !important;
  width: 1px !important;
  height: 1px !important;
}
#cq-age label {
  background: color-mix(in srgb, var(--cq-card) 88%, var(--cq-bg)) !important;
  border: 1.5px solid var(--cq-line) !important;
  border-radius: var(--cq-btn-radius) !important;
  padding: 11px 16px !important;
  margin: 0 !important;
  color: var(--cq-ink) !important;
  font-weight: 700 !important;
  font-size: calc(0.95rem * var(--cq-font-scale)) !important;
  cursor: pointer !important;
  min-height: 44px !important;
  display: inline-flex !important;
  align-items: center !important;
  transition: background .15s var(--cq-ease), border-color .15s var(--cq-ease), color .15s var(--cq-ease) !important;
}
#cq-age label:has(input:checked),
#cq-age input:checked + span,
#cq-age label:has(input:checked) span {
  background: var(--cq-indigo) !important;
  border-color: var(--cq-indigo) !important;
  color: #fff !important;
}
#cq-age label:focus-within {
  box-shadow: var(--cq-focus) !important;
}

button {
  border-radius: var(--cq-btn-radius) !important;
  font-weight: 700 !important;
  letter-spacing: 0.01em;
  transition: transform .14s var(--cq-ease), box-shadow .14s var(--cq-ease), filter .14s var(--cq-ease), background .14s var(--cq-ease) !important;
  min-height: var(--cq-tap) !important;
  font-size: calc(1.02rem * var(--cq-font-scale)) !important;
  font-family: var(--cq-font) !important;
}
button:hover { transform: translateY(-1px); }
button:focus-visible {
  outline: none !important;
  box-shadow: var(--cq-focus) !important;
}
button.primary, #cq-start, #cq-start button {
  background: linear-gradient(135deg, var(--cq-indigo) 0%, color-mix(in srgb, var(--cq-indigo) 72%, var(--cq-teal)) 55%, var(--cq-teal) 140%) !important;
  color: #fff !important;
  border: 2px solid color-mix(in srgb, var(--cq-indigo) 55%, #000) !important;
  box-shadow: 0 12px 28px color-mix(in srgb, var(--cq-indigo) 26%, transparent) !important;
  width: 100% !important;
  overflow: visible !important;
  white-space: normal !important;
  height: auto !important;
  min-height: var(--cq-tap) !important;
  padding: 12px 20px !important;
  line-height: 1.25 !important;
  flex-shrink: 0 !important;
  text-overflow: clip !important;
}
button.primary span, #cq-start span {
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: clip !important;
  line-height: 1.25 !important;
}
button.secondary {
  background: transparent !important;
  color: var(--cq-muted) !important;
  border: 1px solid var(--cq-line) !important;
  box-shadow: none !important;
  font-weight: 600 !important;
  min-width: 88px !important;
}
button.secondary:hover {
  background: var(--cq-indigo-soft) !important;
  color: var(--cq-indigo) !important;
  border-color: color-mix(in srgb, var(--cq-indigo) 22%, transparent) !important;
}

/* Think: chat bubbles + thin chrome */
#cq-chatbot .label-wrap,
#cq-chatbot > label,
#cq-chatbot .icon-button,
#cq-chatbot button[aria-label="Clear"],
#cq-chatbot button[aria-label="Copy"] { display: none !important; }
#cq-chatbot, #cq-chatbot .bubble-wrap, #cq-chatbot .wrapper, #cq-chatbot > .wrap {
  background: color-mix(in srgb, var(--cq-card) 72%, var(--cq-bg)) !important;
  border: 1px solid var(--cq-line) !important;
  border-radius: calc(var(--cq-card-radius) - 4px) !important;
  min-height: 320px !important;
  box-shadow: none !important;
}
#cq-chatbot .message, #cq-chatbot .bot, #cq-chatbot .user,
#cq-chatbot .bubble, #cq-chatbot [data-testid="bot"], #cq-chatbot [data-testid="user"] {
  border-radius: calc(var(--cq-card-radius) - 8px) !important;
  font-size: calc(1.04rem * var(--cq-font-scale)) !important;
  line-height: 1.55 !important;
  font-weight: 500 !important;
}
#cq-chatbot .bot, #cq-chatbot .assistant, #cq-chatbot [data-testid="bot"],
#cq-chatbot .message.bot, #cq-chatbot .bubble.bot {
  background: var(--cq-card) !important;
  color: var(--cq-ink) !important;
  border: 1px solid var(--cq-line) !important;
  box-shadow: 0 1px 0 rgba(28, 36, 52, 0.03) !important;
}
#cq-chatbot .user, #cq-chatbot [data-testid="user"],
#cq-chatbot .message.user, #cq-chatbot .bubble.user {
  background: var(--cq-indigo) !important;
  color: #fff !important;
  border: none !important;
}

#cq-empty {
  text-align: center;
  padding: 22px 16px 6px;
  color: var(--cq-muted);
  overflow: visible;
  max-width: 100%;
}
#cq-empty .cq-empty-mark {
  width: 36px; height: 3px; border-radius: 999px;
  background: color-mix(in srgb, var(--cq-indigo) 35%, transparent);
  margin: 0 auto 14px;
}
#cq-empty strong {
  display: block;
  font-family: var(--cq-display);
  font-size: calc(1.18rem * var(--cq-font-scale));
  color: var(--cq-ink);
  margin-bottom: 6px;
  font-weight: 700;
}
#cq-empty .cq-empty-body {
  display: block;
  font-size: calc(0.95rem * var(--cq-font-scale));
  line-height: 1.45;
}

/* Thin session chip */
#cq-session-chip {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 10px;
  padding: 6px 12px;
  margin: 0 0 8px;
  border-radius: var(--cq-chip-radius);
  background: color-mix(in srgb, var(--cq-card) 80%, transparent);
  border: 1px solid var(--cq-line);
  color: var(--cq-ink) !important;
  font-size: var(--cq-chip-size);
  font-weight: 600;
  line-height: 1.3;
  max-width: 100%;
}
#cq-session-chip::before {
  content: "";
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--cq-teal);
  flex: 0 0 auto;
}
#cq-session-chip .cq-chip-meta {
  color: var(--cq-muted) !important;
  font-weight: 500;
  font-size: calc(var(--cq-chip-size) * 0.94);
}

/* Quiet elegant phase pill */
#cq-phase-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 11px;
  margin: 0 0 10px;
  border-radius: var(--cq-chip-radius);
  background: transparent;
  border: 1px solid color-mix(in srgb, var(--cq-teal) 22%, transparent);
  color: var(--cq-teal) !important;
  font-size: calc(0.78rem * var(--cq-font-scale));
  font-weight: 600;
  letter-spacing: 0.01em;
}
#cq-phase-pill > span:first-child {
  color: var(--cq-muted) !important;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: 0.72em;
}

#cq-wrap-card { text-align: center; padding: 28px 18px !important; }
#cq-wrap-card .cq-pride {
  font-family: var(--cq-display);
  font-size: calc(1.3rem * var(--cq-font-scale));
  font-weight: 700;
  color: var(--cq-ink);
  margin: 0 0 18px;
  line-height: 1.35;
}
#cq-wrap-card button.primary { width: auto !important; min-width: 160px !important; }
#cq-wrap-card button.secondary { min-width: 140px !important; }

/* Quiet skills / grown-up until asked */
.accordion {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  margin-top: 6px !important;
  padding: 0 !important;
}
.accordion > .label-wrap,
.accordion > button,
.accordion .label-wrap {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: var(--cq-muted) !important;
  font-size: calc(0.82rem * var(--cq-font-scale)) !important;
  font-weight: 600 !important;
  min-height: 36px !important;
  padding: 4px 2px !important;
  text-decoration: underline;
  text-underline-offset: 3px;
}
.accordion, .accordion *, .accordion .prose, .accordion .prose *,
.accordion p, .accordion li, .accordion span, .accordion strong, .accordion em,
.markdown, .markdown *, .prose, .prose p, .prose li, .prose strong, .prose em, .prose a {
  color: var(--cq-ink) !important;
}
.accordion .prose em, .prose em { color: var(--cq-muted) !important; }

#cq-composer {
  display: flex !important;
  gap: 10px !important;
  align-items: stretch !important;
  margin-top: 8px !important;
  overflow: visible !important;
}
#cq-composer .form, #cq-composer .block { flex: 1 1 auto !important; min-width: 0 !important; }
#cq-composer button.primary {
  width: auto !important;
  min-width: 104px !important;
  padding: 10px 18px !important;
  box-shadow: 0 8px 18px color-mix(in srgb, var(--cq-indigo) 22%, transparent) !important;
  overflow: visible !important;
  white-space: nowrap !important;
  height: auto !important;
  min-height: var(--cq-tap) !important;
  flex: 0 0 auto !important;
  align-self: stretch !important;
  text-overflow: clip !important;
}
#cq-composer button.primary span {
  white-space: nowrap !important;
  overflow: visible !important;
}

#cq-change-seg button,
button#cq-change-seg {
  background: transparent !important;
  color: var(--cq-muted) !important;
  border: none !important;
  box-shadow: none !important;
  min-height: 40px !important;
  font-size: calc(0.86rem * var(--cq-font-scale)) !important;
  font-weight: 600 !important;
  text-decoration: underline;
  text-underline-offset: 3px;
  width: auto !important;
  padding: 4px 2px !important;
  transform: none !important;
}

@media (max-width: 720px) {
  .gradio-container { padding: 10px 8px 32px !important; }
  #cq-shell { padding: calc(var(--cq-pad) - 4px) 12px 16px; border-radius: calc(var(--cq-radius) - 4px); }
  #cq-chatbot { min-height: 280px !important; }
  button.primary { min-height: max(52px, var(--cq-tap)) !important; }
}
@media (min-width: 860px) {
  .gradio-container { padding: 28px 18px 56px !important; }
  #cq-shell { padding: var(--cq-pad); }
}

/* Reduce gray Gradio dropdown / select chrome */
.wrap-inner:has(select), .secondary-wrap, .scroll-hide {
  background: color-mix(in srgb, var(--cq-card) 90%, var(--cq-bg)) !important;
}
"""



PHASE_LABELS = {
    "clarify": "Getting clear",
    "clarifying": "Getting clear",
    "assumptions": "What we assume",
    "assumption": "What we assume",
    "evidence": "Checking evidence",
    "alternatives": "Other views",
    "alternative": "Other views",
    "implications": "What follows",
    "implication": "What follows",
    "reflect": "Looking back",
    "reflection": "Looking back",
}

SKILL_LABELS = {
    "curiosity": "Curiosity",
    "evidence": "Evidence",
    "perspective": "Other views",
    "reflection": "Reflection",
}


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
        f"- {icons.get(k, '⭐')} **{SKILL_LABELS.get(k, k.title())}** · {v}"
        for k, v in skills.items()
    ]
    return "\n".join(lines)


def _phase_label(phase: str) -> str:
    return PHASE_LABELS.get((phase or "").strip().lower(), phase or "Getting clear")


def _fmt_phase_pill(phase: str) -> str:
    label = _phase_label(phase)
    return (
        f'<div id="cq-phase-pill"><span>Where we are</span>'
        f"<span>·</span><span>{label}</span></div>"
    )


def _fmt_chip(segment_short: str, topic_use: str) -> str:
    return (
        f'<div id="cq-session-chip">'
        f"<span>{segment_short} · {topic_use}</span>"
        f'<span class="cq-chip-meta"> · {CHIP_DISCLOSURE}</span>'
        f"</div>"
    )


def _empty_html(body: str) -> str:
    return (
        '<div id="cq-empty">'
        '<div class="cq-empty-mark" aria-hidden="true"></div>'
        "<strong>Ready when you are</strong>"
        f'<span class="cq-empty-body">{body}</span>'
        "</div>"
    )


def _hero_html(hero: str, pill: str) -> str:
    return (
        '<div id="cq-hero">'
        '<div id="cq-brand-row">'
        '<div id="cq-brand">'
        "<h1>CritiQuest</h1>"
        f"<p>{hero}</p>"
        "</div>"
        f'<div id="cq-pill">{pill}</div>'
        "</div>"
        "</div>"
    )


def _is_wrap_phase(phase: str) -> bool:
    return (phase or "").strip().lower() in ("reflect", "reflection")


def _own_topic(topic: str) -> bool:
    return (topic or "").startswith("I have my own")


def _engine_age(segment: str, age_radio: str) -> str:
    meta = SEGMENTS.get(segment) or SEGMENTS["middle"]
    if meta["engine_age"]:
        return meta["engine_age"]
    return age_radio or meta["age_default"]


def choose_segment(segment_id: str):
    """LAND -> Start: theme + copy reshape, reveal setup only."""
    meta = SEGMENTS[segment_id]
    titles = topics_for_segment(segment_id) + ["I have my own question"]
    return (
        segment_id,
        gr.update(elem_classes=[f"seg-{segment_id}"]),
        gr.update(value=_hero_html(meta["hero"], meta["pill"]), visible=True),
        gr.update(value=f'<div id="cq-disclosure">{DISCLOSURE}</div>', visible=True),
        gr.update(visible=False),  # land_col
        gr.update(visible=True),  # setup_col
        gr.update(
            choices=meta["age_choices"],
            value=meta["age_default"],
            visible=meta["show_age"],
        ),
        gr.update(value=meta["cta"]),
        gr.update(value=_empty_html(meta["empty"]), visible=True),
        gr.update(visible=True),  # change_seg
        gr.update(choices=titles, value=titles[0]),  # topic list for segment
    )


def back_to_land():
    """Reset to LAND only: Who is this for? + helper + 5 chips."""
    return (
        "",
        gr.update(elem_classes=[]),
        gr.update(value=_hero_html(LAND_HERO, LAND_PILL), visible=False),
        gr.update(value=f'<div id="cq-disclosure">{DISCLOSURE}</div>', visible=False),
        gr.update(visible=True),  # land_col
        gr.update(visible=False),  # setup_col
        gr.update(visible=False),  # age (hidden on land)
        gr.update(value="Let's begin"),
        gr.update(visible=False),  # empty hidden on pure land
        gr.update(visible=False),  # change_seg
        [],
        {},
        _fmt_skills({}),
        "",
        gr.update(value="", visible=False),
        gr.update(value=_fmt_phase_pill("clarify"), visible=False),
        gr.update(value="", visible=False),
        gr.update(visible=False),  # think_col
        gr.update(visible=False),  # skills_acc
        gr.update(visible=False),  # wrap_panel
        gr.update(visible=False),  # grownup_acc
        gr.update(visible=False),  # composer_row
    )


def start_session(segment: str, age: str, topic: str, custom: str):
    meta = SEGMENTS.get(segment) or SEGMENTS["middle"]
    engine_age = _engine_age(segment, age)

    if _own_topic(topic) and custom.strip():
        topic_use = custom.strip()
    elif _own_topic(topic):
        topic_use = CLARIFY_TOPIC
    else:
        topic_use = topic

    st = SessionState(age_band=engine_age, segment=segment or "middle", topic=topic_use)
    opener = opening_message(engine_age, topic_use, segment=segment or "middle")
    st.history = [{"role": "assistant", "content": opener}]
    chat = [{"role": "assistant", "content": opener}]
    return (
        chat,
        st.to_dict(),
        _fmt_skills(st.skills),
        teacher_summary(st),
        gr.update(value=_fmt_chip(meta["short"], topic_use), visible=True),
        gr.update(value=_fmt_phase_pill(st.phase), visible=True),
        gr.update(value="", visible=False),
        gr.update(visible=False),  # setup_col
        gr.update(visible=False),  # empty
        gr.update(visible=False),  # hero_disclosure
        gr.update(visible=True),  # think_col
        gr.update(visible=True),  # skills_acc (quiet accordion until opened)
        gr.update(visible=False),  # wrap_panel
        gr.update(visible=True),  # grownup_acc (quiet accordion until opened)
        gr.update(visible=True),  # composer_row
        gr.update(visible=False),  # change_seg
        gr.update(visible=False),  # land_col
        gr.update(visible=False),  # hero (chat is the stage)
    )


def chat_turn(
    message: str,
    history: list,
    state: dict,
    segment: str,
    age: str,
    topic_label: str,
    custom: str,
):
    if not message or not message.strip():
        return (
            history,
            state,
            gr.update(),
            gr.update(),
            "",
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
        )

    st = SessionState.from_dict(state)
    st.segment = segment or st.segment or "middle"
    st.age_band = _engine_age(segment, age) or st.age_band
    if topic_label and not _own_topic(topic_label):
        st.topic = topic_label
    elif custom.strip():
        st.topic = custom.strip()

    reply, st = respond(message.strip(), st, segment=st.segment)
    history = list(history or [])
    history.append({"role": "user", "content": message.strip()})
    history.append({"role": "assistant", "content": reply})

    wrap = _is_wrap_phase(st.phase)
    return (
        history,
        st.to_dict(),
        _fmt_skills(st.skills),
        teacher_summary(st),
        "",
        gr.update(value=_fmt_phase_pill(st.phase), visible=not wrap),
        gr.update(visible=wrap),  # wrap_panel: pride + two exits only
        gr.update(visible=not wrap),  # session_chip
        gr.update(visible=not wrap),  # think_col
        gr.update(visible=not wrap),  # composer_row
        gr.update(visible=not wrap),  # skills_acc
        gr.update(visible=not wrap),  # grownup_acc
    )


def reset_to_start(segment: str):
    """Another topic: back to Start for current segment."""
    meta = SEGMENTS.get(segment) or SEGMENTS["middle"]
    return (
        [],
        {},
        _fmt_skills({}),
        "",
        gr.update(value="", visible=False),
        gr.update(value=_fmt_phase_pill("clarify"), visible=False),
        gr.update(value="", visible=False),
        gr.update(visible=True),  # setup_col
        gr.update(value=_empty_html(RETURN_EMPTY), visible=True),
        gr.update(visible=True),  # hero_disclosure
        gr.update(visible=False),  # think_col
        gr.update(visible=False),  # skills_acc
        gr.update(visible=False),  # wrap_panel
        gr.update(visible=False),  # grownup_acc
        gr.update(visible=False),  # composer_row
        gr.update(visible=True),  # change_seg
        gr.update(visible=False),  # land_col
        gr.update(value=_hero_html(meta["hero"], meta["pill"]), visible=True),
        gr.update(value=meta["cta"]),
    )


def finish_session():
    return (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(value=DONE_MESSAGE, visible=True),
        gr.update(visible=False),
    )


def _toggle_custom(topic: str):
    return gr.update(visible=_own_topic(topic))


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
    with gr.Blocks(
        title="CritiQuest", theme=THEME, css=CUSTOM_CSS, fill_height=False
    ) as demo:
        segment_state = gr.State("")

        with gr.Column(elem_id="cq-shell", elem_classes=[]) as shell:
            # Hidden on Land; Start shows CritiQuest + segment hero/pill
            hero = gr.HTML(_hero_html(LAND_HERO, LAND_PILL), visible=False)

            hero_disclosure = gr.HTML(
                f'<div id="cq-disclosure">{DISCLOSURE}</div>',
                visible=False,
            )

            state = gr.State({})

            # --- LAND: Who is this for? + helper + 5 chips only ---
            with gr.Column(elem_id="cq-land", visible=True) as land_col:
                gr.HTML(
                    '<div id="cq-land-head">'
                    '<p id="cq-land-title">Who is this for?</p>'
                    f'<p id="cq-land-sub">{LAND_HELPER}</p>'
                    "</div>"
                )
                land_btns = []
                for sid in SEGMENT_IDS:
                    btn = gr.Button(
                        SEGMENTS[sid]["label"],
                        elem_id=f"cq-seg-{sid}",
                        elem_classes=["cq-land-chip"],
                        variant="secondary",
                    )
                    land_btns.append((sid, btn))

            change_seg = gr.Button(
                "Change age group",
                elem_id="cq-change-seg",
                visible=False,
            )

            # --- START (hidden until segment chosen) ---
            with gr.Column(elem_classes=["cq-card"], visible=False) as setup_col:
                age = gr.Radio(
                    AGE_CHOICES_ALL,
                    value="11-12",
                    label="How old are you?",
                    elem_id="cq-age",
                    visible=False,
                )
                topic = gr.Dropdown(
                    TOPICS,
                    value=TOPICS[0],
                    label="What should we explore?",
                )
                custom = gr.Textbox(
                    label="Type your question",
                    placeholder="Example: Why do rumors spread so fast?",
                    lines=1,
                    visible=False,
                )
                start_btn = gr.Button(
                    "Let's begin", variant="primary", elem_id="cq-start"
                )
                with gr.Accordion("More topics to try", open=False):
                    gr.Markdown(
                        "\n".join(
                            f"- **{t['title']}** - _{t['domain']}_"
                            for t in TOPIC_SEEDS
                        )
                    )

            empty = gr.HTML("", visible=False)

            # --- THINK (hidden) ---
            session_chip = gr.HTML("", visible=False)
            phase_pill = gr.HTML(_fmt_phase_pill("clarify"), visible=False)

            with gr.Column(elem_classes=["cq-card"], visible=False) as think_col:
                chatbot = gr.Chatbot(
                    label="Chat",
                    height=420,
                    type="messages",
                    elem_id="cq-chatbot",
                    show_label=False,
                    show_copy_button=False,
                    render_markdown=True,
                    allow_tags=False,
                )
                with gr.Row(elem_id="cq-composer", visible=True) as composer_row:
                    msg = gr.Textbox(
                        label="Your idea",
                        placeholder="Type what you're thinking…",
                        scale=5,
                        container=True,
                        show_label=True,
                    )
                    send = gr.Button("Send", variant="primary", scale=1)

            with gr.Accordion(
                "Skills you're building", open=False, visible=False
            ) as skills_acc:
                skills_md = gr.Markdown(_fmt_skills({}))

            # --- WRAP (hidden) ---
            with gr.Column(
                elem_classes=["cq-card"], elem_id="cq-wrap-card", visible=False
            ) as wrap_panel:
                gr.HTML(f'<p class="cq-pride">{PRIDE_LINE}</p>')
                with gr.Row():
                    another_btn = gr.Button("Another topic", variant="primary")
                    done_btn = gr.Button("Done for now", variant="secondary")

            done_box = gr.Markdown("", visible=False)

            with gr.Accordion(
                "Grown-up view", open=False, visible=False
            ) as grownup_acc:
                gr.Markdown(
                    "*Demo oversight for teachers or parents. Not live school data.*"
                )
                teacher_md = gr.Markdown("")

            start_outputs = [
                chatbot,
                state,
                skills_md,
                teacher_md,
                session_chip,
                phase_pill,
                done_box,
                setup_col,
                empty,
                hero_disclosure,
                think_col,
                skills_acc,
                wrap_panel,
                grownup_acc,
                composer_row,
                change_seg,
                land_col,
                hero,
            ]

            land_outputs = [
                segment_state,
                shell,
                hero,
                hero_disclosure,
                land_col,
                setup_col,
                age,
                start_btn,
                empty,
                change_seg,
                topic,
            ]

            for sid, btn in land_btns:
                btn.click(
                    lambda s=sid: choose_segment(s),
                    inputs=[],
                    outputs=land_outputs,
                )

            change_seg.click(
                back_to_land,
                inputs=[],
                outputs=[
                    segment_state,
                    shell,
                    hero,
                    hero_disclosure,
                    land_col,
                    setup_col,
                    age,
                    start_btn,
                    empty,
                    change_seg,
                    chatbot,
                    state,
                    skills_md,
                    teacher_md,
                    session_chip,
                    phase_pill,
                    done_box,
                    think_col,
                    skills_acc,
                    wrap_panel,
                    grownup_acc,
                    composer_row,
                ],
            )

            topic.change(_toggle_custom, inputs=[topic], outputs=[custom])

            start_btn.click(
                start_session,
                inputs=[segment_state, age, topic, custom],
                outputs=start_outputs,
            )
            think_turn_outputs = [
                chatbot,
                state,
                skills_md,
                teacher_md,
                msg,
                phase_pill,
                wrap_panel,
                session_chip,
                think_col,
                composer_row,
                skills_acc,
                grownup_acc,
            ]
            send.click(
                chat_turn,
                inputs=[msg, chatbot, state, segment_state, age, topic, custom],
                outputs=think_turn_outputs,
            )
            msg.submit(
                chat_turn,
                inputs=[msg, chatbot, state, segment_state, age, topic, custom],
                outputs=think_turn_outputs,
            )
            another_btn.click(
                reset_to_start,
                inputs=[segment_state],
                outputs=start_outputs + [start_btn],
            )
            done_btn.click(
                finish_session,
                inputs=[],
                outputs=[composer_row, wrap_panel, done_box, phase_pill],
            )

        return demo


demo = build_demo()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    demo.launch(server_name="0.0.0.0", server_port=port)
