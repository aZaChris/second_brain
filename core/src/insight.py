"""Decide se e con quale priorità segnalare un collegamento trovato (FR-005, FR-006)."""

from __future__ import annotations

from dataclasses import dataclass

from .similarity import Match


@dataclass(frozen=True)
class Insight:
    event_id: str
    similarity: float
    priority: str  # "alta" | "normale"


def decide_insight(
    matches: list[Match],
    preferences: dict,
    *,
    current_text: str,
    matched_text_by_event_id: dict[str, str],
) -> Insight | None:
    if preferences.get("depth_level") == "minimo":
        return None
    if not matches:
        return None

    best = matches[0]
    matched_text = matched_text_by_event_id.get(best.event_id, "")
    combined = f"{current_text} {matched_text}".lower()
    interests = preferences.get("interests", [])
    is_of_interest = any(interest.lower() in combined for interest in interests)

    return Insight(
        event_id=best.event_id,
        similarity=best.similarity,
        priority="alta" if is_of_interest else "normale",
    )
