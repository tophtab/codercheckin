import pytest

from cookiecloud import client


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
) -> None:
    monkeypatch.delenv("V2EX_COOKIE", raising=False)
    monkeypatch.setattr(client, "_get_cookiecloud_cookie", lambda domains: "sid=cloud")

    assert client.resolve_cookie_value("V2EX_COOKIE", ["v2ex.com"]) == (
        "sid=cloud",
        "Cookie Cloud",
    )
