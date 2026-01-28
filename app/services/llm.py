import asyncio
import logging
import os
import random
from typing import Optional

from groq import AsyncGroq

DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
REQUEST_TIMEOUT_SECONDS = 25
MAX_RETRIES = 2
RETRY_BACKOFF_BASE = 1.5

_client: Optional[AsyncGroq] = None


def _get_client() -> AsyncGroq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set")
        _client = AsyncGroq(api_key=api_key)
    return _client


async def _request_chat(
    *,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_completion_tokens: int,
):
    return await _get_client().chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_completion_tokens=max_completion_tokens,
    )


async def _request_with_retries(
    *,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_completion_tokens: int,
):
    for attempt in range(MAX_RETRIES + 1):
        try:
            return await asyncio.wait_for(
                _request_chat(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_completion_tokens=max_completion_tokens,
                ),
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except Exception:
            logging.exception("Groq API error (attempt %s)", attempt + 1)
            if attempt >= MAX_RETRIES:
                raise
            backoff = RETRY_BACKOFF_BASE ** attempt + random.random()
            await asyncio.sleep(backoff)


async def generate_text(
    *,
    prompt: str,
    system_prompt: str,
    temperature: float,
    max_completion_tokens: int,
    fallback: Optional[str],
) -> Optional[str]:
    model = DEFAULT_GROQ_MODEL
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    try:
        response = await _request_with_retries(
            model=model,
            messages=messages,
            temperature=temperature,
            max_completion_tokens=max_completion_tokens,
        )
    except Exception:
        logging.exception("Groq API failed after retries")
        return fallback

    content = response.choices[0].message.content
    if not content:
        return fallback
    return content.strip()


async def generate_response(
    *,
    prompt: str,
    system_prompt: str,
    temperature: float = 0.6,
    max_completion_tokens: int = 512,
) -> str:
    text = await generate_text(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_completion_tokens=max_completion_tokens,
        fallback="Извините, произошла техническая ошибка. Попробуйте позже.",
    )
    return text or "Я рядом. Можете рассказать подробнее?"


async def generate_summary(
    *,
    prompt: str,
    system_prompt: str,
    max_completion_tokens: int = 256,
) -> Optional[str]:
    return await generate_text(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.3,
        max_completion_tokens=max_completion_tokens,
        fallback=None,
    )
