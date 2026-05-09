import re
import sys
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from http.cookies import SimpleCookie
from urllib.parse import parse_qs, urljoin, urlparse, urlunparse

from curl_cffi import requests
from dotenv import load_dotenv

from config import (
    DEFAULT_ACCEPT_LANGUAGE,
    DEFAULT_BROWSER_IMPERSONATE,
    DEFAULT_SEC_CH_UA,
    DEFAULT_SEC_CH_UA_PLATFORM,
    DEFAULT_USER_AGENT,
    REQUEST_TIMEOUT_SECONDS,
)
from cookiecloud.client import get_cookie_value
from runtime_log import log
from telegram.notify import send_tg_notification


LOGIN_PAGE_MARKERS = (
    "需要先登录",
    "you need to sign in first to view this page",
)
ALREADY_CLAIMED_MARKERS = (
    "每日登录奖励已领取",
)
ACTION_ASSIGNMENT_PATTERN = re.compile(
    r"(?:window\.)?location(?:\.href)?\s*=\s*(['\"])(?P<url>.*?)\1",
    re.IGNORECASE,
)
V2EX_ORIGIN = "https://www.v2ex.com"
MISSION_DAILY_URL = "https://www.v2ex.com/mission/daily"
BALANCE_URL = "https://www.v2ex.com/balance"
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
BALANCE_ROW_PATTERN = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.DOTALL | re.IGNORECASE)
BALANCE_SMALL_GRAY_PATTERN = re.compile(
    r"<small\b(?=[^>]*\bclass=['\"][^'\"]*\bgray\b[^'\"]*['\"])[^>]*>"
    r"(.*?)</small>",
    re.DOTALL | re.IGNORECASE,
)
BALANCE_RIGHT_TD_PATTERN = re.compile(
    r"<td\b(?=[^>]*\bclass=['\"][^'\"]*\bd\b[^'\"]*['\"])"
    r"(?=[^>]*\bstyle=['\"][^'\"]*text-align:\s*right;?[^'\"]*['\"])[^>]*>"
    r"(.*?)</td>",
    re.DOTALL | re.IGNORECASE,
)


def _is_supported_mission_action_path(path: str) -> bool:
    return path in {"/balance", "/mission/daily/redeem"}


def _normalize_v2ex_action_url(action: str) -> str | None:
    parsed = urlparse(urljoin(V2EX_ORIGIN, action.strip()))
    if parsed.scheme not in {"http", "https"}:
        return None
    if parsed.netloc not in {"v2ex.com", "www.v2ex.com"}:
        return None
    if not _is_supported_mission_action_path(parsed.path):
        return None
    if parsed.path == "/mission/daily/redeem" and not parse_qs(parsed.query).get(
        "once"
    ):
        return None

    return urlunparse(("https", "www.v2ex.com", parsed.path, "", parsed.query, ""))


def _is_balance_action_url(action_url: str) -> bool:
    return urlparse(action_url).path == "/balance"


def _is_redeem_action_url(action_url: str) -> bool:
    return urlparse(action_url).path == "/mission/daily/redeem"


def _extract_onclick_action_url(onclick: str) -> str | None:
    match = ACTION_ASSIGNMENT_PATTERN.search(unescape(onclick))
    if not match:
        return None

    return _normalize_v2ex_action_url(match.group("url"))


class _MissionActionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.action_url: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.action_url is not None:
            return

        attr_map = {name.lower(): value or "" for name, value in attrs}
        onclick = attr_map.get("onclick")
        if onclick:
            action_url = _extract_onclick_action_url(onclick)
            if action_url:
                self.action_url = action_url
                return


def _parse_daily_mission_action_url(content: str) -> str | None:
    parser = _MissionActionParser()
    parser.feed(content)
    return parser.action_url


def build_headers(cookie: str) -> dict[str, str]:
    return {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
        "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": DEFAULT_ACCEPT_LANGUAGE,
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "referer": "https://www.v2ex.com/mission/daily",
        "sec-ch-ua": DEFAULT_SEC_CH_UA,
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": DEFAULT_SEC_CH_UA_PLATFORM,
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": DEFAULT_USER_AGENT,
        "cookie": cookie,
    }


def build_session(cookie: str) -> requests.Session:
    session = requests.Session(impersonate=DEFAULT_BROWSER_IMPERSONATE)
    parsed_cookie = SimpleCookie()
    parsed_cookie.load(cookie)
    for name, morsel in parsed_cookie.items():
        session.cookies.set(name, morsel.value, domain="www.v2ex.com", path="/")

    return session


def _headers_for_session(headers: dict[str, str]) -> dict[str, str]:
    return {
        name: value for name, value in headers.items() if name.lower() != "cookie"
    }


