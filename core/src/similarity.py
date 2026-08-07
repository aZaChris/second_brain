"""Confronto per similarità semantica tra eventi (FR-004, FR-008)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

MIN_TEXT_LENGTH = 8  # ponytail: soglia fissa per contenuti troppo generici (FR-008), affina con dati reali


def is_low_signal(text: str) -> bool:
    return len(text.strip()) < MIN_TEXT_LENGTH


def cosine_similarity(a: list[float], b: list[float]) -> float:
    vec_a, vec_b = np.array(a), np.array(b)
    denom = np.linalg.norm(vec_a) * np.linalg.norm(vec_b)
    if denom == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / denom)


@dataclass(frozen=True)
class Match:
    event_id: str
    similarity: float


def find_similar(embedding: list[float], saved_events: list[dict], threshold: float) -> list[Match]:
    """Confronta `embedding` con gli eventi già salvati (FR-004), scartando quelli sotto
    soglia (FR-008), ordinati per pertinenza decrescente."""
    matches = [
        Match(event_id=saved["event_id"], similarity=cosine_similarity(embedding, saved["embedding"]))
        for saved in saved_events
    ]
    relevant = [m for m in matches if m.similarity >= threshold]
    return sorted(relevant, key=lambda m: m.similarity, reverse=True)
