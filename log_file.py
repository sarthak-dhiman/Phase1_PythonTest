from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import logging
from typing import Dict, List, Any
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

    # Accept a path (str/Path), raw bytes, or a file-like object with `read()`.
    file_name: str | Path | bytes | Any
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

        Supports:
        - `file_name` as a filesystem path (str/Path)
        - `file_name` as raw bytes
        - `file_name` as a file-like object (must implement `read()`)

        Returns an empty list if file is missing.
        """
        try:
            # Raw bytes have highest precedence
            if isinstance(self.file_name, (bytes, bytearray)):
                return self.file_name.decode("utf-8").splitlines(True)

            # File-like objects (streams)
            if hasattr(self.file_name, "read"):
                raw = self.file_name.read()
                if isinstance(raw, (bytes, bytearray)):
                    text = raw.decode("utf-8")
                else:
                    text = raw
                return text.splitlines(True)

            # Fallback to path-based reading
            return self.path.read_text(encoding="utf-8").splitlines(True)
        except FileNotFoundError:
            logger.error("Log file not found: %s", self.path)
            return []
        except Exception:
            logger.exception("Failed to load log content from %r", self.file_name)
            raise

    def parse_records(self) -> Dict[str, List[str]]:
        """Parse input into `self.logs` and return it.

        This method avoids loading entire files into memory for file-like
        objects by iterating over the stream line-by-line. Supported input
        types for `file_name`:
        - filesystem path (str / Path)
        - raw bytes or bytearray
        - file-like object supporting iteration over lines (e.g. open file,
          io.BytesIO, SpooledTemporaryFile)

        Malformed lines are skipped with a debug log message.
        """

        # Regex: timestamp (non-space), level (non-space), module (non-space), message (rest)
        pattern = re.compile(r"^(\S+)\s+(\S+)\s+(\S+)\s+(.*)$")

        def process_line(idx: int, line: str) -> None:
            if not line.strip():
                return
            m = pattern.match(line.rstrip('\n'))
            if not m:
                logger.debug("Skipping malformed line %d (no match): %r", idx, line)
                return
            ts, lvl, mod, msg = m.groups()
            self.logs["TIMESTAMP"].append(ts)
            self.logs["LEVEL"].append(lvl)
            self.logs["MODULE"].append(mod)
            self.logs["MESSAGE"].append(msg)

        # If raw bytes were provided, decode and iterate lines
        if isinstance(self.file_name, (bytes, bytearray)):
            text = self.file_name.decode("utf-8")
            for idx, line in enumerate(text.splitlines(True), start=1):
                process_line(idx, line)
            return self.logs

        # If a file-like object was provided, iterate it line by line
        if hasattr(self.file_name, "read") and hasattr(self.file_name, "readline"):
            try:
                # Some file-like objects are binary; ensure text
                for idx, raw in enumerate(self.file_name, start=1):
                    # raw may be bytes
                    if isinstance(raw, (bytes, bytearray)):
                        line = raw.decode("utf-8")
                    else:
                        line = raw
                    process_line(idx, line)
                return self.logs
            except Exception:
                # Fall back to load_file behavior if iteration fails
                logger.exception("Falling back to full-load parsing for %r", self.file_name)

        # Otherwise, treat as path or fallback to loading file contents
        lines = self.load_file()
        for idx, line in enumerate(lines, start=1):
            process_line(idx, line)

        return self.logs


# Backwards-compatible alias
Util = LogFile
