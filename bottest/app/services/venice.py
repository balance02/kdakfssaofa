import asyncio
import logging

import httpx

from app.config import get_settings

log = logging.getLogger(__name__)
BASE = "https://api.venice.ai/api/v1"


class VeniceError(Exception):
    def __init__(self, status: int, body: str = ""):
        self.status = status
        self.body = body
        super().__init__(f"venice {status}")


def _headers() -> dict:
    return {"Authorization": f"Bearer {get_settings().venice_api_key}", "Content-Type": "application/json"}


async def list_models() -> list[dict]:
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(f"{BASE}/models", headers=_headers())
        r.raise_for_status()
        return r.json().get("data", [])


async def chat(messages: list[dict], model: str, max_tokens: int, temperature: float) -> dict:
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens,
               "temperature": temperature, "top_p": 0.95, "stream": False}
    last: VeniceError | None = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=90) as c:
                r = await c.post(f"{BASE}/chat/completions", json=payload, headers=_headers())
            if r.status_code in (429, 500, 502, 503, 504):
                last = VeniceError(r.status_code, r.text[:300])
                await asyncio.sleep(1.5 * (attempt + 1))
                continue
            if r.status_code != 200:
                raise VeniceError(r.status_code, r.text[:300])
            data = r.json()
            return {
                "text": data["choices"][0]["message"]["content"],
                "tokens_in": data.get("usage", {}).get("prompt_tokens", 0),
                "tokens_out": data.get("usage", {}).get("completion_tokens", 0),
            }
        except httpx.RequestError as exc:
            last = VeniceError(0, str(exc))
            await asyncio.sleep(1.5 * (attempt + 1))
    raise last or VeniceError(0, "unknown")