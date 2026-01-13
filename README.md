# chicmic_test

## What this folder contains
A small log parsing + analytics demo. Files have been renamed to follow Python conventions (snake_case modules):

- `log_file.py` - Contains `LogFile` class. Parses simple whitespace-delimited log files into a dictionary of lists: TIMESTAMP, LEVEL, MODULE, MESSAGE. Alias `Util` kept for backwards compatibility.
- `user_analytics.py` - Contains `UserAnalytics` class (alias `util`) which computes counts per log level and prints a simple report.
- `base_processor.py` - CLI-style runner that loads a log file, parses it, demonstrates mutation/shallow/deep copy behavior and prints the analytics report. Use `base_processor.main(path)` to call programmatically.
- `tests/test_chicmic.py` - Pytest tests covering parsing, analytics calculations, and execution of `base_processor.main` with a temp file.

Other files (legacy names) remain in the repo for backwards compatibility but new code should import the snake_case modules.

## How to run
From repository root (`d:\ChicMic_Study`):

1. (Optional) Create & activate a virtualenv
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

2. Install test deps
   python -m pip install pytest

3. Run tests
   python -m pytest -q

4. Run the demo
   python -m pip install -r requirements.txt  # if you have external deps
   cd chicmic_test
   python base_processor.py


## Notes
- The parser expects at least 4 tokens per log line: TIMESTAMP LEVEL MODULE MESSAGE...
- Unknown levels are counted as `INVALID` in analytics.
- If you need the old module names, they are still present (e.g., `LogFile.py`) and expose compatible classes/aliases.
