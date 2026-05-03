import sys

from dotenv import load_dotenv

from attendance_checkin import AttendanceConfig, run_attendance_checkin
from cookiecloud.client import get_cookie_value
from runtime_log import log
from telegram.notify import send_tg_notification


CONFIG = AttendanceConfig(
    name="NODESEEK",
    env_name="NODESEEK_COOKIE",
    domains=["nodeseek.com", "www.nodeseek.com"],
    origin="https://www.nodeseek.com",
    referer="https://www.nodeseek.com/board",
    attendance_url="https://www.nodeseek.com/api/attendance?random=true",
)


def main() -> int:
    load_dotenv()
    return run_attendance_checkin(
        CONFIG,
        get_cookie=get_cookie_value,
        notify=send_tg_notification,
    )


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as err:
        log(err)
        sys.exit(1)
