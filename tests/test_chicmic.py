import sys
from pathlib import Path

# Make chicmic_test importable when running pytest from repo root
CHICMIC_TEST_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CHICMIC_TEST_DIR))

from log_file import LogFile
from user_analytics import UserAnalytics
import base_processor as BaseProcessor


def sample_log_content() -> str:
    return (
        "2026-01-12_10:15:01 INFO  app.startup        Application started\n"
        "2026-01-12_10:15:05 WARN  auth.login        Failed login attempt for user=admin\n"
        "2026-01-12_10:15:12 ERROR payments.process Payment failed order_id=1042 reason=INSUFFICIENT_FUNDS\n"
    )


def test_logfile_parse(tmp_path):
    p = tmp_path / "testlog.txt"
    p.write_text(sample_log_content(), encoding="utf-8")

    lf = LogFile(p)
    lf.parse_records()

    assert len(lf.logs['LEVEL']) == 3
    assert lf.logs['LEVEL'][0] == 'INFO'
    assert lf.logs['MODULE'][-1] == 'payments.process'


def test_useranalytics_calculate():
    logs = {'LEVEL': ['INFO', 'WARN', 'ERROR', 'DEBUG']}
    ua = UserAnalytics(logs)
    stats = ua.calculate_stats()

    assert stats['ERROR'] == 1
    assert stats['INFO'] == 1
    assert stats['WARN'] == 1
    # DEBUG is treated as INVALID
    assert stats['INVALID'] == 1


def test_baseprocessor_main(tmp_path, capsys):
    p = tmp_path / "log.txt"
    p.write_text(sample_log_content(), encoding="utf-8")

    BaseProcessor.main(str(p))

    captured = capsys.readouterr()
    assert "Records:" in captured.out
    assert "ERROR occured : 1" in captured.out
