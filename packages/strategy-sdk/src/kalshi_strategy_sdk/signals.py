from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SignalMetadata:
    confidence: float | None = None
    estimated_probability: float | None = None
    expected_edge: float | None = None
    notes: str | None = None
