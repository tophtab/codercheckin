import sys

from dotenv import load_dotenv

from attendance_checkin import AttendanceConfig, run_attendance_checkin
from cookiecloud.client import get_cookie_value
from runtime_log import log
from telegram.notify import send_tg_notification


CONFIG = AttendanceConfig(
    name="DEEPFLOOD",
    env_name="DEEPFLOOD_COOKIE",
    domains=["deepflood.com", "www.deepflood.com"],
    origin="https://www.deepflood.com",
    referer="https://www.deepflood.com/board",
    attendance_url="https://www.deepflood.com/api/attendance?random=true",
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
