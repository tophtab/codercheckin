import pytest

from config import (
    DEFAULT_ACCEPT_LANGUAGE,
    DEFAULT_BROWSER_IMPERSONATE,
    DEFAULT_SEC_CH_UA,
    DEFAULT_SEC_CH_UA_PLATFORM,
    DEFAULT_USER_AGENT,
)
from tests.log_assertions import assert_timestamped_lines
from v2ex import v2ex


def _redeem_button(action: str) -> str:
    return (
        '<input type="button" class="super normal button" '
        f'value="领取每日登录奖励" onclick="location.href = \'{action}\';">'
    )


def test_get_daily_mission_action_detects_chinese_login_page(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(v2ex, "_fetch_page", lambda url, headers: "需要先登录")

    action_url, signed, message = v2ex.get_daily_mission_action({}, "V2EX\n")

    assert action_url is None
    assert signed is False
    assert "unauthenticated or expired" in message
    output_lines = assert_timestamped_lines(capsys.readouterr().out)
    assert len(output_lines) == 1
    assert (
        "V2EX daily mission page indicates the cookie is unauthenticated"
        in output_lines[0]
    )


def test_get_daily_mission_action_detects_english_login_page(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        v2ex,
        "_fetch_page",
        lambda url, headers: "You need to sign in first to view this page",
    )

    action_url, signed, message = v2ex.get_daily_mission_action({}, "V2EX\n")

    assert action_url is None
    assert signed is False
    assert "unauthenticated or expired" in message
    output_lines = assert_timestamped_lines(capsys.readouterr().out)
    assert len(output_lines) == 1
    assert (
        "V2EX daily mission page indicates the cookie is unauthenticated"
        in output_lines[0]
    )


def test_parse_daily_mission_action_url_extracts_onclick_and_normalizes() -> None:
    action_url = v2ex._parse_daily_mission_action_url(
        '<a href="/balance">Balance</a>'
        + _redeem_button("/mission/daily/redeem?once=secret-once-token")
    )

    assert (
        action_url
        == "https://www.v2ex.com/mission/daily/redeem?once=secret-once-token"
    )


def test_parse_daily_mission_action_url_rejects_redeem_without_once() -> None:
    action_url = v2ex._parse_daily_mission_action_url(
        _redeem_button("/mission/daily/redeem")
    )

    assert action_url is None


def test_build_headers_matches_configured_browser_identity() -> None:
    headers = v2ex.build_headers("sid=direct")

    assert headers["user-agent"] == DEFAULT_USER_AGENT
    assert headers["accept-language"] == DEFAULT_ACCEPT_LANGUAGE
    assert headers["sec-ch-ua"] == DEFAULT_SEC_CH_UA
    assert headers["sec-ch-ua-platform"] == DEFAULT_SEC_CH_UA_PLATFORM
    assert headers["cookie"] == "sid=direct"
    assert "refract-key" not in headers
    assert "refract-sign" not in headers


def test_get_daily_mission_action_does_not_include_token_in_status_message(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        v2ex,
        "_fetch_page",
        lambda url, headers: _redeem_button(
            "/mission/daily/redeem?once=secret-once-token"
        ),
    )

    action_url, signed, message = v2ex.get_daily_mission_action({}, "V2EX\n")

    assert action_url is not None
    assert action_url.endswith("once=secret-once-token")
    assert signed is False
    assert "Successfully got daily mission action" in message
    assert "secret-once-token" not in message
    assert "secret-once-token" not in capsys.readouterr().out


def test_get_daily_mission_action_treats_balance_action_as_signed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        v2ex,
        "_fetch_page",
        lambda url, headers: _redeem_button("/balance"),
    )

    action_url, signed, message = v2ex.get_daily_mission_action({}, "V2EX\n")

    assert action_url is None
    assert signed is True
    assert "already signed today" in message


