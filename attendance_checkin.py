import random
import time
from dataclasses import dataclass
from typing import Callable

from curl_cffi import requests

from checkin_response import is_successful_checkin_response
from config import (
    DEFAULT_ACCEPT_LANGUAGE,
    DEFAULT_BROWSER_IMPERSONATE,
    DEFAULT_DELAY_RANGE_SECONDS,
    DEFAULT_USER_AGENT,
    REQUEST_TIMEOUT_SECONDS,
)
from runtime_log import log


@dataclass(frozen=True)
class AttendanceConfig:
    name: str
    env_name: str
    domains: list[str]
    origin: str
    referer: str
    attendance_url: str


def run_attendance_checkin(
    config: AttendanceConfig,
    *,
    get_cookie: Callable[[str, list[str]], str],
    notify: Callable[[str], bool],
    sleep: Callable[[float], None] = time.sleep,
    randint: Callable[[int, int], int] = random.randint,
    post: Callable = requests.post,
    timeout: int = REQUEST_TIMEOUT_SECONDS,
) -> int:
    cookies = get_cookie(config.env_name, config.domains)
    if not cookies:
        raise ValueError(
            f"Environment variable {config.env_name} is not set and Cookie Cloud has no matching cookie"
        )

    cookie_list = [cookie.strip() for cookie in cookies.split("&") if cookie.strip()]
    if not cookie_list:
        raise ValueError(f"Environment variable {config.env_name} is empty")

    for idx, cookie in enumerate(cookie_list, start=1):
        log(f"Using the {idx} account for check-in...")

        delay = randint(*DEFAULT_DELAY_RANGE_SECONDS)
        log(f"The {idx} account will wait for {delay} seconds...")
        sleep(delay)

        headers = _build_headers(config, cookie)

        try:
            response = post(
                config.attendance_url,
                headers=headers,
                impersonate=DEFAULT_BROWSER_IMPERSONATE,
                timeout=timeout,
            )
        except Exception as err:
            error_message = f"{config.name} account {idx} check-in process error: {err}"
            log(error_message)
            notify(error_message)
            return 1

        log(f"The {idx} account's Status Code: {response.status_code}")
        log(f"The {idx} account's Response Content: {response.text}")

        if is_successful_checkin_response(response.status_code, response.text):
            success_message = f"{config.name} account {idx} check-in successful"
            log(success_message)
            notify(success_message)
            continue

        fail_message = f"{config.name} account {idx} check-in failed, response content: {response.text}"
        log(fail_message)
        notify(fail_message)
        return 1

    return 0


def _build_headers(config: AttendanceConfig, cookie: str) -> dict[str, str]:
    return {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept-Language": DEFAULT_ACCEPT_LANGUAGE,
        "Origin": config.origin,
        "Referer": config.referer,
        "Content-Type": "application/json",
        "Cookie": cookie,
    }
