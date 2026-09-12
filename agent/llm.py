"""LLM access for the agent's injectable ports, backed by an OpenAI-compatible pool.

Credentials come from a local ``.env`` file (see ``.env.example``) — never hard
coded and never committed. Structured-call failures are raised to the caller;
the campaign layer is responsible for recording any explicit offline fallback.

Env keys (``.env``):
  API_KEY     pool token (also accepts LLM_API_KEY)
  BASE_URL    pool base URL, ``/v1`` appended if missing (default token.qianbaner.top)
  LLM_MODEL   model id, e.g. gpt-5.6-terra / gpt-5.6-sol (default gpt-5.6-terra)
  LLM_TIMEOUT per-request seconds (default 90)
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel

_DOTENV_LOADED = False
OutputT = TypeVar("OutputT", bound=BaseModel)


@dataclass(frozen=True)
class StructuredLLMResult(Generic[OutputT]):
    """Validated provider output plus response-side provenance."""

    output: OutputT
    model: str
    requests: int


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


def chat_structured(
    prompt: str,
    output_type: type[OutputT],
    *,
    cfg: dict | None = None,
    temperature: float = 0.0,
    max_tokens: int = 512,
) -> StructuredLLMResult[OutputT]:
    """Run one PydanticAI call whose only valid output is ``output_type``.

    PydanticAI registers the Pydantic model as the provider output-tool schema
    and validates the returned tool arguments. ``retries=0`` makes a malformed
    structured response fail this call immediately; this function never parses
    free-form text and never falls back silently.
    """
    cfg = cfg or llm_config()
    if cfg is None:
        raise RuntimeError("no LLM credentials (set API_KEY in .env)")
    if not isinstance(output_type, type) or not issubclass(output_type, BaseModel):
        raise TypeError("output_type must be a Pydantic BaseModel subclass")

    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=cfg["api_key"],
        base_url=cfg["base_url"],
        timeout=cfg["timeout"],
        max_retries=0,
    )
    provider = OpenAIProvider(openai_client=client)
    model = OpenAIChatModel(cfg["model"], provider=provider)
    agent = Agent(
        model,
        output_type=output_type,
        model_settings={"temperature": temperature, "max_tokens": max_tokens},
        retries=0,
    )
    result = agent.run_sync(prompt)
    if not isinstance(result.output, output_type):
        raise TypeError(f"provider output was not parsed as {output_type.__name__}")
    actual_model = result.response.model_name
    if not actual_model:
        raise RuntimeError("provider response omitted model provenance")
    return StructuredLLMResult(
        output=result.output,
        model=actual_model,
        requests=int(result.usage.requests),
    )
