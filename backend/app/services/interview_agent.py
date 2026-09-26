"""AI interview agent: ask plan questions, evaluate answers, decide follow-ups."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.config import settings
from app.models import InterviewQuestion, InterviewTurn
from app.services.llm_json import as_str_list

logger = logging.getLogger(__name__)


def _word_count(text: str) -> int:
    return len([part for part in text.strip().split() if part])


def _baseline_evaluate(
    answer: str,
    question: InterviewQuestion,
    follow_up_count: int,
    follow_up_limit: int,
) -> dict[str, Any]:
    words = _word_count(answer)
    skill = question.skill_ref or question.topic
    mentions_skill = skill.lower() in answer.lower() if skill else False

    if words < 20:
        technical = 3.0
        communication = 3.5
        should_follow_up = follow_up_count < follow_up_limit
        strengths: list[str] = []
        weaknesses = ["Answer was too brief to demonstrate depth."]
        observations = ["Candidate provided limited detail."]
    elif words < 60:
        technical = 5.5 if mentions_skill else 4.5
        communication = 5.5
        should_follow_up = follow_up_count < follow_up_limit and not mentions_skill
        strengths = ["Answer covered the topic at a high level."]
        weaknesses = ["Could include more concrete examples or trade-offs."]
        observations = ["Moderate detail provided."]
    else:
        technical = 7.5 if mentions_skill else 6.5
        communication = 7.0
        should_follow_up = False
        strengths = ["Answer included substantial detail."]
        weaknesses = []
        observations = ["Candidate elaborated with useful context."]
        if mentions_skill:
            strengths.append(f"Referenced relevant skill/topic: {skill}.")

    follow_up_question = None
    if should_follow_up:
        follow_up_question = (
            f"Can you give a concrete example involving {skill}, including challenges you faced "
            f"and how you measured success?"
            if skill
            else "Can you walk through a concrete example, including challenges and outcomes?"
        )

    quotes = []
    cleaned = " ".join(answer.split())
    if cleaned:
        quotes.append(cleaned[:220] + ("..." if len(cleaned) > 220 else ""))

    return {
        "technical_score": technical,
        "communication_score": communication,
        "observations": observations,
        "evidence_quotes": quotes,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "should_follow_up": should_follow_up,
        "follow_up_question": follow_up_question,
        "advance_question": not should_follow_up,
        "model_version": "baseline",
        "raw_model_response": None,
    }


def _openai_evaluate(
    answer: str,
    question: InterviewQuestion,
    recent_turns: list[InterviewTurn],
    follow_up_count: int,
    follow_up_limit: int,
    job_title: str,
) -> dict[str, Any] | None:
    if not settings.openai_api_key:
        logger.info("interview_agent: no OpenAI API key configured, using deterministic baseline")
        return None

    history = [
        {
            "role": turn.role.value.lower(),
            "content": turn.content,
            "is_follow_up": turn.is_follow_up,
        }
        for turn in recent_turns[-8:]
    ]

    prompt = {
        "job_title": job_title,
        "current_question": {
            "text": question.text,
            "topic": question.topic,
            "skill_ref": question.skill_ref,
            "question_type": question.question_type,
        },
        "candidate_answer": answer,
        "follow_up_count": follow_up_count,
        "follow_up_limit": follow_up_limit,
        "recent_turns": history,
        "instructions": (
            "Evaluate the candidate answer for a software engineering interview. "
            "Return JSON with keys: technical_score (0-10), communication_score (0-10), "
            "observations (string array), evidence_quotes (string array of short quotes from the answer), "
            "strengths (string array), weaknesses (string array), should_follow_up (bool), "
            "follow_up_question (string or null), advance_question (bool). "
            "Ask a follow-up only if the answer is incomplete and follow_up_count < follow_up_limit. "
            "Ground observations in the answer text only. "
            "Every array field MUST be a JSON array of strings, never a single concatenated "
            "string or null."
        ),
    }

    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_model,
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an AI interviewer for software engineering roles. "
                            "Evaluate answers and decide whether a bounded follow-up is needed."
                        ),
                    },
                    {"role": "user", "content": json.dumps(prompt)},
                ],
            },
            timeout=45.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        payload = json.loads(content)

        should_follow_up = bool(payload.get("should_follow_up")) and follow_up_count < follow_up_limit
        follow_up_question = payload.get("follow_up_question") if should_follow_up else None
        if should_follow_up and not follow_up_question:
            follow_up_question = (
                f"Please expand on your experience with {question.skill_ref or question.topic} "
                f"using a concrete project example."
            )

        fallback_quote_cleaned = " ".join(answer.split())
        fallback_quotes = (
            [fallback_quote_cleaned[:220] + ("..." if len(fallback_quote_cleaned) > 220 else "")]
            if fallback_quote_cleaned
            else []
        )
        evidence_quotes = as_str_list(payload.get("evidence_quotes"), fallback_quotes)

        return {
            "technical_score": float(payload.get("technical_score", 5)),
            "communication_score": float(payload.get("communication_score", 5)),
            "observations": as_str_list(payload.get("observations"), []),
            "evidence_quotes": evidence_quotes,
            "strengths": as_str_list(payload.get("strengths"), []),
            "weaknesses": as_str_list(payload.get("weaknesses"), []),
            "should_follow_up": should_follow_up,
            "follow_up_question": follow_up_question,
            "advance_question": not should_follow_up,
            "model_version": settings.openai_model,
            "raw_model_response": payload,
        }
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "interview_agent: OpenAI returned status %s: %s",
            exc.response.status_code,
            exc.response.text[:300],
        )
        return None
    except httpx.HTTPError as exc:
        logger.warning("interview_agent: OpenAI request failed: %s", exc)
        return None
    except (KeyError, json.JSONDecodeError, IndexError, TypeError, ValueError) as exc:
        logger.warning("interview_agent: could not parse OpenAI response: %s", exc)
        return None


class InterviewAgentService:
    def evaluate_answer(
        self,
        answer: str,
        question: InterviewQuestion,
        recent_turns: list[InterviewTurn],
        follow_up_count: int,
        follow_up_limit: int,
        job_title: str,
    ) -> dict[str, Any]:
        enhanced = _openai_evaluate(
            answer, question, recent_turns, follow_up_count, follow_up_limit, job_title
        )
        if enhanced:
            return enhanced
        return _baseline_evaluate(answer, question, follow_up_count, follow_up_limit)
