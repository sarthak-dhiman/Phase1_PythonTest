"""CLI runner for the log parsing demo (snake_case module).

This mirrors the behaviour of the original BaseProcessor but uses snake_case
module naming to follow Python conventions.
"""
from log_file import LogFile
from user_analytics import UserAnalytics
import copy
from pathlib import Path
import logging
import sys


def main(file_name: str | None = None) -> None:
    logger = logging.getLogger(__name__)
    # If caller provided a filename programmatically, use it.
    # Otherwise try to read from CLI args, then prompt if stdin is a TTY,
    # and finally fall back to a sensible default for non-interactive runs.
    if file_name is None:
        import argparse
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('file', nargs='?', help='Path to log file')
        parser.add_argument('--file', dest='file_arg', help='Path to log file')
        args, _ = parser.parse_known_args()

        # Prefer positional, then --file
        file_name = None
        if args and getattr(args, 'file', None):
            file_name = args.file
        elif args and getattr(args, 'file_arg', None):
            file_name = args.file_arg

        # If still no filename, prompt interactively when possible
        if not file_name:
            if sys.stdin.isatty():
                try:
                    print("Enter the file name or directory (default: log.txt): ", end='', flush=True)
                    file_name = input().strip() or 'log.txt'
                except EOFError:
                    file_name = 'log.txt'
            else:
                # Non-interactive environment (CI, container without TTY): use default
                file_name = 'log.txt'

    # Resolve the provided path. Try as given, then relative to this module's directory
    # so that passing names like "log.txt" works when running from repo root.
    path = Path(file_name)
    if not path.exists():
        alt = Path(__file__).parent / file_name
        if alt.exists():
            path = alt
            file_name = str(alt)
        else:
            cwd_alt = Path.cwd() / file_name
            if cwd_alt.exists():
                path = cwd_alt
                file_name = str(cwd_alt)

    if not path.exists():
        logger.error("File not found: %s", file_name)
        print(f"File not found: {file_name}")
        sys.exit(1)

    lf = LogFile(file_name)
    logger.info("Loaded LogFile: %s", lf)
    print(lf)

    try:
        lf.parse_records()
    except Exception as e:
        logger.exception("Failed to parse records for %s", file_name)
        print("Failed to parse records:", e)
        sys.exit(1)

    def mutate_logs(log_dict: dict) -> None:
        log_dict['LEVEL'].append("DEBUG")

    # preserve current demonstration logic showing mutation and copy behavior
    lf.logs['LEVEL'].append("INFO")
    mutate_logs(lf.logs)

    shallow_copy = copy.copy(lf)
    shallow_copy.logs['LEVEL'].append("WARN")

    deep_copy = copy.deepcopy(lf)
    deep_copy.logs['LEVEL'].append("ERROR")

    analytics = UserAnalytics(lf.logs)
    analytics.generate_report()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    try:
        main()
    except Exception:
        logging.exception("Unhandled exception in base_processor")
