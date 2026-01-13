# chicmic_test

## What this folder contains
A small log parsing + analytics demo. Files follow Python conventions (snake_case modules):

- `log_file.py` - Contains `LogFile` class. Parses whitespace-delimited log files into TIMESTAMP, LEVEL, MODULE, MESSAGE.
- `user_analytics.py` - Contains `UserAnalytics` class; computes counts per log level and prints a report.
- `base_processor.py` - CLI-style runner used as the default entrypoint in the Docker image. Use `base_processor.main(path)` to call programmatically.
- `tests/` - Pytest tests covering parsing and analytics.

## How to run locally (without Docker)
1. (Optional) Create & activate a virtualenv
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

2. Install test deps
   python -m pip install pytest

3. Run tests
   python -m pytest -q

4. Run the demo
   python -m pip install -r requirements.txt
   python base_processor.py


## Docker: build and run (PowerShell)
From the project root (`D:\ChicMic_Study\chicmic_test`):

- Build the image (include the final dot as the build context):
  docker build -t chicmic_test .

- Run the container interactively and map port 8000 (if your app uses it):
  docker run --rm -it -p 8000:8000 chicmic_test

- Override the default command (example: run tests):
  docker run --rm -it chicmic_test pytest -q

- Inspect installed packages inside the image:
  docker run --rm chicmic_test pip freeze

Notes:
- Rebuild the image whenever you change `requirements.txt` or the Dockerfile.
- If you accidentally run `docker buildx build` without a PATH, you will get: "requires 1 argument" — provide `.` as the final argument.
