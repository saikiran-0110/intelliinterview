"""Calibrate settings.semantic_match_threshold against real CV/job-spec text.

Usage (from backend/, with OPENAI key set in app/config.py):
    .venv/Scripts/python.exe scripts/calibrate_semantic_threshold.py path/to/cv.txt path/to/job_spec.txt

For every job-required skill that is NOT a lexical strong/partial match on the CV,
embeds the skill's descriptive phrase (app/services/skill_catalog.SKILL_PHRASES),
compares it against every chunk of the CV, and prints the best-matching chunk with
its cosine similarity. A suggested threshold is printed at the midpoint of the
largest gap between consecutive (sorted) similarity scores - the natural cut point
in the actual data, not a guess.

Only reads files and calls the OpenAI embeddings endpoint; makes no database or
HTTP-server calls, so it is safe to run standalone against any two text files.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.services.embeddings import cosine_similarity, embed_texts  # noqa: E402
from app.services.skill_catalog import (  # noqa: E402
    chunk_document,
    compare_skills,
    parse_cv_profile,
    parse_job_requirements,
    skill_phrase,
)


def _read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: calibrate_semantic_threshold.py <cv_file> <job_spec_file>")
        raise SystemExit(1)
    if not settings.openai_api_key:
        print("No OpenAI API key configured in app/config.py - calibration needs real embeddings.")
        raise SystemExit(1)

    cv_text = _read_text(sys.argv[1])
    job_text = _read_text(sys.argv[2])

    cv_profile = parse_cv_profile(cv_text)
    job_requirements = parse_job_requirements(job_text)
    matches = compare_skills(cv_profile["skills"], job_requirements["required_skills"])
    gap_skills = [item["name"] for item in matches["gaps"]]

    if not gap_skills:
        print("No lexical gaps for this CV/job pair - nothing to calibrate against.")
        return

    chunks = chunk_document(cv_text)
    if not chunks:
        print("CV produced no chunks (too short or empty) - nothing to calibrate against.")
        return

    print(f"CV chunked into {len(chunks)} passages.\n")

    chunk_vectors = embed_texts(chunks)
    if not chunk_vectors:
        print("Embedding the CV chunks failed - check the API key and network, then retry.")
        raise SystemExit(1)

    rows: list[tuple[str, float, str]] = []
    for skill in gap_skills:
        phrase_vectors = embed_texts([skill_phrase(skill)])
        if not phrase_vectors:
            continue
        phrase_vector = phrase_vectors[0]
        best_score = -1.0
        best_chunk = ""
        for chunk_text, vector in zip(chunks, chunk_vectors):
            score = cosine_similarity(phrase_vector, vector)
            if score > best_score:
                best_score = score
                best_chunk = chunk_text
        rows.append((skill, best_score, best_chunk))

    rows.sort(key=lambda row: row[1], reverse=True)

    print(f"{'skill':<20} {'similarity':>10}   best-matching CV chunk")
    print("-" * 100)
    for skill, score, chunk_text in rows:
        excerpt = chunk_text if len(chunk_text) <= 70 else chunk_text[:67] + "..."
        print(f"{skill:<20} {score:>10.3f}   {excerpt}")

    scores = sorted((row[1] for row in rows), reverse=True)
    if len(scores) >= 2:
        largest_gap = 0.0
        suggested = scores[0]
        for a, b in zip(scores, scores[1:]):
            gap = a - b
            if gap > largest_gap:
                largest_gap = gap
                suggested = (a + b) / 2
        print(f"\nSuggested threshold (midpoint of largest score gap): {suggested:.3f}")
    else:
        print(f"\nOnly one scored skill ({scores[0]:.3f}) - not enough data to suggest a cut point.")

    print(f"Current settings.semantic_match_threshold = {settings.semantic_match_threshold}")


if __name__ == "__main__":
    main()
