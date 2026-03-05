from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    id: str
    title: str
    severity: str  # ERROR | WARN | INFO
    pain_point: str  # iac_drift | delivery | reliability | security
    remediation: str
    evidence: tuple[str, ...] = ()

