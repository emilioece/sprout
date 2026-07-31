"""
gemini.py

Small helper around the Gemini API that returns validated JSON.
"""

from __future__ import annotations

import json
import os
from typing import Any, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel


# Generic type param for "this returns whatever Pydantic model you ask for".
# Example: generate_json(..., response_model=CareGuideResponse) -> CareGuideResponse
T = TypeVar("T", bound=BaseModel)


def _require_api_key() -> str:
    """Read the Gemini API key from environment (`GEMINI_API_KEY` preferred)."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Gemini is not configured. Set GEMINI_API_KEY in your environment.",
        )
    return api_key


def _extract_json(text: str) -> Any:
    """
    Gemini should return JSON, but this guards against accidental extra text.
    """
    text = (text or "").strip()
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to salvage: grab the first {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])

    raise ValueError("Response was not valid JSON")


def generate_json(
    *,
    prompt: str,
    response_model: type[T],
    model: str | None = None,
    temperature: float = 0.2,
) -> T:
    """
    Call Gemini and parse the response into `response_model`.
    """
    api_key = _require_api_key()
    # You can override the model per-call, or globally via GEMINI_MODEL.
    model_name = model or os.getenv("GEMINI_MODEL") or "gemini-3.5-flash"

    try:
        from google import genai
        from google.genai import types
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Gemini SDK not installed. Install `google-genai`. ({exc})",
        )

    client = genai.Client(api_key=api_key)

    try:
        resp = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                # Force JSON + provide a schema so we can validate with Pydantic.
                response_mime_type="application/json",
                response_schema=response_model.model_json_schema(),
            ),
        )
        # `_extract_json()` is a safety net in case the model returns extra text.
        data = _extract_json(getattr(resp, "text", "") or "")
        return response_model.model_validate(data)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Gemini request failed: {exc}")

