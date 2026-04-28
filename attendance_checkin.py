import random
import time
from dataclasses import dataclass
from typing import Callable

from curl_cffi import requests

from checkin_response import is_successful_checkin_response


DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_DELAY_RANGE_SECONDS = (1, 20)


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
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
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
        print(f"Using the {idx} account for check-in...", flush=True)

        delay = randint(*DEFAULT_DELAY_RANGE_SECONDS)
        print(f"The {idx} account will wait for {delay} seconds...", flush=True)
        sleep(delay)

        headers = _build_headers(config, cookie)

        try:
            response = post(
                config.attendance_url,
                headers=headers,
                impersonate="chrome136",
                timeout=timeout,
            )
        except Exception as err:
            error_message = f"{config.name} account {idx} check-in process error: {err}"
            print(error_message, flush=True)
            notify(error_message)
            return 1

        print(f"The {idx} account's Status Code: {response.status_code}", flush=True)
        print(f"The {idx} account's Response Content: {response.text}", flush=True)

        if is_successful_checkin_response(response.status_code, response.text):
            success_message = f"{config.name} account {idx} check-in successful"
            print(success_message, flush=True)
            notify(success_message)
            continue

        fail_message = f"{config.name} account {idx} check-in failed, response content: {response.text}"
        print(fail_message, flush=True)
        notify(fail_message)
        return 1

    return 0


def _build_headers(config: AttendanceConfig, cookie: str) -> dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
        "Origin": config.origin,
        "Referer": config.referer,
        "Content-Type": "application/json",
        "Cookie": cookie,
    }
