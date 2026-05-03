import pytest

from cookiecloud import client
from tests.log_assertions import assert_timestamped_lines


def test_resolve_cookie_value_prefers_direct_environment_cookie(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("V2EX_COOKIE", "sid=direct")

    def fail_cookiecloud_lookup(domains: list[str]) -> str:
        raise AssertionError("Cookie Cloud should not be used when direct cookie exists")

    monkeypatch.setattr(client, "_get_cookiecloud_cookie", fail_cookiecloud_lookup)

    assert client.resolve_cookie_value("V2EX_COOKIE", ["v2ex.com"]) == (
        "sid=direct",
        "environment",
    )


def test_resolve_cookie_value_reports_cookiecloud_source(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("V2EX_COOKIE", raising=False)
    monkeypatch.setattr(client, "_get_cookiecloud_cookie", lambda domains: "sid=cloud")

    assert client.resolve_cookie_value("V2EX_COOKIE", ["v2ex.com"], announce=True) == (
        "sid=cloud",
        "Cookie Cloud",
    )
    output_lines = assert_timestamped_lines(capsys.readouterr().out)
    assert len(output_lines) == 1
    assert "V2EX_COOKIE loaded from Cookie Cloud" in output_lines[0]
