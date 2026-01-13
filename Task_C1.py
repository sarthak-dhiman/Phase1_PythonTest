"""Task_C1: Log segregation and error extraction.

This module exposes:
- file_checking(file_path) -> list[str]
- log_segregation(lines) -> (logs, error_list)
- write_error_logs(error_list, out_path)
- CLI: interactive selection preserved under __main__
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple
import logging
import argparse

logger = logging.getLogger(__name__)


def file_checking(file_name: str) -> List[str]:
    p = Path(file_name)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {file_name}")
    return p.read_text(encoding="utf-8").splitlines(True)


def log_segregation(lines: List[str]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    logs = {"TIMESTAMP": [], "LEVEL": [], "MODULE": [], "MESSAGE": []}
    error_list = {"TIMESTAMP": [], "LEVEL": [], "MODULE": [], "MESSAGE": []}

    for raw in lines:
        parts = raw.strip().split()
        if len(parts) < 4:
            logger.debug("Skipping malformed line: %r", raw)
            continue
        ts, level, module = parts[0], parts[1], parts[2]
        message = " ".join(parts[3:])

        logs["TIMESTAMP"].append(ts)
        logs["LEVEL"].append(level)
        logs["MODULE"].append(module)
        logs["MESSAGE"].append(message)

        if level == "ERROR":
            error_list["TIMESTAMP"].append(ts)
            error_list["LEVEL"].append(level)
            error_list["MODULE"].append(module)
            error_list["MESSAGE"].append(message)

    return logs, error_list


def write_error_logs(error_list: Dict[str, List[str]], out_path: str | Path) -> None:
    p = Path(out_path)
    with p.open("a", encoding="utf-8") as fh:
        for ts, level, module, msg in zip(
            error_list["TIMESTAMP"],
            error_list["LEVEL"],
            error_list["MODULE"],
            error_list["MESSAGE"],
        ):
            fh.write(f"{ts} {level} {module} {msg}\n")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Log segregation tool")
    parser.add_argument("file", help="Log file to process")
    parser.add_argument("--write-errors", help="Path to append extracted errors", default=None)
    args = parser.parse_args(argv)

    try:
        lines = file_checking(args.file)
    except FileNotFoundError as e:
        print(e)
        return 1

    logs, error_list = log_segregation(lines)

    if args.write_errors and any(error_list["LEVEL"]):
        write_error_logs(error_list, args.write_errors)

    print("logs and errors parsed")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())