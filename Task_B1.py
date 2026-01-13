"""Task_B1: Log parser and important-log detector.

Provides:
- parse_log_file(path) -> logs dict
- find_important_logs(logs) -> list of important log entries
- CLI: accepts a filename and prints important logs
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple
import logging
import argparse

logger = logging.getLogger(__name__)

INFO = 0b0001
WARN = 0b0010
ERROR = 0b0100

LEVEL_FLAGS = {
    "INFO": INFO,
    "WARN": WARN,
    "ERROR": ERROR,
}

IMPORTANT_LEVELS = WARN | ERROR


def parse_log_file(file_path: str | Path) -> Dict[str, List[str]]:
    """Parse a whitespace-delimited log file into columns.

    Expected per-line format: TIMESTAMP LEVEL MODULE MESSAGE...
    Returns a dict with keys TIMESTAMP, LEVEL, MODULE, MESSAGE.
    """
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"Log file not found: {file_path}")

    logs = {"TIMESTAMP": [], "LEVEL": [], "MODULE": [], "MESSAGE": []}

    with p.open("r", encoding="utf-8") as fh:
        for raw in fh:
            parts = raw.strip().split()
            if len(parts) < 4:
                logger.debug("Skipping malformed line: %r", raw)
                continue
            logs["TIMESTAMP"].append(parts[0])
            logs["LEVEL"].append(parts[1])
            logs["MODULE"].append(parts[2])
            logs["MESSAGE"].append(" ".join(parts[3:]))

    return logs


def find_important_logs(logs: Dict[str, List[str]]) -> List[Tuple[str, str, str, str]]:
    """Return list of important logs (WARN or ERROR) as tuples.

    Each tuple is (timestamp, level, module, message).
    """
    res: List[Tuple[str, str, str, str]] = []
    for ts, level, mod, msg in zip(
        logs.get("TIMESTAMP", []),
        logs.get("LEVEL", []),
        logs.get("MODULE", []),
        logs.get("MESSAGE", []),
    ):
        flag = LEVEL_FLAGS.get(level, 0)
        if flag & IMPORTANT_LEVELS:
            res.append((ts, level, mod, msg))
    return res


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect important logs (WARN/ERROR)")
    parser.add_argument("file", help="Path to log file")
    args = parser.parse_args(argv)

    try:
        logs = parse_log_file(args.file)
    except FileNotFoundError as e:
        print(e)
        return 1

    important = find_important_logs(logs)
    if important:
        print("IMPORTANT LOGS FOUND:")
        for ts, level, mod, msg in important:
            print(ts, level, mod, msg)
    else:
        print("No important logs found")

    print("parsing complete")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())