def _fetch_page(
    url: str,
    headers: dict[str, str],
    session: requests.Session | None = None,
) -> str:
    if session is None:
        response = requests.get(
            url,
            headers=headers,
            impersonate=DEFAULT_BROWSER_IMPERSONATE,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    else:
        response = session.get(
            url,
            headers=_headers_for_session(headers),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    return response.text


def _fetch_page_with_session(
    url: str,
    headers: dict[str, str],
    session: requests.Session | None,
) -> str:
    if session is None:
        return _fetch_page(url, headers)

    return _fetch_page(url, headers, session)


def _contains_marker(content: str, markers: tuple[str, ...]) -> bool:
    lowered = content.lower()
    return any(marker in lowered for marker in markers)


def _is_login_page(content: str) -> bool:
    return _contains_marker(content, LOGIN_PAGE_MARKERS)


def _is_already_claimed_page(content: str) -> bool:
    return _contains_marker(content, ALREADY_CLAIMED_MARKERS)


def _today_local_date() -> str:
    return datetime.now().astimezone().date().isoformat()


def _strip_html(value: str) -> str:
    return unescape(HTML_TAG_PATTERN.sub("", value)).strip()


def _parse_balance_daily_rewards(content: str) -> list[tuple[str, str]]:
    entries = []
    for row in BALANCE_ROW_PATTERN.findall(content):
        if "每日登录奖励" not in _strip_html(row):
            continue

        time_match = BALANCE_SMALL_GRAY_PATTERN.search(row)
        if not time_match:
            continue

        right_values = [
            _strip_html(value) for value in BALANCE_RIGHT_TD_PATTERN.findall(row)
        ]
        reward_value = right_values[-1] if right_values else ""
        entries.append((_strip_html(time_match.group(1)), reward_value))

    return entries


def _balance_time_is_today(balance_time: str) -> bool:
    today = _today_local_date()
    return balance_time.startswith(today) or balance_time.startswith(
        today.replace("-", "/")
    )


def _balance_confirms_today_daily_reward(
    headers: dict[str, str],
    session: requests.Session | None = None,
) -> bool:
    try:
        content = _fetch_page_with_session(BALANCE_URL, headers, session)
    except Exception as exc:
        log(f"V2EX balance confirmation failed: {type(exc).__name__}")
        return False

    entries = _parse_balance_daily_rewards(content)
    if any(_balance_time_is_today(reward_time) for reward_time, _ in entries):
        log("V2EX balance page confirms today's daily reward")
        return True

    log("V2EX balance page did not confirm today's daily reward")
    return False


def get_daily_mission_action(
    headers: dict[str, str],
    message: str,
    session: requests.Session | None = None,
) -> tuple[str | None, bool, str]:
    content = _fetch_page_with_session(MISSION_DAILY_URL, headers, session)

    if _is_login_page(content):
        log("V2EX daily mission page indicates the cookie is unauthenticated")
        return None, False, message + "The cookie is unauthenticated or expired.\n"

    if _is_already_claimed_page(content):
        return None, True, message + "You have already signed today.\n"

    action_url = _parse_daily_mission_action_url(content)
    if action_url:
        if _is_balance_action_url(action_url):
            return None, True, message + "You have already signed today.\n"
        return action_url, False, message + "Successfully got daily mission action\n"

    log("V2EX daily mission page loaded but no supported action was found")
    return (
        None,
        False,
        message + "Have not signed, but fail to get daily mission action\n",
    )


def check_in(
    action_url: str,
    headers: dict[str, str],
    message: str,
    session: requests.Session | None = None,
) -> tuple[bool, str]:
    normalized_action_url = _normalize_v2ex_action_url(action_url)
    if not normalized_action_url:
        log("V2EX daily mission action was not a supported V2EX action")
        return False, message + "Fail to check in: unsupported daily mission action\n"

    if _is_balance_action_url(normalized_action_url):
        return True, message + "You have already signed today.\n"

    if not _is_redeem_action_url(normalized_action_url):
        log("V2EX daily mission action was not a supported redeem action")
        return False, message + "Fail to check in: unsupported daily mission action\n"

    try:
        content = _fetch_page_with_session(normalized_action_url, headers, session)
    except Exception as exc:
        log(
            "V2EX redeem action request failed before balance confirmation: "
            f"{type(exc).__name__}"
        )
        return (
            False,
            message
            + "Fail to check in: redeem action request failed before balance confirmation\n",
        )

    if _is_login_page(content):
        log("V2EX redeem response indicates the cookie is unauthenticated")
        return (
            False,
            message + "Fail to check in: cookie is unauthenticated or expired\n",
        )

    if _balance_confirms_today_daily_reward(headers, session):
        return True, message + "Check in successfully\n"

    log("V2EX balance page did not confirm today's reward after redeem action")
    return (
        False,
        message + "Fail to check in: balance page did not confirm today's daily reward\n",
    )


def balance(
    headers: dict[str, str],
    session: requests.Session | None = None,
) -> tuple[str | None, str | None]:
    content = _fetch_page_with_session(BALANCE_URL, headers, session)
    entries = _parse_balance_daily_rewards(content)

    if not entries:
        return None, None

    return entries[0]


def main() -> int:
    load_dotenv()
    cookie = get_cookie_value("V2EX_COOKIE", ["v2ex.com", "www.v2ex.com"])
    if not cookie:
        raise ValueError(
            "Environment variable V2EX_COOKIE is not set and Cookie Cloud has no matching cookie"
        )

    message = datetime.now().astimezone().strftime("%Y/%m/%d %H:%M:%S") + " from V2EX \n"
    headers = build_headers(cookie)
    session = build_session(cookie)
    action_url, signed, message = get_daily_mission_action(headers, message, session)

    if signed:
        log("V2EX already checked in today")
        send_tg_notification(message)
        return 0

    if not action_url:
        send_tg_notification(message + "FAIL.\n")
        raise ValueError("V2EX daily mission page did not provide a supported action")

    success, message = check_in(action_url, headers, message, session)
    if not success:
        send_tg_notification(message)
        raise ValueError("V2EX redeem request did not complete successfully")

    balance_time, balance_value = balance(headers, session)
    if not balance_time or not balance_value:
        log("V2EX balance parsing failed after successful redeem")

    send_tg_notification(message)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as err:
        log(err)
        sys.exit(1)
