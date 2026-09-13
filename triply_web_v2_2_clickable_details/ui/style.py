from __future__ import annotations

import streamlit as st


GLOBAL_CSS = """
<style>
:root {
    --triply-bg: #f7f9fc;
    --triply-card: #ffffff;
    --triply-text: #122033;
    --triply-muted: #667085;
    --triply-border: #e5eaf1;
    --triply-primary: #5b5cf0;
    --triply-primary-dark: #4849ce;
    --triply-accent: #14b8a6;
    --triply-warm: #ff8a5b;
}

html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
                 "Segoe UI", sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 5% 0%, rgba(91,92,240,.08), transparent 30%),
        radial-gradient(circle at 95% 10%, rgba(20,184,166,.07), transparent 28%),
        var(--triply-bg);
    color: var(--triply-text);
}

.block-container {
    max-width: 1240px;
    padding-top: 2.2rem;
    padding-bottom: 5rem;
}

[data-testid="stHeader"] {
    background: rgba(247,249,252,.88);
    backdrop-filter: blur(14px);
    border-bottom: 1px solid rgba(229,234,241,.9);
}

[data-testid="stSidebar"] {
    display: none;
}

.hero {
    padding: 3.8rem 3.2rem;
    border-radius: 28px;
    background:
        radial-gradient(circle at 92% 15%, rgba(255,255,255,.28), transparent 24%),
        linear-gradient(135deg, #4f46e5 0%, #6d5dfc 48%, #0ea5a8 100%);
    color: white;
    box-shadow: 0 20px 60px rgba(79,70,229,.18);
    margin-bottom: 1.5rem;
}

.hero h1 {
    font-size: clamp(2.3rem, 5vw, 4.7rem);
    line-height: 1.02;
    margin: 0 0 1rem 0;
    letter-spacing: -0.045em;
}

.hero p {
    font-size: 1.08rem;
    max-width: 700px;
    color: rgba(255,255,255,.88);
    margin: 0;
}

.eyebrow {
    display: inline-flex;
    padding: .38rem .7rem;
    margin-bottom: 1rem;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,.28);
    background: rgba(255,255,255,.12);
    font-size: .82rem;
    font-weight: 700;
    letter-spacing: .02em;
}

.section-title {
    font-size: 1.75rem;
    letter-spacing: -.025em;
    margin: 2.5rem 0 .35rem 0;
}

.section-subtitle {
    color: var(--triply-muted);
    margin-bottom: 1.2rem;
}

.feature-card {
    background: rgba(255,255,255,.86);
    border: 1px solid var(--triply-border);
    border-radius: 20px;
    padding: 1.25rem;
    min-height: 150px;
    box-shadow: 0 10px 28px rgba(18,32,51,.045);
}

.feature-card .icon {
    font-size: 1.7rem;
}

.feature-card h3 {
    margin: .65rem 0 .3rem 0;
    font-size: 1.02rem;
}

.feature-card p {
    color: var(--triply-muted);
    font-size: .92rem;
    margin: 0;
}

.search-shell {
    background: rgba(255,255,255,.94);
    border: 1px solid var(--triply-border);
    border-radius: 24px;
    padding: 1.25rem 1.35rem .7rem 1.35rem;
    box-shadow: 0 16px 45px rgba(18,32,51,.075);
}

.trip-badge {
    display: inline-block;
    padding: .35rem .65rem;
    border-radius: 999px;
    background: #eef2ff;
    color: #4f46e5;
    font-weight: 700;
    font-size: .82rem;
}

.small-muted {
    color: var(--triply-muted);
    font-size: .88rem;
}

.price {
    font-size: 1.65rem;
    font-weight: 800;
    letter-spacing: -.03em;
}

div[data-testid="stMetric"] {
    background: rgba(255,255,255,.86);
    border: 1px solid var(--triply-border);
    padding: .9rem 1rem;
    border-radius: 16px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 20px;
    border-color: var(--triply-border);
    background: rgba(255,255,255,.88);
    box-shadow: 0 8px 24px rgba(18,32,51,.035);
}

.stButton > button,
.stFormSubmitButton > button {
    border-radius: 12px;
    font-weight: 700;
}

.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background: linear-gradient(135deg, #5b5cf0, #6d5dfc);
    border: none;
}

.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #4849ce, #5b5cf0);
}

[data-testid="stLinkButton"] a {
    border-radius: 12px;
}

.footer {
    text-align: center;
    color: var(--triply-muted);
    font-size: .82rem;
    margin-top: 4rem;
    padding-top: 1rem;
    border-top: 1px solid var(--triply-border);
}

@media (max-width: 800px) {
    .block-container {
        padding: 1.2rem .85rem 4rem .85rem;
    }
    .hero {
        padding: 2.4rem 1.4rem;
        border-radius: 22px;
    }
    .hero h1 {
        font-size: 2.45rem;
    }
}
</style>
"""


def apply_global_styles() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
