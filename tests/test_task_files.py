import sys
from pathlib import Path

# ensure chicmic_test directory is on sys.path when running tests from repo root
CHICMIC_TEST_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CHICMIC_TEST_DIR))

# Import canonical snake_case modules for core functionality
import log_file
import user_analytics
import base_processor

# Task modules (use the existing filenames in the repo)
import Task_B1 as task_b1
import Task_C1 as task_c1


def sample_log_content() -> str:
    return (
        "2026-01-12_10:15:01 INFO  app.startup        Application started\n"
        "2026-01-12_10:15:05 WARN  auth.login        Failed login attempt for user=admin\n"
        "2026-01-12_10:15:12 ERROR payments.process Payment failed order_id=1042 reason=INSUFFICIENT_FUNDS\n"
    )


def test_task_b1_parse_and_important(tmp_path):
    p = tmp_path / "b1log.txt"
    p.write_text(sample_log_content(), encoding="utf-8")

    logs = task_b1.parse_log_file(p)
    assert len(logs['LEVEL']) == 3

    important = task_b1.find_important_logs(logs)
    # one WARN, one ERROR => 2 important
    assert len(important) == 2
    assert important[0][1] == 'WARN'


def test_task_c1_segregation_and_write(tmp_path):
    p = tmp_path / "c1log.txt"
    p.write_text(sample_log_content(), encoding="utf-8")

    lines = task_c1.file_checking(p)
    logs, errors = task_c1.log_segregation(lines)

    assert len(logs['LEVEL']) == 3
    assert len(errors['LEVEL']) == 1

    out = tmp_path / "errors_out.txt"
    task_c1.write_error_logs(errors, out)
    assert out.read_text(encoding='utf-8').count('ERROR') == 1


def test_additional_analytics():
    logs = {'LEVEL': ['INFO', 'WARN', 'ERROR', 'DEBUG', 'UNKNOWN']}
    ua = user_analytics.UserAnalytics(logs)
    stats = ua.calculate_stats()
    assert stats['INVALID'] == 2
