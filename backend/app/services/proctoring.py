"""Live interview proctoring: checks a single candidate video frame for signs of cheating
(looking away from the camera, a phone/tablet/second screen in view, no face, multiple
people) using GPT-4o vision.

Fails open by design: no API key configured, a network/HTTP error, or an unparsable
response all return "no violation" rather than penalising the candidate for an
infrastructure problem. This mirrors the deterministic-fallback pattern used throughout
the AI services (see interview_agent.py) - the difference is there is no meaningful
non-AI baseline for image analysis, so the fallback is simply "don't flag anything".
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

import httpx

from app.config import settings
from app.models import ProctoringEventKind

logger = logging.getLogger(__name__)

NO_VIOLATION: dict[str, Any] = {"violation": False, "kind": None, "detail": ""}

_VALID_KINDS = {kind.value for kind in ProctoringEventKind}


def check_frame(image_bytes: bytes, content_type: str = "image/jpeg") -> dict[str, Any]:
    """Return {"violation": bool, "kind": ProctoringEventKind value or None, "detail": str}."""
    if not settings.openai_api_key:
        logger.info("proctoring: no OpenAI API key configured, skipping frame check")
        return dict(NO_VIOLATION)

    encoded = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:{content_type};base64,{encoded}"

    instructions = (
        "You are an interview proctoring checker. Look at this single webcam frame from a "
        "candidate taking a remote job interview. Decide if it shows evidence of cheating. "
        "Return JSON with keys: violation (bool), kind (one of "
        f"{sorted(_VALID_KINDS)} or null), detail (short plain-English description, or empty "
        "string if no violation). Flag LOOKING_AWAY only for a sustained, clear turn away from "
        "the camera/screen - not a brief glance down or to the side while thinking. Flag "
        "PROHIBITED_OBJECT only for a visible phone, tablet, smartwatch, second screen, or "
        "written notes being read. Do not flag normal fidgeting, blinking, or looking at a "
        "keyboard. When uncertain, prefer violation: false."
    )

    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": instructions},
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    },
                ],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        payload = json.loads(content)
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "proctoring: OpenAI returned status %s: %s", exc.response.status_code, exc.response.text[:300]
        )
        return dict(NO_VIOLATION)
    except httpx.HTTPError as exc:
        logger.warning("proctoring: OpenAI request failed: %s", exc)
        return dict(NO_VIOLATION)
    except (KeyError, json.JSONDecodeError, IndexError, TypeError, ValueError) as exc:
        logger.warning("proctoring: could not parse OpenAI response: %s", exc)
        return dict(NO_VIOLATION)

    violation = bool(payload.get("violation"))
    kind = payload.get("kind")
    if kind not in _VALID_KINDS:
        kind = None
    if not violation or kind is None:
        return dict(NO_VIOLATION)

    detail = payload.get("detail")
    detail = detail.strip() if isinstance(detail, str) and detail.strip() else "Proctoring violation detected."
    return {"violation": True, "kind": kind, "detail": detail}
