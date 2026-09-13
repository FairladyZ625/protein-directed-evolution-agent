"""LLM access for the agent's injectable ports, backed by an OpenAI-compatible pool.

Credentials come from a local ``.env`` file (see ``.env.example``) — never hard
coded and never committed. When no key is configured or the pool errors, callers
fall back to the deterministic path, so the project stays runnable without any
network access or secret.

Env keys (``.env``):
  API_KEY     pool token (also accepts LLM_API_KEY)
  BASE_URL    pool base URL, ``/v1`` appended if missing (default token.qianbaner.top)
  LLM_MODEL   model id, e.g. gpt-5.6-terra / gpt-5.6-sol (default gpt-5.6-terra)
  LLM_TIMEOUT per-request seconds (default 90)
"""
from __future__ import annotations

import os
from pathlib import Path

_DOTENV_LOADED = False


def load_dotenv() -> None:
    """Populate os.environ from the nearest ``.env`` (real env vars win). Idempotent."""
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    _DOTENV_LOADED = True
    seen: set[Path] = set()
    for base in [Path.cwd(), *Path(__file__).resolve().parents]:
        p = base / ".env"
        if p in seen or not p.exists():
            continue
        seen.add(p)
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def llm_config() -> dict | None:
    """Resolved pool config, or None when no credentials are available."""
    load_dotenv()
    key = os.environ.get("API_KEY") or os.environ.get("LLM_API_KEY")
    if not key:
        return None
    base = (os.environ.get("BASE_URL") or os.environ.get("LLM_BASE_URL")
            or "https://token.qianbaner.top").rstrip("/")
    if not base.endswith("/v1"):
        base += "/v1"
    return {"api_key": key, "base_url": base,
            "model": os.environ.get("LLM_MODEL", "gpt-5.6-terra"),
            "timeout": float(os.environ.get("LLM_TIMEOUT", "90"))}


def llm_available() -> bool:
    return llm_config() is not None


def chat_json(prompt: str, *, cfg: dict | None = None) -> str:
    """One-shot deterministic (temperature 0) chat completion; returns raw text.

    Raises on any failure so callers can fall back to a deterministic path.
    """
    cfg = cfg or llm_config()
    if cfg is None:
        raise RuntimeError("no LLM credentials (set API_KEY in .env)")
    from openai import OpenAI
    client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"],
                    timeout=cfg["timeout"], max_retries=0)
    resp = client.chat.completions.create(
        model=cfg["model"],
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0, max_tokens=512)
    return resp.choices[0].message.content or ""
