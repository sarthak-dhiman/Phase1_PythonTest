"""Module user_analytics

Provides UserAnalytics class to compute counts for log levels.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class UserAnalytics:
    """Compute simple statistics over parsed log dictionaries."""

    logs: Dict[str, List[str]]

    def calculate_stats(self) -> Dict[str, int]:
        levels = self.logs.get("LEVEL", [])
        counts = Counter(levels)

        # Preserve current semantics: unknown levels are grouped as INVALID
        known = {"ERROR", "INFO", "WARN"}
        invalid = sum(v for k, v in counts.items() if k not in known)

        return {
            "ERROR": counts.get("ERROR", 0),
            "INFO": counts.get("INFO", 0),
            "WARN": counts.get("WARN", 0),
            "INVALID": invalid,
        }

    def generate_report(self) -> None:
        stats = self.calculate_stats()
        for k, v in stats.items():
            print(f"{k} occured : {v}")


# Backwards-compatible alias
util = UserAnalytics