def test_check_in_requests_action_then_confirms_from_today_balance_entry(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    today = "2026-05-08"
    action_url = "https://www.v2ex.com/mission/daily/redeem?once=redacted-once"
    balance_html = f"""
    <table>
      <tr>
        <td class="d"><small class="gray">{today} 15:22:00 +08:00</small></td>
        <td class="d">每日登录奖励</td>
        <td class="d" style="text-align: right;">+1</td>
        <td class="d" style="text-align: right;">100</td>
      </tr>
    </table>
    """
    calls = []
    monkeypatch.setattr(v2ex, "_today_local_date", lambda: today)

    def fetch_page(url: str, headers: dict[str, str]) -> str:
        calls.append(url)
        if url == action_url:
            return "redeem response changed"
        if url == v2ex.BALANCE_URL:
            return balance_html
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(v2ex, "_fetch_page", fetch_page)

    success, message = v2ex.check_in(action_url, {}, "V2EX\n")

    assert success is True
    assert "Check in successfully, got +1 copper" in message
    assert calls == [action_url, v2ex.BALANCE_URL]
    output_lines = assert_timestamped_lines(capsys.readouterr().out)
    assert any(
        "V2EX balance page confirms today's daily reward: +1 copper" in line
        for line in output_lines
    )
    assert all("redacted-once" not in line for line in output_lines)


def test_shared_session_preserves_mission_cookies_for_redeem_and_balance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    today = "2026-05-08"
    action_url = "https://www.v2ex.com/mission/daily/redeem?once=redacted-once"
    balance_html = f"""
    <table>
      <tr>
        <td class="d"><small class="gray">{today} 15:22:00 +08:00</small></td>
        <td class="d">每日登录奖励</td>
        <td class="d" style="text-align: right;">+1</td>
        <td class="d" style="text-align: right;">100</td>
      </tr>
    </table>
    """

    class Response:
        def __init__(self, text: str) -> None:
            self.text = text

    class Session:
        def __init__(self) -> None:
            self.cookies = {"sid": "initial"}
            self.calls = []

        def get(
            self,
            url: str,
            headers: dict[str, str],
            timeout: int,
        ) -> Response:
            self.calls.append((url, dict(headers), dict(self.cookies), timeout))
            assert "cookie" not in {name.lower() for name in headers}
            if url == v2ex.MISSION_DAILY_URL:
                self.cookies["mission_session"] = "issued"
                return Response(
                    _redeem_button("/mission/daily/redeem?once=redacted-once")
                )
            if url == action_url:
                assert self.cookies["mission_session"] == "issued"
                self.cookies["redeem_session"] = "issued"
                return Response("redeem response changed")
            if url == v2ex.BALANCE_URL:
                assert self.cookies["mission_session"] == "issued"
                assert self.cookies["redeem_session"] == "issued"
                return Response(balance_html)
            raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(v2ex, "_today_local_date", lambda: today)

    session = Session()
    headers = v2ex.build_headers("sid=initial")
    action_url_result, signed, message = v2ex.get_daily_mission_action(
        headers,
        "V2EX\n",
        session,
    )
    success, message = v2ex.check_in(
        action_url_result or "",
        headers,
        message,
        session,
    )

    assert signed is False
    assert action_url_result == action_url
    assert success is True
    assert "Check in successfully, got +1 copper" in message
    assert [call[0] for call in session.calls] == [
        v2ex.MISSION_DAILY_URL,
        action_url,
        v2ex.BALANCE_URL,
    ]
    assert session.calls[1][2]["mission_session"] == "issued"
    assert session.calls[2][2]["redeem_session"] == "issued"
    assert all(call[3] == v2ex.REQUEST_TIMEOUT_SECONDS for call in session.calls)


def test_build_session_seeds_cookie_jar_from_resolved_cookie() -> None:
    session = v2ex.build_session("sid=direct; foo=bar")

    assert session.impersonate == DEFAULT_BROWSER_IMPERSONATE
    assert session.cookies.get("sid") == "direct"
    assert session.cookies.get("foo") == "bar"


def test_check_in_treats_balance_action_as_success() -> None:
    success, message = v2ex.check_in(v2ex.BALANCE_URL, {}, "V2EX\n")

    assert success is True
    assert "already signed today" in message


def test_check_in_rejects_non_v2ex_action_url(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_fetch_page(url: str, headers: dict[str, str]) -> str:
        raise AssertionError("unsupported action URL should not be requested")

    monkeypatch.setattr(v2ex, "_fetch_page", fail_fetch_page)

    success, message = v2ex.check_in(
        "https://example.com/mission/daily/redeem?once=secret-once-token",
        {},
        "V2EX\n",
    )

    assert success is False
    assert "unsupported daily mission action" in message
    assert "secret-once-token" not in message
    output_lines = assert_timestamped_lines(capsys.readouterr().out)
    assert len(output_lines) == 1
    assert (
        "V2EX daily mission action was not a supported V2EX action"
        in output_lines[0]
    )
    assert "example.com" not in output_lines[0]
    assert "secret-once-token" not in output_lines[0]


def test_check_in_requires_balance_after_redeem_success_marker(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    action_url = "https://www.v2ex.com/mission/daily/redeem?once=secret-once-token"
    balance_html = """
    <table>
      <tr>
        <td class="d"><small class="gray">2000-01-01 15:22:00 +08:00</small></td>
        <td class="d">每日登录奖励</td>
        <td class="d" style="text-align: right;">+1</td>
        <td class="d" style="text-align: right;">100</td>
      </tr>
    </table>
    """

    def fetch_page(url: str, headers: dict[str, str]) -> str:
        if url == action_url:
            return "已成功领取每日登录奖励"
        if url == v2ex.BALANCE_URL:
            return balance_html
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(v2ex, "_fetch_page", fetch_page)

    success, message = v2ex.check_in(action_url, {}, "V2EX\n")

    assert success is False
    assert "balance page did not confirm today's daily reward" in message
    assert "secret-once-token" not in message
    output_lines = assert_timestamped_lines(capsys.readouterr().out)
    assert any(
        "V2EX balance page did not confirm today's reward after redeem action"
        in line
        for line in output_lines
    )
    assert all("secret-once-token" not in line for line in output_lines)


def test_check_in_fails_when_redeem_response_is_unauthenticated(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    action_url = "https://www.v2ex.com/mission/daily/redeem?once=redacted-once"
    monkeypatch.setattr(v2ex, "_fetch_page", lambda url, headers: "需要先登录")

    success, message = v2ex.check_in(action_url, {}, "V2EX\n")

    assert success is False
    assert "unauthenticated or expired" in message
    output_lines = assert_timestamped_lines(capsys.readouterr().out)
    assert len(output_lines) == 1
    assert (
        "V2EX redeem response indicates the cookie is unauthenticated"
        in output_lines[0]
    )
    assert "redacted-once" not in output_lines[0]


def test_check_in_does_not_log_action_token_when_redeem_request_fails(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    action_url = "https://www.v2ex.com/mission/daily/redeem?once=secret-once-token"

    def fail_fetch_page(url: str, headers: dict[str, str]) -> str:
        raise RuntimeError("network failure including secret-once-token")

    monkeypatch.setattr(v2ex, "_fetch_page", fail_fetch_page)

    success, message = v2ex.check_in(action_url, {}, "V2EX\n")

    assert success is False
    assert "redeem action request failed before balance confirmation" in message
    assert "secret-once-token" not in message
    output_lines = assert_timestamped_lines(capsys.readouterr().out)
    assert len(output_lines) == 1
    assert "RuntimeError" in output_lines[0]
    assert "secret-once-token" not in output_lines[0]


def test_parse_balance_daily_rewards_keeps_timestamp_with_own_reward_delta() -> None:
    today = "2026-05-08"
    balance_html = f"""
    <table>
      <tr>
        <td class="d"><small class="gray">{today} 10:00:51 +08:00</small></td>
        <td class="d">每日登录奖励</td>
        <td class="d" style="text-align: right;"><span class="positive"><strong>9.0</strong></span></td>
        <td class="d" style="text-align: right;">13665.28</td>
        <td class="d"><span class="gray">20260508 的每日登录奖励 9 铜币</span></td>
      </tr>
      <tr>
        <td class="d"><small class="gray">2026-05-07 10:00:51 +08:00</small></td>
        <td class="d">每日登录奖励</td>
        <td class="d" style="text-align: right;">+1</td>
        <td class="d" style="text-align: right;">13664.28</td>
      </tr>
    </table>
    """

    entries = v2ex._parse_balance_daily_rewards(balance_html)

    assert entries == [
        (f"{today} 10:00:51 +08:00", "9"),
        ("2026-05-07 10:00:51 +08:00", "+1"),
    ]


def test_check_in_keeps_generic_success_when_reward_delta_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    today = "2026-05-08"
    action_url = "https://www.v2ex.com/mission/daily/redeem?once=redacted-once"
    balance_html = f"""
    <table>
      <tr>
        <td class="d"><small class="gray">{today} 15:22:00 +08:00</small></td>
        <td class="d">每日登录奖励</td>
      </tr>
    </table>
    """
    monkeypatch.setattr(v2ex, "_today_local_date", lambda: today)

    def fetch_page(url: str, headers: dict[str, str]) -> str:
        if url == action_url:
            return "redeem response changed"
        if url == v2ex.BALANCE_URL:
            return balance_html
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(v2ex, "_fetch_page", fetch_page)

    success, message = v2ex.check_in(action_url, {}, "V2EX\n")

    assert success is True
    assert "Check in successfully\n" in message
    assert "copper" not in message
    output_lines = assert_timestamped_lines(capsys.readouterr().out)
    assert any(
        "V2EX balance page confirms today's daily reward" in line
        for line in output_lines
    )
    assert all("copper" not in line for line in output_lines)


def test_check_in_fails_when_balance_is_ambiguous(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    action_url = "https://www.v2ex.com/mission/daily/redeem?once=secret-once-token"
    balance_html = """
    <table>
      <tr>
        <td>
          <small class="gray">2000-01-01 15:22:00 +08:00</small>
        </td>
        <td class="d">每日登录奖励</td>
        <td class="d" style="text-align: right;">+1</td>
        <td class="d" style="text-align: right;">100</td>
      </tr>
    </table>
    """

    def fetch_page(url: str, headers: dict[str, str]) -> str:
        if url == action_url:
            return "redeem response changed"
        if url == v2ex.BALANCE_URL:
            return balance_html
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(v2ex, "_fetch_page", fetch_page)

    success, message = v2ex.check_in(action_url, {}, "V2EX\n")

    assert success is False
    assert "balance page did not confirm today's daily reward" in message
    assert "secret-once-token" not in message
    output_lines = assert_timestamped_lines(capsys.readouterr().out)
    assert any(
        "V2EX balance page did not confirm today's reward after redeem action"
        in line
        for line in output_lines
    )
    assert all("secret-once-token" not in line for line in output_lines)


def test_main_keeps_success_when_balance_parsing_fails(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    notifications = []

    monkeypatch.setattr(v2ex, "load_dotenv", lambda: None)
    monkeypatch.setattr(
        v2ex,
        "get_cookie_value",
        lambda env_name, domains: "cookie=value",
    )
    monkeypatch.setattr(
        v2ex,
        "get_daily_mission_action",
        lambda headers, message, session: (
            "https://www.v2ex.com/mission/daily/redeem?once=redacted-once",
            False,
            message + "Successfully got daily mission action\n",
        ),
    )
    monkeypatch.setattr(
        v2ex,
        "check_in",
        lambda action_url, headers, message, session: (
            True,
            message + "Check in successfully\n",
        ),
    )
    monkeypatch.setattr(v2ex, "balance", lambda headers, session: (None, None))
    monkeypatch.setattr(
        v2ex,
        "send_tg_notification",
        lambda message: notifications.append(message),
    )

    assert v2ex.main() == 0

    output_lines = assert_timestamped_lines(capsys.readouterr().out)
    assert len(output_lines) == 1
    assert (
        "V2EX balance reward amount parsing failed after successful redeem"
        in output_lines[0]
    )
    assert len(notifications) == 1
    assert "Check in successfully" in notifications[0]
