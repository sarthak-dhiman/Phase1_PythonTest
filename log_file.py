from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import logging
from typing import Dict, List
import re

logger = logging.getLogger(__name__)


@dataclass
class LogFile:
    """Parse a simple whitespace-delimited log file into columnar lists.

    Expected line format (minimum):
        <TIMESTAMP> <LEVEL> <MODULE> <MESSAGE...>

    The parser recognizes standard levels including DEBUG, INFO, WARN, ERROR
    and treats any other token as a level as well (grouped as INVALID by analytics).
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

        # Regex: timestamp (non-space), level (non-space), module (non-space), message (rest)
        pattern = re.compile(r"^(\S+)\s+(\S+)\s+(\S+)\s+(.*)$")
        for idx, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            m = pattern.match(line.rstrip('\n'))
            if not m:
                logger.debug("Skipping malformed line %d (no match): %r", idx, line)
                continue

            ts, lvl, mod, msg = m.groups()
            self.logs["TIMESTAMP"].append(ts)
            self.logs["LEVEL"].append(lvl)
            self.logs["MODULE"].append(mod)
            self.logs["MESSAGE"].append(msg)

        return self.logs


# Backwards-compatible alias
Util = LogFile
