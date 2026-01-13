"""Module log_file

Provides the LogFile class to parse simple whitespace-delimited log files.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


@dataclass
class LogFile:
    """Parse a simple whitespace-delimited log file into columnar lists.

    Expected line format (minimum):
        <TIMESTAMP> <LEVEL> <MODULE> <MESSAGE...>

    The parser is tolerant to extra whitespace and skips malformed lines.
    """

    file_name: str | Path
    logs: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "TIMESTAMP": [],
            "LEVEL": [],
            "MODULE": [],
            "MESSAGE": [],
        }
    )

    def __str__(self) -> str:
        return f"LogFile('{self.file_name}') | Records: {len(self.logs['LEVEL'])}" 

    @property
    def path(self) -> Path:
        return self.file_name if isinstance(self.file_name, Path) else Path(self.file_name)

    def load_file(self) -> list[str]:
        """Load raw lines.

        Returns an empty list if file is missing.
        """
        try:
            return self.path.read_text(encoding="utf-8").splitlines(True)
        except FileNotFoundError:
            logger.error("Log file not found: %s", self.path)
            return []

    def parse_records(self) -> Dict[str, List[str]]:
        """Parse file content into self.logs and return it."""
        lines = self.load_file()

        for line in lines:
            parts = line.strip().split()
            if len(parts) < 4:
                logger.debug("Skipping malformed line (expected >=4 parts): %r", line)
                continue

            self.logs["TIMESTAMP"].append(parts[0])
            self.logs["LEVEL"].append(parts[1])
            self.logs["MODULE"].append(parts[2])
            self.logs["MESSAGE"].append(" ".join(parts[3:]))

        return self.logs


# Backwards-compatible alias
Util = LogFile
