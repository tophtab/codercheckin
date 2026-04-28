import re
import sys
from datetime import datetime

from curl_cffi import requests
from dotenv import load_dotenv

from cookiecloud.client import get_cookie_value
from telegram.notify import send_tg_notification


REQUEST_TIMEOUT_SECONDS = 30


def build_headers(cookie: str) -> dict[str, str]:
    return {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
        "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "referer": "https://www.v2ex.com/mission/daily",
        "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "cookie": cookie,
    }


def get_once(headers: dict[str, str], message: str) -> tuple[str | None, bool, str]:
    url = "https://www.v2ex.com/mission/daily"
    res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
    content = res.text

    if re.search(r"需要先登录", content):
        return None, False, message + "The cookie is overdated."

    if re.search(r"每日登录奖励已领取", content):
        return None, True, message + "You have already signed today.\n"

    once_match = re.search(r"redeem\?once=(.*?)'", content)
    if once_match:
        once = once_match.group(1)
        return once, False, message + f"Successfully get once {once}\n"

    return None, False, message + "Have not signed, but fail to get once\n"


def check_in(once: str, headers: dict[str, str], message: str) -> tuple[bool, str]:
    url = f"https://www.v2ex.com/mission/daily/redeem?once={once}"
    res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
    content = res.text

    if re.search(r"已成功领取每日登录奖励", content):
        return True, message + "Check in successfully\n"

    return False, message + "Fail to check in\n"


def balance(headers: dict[str, str]) -> tuple[str | None, str | None]:
    url = "https://www.v2ex.com/balance"
    res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
    content = res.text
    pattern = r'每日登录奖励.*?<small class="gray">(.*?)</small>.*?<td class="d" style="text-align: right;">.*?</td>.*?<td class="d" style="text-align: right;">(.*?)</td>'
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        return None, None

    return match.group(1).strip(), match.group(2).strip()


def main() -> int:
    load_dotenv()
    cookie = get_cookie_value(
        "V2EX_COOKIE",
        ["v2ex.com", "www.v2ex.com"],
    )
    if not cookie:
        raise ValueError(
            "Environment variable V2EX_COOKIE is not set and Cookie Cloud has no matching cookie"
        )

    message = datetime.now().astimezone().strftime("%Y/%m/%d %H:%M:%S") + " from V2EX \n"
    headers = build_headers(cookie)

    once, signed, message = get_once(headers, message)

    if once and not signed:
        success, message = check_in(once, headers, message)
        if not success:
            raise ValueError("Fail to check in")
        balance_time, balance_value = balance(headers)
        if not balance_time or not balance_value:
            raise ValueError("Fail to get balance")
        send_tg_notification(message)
        return 0

    if signed:
        print("V2EX already checked in today", flush=True)
        send_tg_notification(message)
        return 0

    message += "FAIL.\n"
    send_tg_notification(message)
    raise ValueError("Fail to check in")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as err:
        print(err, flush=True)
        sys.exit(1)
