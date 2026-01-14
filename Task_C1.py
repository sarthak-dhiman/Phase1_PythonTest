"""Task_C1: Log segregation and error extraction.

This module exposes:
- file_checking(file_path) -> list[str]
- log_segregation(lines) -> (logs, error_list)
- write_error_logs(error_list, out_path)
- CLI: interactive selection preserved under __main__
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple, Union
from log_file import LogFile
import logging
import argparse

logger = logging.getLogger(__name__)


def file_checking(file_name: str) -> List[str]:
    p = Path(file_name)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {file_name}")
    return p.read_text(encoding="utf-8").splitlines(True)


def log_segregation(lines_or_path: Union[List[str], str, Path]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Segregate logs into a logs dict and an error_list dict.

    Accepts either a list of raw lines or a filesystem path/filename. When a
    path is provided, parsing is delegated to `LogFile` to ensure a single
    canonical parser implementation.
    """
    # If a path-like object or string is passed, use LogFile to parse.
    if isinstance(lines_or_path, (str, Path)):
        lf = LogFile(lines_or_path)
        lf.parse_records()
        logs = lf.logs
    else:
        lines = lines_or_path
        logs = {"TIMESTAMP": [], "LEVEL": [], "MODULE": [], "MESSAGE": []}
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

    # Build error_list from the canonical logs structure
    error_list = {"TIMESTAMP": [], "LEVEL": [], "MODULE": [], "MESSAGE": []}
    for ts, level, module, msg in zip(
        logs.get("TIMESTAMP", []),
        logs.get("LEVEL", []),
        logs.get("MODULE", []),
        logs.get("MESSAGE", []),
    ):
        if level == "ERROR":
            error_list["TIMESTAMP"].append(ts)
            error_list["LEVEL"].append(level)
            error_list["MODULE"].append(module)
            error_list["MESSAGE"].append(msg)

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