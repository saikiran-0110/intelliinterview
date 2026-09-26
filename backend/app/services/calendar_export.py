"""Calendar export: hand-built ICS files and provider deep-link URLs.

Two-way calendar sync needs OAuth apps registered with Google and Microsoft,
consent screens, and refresh-token storage - out of scope. This covers the
export half instead: a downloadable .ics file, and public "add to calendar"
URL templates for Google and Outlook that need no API access and no auth.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import UUID


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _format_utc_ics(value: datetime) -> str:
    return _ensure_utc(value).strftime("%Y%m%dT%H%M%SZ")


def _format_utc_basic(value: datetime) -> str:
    """Same as the ICS form; kept as a separate name for the provider URL builders."""
    return _format_utc_ics(value)


def _escape_ics_text(value: str) -> str:
    """Escape commas, semicolons, backslashes and newlines per RFC 5545."""
    return (
        value.replace("\\", "\\\\")
        .replace(",", "\\,")
        .replace(";", "\\;")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _fold_line(line: str) -> str:
    """Fold a content line at 75 octets, continuation lines prefixed with a space (RFC 5545)."""
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line

    parts: list[str] = []
    start = 0
    limit = 75
    while start < len(encoded):
        end = min(start + limit, len(encoded))
        # never split in the middle of a multi-byte UTF-8 sequence
        while end < len(encoded) and (encoded[end] & 0xC0) == 0x80:
            end -= 1
        parts.append(encoded[start:end].decode("utf-8"))
        start = end
        limit = 74  # continuation lines lose one octet to the leading space
    return "\r\n ".join(parts)


def build_ics(
    session_id: UUID,
    scheduled_at: datetime,
    duration_minutes: int,
    job_title: str,
    candidate_name: str,
    recruiter_email: str,
    candidate_email: str,
    portal_url: str,
) -> str:
    start = _ensure_utc(scheduled_at)
    end = start + timedelta(minutes=duration_minutes)
    summary = f"Interview: {job_title} with {candidate_name}"
    description = f"AI interview for {job_title}. Join from the candidate portal: {portal_url}"

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//IntelliInterview//Interview Scheduling//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{session_id}@intelliinterview",
        f"DTSTAMP:{_format_utc_ics(datetime.now(timezone.utc))}",
        f"DTSTART:{_format_utc_ics(start)}",
        f"DTEND:{_format_utc_ics(end)}",
        f"SUMMARY:{_escape_ics_text(summary)}",
        f"DESCRIPTION:{_escape_ics_text(description)}",
        f"ORGANIZER;CN={_escape_ics_text(candidate_name)}:mailto:{recruiter_email}",
        f"ATTENDEE;CN={_escape_ics_text(candidate_name)}:mailto:{candidate_email}",
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        "DESCRIPTION:Interview reminder",
        "TRIGGER:-PT15M",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "\r\n".join(_fold_line(line) for line in lines) + "\r\n"


def google_calendar_url(
    scheduled_at: datetime,
    duration_minutes: int,
    job_title: str,
    candidate_name: str,
    portal_url: str,
) -> str:
    start = _ensure_utc(scheduled_at)
    end = start + timedelta(minutes=duration_minutes)
    params = {
        "action": "TEMPLATE",
        "text": f"Interview: {job_title} with {candidate_name}",
        "dates": f"{_format_utc_basic(start)}/{_format_utc_basic(end)}",
        "details": f"AI interview for {job_title}. Join from the candidate portal: {portal_url}",
    }
    return f"https://calendar.google.com/calendar/render?{urlencode(params)}"


def outlook_calendar_url(
    scheduled_at: datetime,
    duration_minutes: int,
    job_title: str,
    candidate_name: str,
    portal_url: str,
) -> str:
    start = _ensure_utc(scheduled_at)
    end = start + timedelta(minutes=duration_minutes)
    params = {
        "path": "/calendar/action/compose",
        "rru": "addevent",
        "subject": f"Interview: {job_title} with {candidate_name}",
        "startdt": start.isoformat(),
        "enddt": end.isoformat(),
        "body": f"AI interview for {job_title}. Join from the candidate portal: {portal_url}",
    }
    return f"https://outlook.live.com/calendar/0/deeplink/compose?{urlencode(params)}"
