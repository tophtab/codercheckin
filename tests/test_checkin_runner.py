import io
import subprocess
import sys

import pytest

from checkin_runner import (
    RECENT_OUTPUT_LINE_LIMIT,
    TargetExecutionError,
    parse_targets,
    run_targets,
    validate_target_cookies,
)


class FakeProcess:
    def __init__(
        self,
        command: list[str],
        returncode: int,
        stdout_text: str = "",
        stderr_text: str = "",
    ) -> None:
        self.command = command
        self.returncode = returncode
        self.stdout = io.StringIO(stdout_text)
        self.stderr = io.StringIO(stderr_text)

    def wait(self) -> int:
        return self.returncode


def test_parse_targets_uses_default_targets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CHECKIN_TARGETS", raising=False)

    assert parse_targets() == ["nodeseek", "deepflood", "v2ex"]


def test_parse_targets_rejects_unknown_target(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHECKIN_TARGETS", "nodeseek,unknown")

    with pytest.raises(ValueError, match="Unknown check-in targets"):
        parse_targets()


def test_validate_target_cookies_accepts_direct_cookie_source(
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[tuple[str, list[str]]] = []

    def fake_resolve_cookie(env_name: str, domains: list[str]) -> tuple[str, str]:
        calls.append((env_name, domains))
        return "sid=direct", "environment"

    validate_target_cookies(["v2ex"], resolve_cookie=fake_resolve_cookie)

    assert calls == [("V2EX_COOKIE", ["v2ex.com", "www.v2ex.com"])]
    output = capsys.readouterr().out
    assert "Startup validation: target 'v2ex' has cookie from environment" in output
    assert "sid=direct" not in output


def test_validate_target_cookies_accepts_cookiecloud_source(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_resolve_cookie(env_name: str, domains: list[str]) -> tuple[str, str]:
        return "sid=from-cloud", "Cookie Cloud"

    validate_target_cookies(["nodeseek"], resolve_cookie=fake_resolve_cookie)

    output = capsys.readouterr().out
    assert "Startup validation: target 'nodeseek' has cookie from Cookie Cloud" in output
    assert "sid=from-cloud" not in output


def test_validate_target_cookies_rejects_missing_cookie(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_resolve_cookie(env_name: str, domains: list[str]) -> tuple[str, str]:
        return "", ""

    with pytest.raises(ValueError) as excinfo:
        validate_target_cookies(["deepflood"], resolve_cookie=fake_resolve_cookie)

    message = str(excinfo.value)
    assert "Startup validation failed" in message
    assert "deepflood (DEEPFLOOD_COOKIE; domains: deepflood.com, www.deepflood.com)" in message

    output = capsys.readouterr().out
    assert "Startup validation: target 'deepflood' has no cookie" in output


def test_run_targets_logs_success_for_each_target(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[list[str]] = []
    popen_kwargs: list[dict[str, object]] = []

    def fake_popen(command: list[str], **kwargs: object) -> FakeProcess:
        calls.append(command)
        popen_kwargs.append(kwargs)
        return FakeProcess(command, 0)

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    assert run_targets(["nodeseek", "v2ex"]) == 0
    assert calls == [
        [sys.executable, "-m", "nodeseek.nodeseek"],
        [sys.executable, "-m", "v2ex.v2ex"],
    ]
    assert popen_kwargs == [
        {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "bufsize": 1,
        },
        {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "bufsize": 1,
        },
    ]

    output = capsys.readouterr().out
    assert "Starting check-in target 'nodeseek' (nodeseek.nodeseek)" in output
    assert "Check-in target 'nodeseek' succeeded" in output
    assert "Starting check-in target 'v2ex' (v2ex.v2ex)" in output
    assert "Check-in target 'v2ex' succeeded" in output


def test_run_targets_raises_failure_with_target_context(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[list[str]] = []

    def fake_popen(command: list[str], **kwargs: object) -> FakeProcess:
        calls.append(command)
        return FakeProcess(command, 7)

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    with pytest.raises(TargetExecutionError) as excinfo:
        run_targets(["v2ex", "deepflood"])

    assert calls == [[sys.executable, "-m", "v2ex.v2ex"]]
    assert excinfo.value.target == "v2ex"
    assert excinfo.value.returncode == 7

    output = capsys.readouterr().out
    assert "Starting check-in target 'v2ex' (v2ex.v2ex)" in output
    assert "Check-in target 'v2ex' failed with exit code 7" in output
    assert "Recent output from failed target 'v2ex':" in output
    assert "  (no stdout/stderr output captured)" in output
    assert "Starting check-in target 'deepflood'" not in output


def test_run_targets_forwards_output_and_summarizes_recent_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[list[str]] = []

    def fake_popen(command: list[str], **kwargs: object) -> FakeProcess:
        calls.append(command)
        return FakeProcess(
            command,
            7,
            stdout_text="opening v2ex\nfailed step: daily mission\n",
            stderr_text="actual error string: cookie expired\n",
        )

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    with pytest.raises(TargetExecutionError) as excinfo:
        run_targets(["v2ex", "deepflood"])

    assert calls == [[sys.executable, "-m", "v2ex.v2ex"]]

    captured = capsys.readouterr()
    assert "opening v2ex" in captured.out
    assert "failed step: daily mission" in captured.out
    assert "actual error string: cookie expired" in captured.err
    assert "Recent output from failed target 'v2ex':" in captured.out
    assert "  [stdout] failed step: daily mission" in captured.out
    assert "  [stderr] actual error string: cookie expired" in captured.out
    assert "Starting check-in target 'deepflood'" not in captured.out
    message = str(excinfo.value)
    assert "Check-in target 'v2ex' failed with exit code 7" in message
    assert "  [stdout] failed step: daily mission" in message
    assert "  [stderr] actual error string: cookie expired" in message


def test_run_targets_exception_message_uses_bounded_recent_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout_text = "".join(
        f"stdout line {line_number}\n"
        for line_number in range(RECENT_OUTPUT_LINE_LIMIT + 2)
    )

    def fake_popen(command: list[str], **kwargs: object) -> FakeProcess:
        return FakeProcess(command, 7, stdout_text=stdout_text)

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    with pytest.raises(TargetExecutionError) as excinfo:
        run_targets(["v2ex"])

    message = str(excinfo.value)
    assert "  [stdout] stdout line 0\n" not in message
    assert "  [stdout] stdout line 1\n" not in message
    assert "  [stdout] stdout line 2" in message
    assert f"  [stdout] stdout line {RECENT_OUTPUT_LINE_LIMIT + 1}" in message


def test_run_targets_wraps_subprocess_start_failures_with_target_context(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_popen(command: list[str], **kwargs: object) -> FakeProcess:
        raise OSError("exec format error")

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    with pytest.raises(TargetExecutionError) as excinfo:
        run_targets(["v2ex", "deepflood"])

    assert excinfo.value.target == "v2ex"
    assert excinfo.value.returncode is None

    output = capsys.readouterr().out
    assert "Starting check-in target 'v2ex' (v2ex.v2ex)" in output
    assert "Check-in target 'v2ex' failed before it could start" in output
    assert "Failed to start module 'v2ex.v2ex': exec format error" in output
    assert "Starting check-in target 'deepflood'" not in output

    message = str(excinfo.value)
    assert "Check-in target 'v2ex' failed before it could start" in message
    assert "Failed to start module 'v2ex.v2ex': exec format error" in message
