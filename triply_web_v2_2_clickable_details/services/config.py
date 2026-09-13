from __future__ import annotations

from dataclasses import dataclass
import os
import streamlit as st


@dataclass(frozen=True)
class Settings:
    serpapi_key: str | None


def _secret_or_env(name: str, default: str | None = None) -> str | None:
    try:
        if name in st.secrets:
            value = st.secrets[name]
            return str(value) if value is not None else default
    except Exception:
        pass
    return os.getenv(name, default)


def get_settings() -> Settings:
    return Settings(serpapi_key=_secret_or_env("SERPAPI_KEY"))
