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

    if not file_name:
        print("Enter the file name or directory")
        file_name = input().strip()

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
