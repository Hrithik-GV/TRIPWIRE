import pytest
from app.tripwire.risk_checker import RiskChecker, RiskCheckRequest

def test_risk_checker_safe_operations():
    checker = RiskChecker()

    # 1. list_files
    res_list = checker.evaluate(RiskCheckRequest(action="list_files", params={"path": ""}))
    assert res_list.risk_level == "low"
    assert res_list.risk_score <= 0.10
    assert res_list.is_reversible is True

    # 2. read_file (normal file)
    res_read = checker.evaluate(RiskCheckRequest(action="read_file", params={"path": "app.py"}))
    assert res_read.risk_level == "low"
    assert res_read.risk_score <= 0.15
    assert res_read.is_reversible is True

    # 3. run_tests
    res_test = checker.evaluate(RiskCheckRequest(action="run_tests", params={"target": "test_app.py"}))
    assert res_test.risk_level == "low"
    assert res_test.risk_score <= 0.25
    assert res_test.is_reversible is True

def test_risk_checker_suspicious_medium_operations():
    checker = RiskChecker()

    # 1. create_file
    res_create = checker.evaluate(RiskCheckRequest(action="create_file", params={"path": "helper.py"}))
    assert res_create.risk_level == "medium"
    assert 0.30 <= res_create.risk_score <= 0.60
    assert res_create.is_reversible is True

    # 2. write_file (code file)
    res_write = checker.evaluate(RiskCheckRequest(action="write_file", params={"path": "app.py"}))
    assert res_write.risk_level == "medium"
    assert 0.40 <= res_write.risk_score <= 0.60
    assert res_write.is_reversible is True

def test_risk_checker_dangerous_high_operations():
    checker = RiskChecker()

    # 1. delete_file (normal file)
    res_del_normal = checker.evaluate(RiskCheckRequest(action="delete_file", params={"path": "temp.txt"}))
    assert res_del_normal.risk_level == "high"
    assert res_del_normal.risk_score >= 0.70
    assert res_del_normal.is_reversible is False

    # 2. delete_file (core source code)
    res_del_core = checker.evaluate(RiskCheckRequest(action="delete_file", params={"path": "app.py"}))
    assert res_del_core.risk_level == "high"
    assert res_del_core.risk_score >= 0.80
    assert "core_code_destruction" in res_del_core.risk_factors

    # 3. write_file to sensitive .env
    res_env = checker.evaluate(RiskCheckRequest(action="write_file", params={"path": ".env"}))
    assert res_env.risk_level == "high"
    assert res_env.risk_score >= 0.70

def test_risk_checker_critical_operations():
    checker = RiskChecker()

    # 1. Unsupported arbitrary shell command
    res_shell = checker.evaluate(RiskCheckRequest(action="execute_shell", params={"cmd": "rm -rf /"}))
    assert res_shell.risk_level == "critical"
    assert res_shell.risk_score >= 0.90
    assert res_shell.is_reversible is False

    # 2. Path traversal attempt
    res_traversal = checker.evaluate(RiskCheckRequest(action="write_file", params={"path": "../../escape.txt"}))
    assert res_traversal.risk_level == "critical"
    assert res_traversal.risk_score == 1.00

    # 3. Mass / Root deletion attempt
    res_root_del = checker.evaluate(RiskCheckRequest(action="delete_file", params={"path": "*"}))
    assert res_root_del.risk_level == "critical"
    assert res_root_del.risk_score == 1.00

