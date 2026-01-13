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
        known = {"ERROR", "INFO", "WARN", "DEBUG"}
        invalid = sum(v for k, v in counts.items() if k not in known)

        return {
            "ERROR": counts.get("ERROR", 0),
            "INFO": counts.get("INFO", 0),
            "WARN": counts.get("WARN", 0),
            "DEBUG": counts.get("DEBUG", 0),
            "INVALID": invalid,
        }

    def calculate_module_stats(self) -> Dict[str, int]:
        """Return a mapping of module name -> number of times module appears in logs."""
        modules = self.logs.get("MODULE", [])
        return dict(Counter(modules))

    def calculate_levels_per_module(self) -> Dict[str, Dict[str, int]]:
        """Return a mapping module -> { level -> count }."""
        modules = self.logs.get("MODULE", [])
        levels = self.logs.get("LEVEL", [])
        per_module: Dict[str, Counter] = {}
        for mod, lvl in zip(modules, levels):
            if mod not in per_module:
                per_module[mod] = Counter()
            per_module[mod][lvl] += 1

        # Convert Counters to normal dicts
        return {m: dict(c) for m, c in per_module.items()}

    def generate_report(self) -> None:
        stats = self.calculate_stats()
        print("Overall level counts:")
        for k, v in stats.items():
            print(f"  {k}: {v}")

        # Also print legacy-style lines for compatibility with older tests/tools
        # e.g. "ERROR occured : 1"
        for k in ("ERROR", "INFO", "WARN", "DEBUG"):
            print(f"{k} occured : {stats.get(k, 0)}")

        # Module-level counts
        module_counts = self.calculate_module_stats()
        if module_counts:
            print("\nModule call counts:")
            for mod, cnt in sorted(module_counts.items(), key=lambda x: (-x[1], x[0])):
                print(f"  {mod}: {cnt}")

        # Levels per module breakdown
        levels_per_mod = self.calculate_levels_per_module()
        if levels_per_mod:
            print("\nLevels per module:")
            for mod in sorted(levels_per_mod.keys()):
                print(f"  {mod}:")
                for lvl, cnt in sorted(levels_per_mod[mod].items(), key=lambda x: (-x[1], x[0])):
                    print(f"    {lvl}: {cnt}")


# Backwards-compatible alias
util = UserAnalytics
